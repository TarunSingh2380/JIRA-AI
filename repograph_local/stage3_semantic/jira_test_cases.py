"""JIRA ticket → test case generator (GraphRAG pipeline).

Pipeline
--------
1. Semantic search  — find relevant code chunks (files, commits, functions)
   via the EmbeddingDocument vector index.
2. Graph context    — for each hit file, pull functions, callers, callees,
   related classes, and recent commits from Neo4j.
3. Claude call      — send assembled context + ticket to Claude claude-sonnet-4-6;
   get back structured test cases in Markdown.

Public API
----------
    result = await analyze_jira_ticket(driver, ticket, repo, ...)
    # returns JiraAnalysisResult with .test_cases (markdown) and raw context
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import anthropic
from neo4j import AsyncDriver

from config import settings
from stage3_semantic.bge_m3_embeddings import semantic_search

log = logging.getLogger("uvicorn.error")

# ── Schema description injected into every Claude prompt ─────────────────────
_GRAPH_SCHEMA = """
Neo4j graph schema (Stage 1 + Stage 2):

NODES
  (:Repo      {full_name, name, default_branch})
  (:File      {repo_full_name, path, extension})
  (:Commit    {sha, short_sha, summary, committed_at, additions, deletions})
  (:Author    {email, name})
  (:Function  {qualified_name, name, file_path, repo_full_name, start_line, end_line, language})
  (:Class     {qualified_name, name, file_path, repo_full_name, start_line, language})

EDGES
  (:Commit)-[:IN_REPO]->(:Repo)
  (:Commit)-[:AUTHORED_BY]->(:Author)
  (:Commit)-[:TOUCHES {change_type, additions, deletions}]->(:File)
  (:File)-[:IN_REPO]->(:Repo)
  (:Function)-[:DEFINED_IN]->(:File)
  (:Function)-[:CALLS]->(:Function)
  (:Function)-[:METHOD_OF]->(:Class)
  (:Class)-[:DEFINED_IN]->(:File)
  (:Class)-[:EXTENDS]->(:Class)
""".strip()


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class JiraTicket:
    issue_key: str
    summary: str
    description: str = ""
    assignee: str = ""
    due_date: str = ""
    priority: str = ""
    issue_type: str = ""
    status: str = ""
    reporter: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JiraTicket":
        return cls(
            issue_key=d.get("issueKey") or d.get("issue_key", ""),
            summary=d.get("summary", ""),
            description=d.get("description", ""),
            assignee=d.get("assignee", ""),
            due_date=d.get("dueDate") or d.get("due_date", ""),
            priority=d.get("priority", ""),
            issue_type=d.get("issueType") or d.get("issue_type", ""),
            status=d.get("status", ""),
            reporter=d.get("reporter", ""),
        )

    def search_query(self) -> str:
        parts = [self.summary]
        if self.description:
            parts.append(self.description[:500])
        return " ".join(parts)

    def as_text(self) -> str:
        return (
            f"Issue Key: {self.issue_key}\n"
            f"Type: {self.issue_type} | Priority: {self.priority} | Status: {self.status}\n"
            f"Summary: {self.summary}\n"
            f"Description: {self.description or '(no description)'}\n"
            f"Reporter: {self.reporter} | Assignee: {self.assignee}\n"
            f"Due: {self.due_date or 'not set'}"
        )


@dataclass
class GraphContext:
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    recent_commits: List[Dict[str, Any]] = field(default_factory=list)
    call_edges: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class JiraAnalysisResult:
    ticket_key: str
    repo: str
    semantic_hits: List[Dict[str, Any]]
    graph_context: Dict[str, Any]
    test_cases: str
    model: str
    input_tokens: int
    output_tokens: int


# ── Graph queries ─────────────────────────────────────────────────────────────

async def _fetch_graph_context(
    driver: AsyncDriver,
    repo: str,
    file_paths: List[str],
    days: int = 90,
) -> GraphContext:
    """Pull functions, classes, call edges, and recent commits for the given files."""
    ctx = GraphContext()
    if not file_paths:
        return ctx

    async with driver.session(database=settings.neo4j_database) as s:

        # Functions + their direct callers and callees
        q_fn = """
        MATCH (fn:Function {repo_full_name: $repo})
        WHERE fn.file_path IN $files
        OPTIONAL MATCH (fn)-[:CALLS]->(callee:Function)
        OPTIONAL MATCH (caller:Function)-[:CALLS]->(fn)
        RETURN fn.qualified_name AS qn,
               fn.name AS name,
               fn.file_path AS file_path,
               fn.start_line AS start_line,
               fn.language AS language,
               collect(DISTINCT callee.name) AS calls,
               collect(DISTINCT caller.name) AS called_by
        ORDER BY fn.file_path, fn.start_line
        """
        result = await s.run(q_fn, repo=repo, files=file_paths)
        ctx.functions = [r.data() async for r in result]

        # Classes in those files
        q_cls = """
        MATCH (cl:Class {repo_full_name: $repo})
        WHERE cl.file_path IN $files
        RETURN cl.qualified_name AS qn, cl.name AS name,
               cl.file_path AS file_path, cl.start_line AS start_line
        ORDER BY cl.file_path, cl.start_line
        """
        result = await s.run(q_cls, repo=repo, files=file_paths)
        ctx.classes = [r.data() async for r in result]

        # Recent commits touching those files
        q_commits = """
        MATCH (c:Commit)-[:TOUCHES]->(f:File {repo_full_name: $repo})
        WHERE f.path IN $files
          AND c.committed_at > datetime() - duration({days: $days})
        MATCH (c)-[:AUTHORED_BY]->(a:Author)
        RETURN DISTINCT c.short_sha AS sha, c.summary AS summary,
               toString(c.committed_at) AS committed_at,
               a.name AS author, f.path AS file_path
        ORDER BY c.committed_at DESC
        LIMIT 30
        """
        result = await s.run(q_commits, repo=repo, files=file_paths, days=days)
        ctx.recent_commits = [r.data() async for r in result]

    return ctx


async def _fetch_graph_context_by_keyword(
    driver: AsyncDriver,
    repo: str,
    keywords: List[str],
    days: int = 90,
) -> GraphContext:
    """Fallback: keyword search on function names when no embedding hits."""
    ctx = GraphContext()
    if not keywords:
        return ctx

    async with driver.session(database=settings.neo4j_database) as s:
        conditions = " OR ".join(
            f"toLower(fn.name) CONTAINS toLower('{kw.replace(chr(39), '')}')"
            for kw in keywords[:5]
        )
        q = f"""
        MATCH (fn:Function {{repo_full_name: $repo}})
        WHERE {conditions}
        OPTIONAL MATCH (fn)-[:CALLS]->(callee:Function)
        OPTIONAL MATCH (caller:Function)-[:CALLS]->(fn)
        RETURN fn.qualified_name AS qn, fn.name AS name,
               fn.file_path AS file_path, fn.start_line AS start_line,
               fn.language AS language,
               collect(DISTINCT callee.name) AS calls,
               collect(DISTINCT caller.name) AS called_by
        LIMIT 20
        """
        result = await s.run(q, repo=repo)
        ctx.functions = [r.data() async for r in result]
    return ctx


# ── Context assembly ──────────────────────────────────────────────────────────

def _build_context_block(
    semantic_hits: List[Dict[str, Any]],
    graph: GraphContext,
) -> str:
    lines: List[str] = []

    if semantic_hits:
        lines.append("## Semantically Similar Code Chunks")
        for h in semantic_hits[:12]:
            score = h.get("score", 0)
            kind = h.get("kind", "?")
            title = h.get("title", "")
            text = (h.get("text") or "")[:600]
            lines.append(f"\n### [{kind}] {title}  (score={score:.3f})")
            if text:
                lines.append(f"```\n{text}\n```")

    if graph.functions:
        lines.append("\n## Functions in Relevant Files")
        for fn in graph.functions[:20]:
            callee_str = ", ".join(fn.get("calls") or [])
            caller_str = ", ".join(fn.get("called_by") or [])
            lines.append(
                f"- **{fn['name']}** ({fn.get('file_path','?')}:{fn.get('start_line','?')})"
                + (f"\n  calls: {callee_str}" if callee_str else "")
                + (f"\n  called_by: {caller_str}" if caller_str else "")
            )

    if graph.classes:
        lines.append("\n## Classes in Relevant Files")
        for cls in graph.classes[:10]:
            lines.append(f"- **{cls['name']}** ({cls.get('file_path','?')}:{cls.get('start_line','?')})")

    if graph.recent_commits:
        lines.append("\n## Recent Commits on Relevant Files")
        for c in graph.recent_commits[:15]:
            lines.append(
                f"- `{c.get('sha','')}` {c.get('committed_at','')[:10]}  "
                f"**{c.get('author','')}**: {c.get('summary','')[:100]}"
            )

    return "\n".join(lines)


# ── Claude call ───────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a senior software engineer and QA expert specialising in test-driven development.

You receive:
  - A JIRA ticket (key, type, priority, summary, description)
  - Code context retrieved via semantic search and graph traversal of the actual codebase

Your task: produce a concise Markdown test-case document with EXACTLY 5 test cases — no more, no fewer.

Rules:
1. Write concrete test cases — not generic templates.
2. For each test case include: ID, title, preconditions, numbered steps, expected result.
3. Include at least one negative/edge-case test.
4. If the ticket is a bug, one test case must be a regression test.
5. Reference function names / file paths from the code context when relevant.
6. Do NOT invent file contents not shown in the context.
7. Keep each test case brief — 3-5 steps maximum.
"""

_USER_TEMPLATE = """\
## Graph DB Schema (for context)
{schema}

---

## JIRA Ticket
{ticket}

---

## Code Context (semantic search + CGC graph traversal)
{context}

---

Generate EXACTLY 5 test cases (no more, no fewer). Format each test case as:

```
TC-<N>: <Title>
  Preconditions: ...
  Steps:
    1. ...
  Expected: ...
```

After TC-5, add one short **Summary** sentence (max 2 lines).
"""


async def _call_claude(
    ticket: JiraTicket,
    context_block: str,
    api_key: str,
    claude_model: str = "claude-sonnet-4-6",
) -> tuple[str, int, int]:
    """Return (test_cases_markdown, input_tokens, output_tokens)."""
    client = anthropic.AsyncAnthropic(api_key=api_key)

    user_message = _USER_TEMPLATE.format(
        schema=_GRAPH_SCHEMA,
        ticket=ticket.as_text(),
        context=context_block or "(no code context retrieved — answer from ticket alone)",
    )

    response = await client.messages.create(
        model=claude_model,
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text
    usage = response.usage
    return text, usage.input_tokens, usage.output_tokens


# ── Public entry point ────────────────────────────────────────────────────────

async def analyze_jira_ticket(
    driver: AsyncDriver,
    ticket_data: Dict[str, Any],
    repo: str,
    *,
    model_key: str = "bge-m3",
    top_k: int = 15,
    api_key: Optional[str] = None,
    claude_model: str = "claude-sonnet-4-6",
    commit_history_days: int = 90,
) -> JiraAnalysisResult:
    """
    Full pipeline: ticket → semantic search → graph context → Claude test cases.

    Parameters
    ----------
    driver        : async Neo4j driver
    ticket_data   : raw ticket dict (camelCase keys as from JIRA API)
    repo          : repo full_name, e.g. "agrimfincapindia/agrimfincapindia"
    model_key     : embedding model to use for semantic search
    top_k         : number of semantic hits to retrieve
    api_key       : Anthropic API key (falls back to settings.anthropic_api_key)
    claude_model  : Claude model ID to use
    commit_history_days : how far back to look for relevant commits
    """
    ticket = JiraTicket.from_dict(ticket_data)
    resolved_api_key = api_key or settings.anthropic_api_key
    if not resolved_api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in env / .env and not passed in request")

    # ── 1. Semantic search ────────────────────────────────────────────────────
    search_query = ticket.search_query()
    log.info("[JIRA %s] Semantic search: %r", ticket.issue_key, search_query[:80])

    try:
        semantic_hits = await semantic_search(
            driver,
            search_query,
            repos=[repo] if repo else None,
            top_k=top_k,
            model_key=model_key,
        )
    except Exception as exc:
        log.warning("[JIRA %s] Semantic search failed (%s), continuing without it", ticket.issue_key, exc)
        semantic_hits = []

    # ── 2. Extract file paths from hits ──────────────────────────────────────
    file_paths: list[str] = []
    seen: set[str] = set()
    for hit in semantic_hits:
        meta = hit.get("metadata") or {}
        fp = meta.get("file_path") or meta.get("path")
        if fp and fp not in seen:
            file_paths.append(fp)
            seen.add(fp)
        # also treat source_key as a path hint for file-kind hits
        if hit.get("kind") == "file":
            sk = hit.get("source_key", "")
            if sk and sk not in seen:
                file_paths.append(sk)
                seen.add(sk)

    log.info("[JIRA %s] %d semantic hits → %d unique files", ticket.issue_key, len(semantic_hits), len(file_paths))

    # ── 3. Graph context ──────────────────────────────────────────────────────
    if file_paths:
        graph = await _fetch_graph_context(
            driver, repo, file_paths, days=commit_history_days
        )
    else:
        # Fallback: keyword search on function names derived from ticket
        keywords = [w for w in search_query.split() if len(w) > 4][:6]
        graph = await _fetch_graph_context_by_keyword(driver, repo, keywords)

    log.info(
        "[JIRA %s] Graph: %d functions, %d classes, %d commits",
        ticket.issue_key, len(graph.functions), len(graph.classes), len(graph.recent_commits),
    )

    # ── 4. Assemble context block ─────────────────────────────────────────────
    context_block = _build_context_block(semantic_hits, graph)

    # ── 5. Claude: generate test cases ───────────────────────────────────────
    log.info("[JIRA %s] Calling Claude (%s) for test case generation", ticket.issue_key, claude_model)
    test_cases_md, in_tok, out_tok = await _call_claude(
        ticket, context_block, resolved_api_key, claude_model
    )
    log.info("[JIRA %s] Claude done. tokens in=%d out=%d", ticket.issue_key, in_tok, out_tok)

    return JiraAnalysisResult(
        ticket_key=ticket.issue_key,
        repo=repo,
        semantic_hits=semantic_hits,
        graph_context={
            "functions": graph.functions,
            "classes": graph.classes,
            "recent_commits": graph.recent_commits,
        },
        test_cases=test_cases_md,
        model=claude_model,
        input_tokens=in_tok,
        output_tokens=out_tok,
    )

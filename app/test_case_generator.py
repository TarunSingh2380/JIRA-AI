"""Test case generator: JIRA ticket + Qdrant semantic search + CGC Neo4j graph → Claude.

Pipeline
--------
1. Semantic search  — embed ticket text with Ollama, search the Qdrant
                      codebase collection (e.g. "codebase_bge_m3")
2. Graph context    — query Neo4j directly using CGC's schema
                      (:Function, :File, :Class with absolute paths)
                      for functions in the matched files + their call edges
3. LLM generation   — Claude receives assembled context → Markdown test cases

No repograph HTTP service required.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from app.codebase_graph import CODEBASE_EMBEDDING_MODELS
from app.config import Settings
from app.llm_client import LLMClient
from app.ollama_embedder import OllamaEmbedder

log = logging.getLogger(__name__)

_STOP_WORDS = {
    "about", "after", "again", "before", "description",
    "have", "jira", "missing", "please",
    "reply", "should", "there", "ticket", "update", "with",
}

_GRAPH_SCHEMA_SUMMARY = """
Neo4j graph schema (CodeGraphContext):
  (:Repository {path, name})
  (:File       {path})                 ← absolute paths
  (:Function   {name, path, line_number})
  (:Class      {name, path, line_number})
  (:Function)-[:CALLS]->(:Function)
  (:Function)-[:METHOD_OF]->(:Class)
  (:Class)-[:EXTENDS]->(:Class)
  (:File)-[:CONTAINS]->(:Function | :Class)
""".strip()

_SYSTEM_PROMPT = """\
You are a senior software engineer and QA expert specialising in test-driven development.

You receive:
  - A JIRA ticket (key, type, priority, summary, description)
  - Code context retrieved via semantic search and graph traversal of the actual codebase

Your task: produce a thorough, actionable Markdown test-case document.

Rules:
1. Write concrete test cases — not generic templates.
2. Group by feature area or affected component.
3. For each test case include: ID, title, preconditions, numbered steps, expected result.
4. Add at least 3 edge-case / negative test cases.
5. If the ticket is a bug, add a regression test that would have caught it.
6. Reference function names / file paths from the code context when relevant.
7. If the language is evident from context, use it for code snippets.
8. Do NOT invent file contents not shown in the context.
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

Generate the test-case document now. Format each test case as:

```
TC-<N>: <Title>
  Preconditions: ...
  Steps:
    1. ...
  Expected: ...
```

Finish with a **Summary** section: what is being tested and why.
"""


class TestCaseGenerator:
    """Orchestrates Qdrant semantic search, CGC Neo4j graph context, and LLM generation."""

    def __init__(self, settings: Settings, llm_client: LLMClient) -> None:
        self.settings = settings
        self.llm_client = llm_client

    # ── public entry point ────────────────────────────────────────────────────

    def generate(
        self,
        ticket_data: Dict[str, Any],
        *,
        repo: Optional[str] = None,
        embedding_model: str = "codebase_bge_m3",
        top_k: int = 15,
    ) -> Dict[str, Any]:
        """
        Full pipeline → dict with keys:
          test_cases, semantic_hits_count, functions_found,
          files_touched_count, context_chars
        """
        ticket_key = (
            ticket_data.get("issueKey")
            or ticket_data.get("key")
            or ticket_data.get("issue_key")
            or "unknown"
        )
        log.info(
            "TestCaseGenerator.generate ticket=%s repo=%s model=%s",
            ticket_key, repo, embedding_model,
        )

        query = self._build_query(ticket_data)

        # 1. Semantic search via Qdrant + Ollama
        semantic_hits = self._semantic_search_qdrant(
            query, collection=embedding_model, repo=repo, top_k=top_k
        )
        log.info("Semantic hits: %d", len(semantic_hits))

        # 2. CGC graph context from Neo4j
        file_paths = self._extract_file_paths(semantic_hits)
        keywords = self._keywords(query)[:6]
        graph_functions, graph_classes = self._graph_context_cgc(
            file_paths=file_paths,
            keywords=keywords,
            repo=repo,
        )

        # 3. Assemble context block
        context_block = self._build_context_block(semantic_hits, graph_functions, graph_classes)

        # 4. LLM call
        user_message = _USER_TEMPLATE.format(
            schema=_GRAPH_SCHEMA_SUMMARY,
            ticket=self._ticket_as_text(ticket_data),
            context=context_block or "(no code context retrieved — answering from ticket alone)",
        )
        log.info("Calling LLM (context_chars=%d)", len(context_block))
        test_cases_md = self.llm_client.complete(_SYSTEM_PROMPT, user_message)

        return {
            "test_cases": test_cases_md,
            "semantic_hits_count": len(semantic_hits),
            "functions_found": len(graph_functions),
            "files_touched_count": len(file_paths),
            "context_chars": len(context_block),
        }

    # ── semantic search via Qdrant ────────────────────────────────────────────

    def _semantic_search_qdrant(
        self,
        query: str,
        *,
        collection: str,
        repo: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        model_cfg = CODEBASE_EMBEDDING_MODELS.get(
            collection, CODEBASE_EMBEDDING_MODELS["codebase_bge_m3"]
        )
        embedder = OllamaEmbedder(
            base_url=self.settings.ollama_url,
            model=model_cfg["ollama_model"],
            timeout_seconds=self.settings.ollama_embed_timeout_seconds,
        )
        if not embedder.is_available():
            log.warning("Ollama model %s unavailable; skipping semantic search", model_cfg["ollama_model"])
            return []

        query_vector = embedder.embed(query)
        if not query_vector:
            log.warning("Ollama returned empty embedding for query")
            return []

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter, FieldCondition, MatchValue
        except ImportError:
            log.warning("qdrant-client not installed; skipping semantic search")
            return []

        try:
            client = QdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key or None,
            )
            search_filter = None
            if repo:
                search_filter = Filter(
                    must=[FieldCondition(key="repo", match=MatchValue(value=repo))]
                )

            # qdrant-client ≥ 1.9 uses query_points(); older versions use search()
            try:
                response = client.query_points(
                    collection_name=collection,
                    query=query_vector,
                    limit=top_k,
                    query_filter=search_filter,
                    with_payload=True,
                )
                scored_points = response.points
            except AttributeError:
                scored_points = client.search(
                    collection_name=collection,
                    query_vector=query_vector,
                    limit=top_k,
                    query_filter=search_filter,
                    with_payload=True,
                )

            return [
                {
                    "score": r.score,
                    "path": (r.payload or {}).get("path", ""),
                    "repo": (r.payload or {}).get("repo", ""),
                    "repo_name": (r.payload or {}).get("repo_name", ""),
                    "language": (r.payload or {}).get("language", ""),
                    "text": ((r.payload or {}).get("text") or "")[:500],
                }
                for r in scored_points
            ]
        except Exception as exc:
            log.warning("Qdrant search failed: %s", exc)
            return []

    # ── CGC graph context from Neo4j ──────────────────────────────────────────

    def _graph_context_cgc(
        self,
        *,
        file_paths: List[str],
        keywords: List[str],
        repo: Optional[str],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Query CGC's Neo4j schema for functions and classes relevant to the ticket."""
        try:
            from neo4j import GraphDatabase
        except ImportError:
            log.warning("neo4j package not installed; skipping graph context")
            return [], []

        functions: List[Dict[str, Any]] = []
        classes: List[Dict[str, Any]] = []

        try:
            driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
            with driver.session(database=self.settings.neo4j_database) as session:
                # Functions in matched files (using ENDS WITH for relative→absolute path match)
                if file_paths:
                    result = session.run(
                        """
                        MATCH (fn:Function)
                        WHERE ANY(p IN $paths WHERE fn.path ENDS WITH p)
                        OPTIONAL MATCH (fn)-[:CALLS]->(callee:Function)
                        OPTIONAL MATCH (caller:Function)-[:CALLS]->(fn)
                        RETURN fn.name AS name,
                               fn.path AS path,
                               collect(DISTINCT callee.name)[..8] AS calls,
                               collect(DISTINCT caller.name)[..8] AS called_by
                        LIMIT 30
                        """,
                        paths=file_paths,
                    )
                    functions = [dict(r) for r in result]

                # Classes in matched files
                if file_paths:
                    result = session.run(
                        """
                        MATCH (cl:Class)
                        WHERE ANY(p IN $paths WHERE cl.path ENDS WITH p)
                        RETURN cl.name AS name, cl.path AS path
                        LIMIT 15
                        """,
                        paths=file_paths,
                    )
                    classes = [dict(r) for r in result]

                # Keyword fallback: search function names if no file hits
                if not functions and keywords:
                    conditions = " OR ".join(
                        f"toLower(fn.name) CONTAINS toLower('{kw.replace(chr(39), '')}')"
                        for kw in keywords[:5]
                    )
                    result = session.run(
                        f"""
                        MATCH (fn:Function)
                        WHERE {conditions}
                        OPTIONAL MATCH (fn)-[:CALLS]->(callee:Function)
                        OPTIONAL MATCH (caller:Function)-[:CALLS]->(fn)
                        RETURN fn.name AS name,
                               fn.path AS path,
                               collect(DISTINCT callee.name)[..8] AS calls,
                               collect(DISTINCT caller.name)[..8] AS called_by
                        LIMIT 20
                        """
                    )
                    functions = [dict(r) for r in result]

            driver.close()
        except Exception as exc:
            log.warning("Neo4j CGC graph query failed: %s", exc)

        log.info(
            "CGC graph context: %d functions, %d classes from %d file paths + %d keywords",
            len(functions), len(classes), len(file_paths), len(keywords),
        )
        return functions, classes

    # ── context assembly ──────────────────────────────────────────────────────

    def _build_context_block(
        self,
        hits: List[Dict[str, Any]],
        functions: List[Dict[str, Any]],
        classes: List[Dict[str, Any]],
    ) -> str:
        parts: List[str] = []

        if hits:
            parts.append("### Semantically Similar Code Files")
            for h in hits[:12]:
                score = h.get("score", 0)
                path = h.get("path", "")
                lang = h.get("language", "")
                text = h.get("text", "")
                parts.append(f"\n**{path}** ({lang}, score={score:.3f})")
                if text:
                    parts.append(f"```{lang.lower()}\n{text[:400]}\n```")

        if functions:
            parts.append("\n### Functions (from CGC call graph)")
            for fn in functions[:20]:
                name = fn.get("name", "")
                path = fn.get("path") or ""
                calls_str = ", ".join(fn.get("calls") or [])
                callers_str = ", ".join(fn.get("called_by") or [])
                entry = f"- **{name}** ({_short_path(path)})"
                if calls_str:
                    entry += f"\n  calls: {calls_str}"
                if callers_str:
                    entry += f"\n  called_by: {callers_str}"
                parts.append(entry)

        if classes:
            parts.append("\n### Classes (from CGC graph)")
            for cls in classes[:10]:
                name = cls.get("name", "")
                path = cls.get("path") or ""
                parts.append(f"- **{name}** ({_short_path(path)})")

        return "\n".join(parts)

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_query(ticket_data: Dict[str, Any]) -> str:
        parts = []
        for key in ("summary", "title", "description", "description_text"):
            val = ticket_data.get(key) or ""
            if val:
                parts.append(str(val)[:500])
        return " ".join(parts)

    @staticmethod
    def _extract_file_paths(hits: List[Dict[str, Any]]) -> List[str]:
        seen: set[str] = set()
        paths: List[str] = []
        for h in hits:
            p = h.get("path", "")
            if p and p not in seen:
                seen.add(p)
                paths.append(p)
        return paths

    @staticmethod
    def _keywords(text: str) -> List[str]:
        words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", text.lower())
        seen: set[str] = set()
        out: List[str] = []
        for w in words:
            if w not in _STOP_WORDS and w not in seen:
                seen.add(w)
                out.append(w)
        return out

    @staticmethod
    def _ticket_as_text(ticket_data: Dict[str, Any]) -> str:
        key = (
            ticket_data.get("issueKey")
            or ticket_data.get("key")
            or ticket_data.get("issue_key")
            or "?"
        )
        return (
            f"Issue Key  : {key}\n"
            f"Type       : {ticket_data.get('issueType') or ticket_data.get('issue_type') or '?'}\n"
            f"Priority   : {ticket_data.get('priority', '?')}\n"
            f"Status     : {ticket_data.get('status', '?')}\n"
            f"Summary    : {ticket_data.get('summary') or ticket_data.get('title', '')}\n"
            f"Description: {ticket_data.get('description') or ticket_data.get('description_text') or '(none)'}\n"
            f"Reporter   : {ticket_data.get('reporter', '')}\n"
            f"Assignee   : {ticket_data.get('assignee', '')}\n"
            f"Due        : {ticket_data.get('dueDate') or ticket_data.get('due_date', 'not set')}"
        )


def _short_path(abs_path: Optional[str], max_parts: int = 4) -> str:
    """Return last N components of a path to keep context blocks readable."""
    if not abs_path:
        return ""
    parts = abs_path.replace("\\", "/").split("/")
    return "/".join(parts[-max_parts:]) if len(parts) > max_parts else abs_path

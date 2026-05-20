"""Test case generator: JIRA ticket + Graph DB + Embeddings → Claude test cases.

Pipeline
--------
1. Semantic search  — POST repograph /search/semantic with ticket text
2. Graph context    — GET  repograph /functions/{qn}/callers for each hit function
                       GET  repograph /files/touched_recently for ticket keywords
3. LLM generation   — Claude receives assembled context and generates test cases
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import requests

from app.config import Settings
from app.llm_client import LLMClient

log = logging.getLogger(__name__)

# Map the embedding model names used by the graph-admin UI
# to the model_key values accepted by repograph /search/semantic.
_MODEL_KEY_MAP: Dict[str, str] = {
    "codebase_bge_m3": "bge-m3",
    "codebase_qwen3_0_6b": "qwen3-embedding-0.6b",
    "codebase_mxbai_large": "mxbai-embed-large-v1",
    # pass-through if already in repograph format
    "bge-m3": "bge-m3",
    "qwen3-embedding-0.6b": "qwen3-embedding-0.6b",
    "mxbai-embed-large-v1": "mxbai-embed-large-v1",
}

_STOP_WORDS = {
    "about", "after", "again", "before", "description",
    "have", "jira", "missing", "please",
    "reply", "should", "there", "ticket", "update", "with",
}

_GRAPH_SCHEMA_SUMMARY = """
Neo4j graph schema:
  (:Repo)   (:File)   (:Commit)-[:AUTHORED_BY]->(:Author)
  (:Function {qualified_name, name, file_path, repo_full_name, start_line, end_line, language})
  (:Class    {qualified_name, name, file_path, repo_full_name, start_line})
  (:Function)-[:CALLS]->(:Function)
  (:Function)-[:METHOD_OF]->(:Class)
  (:Class)-[:EXTENDS]->(:Class)
  (:Commit)-[:TOUCHES {change_type}]->(:File)
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

## Code Context (semantic search + graph traversal)
{context}

---

Generate the test-case document now. Format each test case as:

```
TC-<N>: <Title>
  Preconditions: ...
  Steps:
    1. ...
    2. ...
  Expected: ...
```

Finish with a **Summary** section: what is being tested and why.
"""


class TestCaseGenerator:
    """Orchestrates semantic search, graph context fetch, and LLM test-case generation."""

    def __init__(self, settings: Settings, llm_client: LLMClient) -> None:
        self.settings = settings
        self.llm_client = llm_client
        self._base = settings.repograph_base_url
        self._timeout = settings.external_request_timeout_seconds

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
          files_touched_count, context_summary
        """
        ticket_key = (
            ticket_data.get("issueKey")
            or ticket_data.get("key")
            or ticket_data.get("issue_key")
            or "unknown"
        )
        log.info("TestCaseGenerator.generate ticket=%s repo=%s model=%s", ticket_key, repo, embedding_model)

        query = self._build_query(ticket_data)
        model_key = _MODEL_KEY_MAP.get(embedding_model, "bge-m3")

        # 1. Semantic search
        semantic_hits = self._semantic_search(query, repo=repo, model_key=model_key, top_k=top_k)
        log.info("Semantic hits: %d", len(semantic_hits))

        # 2. Function call-graph context from semantic hits
        function_context = self._function_context_from_hits(semantic_hits)

        # 3. Files touched recently (keyword fallback / supplement)
        keywords = self._keywords(query)[:6]
        touched = self._files_touched_recently(keywords)

        # 4. Assemble context block
        context_block = self._build_context_block(semantic_hits, function_context, touched)

        # 5. LLM call
        ticket_text = self._ticket_as_text(ticket_data)
        user_message = _USER_TEMPLATE.format(
            schema=_GRAPH_SCHEMA_SUMMARY,
            ticket=ticket_text,
            context=context_block or "(no code context retrieved — answer from ticket alone)",
        )
        log.info("Calling LLM for test case generation (context_chars=%d)", len(context_block))
        test_cases_md = self.llm_client.complete(_SYSTEM_PROMPT, user_message)

        return {
            "test_cases": test_cases_md,
            "semantic_hits_count": len(semantic_hits),
            "functions_found": len(function_context),
            "files_touched_count": len(touched),
            "context_chars": len(context_block),
        }

    # ── repograph callers ─────────────────────────────────────────────────────

    def _semantic_search(
        self,
        query: str,
        *,
        repo: Optional[str],
        model_key: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        try:
            resp = requests.post(
                f"{self._base}/search/semantic",
                json={
                    "query": query,
                    "repos": [repo] if repo else None,
                    "top_k": top_k,
                    "model_key": model_key,
                },
                timeout=self._timeout,
            )
            if resp.status_code in {404, 501}:
                log.debug("repograph /search/semantic not available (%d)", resp.status_code)
                return []
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", []) if isinstance(data, dict) else []
        except requests.RequestException as exc:
            log.warning("Semantic search failed: %s", exc)
            return []

    def _callers_for_function(self, qualified_name: str) -> List[Dict[str, Any]]:
        try:
            resp = requests.get(
                f"{self._base}/functions/{qualified_name}/callers",
                timeout=self._timeout,
            )
            if resp.status_code in {404, 501}:
                return []
            resp.raise_for_status()
            data = resp.json()
            return data.get("callers", []) if isinstance(data, dict) else []
        except requests.RequestException as exc:
            log.debug("Callers fetch failed for %s: %s", qualified_name, exc)
            return []

    def _files_touched_recently(self, keywords: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for kw in keywords:
            try:
                resp = requests.get(
                    f"{self._base}/files/touched_recently",
                    params={"keyword": kw, "days": 180, "limit": 10},
                    timeout=self._timeout,
                )
                if resp.status_code in {404, 501}:
                    continue
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    for item in data[:5]:
                        item["keyword"] = kw
                        results.append(item)
            except requests.RequestException:
                pass
        return results

    # ── context assembly ──────────────────────────────────────────────────────

    def _function_context_from_hits(
        self, hits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """For every Function-kind hit, fetch its callers from the graph."""
        fn_context: List[Dict[str, Any]] = []
        seen_qn: set[str] = set()

        for hit in hits:
            if hit.get("kind") != "function":
                continue
            qn = hit.get("source_key") or ""
            if not qn or qn in seen_qn:
                continue
            seen_qn.add(qn)
            callers = self._callers_for_function(qn)
            fn_context.append({
                "qualified_name": qn,
                "title": hit.get("title", ""),
                "score": hit.get("score", 0),
                "text": (hit.get("text") or "")[:400],
                "callers": [c.get("name", "") for c in callers[:5]],
            })

        return fn_context

    def _build_context_block(
        self,
        hits: List[Dict[str, Any]],
        fn_context: List[Dict[str, Any]],
        touched: List[Dict[str, Any]],
    ) -> str:
        parts: List[str] = []

        if hits:
            parts.append("### Semantically Similar Code")
            for h in hits[:12]:
                score = h.get("score", 0)
                kind = h.get("kind", "?")
                title = h.get("title", "")
                text = (h.get("text") or "")[:500]
                parts.append(f"\n**[{kind}] {title}** (score={score:.3f})")
                if text:
                    parts.append(f"```\n{text}\n```")

        if fn_context:
            parts.append("\n### Function Call Graph")
            for fn in fn_context:
                callers_str = ", ".join(fn["callers"]) if fn["callers"] else "none"
                parts.append(
                    f"- **{fn['title']}** (score={fn['score']:.3f})\n"
                    f"  called_by: {callers_str}\n"
                    + (f"  snippet: {fn['text'][:200]}" if fn["text"] else "")
                )

        if touched:
            parts.append("\n### Recently Changed Files (keyword match)")
            seen_paths: set[str] = set()
            for f in touched[:15]:
                path = f.get("path", "")
                if path in seen_paths:
                    continue
                seen_paths.add(path)
                parts.append(
                    f"- `{path}` (repo={f.get('repo','?')}, "
                    f"touches={f.get('touch_count_180d','?')}, "
                    f"last={f.get('last_touched_at','?')[:10]}, "
                    f"keyword={f.get('keyword','')})"
                )

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

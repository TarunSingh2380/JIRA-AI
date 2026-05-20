"""Finds historically similar Jira tickets using semantic search + PostgreSQL fallback.

Pipeline
--------
1. Embed (summary + description) with Ollama
2. Search Qdrant `jira_tickets` collection filtered by status
3. Enrich hits with full details from PostgreSQL `jira_ticket_cache`
4. Fallback: keyword ILIKE search in PostgreSQL when Ollama is unavailable
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from app.config import Settings
from app.ollama_embedder import OllamaEmbedder
from app.qdrant_store import JIRA_COLLECTION

log = logging.getLogger(__name__)

_STOP_WORDS = {
    "about", "after", "again", "also", "before", "description",
    "from", "have", "into", "jira", "missing", "please",
    "reply", "should", "that", "them", "then", "there",
    "they", "this", "than", "ticket", "update", "when",
    "where", "which", "with",
}


class SimilarTicketFinder:
    """Orchestrates Qdrant semantic search and PostgreSQL enrichment."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # ── public entry point ────────────────────────────────────────────────────

    def find_similar(
        self,
        summary: str,
        description: Optional[str] = None,
        *,
        project_key: Optional[str] = None,
        top_k: int = 10,
        statuses: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return similar closed tickets ordered by similarity score."""
        if statuses is None:
            statuses = ["Done", "Closed", "Resolved"]

        # Mirror _ticket_embed_texts() in graph_job_runner.py exactly:
        # stored vector = summary[:200] + "\n" + description[:500]
        # Matching this format is what makes identical tickets score ~100%.
        query = f"{summary[:200]}\n{(description or '')[:500]}".strip()

        # 1. Try semantic search via Qdrant + Ollama
        hits, method = self._semantic_search(
            query, project_key=project_key, top_k=top_k * 2, statuses=statuses
        )

        # 2. Keyword fallback when Ollama / Qdrant unavailable
        if not hits:
            hits, method = self._keyword_search(
                query, project_key=project_key, top_k=top_k, statuses=statuses
            )
        else:
            # Enrich semantic hits with full PostgreSQL details
            hits = self._enrich_from_db(hits)

        hits = hits[:top_k]
        log.info(
            "SimilarTicketFinder: method=%s found=%d (statuses=%s project=%s)",
            method, len(hits), statuses, project_key,
        )
        return {
            "query_summary": summary,
            "total_found": len(hits),
            "search_method": method,
            "tickets": hits,
        }

    # ── semantic search ───────────────────────────────────────────────────────

    def _semantic_search(
        self,
        query: str,
        *,
        project_key: Optional[str],
        top_k: int,
        statuses: List[str],
    ) -> tuple[List[Dict[str, Any]], str]:
        embedder = OllamaEmbedder(
            base_url=self.settings.ollama_url,
            model=self.settings.ollama_embed_model,
            timeout_seconds=self.settings.ollama_embed_timeout_seconds,
        )
        if not embedder.is_available():
            log.warning("Ollama unavailable; skipping semantic search for similar tickets")
            return [], "keyword_fallback"

        vector = embedder.embed(query)
        if not vector:
            log.warning("Empty embedding returned for similar-ticket query")
            return [], "keyword_fallback"

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter, FieldCondition, MatchValue
        except ImportError:
            log.warning("qdrant-client not installed; skipping semantic search")
            return [], "keyword_fallback"

        try:
            client = QdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key or None,
            )

            must = []
            if project_key:
                must.append(FieldCondition(key="project_key", match=MatchValue(value=project_key)))

            # Try MatchAny for multi-value status filter; fall back to post-filter
            status_filter_applied = False
            if statuses:
                try:
                    from qdrant_client.models import MatchAny
                    must.append(FieldCondition(key="status", match=MatchAny(any=statuses)))
                    status_filter_applied = True
                except (ImportError, Exception):
                    pass  # will post-filter below

            search_filter = Filter(must=must) if must else None

            try:
                response = client.query_points(
                    collection_name=JIRA_COLLECTION,
                    query=vector,
                    limit=top_k,
                    query_filter=search_filter,
                    with_payload=True,
                )
                scored = response.points
            except AttributeError:
                scored = client.search(
                    collection_name=JIRA_COLLECTION,
                    query_vector=vector,
                    limit=top_k,
                    query_filter=search_filter,
                    with_payload=True,
                )

            results = []
            for r in scored:
                payload = r.payload or {}
                ticket_status = payload.get("status", "")
                if not status_filter_applied and statuses and ticket_status not in statuses:
                    continue
                results.append({
                    "ticket_key": payload.get("key", ""),
                    "project_key": payload.get("project_key", ""),
                    "summary": payload.get("summary", ""),
                    "status": ticket_status,
                    "issue_type": payload.get("issue_type", ""),
                    "similarity_score": round(r.score, 4),
                    # enriched fields filled in by _enrich_from_db
                    "description": None,
                    "priority": None,
                    "assignee_name": None,
                    "reporter_name": None,
                    "labels": [],
                    "created_at": None,
                    "updated_at": None,
                })

            log.info("Qdrant returned %d similar ticket hits", len(results))
            return results, "semantic"

        except Exception as exc:
            log.warning("Qdrant similar-ticket search failed: %s", exc)
            return [], "keyword_fallback"

    # ── PostgreSQL enrichment ─────────────────────────────────────────────────

    def _enrich_from_db(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch full ticket rows from PostgreSQL and merge into semantic hits."""
        if not self.settings.database_url or not hits:
            return hits

        keys = [h["ticket_key"] for h in hits if h.get("ticket_key")]
        if not keys:
            return hits

        try:
            import psycopg
            from psycopg.rows import dict_row

            with psycopg.connect(self.settings.database_url, row_factory=dict_row) as conn:
                rows = conn.execute(
                    """
                    SELECT ticket_key, project_key, summary, description,
                           status, issue_type, priority,
                           assignee_name, reporter_name, labels,
                           created_at, updated_at
                    FROM jira_ticket_cache
                    WHERE ticket_key = ANY(%s)
                    """,
                    (keys,),
                ).fetchall()

            db_map = {r["ticket_key"]: dict(r) for r in rows}
            enriched = []
            for hit in hits:
                key = hit.get("ticket_key", "")
                db = db_map.get(key, {})
                enriched.append({
                    **hit,
                    "description": db.get("description"),
                    "priority": db.get("priority"),
                    "assignee_name": db.get("assignee_name"),
                    "reporter_name": db.get("reporter_name"),
                    "labels": db.get("labels") or [],
                    "created_at": _fmt_dt(db.get("created_at")),
                    "updated_at": _fmt_dt(db.get("updated_at")),
                    # Override with DB values if Qdrant payload was partial
                    "status": db.get("status") or hit.get("status", ""),
                    "issue_type": db.get("issue_type") or hit.get("issue_type", ""),
                    "project_key": db.get("project_key") or hit.get("project_key", ""),
                    "summary": db.get("summary") or hit.get("summary", ""),
                })
            return enriched

        except Exception as exc:
            log.warning("PostgreSQL enrichment failed: %s", exc)
            return hits

    # ── PostgreSQL keyword fallback ───────────────────────────────────────────

    def _keyword_search(
        self,
        query: str,
        *,
        project_key: Optional[str],
        top_k: int,
        statuses: List[str],
    ) -> tuple[List[Dict[str, Any]], str]:
        if not self.settings.database_url:
            return [], "none"

        keywords = self._extract_keywords(query)[:6]
        if not keywords:
            return [], "none"

        try:
            import psycopg
            from psycopg.rows import dict_row

            where_parts = ["status = ANY(%s)"]
            params: list[Any] = [statuses]

            if project_key:
                where_parts.append("project_key = %s")
                params.append(project_key)

            kw_clause = " OR ".join(
                "(summary ILIKE %s OR description ILIKE %s)" for _ in keywords
            )
            where_parts.append(f"({kw_clause})")
            for kw in keywords:
                params.extend([f"%{kw}%", f"%{kw}%"])

            params.append(top_k)
            where = " AND ".join(where_parts)

            with psycopg.connect(self.settings.database_url, row_factory=dict_row) as conn:
                rows = conn.execute(
                    f"""
                    SELECT ticket_key, project_key, summary, description,
                           status, issue_type, priority,
                           assignee_name, reporter_name, labels,
                           created_at, updated_at
                    FROM jira_ticket_cache
                    WHERE {where}
                    ORDER BY updated_at DESC NULLS LAST
                    LIMIT %s
                    """,
                    params,
                ).fetchall()

            results = [
                {
                    **dict(r),
                    "similarity_score": 0.0,
                    "created_at": _fmt_dt(r.get("created_at")),
                    "updated_at": _fmt_dt(r.get("updated_at")),
                    "labels": r.get("labels") or [],
                }
                for r in rows
            ]
            log.info("PostgreSQL keyword fallback returned %d tickets", len(results))
            return results, "keyword_fallback"

        except Exception as exc:
            log.warning("PostgreSQL keyword search failed: %s", exc)
            return [], "none"

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
        seen: set[str] = set()
        out: List[str] = []
        for w in words:
            if w not in _STOP_WORDS and w not in seen:
                seen.add(w)
                out.append(w)
        return out


def _fmt_dt(val: Any) -> Optional[str]:
    """Serialize datetime / date objects to ISO strings."""
    if val is None:
        return None
    try:
        return val.isoformat()
    except AttributeError:
        return str(val)

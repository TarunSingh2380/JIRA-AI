"""AIGOV-scoped Workflow4 due-date batches.

Mirrors the standard 09:00 assignee / 15:00 TL batches in
:mod:`app.workflow4_due_date`, but restricted to the AIGOV sandbox project.

Each run additionally:
  1. Refetches the AIGOV tickets from Jira into ``jira_ticket_cache``
     (ignoring ``JIRA_EXCLUDED_PROJECT_KEYS``, which excludes AIGOV by default).
  2. Rebuilds their dense embeddings in Qdrant — the same fetch→embed pattern
     used by the graph ingest — best-effort, so a missing Ollama/Qdrant never
     blocks the alert.
  3. Summarizes the qualifying at-risk tickets through the configured LLM and
     sends that summary (rather than the raw template digest) to Slack via n8n.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from app.llm_client import build_llm_client
from app.workflow4_due_date import Workflow4AssigneeChecker, Workflow4TLChecker

LOGGER = logging.getLogger(__name__)

AIGOV_PROJECT_KEY = "AIGOV"

# due_date_tracking.priority is varchar(10) and production stores P0–P4 codes,
# so map the Jira priority *name* down to a code (empty when unknown).
_PRIORITY_NAME_TO_CODE = {
    "highest": "P0",
    "critical": "P0",
    "blocker": "P0",
    "high": "P1",
    "medium": "P2",
    "low": "P3",
    "lowest": "P4",
}


def _normalize_priority(raw: Any) -> str:
    """Coerce a Jira priority (name or code) into a P0–P4 code, capped to 10 chars."""
    value = str(raw or "").strip()
    if not value:
        return ""
    upper = value.upper()
    if upper in {"P0", "P1", "P2", "P3", "P4"}:
        return upper
    return _PRIORITY_NAME_TO_CODE.get(value.lower(), "")[:10]

_SUMMARY_SYSTEM_PROMPT = (
    "You are the AI Governor's due-date assistant. You are given a pre-formatted "
    "Slack digest of Jira tickets in the AIGOV project whose remaining time is "
    "running low. Rewrite it as a concise, well-structured Slack message using "
    "Slack mrkdwn. Open with a one-line situation summary, then keep one line per "
    "ticket. Preserve every ticket key, status, due date and browse URL exactly as "
    "given — do not invent or drop tickets, dates, statuses, or links."
)


# ── refetch + embed (best-effort) ───────────────────────────────────────────
def _refetch_and_embed_aigov() -> list[dict[str, Any]]:
    """Refresh the AIGOV ticket cache, rebuild embeddings best-effort, and return
    the fetched raw Jira issue dicts (empty list on failure)."""
    from app.jira_fetcher import fetch_project_tickets

    try:
        tickets = fetch_project_tickets(AIGOV_PROJECT_KEY, force_refresh=True)
    except Exception:
        LOGGER.exception("workflow4-aigov: AIGOV refetch failed (non-fatal)")
        return []

    LOGGER.info("workflow4-aigov: refetched %d AIGOV ticket(s)", len(tickets))
    if not tickets:
        return []

    try:
        _embed_tickets(tickets)
    except Exception:
        LOGGER.exception("workflow4-aigov: embedding step failed (non-fatal)")
    return tickets


def _embed_tickets(tickets: list[dict[str, Any]]) -> None:
    from app.config import settings as global_settings
    from app.graph_job_runner import _ticket_embed_texts
    from app.ollama_embedder import OllamaEmbedder
    from app.qdrant_store import upsert_jira_embeddings

    if not global_settings.qdrant_url:
        LOGGER.info("workflow4-aigov: QDRANT_URL not set; skipping embeddings")
        return

    embedder = OllamaEmbedder(
        global_settings.ollama_url,
        global_settings.ollama_embed_model,
        timeout_seconds=global_settings.ollama_embed_timeout_seconds,
        batch_size=global_settings.ollama_embed_batch_size,
        concurrency=global_settings.ollama_embed_concurrency,
    )
    if not embedder.is_available():
        LOGGER.warning("workflow4-aigov: Ollama unavailable; skipping embeddings")
        return

    texts = _ticket_embed_texts(tickets)
    embeddings = embedder.embed_batch(texts)
    stored = upsert_jira_embeddings(
        qdrant_url=global_settings.qdrant_url,
        tickets=tickets,
        embeddings=embeddings,
        api_key=global_settings.qdrant_api_key or None,
    )
    LOGGER.info("workflow4-aigov: stored %d AIGOV embedding(s) in Qdrant", stored)


# ── shared AIGOV behaviour ──────────────────────────────────────────────────
class _AigovFlowMixin:
    """Scopes a batch checker to AIGOV, refreshes data first, and routes each
    template digest through the LLM before it is sent."""

    project_key = AIGOV_PROJECT_KEY

    def _pre_check(self) -> None:
        tickets = _refetch_and_embed_aigov()
        try:
            self._enroll_aigov_tickets(tickets)
        except Exception:
            LOGGER.exception("workflow4-aigov: enrollment step failed (non-fatal)")

    def _enroll_aigov_tickets(self, tickets: list[dict[str, Any]]) -> None:
        """Auto-enroll fetched AIGOV tickets that carry a due date into
        ``due_date_tracking`` so the scan can alert on them.

        Unlike production (where workflow1/workflow3 own enrollment), the AIGOV
        sandbox enrolls straight from the Jira fetch. A minimal ``tickets`` row
        is upserted first to satisfy the ``due_date_tracking.ticket_id`` FK.
        The assignee→Slack mapping isn't resolved here, so ``assignee_slack_id``
        is left empty: per-assignee DMs won't fire, but the consolidated
        Governor (jira_owner) and TL (eng_lead) digests will."""
        if not tickets:
            return
        import psycopg2

        enrolled = 0
        with psycopg2.connect(self.settings.database_url) as conn:
            with conn.cursor() as cursor:
                for ticket in tickets:
                    key = str(ticket.get("key") or "")
                    if not key:
                        continue
                    try:
                        info = self._fetch_jira_phase(key)
                        if info.get("done"):
                            continue
                        due = (
                            info.get("system_due")
                            or info.get("dev_due")
                            or info.get("qa_due")
                            or info.get("live_due")
                        )
                        if due is None:
                            continue  # nothing to track without a due date

                        fields = ticket.get("fields", {}) or {}
                        tracking_start = (
                            self._parse_jira_date(fields.get("created")) or date.today()
                        )
                        total = self._count_working_days(tracking_start, due)
                        if total <= 0:
                            total = 1
                        priority = _normalize_priority((fields.get("priority") or {}).get("name"))

                        cursor.execute(
                            """
                            INSERT INTO tickets (jira_ticket_id, status)
                            VALUES (%s, 'open')
                            ON CONFLICT (jira_ticket_id)
                            DO UPDATE SET jira_ticket_id = EXCLUDED.jira_ticket_id
                            RETURNING id
                            """,
                            (key,),
                        )
                        ticket_row_id = cursor.fetchone()[0]

                        cursor.execute(
                            """
                            INSERT INTO due_date_tracking (
                                ticket_id, jira_ticket_id, priority, assignee_slack_id,
                                due_date, tracking_start_date, total_working_days
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (jira_ticket_id) DO UPDATE SET
                                due_date            = EXCLUDED.due_date,
                                tracking_start_date = EXCLUDED.tracking_start_date,
                                total_working_days  = EXCLUDED.total_working_days,
                                priority            = EXCLUDED.priority,
                                is_completed        = FALSE
                            """,
                            (ticket_row_id, key, priority, "", due, tracking_start, total),
                        )
                        conn.commit()
                        enrolled += 1
                    except Exception:
                        conn.rollback()
                        LOGGER.exception(
                            "workflow4-aigov: enroll failed for %s (skipping)", key
                        )
        LOGGER.info(
            "workflow4-aigov: enrolled/updated %d AIGOV ticket(s) in due_date_tracking",
            enrolled,
        )

    def _format_digest(
        self, title: str, items: list[dict[str, Any]], *, show_assignee: bool
    ) -> str:
        template = super()._format_digest(title, items, show_assignee=show_assignee)
        try:
            client = build_llm_client(self.settings)
            summary = client.complete(_SUMMARY_SYSTEM_PROMPT, template)
            return summary.strip() or template
        except Exception:
            LOGGER.exception(
                "workflow4-aigov: LLM summary failed; falling back to template digest"
            )
            return template


class Workflow4AigovAssigneeChecker(_AigovFlowMixin, Workflow4AssigneeChecker):
    """AIGOV 09:00 batch — under 75% time left."""

    name = "workflow4-aigov-daily-assignee"


class Workflow4AigovTLChecker(_AigovFlowMixin, Workflow4TLChecker):
    """AIGOV 15:00 batch — 50% or less time left."""

    name = "workflow4-aigov-tl"

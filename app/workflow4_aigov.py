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
from typing import Any

from app.llm_client import build_llm_client
from app.workflow4_due_date import Workflow4AssigneeChecker, Workflow4TLChecker

LOGGER = logging.getLogger(__name__)

AIGOV_PROJECT_KEY = "AIGOV"

_SUMMARY_SYSTEM_PROMPT = (
    "You are the AI Governor's due-date assistant. You are given a pre-formatted "
    "Slack digest of Jira tickets in the AIGOV project whose remaining time is "
    "running low. Rewrite it as a concise, well-structured Slack message using "
    "Slack mrkdwn. Open with a one-line situation summary, then keep one line per "
    "ticket. Preserve every ticket key, status, due date and browse URL exactly as "
    "given — do not invent or drop tickets, dates, statuses, or links."
)


# ── refetch + embed (best-effort) ───────────────────────────────────────────
def _refetch_and_embed_aigov() -> None:
    """Refresh the AIGOV ticket cache, then rebuild its embeddings best-effort."""
    from app.jira_fetcher import fetch_project_tickets

    try:
        tickets = fetch_project_tickets(AIGOV_PROJECT_KEY, force_refresh=True)
    except Exception:
        LOGGER.exception("workflow4-aigov: AIGOV refetch failed (non-fatal)")
        return

    LOGGER.info("workflow4-aigov: refetched %d AIGOV ticket(s)", len(tickets))
    if not tickets:
        return

    try:
        _embed_tickets(tickets)
    except Exception:
        LOGGER.exception("workflow4-aigov: embedding step failed (non-fatal)")


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
        _refetch_and_embed_aigov()

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

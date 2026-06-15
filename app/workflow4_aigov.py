"""Enriched Workflow4 due-date batches (production + AIGOV test).

Both the production 09:00/15:00 batches and the AIGOV sandbox variants share one
enrichment pipeline (:class:`_Workflow4SummaryMixin`): before the digest is sent
they refetch tickets, rebuild dense embeddings (best-effort), map each Story to
its child issues (assignee + dev/QA due dates), and rewrite the digest through
the LLM with that subtask breakdown nested under each Story.

  * Production (:class:`Workflow4SummaryAssigneeChecker` / ``…TLChecker``) runs
    across all spaces — story scope follows ``STORY_SUBTASK_PROJECT_KEYS``
    (blank = all visible projects minus ``JIRA_EXCLUDED_PROJECT_KEYS``).
  * AIGOV (:class:`Workflow4AigovAssigneeChecker` / ``…TLChecker``) is restricted
    to the AIGOV sandbox and additionally auto-enrolls fetched tickets into
    ``due_date_tracking`` (production relies on workflow1/workflow3 for that).
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from app.llm_client import build_llm_client
from app.workflow4_due_date import (
    DONE_STATUSES,
    Workflow4AssigneeChecker,
    Workflow4TLChecker,
)

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
    "Slack digest of Jira tickets whose remaining time is running low, optionally "
    "followed by a 'Subtask breakdown by Story' section listing each Story's child "
    "issues with assignee and dev/qa due dates. Rewrite it as a concise, "
    "well-structured Slack message using Slack mrkdwn. Open with a one-line "
    "situation summary, then keep one line per ticket. When a ticket is a Story "
    "that has a subtask breakdown, nest its child issues beneath it, calling out "
    "the assignee and any dev/qa due date that is overdue or at risk. Preserve "
    "every ticket/subtask key, status, due date and browse URL exactly as given — "
    "do not invent or drop tickets, dates, statuses, or links."
)


# ── embeddings (best-effort) ─────────────────────────────────────────────────
def _embed_tickets(tickets: list[dict[str, Any]]) -> None:
    from app.config import settings as global_settings
    from app.graph_job_runner import _ticket_embed_texts
    from app.ollama_embedder import OllamaEmbedder
    from app.qdrant_store import upsert_jira_embeddings

    if not global_settings.qdrant_url:
        LOGGER.info("workflow4-summary: QDRANT_URL not set; skipping embeddings")
        return

    embedder = OllamaEmbedder(
        global_settings.ollama_url,
        global_settings.ollama_embed_model,
        timeout_seconds=global_settings.ollama_embed_timeout_seconds,
        batch_size=global_settings.ollama_embed_batch_size,
        concurrency=global_settings.ollama_embed_concurrency,
    )
    if not embedder.is_available():
        LOGGER.warning("workflow4-summary: Ollama unavailable; skipping embeddings")
        return

    texts = _ticket_embed_texts(tickets)
    embeddings = embedder.embed_batch(texts)
    stored = upsert_jira_embeddings(
        qdrant_url=global_settings.qdrant_url,
        tickets=tickets,
        embeddings=embeddings,
        api_key=global_settings.qdrant_api_key or None,
    )
    LOGGER.info("workflow4-summary: stored %d embedding(s) in Qdrant", stored)


# ── shared enrichment: refetch + embed + map + LLM summary ───────────────────
class _Workflow4SummaryMixin:
    """Refetch tickets, rebuild embeddings, map Story→subtasks, and summarize the
    digest through the LLM. Production scope by default; subclasses override
    ``_fetch_tickets`` / hooks to narrow it."""

    # Production honours the cache TTL to avoid hammering Jira twice a day;
    # the AIGOV test flow forces a refresh for immediacy.
    summary_force_refresh: bool = False
    # Workflow4 is self-sufficient: it enrolls its own fetched tickets into
    # due_date_tracking rather than depending on workflow1/workflow3.
    auto_enroll: bool = True

    # Phase data ({key: {status, done, dev_due, qa_due, live_due, system_due}})
    # prefetched once per run via one JQL so enrollment + the scan don't make a
    # Jira call per ticket. None until _pre_check builds it.
    _phase_cache: dict[str, dict[str, Any]] | None = None

    def _build_embeddings_enabled(self) -> bool:
        """Embeddings are off by default in production (unused by the digest,
        and embedding every ticket per run blows the request budget). Toggle
        via WORKFLOW4_BUILD_EMBEDDINGS."""
        return bool(getattr(self.settings, "workflow4_build_embeddings", False))

    def _scope_jql(self) -> str:
        """JQL project clause for this checker's scope (empty = all projects)."""
        include = self._included_project_keys()
        if include:
            return "project in ({})".format(",".join(f'"{k}"' for k in include))
        excluded = self._excluded_project_keys()
        if excluded:
            return "project not in ({})".format(",".join(f'"{k}"' for k in excluded))
        return ""

    def _build_phase_cache(self) -> dict[str, dict[str, Any]]:
        """One paginated JQL over the scope (non-Done issues) returning each
        ticket's phase due dates — replaces per-ticket `_fetch_jira_phase` calls."""
        from app.jira_fetcher import _jira_get

        s = self.settings
        field_ids = ["status", "duedate"]
        for fid in (
            s.jira_dev_due_date_field,
            s.jira_qa_due_date_field,
            s.jira_live_due_date_field,
        ):
            if fid:
                field_ids.append(fid)

        scope = self._scope_jql()
        jql = (f"{scope} AND " if scope else "") + "statusCategory != Done ORDER BY updated DESC"

        cache: dict[str, dict[str, Any]] = {}
        start = 0
        next_token: str | None = None
        while True:
            params: dict[str, Any] = {
                "jql": jql,
                "maxResults": 100,
                "fields": ",".join(field_ids),
            }
            if next_token:
                params["nextPageToken"] = next_token
            else:
                params["startAt"] = start

            data = _jira_get("/rest/api/3/search/jql", params)
            batch = data.get("issues", [])
            for issue in batch:
                key = str(issue.get("key") or "")
                if not key:
                    continue
                f = issue.get("fields", {}) or {}
                status = ((f.get("status") or {}).get("name")) or ""
                cache[key] = {
                    "status": status,
                    "done": status in DONE_STATUSES,
                    "dev_due": self._parse_jira_date(f.get(s.jira_dev_due_date_field))
                    if s.jira_dev_due_date_field else None,
                    "qa_due": self._parse_jira_date(f.get(s.jira_qa_due_date_field))
                    if s.jira_qa_due_date_field else None,
                    "live_due": self._parse_jira_date(f.get(s.jira_live_due_date_field))
                    if s.jira_live_due_date_field else None,
                    "system_due": self._parse_jira_date(f.get("duedate")),
                }
            start += len(batch)
            next_token = data.get("nextPageToken")
            if data.get("isLast") is True:
                break
            if next_token:
                continue
            total = data.get("total")
            if total is not None and start >= total:
                break
            if not batch:
                break

        LOGGER.info("workflow4-summary: prefetched phase data for %d ticket(s)", len(cache))
        return cache

    def _fetch_jira_phase(self, jira_ticket_id: str) -> dict[str, Any]:
        # Serve from the per-run bulk cache; fall back to a live call for keys
        # not covered (e.g. a now-Done ticket excluded by the cache JQL).
        cache = getattr(self, "_phase_cache", None)
        if cache and jira_ticket_id in cache:
            return cache[jira_ticket_id]
        return super()._fetch_jira_phase(jira_ticket_id)

    def _fetch_tickets(self) -> list[dict[str, Any]]:
        from app.jira_fetcher import fetch_all_tickets, fetch_project_tickets

        include = self._included_project_keys()
        if include:
            tickets: list[dict[str, Any]] = []
            for key in include:
                tickets.extend(
                    fetch_project_tickets(key, force_refresh=self.summary_force_refresh)
                )
            return tickets
        return fetch_all_tickets(force_refresh=self.summary_force_refresh)

    def _mapping_project_keys(self) -> list[str] | None:
        """Story-mapping scope for this checker. Production honours
        WORKFLOW4_PROJECT_KEYS; None lets map_and_store fall back to
        STORY_SUBTASK_PROJECT_KEYS / all-spaces."""
        return self._included_project_keys() or None

    def _pre_check(self) -> None:
        try:
            self._phase_cache = self._build_phase_cache()
        except Exception:
            LOGGER.exception("workflow4-summary: phase prefetch failed (non-fatal)")
            self._phase_cache = {}

        try:
            tickets = self._fetch_tickets()
        except Exception:
            LOGGER.exception("workflow4-summary: refetch failed (non-fatal)")
            tickets = []
        LOGGER.info("workflow4-summary: refetched %d ticket(s)", len(tickets))

        if tickets and self._build_embeddings_enabled():
            try:
                _embed_tickets(tickets)
            except Exception:
                LOGGER.exception("workflow4-summary: embedding step failed (non-fatal)")

        self._extra_pre_check(tickets)

        try:
            from app.story_subtasks import map_and_store

            map_and_store(self.settings, project_keys=self._mapping_project_keys())
        except Exception:
            LOGGER.exception("workflow4-summary: story→subtask mapping failed (non-fatal)")

    def _extra_pre_check(self, tickets: list[dict[str, Any]]) -> None:
        """Auto-enroll fetched tickets (both production and AIGOV) so Workflow4
        is independent of workflow1/workflow3."""
        if not self.auto_enroll:
            return
        try:
            self._enroll_tickets(tickets)
        except Exception:
            LOGGER.exception("%s: enrollment step failed (non-fatal)", self.name)

    def _enroll_tickets(self, tickets: list[dict[str, Any]]) -> None:
        """Enroll fetched tickets that carry a due date (and aren't Done) into
        ``due_date_tracking`` so the scan can alert on them.

        A minimal ``tickets`` row is upserted first to satisfy the
        ``due_date_tracking.ticket_id`` FK. The assignee→Slack mapping isn't
        resolved here, so ``assignee_slack_id`` is left empty: per-assignee DMs
        won't fire, but the consolidated Governor (jira_owner) and TL (eng_lead)
        digests will."""
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
                        LOGGER.exception("%s: enroll failed for %s (skipping)", self.name, key)
        LOGGER.info(
            "%s: enrolled/updated %d ticket(s) in due_date_tracking", self.name, enrolled
        )

    def _format_digest(
        self, title: str, items: list[dict[str, Any]], *, show_assignee: bool
    ) -> str:
        template = super()._format_digest(title, items, show_assignee=show_assignee)
        prompt_input = template + self._subtask_breakdown(items)
        try:
            client = build_llm_client(self.settings)
            summary = client.complete(_SUMMARY_SYSTEM_PROMPT, prompt_input)
            return summary.strip() or template
        except Exception:
            LOGGER.exception(
                "workflow4-summary: LLM summary failed; falling back to template digest"
            )
            return template

    def _subtask_breakdown(self, items: list[dict[str, Any]]) -> str:
        """Append each digest Story's stored subtask breakdown for the LLM."""
        try:
            from app.story_subtasks import format_breakdown, get_subtasks_for_stories

            keys = [str(i.get("key") or "") for i in items if i.get("key")]
            grouped = get_subtasks_for_stories(self.settings, keys)
            return format_breakdown(grouped)
        except Exception:
            LOGGER.exception("workflow4-summary: subtask breakdown failed (non-fatal)")
            return ""


# ── production (all spaces) ──────────────────────────────────────────────────
class Workflow4SummaryAssigneeChecker(_Workflow4SummaryMixin, Workflow4AssigneeChecker):
    """Production 09:00 batch — under 75% time left, enriched + summarized."""

    name = "workflow4-summary-daily-assignee"


class Workflow4SummaryTLChecker(_Workflow4SummaryMixin, Workflow4TLChecker):
    """Production 15:00 batch — 50% or less time left, enriched + summarized."""

    name = "workflow4-summary-tl"


# ── AIGOV sandbox (test scope + auto-enroll) ─────────────────────────────────
class _AigovFlowMixin(_Workflow4SummaryMixin):
    """Restrict the enriched flow to the AIGOV sandbox. Auto-enrollment is
    inherited from the shared mixin (Workflow4 is self-sufficient)."""

    project_key = AIGOV_PROJECT_KEY
    summary_force_refresh = True

    def _build_embeddings_enabled(self) -> bool:
        # AIGOV is a small sandbox — keep embeddings on for parity with the
        # original test flow regardless of the production toggle.
        return True

    def _scope_jql(self) -> str:
        return f'project = "{AIGOV_PROJECT_KEY}"'

    def _fetch_tickets(self) -> list[dict[str, Any]]:
        from app.jira_fetcher import fetch_project_tickets

        return fetch_project_tickets(AIGOV_PROJECT_KEY, force_refresh=True)

    def _mapping_project_keys(self) -> list[str] | None:
        return [AIGOV_PROJECT_KEY]


class Workflow4AigovAssigneeChecker(_AigovFlowMixin, Workflow4AssigneeChecker):
    """AIGOV 09:00 batch — under 75% time left."""

    name = "workflow4-aigov-daily-assignee"


class Workflow4AigovTLChecker(_AigovFlowMixin, Workflow4TLChecker):
    """AIGOV 15:00 batch — 50% or less time left."""

    name = "workflow4-aigov-tl"

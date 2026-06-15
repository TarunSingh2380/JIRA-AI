"""Enriched Workflow4 due-date batches (production + AIGOV test).

Both the production 09:00/15:00 batches and the AIGOV sandbox variants share one
enrichment pipeline (:class:`_Workflow4SummaryMixin`): before the digest is sent
they refetch tickets, rebuild dense embeddings (best-effort), map each Story to
its child issues (assignee + dev/QA due dates), and emit a deterministic tabular
report to the Jira Owner + TL channels — Stories banded by their own due date
(Overdue / 75% / 50% / 25% time left), plus a section for independent tasks.

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

import requests

from app.workflow4_due_date import (
    DONE_STATUSES,
    Workflow4AssigneeChecker,
    Workflow4TLChecker,
)

LOGGER = logging.getLogger(__name__)

AIGOV_PROJECT_KEY = "AIGOV"

# Per-table row cap so a large project can't blow the Slack message size limit.
_MAX_TABLE_ROWS = 40

# Story time-left bands, rendered in this order (label shown in the message).
_BAND_ORDER = [
    ("overdue", "a. Overdue"),
    ("75", "b. 75% time left"),
    ("50", "c. 50% time left"),
    ("25", "d. 25% time left"),
]

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
        field_ids = ["status", "duedate", "created", "priority", "issuetype", "assignee"]
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
                    "created": self._parse_jira_date(f.get("created")),
                    "priority": (f.get("priority") or {}).get("name"),
                    "issuetype": (f.get("issuetype") or {}).get("name"),
                    "assignee_name": (f.get("assignee") or {}).get("displayName"),
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

    _DONE_PHASE = {
        "status": "",
        "done": True,
        "dev_due": None,
        "qa_due": None,
        "live_due": None,
        "system_due": None,
    }

    def _fetch_jira_phase(self, jira_ticket_id: str) -> dict[str, Any]:
        # Serve from the per-run bulk cache; fall back to a live call only for
        # keys not covered (e.g. an already-enrolled ticket that is now Done or
        # was deleted). A 404 means the issue is gone → treat as Done so the
        # scan completes/skips it instead of erroring.
        cache = getattr(self, "_phase_cache", None)
        if cache and jira_ticket_id in cache:
            return cache[jira_ticket_id]
        try:
            return super()._fetch_jira_phase(jira_ticket_id)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                LOGGER.info(
                    "%s: %s not found in Jira (404); treating as Done",
                    self.name,
                    jira_ticket_id,
                )
                return dict(self._DONE_PHASE)
            raise

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

        # The mirror fetch + embeddings are only needed when embeddings are on;
        # enrollment and the scan both read the phase cache, not the mirror.
        if self._build_embeddings_enabled():
            try:
                tickets = self._fetch_tickets()
                if tickets:
                    _embed_tickets(tickets)
            except Exception:
                LOGGER.exception("workflow4-summary: refetch/embed failed (non-fatal)")

        if self.auto_enroll:
            try:
                self._enroll_tickets()
            except Exception:
                LOGGER.exception("%s: enrollment step failed (non-fatal)", self.name)

        try:
            from app.story_subtasks import map_and_store

            map_and_store(self.settings, project_keys=self._mapping_project_keys())
        except Exception:
            LOGGER.exception("workflow4-summary: story→subtask mapping failed (non-fatal)")

    def _enroll_tickets(self) -> None:
        """Enroll every phase-cached ticket that has a due date into
        ``due_date_tracking`` so the scan can alert on it.

        Driven by the per-run phase cache (current, in-scope, non-Done tickets),
        so there are no per-ticket Jira calls and no stale/deleted keys. A
        minimal ``tickets`` row is upserted first for the
        ``due_date_tracking.ticket_id`` FK; ``assignee_slack_id`` is left empty,
        so alerts route via the Governor/TL digests, not per-assignee DMs."""
        cache = getattr(self, "_phase_cache", None) or {}
        if not cache:
            return
        import psycopg2

        enrolled = 0
        with psycopg2.connect(self.settings.database_url) as conn:
            with conn.cursor() as cursor:
                for key, info in cache.items():
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
                    try:
                        tracking_start = info.get("created") or date.today()
                        total = self._count_working_days(tracking_start, due)
                        if total <= 0:
                            total = 1
                        priority = _normalize_priority(info.get("priority"))

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

    # ── deterministic tabular digest (Jira Owner + TL) ──────────────────────
    def _build_digests(
        self, qualifying: list[dict[str, Any]], role_channels: dict[str, str | None]
    ) -> list[dict[str, str]]:
        """Build ONE banded, tabular report and send it to the Jira Owner
        (jira_owner) and TL (eng_lead) channels. Replaces the per-assignee /
        per-recipient digests and the LLM rewrite. `qualifying` is ignored —
        the report is built from the phase cache + story_subtasks mapping."""
        try:
            message = self._build_tabular_message()
        except Exception:
            LOGGER.exception("workflow4-summary: tabular digest build failed")
            return []
        if not message:
            return []
        channels: list[str] = []
        for role in ("jira_owner", "eng_lead"):
            channel = role_channels.get(role)
            if channel and channel not in channels:
                channels.append(channel)
        return [{"channel_id": channel, "message": message} for channel in channels]

    @staticmethod
    def _effective_due(entry: dict[str, Any]) -> Any:
        """The due date that governs a ticket: system `duedate`, else the first
        non-null phase date."""
        return (
            entry.get("system_due")
            or entry.get("dev_due")
            or entry.get("qa_due")
            or entry.get("live_due")
        )

    def _time_left(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        """Working-day time-left for a cached ticket, from its own due date.
        Returns None when the ticket has no due date (undated)."""
        due = self._effective_due(entry)
        if due is None:
            return None
        today = date.today()
        start = entry.get("created") or today
        total = self._count_working_days(start, due)
        remaining = 0 if today > due else self._count_working_days(today, due)
        pct = 0.0 if total <= 0 else max(0.0, min(100.0, remaining / total * 100))
        return {"due": due, "remaining": remaining, "pct": pct}

    @staticmethod
    def _band(remaining: int, pct: float) -> str | None:
        """Bucket a ticket into a time-left band, or None if not at risk (>75%)."""
        if remaining <= 0:
            return "overdue"
        if pct <= 25:
            return "25"
        if pct <= 50:
            return "50"
        if pct <= 75:
            return "75"
        return None

    @staticmethod
    def _subtask_due(row: dict[str, Any]) -> Any:
        return (
            row.get("system_due_date")
            or row.get("dev_due_date")
            or row.get("qa_due_date")
        )

    @staticmethod
    def _format_table(headers: list[str], rows: list[list[Any]]) -> str:
        """Render an aligned monospace table inside a Slack code block."""
        str_rows = [["" if c is None else str(c) for c in r] for r in rows]
        widths = [len(h) for h in headers]
        for r in str_rows:
            for i, cell in enumerate(r):
                widths[i] = max(widths[i], len(cell))
        line = lambda r: "  ".join(c.ljust(widths[i]) for i, c in enumerate(r))
        return "```\n" + "\n".join([line(headers)] + [line(r) for r in str_rows]) + "\n```"

    def _build_tabular_message(self) -> str | None:
        """Compose the banded Story tables + independent-task table. Returns
        None when nothing is at risk (so no Slack message is sent)."""
        from app.story_subtasks import get_all_subtasks

        cache = getattr(self, "_phase_cache", None) or {}
        scope = self._mapping_project_keys()
        grouped = get_all_subtasks(self.settings, scope)

        bands: dict[str, list[list[Any]]] = {"overdue": [], "75": [], "50": [], "25": []}
        undated: list[list[Any]] = []
        subtask_keys: set[str] = set()

        for story_key, rows in grouped.items():
            for r in rows:
                subtask_keys.add(r["subtask_key"])
            entry = cache.get(story_key)
            if entry is None or entry.get("done"):
                continue  # Story is Done or out of scope
            story_rows = [
                [
                    story_key,
                    r["subtask_key"],
                    r.get("status") or "—",
                    str(self._subtask_due(r) or "—"),
                    r.get("assignee_name") or "Unassigned",
                ]
                for r in rows
            ]
            tl = self._time_left(entry)
            if tl is None:
                undated.extend(story_rows)
                continue
            band = self._band(tl["remaining"], tl["pct"])
            if band is not None:
                bands[band].extend(story_rows)

        # Independent tasks: in scope, not a Story, not a child of any Story.
        story_keys = set(grouped.keys())
        independent: list[list[Any]] = []
        for key, entry in cache.items():
            if key in story_keys or key in subtask_keys:
                continue
            if str(entry.get("issuetype") or "").strip().lower() == "story":
                continue
            tl = self._time_left(entry)
            if tl is None or self._band(tl["remaining"], tl["pct"]) is None:
                continue
            independent.append(
                [key, entry.get("status") or "—", str(tl["due"]), entry.get("assignee_name") or "Unassigned"]
            )

        total = sum(len(v) for v in bands.values()) + len(undated) + len(independent)
        if total == 0:
            return None

        scope_label = ", ".join(scope) if scope else "all spaces"
        story_headers = ["Story", "Task", "State", "Due", "Assignee"]
        parts = [
            f"*Due-Date Compliance — {scope_label} — {date.today():%Y-%m-%d}*",
            "",
            "*1. Stories*",
        ]
        for band_key, label in _BAND_ORDER:
            rows = bands[band_key]
            parts.append(f"\n*{label}* ({len(rows)})")
            if rows:
                parts.append(self._format_table(story_headers, rows[:_MAX_TABLE_ROWS]))
                if len(rows) > _MAX_TABLE_ROWS:
                    parts.append(f"_…and {len(rows) - _MAX_TABLE_ROWS} more_")
            else:
                parts.append("_none_")
        if undated:
            parts.append(f"\n*e. No due date on Story* ({len(undated)})")
            parts.append(self._format_table(story_headers, undated[:_MAX_TABLE_ROWS]))
            if len(undated) > _MAX_TABLE_ROWS:
                parts.append(f"_…and {len(undated) - _MAX_TABLE_ROWS} more_")

        parts.append("\n*2. Independent Tasks (not under any Story)*")
        if independent:
            parts.append(
                self._format_table(["Task", "State", "Due", "Assignee"], independent[:_MAX_TABLE_ROWS])
            )
            if len(independent) > _MAX_TABLE_ROWS:
                parts.append(f"_…and {len(independent) - _MAX_TABLE_ROWS} more_")
        else:
            parts.append("_none_")

        return "\n".join(parts)


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

"""RFT estimate report (Workflow 7).

Finds open RFT tickets that have a Jira **Original Estimate** filled and builds
a single Slack digest for the governor channel, returned in the shared
``AlertBatchResponse`` shape (``{"alerts": [...], "alerts_sent": N}``) that the
WF7 Split-Alerts → Slack nodes already consume.

The Jira ticket cache does not store time-tracking, so this queries Jira live
via the project-scoped ``/rest/api/3/search/jql`` endpoint, requests the
``timetracking`` field, and filters in Python on ``originalEstimateSeconds``
(robust — no reliance on a JQL estimate field name that may differ per
instance). Scope is ``statusCategory != Done``.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import Settings
from app import jira_fetcher

LOGGER = logging.getLogger(__name__)

_FIELDS = "summary,status,issuetype,assignee,priority,timetracking,timeoriginalestimate"


def _fmt_estimate(seconds: int, pretty: str) -> str:
    """Prefer Jira's own pretty string ('2d 4h'); else derive from seconds."""
    if pretty:
        return pretty
    if not seconds:
        return ""
    # Jira working day = 8h, working week = 5d (Jira defaults).
    units = [("w", 5 * 8 * 3600), ("d", 8 * 3600), ("h", 3600), ("m", 60)]
    parts: list[str] = []
    remaining = int(seconds)
    for label, size in units:
        if remaining >= size:
            qty, remaining = divmod(remaining, size)
            parts.append(f"{qty}{label}")
    return " ".join(parts) or f"{seconds}s"


def _fetch_estimated_tickets(settings: Settings) -> list[dict[str, Any]]:
    project = (settings.rft_estimate_project_key or "RFT").strip()
    jql = f'project = "{project}" AND statusCategory != Done ORDER BY created DESC'

    tickets: list[dict[str, Any]] = []
    start = 0
    next_page_token: str | None = None

    while True:
        params: dict[str, Any] = {"jql": jql, "maxResults": 100, "fields": _FIELDS}
        if next_page_token:
            params["nextPageToken"] = next_page_token
        else:
            params["startAt"] = start

        data = jira_fetcher._jira_get("/rest/api/3/search/jql", params)
        batch = data.get("issues", []) or []

        for issue in batch:
            fields = issue.get("fields", {}) or {}
            tracking = fields.get("timetracking") or {}
            seconds = (
                tracking.get("originalEstimateSeconds")
                or fields.get("timeoriginalestimate")
                or 0
            )
            if not seconds:
                continue
            assignee = fields.get("assignee") or {}
            tickets.append(
                {
                    "key": issue.get("key", ""),
                    "summary": (fields.get("summary") or "").strip(),
                    "status": (fields.get("status") or {}).get("name", ""),
                    "issue_type": (fields.get("issuetype") or {}).get("name", ""),
                    "assignee": assignee.get("displayName") or "Unassigned",
                    "estimate_seconds": int(seconds),
                    "estimate": _fmt_estimate(
                        int(seconds), (tracking.get("originalEstimate") or "").strip()
                    ),
                }
            )

        start += len(batch)
        next_page_token = data.get("nextPageToken")
        if data.get("isLast") is True:
            break
        if next_page_token:
            continue
        total = data.get("total")
        if total is not None and start >= total:
            break
        if not batch:
            break

    # Largest estimate first.
    tickets.sort(key=lambda t: t["estimate_seconds"], reverse=True)
    return tickets


def _link(settings: Settings, key: str) -> str:
    base = settings.jira_base_url
    return f"<{base}/browse/{key}|{key}>" if base else key


def _build_message(settings: Settings, tickets: list[dict[str, Any]]) -> str:
    project = (settings.rft_estimate_project_key or "RFT").strip()
    if not tickets:
        return f":bar_chart: *{project} tickets with an Original Estimate (open)* — none found."

    cap = max(1, settings.rft_estimate_max_rows)
    shown = tickets[:cap]
    lines = [
        f":bar_chart: *{project} tickets with an Original Estimate (open)* — "
        f"{len(tickets)} ticket{'s' if len(tickets) != 1 else ''}",
    ]
    for t in shown:
        lines.append(
            f"• {_link(settings, t['key'])} · {t['summary'][:90]} · "
            f"*{t['estimate']}* · {t['assignee']} · _{t['status']}_"
        )
    if len(tickets) > cap:
        lines.append(f"…and {len(tickets) - cap} more")
    return "\n".join(lines)


def build_rft_estimate_report(settings: Settings) -> dict[str, Any]:
    channel_id = (settings.governor_notify_channel_id or "").strip()
    if not channel_id:
        LOGGER.warning("rft-estimates: GOVERNOR_NOTIFY_CHANNEL_ID not set; no alert produced")
        return {"alerts": [], "alerts_sent": 0}
    if not all([settings.jira_base_url, settings.jira_email, settings.jira_api_token]):
        raise RuntimeError("JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN are required")

    tickets = _fetch_estimated_tickets(settings)
    LOGGER.info("rft-estimates: %d open tickets with an original estimate", len(tickets))
    message = _build_message(settings, tickets)
    return {
        "alerts": [{"channel_id": channel_id, "message": message}],
        "alerts_sent": 1,
        "ticket_count": len(tickets),
    }

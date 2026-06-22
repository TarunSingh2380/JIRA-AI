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
from app.app_settings import get_setting

LOGGER = logging.getLogger(__name__)

_FIELDS = "summary,status,issuetype,assignee,priority,timetracking,timeoriginalestimate"

# Admin-editable setting key. Value semantics:
#   "open"  → sprint in openSprints()  (current/active sprint)
#   "<id>"  → sprint = <id>            (a specific sprint, e.g. "284")
#   "all"   → no sprint filter         (whole project)
SPRINT_SETTING_KEY = "rft_estimate_sprint"


def resolve_sprint_value(settings: Settings) -> str:
    """Effective sprint selection: DB setting wins, else env config."""
    stored = get_setting(settings, SPRINT_SETTING_KEY)
    if stored is not None and stored.strip():
        return stored.strip()
    if (settings.rft_estimate_sprint_id or "").strip():
        return settings.rft_estimate_sprint_id.strip()
    return "open" if settings.rft_estimate_current_sprint_only else "all"


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


def _sprint_clause(settings: Settings) -> str:
    """JQL fragment restricting to the selected sprint, or '' for no restriction."""
    value = resolve_sprint_value(settings)
    if value in ("all", "none", ""):
        return ""
    if value == "open":
        return "sprint in openSprints()"
    if value.isdigit():
        return f"sprint = {value}"
    # Unknown value — be safe and don't filter.
    return ""


def _fetch_estimated_tickets(settings: Settings) -> list[dict[str, Any]]:
    project = (settings.rft_estimate_project_key or "RFT").strip()
    clauses = [f'project = "{project}"', "statusCategory != Done"]
    sprint_clause = _sprint_clause(settings)
    if sprint_clause:
        clauses.append(sprint_clause)
    jql = " AND ".join(clauses) + " ORDER BY created DESC"

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


def _scope_label(settings: Settings) -> str:
    value = resolve_sprint_value(settings)
    if value == "open":
        return "open, current sprint"
    if value.isdigit():
        return f"open, sprint {value}"
    return "open"


def _build_message(settings: Settings, tickets: list[dict[str, Any]]) -> str:
    project = (settings.rft_estimate_project_key or "RFT").strip()
    scope = _scope_label(settings)
    if not tickets:
        return f":bar_chart: *{project} tickets with an Original Estimate ({scope})* — none found."

    cap = max(1, settings.rft_estimate_max_rows)
    shown = tickets[:cap]
    lines = [
        f":bar_chart: *{project} tickets with an Original Estimate ({scope})* — "
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


# ── admin: current sprint selection + available sprints ──────────────────────
def get_sprint_setting(settings: Settings) -> dict[str, Any]:
    """Current sprint selection for the admin UI."""
    value = resolve_sprint_value(settings)
    return {
        "value": value,
        "scope_label": _scope_label(settings),
        "jql_clause": _sprint_clause(settings),
        "project_key": (settings.rft_estimate_project_key or "RFT").strip(),
    }


def list_rft_sprints(settings: Settings) -> dict[str, Any]:
    """Active + future sprints across the project's boards (Jira Agile API).

    Always returns the synthetic 'current' and 'all' choices; the concrete
    sprint list degrades to empty (with an error note) if the Agile API or
    boards are unavailable, so the dropdown still offers manual id entry.
    """
    project = (settings.rft_estimate_project_key or "RFT").strip()
    options: list[dict[str, Any]] = [
        {"value": "open", "label": "Current sprint (active / open)"},
    ]
    error: str | None = None
    if not all([settings.jira_base_url, settings.jira_email, settings.jira_api_token]):
        error = "Jira is not configured"
    else:
        try:
            seen: set[str] = set()
            for board in _fetch_boards(project):
                board_id = board.get("id")
                board_name = board.get("name", "")
                if board_id is None:
                    continue
                for sprint in _fetch_board_sprints(board_id):
                    sid = str(sprint.get("id"))
                    if sid in seen:
                        continue
                    seen.add(sid)
                    state = sprint.get("state", "")
                    options.append(
                        {
                            "value": sid,
                            "label": f"{sprint.get('name', sid)} · {state} · {board_name}",
                            "state": state,
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("list_rft_sprints failed: %s", exc)
            error = str(exc)

    options.append({"value": "all", "label": "All sprints (no filter)"})
    return {"project_key": project, "options": options, "error": error}


def _fetch_boards(project: str) -> list[dict[str, Any]]:
    boards: list[dict[str, Any]] = []
    start = 0
    while True:
        data = jira_fetcher._jira_get(
            "/rest/agile/1.0/board",
            {"projectKeyOrId": project, "maxResults": 50, "startAt": start},
        )
        values = data.get("values", []) or []
        boards.extend(values)
        if data.get("isLast", True) or not values:
            break
        start += len(values)
    return boards


def _fetch_board_sprints(board_id: Any) -> list[dict[str, Any]]:
    sprints: list[dict[str, Any]] = []
    start = 0
    while True:
        try:
            data = jira_fetcher._jira_get(
                f"/rest/agile/1.0/board/{board_id}/sprint",
                {"state": "active,future", "maxResults": 50, "startAt": start},
            )
        except Exception as exc:  # noqa: BLE001 - some boards (kanban) have no sprints
            LOGGER.debug("board %s sprint fetch skipped: %s", board_id, exc)
            break
        values = data.get("values", []) or []
        sprints.extend(values)
        if data.get("isLast", True) or not values:
            break
        start += len(values)
    return sprints

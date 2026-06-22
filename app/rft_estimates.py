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

_FIELDS = "summary,status,issuetype,assignee,priority,parent,timetracking,timeoriginalestimate"

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

    # Skip tickets at or below the minimum estimate (too small to analyze).
    min_seconds = int(round(max(0.0, settings.rft_estimate_min_hours) * 3600))

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
            if not seconds or int(seconds) <= min_seconds:
                continue
            assignee = fields.get("assignee") or {}
            parent = fields.get("parent") or {}
            tickets.append(
                {
                    "key": issue.get("key", ""),
                    "summary": (fields.get("summary") or "").strip(),
                    "status": (fields.get("status") or {}).get("name", ""),
                    "issue_type": (fields.get("issuetype") or {}).get("name", ""),
                    "assignee": assignee.get("displayName") or "Unassigned",
                    "parent_key": parent.get("key") or "",
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

    if not tickets:
        return {
            "alerts": [{"channel_id": channel_id, "message": _build_message(settings, [])}],
            "alerts_sent": 1,
            "ticket_count": 0,
        }

    if settings.rft_estimate_analyze:
        from app.rft_estimate_analysis import analyze_tickets

        stats = analyze_tickets(settings, tickets)
        LOGGER.info("rft-estimates: analyzed=%(analyzed)s flagged=%(flagged)s llm=%(llm)s", stats)
        alerts = _build_analysis_alerts(settings, channel_id, tickets, stats)
    else:
        alerts = [{"channel_id": channel_id, "message": _build_message(settings, tickets)}]

    return {
        "alerts": alerts,
        "alerts_sent": len(alerts),
        "ticket_count": len(tickets),
    }


# ── hierarchical Story → Task analysis report (multi-part, chunked) ──────────
_CHAR_BUDGET = 2800


def _fmt_delta(pct: Any) -> str:
    if pct is None:
        return "—"
    return f"+{pct}%" if pct >= 0 else f"{pct}%"


def _is_story(t: dict[str, Any] | None) -> bool:
    return bool(t) and (t.get("issue_type") or "").lower() == "story"


def _fetch_parent_meta(settings: Settings, keys: list[str]) -> dict[str, dict[str, Any]]:
    """Batch lookup of summary + issue type for parent keys not in the set."""
    meta: dict[str, dict[str, Any]] = {}
    chunk = 80
    for i in range(0, len(keys), chunk):
        batch = keys[i : i + chunk]
        jql = "key in (" + ",".join(batch) + ")"
        try:
            data = jira_fetcher._jira_get(
                "/rest/api/3/search/jql",
                {"jql": jql, "maxResults": chunk, "fields": "summary,issuetype"},
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("parent meta fetch failed: %s", exc)
            continue
        for issue in data.get("issues", []) or []:
            fields = issue.get("fields", {}) or {}
            meta[issue.get("key", "")] = {
                "summary": (fields.get("summary") or "").strip(),
                "issue_type": (fields.get("issuetype") or {}).get("name", ""),
            }
    return meta


def _resolve_groups(
    settings: Settings, tickets: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Group analyzed tickets under their parent Story.

    Returns (story_groups, other_tasks). A group = {key, summary, ticket (the
    Story's own analyzed row or None), children:[...]}. Parent Stories not in
    the set are fetched (summary + type) so they can still head a group.
    """
    by_key = {t["key"]: t for t in tickets}
    missing = sorted(
        {t["parent_key"] for t in tickets if t.get("parent_key") and t["parent_key"] not in by_key}
    )
    parent_meta = _fetch_parent_meta(settings, missing) if missing else {}

    def is_story_key(key: str) -> bool:
        if key in by_key:
            return _is_story(by_key[key])
        meta = parent_meta.get(key)
        return bool(meta and (meta.get("issue_type") or "").lower() == "story")

    def summary_of(key: str) -> str:
        if key in by_key:
            return by_key[key].get("summary", "")
        return (parent_meta.get(key) or {}).get("summary", "")

    groups: dict[str, dict[str, Any]] = {}

    def ensure_group(key: str) -> dict[str, Any]:
        if key not in groups:
            groups[key] = {
                "key": key,
                "summary": summary_of(key),
                "ticket": by_key.get(key),
                "children": [],
            }
        return groups[key]

    other: list[dict[str, Any]] = []
    for t in tickets:
        if _is_story(t):
            ensure_group(t["key"])
            continue
        pkey = t.get("parent_key")
        if pkey and is_story_key(pkey):
            ensure_group(pkey)["children"].append(t)
        else:
            other.append(t)

    def _est(t: dict[str, Any] | None) -> int:
        return int(t["estimate_seconds"]) if t else 0

    ordered = sorted(
        groups.values(),
        key=lambda g: (_est(g["ticket"]), len(g["children"])),
        reverse=True,
    )
    for g in ordered:
        g["children"].sort(key=lambda c: _est(c), reverse=True)
    other.sort(key=lambda t: _est(t), reverse=True)
    return ordered, other


def _render_item(label: str, t: dict[str, Any] | None, indent: str) -> str:
    """'<label>: [FLAG · Δ% · low/med reason] explanation' (or header if no analysis)."""
    flag = (t or {}).get("flag")
    if t is None or not flag or flag == "n/a":
        base = f"{indent}{label}"
        if t is not None and flag == "n/a":
            return f"{base}: _not analyzed yet_"
        return f"{base}:"
    seg = [flag, _fmt_delta(t.get("delta_pct"))]
    conf = (t.get("confidence") or "").lower()
    if conf in ("low", "medium") and t.get("reason"):
        seg.append(f"{conf} conf: {t['reason']}")
    explanation = (t.get("explanation") or "").strip()
    tail = f" {explanation}" if explanation else ""
    return f"{indent}{label}: [{' · '.join(seg)}]{tail}"


def _child_label(t: dict[str, Any]) -> str:
    label = f"↳ *{t['key']}*"
    if t.get("summary"):
        label += f" — {t['summary'][:60]}"
    return label


def _render_report_lines(
    groups: list[dict[str, Any]], other: list[dict[str, Any]]
) -> list[str]:
    # Hide tickets within tolerance ('OK'); keep UNDER / PLUS / n/a. A Story is
    # kept as a header (for context) when it has visible children even if its
    # own line is OK; an all-OK group is dropped entirely.
    lines: list[str] = []
    for g in groups:
        story = g.get("ticket")
        story_visible = bool(story) and story.get("flag") != "OK"
        visible_children = [c for c in g["children"] if c.get("flag") != "OK"]
        if not story_visible and not visible_children:
            continue

        title = f"*{g['key']}*"
        if g.get("summary"):
            title += f" — {g['summary'][:70]}"
        # Show the Story's own analysis only when it is itself flagged; otherwise
        # render a plain header so it just groups its flagged children.
        lines.append(_render_item(title, story if story_visible else None, ""))
        for child in visible_children:
            lines.append(_render_item(_child_label(child), child, "   "))
        lines.append("")  # spacer between stories

    visible_other = [t for t in other if t.get("flag") != "OK"]
    if visible_other:
        lines.append("*Other tasks (Not In Any Story)*")
        for t in visible_other:
            lines.append(_render_item(_child_label(t), t, "   "))
    return lines


def _chunk_lines(lines: list[str]) -> list[list[str]]:
    """Split rendered lines into Slack-sized parts, repeating the section header
    as '(cont.)' context when a split lands mid-section."""
    parts: list[list[str]] = []
    cur: list[str] = []
    cur_len = 0
    header: str | None = None  # most recent non-indented bold header line
    for line in lines:
        if line and not line.startswith(" ") and line.startswith("*"):
            header = line.split("  _(cont.)_")[0]
        if cur and cur_len + len(line) + 1 > _CHAR_BUDGET:
            parts.append(cur)
            cur = []
            cur_len = 0
            if line.startswith(" ") and header:  # mid-section child after a split
                ctx = f"{header}  _(cont.)_"
                cur.append(ctx)
                cur_len += len(ctx) + 1
        cur.append(line)
        cur_len += len(line) + 1
    if cur:
        parts.append(cur)
    return parts or [[]]


def _build_analysis_alerts(
    settings: Settings,
    channel_id: str,
    tickets: list[dict[str, Any]],
    stats: dict[str, Any],
) -> list[dict[str, Any]]:
    project = (settings.rft_estimate_project_key or "RFT").strip()
    scope = _scope_label(settings)

    groups, other = _resolve_groups(settings, tickets)
    report_lines = _render_report_lines(groups, other)

    base_headline = (
        f":bar_chart: *{project} Estimate Analysis ({scope})* — "
        f"{len(tickets)} ticket{'s' if len(tickets) != 1 else ''} · "
        f"*{stats.get('flagged', 0)} flagged*"
    )

    # Everything within tolerance — nothing flagged to show.
    if not report_lines:
        message = (
            f"{base_headline}\n\n_All analyzed tickets are within the estimate "
            "tolerance — nothing to flag._"
        )
        if not stats.get("llm", True):
            message += "\n_⚠ LLM unavailable this run — predictions skipped._"
        return [{"channel_id": channel_id, "message": message}]

    parts = _chunk_lines(report_lines)
    total = len(parts)

    alerts: list[dict[str, Any]] = []
    for idx, part in enumerate(parts, 1):
        suffix = f"  (part {idx}/{total})" if total > 1 else ""
        body = "\n".join(part).rstrip()
        message = f"{base_headline}{suffix}\n\n{body}"
        if idx == 1:
            message += (
                "\n\n_Format: [UNDER/PLUS · Δ% · low/med-conf reason] explanation. "
                "UNDER = the Original Estimate looks too low, PLUS = too high. "
                "Within-tolerance tickets are hidden. Predicted for an average "
                "experienced developer._"
            )
            if not stats.get("llm", True):
                message += "\n_⚠ LLM unavailable this run — predictions skipped._"
        alerts.append({"channel_id": channel_id, "message": message})

    return alerts


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

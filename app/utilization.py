"""Utilization analytics for the admin dashboard.

Two responsibilities:

1. ``ticket_status_history`` — a lightweight, self-healing transition log. The
   Jira webhook (via the n8n "Status Transition Logger" workflow) posts each
   status change to ``POST /workflow/record-transition`` which calls
   ``record_status_change``. Rows accrue going forward; the table starts empty.

2. ``build_utilization_report`` — a read-only aggregation across every table the
   AI Governor system writes (test cases, doc reviews, ticket cache, due-date
   tracking, SLA, documentation generation, Slack conversations, transitions),
   returned as a plain dict for the ``/graph-admin/utilization`` endpoint.

Every section is computed defensively: a missing table or column degrades that
one section to empty rather than failing the whole report, so the dashboard
works across environments at different migration states.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import Settings

LOGGER = logging.getLogger(__name__)


# ── connection + small query helpers ─────────────────────────────────────────
def _connect(settings: Settings):
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(settings.database_url, row_factory=dict_row)


def _table_exists(conn, name: str) -> bool:
    try:
        row = conn.execute("SELECT to_regclass(%s) AS t", (name,)).fetchone()
        return bool(row and row.get("t"))
    except Exception:  # noqa: BLE001
        return False


def _rows(conn, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Run a query, returning [] on any error (e.g. missing column)."""
    try:
        return conn.execute(sql, params).fetchall()
    except Exception as exc:  # noqa: BLE001
        LOGGER.debug("utilization query skipped: %s", exc)
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        return []


def _one(conn, sql: str, params: tuple = ()) -> dict[str, Any]:
    rows = _rows(conn, sql, params)
    return rows[0] if rows else {}


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


# ── transition log (write path) ──────────────────────────────────────────────
def ensure_status_history_schema(settings: Settings) -> None:
    if not settings.database_url:
        return
    with _connect(settings) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_status_history (
                id             BIGSERIAL PRIMARY KEY,
                jira_ticket_id TEXT NOT NULL,
                project_key    TEXT,
                issue_type     TEXT,
                from_status    TEXT,
                to_status      TEXT NOT NULL,
                assignee_name  TEXT,
                source         TEXT DEFAULT 'webhook',
                changed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_tsh_ticket ON ticket_status_history (jira_ticket_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_tsh_changed ON ticket_status_history (changed_at)"
        )
        # Dedupe guard: the same webhook can be delivered more than once.
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_tsh_event "
            "ON ticket_status_history (jira_ticket_id, to_status, changed_at)"
        )
        conn.commit()


def record_status_change(
    settings: Settings,
    *,
    issue_key: str,
    to_status: str,
    from_status: str = "",
    project_key: str = "",
    issue_type: str = "",
    assignee: str = "",
    changed_at: str = "",
    source: str = "webhook",
) -> dict[str, Any]:
    """Persist one status transition. Idempotent on (ticket, to_status, changed_at)."""
    if not settings.database_url:
        return {"recorded": False, "reason": "DATABASE_URL not configured"}
    if not issue_key or not to_status:
        return {"recorded": False, "reason": "issueKey and toStatus are required"}

    ensure_status_history_schema(settings)

    ts: Optional[datetime] = None
    if changed_at:
        try:
            ts = datetime.fromisoformat(changed_at.replace("Z", "+00:00"))
        except ValueError:
            ts = None
    if ts is None:
        ts = datetime.now(timezone.utc)

    with _connect(settings) as conn:
        cur = conn.execute(
            """
            INSERT INTO ticket_status_history
                (jira_ticket_id, project_key, issue_type, from_status,
                 to_status, assignee_name, source, changed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (jira_ticket_id, to_status, changed_at) DO NOTHING
            RETURNING id
            """,
            (
                issue_key.strip(),
                (project_key or "").strip() or None,
                (issue_type or "").strip() or None,
                (from_status or "").strip() or None,
                to_status.strip(),
                (assignee or "").strip() or None,
                source,
                ts,
            ),
        )
        row = cur.fetchone()
        conn.commit()

    recorded = bool(row)
    LOGGER.info(
        "record_status_change issue=%s %s -> %s recorded=%s",
        issue_key,
        from_status or "?",
        to_status,
        recorded,
    )
    return {"recorded": recorded, "ticket": issue_key, "to_status": to_status}


# ── utilization report (read path) ───────────────────────────────────────────
def build_utilization_report(settings: Settings) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    report: dict[str, Any] = {
        "generated_at": now,
        "database_configured": bool(settings.database_url),
    }
    if not settings.database_url:
        return report

    with _connect(settings) as conn:
        report["test_cases"] = _test_cases_section(conn)
        report["doc_reviews"] = _doc_reviews_section(conn)
        report["tickets"] = _tickets_section(conn)
        report["transitions"] = _transitions_section(conn)
        report["due_date"] = _due_date_section(conn)
        report["sla"] = _sla_section(conn)
        report["documentation"] = _documentation_section(conn)
        report["conversations"] = _conversations_section(conn)

    return report


def _test_cases_section(conn) -> dict[str, Any]:
    # NOTE: test cases are AI-*generated* artifacts. There is no pass/fail
    # execution tracking — `test_cases.status` is always inserted as 'pending'
    # and never updated. The "tests passed" signal is the developer moving the
    # ticket out of QA (QA -> Ready for Deployment), which lives in the
    # transitions section, not here. So we report generation volume only.
    if not _table_exists(conn, "test_cases"):
        return {"available": False}
    totals = _one(
        conn,
        "SELECT COUNT(*) AS total, COUNT(DISTINCT jira_ticket_id) AS tickets FROM test_cases",
    )
    total = _int(totals.get("total"))
    tickets = _int(totals.get("tickets"))
    return {
        "available": True,
        "total_test_cases": total,
        "tickets_covered": tickets,
        "avg_per_ticket": round(total / tickets, 1) if tickets else 0,
    }


def _doc_reviews_section(conn) -> dict[str, Any]:
    if not _table_exists(conn, "doc_reviews"):
        return {"available": False}
    totals = _one(
        conn,
        "SELECT COUNT(*) AS docs, COUNT(DISTINCT jira_ticket_id) AS tickets, "
        "COALESCE(SUM(review_count),0) AS reviews FROM doc_reviews",
    )
    by_type = _rows(
        conn,
        "SELECT COALESCE(NULLIF(doc_type,''),'(other)') AS doc_type, COUNT(*) AS docs, "
        "COALESCE(SUM(review_count),0) AS reviews FROM doc_reviews GROUP BY 1 ORDER BY docs DESC",
    )
    return {
        "available": True,
        "docs_reviewed": _int(totals.get("docs")),
        "tickets_covered": _int(totals.get("tickets")),
        "total_reviews": _int(totals.get("reviews")),
        "by_type": [
            {"doc_type": r["doc_type"], "docs": _int(r["docs"]), "reviews": _int(r["reviews"])}
            for r in by_type
        ],
    }


def _tickets_section(conn) -> dict[str, Any]:
    if not _table_exists(conn, "jira_ticket_cache"):
        return {"available": False}
    total = _int(_one(conn, "SELECT COUNT(*) AS c FROM jira_ticket_cache").get("c"))

    def _group(col: str, label: str) -> list[dict[str, Any]]:
        rows = _rows(
            conn,
            f"SELECT COALESCE(NULLIF({col},''),'(none)') AS k, COUNT(*) AS c "
            f"FROM jira_ticket_cache GROUP BY 1 ORDER BY c DESC",
        )
        return [{label: r["k"], "count": _int(r["c"])} for r in rows]

    return {
        "available": True,
        "total": total,
        "by_status": _group("status", "status"),
        "by_project": _group("project_key", "project"),
        "by_issue_type": _group("issue_type", "issue_type"),
        "by_priority": _group("priority", "priority"),
    }


def _transitions_section(conn) -> dict[str, Any]:
    if not _table_exists(conn, "ticket_status_history"):
        return {"available": False, "total": 0}
    totals = _one(
        conn,
        "SELECT COUNT(*) AS total, COUNT(DISTINCT jira_ticket_id) AS tickets "
        "FROM ticket_status_history",
    )
    by_transition = _rows(
        conn,
        "SELECT COALESCE(from_status,'(start)') AS from_status, to_status, COUNT(*) AS count "
        "FROM ticket_status_history GROUP BY 1, 2 ORDER BY count DESC LIMIT 50",
    )
    by_to_status = _rows(
        conn,
        "SELECT to_status, COUNT(*) AS count FROM ticket_status_history "
        "GROUP BY 1 ORDER BY count DESC",
    )
    recent = _rows(
        conn,
        "SELECT jira_ticket_id, from_status, to_status, assignee_name, "
        "to_char(changed_at, 'YYYY-MM-DD\"T\"HH24:MI:SSZ') AS changed_at "
        "FROM ticket_status_history ORDER BY changed_at DESC LIMIT 25",
    )
    return {
        "available": True,
        "total": _int(totals.get("total")),
        "distinct_tickets": _int(totals.get("tickets")),
        "by_transition": [
            {
                "from_status": r["from_status"],
                "to_status": r["to_status"],
                "count": _int(r["count"]),
            }
            for r in by_transition
        ],
        "by_to_status": [
            {"to_status": r["to_status"], "count": _int(r["count"])} for r in by_to_status
        ],
        "recent": recent,
    }


def _due_date_section(conn) -> dict[str, Any]:
    if not _table_exists(conn, "due_date_tracking"):
        return {"available": False}
    tracked = _int(_one(conn, "SELECT COUNT(*) AS c FROM due_date_tracking").get("c"))
    alerts = _one(
        conn,
        "SELECT "
        "COALESCE(SUM(CASE WHEN alert_75_sent THEN 1 ELSE 0 END),0) AS a75, "
        "COALESCE(SUM(CASE WHEN alert_50_sent THEN 1 ELSE 0 END),0) AS a50, "
        "COALESCE(SUM(CASE WHEN alert_25_sent THEN 1 ELSE 0 END),0) AS a25, "
        "COALESCE(SUM(CASE WHEN alert_0_sent  THEN 1 ELSE 0 END),0) AS a0 "
        "FROM due_date_tracking",
    )
    return {
        "available": True,
        "tracked": tracked,
        "alerts": {
            "lt_75pct": _int(alerts.get("a75")),
            "lt_50pct": _int(alerts.get("a50")),
            "lt_25pct": _int(alerts.get("a25")),
            "breached": _int(alerts.get("a0")),
        },
    }


def _sla_section(conn) -> dict[str, Any]:
    if not _table_exists(conn, "sla_tracking"):
        return {"available": False}
    total = _int(_one(conn, "SELECT COUNT(*) AS c FROM sla_tracking").get("c"))
    return {"available": True, "tracked": total}


def _documentation_section(conn) -> dict[str, Any]:
    if not _table_exists(conn, "doc_generation_usage"):
        return {"available": False}
    totals = _one(
        conn,
        "SELECT COUNT(*) AS jobs, "
        "COALESCE(SUM(CASE WHEN reused THEN 1 ELSE 0 END),0) AS reused, "
        "COALESCE(SUM(input_tokens + output_tokens),0) AS tokens, "
        "COALESCE(SUM(cost_usd),0) AS cost FROM doc_generation_usage",
    )
    by_type = _rows(
        conn,
        "SELECT doc_type, COUNT(*) AS jobs FROM doc_generation_usage "
        "GROUP BY 1 ORDER BY jobs DESC",
    )
    return {
        "available": True,
        "generated": _int(totals.get("jobs")),
        "reused": _int(totals.get("reused")),
        "total_tokens": _int(totals.get("tokens")),
        "total_cost_usd": round(float(totals.get("cost") or 0), 4),
        "by_type": [{"doc_type": r["doc_type"], "jobs": _int(r["jobs"])} for r in by_type],
    }


def _conversations_section(conn) -> dict[str, Any]:
    if not _table_exists(conn, "jira_slack_conversations"):
        return {"available": False}
    totals = _one(
        conn,
        "SELECT COUNT(*) AS threads, COUNT(DISTINCT jira_issue_key) AS tickets "
        "FROM jira_slack_conversations",
    )
    return {
        "available": True,
        "threads": _int(totals.get("threads")),
        "tickets": _int(totals.get("tickets")),
    }

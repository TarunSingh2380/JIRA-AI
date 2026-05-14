"""Jira ticket fetcher with PostgreSQL caching.

Fetches all tickets across all accessible Jira projects. Results are cached
in the `jira_ticket_cache` table so repeated calls within the TTL window
return stored data without hitting the Jira REST API.

Tables written (created by migrations/001_init.sql):
  jira_projects      – one row per project, upserted on every run
  jira_ticket_cache  – full ticket JSON + queryable denormalized columns
  jira_fetch_log     – one row per project per run (audit + TTL check)
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import psycopg
import requests
from requests.auth import HTTPBasicAuth

from app.config import settings
from app.jira_graph import _adf_to_text

log = logging.getLogger(__name__)

_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


# ─── Jira REST helpers ───────────────────────────────────────────────────────

def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(settings.jira_email, settings.jira_api_token)


def _jira_get(path: str, params: Optional[dict] = None) -> dict[str, Any]:
    url = f"{settings.jira_base_url}{path}"
    for _ in range(5):
        resp = requests.get(url, headers=_HEADERS, auth=_auth(), params=params, timeout=60)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "5"))
            log.warning("Jira rate-limited; sleeping %ds", wait)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json() if resp.text else {}
    raise RuntimeError(f"Jira GET {path} failed after retries")


def _fetch_all_projects() -> list[dict[str, Any]]:
    projects: list[dict] = []
    start = 0
    while True:
        data = _jira_get("/rest/api/3/project/search", {"startAt": start, "maxResults": 50})
        batch = data.get("values", [])
        projects.extend(batch)
        if data.get("isLast", True) or len(batch) < 50:
            break
        start += 50
    return projects


def _fetch_tickets_for_project(project_key: str) -> list[dict[str, Any]]:
    """Paginate through all issues in a project via JQL search."""
    tickets: list[dict] = []
    start = 0
    fields = (
        "summary,description,status,issuetype,priority,assignee,reporter,"
        "created,updated,parent,subtasks,components,labels,fixVersions,comment"
    )
    while True:
        data = _jira_get(
            "/rest/api/3/search",
            {
                "jql": f"project={project_key} ORDER BY created DESC",
                "startAt": start,
                "maxResults": 100,
                "fields": fields,
            },
        )
        batch = data.get("issues", [])
        tickets.extend(batch)
        total = data.get("total", 0)
        start += len(batch)
        if start >= total or not batch:
            break
    return tickets


# ─── PostgreSQL writers ──────────────────────────────────────────────────────

def _upsert_project(conn: psycopg.Connection, project: dict[str, Any]) -> None:
    lead = project.get("lead") or {}
    conn.execute(
        """
        INSERT INTO jira_projects
            (key, name, project_type, description, lead_name, lead_email, data, fetched_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (key) DO UPDATE
            SET name         = EXCLUDED.name,
                project_type = EXCLUDED.project_type,
                description  = EXCLUDED.description,
                lead_name    = EXCLUDED.lead_name,
                lead_email   = EXCLUDED.lead_email,
                data         = EXCLUDED.data,
                fetched_at   = NOW()
        """,
        (
            project.get("key", ""),
            project.get("name", ""),
            project.get("projectTypeKey"),
            project.get("description"),
            lead.get("displayName"),
            lead.get("emailAddress"),
            json.dumps(project),
        ),
    )


def _ticket_columns(ticket: dict[str, Any]) -> dict[str, Any]:
    """Extract denormalized columns from a raw Jira issue dict."""
    fields = ticket.get("fields", {}) or {}
    key = ticket.get("key", "")
    project_key = key.rsplit("-", 1)[0] if "-" in key else key

    assignee = fields.get("assignee") or {}
    reporter = fields.get("reporter") or {}

    def _ts(val: Any) -> Optional[datetime]:
        if not val:
            return None
        try:
            return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        except ValueError:
            return None

    return {
        "ticket_key": key,
        "project_key": project_key,
        "summary": (fields.get("summary") or "")[:500],
        "description": _adf_to_text(fields.get("description"))[:2000],
        "status": (fields.get("status") or {}).get("name", ""),
        "issue_type": (fields.get("issuetype") or {}).get("name", ""),
        "priority": (fields.get("priority") or {}).get("name", ""),
        "assignee_email": assignee.get("emailAddress"),
        "assignee_name": assignee.get("displayName"),
        "reporter_email": reporter.get("emailAddress"),
        "reporter_name": reporter.get("displayName"),
        "labels": fields.get("labels") or [],
        "created_at": _ts(fields.get("created")),
        "updated_at": _ts(fields.get("updated")),
        "data": json.dumps(ticket),
    }


def _upsert_tickets(conn: psycopg.Connection, tickets: list[dict[str, Any]]) -> None:
    for ticket in tickets:
        col = _ticket_columns(ticket)
        conn.execute(
            """
            INSERT INTO jira_ticket_cache (
                ticket_key, project_key, summary, description, status,
                issue_type, priority, assignee_email, assignee_name,
                reporter_email, reporter_name, labels,
                created_at, updated_at, data, fetched_at
            )
            VALUES (
                %(ticket_key)s, %(project_key)s, %(summary)s, %(description)s, %(status)s,
                %(issue_type)s, %(priority)s, %(assignee_email)s, %(assignee_name)s,
                %(reporter_email)s, %(reporter_name)s, %(labels)s,
                %(created_at)s, %(updated_at)s, %(data)s, NOW()
            )
            ON CONFLICT (ticket_key) DO UPDATE
                SET project_key    = EXCLUDED.project_key,
                    summary        = EXCLUDED.summary,
                    description    = EXCLUDED.description,
                    status         = EXCLUDED.status,
                    issue_type     = EXCLUDED.issue_type,
                    priority       = EXCLUDED.priority,
                    assignee_email = EXCLUDED.assignee_email,
                    assignee_name  = EXCLUDED.assignee_name,
                    reporter_email = EXCLUDED.reporter_email,
                    reporter_name  = EXCLUDED.reporter_name,
                    labels         = EXCLUDED.labels,
                    created_at     = EXCLUDED.created_at,
                    updated_at     = EXCLUDED.updated_at,
                    data           = EXCLUDED.data,
                    fetched_at     = NOW()
            """,
            col,
        )


def _log_fetch(
    conn: psycopg.Connection,
    project_key: str,
    ticket_count: int,
    from_cache: bool,
    force_refresh: bool,
    duration_ms: int,
    error: Optional[str] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO jira_fetch_log
            (project_key, ticket_count, from_cache, force_refresh, duration_ms, error)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (project_key, ticket_count, from_cache, force_refresh, duration_ms, error),
    )


# ─── Cache TTL check ─────────────────────────────────────────────────────────

def _is_cache_fresh(conn: psycopg.Connection, project_key: str, ttl_hours: int) -> bool:
    if ttl_hours <= 0:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)
    row = conn.execute(
        """
        SELECT COUNT(*) FROM jira_ticket_cache
        WHERE project_key = %s AND fetched_at > %s
        """,
        (project_key, cutoff),
    ).fetchone()
    return (row[0] if row else 0) > 0


def _load_from_cache(conn: psycopg.Connection, project_key: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT data FROM jira_ticket_cache WHERE project_key = %s",
        (project_key,),
    ).fetchall()
    return [row[0] for row in rows]


# ─── Public API ──────────────────────────────────────────────────────────────

def fetch_all_tickets(
    force_refresh: bool = False,
    ttl_hours: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Return all Jira tickets across all projects.

    Serves from the PostgreSQL cache when fresh; falls back to the Jira API
    otherwise and stores the result back into the cache.
    Returns an empty list gracefully when credentials are absent.
    """
    if not all([settings.jira_base_url, settings.jira_email, settings.jira_api_token]):
        log.warning("Jira credentials not configured; returning empty ticket list")
        return []

    effective_ttl = ttl_hours if ttl_hours is not None else settings.jira_cache_ttl_hours
    all_tickets: list[dict[str, Any]] = []

    with psycopg.connect(settings.database_url) as conn:
        projects = _fetch_all_projects()
        log.info("Found %d Jira projects", len(projects))

        for project in projects:
            key = project["key"]
            t0 = time.monotonic()

            # Upsert the project metadata row
            _upsert_project(conn, project)

            # Serve from cache if still fresh
            if not force_refresh and _is_cache_fresh(conn, key, effective_ttl):
                cached = _load_from_cache(conn, key)
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                _log_fetch(conn, key, len(cached), from_cache=True,
                           force_refresh=False, duration_ms=elapsed_ms)
                conn.commit()
                log.info("Cache hit: %d tickets for project %s", len(cached), key)
                all_tickets.extend(cached)
                continue

            # Hit the Jira API
            log.info("Fetching tickets for project %s from Jira API ...", key)
            error_msg: Optional[str] = None
            tickets: list[dict] = []
            try:
                tickets = _fetch_tickets_for_project(key)
                _upsert_tickets(conn, tickets)
            except Exception as exc:
                error_msg = str(exc)[:500]
                log.warning("Failed to fetch/store project %s: %s", key, error_msg)

            elapsed_ms = int((time.monotonic() - t0) * 1000)
            _log_fetch(conn, key, len(tickets), from_cache=False,
                       force_refresh=force_refresh, duration_ms=elapsed_ms,
                       error=error_msg)
            conn.commit()

            all_tickets.extend(tickets)
            log.info("Fetched and stored %d tickets for project %s", len(tickets), key)

    return all_tickets


def get_cached_ticket_count() -> int:
    """Return the total number of tickets currently in the cache (any age)."""
    if not settings.database_url:
        return 0
    try:
        with psycopg.connect(settings.database_url) as conn:
            row = conn.execute("SELECT COUNT(*) FROM jira_ticket_cache").fetchone()
            return row[0] if row else 0
    except Exception as exc:
        log.warning("Could not query jira_ticket_cache: %s", exc)
        return 0

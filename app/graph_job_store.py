"""Postgres persistence for graph admin jobs."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from app.config import Settings
from app.graph_job_types import GraphJob


class GraphJobStoreError(RuntimeError):
    pass


class PostgresGraphJobStore:
    def __init__(self, settings: Settings) -> None:
        if not settings.database_url:
            raise GraphJobStoreError("DATABASE_URL is required for graph job persistence")

        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise GraphJobStoreError("Install psycopg[binary] to use graph job persistence") from exc

        self.settings = settings
        self._psycopg = psycopg
        self._dict_row = dict_row

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_jobs (
                    job_id UUID PRIMARY KEY,
                    action VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    repos_total INTEGER NOT NULL DEFAULT 0,
                    repos_done INTEGER NOT NULL DEFAULT 0,
                    jira_total INTEGER NOT NULL DEFAULT 0,
                    jira_done INTEGER NOT NULL DEFAULT 0,
                    error_msg TEXT,
                    notes TEXT,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    completed_at TIMESTAMPTZ
                )
                """
            )
            for statement in _GRAPH_JOB_ALTERS:
                conn.execute(statement)
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_graph_jobs_updated_at
                ON graph_jobs (updated_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_graph_jobs_status
                ON graph_jobs (status)
                """
            )

    def save(self, job: GraphJob) -> None:
        self.init_schema()
        completed_at = job.updated_at if job.status in {"completed", "failed"} else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO graph_jobs (
                    job_id,
                    action,
                    status,
                    repos_total,
                    repos_done,
                    jira_total,
                    jira_done,
                    error_msg,
                    notes,
                    started_at,
                    completed_at,
                    options,
                    totals,
                    progress,
                    repositories,
                    jira_tickets,
                    logs,
                    created_at,
                    updated_at
                )
                VALUES (
                    %(job_id)s::uuid,
                    %(action)s,
                    %(status)s,
                    %(repos_total)s,
                    %(repos_done)s,
                    %(jira_total)s,
                    %(jira_done)s,
                    %(error_msg)s,
                    %(notes)s,
                    %(started_at)s::timestamptz,
                    %(completed_at)s::timestamptz,
                    %(options)s::jsonb,
                    %(totals)s::jsonb,
                    %(progress)s::jsonb,
                    %(repositories)s::jsonb,
                    %(jira_tickets)s::jsonb,
                    %(logs)s::jsonb,
                    %(created_at)s::timestamptz,
                    %(updated_at)s::timestamptz
                )
                ON CONFLICT (job_id)
                DO UPDATE SET
                    action = EXCLUDED.action,
                    status = EXCLUDED.status,
                    repos_total = EXCLUDED.repos_total,
                    repos_done = EXCLUDED.repos_done,
                    jira_total = EXCLUDED.jira_total,
                    jira_done = EXCLUDED.jira_done,
                    error_msg = EXCLUDED.error_msg,
                    notes = EXCLUDED.notes,
                    completed_at = EXCLUDED.completed_at,
                    options = EXCLUDED.options,
                    totals = EXCLUDED.totals,
                    progress = EXCLUDED.progress,
                    repositories = EXCLUDED.repositories,
                    jira_tickets = EXCLUDED.jira_tickets,
                    logs = EXCLUDED.logs,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at
                """,
                self._params(job, completed_at=completed_at),
            )

    def get(self, job_id: str) -> GraphJob | None:
        self.init_schema()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM graph_jobs WHERE job_id = %s::uuid",
                (job_id,),
            ).fetchone()
        return self._job(row) if row else None

    def list(self, limit: int = 50) -> list[GraphJob]:
        self.init_schema()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM graph_jobs
                ORDER BY updated_at DESC NULLS LAST, started_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return [self._job(row) for row in rows]

    def _connect(self):
        return self._psycopg.connect(self.settings.database_url, row_factory=self._dict_row)

    def _params(self, job: GraphJob, *, completed_at: str | None) -> dict[str, Any]:
        totals = job.totals or {}
        progress = job.progress or {}
        options = job.options or {}
        return {
            "job_id": job.id,
            "action": job.action,
            "status": job.status,
            "repos_total": int(totals.get("repositories", 0) or 0),
            "repos_done": int(progress.get("repositories_done", 0) or 0),
            "jira_total": int(totals.get("jira_tickets", 0) or 0),
            "jira_done": int(progress.get("jira_tickets_done", 0) or 0),
            "error_msg": job.error,
            "notes": options.get("notes"),
            "started_at": job.created_at,
            "completed_at": completed_at,
            "options": self._json(options),
            "totals": self._json(totals),
            "progress": self._json(progress),
            "repositories": self._json(job.repositories),
            "jira_tickets": self._json(job.jira_tickets),
            "logs": self._json(job.logs),
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }

    def _job(self, row: dict[str, Any]) -> GraphJob:
        totals = row.get("totals") or {
            "repositories": row.get("repos_total") or 0,
            "jira_tickets": row.get("jira_total") or 0,
        }
        progress = row.get("progress") or {
            "repositories_done": row.get("repos_done") or 0,
            "jira_tickets_done": row.get("jira_done") or 0,
        }
        created_at = row.get("created_at") or row.get("started_at")
        updated_at = row.get("updated_at") or row.get("completed_at") or row.get("started_at")
        return GraphJob(
            id=str(row["job_id"]),
            action=row["action"],
            status=row["status"],
            created_at=_iso(created_at),
            updated_at=_iso(updated_at),
            options=row.get("options") or {"notes": row.get("notes")},
            totals=totals,
            progress=progress,
            repositories=row.get("repositories") or [],
            jira_tickets=row.get("jira_tickets") or [],
            logs=row.get("logs") or [],
            error=row.get("error_msg"),
        )

    def _json(self, value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)


def graph_job_to_dict(job: GraphJob) -> dict[str, Any]:
    return asdict(job)


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


_GRAPH_JOB_ALTERS = [
    "ALTER TABLE graph_jobs ADD COLUMN IF NOT EXISTS options JSONB NOT NULL DEFAULT '{}'::jsonb",
    "ALTER TABLE graph_jobs ADD COLUMN IF NOT EXISTS totals JSONB NOT NULL DEFAULT '{}'::jsonb",
    "ALTER TABLE graph_jobs ADD COLUMN IF NOT EXISTS progress JSONB NOT NULL DEFAULT '{}'::jsonb",
    "ALTER TABLE graph_jobs ADD COLUMN IF NOT EXISTS repositories JSONB NOT NULL DEFAULT '[]'::jsonb",
    "ALTER TABLE graph_jobs ADD COLUMN IF NOT EXISTS jira_tickets JSONB NOT NULL DEFAULT '[]'::jsonb",
    "ALTER TABLE graph_jobs ADD COLUMN IF NOT EXISTS logs JSONB NOT NULL DEFAULT '[]'::jsonb",
    "ALTER TABLE graph_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    "ALTER TABLE graph_jobs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
]

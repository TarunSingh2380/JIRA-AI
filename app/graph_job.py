"""In-memory job state tracking for graph build operations.

Jobs are stored in a module-level JobStore (last 50 kept). Each job tracks
action, status, per-step totals, and live progress counters that the
background runner updates as work proceeds.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class GraphJob:
    job_id: str
    action: str
    status: str  # "pending" | "running" | "completed" | "failed"
    totals: dict[str, int] = field(default_factory=lambda: {"repositories": 0, "jira_tickets": 0})
    progress: dict[str, int] = field(default_factory=lambda: {"repositories_done": 0, "jira_tickets_done": 0})
    error: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "action": self.action,
            "status": self.status,
            "totals": dict(self.totals),
            "progress": dict(self.progress),
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def mark_done(self) -> None:
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, reason: str) -> None:
        self.status = "failed"
        self.error = reason[:1000]
        self.completed_at = datetime.now(timezone.utc)


class JobStore:
    """Thread-safe in-memory store for recent graph jobs (capped at max_jobs)."""

    def __init__(self, max_jobs: int = 50) -> None:
        self._jobs: dict[str, GraphJob] = {}
        self._order: list[str] = []
        self._max = max_jobs

    def create(self, action: str) -> GraphJob:
        job_id = str(uuid.uuid4())
        job = GraphJob(job_id=job_id, action=action, status="pending")
        self._jobs[job_id] = job
        self._order.append(job_id)
        if len(self._order) > self._max:
            oldest = self._order.pop(0)
            self._jobs.pop(oldest, None)
        return job

    def get(self, job_id: str) -> Optional[GraphJob]:
        return self._jobs.get(job_id)

    def list_recent(self, limit: int = 10) -> list[GraphJob]:
        ids = self._order[-limit:][::-1]
        return [self._jobs[j] for j in ids if j in self._jobs]


# Module-level singleton used by api.py and graph_job_runner.py
job_store = JobStore()

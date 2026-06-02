"""In-process async jobs for repository document generation.

Document generation runs the LLM for 30s-4min, which exceeds typical reverse-proxy
read timeouts (nginx defaults to 60s) when done as one synchronous HTTP request.
Instead we start a background thread and let the UI poll a short status endpoint, so
no single request stays open long enough to be killed by the proxy.

The store is in-memory and process-local. The service runs a single uvicorn worker,
so all start/poll requests hit the same process; if the app is ever scaled to
multiple workers this must move to shared storage.
"""
from __future__ import annotations

import logging
import threading
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

from app.repo_doc_generator import generate_repo_document

log = logging.getLogger(__name__)

_MAX_JOBS = 100
_lock = threading.Lock()
_jobs: "OrderedDict[str, dict[str, Any]]" = OrderedDict()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_doc_job(repo: str, doc_type: str) -> str:
    """Create a job and run generation on a background thread. Returns job_id."""
    job_id = uuid.uuid4().hex
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "repo": repo,
            "doc_type": doc_type,
            "filename": None,
            "markdown": None,
            "error": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        while len(_jobs) > _MAX_JOBS:
            _jobs.popitem(last=False)

    thread = threading.Thread(
        target=_run_job, args=(job_id, repo, doc_type), name=f"repo-doc-{job_id[:8]}", daemon=True
    )
    thread.start()
    log.info("Started repo-doc job %s repo=%s doc_type=%s", job_id, repo, doc_type)
    return job_id


def _run_job(job_id: str, repo: str, doc_type: str) -> None:
    try:
        filename, markdown = generate_repo_document(repo, doc_type)
        _update(job_id, status="done", filename=filename, markdown=markdown)
        log.info("repo-doc job %s done (%d chars)", job_id, len(markdown))
    except ValueError as exc:
        _update(job_id, status="error", error=str(exc))
        log.warning("repo-doc job %s rejected: %s", job_id, exc)
    except Exception as exc:  # noqa: BLE001
        log.exception("repo-doc job %s failed", job_id)
        _update(job_id, status="error", error=str(exc))


def _update(job_id: str, **fields: Any) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if job is not None:
            job.update(fields)
            job["updated_at"] = _now()


def get_doc_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job is not None else None

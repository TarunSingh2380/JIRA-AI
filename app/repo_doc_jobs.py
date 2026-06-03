"""In-process async jobs for repository document generation.

Document generation runs the LLM for 30s-4min, which exceeds typical reverse-proxy
read timeouts (nginx defaults to 60s) when done as one synchronous HTTP request.
Instead we start a background thread and let the UI poll a short status endpoint, so
no single request stays open long enough to be killed by the proxy.

A job can generate a single document or ALL document types (mode="all"). As it
runs it reports live progress, cumulative token counts and an estimated USD cost,
and it reuses a previously generated document when the repository context is
unchanged (so no tokens are spent regenerating identical output). Every event is
logged to Postgres per user for later analysis.

The job store is in-memory and process-local. The service runs a single uvicorn
worker, so all start/poll requests hit the same process; if the app is ever
scaled to multiple workers this must move to shared storage.
"""
from __future__ import annotations

import logging
import threading
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import settings
from app.repo_doc_generator import (
    build_document_context,
    document_label,
    document_type_ids,
    generate_repo_document_full,
)
from app.repo_doc_usage import (
    compute_cost,
    context_hash,
    get_cached_artifact,
    record_usage,
    save_artifact,
)

log = logging.getLogger(__name__)

_MAX_JOBS = 100
_lock = threading.Lock()
_jobs: "OrderedDict[str, dict[str, Any]]" = OrderedDict()

# Rough per-document output-token estimate used only for the pre-run cost preview.
_ESTIMATED_OUTPUT_TOKENS = 8_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_usage() -> dict[str, Any]:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "cost_usd": 0.0,
        "reused_count": 0,
        "generated_count": 0,
    }


def estimate_doc_job(repo: str, doc_type: str) -> dict[str, Any]:
    """Pre-flight cost/cache check for a (repo, doc_type) before starting a job.

    Builds the model context (just reads cached artifacts, spends no tokens),
    then for each document type reports whether a previously generated copy can
    be reused for the current code (cost 0) and estimates the USD cost of the
    documents that would actually be generated. The UI uses this to confirm
    spend up front — and to skip the cost prompt when everything is already
    cached. ``doc_type == "all"`` covers every document type.

    Raises ValueError on bad input / missing artifacts (same as generation).
    """
    mode = "all" if doc_type == "all" else "single"
    doc_types = document_type_ids() if mode == "all" else [doc_type]

    context, _stats = build_document_context(repo)
    ctx_hash = context_hash(context)
    est_input = max(1, len(context) // 4)

    docs: list[dict[str, Any]] = []
    est_cost = 0.0
    est_tokens = 0
    cached_count = 0
    for dtype in doc_types:
        cached = get_cached_artifact(repo, dtype, ctx_hash) is not None
        if cached:
            cached_count += 1
        else:
            est_cost += compute_cost(settings.llm_model, est_input, _ESTIMATED_OUTPUT_TOKENS)
            est_tokens += est_input
        docs.append({"doc_type": dtype, "label": document_label(dtype), "cached": cached})

    uncached_count = len(doc_types) - cached_count
    return {
        "repo": repo,
        "doc_type": doc_type,
        "mode": mode,
        "docs": docs,
        "cached_count": cached_count,
        "uncached_count": uncached_count,
        "all_cached": uncached_count == 0,
        "estimated_input_tokens": est_tokens,
        "estimated_cost_usd": round(est_cost, 6),
    }


def start_doc_job(repo: str, doc_type: str, user_email: Optional[str] = None) -> str:
    """Create a job and run generation on a background thread. Returns job_id.

    ``doc_type == "all"`` generates every document type for the repo.
    """
    job_id = uuid.uuid4().hex
    mode = "all" if doc_type == "all" else "single"
    doc_types = document_type_ids() if mode == "all" else [doc_type]
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "mode": mode,
            "status": "pending",
            "repo": repo,
            "doc_type": doc_type,
            "user_email": user_email,
            "filename": None,
            "markdown": None,
            "docs": [],
            "progress": {"total": len(doc_types), "completed": 0, "current_label": "", "percent": 0},
            "usage": _empty_usage(),
            "estimate": {"input_tokens": 0, "cost_usd": 0.0},
            "error": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        while len(_jobs) > _MAX_JOBS:
            _jobs.popitem(last=False)

    thread = threading.Thread(
        target=_run_job,
        args=(job_id, repo, doc_types, mode, user_email),
        name=f"repo-doc-{job_id[:8]}",
        daemon=True,
    )
    thread.start()
    log.info("Started repo-doc job %s repo=%s doc_type=%s mode=%s", job_id, repo, doc_type, mode)
    return job_id


def _run_job(
    job_id: str,
    repo: str,
    doc_types: list[str],
    mode: str,
    user_email: Optional[str],
) -> None:
    try:
        _update(job_id, status="running")

        # Build the model context once; its hash is our "did the code change?" key.
        context, _stats = build_document_context(repo)
        ctx_hash = context_hash(context)

        # Pre-run cost estimate (rough; refined live as each doc completes).
        est_input = max(1, len(context) // 4)
        est_cost = sum(
            compute_cost(settings.llm_model, est_input, _ESTIMATED_OUTPUT_TOKENS)
            for _ in doc_types
        )
        _update(job_id, estimate={"input_tokens": est_input * len(doc_types), "cost_usd": round(est_cost, 6)})

        usage = _empty_usage()
        docs: list[dict[str, Any]] = []

        for idx, dtype in enumerate(doc_types):
            label = document_label(dtype)
            _set_progress(job_id, completed=idx, total=len(doc_types), current_label=f"Generating {label}…")

            cached = get_cached_artifact(repo, dtype, ctx_hash)
            if cached is not None:
                # No code change since last generation — reuse, spend no tokens.
                doc = {
                    "doc_type": dtype,
                    "label": label,
                    "filename": cached["filename"],
                    "markdown": cached["markdown"],
                    "reused": True,
                    "model": cached.get("model") or "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                }
                usage["reused_count"] += 1
                record_usage(
                    user_email=user_email, repo=repo, doc_type=dtype, reused=True,
                    model=cached.get("model") or "", input_tokens=0, output_tokens=0,
                    cache_read_tokens=0, cache_creation_tokens=0, cost_usd=0.0, ctx_hash=ctx_hash,
                )
                log.info("repo-doc job %s reused cached %s for %s", job_id, dtype, repo)
            else:
                res = generate_repo_document_full(repo, dtype, context=context)
                cost = compute_cost(
                    res.model, res.input_tokens, res.output_tokens,
                    res.cache_read_tokens, res.cache_creation_tokens,
                )
                doc = {
                    "doc_type": dtype,
                    "label": label,
                    "filename": res.filename,
                    "markdown": res.markdown,
                    "reused": False,
                    "model": res.model,
                    "input_tokens": res.input_tokens,
                    "output_tokens": res.output_tokens,
                    "cost_usd": cost,
                }
                usage["input_tokens"] += res.input_tokens
                usage["output_tokens"] += res.output_tokens
                usage["cache_read_tokens"] += res.cache_read_tokens
                usage["cache_creation_tokens"] += res.cache_creation_tokens
                usage["cost_usd"] = round(usage["cost_usd"] + cost, 6)
                usage["generated_count"] += 1
                save_artifact(
                    repo=repo, doc_type=dtype, ctx_hash=ctx_hash, filename=res.filename,
                    markdown=res.markdown, model=res.model, input_tokens=res.input_tokens,
                    output_tokens=res.output_tokens, cache_read_tokens=res.cache_read_tokens,
                    cache_creation_tokens=res.cache_creation_tokens, cost_usd=cost,
                    created_by=user_email,
                )
                record_usage(
                    user_email=user_email, repo=repo, doc_type=dtype, reused=False,
                    model=res.model, input_tokens=res.input_tokens, output_tokens=res.output_tokens,
                    cache_read_tokens=res.cache_read_tokens, cache_creation_tokens=res.cache_creation_tokens,
                    cost_usd=cost, ctx_hash=ctx_hash,
                )

            docs.append(doc)
            _update(job_id, docs=list(docs), usage=dict(usage))
            _set_progress(job_id, completed=idx + 1, total=len(doc_types), current_label="")

        # Backward-compatible single-mode fields for existing UI paths.
        first = docs[0] if docs else None
        _update(
            job_id,
            status="done",
            docs=list(docs),
            usage=dict(usage),
            filename=first["filename"] if first else None,
            markdown=first["markdown"] if first else None,
        )
        log.info(
            "repo-doc job %s done: %d generated, %d reused, $%.4f",
            job_id, usage["generated_count"], usage["reused_count"], usage["cost_usd"],
        )
    except ValueError as exc:
        _update(job_id, status="error", error=str(exc))
        log.warning("repo-doc job %s rejected: %s", job_id, exc)
    except Exception as exc:  # noqa: BLE001
        log.exception("repo-doc job %s failed", job_id)
        _update(job_id, status="error", error=str(exc))


def _set_progress(job_id: str, *, completed: int, total: int, current_label: str) -> None:
    percent = round((completed / total) * 100) if total else 0
    _update(job_id, progress={"total": total, "completed": completed, "current_label": current_label, "percent": percent})


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

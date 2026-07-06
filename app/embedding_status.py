"""Live health + freshness status for every embedding collection.

Reports, for each Qdrant collection this app writes embeddings to: whether it
exists, how many vectors it holds, its vector dimension, when it was last
updated (persisted in ``app_settings`` so it survives restarts), and whether a
background job is currently writing to it.

Consumed by the admin dashboard's live status panel via
``GET /graph-admin/embeddings/status``. Every call is best-effort: a missing
DATABASE_URL, an unreachable Qdrant, or a partially-configured collection
degrades gracefully to a status entry rather than raising.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.app_settings import get_setting, set_setting
from app.codebase_graph import CODEBASE_EMBEDDING_MODELS
from app.config import Settings
from app.qdrant_store import (
    GITHUB_COLLECTION,
    JIRA_COLLECTION,
    JIRA_HYBRID_COLLECTION,
)

log = logging.getLogger(__name__)

_SETTING_PREFIX = "embed_last_updated:"


# ─── recording (write side) ──────────────────────────────────────────────────

def record_embedding_update(
    settings: Settings, collection: str, count: Optional[int] = None
) -> None:
    """Persist the last-updated timestamp (+ optional point count) for a collection.

    Best-effort: silently no-ops when DATABASE_URL is unset or the write fails,
    so it can be dropped into embedding pipelines without adding a failure mode.
    """
    if not settings.database_url:
        return
    try:
        payload = datetime.now(timezone.utc).isoformat()
        if count is not None:
            payload = f"{payload}|{count}"
        set_setting(settings, _SETTING_PREFIX + collection, payload)
    except Exception as exc:  # noqa: BLE001 - never let bookkeeping break a job
        log.debug("record_embedding_update(%s) failed: %s", collection, exc)


def _read_last_updated(settings: Settings, collection: str) -> tuple[Optional[str], Optional[int]]:
    raw = get_setting(settings, _SETTING_PREFIX + collection)
    if not raw:
        return None, None
    ts, _, cnt = raw.partition("|")
    last_count = int(cnt) if cnt.isdigit() else None
    return (ts or None), last_count


# ─── registry ────────────────────────────────────────────────────────────────

def _registry(settings: Settings) -> list[dict[str, str]]:
    """Ordered list of collections to report on, with display metadata."""
    cols: list[dict[str, str]] = [
        {"key": JIRA_COLLECTION, "label": "Jira tickets (dense)", "kind": "jira"},
        {"key": JIRA_HYBRID_COLLECTION, "label": "Jira tickets (hybrid)", "kind": "jira"},
        {"key": GITHUB_COLLECTION, "label": "GitHub commits", "kind": "commits"},
    ]
    for model_key, meta in CODEBASE_EMBEDDING_MODELS.items():
        cols.append({"key": model_key, "label": f"Codebase · {meta['label']}", "kind": "codebase"})
    cols.append(
        {"key": settings.rca_code_chunks_collection, "label": "RCA code chunks", "kind": "rca"}
    )
    return cols


# ─── live "updating" detection from the in-memory job store ───────────────────

def _updating_collections(job_store: Any, registry: list[dict[str, str]]) -> set[str]:
    """Collections that a currently-running background job is writing to."""
    updating: set[str] = set()
    codebase_keys = {c["key"] for c in registry if c["kind"] == "codebase"}
    rca_keys = {c["key"] for c in registry if c["kind"] == "rca"}
    try:
        jobs = job_store.list_recent(limit=10)
    except Exception:  # noqa: BLE001
        return updating
    for job in jobs:
        if getattr(job, "status", None) not in ("pending", "running"):
            continue
        action = getattr(job, "action", "") or ""
        totals = getattr(job, "totals", {}) or {}
        meta = getattr(job, "meta", {}) or {}
        if action == "rca_code_index_build":
            updating |= rca_keys
        if action == "jira_tickets_only" or totals.get("jira_embedding_documents"):
            updating.add(JIRA_COLLECTION)
            updating.add(JIRA_HYBRID_COLLECTION)
        if totals.get("codebase_embedding_documents") or action in ("update", "regenerate", "create_new"):
            model = meta.get("embedding_model")
            if model in codebase_keys:
                updating.add(model)
            else:
                # Model unknown (older job) — flag all codebase collections so the
                # panel still shows activity rather than silently missing it.
                updating |= codebase_keys
    return updating


# ─── qdrant probe ────────────────────────────────────────────────────────────

def _vector_dim(info: Any) -> Optional[int]:
    """Best-effort extraction of the dense vector size from a collection info."""
    try:
        vectors = info.config.params.vectors
    except Exception:  # noqa: BLE001
        return None
    size = getattr(vectors, "size", None)
    if isinstance(size, int):
        return size
    # Named-vector config: a dict of {name: VectorParams}.
    if isinstance(vectors, dict):
        for params in vectors.values():
            s = getattr(params, "size", None)
            if isinstance(s, int):
                return s
    return None


def get_embeddings_status(settings: Settings, job_store: Any) -> dict[str, Any]:
    """Assemble the full status payload for the live embeddings panel."""
    registry = _registry(settings)
    updating = _updating_collections(job_store, registry)

    reachable = True
    reach_error: Optional[str] = None
    existing: set[str] = set()
    client = None
    if not settings.qdrant_url:
        reachable = False
        reach_error = "QDRANT_URL is not configured"
    else:
        try:
            from app.qdrant_store import _get_client

            client = _get_client(settings.qdrant_url, settings.qdrant_api_key or None)
            existing = {c.name for c in client.get_collections().collections}
        except Exception as exc:  # noqa: BLE001
            reachable = False
            reach_error = str(exc)

    collections: list[dict[str, Any]] = []
    for entry in registry:
        key = entry["key"]
        last_updated, last_count = _read_last_updated(settings, key)
        item: dict[str, Any] = {
            "key": key,
            "label": entry["label"],
            "kind": entry["kind"],
            "exists": False,
            "points": None,
            "vector_dim": None,
            "last_updated": last_updated,
            "updating": key in updating,
            "health": "unknown",
        }
        if not reachable:
            item["health"] = "unreachable"
        elif key not in existing:
            item["health"] = "missing"
        else:
            item["exists"] = True
            try:
                item["points"] = client.count(key).count
            except Exception as exc:  # noqa: BLE001
                item["points"] = last_count
                log.debug("count(%s) failed: %s", key, exc)
            try:
                item["vector_dim"] = _vector_dim(client.get_collection(key))
            except Exception as exc:  # noqa: BLE001
                log.debug("get_collection(%s) failed: %s", key, exc)
            item["health"] = "ok" if (item["points"] or 0) > 0 else "empty"
        collections.append(item)

    if not reachable:
        overall = "unreachable"
    elif any(c["health"] in ("missing", "empty") for c in collections):
        overall = "degraded"
    else:
        overall = "ok"

    return {
        "reachable": reachable,
        "error": reach_error,
        "overall": overall,
        "updating": bool(updating),
        "qdrant_url": settings.qdrant_url,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "collections": collections,
    }

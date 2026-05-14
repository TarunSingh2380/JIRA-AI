"""Qdrant vector store operations for commit and Jira ticket embeddings.

Collections managed:
  github_commits  – BGE-M3 vectors for commit summaries
  jira_tickets    – BGE-M3 vectors for ticket summaries + descriptions

Gracefully skips upsert if qdrant-client is not installed or the server
is unreachable — embedding generation is best-effort.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

log = logging.getLogger(__name__)

GITHUB_COLLECTION = "github_commits"
JIRA_COLLECTION = "jira_tickets"
VECTOR_SIZE = 1024  # BGE-M3 output dimensionality


def _get_client(url: str, api_key: Optional[str] = None):
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        raise RuntimeError(
            "qdrant-client not installed. Add it to requirements.txt and reinstall."
        ) from exc
    return QdrantClient(url=url, api_key=api_key or None)


def _ensure_collection(client, name: str) -> None:
    try:
        from qdrant_client.models import Distance, VectorParams
    except ImportError:
        return
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        log.info("Created Qdrant collection '%s'", name)


def _stable_id(seed: str) -> str:
    """Derive a deterministic UUID from a string so upserts are idempotent."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))


# ─── Jira tickets ────────────────────────────────────────────────────────────

def upsert_jira_embeddings(
    qdrant_url: str,
    tickets: list[dict[str, Any]],
    embeddings: list[Optional[list[float]]],
    api_key: Optional[str] = None,
) -> int:
    """Store Jira ticket embeddings in Qdrant. Returns the number of points written."""
    try:
        from qdrant_client.models import PointStruct
    except ImportError:
        log.warning("qdrant-client not installed; skipping Jira embedding storage")
        return 0

    try:
        client = _get_client(qdrant_url, api_key)
        _ensure_collection(client, JIRA_COLLECTION)

        points: list[PointStruct] = []
        for ticket, emb in zip(tickets, embeddings):
            if emb is None:
                continue
            fields = ticket.get("fields", {}) or {}
            key = ticket.get("key", "")
            points.append(
                PointStruct(
                    id=_stable_id(key or str(uuid.uuid4())),
                    vector=emb,
                    payload={
                        "key": key,
                        "summary": (fields.get("summary") or "")[:300],
                        "status": (fields.get("status") or {}).get("name", ""),
                        "issue_type": (fields.get("issuetype") or {}).get("name", ""),
                        "project_key": key.rsplit("-", 1)[0] if "-" in key else key,
                    },
                )
            )

        if points:
            client.upsert(collection_name=JIRA_COLLECTION, points=points)
            log.info("Stored %d Jira ticket embeddings in Qdrant", len(points))

        return len(points)

    except Exception as exc:
        log.warning("Qdrant Jira upsert failed: %s", exc)
        return 0


# ─── GitHub commits ──────────────────────────────────────────────────────────

def upsert_commit_embeddings(
    qdrant_url: str,
    commits: list[dict[str, Any]],
    embeddings: list[Optional[list[float]]],
    api_key: Optional[str] = None,
) -> int:
    """Store commit summary embeddings in Qdrant. Returns the number of points written."""
    try:
        from qdrant_client.models import PointStruct
    except ImportError:
        log.warning("qdrant-client not installed; skipping commit embedding storage")
        return 0

    try:
        client = _get_client(qdrant_url, api_key)
        _ensure_collection(client, GITHUB_COLLECTION)

        points: list[PointStruct] = []
        for commit, emb in zip(commits, embeddings):
            if emb is None:
                continue
            sha = commit.get("sha", "")
            points.append(
                PointStruct(
                    id=_stable_id(sha or str(uuid.uuid4())),
                    vector=emb,
                    payload={
                        "sha": sha,
                        "summary": (commit.get("summary") or "")[:300],
                        "repo": commit.get("repo_full_name", ""),
                        "author_email": commit.get("author_email", ""),
                    },
                )
            )

        if points:
            client.upsert(collection_name=GITHUB_COLLECTION, points=points)
            log.info("Stored %d commit embeddings in Qdrant", len(points))

        return len(points)

    except Exception as exc:
        log.warning("Qdrant commit upsert failed: %s", exc)
        return 0

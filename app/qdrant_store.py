"""Qdrant vector store operations for commit and Jira ticket embeddings.

Collections managed:
  github_commits       – vectors for commit summaries
  jira_tickets         – vectors for ticket summaries + descriptions
  codebase_*           – model-specific vectors for source files

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
_DEFAULT_VECTOR_SIZE = 1024  # qwen3:0.6b and BGE-M3 both output 1024-dim vectors


def _get_client(url: str, api_key: Optional[str] = None):
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        raise RuntimeError(
            "qdrant-client not installed. Add it to requirements.txt and reinstall."
        ) from exc
    return QdrantClient(url=url, api_key=api_key or None)


def _infer_vector_size(embeddings: list[Optional[list[float]]]) -> int:
    """Return the dimension of the first non-None embedding, or the default."""
    for emb in embeddings:
        if emb is not None:
            return len(emb)
    return _DEFAULT_VECTOR_SIZE


def _ensure_collection(client, name: str, vector_size: int = _DEFAULT_VECTOR_SIZE) -> None:
    try:
        from qdrant_client.models import Distance, VectorParams
    except ImportError:
        return
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        log.info("Created Qdrant collection '%s' (dim=%d)", name, vector_size)


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
        _ensure_collection(client, JIRA_COLLECTION, _infer_vector_size(embeddings))

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
        _ensure_collection(client, GITHUB_COLLECTION, _infer_vector_size(embeddings))

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


# ─── Codebase files ──────────────────────────────────────────────────────────

def upsert_codebase_embeddings(
    qdrant_url: str,
    collection_name: str,
    documents: list[dict[str, Any]],
    embeddings: list[Optional[list[float]]],
    model_key: str,
    model_name: str,
    api_key: Optional[str] = None,
) -> int:
    """Store source-file embeddings in a model-specific Qdrant collection."""
    try:
        from qdrant_client.models import PointStruct
    except ImportError:
        log.warning("qdrant-client not installed; skipping codebase embedding storage")
        return 0

    try:
        client = _get_client(qdrant_url, api_key)
        _ensure_collection(client, collection_name, _infer_vector_size(embeddings))

        points: list[PointStruct] = []
        for doc, emb in zip(documents, embeddings):
            if emb is None:
                continue
            seed = f"{collection_name}:{doc.get('id') or doc.get('path')}"
            points.append(
                PointStruct(
                    id=_stable_id(seed),
                    vector=emb,
                    payload={
                        "id": doc.get("id", ""),
                        "repo": doc.get("repo", ""),
                        "repo_name": doc.get("repo_name", ""),
                        "path": doc.get("path", ""),
                        "language": doc.get("language", ""),
                        "extension": doc.get("extension", ""),
                        "lines": doc.get("lines", 0),
                        "model_key": model_key,
                        "model_name": model_name,
                        "text": (doc.get("text") or "")[:2000],
                    },
                )
            )

        if points:
            client.upsert(collection_name=collection_name, points=points)
            log.info(
                "Stored %d codebase embeddings in Qdrant collection '%s'",
                len(points),
                collection_name,
            )

        return len(points)

    except Exception as exc:
        log.warning("Qdrant codebase upsert failed: %s", exc)
        return 0

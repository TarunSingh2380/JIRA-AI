"""Semantic embeddings stored directly in Neo4j.

The graph keeps embeddings on :EmbeddingDocument nodes and links each one back
to the graph item it represents. This avoids duplicating vector properties
across many labels while still making search results graph-native.
"""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from neo4j import AsyncDriver

from config import settings


VECTOR_INDEX_NAME = "embedding_document_vector"
EMBEDDING_LABEL = "EmbeddingDocument"
DEFAULT_EMBEDDING_MODEL_KEY = "bge-m3"

EMBEDDING_MODEL_OPTIONS = {
    "bge-m3": {
        "label": "BGE-M3 (568M)",
        "model_name": settings.bge_m3_model_name,
        "revision": "main",
        "model_kwargs": {"use_safetensors": False},
        "snapshot_allow_patterns": [
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "sentencepiece.bpe.model",
            "pytorch_model.bin",
        ],
        "dimensions": 1024,
    },
    "qwen3-embedding-0.6b": {
        "label": "Qwen3-Embedding-0.6B",
        "model_name": "Qwen/Qwen3-Embedding-0.6B",
        "dimensions": 1024,
    },
    "mxbai-embed-large-v1": {
        "label": "mxbai-embed-large-v1 (335M)",
        "model_name": "mixedbread-ai/mxbai-embed-large-v1",
        "dimensions": 1024,
    },
}


@dataclass(slots=True)
class EmbeddingDocument:
    id: str
    kind: str
    source_key: str
    repo_full_name: str | None
    title: str
    text: str
    metadata: dict[str, Any]


def _cached_snapshot_path(model_name: str, revision: str | None) -> Path | None:
    cache_root = Path(os.getenv("TRANSFORMERS_CACHE") or os.getenv("HF_HOME") or "/cache/huggingface")
    model_dir = cache_root / f"models--{model_name.replace('/', '--')}"
    ref_path = model_dir / "refs" / (revision or "main")
    if not ref_path.exists():
        return None
    snapshot_id = ref_path.read_text(encoding="utf-8").strip()
    snapshot_path = model_dir / "snapshots" / snapshot_id
    return snapshot_path if snapshot_path.exists() else None


class SentenceTransformerEmbedder:
    def __init__(self, model_key: str | None = None) -> None:
        self.profile = resolve_embedding_model(model_key)
        self.model_key = self.profile["key"]
        self.model_label = self.profile["label"]
        self.model_name = self.profile["model_name"]
        self.revision = self.profile.get("revision")
        self.model_kwargs = dict(self.profile.get("model_kwargs") or {})
        self.model_load_path = self._resolve_model_load_path()
        self.model_revision = None if Path(self.model_load_path).exists() else self.revision
        self.dimensions = int(self.profile["dimensions"])

        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            raise RuntimeError(
                "sentence-transformers failed to import. Check the Repograph "
                f"Torch/Transformers dependency pins: {exc}"
            ) from exc

        try:
            self.model = SentenceTransformer(
                self.model_load_path,
                revision=self.model_revision,
                model_kwargs=self.model_kwargs or None,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load embedding model {self.model_label} "
                f"({self.model_name}): {exc}"
            ) from exc

    def _resolve_model_load_path(self) -> str:
        allow_patterns = self.profile.get("snapshot_allow_patterns")
        if not allow_patterns:
            return self.model_name

        try:
            from huggingface_hub import snapshot_download
        except Exception as exc:
            raise RuntimeError(f"huggingface-hub failed to import: {exc}") from exc

        try:
            return snapshot_download(
                repo_id=self.model_name,
                revision=self.revision,
                allow_patterns=list(allow_patterns),
                cache_dir=os.getenv("TRANSFORMERS_CACHE") or os.getenv("HF_HOME"),
            )
        except Exception as exc:
            cached_path = _cached_snapshot_path(self.model_name, self.revision)
            if cached_path:
                return str(cached_path)
            raise RuntimeError(
                f"Failed to resolve embedding model snapshot {self.model_name}: {exc}"
            ) from exc

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return await asyncio.to_thread(self._encode, texts)

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed_documents([text])
        return vectors[0]

    def _encode(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self.model.encode(
            list(texts),
            batch_size=settings.semantic_embed_batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.astype(float).tolist() for vector in vectors]


async def ensure_embedding_schema(driver: AsyncDriver, dimensions: int | None = None) -> None:
    dimensions = dimensions or settings.semantic_embedding_dimensions
    index_query = f"""
    CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
    FOR (d:{EMBEDDING_LABEL}) ON (d.embedding)
    OPTIONS {{indexConfig: {{
      `vector.dimensions`: {dimensions},
      `vector.similarity_function`: 'cosine'
    }}}}
    """
    async with driver.session(database=settings.neo4j_database) as session:
        await session.run(
            """
            CREATE CONSTRAINT embedding_document_id IF NOT EXISTS
            FOR (d:EmbeddingDocument) REQUIRE d.id IS UNIQUE
            """
        )
        await session.run(index_query)


async def rebuild_embeddings(
    driver: AsyncDriver,
    *,
    kinds: Sequence[str] | None = None,
    limit: int | None = None,
    batch_size: int | None = None,
    model_key: str | None = None,
) -> dict[str, Any]:
    embedder = SentenceTransformerEmbedder(model_key)
    await ensure_embedding_schema(driver, dimensions=embedder.dimensions)
    docs = await fetch_embedding_documents(driver, kinds=kinds, limit=limit)
    batch = batch_size or settings.semantic_embed_batch_size
    written = 0

    for chunk in _chunks(docs, batch):
        vectors = await embedder.embed_documents([doc.text for doc in chunk])
        rows = [
            {
                "id": f"{embedder.model_key}:{doc.id}",
                "source_document_id": doc.id,
                "kind": doc.kind,
                "source_key": doc.source_key,
                "repo_full_name": doc.repo_full_name,
                "title": doc.title,
                "text": doc.text,
                "metadata": doc.metadata,
                "metadata_json": json.dumps(doc.metadata, ensure_ascii=False, default=str),
                "embedding": vector,
                "model_key": embedder.model_key,
                "model_label": embedder.model_label,
                "model": embedder.model_name,
                "dimensions": len(vector),
            }
            for doc, vector in zip(chunk, vectors)
        ]
        await upsert_embedding_documents(driver, rows)
        written += len(rows)

    return {
        "documents": len(docs),
        "embedded": written,
        "embedding_model_key": embedder.model_key,
        "embedding_model": embedder.model_name,
        "embedding_model_label": embedder.model_label,
        "embedding_dimensions": embedder.dimensions,
    }


async def semantic_search(
    driver: AsyncDriver,
    query: str,
    *,
    repos: Sequence[str] | None = None,
    kinds: Sequence[str] | None = None,
    top_k: int = 10,
    model_key: str | None = None,
) -> list[dict[str, Any]]:
    embedder = SentenceTransformerEmbedder(model_key)
    await ensure_embedding_schema(driver, dimensions=embedder.dimensions)
    vector = await embedder.embed_query(query)
    repo_filter = list(repos or [])
    kind_filter = list(kinds or [])
    cypher = f"""
    CALL db.index.vector.queryNodes('{VECTOR_INDEX_NAME}', $top_k, $embedding)
    YIELD node, score
    WHERE ($repos = [] OR node.repo_full_name IN $repos)
      AND ($kinds = [] OR node.kind IN $kinds)
      AND (
        coalesce(node.embedding_model_key, '') = $model_key
        OR coalesce(node.embedding_model, '') = $model_name
      )
    RETURN node.id AS id,
           node.kind AS kind,
           node.source_key AS source_key,
           node.repo_full_name AS repo_full_name,
           node.title AS title,
           node.text AS text,
           node.metadata_json AS metadata_json,
           node.embedding_model_key AS embedding_model_key,
           node.embedding_model AS embedding_model,
           score
    ORDER BY score DESC
    """
    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(
            cypher,
            top_k=max(1, min(top_k, 100)),
            embedding=vector,
            repos=repo_filter,
            kinds=kind_filter,
            model_key=embedder.model_key,
            model_name=embedder.model_name,
        )
        rows = []
        async for record in result:
            data = record.data()
            data["metadata"] = json.loads(data.pop("metadata_json") or "{}")
            rows.append(data)
        return rows


async def fetch_embedding_documents(
    driver: AsyncDriver,
    *,
    kinds: Sequence[str] | None = None,
    limit: int | None = None,
) -> list[EmbeddingDocument]:
    wanted = set(kinds or ["repo", "commit", "file", "jira_ticket"])
    max_docs = limit if limit is not None else settings.semantic_max_docs_per_run
    docs: list[EmbeddingDocument] = []
    async with driver.session(database=settings.neo4j_database) as session:
        remaining = max_docs if max_docs and max_docs > 0 else None

        async def add_docs(kind: str, query: str) -> None:
            nonlocal remaining
            if kind not in wanted:
                return
            if remaining is not None and remaining <= 0:
                return
            kind_docs = await _fetch(session, query, limit=remaining)
            docs.extend(kind_docs)
            if remaining is not None:
                remaining -= len(kind_docs)

        if "repo" in wanted:
            await add_docs("repo", _QUERY_REPO_DOCS)
        if "commit" in wanted:
            await add_docs("commit", _QUERY_COMMIT_DOCS)
        if "file" in wanted:
            await add_docs("file", _QUERY_FILE_DOCS)
        if "jira_ticket" in wanted:
            await add_docs("jira_ticket", _QUERY_JIRA_DOCS)

    if max_docs and max_docs > 0:
        docs = docs[:max_docs]
    return docs


async def upsert_embedding_documents(driver: AsyncDriver, rows: list[dict[str, Any]]) -> None:
    by_kind = {
        "repo": [row for row in rows if row["kind"] == "repo"],
        "commit": [row for row in rows if row["kind"] == "commit"],
        "file": [row for row in rows if row["kind"] == "file"],
        "jira_ticket": [row for row in rows if row["kind"] == "jira_ticket"],
    }
    async with driver.session(database=settings.neo4j_database) as session:
        for kind, kind_rows in by_kind.items():
            if not kind_rows:
                continue
            await session.run(_UPSERT_BY_KIND[kind], rows=kind_rows)


async def _fetch(
    session: Any,
    query: str,
    *,
    limit: int | None = None,
) -> list[EmbeddingDocument]:
    if limit is not None and limit > 0:
        result = await session.run(f"{query}\nLIMIT $limit", limit=limit)
    else:
        result = await session.run(query)
    docs = []
    async for record in result:
        data = record.data()
        text = _clean_text(data.pop("text", ""))
        if not text:
            continue
        docs.append(
            EmbeddingDocument(
                id=data["id"],
                kind=data["kind"],
                source_key=data["source_key"],
                repo_full_name=data.get("repo_full_name"),
                title=data.get("title") or data["source_key"],
                text=text,
                metadata=data.get("metadata") or {},
            )
        )
    return docs


def _chunks(items: Sequence[EmbeddingDocument], size: int) -> Iterable[Sequence[EmbeddingDocument]]:
    size = max(1, size)
    for index in range(0, len(items), size):
        yield items[index : index + size]


def _clean_text(value: str) -> str:
    return " ".join(str(value or "").split())


def resolve_embedding_model(model_key: str | None = None) -> dict[str, Any]:
    requested = (model_key or DEFAULT_EMBEDDING_MODEL_KEY).strip()
    if not requested:
        requested = DEFAULT_EMBEDDING_MODEL_KEY
    normalized = _normalize_model_key(requested)

    for key, profile in EMBEDDING_MODEL_OPTIONS.items():
        candidates = {
            key,
            profile["model_name"],
            profile["label"],
            profile["label"].split(" (", 1)[0],
        }
        if normalized in {_normalize_model_key(candidate) for candidate in candidates}:
            return {"key": key, **profile}

    allowed = ", ".join(EMBEDDING_MODEL_OPTIONS)
    raise ValueError(f"Unsupported embedding model '{requested}'. Expected one of: {allowed}")


def _normalize_model_key(value: str) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace("_", "-")
        .replace(" ", "")
    )


def embedding_model_options() -> list[dict[str, Any]]:
    return [
        {"key": key, **profile}
        for key, profile in EMBEDDING_MODEL_OPTIONS.items()
    ]


_QUERY_REPO_DOCS = """
MATCH (r:Repo)
RETURN
  'repo:' + r.full_name AS id,
  'repo' AS kind,
  r.full_name AS source_key,
  r.full_name AS repo_full_name,
  r.full_name AS title,
  {
    owner: r.owner,
    name: r.name,
    default_branch: r.default_branch,
    language: r.language,
    url: r.url
  } AS metadata,
  'Repository ' + r.full_name +
  coalesce(' language ' + r.language, '') +
  coalesce(' description ' + r.description, '') AS text
ORDER BY r.full_name
"""

_QUERY_COMMIT_DOCS = """
MATCH (c:Commit)-[:IN_REPO]->(r:Repo)
OPTIONAL MATCH (c)-[:AUTHORED_BY]->(a:Author)
RETURN
  'commit:' + c.sha AS id,
  'commit' AS kind,
  c.sha AS source_key,
  r.full_name AS repo_full_name,
  coalesce(c.summary, c.short_sha) AS title,
  {
    sha: c.sha,
    short_sha: c.short_sha,
    author_email: a.email,
    author_name: a.name,
    committed_at: toString(c.committed_at),
    additions: c.additions,
    deletions: c.deletions,
    files_changed_count: c.files_changed_count
  } AS metadata,
  'Commit in repository ' + r.full_name +
  coalesce(' by ' + a.name, '') +
  coalesce(' summary ' + c.summary, '') +
  coalesce(' message ' + c.message, '') AS text
ORDER BY c.committed_at DESC
"""

_QUERY_FILE_DOCS = """
MATCH (f:File)-[:IN_REPO]->(r:Repo)
OPTIONAL MATCH (c:Commit)-[touch:TOUCHES]->(f)
WHERE coalesce(f.current, true)
  AND size(coalesce(f.path, '')) <= 240
  AND (
    coalesce(f.extension, '') IN [
      'py', 'js', 'jsx', 'ts', 'tsx', 'java', 'kt', 'go', 'php', 'rb',
      'cs', 'cpp', 'c', 'h', 'hpp', 'rs', 'swift', 'scala', 'sql',
      'html', 'css', 'scss', 'vue', 'svelte', 'json', 'yaml', 'yml',
      'xml', 'md', 'sh'
    ]
    OR f.path ENDS WITH 'Dockerfile'
  )
  AND NOT toLower(f.path) ENDS WITH '.min.js'
  AND NONE(part IN split(toLower(f.path), '/') WHERE part IN [
    'node_modules', 'vendor', 'dist', 'build', '.next', 'coverage',
    'test-output', '__pycache__', '.git', 'qdrant_storage', 'storage',
    'tmp', 'logs', 'old', 'google-auth'
  ])
WITH f, r, count(touch) AS touch_count, max(c.committed_at) AS last_touched
RETURN
  'file:' + f.repo_full_name + ':' + f.path AS id,
  'file' AS kind,
  f.repo_full_name + ':' + f.path AS source_key,
  f.repo_full_name AS repo_full_name,
  f.path AS title,
  {
    path: f.path,
    extension: f.extension,
    current: f.current,
    touch_count: touch_count,
    last_touched_at: toString(last_touched)
  } AS metadata,
  'File ' + f.path + ' in repository ' + r.full_name +
  coalesce(' extension ' + f.extension, '') +
  ' touched ' + toString(touch_count) + ' times' AS text
ORDER BY last_touched DESC
"""

_QUERY_JIRA_DOCS = """
MATCH (t:JiraTicket)
RETURN
  'jira:' + t.key AS id,
  'jira_ticket' AS kind,
  t.key AS source_key,
  null AS repo_full_name,
  t.key + ' ' + coalesce(t.summary, '') AS title,
  {
    key: t.key,
    url: t.url,
    status: t.status,
    priority: t.priority,
    issue_type: t.issue_type,
    assignee: t.assignee,
    project_key: t.project_key,
    updated: t.updated
  } AS metadata,
  'Jira ticket ' + t.key +
  coalesce(' summary ' + t.summary, '') +
  coalesce(' description ' + t.description, '') +
  coalesce(' status ' + t.status, '') +
  coalesce(' priority ' + t.priority, '') AS text
ORDER BY t.updated DESC
"""

_SET_EMBEDDING_DOC = """
MERGE (d:EmbeddingDocument {id: row.id})
SET d.source_document_id = row.source_document_id,
    d.kind = row.kind,
    d.source_key = row.source_key,
    d.repo_full_name = row.repo_full_name,
    d.title = row.title,
    d.text = row.text,
    d.metadata_json = row.metadata_json,
    d.embedding = row.embedding,
    d.embedding_model_key = row.model_key,
    d.embedding_model_label = row.model_label,
    d.embedding_model = row.model,
    d.embedding_dimensions = row.dimensions,
    d.embedded_at = datetime()
"""

_UPSERT_BY_KIND = {
    "repo": f"""
    UNWIND $rows AS row
    {_SET_EMBEDDING_DOC}
    WITH d, row
    MATCH (source:Repo {{full_name: row.source_key}})
    MERGE (d)-[:EMBEDS]->(source)
    """,
    "commit": f"""
    UNWIND $rows AS row
    {_SET_EMBEDDING_DOC}
    WITH d, row
    MATCH (source:Commit {{sha: row.source_key}})
    MERGE (d)-[:EMBEDS]->(source)
    """,
    "file": f"""
    UNWIND $rows AS row
    {_SET_EMBEDDING_DOC}
    WITH d, row
    MATCH (source:File {{repo_full_name: row.repo_full_name, path: row.metadata.path}})
    MERGE (d)-[:EMBEDS]->(source)
    """,
    "jira_ticket": f"""
    UNWIND $rows AS row
    {_SET_EMBEDDING_DOC}
    WITH d, row
    MATCH (source:JiraTicket {{key: row.source_key}})
    MERGE (d)-[:EMBEDS]->(source)
    """,
}

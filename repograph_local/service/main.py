"""FastAPI service.

A small HTTP wrapper over the graph + (eventually) the vector store.

Run with:
  uvicorn service.main:app --host 0.0.0.0 --port 8088 --reload

Endpoints (Stage 1):
  GET  /health
  GET  /repos
  GET  /repos/{full_name}/recent_commits?days=30&limit=50
  GET  /authors/{email}/recent_activity?days=30
  GET  /files/touched_recently?keyword=razorpay&days=180

Endpoints (Stage 2, stubbed):
  GET  /functions/{qualified_name}/callers
  POST /pr/impact_analysis

Endpoints (Stage 3, stubbed):
  POST /search/semantic
  POST /ask                          # GraphRAG natural-language query
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from neo4j import AsyncGraphDatabase, AsyncDriver
from pydantic import BaseModel

from config import settings
from ingest.git_history import ingest_repo, make_driver
from ingest.local_repos import discover_from_settings

log = logging.getLogger(__name__)


# ─── Lifecycle ─────────────────────────────────────────────────────────

class AppState:
    driver: Optional[AsyncDriver] = None


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    state.driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        yield
    finally:
        if state.driver is not None:
            await state.driver.close()


app = FastAPI(title="repograph", version="0.1.0", lifespan=lifespan)


async def get_driver() -> AsyncDriver:
    if state.driver is None:
        raise HTTPException(503, "driver not initialised")
    return state.driver


# ─── Models ────────────────────────────────────────────────────────────

class RepoOut(BaseModel):
    full_name: str
    name: str
    language: Optional[str]
    private: bool
    default_branch: str


class CommitOut(BaseModel):
    sha: str
    short_sha: str
    summary: str
    committed_at: str
    author_name: str
    additions: int
    deletions: int
    files_changed_count: int


class FileTouchOut(BaseModel):
    repo: str
    path: str
    last_touched_at: str
    touch_count_180d: int


# ─── Stage 1 endpoints ─────────────────────────────────────────────────

@app.get("/health")
async def health(driver: AsyncDriver = Depends(get_driver)) -> dict:
    async with driver.session(database=settings.neo4j_database) as s:
        rec = await (await s.run("RETURN 1 AS ok")).single()
    return {"status": "ok", "neo4j": rec["ok"] == 1}


@app.get("/repos", response_model=list[RepoOut])
async def list_repos(driver: AsyncDriver = Depends(get_driver)) -> list[RepoOut]:
    q = """
    MATCH (r:Repo)
    RETURN r.full_name AS full_name, r.name AS name,
           r.language AS language, r.private AS private,
           r.default_branch AS default_branch
    ORDER BY r.full_name
    """
    async with driver.session(database=settings.neo4j_database) as s:
        result = await s.run(q)
        return [RepoOut(**r.data()) async for r in result]


@app.get("/repos/{full_name:path}/recent_commits", response_model=list[CommitOut])
async def recent_commits(
    full_name: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=500),
    driver: AsyncDriver = Depends(get_driver),
) -> list[CommitOut]:
    q = """
    MATCH (r:Repo {full_name: $full_name})<-[:IN_REPO]-(c:Commit)
    WHERE c.committed_at > datetime() - duration({days: $days})
    MATCH (c)-[:AUTHORED_BY]->(a:Author)
    RETURN c.sha AS sha, c.short_sha AS short_sha,
           c.summary AS summary,
           toString(c.committed_at) AS committed_at,
           a.name AS author_name,
           c.additions AS additions, c.deletions AS deletions,
           c.files_changed_count AS files_changed_count
    ORDER BY c.committed_at DESC LIMIT $limit
    """
    async with driver.session(database=settings.neo4j_database) as s:
        result = await s.run(q, full_name=full_name, days=days, limit=limit)
        return [CommitOut(**r.data()) async for r in result]


@app.get("/authors/{email}/recent_activity")
async def author_activity(
    email: str,
    days: int = Query(30, ge=1, le=365),
    driver: AsyncDriver = Depends(get_driver),
) -> list[dict]:
    q = """
    MATCH (a:Author {email: $email})<-[:AUTHORED_BY]-(c:Commit)-[:IN_REPO]->(r:Repo)
    WHERE c.committed_at > datetime() - duration({days: $days})
    RETURN r.full_name AS repo,
           count(c) AS commits,
           sum(c.additions) AS additions,
           sum(c.deletions) AS deletions
    ORDER BY commits DESC
    """
    async with driver.session(database=settings.neo4j_database) as s:
        result = await s.run(q, email=email.lower(), days=days)
        return [r.data() async for r in result]


@app.get("/files/touched_recently", response_model=list[FileTouchOut])
async def files_touched_recently(
    keyword: str = Query(..., min_length=2),
    days: int = Query(180, ge=1, le=730),
    limit: int = Query(50, ge=1, le=500),
    driver: AsyncDriver = Depends(get_driver),
) -> list[FileTouchOut]:
    q = """
    MATCH (c:Commit)-[t:TOUCHES]->(f:File)
    WHERE toLower(f.path) CONTAINS toLower($keyword)
      AND c.committed_at > datetime() - duration({days: $days})
    WITH f, count(t) AS touches, max(c.committed_at) AS last_touched
    RETURN f.repo_full_name AS repo,
           f.path AS path,
           toString(last_touched) AS last_touched_at,
           touches AS touch_count_180d
    ORDER BY last_touched DESC LIMIT $limit
    """
    async with driver.session(database=settings.neo4j_database) as s:
        result = await s.run(q, keyword=keyword, days=days, limit=limit)
        return [FileTouchOut(**r.data()) async for r in result]


# ─── Ingest trigger ────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    fetch_first: bool = False
    since_days: Optional[int] = None


class IngestResponse(BaseModel):
    repos_found: int
    repos_ingested: int
    commits_total: int
    branches_total: int
    failures: list[str]


@app.post("/ingest", response_model=IngestResponse)
async def trigger_ingest(
    req: IngestRequest,
    driver: AsyncDriver = Depends(get_driver),
) -> IngestResponse:
    """Discover local repos and ingest them into Neo4j (Stage 1)."""
    repos = discover_from_settings()
    if not repos:
        return IngestResponse(
            repos_found=0, repos_ingested=0, commits_total=0, branches_total=0, failures=[]
        )

    sem = asyncio.Semaphore(settings.ingest_concurrency)
    total_commits = 0
    total_branches = 0
    failures: list[str] = []

    async def _one(repo) -> None:
        nonlocal total_commits, total_branches
        async with sem:
            try:
                stats = await ingest_repo(driver, repo, fetch_first=req.fetch_first)
                total_commits += stats["commits"]
                total_branches += stats["branches"]
            except Exception as exc:
                log.exception("Ingest failed for %s", repo.full_name)
                failures.append(f"{repo.full_name}: {str(exc)[:200]}")

    await asyncio.gather(*(_one(r) for r in repos))

    return IngestResponse(
        repos_found=len(repos),
        repos_ingested=len(repos) - len(failures),
        commits_total=total_commits,
        branches_total=total_branches,
        failures=failures,
    )


# ─── Stage 2 stubs ─────────────────────────────────────────────────────

@app.get("/functions/{qualified_name:path}/callers")
async def function_callers(qualified_name: str) -> dict:
    """STUB. Implemented in Stage 2 once the tree-sitter overlay is in place.

    Returns the call graph for a function — every Function node that has an
    outgoing :CALLS edge to the target.
    """
    raise HTTPException(501, "Stage 2 (tree-sitter overlay) not yet implemented")


class ImpactRequest(BaseModel):
    repo: str
    changed_files: list[str]


@app.post("/pr/impact_analysis")
async def pr_impact(req: ImpactRequest) -> dict:
    """STUB. Stage 2: given changed files in a PR, compute reachable callers."""
    raise HTTPException(501, "Stage 2 (tree-sitter overlay) not yet implemented")


# ─── Stage 3 stubs ─────────────────────────────────────────────────────

class SemanticQuery(BaseModel):
    query: str
    repos: Optional[list[str]] = None
    kinds: Optional[list[str]] = None
    top_k: int = 10


@app.post("/search/semantic")
async def search_semantic(q: SemanticQuery, driver: AsyncDriver = Depends(get_driver)) -> dict:
    results = await search_bge_m3_embeddings(
        driver,
        q.query,
        repos=q.repos,
        kinds=q.kinds,
        top_k=q.top_k,
    )
    return {"query": q.query, "results": results}


class EmbeddingRebuildRequest(BaseModel):
    kinds: Optional[list[str]] = None
    limit: Optional[int] = None
    batch_size: Optional[int] = None


@app.post("/embeddings/rebuild")
async def rebuild_semantic_embeddings(
    req: EmbeddingRebuildRequest,
    driver: AsyncDriver = Depends(get_driver),
) -> dict:
    stats = await rebuild_bge_m3_embeddings(
        driver,
        kinds=req.kinds,
        limit=req.limit,
        batch_size=req.batch_size,
    )
    return {"embedding_model": settings.bge_m3_model_name, **stats}


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask(req: AskRequest) -> dict:
    """STUB. Stage 3: GraphRAG over the Neo4j graph + Qdrant vectors via LlamaIndex."""
    raise HTTPException(501, "Stage 3 (GraphRAG) not yet implemented")

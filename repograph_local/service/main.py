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
from ingest.local_repos import discover_from_settings, RepoInfo
from stage2_ast.cgc_bridge import ingest_ast_for_repo
from stage3_semantic.bge_m3_embeddings import (
    embedding_model_options,
    rebuild_embeddings as rebuild_semantic_embedding_documents,
    semantic_search as search_semantic_embeddings,
)
from stage3_semantic.jira_test_cases import analyze_jira_ticket

log = logging.getLogger("uvicorn.error")


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
    try:
        async with driver.session(database=settings.neo4j_database) as s:
            rec = await (await s.run("RETURN 1 AS ok")).single()
    except Exception as exc:
        log.warning("Neo4j health check failed: %s", exc)
        raise HTTPException(503, f"neo4j health check failed: {exc}") from exc
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

    log.info(
        "Starting graph ingest for %d repos (fetch_first=%s)",
        len(repos),
        req.fetch_first,
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

    if failures:
        log.warning(
            "Graph ingest completed with %d repo failure(s): %s",
            len(failures),
            failures[:5],
        )
    else:
        log.info(
            "Graph ingest completed successfully for %d repos",
            len(repos),
        )

    return IngestResponse(
        repos_found=len(repos),
        repos_ingested=len(repos) - len(failures),
        commits_total=total_commits,
        branches_total=total_branches,
        failures=failures,
    )


# ─── Stage 2 — AST / call-graph endpoints ─────────────────────────────

class AstIngestRequest(BaseModel):
    only: Optional[list[str]] = None  # repo full_names to restrict; None = all


class AstIngestResponse(BaseModel):
    repos_found: int
    repos_ingested: int
    functions_total: int
    classes_total: int
    calls_total: int
    extends_total: int
    failures: list[str]


@app.post("/ast/ingest", response_model=AstIngestResponse)
async def ast_ingest(req: AstIngestRequest) -> AstIngestResponse:
    """Run CGC tree-sitter AST ingest for local repos (Stage 2)."""
    repos = discover_from_settings()
    if req.only:
        only_set = set(req.only)
        repos = [r for r in repos if r.name in only_set or r.full_name in only_set]

    if not repos:
        return AstIngestResponse(
            repos_found=0, repos_ingested=0, functions_total=0,
            classes_total=0, calls_total=0, extends_total=0, failures=[],
        )

    log.info("Starting AST ingest for %d repos", len(repos))
    sem = asyncio.Semaphore(settings.ingest_concurrency)
    totals = {"functions": 0, "classes": 0, "calls": 0, "extends": 0}
    failures: list[str] = []

    async def _one(repo: RepoInfo) -> None:
        async with sem:
            try:
                result = await ingest_ast_for_repo(settings, repo)
                for k in totals:
                    totals[k] += result.get(k, 0)
            except Exception as exc:
                log.exception("AST ingest failed for %s", repo.full_name)
                failures.append(f"{repo.full_name}: {str(exc)[:200]}")

    await asyncio.gather(*(_one(r) for r in repos))

    return AstIngestResponse(
        repos_found=len(repos),
        repos_ingested=len(repos) - len(failures),
        functions_total=totals["functions"],
        classes_total=totals["classes"],
        calls_total=totals["calls"],
        extends_total=totals["extends"],
        failures=failures,
    )


@app.get("/functions/{qualified_name:path}/callers")
async def function_callers(
    qualified_name: str,
    driver: AsyncDriver = Depends(get_driver),
) -> dict:
    """Return all callers of a function (requires Stage 2 AST ingest to have run)."""
    q = """
    MATCH (caller:Function)-[:CALLS]->(fn:Function {qualified_name: $qn})
    RETURN caller.qualified_name AS qualified_name,
           caller.name AS name,
           caller.file_path AS file_path,
           caller.repo_full_name AS repo,
           caller.start_line AS start_line
    ORDER BY caller.qualified_name
    """
    async with driver.session(database=settings.neo4j_database) as s:
        result = await s.run(q, qn=qualified_name)
        callers = [r.data() async for r in result]
    return {"qualified_name": qualified_name, "callers": callers}


class ImpactRequest(BaseModel):
    repo: str
    changed_files: list[str]


@app.post("/pr/impact_analysis")
async def pr_impact(
    req: ImpactRequest,
    driver: AsyncDriver = Depends(get_driver),
) -> dict:
    """Return functions defined in changed files and their callers (Stage 2)."""
    q = """
    MATCH (fn:Function {repo_full_name: $repo})
    WHERE fn.file_path IN $files
    OPTIONAL MATCH (caller:Function)-[:CALLS]->(fn)
    RETURN fn.qualified_name AS function,
           fn.file_path AS file,
           collect(DISTINCT caller.qualified_name) AS callers
    ORDER BY fn.file_path, fn.start_line
    """
    async with driver.session(database=settings.neo4j_database) as s:
        result = await s.run(q, repo=req.repo, files=req.changed_files)
        rows = [r.data() async for r in result]
    return {"repo": req.repo, "changed_files": req.changed_files, "impact": rows}


# ─── Stage 3 stubs ─────────────────────────────────────────────────────

class SemanticQuery(BaseModel):
    query: str
    repos: Optional[list[str]] = None
    kinds: Optional[list[str]] = None
    top_k: int = 10
    model_key: str = "bge-m3"


@app.get("/embedding-models")
async def list_embedding_models() -> dict:
    return {"models": embedding_model_options()}


@app.post("/search/semantic")
async def search_semantic(q: SemanticQuery, driver: AsyncDriver = Depends(get_driver)) -> dict:
    try:
        results = await search_semantic_embeddings(
            driver,
            q.query,
            repos=q.repos,
            kinds=q.kinds,
            top_k=q.top_k,
            model_key=q.model_key,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        log.exception("Semantic search failed")
        raise HTTPException(500, str(exc)) from exc
    except Exception as exc:
        log.exception("Semantic search failed")
        raise HTTPException(500, str(exc)) from exc
    return {"query": q.query, "model_key": q.model_key, "results": results}


class EmbeddingRebuildRequest(BaseModel):
    kinds: Optional[list[str]] = None
    limit: Optional[int] = None
    batch_size: Optional[int] = None
    model_key: str = "bge-m3"


@app.post("/embeddings/rebuild")
async def rebuild_semantic_embeddings(
    req: EmbeddingRebuildRequest,
    driver: AsyncDriver = Depends(get_driver),
) -> dict:
    try:
        stats = await rebuild_semantic_embedding_documents(
            driver,
            kinds=req.kinds,
            limit=req.limit,
            batch_size=req.batch_size,
            model_key=req.model_key,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        log.exception("Semantic embedding rebuild failed")
        raise HTTPException(500, str(exc)) from exc
    except Exception as exc:
        log.exception("Semantic embedding rebuild failed")
        raise HTTPException(500, str(exc)) from exc
    return stats


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask(req: AskRequest) -> dict:
    """STUB. Stage 3: GraphRAG over the Neo4j graph + Qdrant vectors via LlamaIndex."""
    raise HTTPException(501, "Stage 3 (GraphRAG) not yet implemented")


# ─── JIRA → test-case generator ────────────────────────────────────────────────

class JiraTicketIn(BaseModel):
    issueKey: str
    summary: str
    description: str = ""
    assignee: str = ""
    dueDate: str = ""
    priority: str = ""
    issueType: str = ""
    status: str = ""
    reporter: str = ""


class JiraAnalyzeRequest(BaseModel):
    ticket: JiraTicketIn
    repo: str                             # e.g. "agrimfincapindia/agrimfincapindia"
    model_key: str = "bge-m3"            # embedding model for semantic search
    top_k: int = 15                       # semantic hits to retrieve
    anthropic_api_key: Optional[str] = None  # overrides ANTHROPIC_API_KEY in .env
    claude_model: str = "claude-sonnet-4-6"
    commit_history_days: int = 90


class JiraAnalyzeResponse(BaseModel):
    ticket_key: str
    repo: str
    semantic_hits_count: int
    functions_found: int
    classes_found: int
    commits_found: int
    test_cases: str                       # Markdown document
    model: str
    input_tokens: int
    output_tokens: int


@app.post("/jira/analyze", response_model=JiraAnalyzeResponse)
async def jira_analyze(
    req: JiraAnalyzeRequest,
    driver: AsyncDriver = Depends(get_driver),
) -> JiraAnalyzeResponse:
    """
    JIRA ticket → semantic search → graph context → Claude test cases.

    Requires ANTHROPIC_API_KEY in .env (or passed in the request body).
    Run Stage 1 ingest first (POST /ingest), and optionally Stage 2 AST
    ingest (POST /ast/ingest) for richer call-graph context.
    """
    try:
        result = await analyze_jira_ticket(
            driver,
            req.ticket.model_dump(by_alias=False),
            req.repo,
            model_key=req.model_key,
            top_k=req.top_k,
            api_key=req.anthropic_api_key,
            claude_model=req.claude_model,
            commit_history_days=req.commit_history_days,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        log.exception("JIRA analysis failed for %s", req.ticket.issueKey)
        raise HTTPException(500, str(exc)) from exc

    gc = result.graph_context
    return JiraAnalyzeResponse(
        ticket_key=result.ticket_key,
        repo=result.repo,
        semantic_hits_count=len(result.semantic_hits),
        functions_found=len(gc.get("functions", [])),
        classes_found=len(gc.get("classes", [])),
        commits_found=len(gc.get("recent_commits", [])),
        test_cases=result.test_cases,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )

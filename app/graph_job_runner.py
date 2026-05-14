"""Background job orchestrator for graph build operations.

Each job runs as an asyncio background task. Progress is written back to the
GraphJob in `job_store` *and* persisted to the `graph_jobs` table so history
survives restarts. GitHub repositories and git pull results are also logged.

Job actions:
  update            – git pull (optional) + ingest repos + Jira fetch/graph
  regenerate        – same as update, forces Jira re-fetch (ignores cache)
  create_new        – same as regenerate + clears Jira nodes in Neo4j first
  jira_tickets_only – skip repos; only fetch/graph Jira tickets
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import time
from typing import Any, Optional
from uuid import UUID

import psycopg
import requests

from app.config import settings
from app.graph_job import GraphJob
from app.jira_fetcher import fetch_all_tickets
from app.jira_graph import _adf_to_text, make_neo4j_driver, upsert_jira_tickets
from app.ollama_embedder import OllamaEmbedder
from app.qdrant_store import upsert_commit_embeddings, upsert_jira_embeddings
from app.repository_discovery import discover_graph_repositories

log = logging.getLogger(__name__)


# ─── PostgreSQL helpers ──────────────────────────────────────────────────────

def _db_connect() -> Optional[psycopg.Connection]:
    if not settings.database_url:
        return None
    try:
        return psycopg.connect(settings.database_url)
    except Exception as exc:
        log.warning("DB connection failed; job will not be persisted: %s", exc)
        return None


def _persist_job_start(job: GraphJob) -> None:
    conn = _db_connect()
    if conn is None:
        return
    with conn:
        conn.execute(
            """
            INSERT INTO graph_jobs (job_id, action, status, started_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (job_id) DO NOTHING
            """,
            (UUID(job.job_id), job.action, job.status),
        )


def _persist_job_progress(job: GraphJob) -> None:
    conn = _db_connect()
    if conn is None:
        return
    with conn:
        conn.execute(
            """
            UPDATE graph_jobs
            SET status      = %s,
                repos_total = %s,
                repos_done  = %s,
                jira_total  = %s,
                jira_done   = %s,
                error_msg   = %s,
                completed_at = %s
            WHERE job_id = %s
            """,
            (
                job.status,
                job.totals.get("repositories", 0),
                job.progress.get("repositories_done", 0),
                job.totals.get("jira_tickets", 0),
                job.progress.get("jira_tickets_done", 0),
                job.error,
                job.completed_at,
                UUID(job.job_id),
            ),
        )


def _upsert_repo_row(conn: psycopg.Connection, repo: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO github_repositories
            (name, full_name, container_path, host_path, remote_url, branch, current_commit, last_seen)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (container_path) DO UPDATE
            SET name           = EXCLUDED.name,
                full_name      = EXCLUDED.full_name,
                host_path      = EXCLUDED.host_path,
                remote_url     = EXCLUDED.remote_url,
                branch         = EXCLUDED.branch,
                current_commit = EXCLUDED.current_commit,
                last_seen      = NOW()
        """,
        (
            repo.get("name", ""),
            repo.get("name", ""),        # full_name same as name for local repos
            repo.get("container_path") or repo.get("path", ""),
            repo.get("path", ""),
            repo.get("remote_url", ""),
            repo.get("branch", ""),
            repo.get("current_commit", ""),
        ),
    )


def _log_pull(
    conn: psycopg.Connection,
    job_id: str,
    repo_name: str,
    container_path: str,
    success: bool,
    output: str,
) -> None:
    conn.execute(
        """
        INSERT INTO github_pull_log (job_id, repo_name, container_path, success, output)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (UUID(job_id), repo_name, container_path, success, output[:2000]),
    )


# ─── Git pull helper ─────────────────────────────────────────────────────────

def _git_pull(repo: dict[str, Any]) -> tuple[bool, str]:
    """Run git pull --ff-only. Returns (success, output)."""
    container_path = repo.get("container_path") or repo.get("path", "")
    if not container_path:
        return False, "no container_path"
    try:
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=container_path,
            capture_output=True,
            text=True,
            timeout=120,
            env={**__import__("os").environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        out = (result.stdout + result.stderr).strip()
        return result.returncode == 0, out
    except Exception as exc:
        return False, str(exc)


# ─── Repograph service proxy ─────────────────────────────────────────────────

def _trigger_repograph_ingest(fetch_first: bool = False) -> dict[str, Any]:
    url = f"{settings.repograph_base_url}/ingest"
    try:
        resp = requests.post(
            url,
            json={"fetch_first": fetch_first},
            timeout=settings.external_request_timeout_seconds * 20,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        log.warning("Repograph service not reachable at %s; skipping repo ingest", url)
        return {"skipped": True, "reason": "repograph service not reachable"}
    except Exception as exc:
        log.warning("Repograph ingest call failed: %s", exc)
        return {"skipped": True, "reason": str(exc)}


# ─── Commit embeddings via Neo4j query ───────────────────────────────────────

async def _embed_recent_commits(
    embedder: OllamaEmbedder,
    driver,
    database: str,
    limit: int = 500,
) -> int:
    if not settings.qdrant_url:
        return 0
    query = """
    MATCH (c:Commit)-[:IN_REPO]->(r:Repo)
    WHERE c.committed_at > datetime() - duration({days: 90})
    RETURN c.sha AS sha, c.summary AS summary,
           r.full_name AS repo_full_name, c.author_email AS author_email
    ORDER BY c.committed_at DESC LIMIT $limit
    """
    async with driver.session(database=database) as session:
        result = await session.run(query, limit=limit)
        commits = [dict(r) async for r in result]
    if not commits:
        return 0
    texts = [f"{c.get('repo_full_name', '')}: {c.get('summary', '')}" for c in commits]
    embeddings = await asyncio.to_thread(embedder.embed_batch, texts)
    return upsert_commit_embeddings(
        qdrant_url=settings.qdrant_url,
        commits=commits,
        embeddings=embeddings,
        api_key=settings.qdrant_api_key or None,
    )


# ─── Main job runner ──────────────────────────────────────────────────────────

async def run_graph_job(
    job: GraphJob,
    pull_latest_code: bool = True,
    fetch_latest_jira: bool = True,
    include_jira_in_graph: bool = True,
) -> None:
    """Execute a graph build job in the background; updates `job` and persists to DB."""
    job.status = "running"
    _persist_job_start(job)
    log.info("Graph job %s started (action=%s)", job.job_id, job.action)

    neo4j_driver = None

    try:
        action = job.action
        jira_only = action == "jira_tickets_only"
        clear_jira = action == "create_new"
        force_jira_refresh = action in ("create_new", "regenerate")

        # ── Step 1: GitHub repos ──────────────────────────────────────────
        if not jira_only:
            repos = discover_graph_repositories(settings)
            job.totals["repositories"] = len(repos)
            _persist_job_progress(job)

            conn = _db_connect()
            if conn:
                with conn:
                    for repo in repos:
                        _upsert_repo_row(conn, repo)

            if pull_latest_code:
                log.info("Running git pull on %d repos ...", len(repos))
                for repo in repos:
                    success, output = await asyncio.to_thread(_git_pull, repo)
                    if conn:
                        with conn:
                            _log_pull(
                                conn, job.job_id,
                                repo.get("name", ""),
                                repo.get("container_path") or repo.get("path", ""),
                                success, output,
                            )

            log.info("Triggering repograph ingest for %d repos ...", len(repos))
            ingest_result = await asyncio.to_thread(_trigger_repograph_ingest, pull_latest_code)
            log.info("Repograph ingest result: %s", ingest_result)

            job.progress["repositories_done"] = len(repos)
            _persist_job_progress(job)

        # ── Step 2: Jira tickets ──────────────────────────────────────────
        if jira_only or (fetch_latest_jira and include_jira_in_graph):
            log.info("Fetching Jira tickets (force_refresh=%s) ...", force_jira_refresh)
            tickets = await asyncio.to_thread(fetch_all_tickets, force_jira_refresh)
            job.totals["jira_tickets"] = len(tickets)
            _persist_job_progress(job)
            log.info("Got %d Jira tickets", len(tickets))

            if tickets and include_jira_in_graph:
                neo4j_driver = make_neo4j_driver(
                    settings.neo4j_uri,
                    settings.neo4j_user,
                    settings.neo4j_password,
                )
                written = await upsert_jira_tickets(
                    driver=neo4j_driver,
                    tickets=tickets,
                    jira_base_url=settings.jira_base_url,
                    database=settings.neo4j_database,
                    clear_first=clear_jira,
                )
                job.progress["jira_tickets_done"] = written
                _persist_job_progress(job)
                log.info("Wrote %d Jira tickets to Neo4j", written)

                # ── Step 3: Jira embeddings ──────────────────────────────
                if settings.qdrant_url:
                    embedder = OllamaEmbedder(settings.ollama_url, settings.ollama_embed_model)
                    if embedder.is_available():
                        log.info("Generating BGE-M3 embeddings for %d Jira tickets ...", len(tickets))
                        texts = _ticket_embed_texts(tickets)
                        embeddings = await asyncio.to_thread(embedder.embed_batch, texts)
                        stored = upsert_jira_embeddings(
                            qdrant_url=settings.qdrant_url,
                            tickets=tickets,
                            embeddings=embeddings,
                            api_key=settings.qdrant_api_key or None,
                        )
                        log.info("Stored %d Jira embeddings in Qdrant", stored)
                    else:
                        log.info("Ollama BGE-M3 not available; skipping Jira embeddings")

        # ── Step 4: Commit embeddings ────────────────────────────────────
        if not jira_only and settings.qdrant_url:
            if neo4j_driver is None:
                neo4j_driver = make_neo4j_driver(
                    settings.neo4j_uri,
                    settings.neo4j_user,
                    settings.neo4j_password,
                )
            embedder = OllamaEmbedder(settings.ollama_url, settings.ollama_embed_model)
            if embedder.is_available():
                log.info("Generating BGE-M3 embeddings for recent commits ...")
                stored = await _embed_recent_commits(
                    embedder, neo4j_driver, settings.neo4j_database
                )
                log.info("Stored %d commit embeddings in Qdrant", stored)

        job.mark_done()
        _persist_job_progress(job)
        log.info("Graph job %s completed", job.job_id)

    except Exception as exc:
        log.exception("Graph job %s failed: %s", job.job_id, exc)
        job.mark_failed(str(exc))
        _persist_job_progress(job)

    finally:
        if neo4j_driver is not None:
            await neo4j_driver.close()


def _ticket_embed_texts(tickets: list[dict]) -> list[str]:
    result = []
    for t in tickets:
        fields = t.get("fields", {}) or {}
        summary = (fields.get("summary") or "")[:200]
        desc = _adf_to_text(fields.get("description"))[:500]
        result.append(f"{summary}\n{desc}".strip())
    return result

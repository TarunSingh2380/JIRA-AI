"""Git-history ingestion (Stage 1, local-mode).

Walks pre-cloned repositories on disk. For each repo:
  1. Optionally `git fetch --all --tags --prune` (--fetch-first CLI flag).
  2. Walk every commit reachable from local branches AND origin/* remotes.
  3. Emit Repo, Commit, Author, File, Branch nodes and edges.
  4. Stream-batch into Neo4j using parameterised MERGE.

Idempotent: re-runs only insert new nodes/edges; nothing is deleted.
"""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

import pygit2  # type: ignore[import-untyped]
from neo4j import AsyncGraphDatabase, AsyncDriver

from config import settings
from ingest.local_repos import RepoInfo

log = logging.getLogger(__name__)


# ─── Optional pre-fetch ──────────────────────────────────────────────────

def fetch_remote(repo: RepoInfo) -> None:
    """Run `git fetch --all --tags --prune` so we walk the latest objects.

    Quiet on success; logs on failure but doesn't raise — we'd rather ingest
    the local state we have than abort the whole repo.
    """
    try:
        subprocess.run(
            ["git", "fetch", "--all", "--tags", "--prune", "--quiet"],
            cwd=str(repo.local_path),
            check=True,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            timeout=300,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log.warning("Fetch failed for %s: %s — proceeding with local state", repo.full_name, e)


# ─── Walking commits ─────────────────────────────────────────────────────

@dataclass(slots=True)
class CommitRow:
    sha: str
    short_sha: str
    message: str
    summary: str
    authored_at: datetime
    committed_at: datetime
    author_email: str
    author_name: str
    parents: list[str]
    additions: int
    deletions: int
    files_changed_count: int
    files_changed: list["FileChange"]


@dataclass(slots=True)
class FileChange:
    path: str
    change_type: str        # "A" | "M" | "D" | "R" | "C"
    additions: int
    deletions: int


def _walk_commits(
    repo_path: Path,
    *,
    since: Optional[datetime] = None,
) -> Iterator[CommitRow]:
    """Yield CommitRow for every commit reachable from local AND remote refs.

    Walking *remote* refs too is important in local-mode: a working-tree clone
    typically only has `main` checked out locally, but origin/* has every branch.
    """
    repo = pygit2.Repository(str(repo_path))

    # Collect walk roots: every local branch head + every remote branch head.
    root_ids: list[pygit2.Oid] = []

    for name in repo.branches.local:
        ref = repo.lookup_branch(name)
        if ref is not None and ref.target is not None:
            root_ids.append(ref.target)

    for name in repo.branches.remote:
        # Skip HEAD-aliases like 'origin/HEAD'
        if name.endswith("/HEAD"):
            continue
        ref = repo.lookup_branch(name, pygit2.GIT_BRANCH_REMOTE)
        if ref is not None and ref.target is not None:
            root_ids.append(ref.target)

    if not root_ids:
        # Empty repo or no branches; fall back to whatever HEAD points at.
        try:
            root_ids = [repo.head.target]
        except (pygit2.GitError, KeyError):
            return

    seen: set[str] = set()
    walker = repo.walk(root_ids[0], pygit2.GIT_SORT_TIME)
    for rid in root_ids[1:]:
        walker.push(rid)

    for commit in walker:
        sha = str(commit.id)
        if sha in seen:
            continue
        seen.add(sha)

        committed_at = datetime.fromtimestamp(commit.commit_time, tz=timezone.utc)
        if since and committed_at < since:
            continue

        parents = [str(p) for p in commit.parent_ids]
        additions = 0
        deletions = 0
        files: list[FileChange] = []

        try:
            if parents:
                parent_commit = repo[commit.parent_ids[0]]
                diff = parent_commit.tree.diff_to_tree(commit.tree)
            else:
                diff = commit.tree.diff_to_tree(swap=True)
            stats = diff.stats
            additions = stats.insertions
            deletions = stats.deletions
            status_map = {
                pygit2.GIT_DELTA_ADDED:    "A",
                pygit2.GIT_DELTA_MODIFIED: "M",
                pygit2.GIT_DELTA_DELETED:  "D",
                pygit2.GIT_DELTA_RENAMED:  "R",
                pygit2.GIT_DELTA_COPIED:   "C",
            }
            for patch in diff:
                delta = patch.delta
                path = delta.new_file.path or delta.old_file.path
                files.append(
                    FileChange(
                        path=path,
                        change_type=status_map.get(delta.status, "M"),
                        additions=patch.line_stats[1],
                        deletions=patch.line_stats[2],
                    )
                )
        except Exception as e:  # noqa: BLE001
            log.debug("Diff stats failed for %s: %s", sha[:7], e)

        message = (commit.message or "").rstrip()
        summary = message.split("\n", 1)[0][:200]

        yield CommitRow(
            sha=sha,
            short_sha=sha[:7],
            message=message,
            summary=summary,
            authored_at=datetime.fromtimestamp(commit.author.time, tz=timezone.utc),
            committed_at=committed_at,
            author_email=(commit.author.email or "").lower() or "unknown@local",
            author_name=commit.author.name or "unknown",
            parents=parents,
            additions=additions,
            deletions=deletions,
            files_changed_count=len(files),
            files_changed=files,
        )


def list_branches(repo_path: Path) -> list[tuple[str, str, bool]]:
    """Return [(branch_name, head_sha, is_remote)] for every branch in the repo."""
    repo = pygit2.Repository(str(repo_path))
    out: list[tuple[str, str, bool]] = []
    for name in repo.branches.local:
        ref = repo.lookup_branch(name)
        if ref and ref.target:
            out.append((name, str(ref.target), False))
    for name in repo.branches.remote:
        if name.endswith("/HEAD"):
            continue
        ref = repo.lookup_branch(name, pygit2.GIT_BRANCH_REMOTE)
        if ref and ref.target:
            out.append((name, str(ref.target), True))
    return out


# ─── Neo4j writers ───────────────────────────────────────────────────────

_CYPHER_UPSERT_REPO = """
MERGE (r:Repo {full_name: $full_name})
SET r.name = $name,
    r.owner = $owner,
    r.default_branch = $default_branch,
    r.private = $private,
    r.language = $language,
    r.description = $description,
    r.url = $url,
    r.local_path = $local_path,
    r.ingested_at = datetime()
RETURN r
"""

_CYPHER_UPSERT_COMMITS_BATCH = """
UNWIND $commits AS c
MERGE (commit:Commit {sha: c.sha})
ON CREATE SET
    commit.short_sha = c.short_sha,
    commit.message = c.message,
    commit.summary = c.summary,
    commit.authored_at = c.authored_at,
    commit.committed_at = c.committed_at,
    commit.additions = c.additions,
    commit.deletions = c.deletions,
    commit.files_changed_count = c.files_changed_count
WITH commit, c
MERGE (repo:Repo {full_name: $repo_full_name})
MERGE (commit)-[:IN_REPO]->(repo)
MERGE (author:Author {email: c.author_email})
ON CREATE SET author.name = c.author_name
MERGE (commit)-[:AUTHORED_BY]->(author)
WITH commit, c
UNWIND c.parents AS parent_sha
MERGE (parent:Commit {sha: parent_sha})
MERGE (commit)-[:PARENT]->(parent)
"""

_CYPHER_UPSERT_FILE_TOUCHES_BATCH = """
UNWIND $rows AS row
MATCH (commit:Commit {sha: row.commit_sha})
MATCH (repo:Repo {full_name: $repo_full_name})
MERGE (file:File {repo_full_name: $repo_full_name, path: row.path})
ON CREATE SET
    file.extension = row.extension,
    file.current = true
MERGE (file)-[:IN_REPO]->(repo)
MERGE (commit)-[t:TOUCHES {change_type: row.change_type}]->(file)
ON CREATE SET
    t.additions = row.additions,
    t.deletions = row.deletions
"""

_CYPHER_UPSERT_BRANCHES = """
UNWIND $branches AS b
MERGE (br:Branch {repo_full_name: $repo_full_name, name: b.name})
SET br.head_sha = b.head_sha,
    br.is_remote = b.is_remote
WITH br, b
MATCH (repo:Repo {full_name: $repo_full_name})
MERGE (br)-[:IN_REPO]->(repo)
WITH br, b
MATCH (c:Commit {sha: b.head_sha})
MERGE (br)-[:HEAD]->(c)
"""


def _ext_of(path: str) -> str:
    _, dot, ext = path.rpartition(".")
    return ext.lower() if dot else ""


async def upsert_repo(driver: AsyncDriver, repo: RepoInfo) -> None:
    async with driver.session(database=settings.neo4j_database) as session:
        await session.run(
            _CYPHER_UPSERT_REPO,
            full_name=repo.full_name,
            name=repo.name,
            owner=repo.owner,
            default_branch=repo.default_branch,
            private=repo.private,
            language=repo.language,
            description=repo.description,
            url=repo.url,
            local_path=str(repo.local_path),
        )


async def upsert_commits(
    driver: AsyncDriver,
    repo: RepoInfo,
    commits: list[CommitRow],
) -> None:
    if not commits:
        return
    commit_payload = [
        {
            "sha": c.sha,
            "short_sha": c.short_sha,
            "message": c.message,
            "summary": c.summary,
            "authored_at": c.authored_at,
            "committed_at": c.committed_at,
            "author_email": c.author_email,
            "author_name": c.author_name,
            "parents": c.parents,
            "additions": c.additions,
            "deletions": c.deletions,
            "files_changed_count": c.files_changed_count,
        }
        for c in commits
    ]
    file_rows: list[dict[str, Any]] = []
    for c in commits:
        for f in c.files_changed:
            file_rows.append(
                {
                    "commit_sha": c.sha,
                    "path": f.path,
                    "extension": _ext_of(f.path),
                    "change_type": f.change_type,
                    "additions": f.additions,
                    "deletions": f.deletions,
                }
            )

    async with driver.session(database=settings.neo4j_database) as session:
        await session.run(
            _CYPHER_UPSERT_COMMITS_BATCH,
            commits=commit_payload,
            repo_full_name=repo.full_name,
        )
        if file_rows:
            await session.run(
                _CYPHER_UPSERT_FILE_TOUCHES_BATCH,
                rows=file_rows,
                repo_full_name=repo.full_name,
            )


async def upsert_branches(
    driver: AsyncDriver,
    repo: RepoInfo,
    branches: list[tuple[str, str, bool]],
) -> None:
    if not branches:
        return
    payload = [{"name": n, "head_sha": s, "is_remote": is_remote} for n, s, is_remote in branches]
    async with driver.session(database=settings.neo4j_database) as session:
        await session.run(
            _CYPHER_UPSERT_BRANCHES,
            branches=payload,
            repo_full_name=repo.full_name,
        )


# ─── Per-repo orchestrator ───────────────────────────────────────────────

async def ingest_repo(
    driver: AsyncDriver,
    repo: RepoInfo,
    *,
    fetch_first: bool = False,
) -> dict[str, int]:
    """End-to-end ingest for one repo. Returns simple stats."""
    log.info("Ingesting %s (%s)", repo.full_name, repo.local_path)

    if fetch_first:
        await asyncio.to_thread(fetch_remote, repo)

    await upsert_repo(driver, repo)

    since = None
    if settings.since_days:
        from datetime import timedelta
        since = datetime.now(timezone.utc) - timedelta(days=settings.since_days)

    commits_iter = await asyncio.to_thread(
        lambda: list(_walk_commits(repo.local_path, since=since))
    )

    for i in range(0, len(commits_iter), settings.commit_batch_size):
        chunk = commits_iter[i : i + settings.commit_batch_size]
        await upsert_commits(driver, repo, chunk)
        log.debug(
            "  %s: wrote %d/%d commits",
            repo.full_name,
            i + len(chunk),
            len(commits_iter),
        )

    branches = await asyncio.to_thread(list_branches, repo.local_path)
    await upsert_branches(driver, repo, branches)

    stats = {"commits": len(commits_iter), "branches": len(branches)}
    log.info("Finished %s: %s", repo.full_name, stats)
    return stats


# ─── Driver factory ──────────────────────────────────────────────────────

def make_driver() -> AsyncDriver:
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

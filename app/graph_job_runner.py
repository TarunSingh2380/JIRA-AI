"""Local graph build jobs with live progress for repos and Jira tickets."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import threading
import traceback
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from app.config import Settings
from app.graph_job_store import GraphJobStoreError, PostgresGraphJobStore, graph_job_to_dict
from app.graph_job_types import GraphJob
from app.repository_discovery import discover_graph_repositories
from app.schemas import GraphAdminTriggerRequest


class GraphJobRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jobs: dict[str, GraphJob] = {}
        self._lock = threading.Lock()
        self._store = self._build_store()
        self._load_persisted_jobs()

    def start(self, request: GraphAdminTriggerRequest) -> dict[str, Any]:
        now = _now()
        job = GraphJob(
            id=str(uuid.uuid4()),
            action=request.action,
            status="queued",
            created_at=now,
            updated_at=now,
            options=request.model_dump(),
            totals={"repositories": 0, "jira_tickets": 0},
            progress={"repositories_done": 0, "jira_tickets_done": 0},
        )
        with self._lock:
            self._jobs[job.id] = job
        self._persist(job)

        thread = threading.Thread(target=self._run_job, args=(job.id, request), daemon=True)
        thread.start()
        return self.get(job.id)["job"]

    def get(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None and self._store is not None:
            job = self._store.get(job_id)
            if job is not None:
                with self._lock:
                    self._jobs[job.id] = job
        if job is None:
            raise KeyError(job_id)
        return {"job": graph_job_to_dict(job)}

    def list(self) -> list[dict[str, Any]]:
        if self._store is not None:
            persisted = self._store.list()
            with self._lock:
                for job in persisted:
                    self._jobs[job.id] = job
        with self._lock:
            jobs = [graph_job_to_dict(job) for job in self._jobs.values()]
        return sorted(jobs, key=lambda item: item["updated_at"], reverse=True)

    def latest_jira_tickets(self) -> list[dict[str, Any]]:
        if self._store is not None:
            for job in self._store.list():
                if job.jira_tickets:
                    return deepcopy(job.jira_tickets)
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda item: item.created_at, reverse=True)
            for job in jobs:
                if job.jira_tickets:
                    return deepcopy(job.jira_tickets)
        return []

    def _run_job(self, job_id: str, request: GraphAdminTriggerRequest) -> None:
        try:
            self._set_status(job_id, "running")
            self._log(job_id, "Job started")
            jira_only = request.action == "jira_tickets_only"
            repositories = [] if jira_only else discover_graph_repositories(self.settings)
            self._update(job_id, repositories=repositories, totals={"repositories": len(repositories), "jira_tickets": 0})

            if not self.settings.neo4j_password:
                raise RuntimeError("NEO4J_PASSWORD is required to build the graph")

            self._prepare_graph(job_id, request.action)

            if jira_only:
                self._log(job_id, "Jira-only job: skipping GitHub repository pull and code ingestion")
            elif request.pull_latest_code:
                self._pull_repositories(job_id, repositories)

            if not jira_only:
                self._ingest_repositories(job_id, repositories)

            should_fetch_jira = jira_only or request.fetch_latest_jira_tickets or request.include_jira_tickets
            should_ingest_jira = jira_only or request.include_jira_tickets
            if should_fetch_jira:
                tickets = self._fetch_jira_tickets(job_id)
                self._update(job_id, jira_tickets=tickets, totals={"repositories": len(repositories), "jira_tickets": len(tickets)})
                if should_ingest_jira:
                    self._ingest_jira_tickets(job_id, tickets)

            if request.build_embeddings and self.settings.graph_job_build_embeddings:
                self._build_embeddings(job_id)

            self._set_status(job_id, "completed")
            self._log(job_id, "Job completed")
        except Exception as exc:  # noqa: BLE001
            self._set_status(job_id, "failed", error=str(exc))
            self._log(job_id, f"Job failed: {exc}", level="error")
            self._log(job_id, traceback.format_exc(), level="debug")

    def _prepare_graph(self, job_id: str, action: str) -> None:
        self._log(job_id, "Connecting to Neo4j")
        async def prepare() -> None:
            from neo4j import AsyncGraphDatabase

            driver = AsyncGraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
            try:
                async with driver.session(database=self.settings.neo4j_database) as session:
                    if action in {"regenerate", "create_new"}:
                        self._log(job_id, "Clearing existing Neo4j graph")
                        await session.run("MATCH (n) DETACH DELETE n")
                    elif action == "jira_tickets_only":
                        self._log(job_id, "Clearing existing Jira ticket graph")
                        await session.run(
                            """
                            MATCH (n)
                            WHERE n:JiraTicket OR n:JiraProject OR n:JiraComment OR n:JiraChange
                            DETACH DELETE n
                            """
                        )

                    schema_path = Path("repograph_local/schema/cypher_init.cypher")
                    if schema_path.exists():
                        self._log(job_id, "Applying Neo4j schema")
                        for statement in _cypher_statements(schema_path.read_text(encoding="utf-8")):
                            await session.run(statement)

                    await session.run(
                        """
                        CREATE CONSTRAINT jira_ticket_key IF NOT EXISTS
                        FOR (t:JiraTicket) REQUIRE t.key IS UNIQUE
                        """
                    )
                    await session.run(
                        """
                        CREATE CONSTRAINT jira_comment_id IF NOT EXISTS
                        FOR (c:JiraComment) REQUIRE c.id IS UNIQUE
                        """
                    )
                    await session.run(
                        """
                        CREATE CONSTRAINT jira_change_id IF NOT EXISTS
                        FOR (c:JiraChange) REQUIRE c.id IS UNIQUE
                        """
                    )
            finally:
                await driver.close()

        asyncio.run(prepare())

    def _pull_repositories(self, job_id: str, repositories: list[dict[str, Any]]) -> None:
        self._log(job_id, "Fetching latest GitHub refs in local clones")
        for repo in repositories:
            self._repo_status(job_id, repo["name"], "fetching")
            path = repo.get("container_path") or repo["path"]
            fetch_result = subprocess.run(
                ["git", "-C", path, "fetch", "--all", "--tags", "--prune"],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
                timeout=300,
            )
            if fetch_result.returncode != 0:
                repo["fetch_status"] = "failed"
                repo["fetch_output"] = (fetch_result.stderr or fetch_result.stdout).strip()[:1000]
                self._repo_status(job_id, repo["name"], "fetch_failed")
                self._log(job_id, f"Fetch failed for {repo['name']}: {repo['fetch_output']}", level="warning")
                continue

            repo["fetch_status"] = "ok"
            repo["fetch_output"] = (fetch_result.stdout or fetch_result.stderr).strip()[:1000]

            pull_result = subprocess.run(
                ["git", "-C", path, "pull", "--ff-only"],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
                timeout=300,
            )
            if pull_result.returncode == 0:
                repo["pull_status"] = "ok"
                repo["pull_output"] = (pull_result.stdout or pull_result.stderr).strip()[:1000]
                self._repo_status(job_id, repo["name"], "pulled")
                continue

            repo["pull_status"] = "skipped_after_fetch"
            repo["pull_output"] = (pull_result.stderr or pull_result.stdout).strip()[:1000]
            self._repo_status(job_id, repo["name"], "fetched")
            self._log(
                job_id,
                f"Pull skipped for {repo['name']} after successful fetch: {repo['pull_output']}",
                level="warning",
            )

    def _ingest_repositories(self, job_id: str, repositories: list[dict[str, Any]]) -> None:
        self._log(job_id, "Ingesting GitHub code history into Neo4j")
        asyncio.run(self._ingest_repositories_async(job_id, repositories))

    async def _ingest_repositories_async(self, job_id: str, repositories: list[dict[str, Any]]) -> None:
        repograph_path = str(Path("repograph_local").resolve())
        if repograph_path not in sys.path:
            sys.path.insert(0, repograph_path)

        from ingest.git_history import make_driver

        driver = make_driver()
        try:
            for repo in repositories:
                repo_info = _repo_info_from_discovered(repo)
                timeout = self.settings.graph_job_repo_timeout_seconds
                self._repo_status(job_id, repo["name"], "ingesting")
                self._log(job_id, f"Ingesting repo {repo['name']} with timeout={timeout}s")
                try:
                    stats = await asyncio.wait_for(
                        self._ingest_one_repository_streaming(job_id, driver, repo, repo_info),
                        timeout=timeout,
                    )
                    repo["ingest_status"] = "ok"
                    repo["commits"] = stats.get("commits", 0)
                    repo["branches"] = stats.get("branches", 0)
                    self._repo_status(job_id, repo["name"], "completed", stats=stats)
                except asyncio.TimeoutError:
                    repo["ingest_status"] = "timeout"
                    repo["ingest_error"] = f"Timed out after {timeout}s"
                    self._repo_status(job_id, repo["name"], "timeout")
                    self._log(job_id, f"Timed out ingesting {repo['name']} after {timeout}s; moving on", level="warning")
                except Exception as exc:  # noqa: BLE001
                    repo["ingest_status"] = "failed"
                    repo["ingest_error"] = str(exc)[:1000]
                    self._repo_status(job_id, repo["name"], "failed")
                    self._log(job_id, f"Failed ingesting {repo['name']}: {exc}", level="error")
                self._increment(job_id, "repositories_done")
        finally:
            await driver.close()

    async def _ingest_one_repository_streaming(
        self,
        job_id: str,
        driver: Any,
        repo: dict[str, Any],
        repo_info: Any,
    ) -> dict[str, int]:
        from ingest.git_history import (
            _walk_commits,
            list_branches,
            upsert_branches,
            upsert_commits,
            upsert_repo,
        )

        await upsert_repo(driver, repo_info)

        batch = []
        commit_count = 0
        batch_size = self.settings.graph_job_commit_batch_size
        self._repo_status(job_id, repo["name"], "scanning", stats={"commits_scanned": 0})

        for commit in _walk_commits(repo_info.local_path, since=None):
            batch.append(commit)
            commit_count += 1

            if commit_count % 100 == 0:
                self._repo_status(
                    job_id,
                    repo["name"],
                    "scanning",
                    stats={"commits_scanned": commit_count},
                )
                await asyncio.sleep(0)

            if len(batch) >= batch_size:
                await upsert_commits(driver, repo_info, batch)
                batch = []
                self._repo_status(
                    job_id,
                    repo["name"],
                    "writing",
                    stats={"commits": commit_count, "commits_scanned": commit_count},
                )
                self._log(job_id, f"{repo['name']}: wrote {commit_count} commits")

        if batch:
            await upsert_commits(driver, repo_info, batch)

        branches = await asyncio.to_thread(list_branches, repo_info.local_path)
        await upsert_branches(driver, repo_info, branches)

        return {"commits": commit_count, "branches": len(branches)}

    def _fetch_jira_tickets(self, job_id: str) -> list[dict[str, Any]]:
        if not self._jira_configured():
            self._log(job_id, "Skipping Jira fetch because Jira credentials are not configured", level="warning")
            return []

        project_keys = self._jira_project_keys()
        if project_keys:
            jql_scope = " OR ".join(f'project = "{key}"' for key in project_keys)
            jql = f"({jql_scope}) ORDER BY updated DESC"
            self._log(job_id, f"Fetching Jira tickets for projects: {', '.join(project_keys)}")
        else:
            jql = 'created >= "1970/01/01" ORDER BY updated DESC'
            self._log(job_id, "Fetching Jira tickets across all visible projects")

        issues: list[dict[str, Any]] = []
        next_page_token = None
        max_results = 100
        limit = self.settings.graph_job_limit_jira_issues
        fields = [
            "summary",
            "description",
            "issuetype",
            "status",
            "priority",
            "assignee",
            "reporter",
            "created",
            "updated",
            "duedate",
            "project",
            "labels",
            "components",
        ]

        while True:
            body: dict[str, Any] = {
                "jql": jql,
                "maxResults": max_results,
                "fields": fields,
            }
            if next_page_token:
                body["nextPageToken"] = next_page_token

            page = self._jira_post("/rest/api/3/search/jql", json_body=body)
            batch = page.get("issues", [])
            issues.extend(batch)
            self._log(job_id, f"Fetched {len(issues)} Jira issues")

            if limit and len(issues) >= limit:
                issues = issues[:limit]
                break

            if page.get("isLast") or not batch:
                break
            next_page_token = page.get("nextPageToken")
            if not next_page_token:
                break

        tickets: list[dict[str, Any]] = []
        self._update(job_id, totals={"repositories": self._repo_total(job_id), "jira_tickets": len(issues)})
        for index, issue in enumerate(issues, start=1):
            key = issue.get("key", "")
            self._log(job_id, f"Fetching Jira history {index}/{len(issues)}: {key}")
            comments = self._jira_get_all(f"/rest/api/3/issue/{key}/comment", "comments")
            changelog = self._jira_get_all(f"/rest/api/3/issue/{key}/changelog", "values")
            ticket = _normalize_jira_issue(issue, comments, changelog, self.settings.jira_base_url)
            tickets.append(ticket)
            self._update(job_id, jira_tickets=tickets)
            self._increment(job_id, "jira_tickets_done")

        return tickets

    def _ingest_jira_tickets(self, job_id: str, tickets: list[dict[str, Any]]) -> None:
        if not tickets:
            return
        self._log(job_id, "Ingesting Jira tickets and history into Neo4j")

        async def ingest() -> None:
            from neo4j import AsyncGraphDatabase

            driver = AsyncGraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
            try:
                async with driver.session(database=self.settings.neo4j_database) as session:
                    for ticket in tickets:
                        await session.run(_CYPHER_UPSERT_JIRA_TICKET, ticket=ticket)
                        if ticket["comments"]:
                            await session.run(_CYPHER_UPSERT_JIRA_COMMENTS, key=ticket["key"], comments=ticket["comments"])
                        if ticket["changes"]:
                            await session.run(_CYPHER_UPSERT_JIRA_CHANGES, key=ticket["key"], changes=ticket["changes"])
            finally:
                await driver.close()

        asyncio.run(ingest())

    def _build_embeddings(self, job_id: str) -> None:
        self._log(job_id, "Building BGE-M3 embeddings in Neo4j")

        async def build() -> dict[str, int]:
            repograph_path = str(Path("repograph_local").resolve())
            if repograph_path not in sys.path:
                sys.path.insert(0, repograph_path)

            from ingest.git_history import make_driver
            from stage3_semantic.bge_m3_embeddings import rebuild_embeddings

            driver = make_driver()
            try:
                return await rebuild_embeddings(driver)
            finally:
                await driver.close()

        stats = asyncio.run(build())
        self._update(job_id, totals={**self.get(job_id)["job"]["totals"], "embedding_documents": stats["documents"]})
        self._log(job_id, f"BGE-M3 embeddings complete: {stats['embedded']} documents")

    def _jira_get_all(self, path: str, item_key: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        start_at = 0
        while True:
            data = self._jira_get(path, params={"startAt": start_at, "maxResults": 100})
            batch = data.get(item_key, [])
            items.extend(batch)
            if start_at + len(batch) >= data.get("total", len(items)) or not batch:
                break
            start_at += len(batch)
        return items

    def _jira_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = requests.get(
            f"{self.settings.jira_base_url}{path}",
            params=params,
            auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
            headers={"Accept": "application/json"},
            timeout=60,
        )
        return self._jira_response_json(response)

    def _jira_post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.settings.jira_base_url}{path}",
            json=json_body,
            auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=60,
        )
        return self._jira_response_json(response)

    def _jira_response_json(self, response: requests.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            message = f"{response.status_code} {response.reason} for {response.url}: {response.text[:1000]}"
            raise requests.HTTPError(message, response=response)
        return response.json() if response.content else {}

    def _jira_configured(self) -> bool:
        return bool(
            self.settings.jira_base_url
            and self.settings.jira_email
            and self.settings.jira_api_token
        )

    def _jira_project_keys(self) -> list[str]:
        return [
            key.strip()
            for key in self.settings.jira_project_keys.split(",")
            if key.strip()
        ]

    def _repo_total(self, job_id: str) -> int:
        with self._lock:
            return self._jobs[job_id].totals.get("repositories", 0)

    def _set_status(self, job_id: str, status: str, error: str | None = None) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = status
            job.error = error
            job.updated_at = _now()
            snapshot = deepcopy(job)
        self._persist(snapshot)

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                if key == "totals":
                    job.totals.update(value)
                else:
                    setattr(job, key, value)
            job.updated_at = _now()
            snapshot = deepcopy(job)
        self._persist(snapshot)

    def _increment(self, job_id: str, key: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.progress[key] = job.progress.get(key, 0) + 1
            job.updated_at = _now()
            snapshot = deepcopy(job)
        self._persist(snapshot)

    def _repo_status(self, job_id: str, name: str, status: str, stats: dict[str, int] | None = None) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for repo in job.repositories:
                if repo.get("name") == name:
                    repo["status"] = status
                    repo["updated_at"] = _now()
                    if stats:
                        repo.update(stats)
                    break
            job.updated_at = _now()
            snapshot = deepcopy(job)
        self._persist(snapshot)

    def _log(self, job_id: str, message: str, level: str = "info") -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.logs.append({"ts": _now(), "level": level, "message": message})
            job.logs = job.logs[-500:]
            job.updated_at = _now()
            snapshot = deepcopy(job)
        self._persist(snapshot)

    def _build_store(self) -> PostgresGraphJobStore | None:
        try:
            store = PostgresGraphJobStore(self.settings)
            store.init_schema()
            return store
        except GraphJobStoreError:
            return None
        except Exception:
            return None

    def _load_persisted_jobs(self) -> None:
        if self._store is None:
            return
        for job in self._store.list():
            self._jobs[job.id] = job

    def _persist(self, job: GraphJob) -> None:
        if self._store is None:
            return
        try:
            self._store.save(job)
        except Exception:
            return


def _repo_info_from_discovered(repo: dict[str, Any]) -> Any:
    from ingest.local_repos import RepoInfo

    owner, name = _owner_name(repo)
    return RepoInfo(
        full_name=f"{owner}/{name}",
        name=name,
        owner=owner,
        default_branch=repo.get("branch") or "main",
        private=None,
        language=None,
        description=None,
        url=repo.get("remote_url") or None,
        clone_url=repo.get("remote_url") or None,
        local_path=Path(repo.get("container_path") or repo["path"]),
    )


def _owner_name(repo: dict[str, Any]) -> tuple[str, str]:
    remote = repo.get("remote_url") or ""
    name = repo["name"]
    if ":" in remote and "/" in remote:
        tail = remote.rsplit(":", 1)[-1]
        owner, repo_name = tail.split("/", 1)
        return owner, repo_name.removesuffix(".git")
    if "github.com/" in remote:
        tail = remote.split("github.com/", 1)[-1]
        owner, repo_name = tail.split("/", 1)
        return owner, repo_name.removesuffix(".git").rstrip("/")
    return "local", name


def _normalize_jira_issue(
    issue: dict[str, Any],
    comments: list[dict[str, Any]],
    changelog: list[dict[str, Any]],
    base_url: str,
) -> dict[str, Any]:
    fields = issue.get("fields", {})
    project = fields.get("project") if isinstance(fields.get("project"), dict) else {}
    return {
        "id": issue.get("id"),
        "key": issue.get("key"),
        "url": f"{base_url}/browse/{issue.get('key')}",
        "summary": fields.get("summary") or "",
        "description": _adf_text(fields.get("description")),
        "issue_type": _name(fields.get("issuetype")),
        "status": _name(fields.get("status")),
        "priority": _name(fields.get("priority")),
        "assignee": _display_name(fields.get("assignee")),
        "reporter": _display_name(fields.get("reporter")),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "due_date": fields.get("duedate"),
        "project_key": project.get("key"),
        "project_name": project.get("name"),
        "labels": fields.get("labels") or [],
        "components": [_name(component) for component in fields.get("components", []) or []],
        "comment_count": len(comments),
        "change_count": sum(len(history.get("items", [])) for history in changelog),
        "comments": [
            {
                "id": comment.get("id"),
                "author": _display_name(comment.get("author")),
                "created": comment.get("created"),
                "updated": comment.get("updated"),
                "body": _adf_text(comment.get("body")),
            }
            for comment in comments
        ],
        "changes": _normalize_changelog(changelog),
    }


def _normalize_changelog(changelog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for history in changelog:
        for index, item in enumerate(history.get("items", [])):
            rows.append(
                {
                    "id": f"{history.get('id')}-{index}",
                    "author": _display_name(history.get("author")),
                    "created": history.get("created"),
                    "field": item.get("field"),
                    "from_value": item.get("fromString") or item.get("from"),
                    "to_value": item.get("toString") or item.get("to"),
                }
            )
    return rows


def _adf_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = []
        if value.get("type") == "text" and value.get("text"):
            parts.append(value["text"])
        for child in value.get("content", []) or []:
            parts.append(_adf_text(child))
        return " ".join(part for part in parts if part).strip()
    if isinstance(value, list):
        return " ".join(_adf_text(item) for item in value).strip()
    return json.dumps(value, ensure_ascii=False)


def _name(value: Any) -> str:
    return value.get("name", "") if isinstance(value, dict) else ""


def _display_name(value: Any) -> str:
    return value.get("displayName", "") if isinstance(value, dict) else ""


def _cypher_statements(text: str) -> list[str]:
    statements = []
    current = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";"))
            current = []
    if current:
        statements.append("\n".join(current))
    return statements


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_CYPHER_UPSERT_JIRA_TICKET = """
MERGE (ticket:JiraTicket {key: $ticket.key})
SET ticket.id = $ticket.id,
    ticket.url = $ticket.url,
    ticket.summary = $ticket.summary,
    ticket.description = $ticket.description,
    ticket.issue_type = $ticket.issue_type,
    ticket.status = $ticket.status,
    ticket.priority = $ticket.priority,
    ticket.assignee = $ticket.assignee,
    ticket.reporter = $ticket.reporter,
    ticket.created = $ticket.created,
    ticket.updated = $ticket.updated,
    ticket.due_date = $ticket.due_date,
    ticket.project_key = $ticket.project_key,
    ticket.project_name = $ticket.project_name,
    ticket.labels = $ticket.labels,
    ticket.components = $ticket.components,
    ticket.comment_count = $ticket.comment_count,
    ticket.change_count = $ticket.change_count,
    ticket.ingested_at = datetime()
MERGE (project:JiraProject {key: $ticket.project_key})
SET project.name = $ticket.project_name
MERGE (ticket)-[:IN_JIRA_PROJECT]->(project)
"""

_CYPHER_UPSERT_JIRA_COMMENTS = """
UNWIND $comments AS comment
MERGE (c:JiraComment {id: comment.id})
SET c.author = comment.author,
    c.created = comment.created,
    c.updated = comment.updated,
    c.body = comment.body
WITH c
MATCH (ticket:JiraTicket {key: $key})
MERGE (ticket)-[:HAS_COMMENT]->(c)
"""

_CYPHER_UPSERT_JIRA_CHANGES = """
UNWIND $changes AS change
MERGE (c:JiraChange {id: change.id})
SET c.author = change.author,
    c.created = change.created,
    c.field = change.field,
    c.from_value = change.from_value,
    c.to_value = change.to_value
WITH c
MATCH (ticket:JiraTicket {key: $key})
MERGE (ticket)-[:HAS_CHANGE]->(c)
"""

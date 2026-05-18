"""FastAPI entry point for Jira ticket analysis and graph DB administration.

Graph admin flow (replaces n8n):
  POST /graph-admin/trigger  → starts background job, returns job_id
  GET  /graph-admin/jobs     → list recent jobs
  GET  /graph-admin/jobs/{job_id} → poll job status + progress
"""

import asyncio
import json
import logging

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from fastapi.responses import HTMLResponse, Response

from app.code_analysis_report import build_code_analysis_report
from app.config import settings
from app.conversation_store import ConversationStoreError, PostgresConversationStore
from app.db_init import run_migrations
from app.exceptions import LLMConfigurationError, PromptNotFoundError
from app.graph_context import GraphContextClient
from app.graph_job import job_store
from app.graph_job_runner import run_graph_job
from app.jira_client import JiraClient
from app.json_utils import parse_model_json, review_status, review_text
from app.llm_client import build_llm_client
from app.prompt_store import PromptStore
from app.repository_discovery import discover_graph_repositories
from app.schemas import (
    AnalyzeTicketRequest,
    AnalyzeTicketResponse,
    CodeAnalysisReportRequest,
    GraphAdminTriggerRequest,
    GraphAdminTriggerResponse,
    GraphJobResponse,
    JiraReviewWorkflowRequest,
    JiraReviewWorkflowResponse,
    PromptListResponse,
    SlackReplyRequest,
    SlackReplyResponse,
    SlackMessageRequest,
    SlackMessageResponse,
)
from app.slack_client import SlackClient
from app.slack_review_workflow import SlackReviewWorkflow
from app.ticket_analyzer import TicketAnalyzer

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        run_migrations(settings.database_url)
    except Exception as exc:
        log.error("DB migration failed on startup: %s", exc)
    yield


app = FastAPI(
    title="Jira AI Ticket Analyzer",
    version="0.2.0",
    description="Jira ticket analysis, Slack review workflow, and graph DB administration.",
    lifespan=lifespan,
)

prompt_store = PromptStore(settings.prompt_dir)

SLACK_CHAT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Send the reply of the user message and only "
    "in a single line of 11-21 words."
)


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "model": settings.llm_model,
    }


@app.get("/prompts", response_model=PromptListResponse)
def list_prompts() -> PromptListResponse:
    return PromptListResponse(prompts=prompt_store.list_prompts())


# ─── Graph admin UI ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def graph_admin_ui() -> str:
    return GRAPH_ADMIN_HTML


@app.get("/graph-admin", response_class=HTMLResponse)
def graph_admin_ui_alias() -> str:
    return GRAPH_ADMIN_HTML


# ─── Graph admin API ─────────────────────────────────────────────────────────

@app.get("/graph-admin/repositories")
def graph_admin_repositories() -> dict[str, Any]:
    repositories = discover_graph_repositories(settings)
    return {
        "repository_count": len(repositories),
        "repositories": repositories,
        "excluded_repositories": _excluded_repositories(),
    }


@app.post("/graph-admin/trigger", response_model=GraphAdminTriggerResponse)
def graph_admin_trigger(
    request: GraphAdminTriggerRequest,
    background_tasks: BackgroundTasks,
) -> GraphAdminTriggerResponse:
    repositories = discover_graph_repositories(settings)

    job = job_store.create(action=request.action)

    background_tasks.add_task(
        run_graph_job,
        job,
        pull_latest_code=request.pull_latest_code,
        fetch_latest_jira=request.fetch_latest_jira_tickets,
        include_jira_in_graph=request.include_jira_tickets,
        build_embeddings=request.build_embeddings,
        embedding_model=request.embedding_model,
    )

    return GraphAdminTriggerResponse(
        job_id=job.job_id,
        action=job.action,
        status=job.status,
        repository_count=len(repositories),
        excluded_repositories=_excluded_repositories(),
    )


@app.get("/graph-admin/jobs", response_model=list[GraphJobResponse])
def list_graph_jobs(limit: int = 10) -> list[GraphJobResponse]:
    jobs = job_store.list_recent(limit=min(limit, 50))
    return [GraphJobResponse(**j.to_dict()) for j in jobs]


@app.get("/graph-admin/jobs/{job_id}", response_model=GraphJobResponse)
def get_graph_job(job_id: str) -> GraphJobResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return GraphJobResponse(**job.to_dict())


@app.post("/graph-admin/code-analysis-report")
async def download_code_analysis_report(request: CodeAnalysisReportRequest) -> Response:
    repositories = discover_graph_repositories(settings)
    selected = set(request.repositories)
    selected_repositories = [
        repo for repo in repositories
        if repo.get("name") in selected or repo.get("path") in selected
    ]
    if not selected_repositories:
        raise HTTPException(status_code=400, detail="Select at least one known repository")

    filename, markdown = await build_code_analysis_report(
        settings=settings,
        selected_repositories=selected_repositories,
        include_graph_context=request.include_graph_context,
        embedding_model=request.embedding_model,
    )
    return Response(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── Jira ticket cache browser ───────────────────────────────────────────────

@app.get("/graph-admin/jira-tickets")
def graph_admin_jira_tickets(
    limit: int = 100,
    offset: int = 0,
    project_key: str | None = None,
) -> dict[str, Any]:
    if not settings.database_url:
        return {"count": 0, "tickets": [], "error": "DATABASE_URL not configured"}
    try:
        import psycopg
        from psycopg.rows import dict_row

        where = "WHERE project_key = %s" if project_key else ""
        with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
            count_params = (project_key,) if project_key else ()
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM jira_ticket_cache {where}",
                count_params,
            ).fetchone()
            count = row["n"] if row else 0

            list_params = (project_key, limit, offset) if project_key else (limit, offset)
            tickets = conn.execute(
                f"""
                SELECT ticket_key, project_key, summary, status, issue_type,
                       priority, assignee_name, reporter_name, updated_at, fetched_at
                FROM jira_ticket_cache
                {where}
                ORDER BY updated_at DESC NULLS LAST
                LIMIT %s OFFSET %s
                """,
                list_params,
            ).fetchall()
            return {"count": count, "tickets": [dict(t) for t in tickets]}
    except Exception as exc:
        return {"count": 0, "tickets": [], "error": str(exc)}


@app.get("/graph-admin/fetch-logs")
def graph_admin_fetch_logs(limit: int = 100) -> dict[str, Any]:
    if not settings.database_url:
        return {"logs": [], "error": "DATABASE_URL not configured"}
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
            logs = conn.execute(
                """
                SELECT project_key, ticket_count, from_cache, force_refresh,
                       duration_ms, error, fetched_at
                FROM jira_fetch_log
                ORDER BY fetched_at DESC NULLS LAST
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
            return {"logs": [dict(l) for l in logs]}
    except Exception as exc:
        return {"logs": [], "error": str(exc)}


# ─── Ticket analysis ─────────────────────────────────────────────────────────

@app.post("/analyze-ticket", response_model=AnalyzeTicketResponse)
def analyze_ticket(request: AnalyzeTicketRequest) -> AnalyzeTicketResponse:
    try:
        analyzer = TicketAnalyzer(
            settings=settings,
            prompt_store=prompt_store,
            llm_client=build_llm_client(settings),
        )
        result = analyzer.analyze(
            ticket_data=request.ticket_data,
            prompt_name=settings.default_prompt,
        )
        try:
            model_json = parse_model_json(result["model_output"])
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail="LLM returned non-JSON output. Use a prompt that returns only JSON.",
            ) from exc

        return AnalyzeTicketResponse(status=review_status(model_json), review=review_text(model_json))

    except PromptNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─── Chat ────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=SlackMessageResponse)
def reply_to_message(request: SlackMessageRequest) -> SlackMessageResponse:
    try:
        llm_client = build_llm_client(settings)
        llm_reply = llm_client.complete(SLACK_CHAT_SYSTEM_PROMPT, request.user_message).strip()
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SlackMessageResponse(userid=request.userid, llm_reply=llm_reply)


# ─── Jira review workflow ────────────────────────────────────────────────────

@app.post("/workflow/jira-review", response_model=JiraReviewWorkflowResponse)
def workflow_jira_review(request: JiraReviewWorkflowRequest) -> JiraReviewWorkflowResponse:
    try:
        workflow = build_workflow()
        result = workflow.handle_jira_review(
            ticket_data=request.ticket_data,
            slack_channel_id=request.slack_channel_id,
        )
        return JiraReviewWorkflowResponse(**result)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="LLM returned non-JSON output") from exc
    except (ConversationStoreError, LLMConfigurationError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/workflow/slack-reply", response_model=SlackReplyResponse)
def workflow_slack_reply(request: SlackReplyRequest) -> SlackReplyResponse:
    try:
        workflow = build_workflow()
        result = workflow.handle_slack_reply(
            user_id=request.user_id,
            channel_id=request.channel_id,
            thread_ts=request.thread_ts,
            text=request.text,
            event_ts=request.event_ts,
        )
        return SlackReplyResponse(**result)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="LLM returned non-JSON output") from exc
    except (ConversationStoreError, LLMConfigurationError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/workflow/slack-events")
def workflow_slack_events(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    event = payload.get("event")
    if not isinstance(event, dict):
        return {"ok": True, "ignored": "missing_event"}

    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return {"ok": True, "ignored": "bot_message"}

    thread_ts = event.get("thread_ts")
    text = event.get("text")
    channel_id = event.get("channel")
    user_id = event.get("user")
    if not all(isinstance(value, str) and value for value in [thread_ts, text, channel_id, user_id]):
        return {"ok": True, "ignored": "not_a_thread_reply"}

    response = workflow_slack_reply(
        SlackReplyRequest(
            user=user_id,
            channel=channel_id,
            thread_ts=thread_ts,
            text=text,
            event_ts=event.get("ts"),
        )
    )
    return {"ok": True, "result": response.model_dump()}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def build_workflow() -> SlackReviewWorkflow:
    return SlackReviewWorkflow(
        settings=settings,
        prompt_store=prompt_store,
        llm_client=build_llm_client(settings),
        store=PostgresConversationStore(settings),
        slack_client=SlackClient(settings),
        jira_client=JiraClient(settings),
        graph_client=GraphContextClient(settings),
    )


def _excluded_repositories() -> list[str]:
    return [
        name.strip()
        for name in settings.excluded_repository_names.split(",")
        if name.strip()
    ]


# ─── Graph admin HTML UI ─────────────────────────────────────────────────────

GRAPH_ADMIN_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Graph DB Admin</title>
  <style>
    /* ── tab nav ── */
    .tab-nav {
      display: flex;
      gap: 0;
      border-bottom: 2px solid var(--line);
      margin-bottom: 18px;
    }
    .tab-btn {
      padding: 9px 20px;
      border: none;
      border-bottom: 2px solid transparent;
      background: transparent;
      color: var(--muted);
      font: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      width: auto;
      min-height: unset;
      border-radius: 0;
      margin-bottom: -2px;
    }
    .tab-btn.active {
      color: var(--accent);
      border-bottom-color: var(--accent);
    }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    /* ── badge ── */
    .badge {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
      background: var(--line);
      color: var(--muted);
      vertical-align: middle;
    }
    .badge.ok  { background: #dcfce7; color: var(--ok); }
    .badge.err { background: #fee2e2; color: var(--danger); }
    .badge.run { background: #dbeafe; color: var(--accent); }
  </style>
  <!-- original styles below -->
  <style>
    :root {
      color-scheme: light;
      --ink: #172033;
      --muted: #667085;
      --line: #d7dde8;
      --surface: #f7f9fc;
      --accent: #1d5fd1;
      --accent-strong: #0f3f91;
      --danger: #b42318;
      --ok: #067647;
      --warn: #b54708;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
    }
    header {
      border-bottom: 1px solid var(--line);
      padding: 18px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 { margin: 0; font-size: 20px; font-weight: 700; }
    main {
      display: grid;
      grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
      min-height: calc(100vh - 70px);
    }
    aside {
      border-right: 1px solid var(--line);
      background: var(--surface);
      padding: 22px;
    }
    section { padding: 22px; min-width: 0; }
    .toolbar { display: grid; gap: 10px; margin-top: 18px; }
    button {
      width: 100%;
      min-height: 44px;
      border: 1px solid var(--accent);
      border-radius: 6px;
      background: var(--accent);
      color: #ffffff;
      font: inherit;
      font-weight: 650;
      cursor: pointer;
    }
    button.secondary { background: #ffffff; color: var(--accent-strong); }
    button.danger { border-color: var(--danger); background: var(--danger); }
    button.warn { border-color: var(--warn); background: var(--warn); }
    button:disabled { cursor: wait; opacity: 0.7; }
    label {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 12px 0;
      color: var(--ink);
      font-size: 14px;
    }
    input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent); }
    .repo-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .repo-actions label { margin: 0; }
    .repo-actions button {
      width: auto;
      min-height: 36px;
      padding: 7px 14px;
      white-space: nowrap;
    }
    textarea {
      width: 100%;
      min-height: 72px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      font: inherit;
      margin-top: 14px;
    }
    .meta { color: var(--muted); font-size: 13px; line-height: 1.55; margin-top: 16px; }
    .status-bar { min-height: 34px; padding: 8px 0; color: var(--muted); font-size: 14px; }
    .status-bar.ok { color: var(--ok); }
    .status-bar.error { color: var(--danger); }
    .status-bar.running { color: var(--accent); }

    /* Stats row */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 12px;
      margin-bottom: 20px;
    }
    .stat-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
    }
    .stat-value { font-size: 22px; font-weight: 700; }
    .stat-label { font-size: 11px; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-top: 4px; }

    /* Progress bars */
    .progress-section { margin-bottom: 18px; }
    .progress-label { font-size: 13px; color: var(--muted); margin-bottom: 6px; }
    .progress-track { height: 8px; background: var(--line); border-radius: 4px; overflow: hidden; }
    .progress-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.4s; }

    /* Repo table */
    table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 14px; }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }
    th { color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 700; }
    pre {
      margin: 18px 0 0;
      padding: 14px;
      overflow: auto;
      background: #101828;
      color: #eef4ff;
      border-radius: 6px;
      max-height: 280px;
      font-size: 13px;
    }
    @media (max-width: 900px) {
      header { padding: 16px; flex-direction: column; align-items: flex-start; }
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      section, aside { padding: 16px; }
      .stats-grid { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <header>
    <h1>Graph DB Admin</h1>
    <div class="status-bar" id="status">Loading repositories...</div>
  </header>
  <main>
    <aside>
      <label><input id="pullLatestCode" type="checkbox" checked> Run git pull in local clones</label>
      <label><input id="fetchLatestJira" type="checkbox" checked> Fetch latest Jira tickets</label>
      <label><input id="includeJira" type="checkbox" checked> Include Jira tickets in graph</label>
      <label><input id="buildEmbeddings" type="checkbox" checked> Build semantic embeddings</label>
      <label style="display:block;">
        <span style="display:block;margin-bottom:6px;">Embedding model</span>
        <select id="embeddingModel" style="width:100%;border:1px solid var(--line);border-radius:6px;padding:9px 10px;font:inherit;background:#fff;">
          <option value="bge-m3">BGE-M3 (568M)</option>
          <option value="qwen3-embedding-0.6b">Qwen3-Embedding-0.6B</option>
          <option value="mxbai-embed-large-v1">mxbai-embed-large-v1 (335M)</option>
        </select>
      </label>
      <textarea id="notes" placeholder="Optional run note"></textarea>
      <div class="toolbar">
        <button data-action="update">Update Graph DB</button>
        <button class="secondary" data-action="regenerate">Regenerate Graph DB</button>
        <button class="warn" data-action="jira_tickets_only">Fetch Jira Tickets Only</button>
        <button class="danger" data-action="create_new">Create New Graph DB</button>
        <button class="secondary" data-action="jira_tickets_only">Refresh Jira Tickets Only</button>
      </div>
      <div class="meta" id="meta"></div>
    </aside>
    <section>
      <!-- Stats cards (shown during/after a job) -->
      <div class="stats-grid" id="statsGrid" hidden>
        <div class="stat-card">
          <div class="stat-value" id="statStatus">—</div>
          <div class="stat-label">Status</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="statRepos">—</div>
          <div class="stat-label">Repositories</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="statJira">—</div>
          <div class="stat-label">Jira Tickets</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="statEmbeddings">—</div>
          <div class="stat-label">Embeddings</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="statAction">—</div>
          <div class="stat-label">Action</div>
        </div>
      </div>

      <!-- Progress bars -->
      <div id="progressSection" hidden>
        <div class="progress-section">
          <div class="progress-label">Repository progress</div>
          <div class="progress-track"><div class="progress-fill" id="repoProgress" style="width:0%"></div></div>
        </div>
        <div class="progress-section">
          <div class="progress-label">Jira ticket progress</div>
          <div class="progress-track"><div class="progress-fill" id="jiraProgress" style="width:0%"></div></div>
        </div>
        <div class="progress-section" id="embeddingProgressSection" hidden>
          <div class="progress-label" id="embeddingProgressLabel">Semantic embedding progress</div>
          <div class="progress-track"><div class="progress-fill" id="embeddingProgress" style="width:0%"></div></div>
        </div>
      </div>

      <!-- Tab navigation -->
      <nav class="tab-nav">
        <button class="tab-btn active" data-tab="repos">Repositories</button>
        <button class="tab-btn" data-tab="jira">Jira Tickets</button>
        <button class="tab-btn" data-tab="logs">Logs</button>
      </nav>

      <!-- Tab: Repositories -->
      <div class="tab-panel active" id="tab-repos">
        <div class="repo-actions">
          <label><input id="selectAllRepos" type="checkbox" checked> Select all repositories</label>
          <button class="secondary" id="downloadAnalysisBtn">Download Code Analysis</button>
        </div>
        <table id="repoTable">
          <thead>
            <tr>
              <th style="width:6%">Use</th>
              <th style="width:20%">Repository</th>
              <th>Local clone path</th>
              <th style="width:16%">Branch</th>
              <th style="width:18%">Commit</th>
            </tr>
          </thead>
          <tbody id="repoRows"></tbody>
        </table>
        <pre id="result" hidden></pre>
      </div>

      <!-- Tab: Jira Tickets -->
      <div class="tab-panel" id="tab-jira">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
          <span id="jiraTicketCount" style="font-size:13px;color:var(--muted)">Loading…</span>
          <input id="jiraProjectFilter" type="text" placeholder="Filter by project key…"
            style="border:1px solid var(--line);border-radius:5px;padding:5px 10px;font:inherit;font-size:13px;width:180px;">
          <button class="secondary" id="jiraRefreshBtn"
            style="width:auto;min-height:unset;padding:6px 14px;font-size:13px;">Refresh</button>
        </div>
        <table>
          <thead>
            <tr>
              <th style="width:10%">Key</th>
              <th style="width:9%">Project</th>
              <th>Summary</th>
              <th style="width:10%">Status</th>
              <th style="width:10%">Type</th>
              <th style="width:9%">Priority</th>
              <th style="width:12%">Assignee</th>
              <th style="width:13%">Updated</th>
            </tr>
          </thead>
          <tbody id="jiraRows"></tbody>
        </table>
        <div id="jiraError" style="color:var(--danger);font-size:13px;margin-top:8px;"></div>
      </div>

      <!-- Tab: Logs -->
      <div class="tab-panel" id="tab-logs">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
          <span style="font-size:13px;color:var(--muted)">Recent graph jobs &amp; Jira fetch log</span>
          <button class="secondary" id="logsRefreshBtn"
            style="width:auto;min-height:unset;padding:6px 14px;font-size:13px;">Refresh</button>
        </div>

        <p style="font-size:13px;font-weight:700;color:var(--muted);margin:0 0 8px;">Graph Jobs</p>
        <table>
          <thead>
            <tr>
              <th style="width:10%">Job ID</th>
              <th style="width:14%">Action</th>
              <th style="width:10%">Status</th>
              <th style="width:8%">Repos</th>
              <th style="width:8%">Jira</th>
              <th style="width:10%">Embeddings</th>
              <th style="width:14%">Started</th>
              <th style="width:14%">Completed</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody id="jobRows"></tbody>
        </table>

        <p style="font-size:13px;font-weight:700;color:var(--muted);margin:18px 0 8px;">Jira Fetch Log</p>
        <table>
          <thead>
            <tr>
              <th style="width:12%">Project</th>
              <th style="width:10%">Tickets</th>
              <th style="width:9%">From Cache</th>
              <th style="width:10%">Duration ms</th>
              <th style="width:16%">Fetched At</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody id="fetchLogRows"></tbody>
        </table>
        <div id="logsError" style="color:var(--danger);font-size:13px;margin-top:8px;"></div>
      </div>
    </section>
  </main>
  <script>
    const statusEl  = document.querySelector("#status");
    const metaEl    = document.querySelector("#meta");
    const resultEl  = document.querySelector("#result");
    const repoRows  = document.querySelector("#repoRows");
    const statsGrid = document.querySelector("#statsGrid");
    const progressSection = document.querySelector("#progressSection");
    const buttons   = [...document.querySelectorAll("button[data-action]")];
    const downloadAnalysisBtn = document.querySelector("#downloadAnalysisBtn");
    const selectAllRepos = document.querySelector("#selectAllRepos");

    let pollTimer = null;
    let repositories = [];
    let selectedRepos = new Set();

    // ── Repo list ────────────────────────────────────────────────────────
    async function loadRepos() {
      try {
        const res  = await fetch("/graph-admin/repositories");
        const data = await res.json();
        repositories = data.repositories || [];
        selectedRepos = new Set(repositories.map(r => r.name));
        selectAllRepos.checked = true;
        repoRows.innerHTML = repositories.map(r => `
          <tr>
            <td><input class="repo-select" type="checkbox" data-repo="${escAttr(r.name)}" checked></td>
            <td>${esc(r.name)}</td>
            <td>${esc(r.path)}</td>
            <td>${esc(r.branch || "-")}</td>
            <td>${esc((r.current_commit || "-").slice(0, 12))}</td>
          </tr>
        `).join("");
        setStatus(`${data.repository_count} repositories ready`, "ok");
        metaEl.textContent =
          `Using existing local clones. Excluded: ${data.excluded_repositories.join(", ") || "none"}`;
        wireRepoSelection();
      } catch (err) {
        setStatus(`Repository load failed: ${err.message}`, "error");
      }
    }

    function wireRepoSelection() {
      [...document.querySelectorAll(".repo-select")].forEach(input => {
        input.addEventListener("change", () => {
          if (input.checked) selectedRepos.add(input.dataset.repo);
          else selectedRepos.delete(input.dataset.repo);
          selectAllRepos.checked = selectedRepos.size === repositories.length;
        });
      });
    }

    selectAllRepos.addEventListener("change", () => {
      selectedRepos = new Set(selectAllRepos.checked ? repositories.map(r => r.name) : []);
      [...document.querySelectorAll(".repo-select")].forEach(input => {
        input.checked = selectAllRepos.checked;
      });
    });

    async function downloadCodeAnalysis() {
      if (selectedRepos.size === 0) {
        setStatus("Select at least one repository for analysis", "error");
        return;
      }
      downloadAnalysisBtn.disabled = true;
      setStatus("Generating code analysis document...", "running");
      try {
        const res = await fetch("/graph-admin/code-analysis-report", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            repositories: [...selectedRepos],
            include_graph_context: true,
            embedding_model: document.querySelector("#embeddingModel").value,
          }),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || "Report generation failed");
        }
        const blob = await res.blob();
        const disposition = res.headers.get("Content-Disposition") || "";
        const match = disposition.match(/filename="([^"]+)"/);
        const filename = match ? match[1] : "code-analysis-report.md";
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        setStatus("Code analysis document downloaded", "ok");
      } catch (err) {
        setStatus(err.message, "error");
      } finally {
        downloadAnalysisBtn.disabled = false;
      }
    }

    // ── Trigger ──────────────────────────────────────────────────────────
    async function trigger(action) {
      setBusy(true);
      resultEl.hidden = true;
      statsGrid.hidden = true;
      progressSection.hidden = true;
      setStatus("Starting job...", "running");

      try {
        const res  = await fetch("/graph-admin/trigger", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            action,
            pull_latest_code:         document.querySelector("#pullLatestCode").checked,
            fetch_latest_jira_tickets: document.querySelector("#fetchLatestJira").checked,
            include_jira_tickets:      document.querySelector("#includeJira").checked,
            build_embeddings:          document.querySelector("#buildEmbeddings").checked,
            embedding_model:           document.querySelector("#embeddingModel").value,
            notes: document.querySelector("#notes").value || null,
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Trigger failed");

        setStatus(`Job started (${data.job_id.slice(0, 8)}...)`, "running");
        statsGrid.hidden = false;
        progressSection.hidden = false;
        updateStats(data);
        startPolling(data.job_id);

      } catch (err) {
        setStatus(err.message, "error");
        setBusy(false);
      }
    }

    // ── Polling ──────────────────────────────────────────────────────────
    function startPolling(jobId) {
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(() => pollJob(jobId), 2000);
    }

    async function pollJob(jobId) {
      try {
        const res  = await fetch(`/graph-admin/jobs/${jobId}`);
        const data = await res.json();
        updateStats(data);
        if (data.status === "running") {
          setStatus(runningStatusMessage(data), "running");
        }

        resultEl.textContent = JSON.stringify(data, null, 2);
        resultEl.hidden = false;

        if (data.status === "completed" || data.status === "failed") {
          clearInterval(pollTimer);
          pollTimer = null;
          setBusy(false);
          setStatus(
            data.status === "completed" ? "Job completed successfully" : `Job failed: ${data.error || "unknown"}`,
            data.status === "completed" ? "ok" : "error",
          );
        }
      } catch (err) {
        /* ignore transient poll errors */
      }
    }

    // ── Stats / progress ─────────────────────────────────────────────────
    function updateStats(data) {
      const totals   = data.totals   || {};
      const progress = data.progress || {};

      document.querySelector("#statStatus").textContent = data.status || "—";
      document.querySelector("#statAction").textContent = data.action || "—";

      const repoT = totals.repositories   || 0;
      const repoD = progress.repositories_done || 0;
      const jiraT = totals.jira_tickets   || 0;
      const jiraD = progress.jira_tickets_done || 0;
      const embT  = totals.embedding_documents || 0;
      const embD  = progress.embedding_documents_done || 0;
      const embActive = embT > 0 || embD > 0;
      const inferEmbeddingActive =
        !embActive &&
        data.status === "running" &&
        document.querySelector("#buildEmbeddings").checked &&
        repoT > 0 &&
        repoD >= repoT &&
        (jiraT === 0 || jiraD >= jiraT);

      document.querySelector("#statRepos").textContent =
        repoT > 0 ? `${repoD}/${repoT}` : (data.repository_count != null ? `${data.repository_count}` : "0/0");
      document.querySelector("#statJira").textContent  =
        jiraT > 0 ? `${jiraD}/${jiraT}` : "0/0";
      document.querySelector("#statEmbeddings").textContent =
        embActive ? `${embD}/${embT}` : (inferEmbeddingActive ? "running" : "—");

      setProgressBar("repoProgress", repoD, repoT);
      setProgressBar("jiraProgress", jiraD, jiraT);
      document.querySelector("#embeddingProgressSection").hidden = !(embActive || inferEmbeddingActive);
      document.querySelector("#embeddingProgressLabel").textContent =
        (embActive && data.status === "running" && embD === 0) || inferEmbeddingActive
          ? "Semantic embedding progress (model running)"
          : "Semantic embedding progress";
      if (inferEmbeddingActive) {
        document.querySelector("#embeddingProgress").style.width = "15%";
      } else {
        setProgressBar("embeddingProgress", embD, embT);
      }
    }

    function setProgressBar(id, done, total) {
      const pct = total > 0 ? Math.round((done / total) * 100) : 0;
      document.querySelector(`#${id}`).style.width = `${pct}%`;
    }

    function runningStatusMessage(data) {
      const totals = data.totals || {};
      const progress = data.progress || {};
      const repoDone = (totals.repositories || 0) > 0 && progress.repositories_done >= totals.repositories;
      const jiraDone = (totals.jira_tickets || 0) > 0 && progress.jira_tickets_done >= totals.jira_tickets;
      const embTotal = totals.embedding_documents || 0;
      const embDone = progress.embedding_documents_done || 0;
      if (embTotal > 0 && embDone < embTotal) return "Building semantic embeddings...";
      if (
        document.querySelector("#buildEmbeddings").checked &&
        repoDone &&
        (jiraDone || (totals.jira_tickets || 0) === 0)
      ) return "Building semantic embeddings...";
      if (repoDone && jiraDone) return "Finalizing graph job...";
      return "Graph job running...";
    }

    // ── Helpers ──────────────────────────────────────────────────────────
    function setStatus(msg, cls = "") {
      statusEl.textContent  = msg;
      statusEl.className    = `status-bar ${cls}`;
    }

    function setBusy(busy) {
      buttons.forEach(b => b.disabled = busy);
    }

    function esc(v) {
      return String(v).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"})[c]);
    }

    function escAttr(v) {
      return esc(v).replace(/`/g, "&#096;");
    }

    // ── Tab switching ────────────────────────────────────────────────────
    const tabBtns   = [...document.querySelectorAll(".tab-btn")];
    const tabPanels = [...document.querySelectorAll(".tab-panel")];

    function switchTab(name) {
      tabBtns.forEach(b => b.classList.toggle("active", b.dataset.tab === name));
      tabPanels.forEach(p => p.classList.toggle("active", p.id === `tab-${name}`));
      if (name === "jira")  loadJiraTickets();
      if (name === "logs")  loadLogs();
    }

    tabBtns.forEach(b => b.addEventListener("click", () => switchTab(b.dataset.tab)));

    // ── Jira tickets tab ─────────────────────────────────────────────────
    let jiraProjectFilter = "";

    async function loadJiraTickets() {
      const countEl = document.querySelector("#jiraTicketCount");
      const rowsEl  = document.querySelector("#jiraRows");
      const errEl   = document.querySelector("#jiraError");
      countEl.textContent = "Loading…";
      errEl.textContent   = "";
      const project = document.querySelector("#jiraProjectFilter").value.trim().toUpperCase();
      const qs = project ? `?project_key=${encodeURIComponent(project)}&limit=200` : "?limit=200";
      try {
        const res  = await fetch(`/graph-admin/jira-tickets${qs}`);
        const data = await res.json();
        if (data.error) {
          errEl.textContent = data.error;
          countEl.textContent = "—";
          rowsEl.innerHTML = "";
          return;
        }
        countEl.textContent = `${data.count} ticket${data.count !== 1 ? "s" : ""} in cache`;
        rowsEl.innerHTML = (data.tickets || []).map(t => `
          <tr>
            <td><b>${esc(t.ticket_key)}</b></td>
            <td>${esc(t.project_key)}</td>
            <td>${esc(t.summary || "")}</td>
            <td><span class="badge">${esc(t.status || "—")}</span></td>
            <td>${esc(t.issue_type || "—")}</td>
            <td>${esc(t.priority || "—")}</td>
            <td>${esc(t.assignee_name || "—")}</td>
            <td>${esc(fmtDate(t.updated_at))}</td>
          </tr>
        `).join("");
      } catch (err) {
        errEl.textContent = err.message;
        countEl.textContent = "—";
      }
    }

    document.querySelector("#jiraRefreshBtn").addEventListener("click", loadJiraTickets);
    document.querySelector("#jiraProjectFilter").addEventListener("keydown", e => {
      if (e.key === "Enter") loadJiraTickets();
    });

    // ── Logs tab ─────────────────────────────────────────────────────────
    async function loadLogs() {
      const jobRowsEl   = document.querySelector("#jobRows");
      const fetchRowsEl = document.querySelector("#fetchLogRows");
      const errEl       = document.querySelector("#logsError");
      errEl.textContent = "";

      try {
        const [jobsRes, fetchRes] = await Promise.all([
          fetch("/graph-admin/jobs?limit=50"),
          fetch("/graph-admin/fetch-logs?limit=100"),
        ]);
        const jobs      = await jobsRes.json();
        const fetchData = await fetchRes.json();

        jobRowsEl.innerHTML = (Array.isArray(jobs) ? jobs : []).map(j => `
          <tr>
            <td style="font-family:monospace;font-size:12px">${esc((j.job_id||"").slice(0,8))}</td>
            <td>${esc(j.action || "—")}</td>
            <td><span class="badge ${j.status==="completed"?"ok":j.status==="failed"?"err":"run"}">${esc(j.status||"—")}</span></td>
            <td>${esc(String((j.progress||{}).repositories_done||0))}/${esc(String((j.totals||{}).repositories||0))}</td>
            <td>${esc(String((j.progress||{}).jira_tickets_done||0))}/${esc(String((j.totals||{}).jira_tickets||0))}</td>
            <td>${esc(String((j.progress||{}).embedding_documents_done||0))}/${esc(String((j.totals||{}).embedding_documents||0))}</td>
            <td>${esc(fmtDate(j.started_at))}</td>
            <td>${esc(fmtDate(j.completed_at))}</td>
            <td style="color:var(--danger);font-size:12px">${esc(j.error||"")}</td>
          </tr>
        `).join("") || '<tr><td colspan="9" style="color:var(--muted)">No jobs yet</td></tr>';

        if (fetchData.error) {
          errEl.textContent = fetchData.error;
        }
        fetchRowsEl.innerHTML = (fetchData.logs || []).map(l => `
          <tr>
            <td>${esc(l.project_key)}</td>
            <td>${esc(String(l.ticket_count))}</td>
            <td>${l.from_cache ? "✓" : ""}</td>
            <td>${esc(String(l.duration_ms))}</td>
            <td>${esc(fmtDate(l.fetched_at))}</td>
            <td style="color:var(--danger);font-size:12px">${esc(l.error||"")}</td>
          </tr>
        `).join("") || '<tr><td colspan="6" style="color:var(--muted)">No fetch log entries yet</td></tr>';

      } catch (err) {
        errEl.textContent = err.message;
      }
    }

    document.querySelector("#logsRefreshBtn").addEventListener("click", loadLogs);

    // ── Helpers ──────────────────────────────────────────────────────────
    function fmtDate(val) {
      if (!val) return "—";
      try { return new Date(val).toLocaleString(); } catch { return val; }
    }

    // ── Init ─────────────────────────────────────────────────────────────
    buttons.forEach(b => b.addEventListener("click", () => trigger(b.dataset.action)));
    downloadAnalysisBtn.addEventListener("click", downloadCodeAnalysis);
    loadRepos();
  </script>
</body>
</html>
"""

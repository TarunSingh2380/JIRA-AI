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
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from fastapi.responses import HTMLResponse

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
graph_job_runner = GraphJobRunner(settings)

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


# ─── Ticket analysis ─────────────────────────────────────────────────────────

@app.post("/graph-admin/jobs")
def graph_admin_start_job(request: GraphAdminTriggerRequest) -> dict[str, Any]:
    return graph_job_runner.start(request)


@app.get("/graph-admin/jobs")
def graph_admin_jobs() -> dict[str, Any]:
    return {"jobs": graph_job_runner.list()}


@app.get("/graph-admin/jobs/{job_id}")
def graph_admin_job(job_id: str) -> dict[str, Any]:
    try:
        return graph_job_runner.get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Graph job not found") from exc


@app.websocket("/graph-admin/jobs/{job_id}/ws")
async def graph_admin_job_ws(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    last_updated_at = None

    try:
        while True:
            payload = graph_job_runner.get(job_id)
            updated_at = payload["job"].get("updated_at")
            if updated_at != last_updated_at:
                await websocket.send_json(payload)
                last_updated_at = updated_at

            if payload["job"].get("status") in {"completed", "failed"}:
                await websocket.close(code=1000)
                return
            else:
                await asyncio.sleep(0.5)
    except KeyError:
        await websocket.close(code=1008, reason="Graph job not found")
    except WebSocketDisconnect:
        return
    except RuntimeError:
        return


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
      grid-template-columns: repeat(4, 1fr);
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
      <label><input id="buildEmbeddings" type="checkbox" checked> Build BGE-M3 embeddings</label>
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
      <!-- Stats cards -->
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
      </div>

      <!-- Repo table -->
      <table id="repoTable">
        <thead>
          <tr>
            <th style="width:20%">Repository</th>
            <th>Local clone path</th>
            <th style="width:16%">Branch</th>
            <th style="width:18%">Commit</th>
          </tr>
        </thead>
        <tbody id="repoRows"></tbody>
      </table>

      <!-- Raw JSON result -->
      <pre id="result" hidden></pre>
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

    let pollTimer = null;

    // ── Repo list ────────────────────────────────────────────────────────
    async function loadRepos() {
      try {
        const res  = await fetch("/graph-admin/repositories");
        const data = await res.json();
        repoRows.innerHTML = data.repositories.map(r => `
          <tr>
            <td>${esc(r.name)}</td>
            <td>${esc(r.path)}</td>
            <td>${esc(r.branch || "-")}</td>
            <td>${esc((r.current_commit || "-").slice(0, 12))}</td>
          </tr>
        `).join("");
        setStatus(`${data.repository_count} repositories ready`, "ok");
        metaEl.textContent =
          `Using existing local clones. Excluded: ${data.excluded_repositories.join(", ") || "none"}`;
      } catch (err) {
        setStatus(`Repository load failed: ${err.message}`, "error");
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

      document.querySelector("#statRepos").textContent =
        repoT > 0 ? `${repoD}/${repoT}` : (data.repository_count != null ? `${data.repository_count}` : "0/0");
      document.querySelector("#statJira").textContent  =
        jiraT > 0 ? `${jiraD}/${jiraT}` : "0/0";

      setProgressBar("repoProgress", repoD, repoT);
      setProgressBar("jiraProgress", jiraD, jiraT);
    }

    function setProgressBar(id, done, total) {
      const pct = total > 0 ? Math.round((done / total) * 100) : 0;
      document.querySelector(`#${id}`).style.width = `${pct}%`;
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

    // ── Init ─────────────────────────────────────────────────────────────
    buttons.forEach(b => b.addEventListener("click", () => trigger(b.dataset.action)));
    loadRepos();
  </script>
</body>
</html>
"""

"""FastAPI entry point for serving Jira ticket analysis over HTTP.

This file exposes health, prompt-listing, and ticket-analysis endpoints.
It wires together the prompt store, LLM client, request/response schemas,
and the ticket analyzer service for external consumers.
"""

import asyncio
import json

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.config import settings
from app.conversation_store import ConversationStoreError, PostgresConversationStore
from app.exceptions import LLMConfigurationError, PromptNotFoundError
from app.graph_context import GraphContextClient
from app.graph_job_runner import GraphJobRunner
from app.jira_client import JiraClient
from app.json_utils import parse_model_json, review_status, review_text
from app.llm_client import build_llm_client
from app.n8n_client import N8NGraphClient
from app.prompt_store import PromptStore
from app.repository_discovery import discover_graph_repositories
from app.schemas import (
    AnalyzeTicketRequest,
    AnalyzeTicketResponse,
    GraphAdminTriggerRequest,
    GraphAdminTriggerResponse,
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


app = FastAPI(
    title="Jira AI Ticket Analyzer",
    version="0.1.0",
    description="Injects Jira ticket metadata into prompt templates and returns LLM analysis.",
)

prompt_store = PromptStore(settings.prompt_dir)
graph_job_runner = GraphJobRunner(settings)

SLACK_CHAT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Send the reply of the user message and only "
    "in a single line of 11-21 words."
)


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


@app.get("/", response_class=HTMLResponse)
def graph_admin_ui() -> str:
    return GRAPH_ADMIN_HTML


@app.get("/graph-admin", response_class=HTMLResponse)
def graph_admin_ui_alias() -> str:
    return GRAPH_ADMIN_HTML


@app.get("/graph-admin/repositories")
def graph_admin_repositories() -> dict[str, Any]:
    repositories = discover_graph_repositories(settings)
    return {
        "repository_count": len(repositories),
        "repositories": repositories,
        "excluded_repositories": _excluded_repositories(),
    }


@app.post("/graph-admin/trigger", response_model=GraphAdminTriggerResponse)
def graph_admin_trigger(request: GraphAdminTriggerRequest) -> GraphAdminTriggerResponse:
    repositories = discover_graph_repositories(settings)
    payload = {
        "source": "jira-ai-admin-ui",
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "action": request.action,
        "graph_db": {
            "operation": request.action,
            "scope": "all_repositories_and_jira_tickets",
        },
        "github": {
            "clone_strategy": "use_existing_local_clones",
            "local_clone_root": settings.repository_host_root,
            "container_scan_root": settings.repository_search_root,
            "pull_latest_code": request.pull_latest_code,
            "pull_mode": "git_pull_ff_only_per_repo",
            "repositories": repositories,
            "excluded_repository_names": _excluded_repositories(),
        },
        "jira": {
            "fetch_latest_tickets": request.fetch_latest_jira_tickets,
            "include_tickets_in_graph": request.include_jira_tickets,
            "base_url_configured": bool(settings.jira_base_url),
        },
        "notes": request.notes,
    }

    try:
        n8n_result = N8NGraphClient(settings).trigger_graph_job(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"n8n trigger failed: {exc}") from exc

    return GraphAdminTriggerResponse(
        action=request.action,
        repository_count=len(repositories),
        excluded_repositories=_excluded_repositories(),
        n8n=n8n_result,
    )


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


@app.post("/chat", response_model=SlackMessageResponse)
def reply_to_message(request: SlackMessageRequest) -> SlackMessageResponse:
    try:
        llm_client = build_llm_client(settings)
        llm_reply = llm_client.complete(SLACK_CHAT_SYSTEM_PROMPT, request.user_message).strip()
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SlackMessageResponse(userid=request.userid, llm_reply=llm_reply)


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
    h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.2;
      font-weight: 700;
      letter-spacing: 0;
    }
    main {
      display: grid;
      grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
      min-height: calc(100vh - 70px);
    }
    aside {
      border-right: 1px solid var(--line);
      background: var(--surface);
      padding: 22px;
    }
    section {
      padding: 22px;
      min-width: 0;
    }
    .toolbar {
      display: grid;
      gap: 10px;
      margin-top: 18px;
    }
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
    button.secondary {
      background: #ffffff;
      color: var(--accent-strong);
    }
    button.danger {
      border-color: var(--danger);
      background: var(--danger);
    }
    button:disabled {
      cursor: wait;
      opacity: 0.7;
    }
    label {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 12px 0;
      color: var(--ink);
      font-size: 14px;
    }
    input[type="checkbox"] {
      width: 18px;
      height: 18px;
      accent-color: var(--accent);
    }
    textarea {
      width: 100%;
      min-height: 92px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      font: inherit;
      margin-top: 14px;
    }
    .meta {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
      margin-top: 16px;
    }
    .status {
      min-height: 34px;
      padding: 8px 0;
      color: var(--muted);
      font-size: 14px;
    }
    .status.ok { color: var(--ok); }
    .status.error { color: var(--danger); }
    table {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: 14px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }
    th {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      font-weight: 700;
    }
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
    @media (max-width: 820px) {
      header { padding: 16px; align-items: flex-start; flex-direction: column; }
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      section, aside { padding: 16px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Graph DB Admin</h1>
    <div class="status" id="status">Loading repositories...</div>
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
        <button class="danger" data-action="create_new">Create New Graph DB</button>
        <button class="secondary" data-action="jira_tickets_only">Refresh Jira Tickets Only</button>
      </div>
      <div class="meta" id="meta"></div>
    </aside>
    <section>
      <table>
        <thead>
          <tr>
            <th style="width: 20%">Repository</th>
            <th>Local clone path</th>
            <th style="width: 16%">Branch</th>
            <th style="width: 18%">Commit</th>
          </tr>
        </thead>
        <tbody id="repoRows"></tbody>
      </table>
      <pre id="result" hidden></pre>
    </section>
  </main>
  <script>
    const statusEl = document.querySelector("#status");
    const metaEl = document.querySelector("#meta");
    const resultEl = document.querySelector("#result");
    const repoRows = document.querySelector("#repoRows");
    const buttons = [...document.querySelectorAll("button[data-action]")];
    let currentSocket = null;

    async function loadRepos() {
      try {
        const response = await fetch("/graph-admin/repositories");
        const data = await response.json();
        repoRows.innerHTML = data.repositories.map(repo => `
          <tr>
            <td>${escapeHtml(repo.name)}</td>
            <td>${escapeHtml(repo.path)}</td>
            <td>${escapeHtml(repo.branch || "-")}</td>
            <td>${escapeHtml((repo.current_commit || "-").slice(0, 12))}</td>
          </tr>
        `).join("");
        statusEl.textContent = `${data.repository_count} repositories ready`;
        statusEl.className = "status ok";
        metaEl.textContent = `Using existing local clones. Excluded: ${data.excluded_repositories.join(", ") || "none"}`;
      } catch (error) {
        statusEl.textContent = `Repository load failed: ${error.message}`;
        statusEl.className = "status error";
      }
    }

    async function trigger(action) {
      setBusy(true);
      resultEl.hidden = true;
      statusEl.textContent = "Starting graph job...";
      statusEl.className = "status";
      try {
        const response = await fetch("/graph-admin/jobs", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            action,
            pull_latest_code: document.querySelector("#pullLatestCode").checked,
            fetch_latest_jira_tickets: document.querySelector("#fetchLatestJira").checked,
            include_jira_tickets: document.querySelector("#includeJira").checked,
            build_embeddings: document.querySelector("#buildEmbeddings").checked,
            notes: document.querySelector("#notes").value || null
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Job start failed");
        const job = normalizeJobPayload(data);
        if (!job) throw new Error("Job start response did not include a job");
        renderJob(job);
        if (job.id) watchJob(job.id);
      } catch (error) {
        statusEl.textContent = error.message;
        statusEl.className = "status error";
        setBusy(false);
      }
    }

    async function loadLatestJob() {
      try {
        const response = await fetch("/graph-admin/jobs");
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Job load failed");
        const latest = (data.jobs || [])[0];
        if (!latest) return;
        renderJob(latest);
        if (latest.id && (latest.status === "queued" || latest.status === "running")) {
          setBusy(true);
          watchJob(latest.id);
        }
      } catch (error) {
        console.warn("Latest graph job load failed", error);
      }
    }

    function watchJob(jobId) {
      if (currentSocket) {
        currentSocket.close();
      }
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(`${protocol}://${window.location.host}/graph-admin/jobs/${jobId}/ws`);
      currentSocket = socket;
      socket.onmessage = event => {
        const job = normalizeJobPayload(JSON.parse(event.data));
        if (job) renderJob(job);
      };
      socket.onerror = () => {
        statusEl.textContent = "Job progress connection failed";
        statusEl.className = "status error";
        setBusy(false);
      };
      socket.onclose = () => {
        if (currentSocket === socket) currentSocket = null;
        setBusy(false);
      };
    }

    function normalizeJobPayload(payload) {
      if (!payload) return null;
      if (payload.job) return payload.job;
      return payload.id || payload.status || payload.progress || payload.totals ? payload : null;
    }

    function renderJob(job) {
      const progress = job.progress || {};
      const totals = job.totals || {};
      const status = job.status || "unknown";
      const repoDone = progress.repositories_done || 0;
      const repoTotal = totals.repositories || 0;
      const jiraDone = progress.jira_tickets_done || 0;
      const jiraTotal = totals.jira_tickets || 0;
      const summary = `${status}: repos ${repoDone}/${repoTotal}, Jira ${jiraDone}/${jiraTotal}`;
      statusEl.textContent = status === "failed" && job.error ? `${summary} - ${job.error}` : summary;
      statusEl.className = status === "failed" ? "status error" : "status ok";

      const recentLogs = (job.logs || []).slice(-80).map(log => (
        `[${log.ts || ""}] ${(log.level || "info").toUpperCase()} ${log.message || ""}`
      ));
      resultEl.textContent = JSON.stringify({
        id: job.id,
        action: job.action,
        status,
        error: job.error,
        totals,
        progress,
        repositories: job.repositories || [],
        recent_logs: recentLogs
      }, null, 2);
      resultEl.hidden = false;
      if (status === "completed" || status === "failed") {
        setBusy(false);
      }
    }

    function setBusy(isBusy) {
      buttons.forEach(button => button.disabled = isBusy);
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
      })[char]);
    }

    buttons.forEach(button => button.addEventListener("click", () => trigger(button.dataset.action)));
    async function init() {
      await loadRepos();
      await loadLatestJob();
    }

    init();
  </script>
</body>
</html>
"""

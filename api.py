"""FastAPI entry point for Jira ticket analysis and graph DB administration.

Graph admin flow (replaces n8n):
  POST /graph-admin/trigger  → starts background job, returns job_id
  GET  /graph-admin/jobs     → list recent jobs
  GET  /graph-admin/jobs/{job_id} → poll job status + progress
"""

import asyncio
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s: %(message)s",
    force=True,
)

from pathlib import Path
from typing import Any
from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from app.code_analysis_report import build_code_analysis_report
from app.config import settings
from app.conversation_store import ConversationStoreError, PostgresConversationStore
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
    SimilarTicketRequest,
    SimilarTicketResult,
    SimilarTicketsResponse,
    TestCaseRequest,
    TestCaseResponse,
    Workflow1ReviewRequest,
    Workflow1ReviewResponse,
    Workflow2ReplyRequest,
    Workflow2ReplyResponse,
    Workflow2Request,
    Workflow2Response,
    Workflow3SLAResponse,
    Workflow4DueDateResponse,
)
from app.similar_ticket_finder import SimilarTicketFinder
from app.slack_client import SlackClient
from app.slack_review_workflow import SlackReviewWorkflow
from app.testcase_chat_workflow import TestCaseChatWorkflow
from app.test_case_generator import TestCaseGenerator
from app.ticket_analyzer import TicketAnalyzer
from app.workflow1_reviewer import Workflow1Reviewer
from app.workflow2_replier import Workflow2Replier
from app.workflow3_sla import Workflow3SLAChecker
from app.workflow4_due_date import Workflow4DueDateChecker

log = logging.getLogger(__name__)


app = FastAPI(
    title="Jira AI Ticket Analyzer",
    version="0.2.0",
    description="Jira ticket analysis, Slack review workflow, and graph DB administration.",
    docs_url=None,
)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent / "app" / "static"),
    name="static",
)


@app.get("/docs", include_in_schema=False)
def swagger_ui_html() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
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


# ─── Jira AI workflow endpoints ──────────────────────────────────────────────

@app.post("/workflow1", response_model=Workflow1ReviewResponse)
def workflow1_review(request: Workflow1ReviewRequest) -> Workflow1ReviewResponse:
    log.info("POST /workflow1 issue=%s", request.issueKey)
    try:
        reviewer = Workflow1Reviewer(settings=settings, prompt_store=prompt_store)
        return Workflow1ReviewResponse(**reviewer.review(request))
    except ValueError as exc:
        log.exception("/workflow1 validation failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (PromptNotFoundError, RuntimeError) as exc:
        log.exception("/workflow1 runtime failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow1 failed")
        raise HTTPException(status_code=500, detail=f"workflow1 failed: {exc}") from exc


@app.post("/workflow2/reply", response_model=Workflow2ReplyResponse)
def workflow2_reply(request: Workflow2ReplyRequest) -> Workflow2ReplyResponse:
    log.info(
        "POST /workflow2/reply user=%s channel=%s thread=%s",
        request.user_id,
        request.slack_channel_id,
        request.slack_thread_ts,
    )
    try:
        replier = Workflow2Replier(settings=settings, prompt_store=prompt_store)
        return Workflow2ReplyResponse(**replier.reply(request))
    except ValueError as exc:
        log.exception("/workflow2/reply validation failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        log.exception("/workflow2/reply ticket lookup failed")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow2/reply failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/workflow3", response_model=Workflow3SLAResponse)
def workflow3_sla_check() -> Workflow3SLAResponse:
    log.info("POST /workflow3")
    try:
        checker = Workflow3SLAChecker(settings=settings)
        return Workflow3SLAResponse(**checker.check())
    except RuntimeError as exc:
        log.exception("/workflow3 runtime failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow3 failed")
        raise HTTPException(status_code=500, detail=f"workflow3 failed: {exc}") from exc


@app.post("/workflow4", response_model=Workflow4DueDateResponse)
def workflow4_due_date_check() -> Workflow4DueDateResponse:
    log.info("POST /workflow4")
    try:
        checker = Workflow4DueDateChecker(settings=settings)
        return Workflow4DueDateResponse(**checker.check())
    except RuntimeError as exc:
        log.exception("/workflow4 runtime failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow4 failed")
        raise HTTPException(status_code=500, detail=f"workflow4 failed: {exc}") from exc


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
    log.info("GET /graph-admin/repositories")
    repositories = discover_graph_repositories(settings)
    log.info("Returning %d repositories", len(repositories))
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
    log.info(
        "POST /graph-admin/trigger action=%s pull_code=%s fetch_jira=%s include_jira=%s selected_repos=%d",
        request.action,
        request.pull_latest_code,
        request.fetch_latest_jira_tickets,
        request.include_jira_tickets,
        len(request.repositories),
    )
    repositories = discover_graph_repositories(settings)
    selected_repositories = _selected_repositories(repositories, request.repositories)
    if request.action != "jira_tickets_only" and not selected_repositories:
        raise HTTPException(status_code=400, detail="Select at least one repository")

    job = job_store.create(action=request.action)
    log.info("Enqueuing background job %s for action=%s", job.job_id, request.action)

    background_tasks.add_task(
        run_graph_job,
        job,
        pull_latest_code=request.pull_latest_code,
        fetch_latest_jira=request.fetch_latest_jira_tickets,
        include_jira_in_graph=request.include_jira_tickets,
        build_embeddings=request.build_embeddings,
        embedding_model=request.embedding_model,
        selected_repositories=[repo.get("name", "") for repo in selected_repositories],
    )

    return GraphAdminTriggerResponse(
        job_id=job.job_id,
        action=job.action,
        status=job.status,
        repository_count=len(selected_repositories) if request.action != "jira_tickets_only" else 0,
        excluded_repositories=_excluded_repositories(),
    )


@app.get("/graph-admin/jobs", response_model=list[GraphJobResponse])
def list_graph_jobs(limit: int = 10) -> list[GraphJobResponse]:
    log.debug("GET /graph-admin/jobs limit=%d", limit)
    jobs = job_store.list_recent(limit=min(limit, 50))
    return [GraphJobResponse(**j.to_dict()) for j in jobs]


@app.get("/graph-admin/jobs/{job_id}", response_model=GraphJobResponse)
def get_graph_job(job_id: str) -> GraphJobResponse:
    log.debug("GET /graph-admin/jobs/%s", job_id)
    job = job_store.get(job_id)
    if job is None:
        log.warning("Job %s not found", job_id)
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
    log.debug("GET /graph-admin/jira-tickets project=%s limit=%d offset=%d", project_key, limit, offset)
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
                       updated_at, fetched_at
                FROM jira_ticket_cache
                {where}
                ORDER BY updated_at DESC NULLS LAST
                LIMIT %s OFFSET %s
                """,
                list_params,
            ).fetchall()
            log.info("Returning %d of %d jira tickets (project=%s)", len(tickets), count, project_key)
            return {"count": count, "tickets": [dict(t) for t in tickets]}
    except Exception as exc:
        log.error("Failed to query jira_ticket_cache: %s", exc)
        return {"count": 0, "tickets": [], "error": str(exc)}


@app.get("/graph-admin/fetch-logs")
def graph_admin_fetch_logs(limit: int = 100) -> dict[str, Any]:
    log.debug("GET /graph-admin/fetch-logs limit=%d", limit)
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
            log.debug("Returning %d fetch log entries", len(logs))
            return {"logs": [dict(l) for l in logs]}
    except Exception as exc:
        log.error("Failed to query jira_fetch_log: %s", exc)
        return {"logs": [], "error": str(exc)}


# ─── Ticket analysis ─────────────────────────────────────────────────────────

@app.post("/analyze-ticket", response_model=AnalyzeTicketResponse)
def analyze_ticket(request: AnalyzeTicketRequest) -> AnalyzeTicketResponse:
    ticket_key = request.ticket_data.get("key") or request.ticket_data.get("issue_key") or "unknown"
    log.info("POST /analyze-ticket key=%s", ticket_key)
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
            log.error("LLM returned non-JSON for ticket %s", ticket_key)
            raise HTTPException(
                status_code=502,
                detail="LLM returned non-JSON output. Use a prompt that returns only JSON.",
            ) from exc

        status = review_status(model_json)
        log.info("Ticket %s analysis complete: status=%s", ticket_key, status)
        return AnalyzeTicketResponse(status=status, review=review_text(model_json))

    except PromptNotFoundError as exc:
        log.error("Prompt not found: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except LLMConfigurationError as exc:
        log.error("LLM configuration error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─── Test case generator ─────────────────────────────────────────────────────

@app.post("/analyze-ticket/test-cases", response_model=TestCaseResponse)
def generate_test_cases(request: TestCaseRequest) -> TestCaseResponse:
    """
    Generate test cases for a JIRA ticket using:
      1. RepoTree's Repomix-derived repository context
      2. Qdrant semantic code hits fetched by RepoTree
      3. Claude LLM in RepoTree to synthesise a Markdown test-case document

    Prerequisites: run the Graph Admin trigger first to build Qdrant embeddings,
    and run RepoTree's scan so its Repomix maps are available.
    """
    ticket_key = (
        request.ticket_data.get("issueKey")
        or request.ticket_data.get("key")
        or request.ticket_data.get("issue_key")
        or "unknown"
    )
    log.info(
        "POST /analyze-ticket/test-cases key=%s repo=%s model=%s style=%s",
        ticket_key, request.repo, request.embedding_model, request.style,
    )
    try:
        generator = TestCaseGenerator(settings=settings)
        result = generator.generate(
            request.ticket_data,
            repo=request.repo,
            embedding_model=request.embedding_model,
            top_k=request.top_k,
            style=request.style,
        )
    except LLMConfigurationError as exc:
        log.error("LLM configuration error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Test case generation failed for ticket %s", ticket_key)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    log.info(
        "Test cases generated for %s: semantic=%d repos=%d files=%d",
        ticket_key, result["semantic_hits_count"],
        result["functions_found"], result["files_touched_count"],
    )
    return TestCaseResponse(
        ticket_key=ticket_key,
        test_cases=result["test_cases"],
        semantic_hits_count=result["semantic_hits_count"],
        functions_found=result["functions_found"],
        files_touched_count=result["files_touched_count"],
        grounded_repos=result.get("grounded_repos") or [],
        style=result.get("style") or request.style,
        architecture_context_chars=result.get("architecture_context_chars") or 0,
        repomix_context_chars=result.get("repomix_context_chars") or 0,
    )


# ─── Similar ticket finder ────────────────────────────────────────────────────

@app.post("/analyze-ticket/similar", response_model=SimilarTicketsResponse)
def find_similar_tickets(request: SimilarTicketRequest) -> SimilarTicketsResponse:
    """
    Find historically similar Jira tickets for a new incoming ticket.

    Search strategy (in order):
      1. Semantic – embed (summary + description) with Ollama, search Qdrant
         `jira_tickets` collection and enrich hits from PostgreSQL.
      2. Keyword fallback – ILIKE search in PostgreSQL `jira_ticket_cache` when
         Ollama / Qdrant is unavailable.

    All ticket statuses are considered. The response returns only the single best
    ticket when its similarity score is greater than 55%; otherwise it returns empty.
    """
    log.info(
        "POST /analyze-ticket/similar summary=%r project=%s",
        request.summary[:60], request.project_key,
    )
    try:
        finder = SimilarTicketFinder(settings=settings)
        result = finder.find_similar(
            request.summary,
            request.description,
            project_key=request.project_key,
        )
    except Exception as exc:
        log.exception("Similar ticket search failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    tickets = [
        SimilarTicketResult(
            ticket_key=t.get("ticket_key", ""),
            project_key=t.get("project_key", ""),
            summary=t.get("summary", ""),
            description=t.get("description"),
            status=t.get("status", ""),
            issue_type=t.get("issue_type"),
            priority=t.get("priority"),
            assignee_name=t.get("assignee_name"),
            reporter_name=t.get("reporter_name"),
            labels=t.get("labels") or [],
            created_at=t.get("created_at"),
            updated_at=t.get("updated_at"),
            similarity_score=t.get("similarity_score", 0.0),
        )
        for t in result["tickets"]
    ]
    log.info(
        "Similar tickets: method=%s found=%d",
        result["search_method"], len(tickets),
    )
    return SimilarTicketsResponse(
        query_summary=result["query_summary"],
        total_found=result["total_found"],
        search_method=result["search_method"],
        tickets=tickets,
    )


# ─── Chat ────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=SlackMessageResponse)
def reply_to_message(request: SlackMessageRequest) -> SlackMessageResponse:
    log.info("POST /chat user=%s msg_chars=%d", request.userid, len(request.user_message))
    try:
        llm_client = build_llm_client(settings)
        llm_reply = llm_client.complete(SLACK_CHAT_SYSTEM_PROMPT, request.user_message).strip()
    except LLMConfigurationError as exc:
        log.error("LLM configuration error in /chat: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    log.info("Chat reply generated for user=%s reply_chars=%d", request.userid, len(llm_reply))
    return SlackMessageResponse(userid=request.userid, llm_reply=llm_reply)


# ─── Jira review workflow ────────────────────────────────────────────────────

@app.post("/workflow/jira-review", response_model=JiraReviewWorkflowResponse)
def workflow_jira_review(request: JiraReviewWorkflowRequest) -> JiraReviewWorkflowResponse:
    ticket_key = request.ticket_data.get("key") or request.ticket_data.get("issue_key") or "unknown"
    log.info("POST /workflow/jira-review key=%s channel=%s", ticket_key, request.slack_channel_id)
    try:
        workflow = build_workflow()
        result = workflow.handle_jira_review(
            ticket_data=request.ticket_data,
            slack_channel_id=request.slack_channel_id,
        )
        log.info("Jira review complete for %s: status=%s slack_sent=%s", ticket_key, result.get("status"), result.get("slack_sent"))
        return JiraReviewWorkflowResponse(**result)
    except json.JSONDecodeError as exc:
        log.error("LLM returned non-JSON for ticket %s", ticket_key)
        raise HTTPException(status_code=502, detail="LLM returned non-JSON output") from exc
    except (ConversationStoreError, LLMConfigurationError, RuntimeError, ValueError) as exc:
        log.error("Jira review workflow error for %s: %s", ticket_key, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/workflow/slack-reply", response_model=SlackReplyResponse)
def workflow_slack_reply(request: SlackReplyRequest) -> SlackReplyResponse:
    log.info(
        "POST /workflow/slack-reply user=%s channel=%s thread=%s",
        request.user_id, request.channel_id, request.thread_ts,
    )
    try:
        workflow = build_workflow()
        result = workflow.handle_slack_reply(
            user_id=request.user_id,
            channel_id=request.channel_id,
            thread_ts=request.thread_ts,
            text=request.text,
            event_ts=request.event_ts,
        )
        log.info("Slack reply handled: issue=%s status=%s", result.get("jira_issue_key"), result.get("status"))
        return SlackReplyResponse(**result)
    except json.JSONDecodeError as exc:
        log.error("LLM returned non-JSON in slack-reply: %s", exc)
        raise HTTPException(status_code=502, detail="LLM returned non-JSON output") from exc
    except (ConversationStoreError, LLMConfigurationError, RuntimeError, ValueError) as exc:
        log.error("Slack reply workflow error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/workflow/slack-events")
def workflow_slack_events(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("type") == "url_verification":
        log.debug("Slack url_verification challenge received")
        return {"challenge": payload.get("challenge")}

    event = payload.get("event")
    if not isinstance(event, dict):
        return {"ok": True, "ignored": "missing_event"}

    if event.get("bot_id") or event.get("subtype") == "bot_message":
        log.debug("Ignoring bot message in Slack events")
        return {"ok": True, "ignored": "bot_message"}

    thread_ts = event.get("thread_ts")
    text = event.get("text")
    channel_id = event.get("channel")
    user_id = event.get("user")
    if not all(isinstance(value, str) and value for value in [thread_ts, text, channel_id, user_id]):
        log.debug("Ignoring non-thread-reply Slack event")
        return {"ok": True, "ignored": "not_a_thread_reply"}

    log.info("Slack event: thread reply from user=%s channel=%s thread=%s", user_id, channel_id, thread_ts)

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


@app.post("/workflow2", response_model=Workflow2Response)
def workflow2(request: Workflow2Request) -> Workflow2Response:
    log.info(
        "POST /workflow2 user=%s channel=%s thread=%s msg_chars=%d",
        request.user_id,
        request.slack_channel_id,
        request.slack_thread_ts,
        len(request.user_message),
    )

    def out(reply: str) -> Workflow2Response:
        return Workflow2Response(
            slack_channel_id=request.slack_channel_id,
            slack_thread_ts=request.slack_thread_ts,
            reply=reply,
        )

    try:
        workflow = TestCaseChatWorkflow(settings)
        reply = workflow.handle(
            slack_channel_id=request.slack_channel_id,
            slack_thread_ts=request.slack_thread_ts,
            user_message=request.user_message,
        )
        return out(reply)
    except Exception:
        log.exception("/workflow2 failed")
        return out("Something went wrong while handling that test-case reply. Please check the service logs.")


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


def _selected_repositories(
    repositories: list[dict[str, Any]],
    selected_values: list[str],
) -> list[dict[str, Any]]:
    if not selected_values:
        return repositories
    selected = set(selected_values)
    return [
        repo for repo in repositories
        if repo.get("name") in selected or repo.get("path") in selected
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

    /* ── Test Cases tab ── */
    .tc-layout {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 24px;
      align-items: start;
    }
    .tc-form-col { min-width: 0; }
    .tc-result-col { min-width: 0; }
    .tc-section-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--muted);
      letter-spacing: .05em;
      margin: 0 0 10px;
    }
    .tc-field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
    .tc-field-row { display: flex; gap: 12px; margin-bottom: 12px; }
    .tc-label { font-size: 13px; font-weight: 600; color: var(--ink); }
    .tc-optional { font-weight: 400; color: var(--muted); }
    .tc-required { color: var(--danger); }
    .tc-input, .tc-select, .tc-textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
      font-size: 13px;
      background: #fff;
      color: var(--ink);
    }
    .tc-input:focus, .tc-select:focus, .tc-textarea:focus {
      outline: 2px solid var(--accent);
      outline-offset: -1px;
    }
    .tc-textarea { resize: vertical; min-height: 90px; }
    .tc-field { margin-bottom: 12px; }
    .tc-field-row .tc-field { margin-bottom: 0; }
    .tc-placeholder {
      color: var(--muted);
      font-size: 14px;
      padding: 48px 0;
      text-align: center;
    }
    .tc-stats {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }
    .tc-stat {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 4px 12px;
      font-size: 12px;
      font-weight: 600;
      color: var(--muted);
    }
    .tc-stat span { color: var(--accent); font-weight: 700; }
    .tc-output { line-height: 1.55; font-size: 14px; color: var(--ink); }
    .tc-doc { display: flex; flex-direction: column; gap: 14px; }
    .tc-overview {
      border-bottom: 1px solid var(--line);
      padding: 0 0 14px;
      color: #1f2937;
    }
    .tc-overview h3, .tc-gap h3 {
      font-size: 15px;
      margin: 0 0 8px;
      color: var(--ink);
    }
    .tc-overview p, .tc-gap p { margin: 7px 0; }
    .tc-case {
      border: 1px solid var(--line);
      border-left: 4px solid var(--accent);
      border-radius: 8px;
      background: #fff;
      padding: 16px;
      box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
    }
    .tc-case-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 10px;
    }
    .tc-case-title {
      font-size: 15px;
      line-height: 1.35;
      margin: 0;
      color: var(--ink);
      overflow-wrap: anywhere;
    }
    .tc-chip-row { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
    .tc-chip {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 3px 9px;
      background: var(--surface);
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      white-space: nowrap;
    }
    .tc-chip.p0 { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
    .tc-chip.p1 { background: #fff7ed; color: #9a3412; border-color: #fed7aa; }
    .tc-chip.p2 { background: #ecfdf5; color: #166534; border-color: #bbf7d0; }
    .tc-case-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 14px;
    }
    .tc-case-section {
      min-width: 0;
      border-top: 1px solid #eef2f7;
      padding-top: 9px;
    }
    .tc-case-section.full { grid-column: 1 / -1; }
    .tc-section-title {
      display: block;
      margin-bottom: 5px;
      font-size: 11px;
      line-height: 1.2;
      font-weight: 800;
      letter-spacing: .04em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .tc-section-body {
      color: #111827;
      overflow-wrap: anywhere;
    }
    .tc-section-body p { margin: 5px 0; }
    .tc-section-body ul, .tc-section-body ol {
      margin: 5px 0 0 18px;
      padding: 0;
    }
    .tc-section-body li { margin: 3px 0; }
    .tc-section-body code, .tc-overview code, .tc-gap code {
      font-family: ui-monospace, "Cascadia Code", "Fira Code", monospace;
      font-size: 12px;
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-radius: 5px;
      padding: 1px 4px;
      white-space: normal;
      overflow-wrap: anywhere;
    }
    .tc-gap {
      border: 1px solid #fed7aa;
      border-left: 4px solid #f97316;
      border-radius: 8px;
      background: #fffaf0;
      padding: 14px 16px;
      margin-top: 4px;
      color: #1f2937;
    }
    .tc-output hr { border: none; border-top: 1px solid var(--line); margin: 16px 0; }
    .tc-output strong { font-weight: 700; }
    .tc-card {
      background: #f0f4ff;
      border: 1px solid #c7d7f8;
      border-left: 4px solid var(--accent);
      border-radius: 8px;
      padding: 14px 16px;
      margin: 10px 0 16px;
      font-family: ui-monospace, "Cascadia Code", "Fira Code", monospace;
      font-size: 12.5px;
      white-space: pre-wrap;
      word-break: break-word;
      color: #172033;
    }
    .tc-card-title {
      font-weight: 700;
      font-size: 13px;
      color: var(--accent-strong);
      margin-bottom: 8px;
      display: block;
    }
    @media (max-width: 900px) {
      .tc-layout { grid-template-columns: 1fr; }
      .tc-case-head { flex-direction: column; }
      .tc-chip-row { justify-content: flex-start; }
      .tc-case-grid { grid-template-columns: 1fr; }
    }

    /* ── Similar Tickets tab ── */
    .sim-card {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 12px;
      transition: box-shadow .15s;
    }
    .sim-card:hover { box-shadow: 0 2px 10px rgba(0,0,0,.08); }
    .sim-card-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
    }
    .sim-card-key {
      font-family: ui-monospace, monospace;
      font-size: 12px;
      font-weight: 700;
      color: var(--accent);
      white-space: nowrap;
    }
    .sim-card-summary {
      font-size: 14px;
      font-weight: 600;
      color: var(--ink);
      flex: 1;
    }
    .sim-score {
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 20px;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .sim-score.high   { background: #dcfce7; color: var(--ok); }
    .sim-score.medium { background: #fef9c3; color: #854d0e; }
    .sim-score.low    { background: #f1f5f9; color: var(--muted); }
    .sim-score.kw     { background: #f1f5f9; color: var(--muted); }
    .sim-card-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 8px;
    }
    .sim-chip {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 10px;
      background: var(--surface);
      border: 1px solid var(--line);
      color: var(--muted);
    }
    .sim-chip.status-done     { background: #dcfce7; color: var(--ok);     border-color: #a7f3d0; }
    .sim-chip.status-closed   { background: #f1f5f9; color: var(--muted);  border-color: var(--line); }
    .sim-chip.status-resolved { background: #ede9fe; color: #6d28d9;       border-color: #c4b5fd; }
    .sim-chip.type-bug        { background: #fee2e2; color: var(--danger);  border-color: #fca5a5; }
    .sim-chip.type-story      { background: #dbeafe; color: var(--accent);  border-color: #93c5fd; }
    .sim-chip.type-task       { background: #fef9c3; color: #854d0e;        border-color: #fde68a; }
    .sim-description {
      font-size: 13px;
      color: var(--muted);
      line-height: 1.55;
      margin-top: 6px;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .sim-description.expanded { -webkit-line-clamp: unset; }
    .sim-expand-btn {
      font-size: 12px;
      color: var(--accent);
      background: none;
      border: none;
      padding: 2px 0;
      cursor: pointer;
      width: auto;
      min-height: unset;
      font-weight: 600;
      margin-top: 2px;
    }
    .sim-footer {
      display: flex;
      gap: 16px;
      margin-top: 8px;
      font-size: 12px;
      color: var(--muted);
      flex-wrap: wrap;
    }
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
    .progress-meta { font-size: 12px; color: var(--muted); margin-top: 6px; min-height: 16px; }
    .progress-track { height: 8px; background: var(--line); border-radius: 4px; overflow: hidden; }
    .progress-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.4s; }
    .progress-fill.indeterminate {
      width: 18%;
      background: linear-gradient(90deg, var(--accent), #8fb4ff, var(--accent));
      background-size: 180% 100%;
      animation: progressPulse 1.2s linear infinite;
    }
    @keyframes progressPulse {
      from { background-position: 180% 0; }
      to { background-position: -180% 0; }
    }

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
      <label><input id="buildEmbeddings" type="checkbox" checked> Build codebase embeddings</label>
      <label style="display:block;">
        <span style="display:block;margin-bottom:6px;">Codebase embedding model</span>
        <select id="embeddingModel" style="width:100%;border:1px solid var(--line);border-radius:6px;padding:9px 10px;font:inherit;background:#fff;">
          <option value="codebase_bge_m3">codebase_bge_m3</option>
          <option value="codebase_qwen3_0_6b">codebase_qwen3_0_6b</option>
          <option value="codebase_mxbai_large">codebase_mxbai_large</option>
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
          <div class="progress-meta" id="repoEta"></div>
        </div>
        <div class="progress-section">
          <div class="progress-label">Jira ticket progress</div>
          <div class="progress-track"><div class="progress-fill" id="jiraProgress" style="width:0%"></div></div>
          <div class="progress-meta" id="jiraEta"></div>
        </div>
        <div class="progress-section" id="embeddingProgressSection" hidden>
          <div class="progress-label" id="embeddingProgressLabel">Semantic embedding progress</div>
          <div class="progress-track"><div class="progress-fill" id="embeddingProgress" style="width:0%"></div></div>
          <div class="progress-meta" id="embeddingEta"></div>
        </div>
      </div>

      <!-- Tab navigation -->
      <nav class="tab-nav">
        <button class="tab-btn active" data-tab="repos">Repositories</button>
        <button class="tab-btn" data-tab="jira">Jira Tickets</button>
        <button class="tab-btn" data-tab="logs">Logs</button>
        <button class="tab-btn" data-tab="testcases">Test Cases</button>
        <button class="tab-btn" data-tab="similar">Similar Tickets</button>
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
      <!-- Tab: Test Cases -->
      <div class="tab-panel" id="tab-testcases">
        <div class="tc-layout">
          <!-- ── Form ── -->
          <div class="tc-form-col">
            <p class="tc-section-label">Search settings</p>
            <div class="tc-field-row">
              <div class="tc-field">
                <label class="tc-label">Style</label>
                <select id="tc-style" class="tc-select">
                  <option value="plain" selected>Plain Test Cases</option>
                  <option value="gherkin">Gherkin</option>
                  <option value="pytest">pytest</option>
                  <option value="junit">JUnit 5</option>
                </select>
              </div>
              <div class="tc-field">
                <label class="tc-label">Embedding model</label>
                <select id="tc-embeddingModel" class="tc-select">
                  <option value="codebase_bge_m3">codebase_bge_m3</option>
                  <option value="codebase_qwen3_0_6b">codebase_qwen3_0_6b</option>
                  <option value="codebase_mxbai_large">codebase_mxbai_large</option>
                </select>
              </div>
            </div>
            <div class="tc-field-row">
              <div class="tc-field">
                <label class="tc-label">Top K hits</label>
                <select id="tc-topK" class="tc-select">
                  <option value="5">5</option>
                  <option value="10">10</option>
                  <option value="15" selected>15</option>
                  <option value="20">20</option>
                  <option value="30">30</option>
                  <option value="50">50</option>
                </select>
              </div>
            </div>
            <div class="tc-field">
              <label class="tc-label">Repository <span class="tc-optional">(optional — leave blank for all repos)</span></label>
              <input id="tc-repo" type="text" class="tc-input" placeholder="e.g. ramfincorp-backend">
            </div>

            <p class="tc-section-label" style="margin-top:18px;">Ticket fields</p>
            <div class="tc-field-row">
              <div class="tc-field">
                <label class="tc-label">Issue key <span class="tc-required">*</span></label>
                <input id="tc-issueKey" type="text" class="tc-input" placeholder="RFC-101">
              </div>
              <div class="tc-field">
                <label class="tc-label">Issue type</label>
                <select id="tc-issueType" class="tc-select">
                  <option value="Bug">Bug</option>
                  <option value="Story">Story</option>
                  <option value="Task">Task</option>
                  <option value="Epic">Epic</option>
                  <option value="Improvement">Improvement</option>
                  <option value="Sub-task">Sub-task</option>
                </select>
              </div>
            </div>
            <div class="tc-field">
              <label class="tc-label">Summary <span class="tc-required">*</span></label>
              <input id="tc-summary" type="text" class="tc-input" placeholder="Short description of the ticket">
            </div>
            <div class="tc-field">
              <label class="tc-label">Description</label>
              <textarea id="tc-description" class="tc-textarea" rows="5" placeholder="Full ticket description…"></textarea>
            </div>
            <button id="tc-generateBtn" style="margin-top:18px;" onclick="generateTestCases()">Generate Test Cases</button>
            <div id="tc-status" class="status-bar" style="margin-top:10px;"></div>
          </div>

          <!-- ── Results ── -->
          <div class="tc-result-col" id="tc-result-col">
            <div id="tc-placeholder" class="tc-placeholder">
              Fill in the ticket details and click <strong>Generate Test Cases</strong>.
            </div>
            <div id="tc-stats" class="tc-stats" hidden>
              <span class="tc-stat"><span id="tc-stat-hits">0</span> semantic hits</span>
              <span class="tc-stat"><span id="tc-stat-funcs">0</span> Repomix repos</span>
              <span class="tc-stat"><span id="tc-stat-files">0</span> files</span>
              <button class="secondary" id="tc-copyBtn"
                style="width:auto;min-height:32px;padding:5px 14px;font-size:13px;margin-left:auto;"
                onclick="copyTestCases()">Copy Markdown</button>
            </div>
            <div id="tc-output" class="tc-output" hidden></div>
          </div>
        </div>
      </div>

      <!-- Tab: Similar Tickets -->
      <div class="tab-panel" id="tab-similar">
        <div class="tc-layout">

          <!-- ── Form ── -->
          <div class="tc-form-col">
            <p class="tc-section-label">New ticket details</p>
            <div class="tc-field">
              <label class="tc-label">Summary <span class="tc-required">*</span></label>
              <input id="sim-summary" type="text" class="tc-input" placeholder="Short description of the new ticket">
            </div>
            <div class="tc-field">
              <label class="tc-label">Description <span class="tc-optional">(optional but improves results)</span></label>
              <textarea id="sim-description" class="tc-textarea" rows="6" placeholder="Full ticket description…"></textarea>
            </div>

            <p class="tc-section-label" style="margin-top:18px;">Search filters</p>
            <div class="tc-field-row">
              <div class="tc-field">
                <label class="tc-label">Project key <span class="tc-optional">(optional)</span></label>
                <input id="sim-projectKey" type="text" class="tc-input" placeholder="e.g. RFC">
              </div>
            </div>
            <button id="sim-searchBtn" style="margin-top:18px;" onclick="searchSimilarTickets()">Find Similar Tickets</button>
            <div id="sim-status" class="status-bar" style="margin-top:10px;"></div>
          </div>

          <!-- ── Results ── -->
          <div class="tc-result-col">
            <div id="sim-placeholder" class="tc-placeholder">
              Fill in a ticket summary and click <strong>Find Similar Tickets</strong>.
            </div>

            <div id="sim-stats" hidden style="display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
              <span class="tc-stat"><span id="sim-stat-total">0</span> tickets found</span>
              <span class="tc-stat" id="sim-stat-method-badge">—</span>
            </div>

            <div id="sim-results" hidden></div>
          </div>
        </div>
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
      const selected = [...selectedRepos];
      if (action !== "jira_tickets_only" && selected.length === 0) {
        setStatus("Select at least one repository", "error");
        return;
      }
      setBusy(true);
      resultEl.hidden = true;
      statsGrid.hidden = true;
      progressSection.hidden = true;
      setStatus(
        action === "jira_tickets_only"
          ? "Starting Jira-only job..."
          : `Starting job for ${selected.length} selected repos...`,
        "running",
      );

      try {
        const res  = await fetch("/graph-admin/trigger", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            action,
            repositories: selected,
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

        setStatus(
          `Job started (${data.job_id.slice(0, 8)}...) for ${data.repository_count || selected.length} repos`,
          "running",
        );
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
      const jiraEmbT = totals.jira_embedding_documents || 0;
      const jiraEmbD = progress.jira_embedding_documents_done || 0;
      const codeEmbT = totals.codebase_embedding_documents || 0;
      const codeEmbD = progress.codebase_embedding_documents_done || 0;
      const repoEta = progress.repositories_eta_seconds || 0;
      const jiraEta = progress.jira_embedding_eta_seconds || 0;
      const codeEta = progress.codebase_embedding_eta_seconds || 0;
      const embEta = progress.embedding_eta_seconds || jiraEta || codeEta || 0;
      const embActive = embT > 0 || embD > 0;
      let activeEmbD = embD;
      let activeEmbT = embT;
      let activeEmbEta = embEta;
      let activeEmbKind = "";
      if (jiraEmbT > 0 && jiraEmbD < jiraEmbT) {
        activeEmbD = jiraEmbD;
        activeEmbT = jiraEmbT;
        activeEmbEta = jiraEta;
        activeEmbKind = "Jira";
      } else if (codeEmbT > 0 && codeEmbD < codeEmbT) {
        activeEmbD = codeEmbD;
        activeEmbT = codeEmbT;
        activeEmbEta = codeEta;
        activeEmbKind = "Codebase";
      } else if (codeEmbT > 0) {
        activeEmbD = codeEmbD;
        activeEmbT = codeEmbT;
        activeEmbEta = codeEta;
        activeEmbKind = "Codebase";
      } else if (jiraEmbT > 0) {
        activeEmbD = jiraEmbD;
        activeEmbT = jiraEmbT;
        activeEmbEta = jiraEta;
        activeEmbKind = "Jira";
      }
      const inferEmbeddingActive =
        !embActive &&
        data.status === "running" &&
        document.querySelector("#buildEmbeddings").checked &&
        repoT > 0 &&
        repoD >= repoT;

      document.querySelector("#statRepos").textContent =
        repoT > 0 ? `${repoD}/${repoT}` : (data.repository_count != null ? `${data.repository_count}` : "0/0");
      document.querySelector("#statJira").textContent  =
        jiraT > 0 ? `${jiraD}/${jiraT}` : "0/0";
      document.querySelector("#statEmbeddings").textContent =
        embActive
          ? `${activeEmbD}/${activeEmbT}${activeEmbKind ? ` ${activeEmbKind}` : ""}`
          : (inferEmbeddingActive ? "running" : "—");

      setProgressBar("repoProgress", repoD, repoT);
      setProgressBar("jiraProgress", jiraD, jiraT);
      document.querySelector("#repoEta").textContent = formatEta(repoEta);
      document.querySelector("#jiraEta").textContent = formatEta(jiraEta);
      document.querySelector("#embeddingProgressSection").hidden = !(embActive || inferEmbeddingActive);
      let embeddingLabel = "Embedding progress";
      if (activeEmbKind === "Jira") {
        embeddingLabel = "Jira embedding progress";
      } else if (activeEmbKind === "Codebase") {
        embeddingLabel = "Codebase embedding progress";
      }
      if ((embActive && data.status === "running" && activeEmbT > 0 && activeEmbD === 0) || inferEmbeddingActive) {
        embeddingLabel += " (model running)";
      }
      document.querySelector("#embeddingProgressLabel").textContent = embeddingLabel;
      const embeddingProgress = document.querySelector("#embeddingProgress");
      const embeddingStarting = data.status === "running" && document.querySelector("#buildEmbeddings").checked && activeEmbT > 0 && activeEmbD === 0;
      if (inferEmbeddingActive || embeddingStarting) {
        embeddingProgress.classList.add("indeterminate");
      } else {
        embeddingProgress.classList.remove("indeterminate");
        setProgressBar("embeddingProgress", activeEmbD, activeEmbT);
      }
      const aggregateSuffix = activeEmbKind && embT > activeEmbT
        ? ` · Overall ${embD}/${embT}`
        : "";
      document.querySelector("#embeddingEta").textContent =
        `${formatEta(activeEmbEta)}${aggregateSuffix}`;
    }

    function setProgressBar(id, done, total) {
      const pct = total > 0 ? Math.round((done / total) * 100) : 0;
      document.querySelector(`#${id}`).style.width = `${pct}%`;
    }

    function formatEta(seconds) {
      seconds = Number(seconds || 0);
      if (!Number.isFinite(seconds) || seconds <= 0) return "";
      if (seconds < 60) return `ETA ${Math.round(seconds)}s`;
      const minutes = Math.floor(seconds / 60);
      const secs = Math.round(seconds % 60);
      if (minutes < 60) return `ETA ${minutes}m ${secs}s`;
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return `ETA ${hours}h ${mins}m`;
    }

    function runningStatusMessage(data) {
      const totals = data.totals || {};
      const progress = data.progress || {};
      const repoDone = (totals.repositories || 0) > 0 && progress.repositories_done >= totals.repositories;
      const jiraDone = (totals.jira_tickets || 0) > 0 && progress.jira_tickets_done >= totals.jira_tickets;
      const embTotal = totals.embedding_documents || 0;
      const embDone = progress.embedding_documents_done || 0;
      const jiraEmbTotal = totals.jira_embedding_documents || 0;
      const jiraEmbDone = progress.jira_embedding_documents_done || 0;
      const codeEmbTotal = totals.codebase_embedding_documents || 0;
      const codeEmbDone = progress.codebase_embedding_documents_done || 0;
      if (jiraEmbTotal > 0 && jiraEmbDone < jiraEmbTotal) return "Building Jira embeddings...";
      if (codeEmbTotal > 0 && codeEmbDone < codeEmbTotal) return "Building codebase embeddings...";
      if (embTotal > 0 && embDone < embTotal) return "Building embeddings...";
      if (
        embTotal === 0 &&
        document.querySelector("#buildEmbeddings").checked &&
        repoDone
      ) return "Building codebase embeddings...";
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

    // ── Test Cases tab ───────────────────────────────────────────────────
    let lastTestCaseMarkdown = "";

    async function generateTestCases() {
      const issueKey = document.querySelector("#tc-issueKey").value.trim();
      const summary  = document.querySelector("#tc-summary").value.trim();
      if (!issueKey || !summary) {
        tcSetStatus("Issue key and summary are required", "error");
        return;
      }

      const btn = document.querySelector("#tc-generateBtn");
      btn.disabled = true;
      tcSetStatus("Generating test cases with RepoTree… this may take 20–40 seconds", "running");
      document.querySelector("#tc-placeholder").hidden = false;
      document.querySelector("#tc-stats").hidden = true;
      document.querySelector("#tc-output").hidden = true;

      const ticket = {
        issueKey:     issueKey,
        issueType:    document.querySelector("#tc-issueType").value,
        summary:      summary,
        description:  document.querySelector("#tc-description").value.trim() || null,
      };

      const repoVal = document.querySelector("#tc-repo").value.trim();
      const body = {
        ticket_data:     ticket,
        repo:            repoVal || null,
        embedding_model: document.querySelector("#tc-embeddingModel").value,
        style:           document.querySelector("#tc-style").value,
        top_k:           parseInt(document.querySelector("#tc-topK").value, 10),
      };

      try {
        const res  = await fetch("/analyze-ticket/test-cases", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Generation failed");

        lastTestCaseMarkdown = data.test_cases || "";

        document.querySelector("#tc-stat-hits").textContent  = data.semantic_hits_count ?? 0;
        document.querySelector("#tc-stat-funcs").textContent = (data.grounded_repos || []).length || data.functions_found || 0;
        document.querySelector("#tc-stat-files").textContent = data.files_touched_count ?? 0;
        document.querySelector("#tc-stats").hidden  = false;
        document.querySelector("#tc-placeholder").hidden = true;

        const outputEl = document.querySelector("#tc-output");
        outputEl.innerHTML = renderMarkdown(lastTestCaseMarkdown);
        outputEl.hidden = false;

        tcSetStatus("Done", "ok");
      } catch (err) {
        tcSetStatus(err.message, "error");
        document.querySelector("#tc-placeholder").hidden = false;
      } finally {
        btn.disabled = false;
      }
    }

    function copyTestCases() {
      if (!lastTestCaseMarkdown) return;
      navigator.clipboard.writeText(lastTestCaseMarkdown).then(() => {
        const btn = document.querySelector("#tc-copyBtn");
        const orig = btn.textContent;
        btn.textContent = "Copied!";
        setTimeout(() => { btn.textContent = orig; }, 1800);
      });
    }

    function tcSetStatus(msg, cls = "") {
      const el = document.querySelector("#tc-status");
      el.textContent = msg;
      el.className = `status-bar ${cls}`;
    }

    function renderMarkdown(md) {
      const normalized = String(md || "").replace(/\\r\\n/g, "\\n").replace(/\\r/g, "\\n").trim();
      if (/^(?:#{1,6}\\s*)?TC-\\d+[:\\-]/im.test(normalized)) {
        return renderStructuredTestCases(normalized);
      }
      return `<div class="tc-doc">${renderBasicMarkdown(normalized)}</div>`;
    }

    const TC_FIELD_LABELS = [
      "Type", "Priority", "API / Layer", "Source references", "DB fixtures",
      "Auth fixtures", "Preconditions", "Test data", "Steps", "Expected result",
      "Assertions", "Automation notes", "Ticket reference"
    ];

    function renderStructuredTestCases(md) {
      const firstTc = md.search(/^(?:#{1,6}\\s*)?TC-\\d+[:\\-]/im);
      const overview = firstTc > 0 ? md.slice(0, firstTc).trim() : "";
      const rest = firstTc >= 0 ? md.slice(firstTc).trim() : md;
      const gapIndex = rest.search(/^(?:#{1,6}\\s*)?(Gaps|Open Questions)\\b/im);
      const casesText = gapIndex >= 0 ? rest.slice(0, gapIndex).trim() : rest;
      const gapText = gapIndex >= 0 ? rest.slice(gapIndex).trim() : "";
      const blocks = casesText
        .split(/(?=^(?:#{1,6}\\s*)?TC-\\d+[:\\-])/gim)
        .map(s => s.trim())
        .filter(Boolean);

      const html = [];
      if (overview) html.push(`<section class="tc-overview">${renderBasicMarkdown(overview, "Summary")}</section>`);
      blocks.forEach(block => html.push(renderTestCaseCard(block)));
      if (gapText) html.push(`<section class="tc-gap">${renderBasicMarkdown(gapText)}</section>`);
      return `<div class="tc-doc">${html.join("")}</div>`;
    }

    function renderTestCaseCard(block) {
      const lines = block.split("\\n");
      const title = (lines.shift() || "")
        .replace(/^#{1,6}\\s*/, "")
        .trim();
      const parsed = parseTestCaseFields(lines);
      const type = firstFieldLine(parsed.fields["Type"]);
      const priority = firstFieldLine(parsed.fields["Priority"]);

      const sections = [
        "API / Layer", "Source references", "DB fixtures", "Auth fixtures",
        "Preconditions", "Test data", "Steps", "Expected result", "Assertions",
        "Automation notes", "Ticket reference"
      ];

      const body = [];
      if (parsed.intro.length) {
        body.push(renderCaseSection("Notes", parsed.intro, true));
      }
      sections.forEach(label => {
        const lines = parsed.fields[label];
        if (!lines || !lines.length) return;
        const full = ["Source references", "DB fixtures", "Auth fixtures", "Steps", "Assertions"].includes(label);
        body.push(renderCaseSection(label, lines, full));
      });

      return `
        <article class="tc-case">
          <div class="tc-case-head">
            <h3 class="tc-case-title">${inlineFormat(title)}</h3>
            <div class="tc-chip-row">
              ${type ? `<span class="tc-chip">${inlineFormat(type)}</span>` : ""}
              ${priority ? `<span class="tc-chip ${priority.toLowerCase()}">${inlineFormat(priority)}</span>` : ""}
            </div>
          </div>
          <div class="tc-case-grid">${body.join("")}</div>
        </article>
      `;
    }

    function parseTestCaseFields(lines) {
      const fields = {};
      const intro = [];
      let current = null;

      lines.forEach(line => {
        const field = getFieldLine(line);
        if (field) {
          current = field.label;
          fields[current] = fields[current] || [];
          if (field.value) fields[current].push(field.value);
          return;
        }
        if (current) fields[current].push(line);
        else intro.push(line);
      });

      return {fields, intro: trimBlankLines(intro)};
    }

    function getFieldLine(line) {
      const stripped = line.trim().replace(/^[-*]\\s*/, "");
      for (const label of TC_FIELD_LABELS) {
        if (stripped.toLowerCase().startsWith(`${label.toLowerCase()}:`)) {
          return {
            label,
            value: stripped.slice(label.length + 1).trim(),
          };
        }
      }
      return null;
    }

    function renderCaseSection(label, lines, full = false) {
      const cleaned = trimBlankLines(lines);
      if (!cleaned.length) return "";
      return `
        <section class="tc-case-section ${full ? "full" : ""}">
          <span class="tc-section-title">${esc(label)}</span>
          <div class="tc-section-body">${renderLines(cleaned)}</div>
        </section>
      `;
    }

    function renderBasicMarkdown(text, fallbackTitle = "") {
      const lines = String(text || "").split("\\n");
      const html = [];
      let bodyLines = lines;
      const first = (lines[0] || "").trim();

      if (/^#{1,6}\\s+/.test(first)) {
        html.push(`<h3>${inlineFormat(first.replace(/^#{1,6}\\s+/, ""))}</h3>`);
        bodyLines = lines.slice(1);
      } else if (fallbackTitle) {
        html.push(`<h3>${esc(fallbackTitle)}</h3>`);
      }

      html.push(renderLines(bodyLines));
      return html.join("");
    }

    function renderLines(lines) {
      const html = [];
      let list = null;

      const closeList = () => {
        if (!list) return;
        html.push(`</${list}>`);
        list = null;
      };
      const openList = tag => {
        if (list === tag) return;
        closeList();
        list = tag;
        html.push(`<${tag}>`);
      };

      trimBlankLines(lines).forEach(raw => {
        const line = raw.trim();
        if (!line) {
          closeList();
          return;
        }
        const bullet = line.match(/^[-*]\\s+(.+)$/);
        if (bullet) {
          openList("ul");
          html.push(`<li>${inlineFormat(bullet[1])}</li>`);
          return;
        }
        const numbered = line.match(/^\\d+[.)]\\s+(.+)$/);
        if (numbered) {
          openList("ol");
          html.push(`<li>${inlineFormat(numbered[1])}</li>`);
          return;
        }
        closeList();
        if (/^---+$/.test(line)) html.push("<hr>");
        else html.push(`<p>${inlineFormat(line)}</p>`);
      });
      closeList();
      return html.join("");
    }

    function firstFieldLine(lines) {
      return (trimBlankLines(lines || [])[0] || "").trim();
    }

    function trimBlankLines(lines) {
      const copy = [...(lines || [])];
      while (copy.length && !copy[0].trim()) copy.shift();
      while (copy.length && !copy[copy.length - 1].trim()) copy.pop();
      return copy;
    }

    function inlineFormat(text) {
      return esc(text)
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>")
        .replace(/\\*([^*]+)\\*/g, "<em>$1</em>");
    }

    // ── Similar Tickets tab ──────────────────────────────────────────────
    async function searchSimilarTickets() {
      const summary = document.querySelector("#sim-summary").value.trim();
      if (!summary) {
        simSetStatus("Summary is required", "error");
        return;
      }
      const btn = document.querySelector("#sim-searchBtn");
      btn.disabled = true;
      simSetStatus("Searching for similar tickets…", "running");
      document.querySelector("#sim-placeholder").hidden = false;
      document.querySelector("#sim-stats").hidden = true;
      document.querySelector("#sim-results").hidden = true;

      const body = {
        summary,
        description: document.querySelector("#sim-description").value.trim() || null,
        project_key: document.querySelector("#sim-projectKey").value.trim() || null,
      };

      try {
        const res  = await fetch("/analyze-ticket/similar", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Search failed");

        document.querySelector("#sim-stat-total").textContent = data.total_found;
        const methodBadge = document.querySelector("#sim-stat-method-badge");
        const methodLabels = {
          "hybrid_rrf": "Hybrid semantic (RRF)",
          "semantic":   "Dense semantic",
          "keyword_fallback": "Keyword fallback",
          "none":       "No results",
        };
        const methodColors = {
          "hybrid_rrf": "var(--ok)",
          "semantic":   "var(--ok)",
          "keyword_fallback": "var(--warn)",
          "none":       "var(--warn)",
        };
        methodBadge.textContent = methodLabels[data.search_method] ?? data.search_method;
        methodBadge.style.color  = methodColors[data.search_method]  ?? "var(--warn)";

        const statsEl = document.querySelector("#sim-stats");
        statsEl.hidden = false;
        statsEl.style.display = "flex";

        document.querySelector("#sim-placeholder").hidden = true;

        const resultsEl = document.querySelector("#sim-results");
        if (!data.tickets || !data.tickets.length) {
          resultsEl.innerHTML = '<p style="color:var(--muted);font-size:14px;">No ticket above 65% match found. Try removing the project key.</p>';
        } else {
          resultsEl.innerHTML = data.tickets.map(renderSimCard).join("");
        }
        resultsEl.hidden = false;
        simSetStatus(data.total_found ? `Found ${data.total_found} similar ticket${data.total_found !== 1 ? "s" : ""}` : "No matches found", data.total_found ? "ok" : "");
      } catch (err) {
        simSetStatus(err.message, "error");
        document.querySelector("#sim-placeholder").hidden = false;
      } finally {
        btn.disabled = false;
      }
    }

    function renderSimCard(t) {
      const score = t.similarity_score || 0;
      const scoreLabel = score === 0 ? "keyword" : `${Math.round(score * 100)}% match`;
      const scoreClass = score === 0 ? "kw" : score >= 0.75 ? "high" : score >= 0.5 ? "medium" : "low";

      const statusKey = (t.status || "").toLowerCase().replace(/\\s+/g, "-");
      const typeKey   = (t.issue_type || "").toLowerCase();

      const chips = [
        t.status    ? `<span class="sim-chip status-${statusKey}">${esc(t.status)}</span>` : "",
        t.issue_type ? `<span class="sim-chip type-${typeKey}">${esc(t.issue_type)}</span>` : "",
        t.priority  ? `<span class="sim-chip">${esc(t.priority)}</span>` : "",
      ].filter(Boolean).join("");

      const desc = (t.description || "").trim();
      const descId = `sim-desc-${esc(t.ticket_key)}`;
      const descHtml = desc
        ? `<div class="sim-description" id="${descId}">${esc(desc)}</div>
           <button class="sim-expand-btn" onclick="toggleSimDesc('${descId}', this)">Show more</button>`
        : "";

      const footer = [
        t.assignee_name  ? `Assignee: <b>${esc(t.assignee_name)}</b>` : "",
        t.reporter_name  ? `Reporter: <b>${esc(t.reporter_name)}</b>` : "",
        t.updated_at     ? `Updated: ${esc(fmtDate(t.updated_at))}` : "",
        t.created_at     ? `Created: ${esc(fmtDate(t.created_at))}` : "",
      ].filter(Boolean).map(s => `<span>${s}</span>`).join("");

      const labels = (t.labels || []).map(l => `<span class="sim-chip">${esc(l)}</span>`).join("");

      return `
        <div class="sim-card">
          <div class="sim-card-header">
            <div>
              <span class="sim-card-key">${esc(t.ticket_key)}</span>
              <div class="sim-card-summary">${esc(t.summary || "")}</div>
            </div>
            <span class="sim-score ${scoreClass}">${scoreLabel}</span>
          </div>
          <div class="sim-card-meta">${chips}${labels}</div>
          ${descHtml}
          ${footer ? `<div class="sim-footer">${footer}</div>` : ""}
        </div>`;
    }

    function toggleSimDesc(id, btn) {
      const el = document.querySelector("#" + id);
      const expanded = el.classList.toggle("expanded");
      btn.textContent = expanded ? "Show less" : "Show more";
    }

    function simSetStatus(msg, cls = "") {
      const el = document.querySelector("#sim-status");
      el.textContent = msg;
      el.className = `status-bar ${cls}`;
    }

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

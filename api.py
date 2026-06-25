"""FastAPI entry point for Jira ticket analysis and graph DB administration.

Graph admin flow (replaces n8n):
  POST /graph-admin/trigger  → starts background job, returns job_id
  GET  /graph-admin/jobs     → list recent jobs
  GET  /graph-admin/jobs/{job_id} → poll job status + progress
"""

import asyncio
import json
import logging
import re
import time
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s: %(message)s",
    force=True,
)

from pathlib import Path
from typing import Any
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from app import auth
from app.auth import CurrentUser, require_tab

from app.code_analysis_report import build_code_analysis_report
from app.config import settings
from app.conversation_store import ConversationStoreError, PostgresConversationStore
from app.exceptions import LLMConfigurationError, PromptNotFoundError
from app.graph_context import GraphContextClient
from app.graph_job import job_store
from app.graph_job_runner import run_graph_job
from app.neo4j_job_runner import run_neo4j_graph_job
from app.neo4j_graph.analytics import graph_analytics
from app.neo4j_graph.builder import select_active_repositories
from app.neo4j_graph.config import GraphBuildConfig
from app.jira_client import JiraClient
from app.jira_ticket_insights import scan_jira_ticket_cache
from app.n8n_monitor import N8nMonitor, N8nMonitorError
from app.json_utils import parse_model_json, review_status, review_text
from app.llm_client import build_llm_client
from app.prompt_store import PromptStore
from app.repository_discovery import discover_graph_repositories
from app.repo_doc_generator import (
    list_doc_repositories,
    list_document_types,
)
from app.repo_tree_integration import (
    initialize_repo_tree,
    register_repo_tree_routes,
    repo_tree_status,
    shutdown_repo_tree,
)
from app.schemas import (
    AnalyzeTicketRequest,
    AnalyzeTicketResponse,
    CodeAnalysisReportRequest,
    RepoDocRequest,
    RepoDocExportRequest,
    RepoDocEmailRequest,
    RepomixReindexRequest,
    RepomixReindexResponse,
    Neo4jBuildRequest,
    Neo4jBuildResponse,
    GraphAdminTriggerRequest,
    GraphAdminTriggerResponse,
    GraphJobResponse,
    JiraReviewWorkflowRequest,
    JiraReviewWorkflowResponse,
    N8nMonitorResponse,
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
    AlertBatchResponse,
    DocReviewRequest,
    DocReviewResponse,
    TestCaseDocRequest,
    TestCaseDocResponse,
    TransitionRecordRequest,
    TransitionRecordResponse,
    RftSprintSettingRequest,
)
from app.similar_ticket_finder import SimilarTicketFinder
from app.slack_client import SlackClient
from app.slack_review_workflow import SlackReviewWorkflow
from app.testcase_chat_workflow import TestCaseChatWorkflow
from app.test_case_comparison_report import (
    build_test_case_comparison_report,
    build_test_case_comparison_sheet,
)
from app.test_case_generator import TestCaseGenerator
from app.ticket_analyzer import TicketAnalyzer
from app.workflow1_reviewer import Workflow1Reviewer
from app.workflow2_replier import Workflow2Replier
from app.workflow3_sla import Workflow3SLAChecker
from app.workflow4_due_date import Workflow4DueDateChecker
from app.workflow4_aigov import (
    Workflow4AigovAssigneeChecker,
    Workflow4AigovTLChecker,
    Workflow4SummaryAssigneeChecker,
    Workflow4SummaryTLChecker,
)
from app.workflow_governor_notify import GovernorNotifier
from app.rft_estimates import (
    SPRINT_SETTING_KEY,
    build_rft_estimate_report,
    get_sprint_setting,
    list_rft_sprints,
)
from app.app_settings import ensure_app_settings_schema, set_setting
from app.utilization import (
    build_utilization_report,
    ensure_status_history_schema,
    record_status_change,
)
from app.doc_review import DocReviewer
from app.testcase_document import build_and_attach

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_repo_tree()
    try:
        auth.ensure_auth_schema()
    except Exception:  # noqa: BLE001 - never block startup on auth setup
        log.exception("Auth schema initialization failed")
    try:
        from app.repo_doc_usage import ensure_doc_usage_schema

        ensure_doc_usage_schema()
    except Exception:  # noqa: BLE001
        log.exception("Document usage schema initialization failed")
    try:
        ensure_status_history_schema(settings)
    except Exception:  # noqa: BLE001
        log.exception("Status-history schema initialization failed")
    try:
        ensure_app_settings_schema(settings)
    except Exception:  # noqa: BLE001
        log.exception("App-settings schema initialization failed")
    try:
        from app.rft_estimate_analysis import ensure_predictions_schema

        ensure_predictions_schema(settings)
    except Exception:  # noqa: BLE001
        log.exception("RFT estimate predictions schema initialization failed")
    try:
        yield
    finally:
        shutdown_repo_tree()


app = FastAPI(
    title="Jira AI Ticket Analyzer",
    version="0.2.0",
    description="Jira ticket analysis, Slack review workflow, and graph DB administration.",
    docs_url=None,
    lifespan=lifespan,
)

register_repo_tree_routes(app)
app.include_router(auth.router)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent / "app" / "static"),
    name="static",
)

# ─── React SPA (built by Vite into frontend/dist) ────────────────────────────
FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"
if (FRONTEND_DIST / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="spa-assets",
    )

_SPA_MISSING_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Jira AI Admin</title></head><body style="font-family:sans-serif;padding:40px">
<h1>Frontend not built</h1>
<p>The React SPA has not been built yet. Run:</p>
<pre>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</pre>
<p>Then reload this page. The API itself is running normally.</p>
</body></html>"""


def _serve_spa() -> Response:
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return HTMLResponse(_SPA_MISSING_HTML, status_code=200)


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
        "repo_tree": repo_tree_status(),
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


# MoM 2 — 09:00 batch: < 75% time left -> assignee + Jira Governor.
@app.post("/workflow4/daily-assignee", response_model=AlertBatchResponse)
def workflow4_daily_assignee() -> AlertBatchResponse:
    log.info("POST /workflow4/daily-assignee")
    try:
        return AlertBatchResponse(**Workflow4SummaryAssigneeChecker(settings=settings).check())
    except RuntimeError as exc:
        log.exception("/workflow4/daily-assignee runtime failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow4/daily-assignee failed")
        raise HTTPException(status_code=500, detail=f"daily-assignee failed: {exc}") from exc


# MoM 2 — 15:00 batch: <= 50% time left -> TL channels.
@app.post("/workflow4/tl", response_model=AlertBatchResponse)
def workflow4_tl() -> AlertBatchResponse:
    log.info("POST /workflow4/tl")
    try:
        return AlertBatchResponse(**Workflow4SummaryTLChecker(settings=settings).check())
    except RuntimeError as exc:
        log.exception("/workflow4/tl runtime failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow4/tl failed")
        raise HTTPException(status_code=500, detail=f"workflow4/tl failed: {exc}") from exc


# AIGOV sandbox variants — refetch AIGOV + rebuild embeddings + LLM summary.
@app.post("/workflow4/aigov/daily-assignee", response_model=AlertBatchResponse)
def workflow4_aigov_daily_assignee() -> AlertBatchResponse:
    log.info("POST /workflow4/aigov/daily-assignee")
    try:
        return AlertBatchResponse(**Workflow4AigovAssigneeChecker(settings=settings).check())
    except RuntimeError as exc:
        log.exception("/workflow4/aigov/daily-assignee runtime failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow4/aigov/daily-assignee failed")
        raise HTTPException(status_code=500, detail=f"aigov daily-assignee failed: {exc}") from exc


@app.post("/workflow4/aigov/tl", response_model=AlertBatchResponse)
def workflow4_aigov_tl() -> AlertBatchResponse:
    log.info("POST /workflow4/aigov/tl")
    try:
        return AlertBatchResponse(**Workflow4AigovTLChecker(settings=settings).check())
    except RuntimeError as exc:
        log.exception("/workflow4/aigov/tl runtime failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow4/aigov/tl failed")
        raise HTTPException(status_code=500, detail=f"aigov workflow4/tl failed: {exc}") from exc


# AI Governor scheduled notification — cron-triggered n8n workflow posts the
# returned message to GOVERNOR_NOTIFY_CHANNEL_ID (default C0BD06WSN72).
@app.post("/workflow/governor-notify", response_model=AlertBatchResponse)
def workflow_governor_notify() -> AlertBatchResponse:
    log.info("POST /workflow/governor-notify")
    try:
        return AlertBatchResponse(**GovernorNotifier(settings=settings).notify())
    except Exception as exc:
        log.exception("/workflow/governor-notify failed")
        raise HTTPException(status_code=500, detail=f"governor-notify failed: {exc}") from exc


# WF7 — list open RFT tickets that have an Original Estimate filled and post the
# digest to GOVERNOR_NOTIFY_CHANNEL_ID.
@app.post("/workflow/rft-estimates", response_model=AlertBatchResponse)
def workflow_rft_estimates() -> AlertBatchResponse:
    log.info("POST /workflow/rft-estimates")
    try:
        return AlertBatchResponse(**build_rft_estimate_report(settings))
    except RuntimeError as exc:
        log.exception("/workflow/rft-estimates runtime failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("/workflow/rft-estimates failed")
        raise HTTPException(status_code=500, detail=f"rft-estimates failed: {exc}") from exc


# WF7 admin controls — read/update the sprint filter + list available sprints.
@app.get("/graph-admin/rft-estimate/settings")
def graph_admin_rft_estimate_settings(
    _user: CurrentUser = Depends(require_tab("workflows")),
) -> dict[str, Any]:
    return get_sprint_setting(settings)


@app.put("/graph-admin/rft-estimate/settings")
def graph_admin_set_rft_estimate_settings(
    request: RftSprintSettingRequest,
    _user: CurrentUser = Depends(require_tab("workflows")),
) -> dict[str, Any]:
    value = (request.value or "").strip()
    if value not in ("open", "all") and not value.isdigit():
        raise HTTPException(
            status_code=400,
            detail="value must be 'open', 'all', or a numeric sprint id",
        )
    try:
        set_setting(settings, SPRINT_SETTING_KEY, value)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    log.info("RFT estimate sprint filter set to %s", value)
    return get_sprint_setting(settings)


@app.get("/graph-admin/rft-estimate/sprints")
def graph_admin_rft_estimate_sprints(
    _user: CurrentUser = Depends(require_tab("workflows")),
) -> dict[str, Any]:
    return list_rft_sprints(settings)


# Status-transition log — the n8n "Status Transition Logger" workflow posts each
# Jira status change here so utilization analytics can count ticket movement.
@app.post("/workflow/record-transition", response_model=TransitionRecordResponse)
def workflow_record_transition(request: TransitionRecordRequest) -> TransitionRecordResponse:
    log.info(
        "POST /workflow/record-transition issue=%s %s -> %s",
        request.issueKey,
        request.fromStatus or "?",
        request.toStatus,
    )
    try:
        result = record_status_change(
            settings,
            issue_key=request.issueKey,
            to_status=request.toStatus,
            from_status=request.fromStatus,
            project_key=request.projectKey,
            issue_type=request.issueType,
            assignee=request.assignee,
            changed_at=request.changedAt,
        )
        return TransitionRecordResponse(**result)
    except Exception as exc:
        log.exception("/workflow/record-transition failed")
        raise HTTPException(status_code=500, detail=f"record-transition failed: {exc}") from exc


# Utilization analytics — aggregated counts across every AI Governor data source.
@app.get("/graph-admin/utilization")
def graph_admin_utilization(
    _user: CurrentUser = Depends(require_tab("utilization")),
) -> dict[str, Any]:
    log.debug("GET /graph-admin/utilization")
    try:
        return build_utilization_report(settings)
    except Exception as exc:
        log.exception("/graph-admin/utilization failed")
        raise HTTPException(status_code=500, detail=f"utilization failed: {exc}") from exc


# MoM 3 — review PRD / Tech-design docs linked on a ticket; comment the review.
@app.post("/workflow/doc-review", response_model=DocReviewResponse)
def workflow_doc_review(request: DocReviewRequest) -> DocReviewResponse:
    log.info("POST /workflow/doc-review issue=%s", request.issueKey)
    try:
        reviewer = DocReviewer(settings=settings, llm_client=build_llm_client(settings))
        return DocReviewResponse(**reviewer.review(request.issueKey, request.description))
    except Exception as exc:
        log.exception("/workflow/doc-review failed")
        raise HTTPException(status_code=500, detail=f"doc-review failed: {exc}") from exc


# MoM 4 — build a test-case .docx and attach it to the ticket at Ready for QA.
@app.post("/testcases/document", response_model=TestCaseDocResponse)
def testcases_document(request: TestCaseDocRequest) -> TestCaseDocResponse:
    log.info("POST /testcases/document issue=%s tcs=%d", request.issueKey, len(request.testcases))
    try:
        return TestCaseDocResponse(**build_and_attach(request.issueKey, request.summary, request.testcases))
    except Exception as exc:
        log.exception("/testcases/document failed")
        raise HTTPException(status_code=500, detail=f"testcases/document failed: {exc}") from exc


# ─── Admin UI (React SPA) ─────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def spa_root() -> Response:
    return _serve_spa()


@app.get("/graph-admin", include_in_schema=False)
def spa_graph_admin() -> Response:
    return _serve_spa()


# ─── Graph admin API ─────────────────────────────────────────────────────────

@app.get("/graph-admin/repositories")
def graph_admin_repositories(
    _user: CurrentUser = Depends(require_tab("repos")),
) -> dict[str, Any]:
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
    _user: CurrentUser = Depends(require_tab("repos")),
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


@app.post("/graph-admin/repomix/reindex", response_model=RepomixReindexResponse)
async def graph_admin_repomix_reindex(
    request: RepomixReindexRequest,
    _user: CurrentUser = Depends(require_tab("repos")),
) -> RepomixReindexResponse:
    """Refresh the RepoMix packed source for selected repositories.

    This repacks the local RepoMix XML used as code context (it does not touch the
    Graph DB). Only repacks repos whose HEAD changed since the last pack unless
    ``force`` is set. Repo names not present in the RepoMix config are returned in
    ``unknown`` rather than failing the whole call.
    """
    from repo_architect.reindex import reindex_repomix
    from app.repo_tree_integration import repo_tree_runtime

    log.info(
        "POST /graph-admin/repomix/reindex repos=%d pull_code=%s force=%s",
        len(request.repositories),
        request.pull_latest_code,
        request.force,
    )

    try:
        state = repo_tree_runtime()
        config = state.config
    except Exception as exc:
        log.exception("RepoMix runtime unavailable")
        raise HTTPException(status_code=503, detail=f"RepoMix not available: {exc}") from exc

    known_names = {repo.name for repo in config.repos}
    requested = request.repositories or list(known_names)
    selected = [name for name in requested if name in known_names]
    unknown = [name for name in requested if name not in known_names]

    if not selected:
        raise HTTPException(
            status_code=400,
            detail=(
                "No known RepoMix repositories selected. "
                f"Known repos: {', '.join(sorted(known_names)) or 'none'}"
            ),
        )

    try:
        summary = await asyncio.to_thread(
            reindex_repomix,
            config,
            repo_names=selected,
            do_git_pull=request.pull_latest_code,
            force=request.force,
        )
    except Exception as exc:
        log.exception("RepoMix reindex failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RepomixReindexResponse(
        selected=summary.get("selected", selected),
        packed=summary.get("packed", []),
        skipped=summary.get("skipped", []),
        failed=summary.get("failed", []),
        unknown=unknown,
        details=summary.get("details", []),
    )


@app.get("/graph-admin/jobs", response_model=list[GraphJobResponse])
def list_graph_jobs(
    limit: int = 10,
    _user: CurrentUser = Depends(require_tab("repos", "logs")),
) -> list[GraphJobResponse]:
    log.debug("GET /graph-admin/jobs limit=%d", limit)
    jobs = job_store.list_recent(limit=min(limit, 50))
    return [GraphJobResponse(**j.to_dict()) for j in jobs]


@app.get("/graph-admin/jobs/{job_id}", response_model=GraphJobResponse)
def get_graph_job(
    job_id: str,
    _user: CurrentUser = Depends(require_tab("repos", "logs")),
) -> GraphJobResponse:
    log.debug("GET /graph-admin/jobs/%s", job_id)
    job = job_store.get(job_id)
    if job is None:
        log.warning("Job %s not found", job_id)
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return GraphJobResponse(**job.to_dict())


# ─── Neo4j code-graph admin ────────────────────────────────────────────────

@app.get("/graph-admin/neo4j/active-repositories")
def neo4j_active_repositories(
    _user: CurrentUser = Depends(require_tab("neo4j")),
) -> dict[str, Any]:
    """Active (non-stale) repositories eligible for the Neo4j graph build."""
    cfg = GraphBuildConfig.from_settings()
    repos = select_active_repositories(cfg)
    return {
        "repository_count": len(repos),
        "activity_min_score": cfg.activity_min_score,
        "repositories": repos,
    }


@app.get("/graph-admin/neo4j/analytics")
def neo4j_graph_analytics(
    _user: CurrentUser = Depends(require_tab("neo4j")),
) -> dict[str, Any]:
    """Current node/relationship counts and per-repo / per-language breakdowns,
    plus per-metric trends (delta vs the previous snapshot)."""
    log.debug("GET /graph-admin/neo4j/analytics")
    from app.neo4j_graph.snapshots import attach_trends

    analytics = graph_analytics(GraphBuildConfig.from_settings())
    return attach_trends(settings, analytics)


@app.post("/graph-admin/neo4j/build", response_model=Neo4jBuildResponse)
def neo4j_build(
    request: Neo4jBuildRequest,
    background_tasks: BackgroundTasks,
    _user: CurrentUser = Depends(require_tab("neo4j")),
) -> Neo4jBuildResponse:
    """Build/update the Neo4j code graph for active repos in the background."""
    if request.wipe_mode not in ("managed", "all", "none"):
        raise HTTPException(status_code=400, detail="wipe_mode must be managed|all|none")
    if not settings.neo4j_password:
        raise HTTPException(status_code=503, detail="NEO4J_PASSWORD is not configured on the server")

    cfg = GraphBuildConfig.from_settings()
    active = select_active_repositories(cfg, request.repositories or None)
    if not active:
        raise HTTPException(status_code=400, detail="No active repositories matched the request")

    job = job_store.create(action="neo4j_build")
    log.info("Enqueuing Neo4j graph job %s (repos=%d wipe=%s code=%s)",
             job.job_id, len(active), request.wipe_mode, request.include_code)
    background_tasks.add_task(
        run_neo4j_graph_job,
        job,
        selected_repositories=request.repositories or None,
        wipe_mode=request.wipe_mode,
        include_code=request.include_code,
    )
    return Neo4jBuildResponse(
        job_id=job.job_id, status=job.status, repository_count=len(active)
    )


@app.get("/graph-admin/neo4j/jobs/{job_id}", response_model=GraphJobResponse)
def neo4j_get_job(
    job_id: str,
    _user: CurrentUser = Depends(require_tab("neo4j")),
) -> GraphJobResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return GraphJobResponse(**job.to_dict())


@app.post("/graph-admin/code-analysis-report")
async def download_code_analysis_report(
    request: CodeAnalysisReportRequest,
    _user: CurrentUser = Depends(require_tab("repos")),
) -> Response:
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


# ─── Repository documentation ────────────────────────────────────────────────

@app.get("/graph-admin/repo-docs/repositories")
def graph_admin_repo_doc_repositories(
    _user: CurrentUser = Depends(require_tab("docs")),
) -> dict[str, Any]:
    log.info("GET /graph-admin/repo-docs/repositories")
    try:
        repositories = list_doc_repositories()
    except Exception as exc:
        log.exception("Failed to list documentation repositories")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "repository_count": len(repositories),
        "repositories": repositories,
        # Real generation types plus the synthetic "all" bundle option.
        "doc_types": list_document_types() + [{"id": "all", "label": "All documents (ZIP)"}],
        # USD→INR rate so the UI can display costs in rupees.
        "usd_to_inr": settings.usd_to_inr,
    }


@app.post("/graph-admin/repo-docs/generate")
def graph_admin_generate_repo_doc(
    request: RepoDocRequest,
    user: CurrentUser = Depends(require_tab("docs")),
) -> dict[str, Any]:
    """Start async document generation and return a job id to poll.

    Generation runs 30s-4min, so it is done on a background thread to avoid
    reverse-proxy read timeouts (e.g. nginx 504). Poll
    /graph-admin/repo-docs/jobs/{job_id} for the result. ``doc_type == "all"``
    generates every document type and bundles them as a ZIP.
    """
    log.info(
        "POST /graph-admin/repo-docs/generate repo=%s doc_type=%s by=%s",
        request.repo,
        request.doc_type,
        user.email,
    )
    from app.repo_doc_jobs import start_doc_job

    job_id = start_doc_job(request.repo, request.doc_type, user_email=user.email)
    return {"job_id": job_id, "status": "pending"}


@app.post("/graph-admin/repo-docs/estimate")
def graph_admin_estimate_repo_doc(
    request: RepoDocRequest,
    _user: CurrentUser = Depends(require_tab("docs")),
) -> dict[str, Any]:
    """Pre-flight cost + cache check used by the UI to confirm spend before
    starting a paid job. Documents already generated for the current code are
    reused at no cost, so when ``all_cached`` is true the UI can skip the cost
    prompt. Spends no tokens.
    """
    log.info(
        "POST /graph-admin/repo-docs/estimate repo=%s doc_type=%s",
        request.repo,
        request.doc_type,
    )
    from app.repo_doc_jobs import estimate_doc_job

    try:
        return estimate_doc_job(request.repo, request.doc_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/graph-admin/repo-docs/jobs/{job_id}")
def graph_admin_repo_doc_job(
    job_id: str,
    _user: CurrentUser = Depends(require_tab("docs")),
) -> dict[str, Any]:
    from app.repo_doc_jobs import get_doc_job

    job = get_doc_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown document job id")
    return job


@app.post("/graph-admin/repo-docs/export")
def graph_admin_export_repo_doc(
    request: RepoDocExportRequest,
    _user: CurrentUser = Depends(require_tab("docs")),
) -> Response:
    log.info("POST /graph-admin/repo-docs/export filename=%s", request.filename)
    if not request.markdown.strip():
        raise HTTPException(status_code=400, detail="No markdown content to export")
    try:
        from app.markdown_docx import markdown_to_docx_bytes

        data = markdown_to_docx_bytes(request.markdown, title=request.filename)
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="The 'python-docx' package is required for DOCX export",
        ) from exc
    except Exception as exc:
        log.exception("DOCX export failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    base = request.filename or "document"
    if base.lower().endswith(".md"):
        base = base[:-3]
    filename = f"{base}.docx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _docx_for_doc(markdown: str, base: str) -> bytes:
    from app.markdown_docx import markdown_to_docx_bytes

    return markdown_to_docx_bytes(markdown, title=base)


def _base_name(filename: str) -> str:
    return filename[:-3] if filename.lower().endswith(".md") else filename


def _build_doc_attachments(job: dict[str, Any]) -> list[tuple[str, bytes, str]]:
    """Return email/download attachments for a finished doc job.

    One .docx for a single document; a .zip of .docx files for an 'all' job.
    """
    docs = job.get("docs") or []
    if not docs:
        raise HTTPException(status_code=400, detail="Job has no generated documents")

    if len(docs) == 1:
        d = docs[0]
        base = _base_name(d["filename"])
        return [(f"{base}.docx", _docx_for_doc(d["markdown"], base), _DOCX_MIME)]

    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in docs:
            base = _base_name(d["filename"])
            try:
                zf.writestr(f"{base}.docx", _docx_for_doc(d["markdown"], base))
            except Exception:  # noqa: BLE001 - fall back to markdown for this entry
                log.exception("DOCX build failed for %s; zipping markdown instead", base)
                zf.writestr(f"{base}.md", d["markdown"])
    return [(f"{job.get('repo', 'repo')}-docs.zip", buf.getvalue(), "application/zip")]


def _doc_email_bodies(job: dict[str, Any], requester: str) -> tuple[str, str]:
    """Build the plain-text and HTML email body with full generation details:
    repo, per-document token counts, and cost."""
    repo = job.get("repo", "repository")
    docs = job.get("docs") or []
    usage = job.get("usage") or {}
    generated_at = job.get("updated_at") or job.get("created_at") or ""
    model = next((d.get("model") for d in docs if d.get("model")), "") or "—"

    def toks(n: Any) -> str:
        return f"{int(n or 0):,}"

    # Costs are stored in USD; display them converted to INR.
    rate = settings.usd_to_inr

    def inr(n: Any) -> str:
        return f"₹{float(n or 0) * rate:,.2f}"

    total_in = usage.get("input_tokens", 0)
    total_out = usage.get("output_tokens", 0)
    total_cost = usage.get("cost_usd", 0)
    generated = usage.get("generated_count", 0)
    reused = usage.get("reused_count", 0)

    # ── Plain text ──
    lines = [
        f"Repository documentation for '{repo}'",
        "",
        f"Repository:    {repo}",
        f"Requested by:  {requester}",
        f"Generated at:  {generated_at}",
        f"Model:         {model}",
        "",
        f"Documents ({len(docs)}):",
    ]
    for d in docs:
        state = "reused (no code change)" if d.get("reused") else "generated"
        lines.append(
            f"  - {d.get('label', d.get('doc_type'))}: {state} · "
            f"{toks(d.get('input_tokens'))} in / {toks(d.get('output_tokens'))} out · "
            f"{inr(d.get('cost_usd'))}"
        )
    lines += [
        "",
        f"Totals: {toks(total_in)} input + {toks(total_out)} output tokens · {inr(total_cost)}",
        f"        {generated} generated, {reused} reused",
        "",
        f"Attached: {', '.join(d['filename'].replace('.md', '.docx') for d in docs) if len(docs) == 1 else repo + '-docs.zip (' + str(len(docs)) + ' Word files)'}",
    ]
    text = "\n".join(lines)

    # ── HTML ──
    cell = "padding:8px 12px;border-bottom:1px solid #e6eaf2"
    cell_r = cell + ";text-align:right"
    row_parts = []
    for d in docs:
        status_html = (
            "<span style='color:#059669;font-weight:600'>reused</span>"
            if d.get("reused")
            else "generated"
        )
        label = d.get("label", d.get("doc_type"))
        row_parts.append(
            f"<tr>"
            f"<td style='{cell}'>{label}</td>"
            f"<td style='{cell}'>{status_html}</td>"
            f"<td style='{cell_r}'>{toks(d.get('input_tokens'))}</td>"
            f"<td style='{cell_r}'>{toks(d.get('output_tokens'))}</td>"
            f"<td style='{cell_r}'>{inr(d.get('cost_usd'))}</td>"
            f"</tr>"
        )
    rows = "".join(row_parts)
    html = f"""\
<div style="font-family:Inter,Segoe UI,Arial,sans-serif;color:#0f172a;max-width:640px">
  <h2 style="margin:0 0 4px;font-size:20px">Repository documentation</h2>
  <p style="margin:0 0 16px;color:#64748b">Generated for <b>{repo}</b></p>
  <table style="border-collapse:collapse;font-size:13px;margin-bottom:16px">
    <tr><td style="padding:2px 12px 2px 0;color:#64748b">Repository</td><td><b>{repo}</b></td></tr>
    <tr><td style="padding:2px 12px 2px 0;color:#64748b">Requested by</td><td>{requester}</td></tr>
    <tr><td style="padding:2px 12px 2px 0;color:#64748b">Generated at</td><td>{generated_at}</td></tr>
    <tr><td style="padding:2px 12px 2px 0;color:#64748b">Model</td><td>{model}</td></tr>
  </table>
  <table style="border-collapse:collapse;width:100%;font-size:13px;border:1px solid #e6eaf2;border-radius:8px;overflow:hidden">
    <thead>
      <tr style="background:#eef2f9;text-align:left">
        <th style="padding:9px 12px">Document</th>
        <th style="padding:9px 12px">Status</th>
        <th style="padding:9px 12px;text-align:right">Input tok</th>
        <th style="padding:9px 12px;text-align:right">Output tok</th>
        <th style="padding:9px 12px;text-align:right">Cost</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
    <tfoot>
      <tr style="background:#f7f9fd;font-weight:700">
        <td style="padding:9px 12px" colspan="2">Total ({generated} generated, {reused} reused)</td>
        <td style="padding:9px 12px;text-align:right">{toks(total_in)}</td>
        <td style="padding:9px 12px;text-align:right">{toks(total_out)}</td>
        <td style="padding:9px 12px;text-align:right">{inr(total_cost)}</td>
      </tr>
    </tfoot>
  </table>
  <p style="margin:16px 0 0;color:#64748b;font-size:12px">
    The document{'s are' if len(docs) != 1 else ' is'} attached as
    {'a ZIP of Word files' if len(docs) != 1 else 'a Word file'}.
  </p>
</div>"""
    return text, html


@app.get("/graph-admin/repo-docs/jobs/{job_id}/zip")
def graph_admin_repo_doc_zip(
    job_id: str,
    _user: CurrentUser = Depends(require_tab("docs")),
) -> Response:
    from app.repo_doc_jobs import get_doc_job

    job = get_doc_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown document job id")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Job is not finished yet")
    attachments = _build_doc_attachments(job)
    filename, data, mime = attachments[0]
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/graph-admin/repo-docs/email")
def graph_admin_email_repo_doc(
    request: RepoDocEmailRequest,
    user: CurrentUser = Depends(require_tab("docs")),
) -> dict[str, Any]:
    from app.email_sender import EmailConfigError, email_configured, send_email
    from app.repo_doc_jobs import get_doc_job

    if not email_configured():
        raise HTTPException(
            status_code=503,
            detail="Email is not configured. Set SMTP_HOST and SMTP_FROM (and credentials).",
        )
    job = get_doc_job(request.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown document job id")
    if job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Job is not finished yet")

    recipients = [a for a in re.split(r"[,\s]+", request.to_email or "") if a]
    if not recipients:
        raise HTTPException(status_code=400, detail="Provide at least one recipient email")

    attachments = _build_doc_attachments(job)
    repo = job.get("repo", "repository")
    subject = f"Repository documentation — {repo}"
    body, html_body = _doc_email_bodies(job, user.email)
    try:
        send_email(
            to=recipients, subject=subject, body=body, html_body=html_body, attachments=attachments
        )
    except EmailConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("Failed to email repo docs")
        raise HTTPException(status_code=502, detail=f"Email send failed: {exc}") from exc

    log.info("Emailed repo docs job=%s to=%s by=%s", request.job_id, recipients, user.email)
    return {"sent": True, "recipients": recipients, "attachments": [a[0] for a in attachments]}


@app.get("/graph-admin/repo-docs/usage")
def graph_admin_repo_doc_usage(
    limit: int = 50,
    user: CurrentUser = Depends(require_tab("docs", "users")),
) -> dict[str, Any]:
    """Token/cost usage analytics for document generation.

    Admins (and the user-management role) see every user; others see only their
    own consumption.
    """
    from app.auth import has_tab
    from app.repo_doc_usage import usage_summary

    can_see_all = user.is_service or user.role == "admin" or has_tab(user.role, "users")
    scope = None if can_see_all else user.email
    return {
        "scope": "all" if can_see_all else user.email,
        "usd_to_inr": settings.usd_to_inr,
        **usage_summary(user_email=scope, limit=limit),
    }


# ─── Jira ticket cache browser ───────────────────────────────────────────────

@app.get("/graph-admin/jira-tickets")
def graph_admin_jira_tickets(
    limit: int = 100,
    offset: int = 0,
    project_key: str | None = None,
    _user: CurrentUser = Depends(require_tab("jira")),
) -> dict[str, Any]:
    log.debug("GET /graph-admin/jira-tickets project=%s limit=%d offset=%d", project_key, limit, offset)
    if not settings.database_url:
        return {
            "count": 0,
            "tickets": [],
            "excluded_projects": _excluded_jira_projects(),
            "error": "DATABASE_URL not configured",
        }
    try:
        import psycopg
        from psycopg.rows import dict_row

        where, base_params = _jira_project_where_clause(project_key)
        with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM jira_ticket_cache {where}",
                base_params,
            ).fetchone()
            count = row["n"] if row else 0

            list_params = (*base_params, limit, offset)
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
            return {
                "count": count,
                "tickets": [dict(t) for t in tickets],
                "excluded_projects": _excluded_jira_projects(),
            }
    except Exception as exc:
        log.error("Failed to query jira_ticket_cache: %s", exc)
        return {
            "count": 0,
            "tickets": [],
            "excluded_projects": _excluded_jira_projects(),
            "error": str(exc),
        }


@app.get("/graph-admin/fetch-logs")
def graph_admin_fetch_logs(
    limit: int = 100,
    _user: CurrentUser = Depends(require_tab("logs")),
) -> dict[str, Any]:
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


@app.get("/graph-admin/n8n/workflows", response_model=N8nMonitorResponse)
def graph_admin_n8n_workflows(
    _user: CurrentUser = Depends(require_tab("workflows")),
) -> N8nMonitorResponse:
    """Live n8n workflow monitor: published flag + recent run/error counts."""
    log.debug("GET /graph-admin/n8n/workflows")
    monitor = N8nMonitor(settings)
    try:
        data = monitor.overview()
    except N8nMonitorError as exc:
        log.warning("n8n monitor unavailable: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))
    return N8nMonitorResponse(**data)


@app.get("/graph-admin/jira-ticket-insights")
def graph_admin_jira_ticket_insights(
    project_key: str | None = None,
    match_type: str = "all",
    limit: int = 200,
    _user: CurrentUser = Depends(require_tab("insights")),
) -> dict[str, Any]:
    log.debug(
        "GET /graph-admin/jira-ticket-insights project=%s match_type=%s limit=%d",
        project_key,
        match_type,
        limit,
    )
    try:
        clean_project_key = project_key.strip().upper() if project_key else None
        return scan_jira_ticket_cache(
            settings,
            project_key=clean_project_key or None,
            match_type=match_type,
            limit=max(1, min(limit, 1000)),
            excluded_project_keys=_excluded_jira_projects(),
        )
    except Exception as exc:
        log.error("Failed to scan jira_ticket_cache: %s", exc)
        return {
            "total_tickets": 0,
            "matching_tickets": 0,
            "returned_tickets": 0,
            "counts": {},
            "tickets": [],
            "error": str(exc),
        }


@app.get("/graph-admin/test-case-comparison-report")
def graph_admin_test_case_comparison_report(
    project_key: str | None = None,
    limit: int = 500,
    pipeline_limit: int | None = None,
    format: str = "xlsx",
    _user: CurrentUser = Depends(require_tab("insights")),
) -> Response:
    log.debug(
        "GET /graph-admin/test-case-comparison-report project=%s limit=%d pipeline_limit=%s format=%s",
        project_key,
        limit,
        pipeline_limit,
        format,
    )
    try:
        clean_project_key = project_key.strip().upper() if project_key else None
        safe_limit = max(1, min(limit, 2000))
        safe_pipeline_limit = max(0, min(pipeline_limit, 50)) if pipeline_limit is not None else None
        output_format = (format or "xlsx").strip().lower()
        if output_format in {"md", "markdown"}:
            filename, markdown = build_test_case_comparison_report(
                settings,
                project_key=clean_project_key or None,
                limit=safe_limit,
                pipeline_limit=safe_pipeline_limit,
                excluded_project_keys=_excluded_jira_projects(),
            )
            return Response(
                content=markdown,
                media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        filename, workbook = build_test_case_comparison_sheet(
            settings,
            project_key=clean_project_key or None,
            limit=safe_limit,
            pipeline_limit=safe_pipeline_limit,
            excluded_project_keys=_excluded_jira_projects(),
        )
        return Response(
            content=workbook,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        log.exception("Failed to build test-case comparison report")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
def generate_test_cases(
    request: TestCaseRequest,
    _user: CurrentUser = Depends(require_tab("testcases")),
) -> TestCaseResponse:
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
def find_similar_tickets(
    request: SimilarTicketRequest,
    _user: CurrentUser = Depends(require_tab("similar")),
) -> SimilarTicketsResponse:
    """
    Find historically similar Jira tickets for a new incoming ticket.

    Search strategy (in order):
      1. Semantic – embed (summary + description) with Ollama, search Qdrant
         `jira_tickets` collection and enrich hits from PostgreSQL.
      2. Keyword fallback – ILIKE search in PostgreSQL `jira_ticket_cache` when
         Ollama / Qdrant is unavailable.

    All ticket statuses are considered. The response returns only the single best
    ticket when its similarity score is greater than the configured threshold
    (`SIMILAR_TICKET_MATCH_THRESHOLD`, default 68%); otherwise it returns empty.
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
    started_at = time.perf_counter()
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
        log.info(
            "/workflow2 completed channel=%s thread=%s reply_chars=%d duration_ms=%.2f",
            request.slack_channel_id,
            request.slack_thread_ts,
            len(reply),
            (time.perf_counter() - started_at) * 1000,
        )
        return out(reply)
    except Exception:
        log.exception(
            "/workflow2 failed channel=%s thread=%s duration_ms=%.2f",
            request.slack_channel_id,
            request.slack_thread_ts,
            (time.perf_counter() - started_at) * 1000,
        )
        return out("Something went wrong while handling that thread reply. Please check the service logs.")


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


def _excluded_jira_projects() -> list[str]:
    return [
        key.strip().upper()
        for chunk in settings.jira_excluded_project_keys.split(",")
        for key in chunk.split()
        if key.strip()
    ]


def _jira_project_where_clause(project_key: str | None = None) -> tuple[str, tuple[Any, ...]]:
    where_parts: list[str] = []
    params: list[Any] = []
    clean_project_key = project_key.strip().upper() if project_key else ""
    if clean_project_key:
        where_parts.append("UPPER(project_key) = %s")
        params.append(clean_project_key)

    excluded = _excluded_jira_projects()
    if excluded:
        placeholders = ", ".join(["%s"] * len(excluded))
        where_parts.append(f"UPPER(project_key) NOT IN ({placeholders})")
        params.extend(excluded)

    where = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    return where, tuple(params)


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


# ─── SPA client-side routing fallback ────────────────────────────────────────
# Defined last so it only catches paths not already handled by an API route or a
# mounted static directory. Any unknown GET path returns the React index.html so
# client-side routes such as /login and /docs-portal resolve on a hard refresh.

_API_PATH_PREFIXES = (
    "api/", "graph-admin", "auth/", "static/", "assets/", "analyze-ticket",
    "workflow", "scan/", "repomix/", "testcases/", "jobs", "repo-tree",
    "prompts", "chat", "health", "openapi.json",
)


@app.get("/{full_path:path}", include_in_schema=False)
def spa_catch_all(full_path: str) -> Response:
    # Unknown API paths should 404 as JSON-ish, not silently return the SPA shell.
    if full_path.startswith(_API_PATH_PREFIXES):
        raise HTTPException(status_code=404, detail="Not found")
    return _serve_spa()


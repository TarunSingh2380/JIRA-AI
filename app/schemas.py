"""Pydantic request and response models for the FastAPI layer.

This file defines the structured API contracts used by endpoints, including
the ticket-analysis request body, model-output response, and prompt-listing
response.
"""

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeTicketRequest(BaseModel):
    ticket_data: Dict[str, Any] = Field(..., description="Jira ticket metadata JSON.")


class AnalyzeTicketResponse(BaseModel):
    status: str
    review: str


class PromptListResponse(BaseModel):
    prompts: List[str]


class Workflow1ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    issueKey: str = ""
    summary: str = ""
    description: str = ""
    assignee: str = ""
    dueDate: str = ""
    createdAt: str = ""
    priority: str = ""
    issueType: str = ""
    status: str = ""
    reporter: str = ""


class Workflow1ReviewResponse(BaseModel):
    assignee_channel_id: str
    reporter_channel_id: str
    nature: str
    llm_review: str
    priority: str


class Workflow2ReplyRequest(BaseModel):
    slack_thread_ts: str = ""
    slack_channel_id: str = ""
    user_message: str = ""
    user_id: str = ""


class Workflow2ReplyResponse(BaseModel):
    reply: str
    slack_thread_ts: str
    slack_channel_id: str


class Workflow3SlackAlert(BaseModel):
    channel_id: str
    message: str


class Workflow3SLAResponse(BaseModel):
    status: str
    tickets_checked: int
    alerts_sent: int
    resolved_tickets: int
    alerts: List[Workflow3SlackAlert]


class Workflow4SlackAlert(BaseModel):
    channel_id: str
    message: str


class Workflow4DueDateResponse(BaseModel):
    status: str
    tickets_checked: int
    alerts_sent: int
    completed_tickets: int
    alerts: List[Workflow4SlackAlert]


class SlackMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    userid: str
    channelId: str
    threadid: str | None = None
    user_message: str = Field(..., alias="user message")


class SlackMessageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    userid: str
    llm_reply: str = Field(..., alias="LLM reply")


class JiraReviewWorkflowRequest(BaseModel):
    ticket_data: Dict[str, Any] = Field(..., description="Jira ticket metadata JSON.")
    slack_channel_id: str | None = Field(
        default=None,
        description="Slack channel/DM id where review messages should be posted.",
    )


class JiraReviewWorkflowResponse(BaseModel):
    jira_issue_key: str
    status: str
    review: str
    slack_thread_ts: str | None = None
    slack_sent: bool = False
    jira_update: Dict[str, Any] | None = None
    model_output: Dict[str, Any]


class SlackReplyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(..., alias="user")
    channel_id: str = Field(..., alias="channel")
    thread_ts: str
    text: str
    event_ts: str | None = None


class SlackReplyResponse(BaseModel):
    jira_issue_key: str
    status: str
    review: str
    slack_thread_ts: str
    slack_sent: bool
    jira_update: Dict[str, Any] | None = None
    model_output: Dict[str, Any]


class Workflow2Request(BaseModel):
    user_id: str | None = None
    slack_channel_id: str
    slack_thread_ts: str
    user_message: str


class Workflow2Response(BaseModel):
    slack_channel_id: str
    slack_thread_ts: str
    reply: str


class GraphAdminTriggerRequest(BaseModel):
    action: Literal["update", "regenerate", "create_new", "jira_tickets_only"]
    repositories: List[str] = []
    pull_latest_code: bool = True
    fetch_latest_jira_tickets: bool = True
    include_jira_tickets: bool = True
    build_embeddings: bool = True
    embedding_model: Literal["codebase_bge_m3", "codebase_qwen3_0_6b", "codebase_mxbai_large"] = "codebase_bge_m3"
    notes: str | None = None


class GraphAdminTriggerResponse(BaseModel):
    job_id: str
    action: str
    status: str
    repository_count: int
    excluded_repositories: List[str]


class GraphJobResponse(BaseModel):
    job_id: str
    action: str
    status: str
    totals: Dict[str, int]
    progress: Dict[str, int]
    logs: List[Dict[str, Any]] = []
    error: str | None = None
    started_at: str
    completed_at: str | None = None


class CodeAnalysisReportRequest(BaseModel):
    repositories: List[str]
    include_graph_context: bool = True
    embedding_model: Literal["codebase_bge_m3", "codebase_qwen3_0_6b", "codebase_mxbai_large"] = "codebase_bge_m3"


class TestCaseRequest(BaseModel):
    ticket_data: Dict[str, Any] = Field(..., description="JIRA ticket metadata JSON.")
    repo: str | None = Field(
        default=None,
        description="Repo full_name to restrict semantic search (e.g. 'owner/repo'). "
                    "None = search across all repos.",
    )
    embedding_model: Literal["codebase_bge_m3", "codebase_qwen3_0_6b", "codebase_mxbai_large"] = Field(
        default="codebase_bge_m3",
        description="Embedding model used for semantic search.",
    )
    style: Literal["gherkin", "pytest", "junit", "plain"] = Field(
        default="plain",
        description="Output format requested from RepoTree.",
    )
    top_k: int = Field(default=15, ge=1, le=50, description="Number of semantic hits to retrieve.")


class TestCaseResponse(BaseModel):
    ticket_key: str
    test_cases: str = Field(..., description="Markdown test-case document generated by Claude.")
    semantic_hits_count: int
    functions_found: int
    files_touched_count: int
    grounded_repos: list[str] = []
    style: str = "plain"
    architecture_context_chars: int = 0
    repomix_context_chars: int = 0


class SimilarTicketRequest(BaseModel):
    summary: str = Field(..., description="Summary of the new ticket.")
    description: str | None = Field(default=None, description="Full ticket description.")
    project_key: str | None = Field(default=None, description="Restrict search to a project key.")


class SimilarTicketResult(BaseModel):
    ticket_key: str
    project_key: str
    summary: str
    description: str | None = None
    status: str
    issue_type: str | None = None
    priority: str | None = None
    assignee_name: str | None = None
    reporter_name: str | None = None
    labels: list[str] = []
    created_at: str | None = None
    updated_at: str | None = None
    similarity_score: float = 0.0


class SimilarTicketsResponse(BaseModel):
    query_summary: str
    total_found: int
    search_method: str = Field(..., description="'hybrid_rrf', 'semantic', 'keyword_fallback', or 'none'")
    tickets: list[SimilarTicketResult]

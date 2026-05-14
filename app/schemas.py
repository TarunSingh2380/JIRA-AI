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


class GraphAdminTriggerRequest(BaseModel):
    action: Literal["update", "regenerate", "create_new", "jira_tickets_only"]
    pull_latest_code: bool = True
    fetch_latest_jira_tickets: bool = True
    include_jira_tickets: bool = True
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
    error: str | None = None
    started_at: str
    completed_at: str | None = None

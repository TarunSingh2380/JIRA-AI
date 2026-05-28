"""Pydantic request and response models for workflows 1 through 4."""

from typing import List

from pydantic import BaseModel, ConfigDict


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

"""Pydantic request and response models for the FastAPI layer.

This file defines the structured API contracts used by endpoints, including
the ticket-analysis request body, model-output response, and prompt-listing
response.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AnalyzeTicketRequest(BaseModel):
    ticket_data: Dict[str, Any] = Field(..., description="Jira ticket metadata JSON.")


class AnalyzeTicketResponse(BaseModel):
    status: str
    review: str


class PromptListResponse(BaseModel):
    prompts: List[str]

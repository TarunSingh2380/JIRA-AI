"""Simple Slack-style assistant API.

This FastAPI app accepts a Slack user id and message, sends the message to the
configured LLM, and returns a single-line reply.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.config import settings
from app.exceptions import LLMConfigurationError
from app.llm_client import build_llm_client


SYSTEM_PROMPT = (
    "You are a helpful assistant. Send the reply of the user message and only "
    "in a single line of 11-21 words."
)


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


app = FastAPI(
    title="Slack Message LLM API",
    version="0.1.0",
    description="Receives a Slack-style message and returns a one-line LLM reply.",
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "model": settings.llm_model,
    }


@app.post("/chat", response_model=SlackMessageResponse) 
def reply_to_message(request: SlackMessageRequest) -> SlackMessageResponse:
    print("Incoming request:", request.model_dump(by_alias=True))

    try:
        llm_client = build_llm_client(settings)
        llm_reply = llm_client.complete(SYSTEM_PROMPT, request.user_message).strip()
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SlackMessageResponse(userid=request.userid, llm_reply=llm_reply)

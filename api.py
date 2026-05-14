"""FastAPI entry point for serving Jira ticket analysis over HTTP.

This file exposes health, prompt-listing, and ticket-analysis endpoints.
It wires together the prompt store, LLM client, request/response schemas,
and the ticket analyzer service for external consumers.
"""

import json
import re

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.exceptions import LLMConfigurationError, PromptNotFoundError
from app.llm_client import build_llm_client
from app.prompt_store import PromptStore
from app.schemas import AnalyzeTicketRequest, AnalyzeTicketResponse, PromptListResponse
from app.ticket_analyzer import TicketAnalyzer


app = FastAPI(
    title="Jira AI Ticket Analyzer",
    version="0.1.0",
    description="Injects Jira ticket metadata into prompt templates and returns LLM analysis.",
)

prompt_store = PromptStore(settings.prompt_dir)


def parse_model_json(model_output: str) -> dict:
    try:
        parsed = json.loads(model_output)
    except json.JSONDecodeError:
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", model_output, re.DOTALL)
        if fenced_match:
            return json.loads(fenced_match.group(1))

        object_match = re.search(r"\{.*\}", model_output, re.DOTALL)
        if object_match:
            return json.loads(object_match.group(0))

        raise

    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("Expected a JSON object", model_output, 0)

    return parsed


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

        return AnalyzeTicketResponse(**model_json)

    except PromptNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

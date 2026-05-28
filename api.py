"""FastAPI entry point for Jira AI workflows 1 through 4."""

import logging

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.exceptions import PromptNotFoundError
from app.prompt_store import PromptStore
from app.schemas import (
    Workflow1ReviewRequest,
    Workflow1ReviewResponse,
    Workflow2ReplyRequest,
    Workflow2ReplyResponse,
    Workflow3SLAResponse,
    Workflow4DueDateResponse,
)
from app.workflow1_reviewer import Workflow1Reviewer
from app.workflow2_replier import Workflow2Replier
from app.workflow3_sla import Workflow3SLAChecker
from app.workflow4_due_date import Workflow4DueDateChecker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="Jira AI Workflows",
    version="0.1.0",
    description="Serves Jira AI workflow endpoints 1 through 4.",
)

prompt_store = PromptStore(settings.prompt_dir)


@app.post("/workflow1", response_model=Workflow1ReviewResponse)
def workflow1_review(request: Workflow1ReviewRequest) -> Workflow1ReviewResponse:
    LOGGER.info("workflow1 api received request: %s", request.model_dump())
    try:
        reviewer = Workflow1Reviewer(
            settings=settings,
            prompt_store=prompt_store,
        )
        response = Workflow1ReviewResponse(**reviewer.review(request))
        LOGGER.info("workflow1 api sending response: %s", response.model_dump())
        return response
    except ValueError as exc:
        LOGGER.exception("workflow1 api failed with validation error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (PromptNotFoundError, RuntimeError) as exc:
        LOGGER.exception("workflow1 api failed with runtime error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        LOGGER.exception("workflow1 api failed with unexpected error")
        raise HTTPException(status_code=500, detail=f"workflow1 failed: {exc}") from exc


@app.post("/workflow2", response_model=Workflow2ReplyResponse)
def workflow2_reply(request: Workflow2ReplyRequest) -> Workflow2ReplyResponse:
    LOGGER.info("workflow2 api received request: %s", request.model_dump())
    try:
        replier = Workflow2Replier(
            settings=settings,
            prompt_store=prompt_store,
        )
        response = Workflow2ReplyResponse(**replier.reply(request))
        LOGGER.info("workflow2 api sending response: %s", response.model_dump())
        return response
    except ValueError as exc:
        LOGGER.exception("workflow2 api failed with validation error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        LOGGER.exception("workflow2 api failed because ticket was not found")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        LOGGER.exception("workflow2 api failed with unexpected error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/workflow3", response_model=Workflow3SLAResponse)
def workflow3_sla_check() -> Workflow3SLAResponse:
    LOGGER.info("workflow3 api received request")
    try:
        checker = Workflow3SLAChecker(settings=settings)
        response = Workflow3SLAResponse(**checker.check())
        LOGGER.info("workflow3 api sending response: %s", response.model_dump())
        return response
    except RuntimeError as exc:
        LOGGER.exception("workflow3 api failed with runtime error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        LOGGER.exception("workflow3 api failed with unexpected error")
        raise HTTPException(status_code=500, detail=f"workflow3 failed: {exc}") from exc


@app.post("/workflow4", response_model=Workflow4DueDateResponse)
def workflow4_due_date_check() -> Workflow4DueDateResponse:
    LOGGER.info("workflow4 api received request")
    try:
        checker = Workflow4DueDateChecker(settings=settings)
        response = Workflow4DueDateResponse(**checker.check())
        LOGGER.info("workflow4 api sending response: %s", response.model_dump())
        return response
    except RuntimeError as exc:
        LOGGER.exception("workflow4 api failed with runtime error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        LOGGER.exception("workflow4 api failed with unexpected error")
        raise HTTPException(status_code=500, detail=f"workflow4 failed: {exc}") from exc

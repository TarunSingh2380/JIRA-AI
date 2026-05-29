"""Test case generator backed by RepoTree.

RepoTree is integrated in-process from JIRA-AI's bundled `repo_architect`
package, so JIRA-AI does not need a second uvicorn service. The old HTTP client
path is kept as a fallback for deployments that intentionally use a remote
RepoTree service.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

from app.config import Settings
from app.repo_tree_integration import generate_testcases_in_process, repo_tree_status

log = logging.getLogger(__name__)


class TestCaseGenerator:
    """Generate JIRA ticket test cases through RepoTree."""

    def __init__(self, settings: Settings, llm_client: Any | None = None) -> None:
        self.settings = settings
        self.llm_client = llm_client

    def generate(
        self,
        ticket_data: Dict[str, Any],
        *,
        repo: Optional[str] = None,
        embedding_model: str = "codebase_bge_m3",
        top_k: int = 15,
        style: str = "plain",
    ) -> Dict[str, Any]:
        ticket_key = (
            ticket_data.get("issueKey")
            or ticket_data.get("key")
            or ticket_data.get("issue_key")
            or "unknown"
        )
        repos = [repo] if repo else None
        payload = {
            "ticket": _ticket_payload(ticket_data),
            "style": style,
            "repos": repos,
            "embedding_model": embedding_model,
            "top_k": top_k,
            "include_semantic_context": True,
        }

        status_payload = repo_tree_status()
        if status_payload.get("mode") == "in_process":
            log.info(
                "Calling in-process RepoTree testcase generator ticket=%s repo=%s model=%s style=%s",
                ticket_key,
                repo,
                embedding_model,
                style,
            )
            try:
                data = generate_testcases_in_process(payload)
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail, default=str)
                raise RuntimeError(f"RepoTree testcase generation failed: {detail}") from exc
            except Exception as exc:
                log.warning("In-process RepoTree testcase generation failed for %s: %s", ticket_key, exc)
                raise RuntimeError(f"RepoTree testcase generation failed: {exc}") from exc
            return _result_payload(data, style)

        return self._generate_via_http(
            payload,
            ticket_key=ticket_key,
            repo=repo,
            embedding_model=embedding_model,
            style=style,
        )

    def _generate_via_http(
        self,
        payload: dict[str, Any],
        *,
        ticket_key: str,
        repo: Optional[str],
        embedding_model: str,
        style: str,
    ) -> Dict[str, Any]:
        if not self.settings.repo_tree_base_url:
            raise RuntimeError(
                "RepoTree in-process integration is unavailable and REPO_TREE_BASE_URL is not configured"
            )

        url = f"{self.settings.repo_tree_base_url}/testcases/generate"
        log.info(
            "Calling remote RepoTree testcase generator ticket=%s repo=%s model=%s style=%s",
            ticket_key,
            repo,
            embedding_model,
            style,
        )

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"accept": "application/json", "Content-Type": "application/json"},
                timeout=self.settings.repo_tree_timeout_seconds,
            )
            data = _json_response(response)
            response.raise_for_status()
        except requests.RequestException as exc:
            detail = _error_detail(getattr(exc, "response", None))
            message = detail or str(exc)
            log.warning("RepoTree testcase generation failed for %s: %s", ticket_key, message)
            raise RuntimeError(f"RepoTree testcase generation failed: {message}") from exc

        return _result_payload(data, style)


def _ticket_payload(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
    fields = ticket_data.get("fields") or {}
    issue_type = _string_value(
        ticket_data.get("issueType")
        or ticket_data.get("issue_type")
        or (fields.get("issuetype") or {}).get("name")
        or ""
    )
    description = _string_value(
        ticket_data.get("description")
        or ticket_data.get("description_text")
        or fields.get("description")
        or ""
    )
    labels = ticket_data.get("labels") or fields.get("labels") or []
    components = ticket_data.get("components") or fields.get("components") or []
    return {
        "key": _string_value(ticket_data.get("issueKey") or ticket_data.get("key") or ticket_data.get("issue_key") or ""),
        "summary": _string_value(ticket_data.get("summary") or ticket_data.get("title") or fields.get("summary") or ""),
        "issue_type": issue_type,
        "description": description,
        "acceptance_criteria": _string_value(
            ticket_data.get("acceptance_criteria")
            or ticket_data.get("acceptanceCriteria")
            or ticket_data.get("ac")
            or ""
        ),
        "labels": [_string_value(label) for label in labels] if isinstance(labels, list) else [],
        "components": _component_names(components),
    }


def _result_payload(data: dict[str, Any], style: str) -> dict[str, Any]:
    grounded_repos = data.get("grounded_repos") or []
    return {
        "test_cases": data.get("test_cases") or "",
        "semantic_hits_count": int(data.get("semantic_hits_count") or 0),
        "functions_found": len(grounded_repos),
        "files_touched_count": int(data.get("files_touched_count") or 0),
        "grounded_repos": grounded_repos,
        "style": data.get("style") or style,
        "architecture_context_chars": int(data.get("architecture_context_chars") or 0),
        "repomix_context_chars": int(data.get("repomix_context_chars") or 0),
    }


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


def _component_names(components: Any) -> list[str]:
    if not isinstance(components, list):
        return []
    names: list[str] = []
    for component in components:
        if isinstance(component, str):
            names.append(component)
        elif isinstance(component, dict) and component.get("name"):
            names.append(str(component["name"]))
        else:
            value = _string_value(component)
            if value:
                names.append(value)
    return names


def _json_response(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _error_detail(response: requests.Response | None) -> str:
    if response is None:
        return ""
    data = _json_response(response)
    detail = data.get("detail")
    if isinstance(detail, str):
        return detail
    if detail:
        return str(detail)
    return response.text[:500]

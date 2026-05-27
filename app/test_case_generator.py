"""Test case generator client backed by the RepoTree service.

This replaces the old Neo4j/CGC graph traversal in the test-case path. Qdrant
is still used by RepoTree for semantic code hits, then combined with its
Repomix-derived repository context.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import requests

from app.config import Settings

log = logging.getLogger(__name__)


class TestCaseGenerator:
    """Proxy JIRA ticket testcase generation to RepoTree."""

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

        url = f"{self.settings.repo_tree_base_url}/testcases/generate"
        log.info(
            "Calling RepoTree testcase generator ticket=%s repo=%s model=%s style=%s",
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

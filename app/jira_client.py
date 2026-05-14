"""Small Jira Cloud REST client for comments and workflow transitions."""

from __future__ import annotations

from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from app.config import Settings


class JiraClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def is_configured(self) -> bool:
        return bool(self.settings.jira_base_url and self.settings.jira_email and self.settings.jira_api_token)

    def add_comment(self, issue_key: str, text: str) -> dict[str, Any]:
        if not self.is_configured():
            return {"dry_run": True, "reason": "Jira credentials are not configured"}

        return self._request(
            "POST",
            f"/rest/api/3/issue/{issue_key}/comment",
            json={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": text}],
                        }
                    ],
                }
            },
        )

    def transition_to_approved(self, issue_key: str) -> dict[str, Any]:
        if not self.settings.jira_approved_transition_name:
            return {"skipped": True, "reason": "JIRA_APPROVED_TRANSITION_NAME is not configured"}

        transitions = self._request("GET", f"/rest/api/3/issue/{issue_key}/transitions")
        target = None
        for transition in transitions.get("transitions", []):
            if transition.get("name", "").lower() == self.settings.jira_approved_transition_name.lower():
                target = transition
                break

        if not target:
            return {
                "skipped": True,
                "reason": f"Transition '{self.settings.jira_approved_transition_name}' not found",
            }

        return self._request(
            "POST",
            f"/rest/api/3/issue/{issue_key}/transitions",
            json={"transition": {"id": target["id"]}},
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if not self.is_configured():
            return {"dry_run": True, "reason": "Jira credentials are not configured"}

        response = requests.request(
            method,
            f"{self.settings.jira_base_url}{path}",
            auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=self.settings.external_request_timeout_seconds,
            **kwargs,
        )
        if response.status_code == 204:
            return {"ok": True}
        response.raise_for_status()
        return response.json() if response.content else {"ok": True}

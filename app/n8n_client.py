"""n8n webhook client for graph database administration jobs."""

from __future__ import annotations

from typing import Any

import requests

from app.config import Settings


class N8NGraphClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def trigger_graph_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.n8n_graph_webhook_url:
            return {
                "sent": False,
                "dry_run": True,
                "reason": "N8N_GRAPH_WEBHOOK_URL is not configured",
                "payload": payload,
            }

        headers = {"Content-Type": "application/json"}
        if self.settings.n8n_api_key:
            headers["X-N8N-API-KEY"] = self.settings.n8n_api_key

        response = requests.post(
            self.settings.n8n_graph_webhook_url,
            json=payload,
            headers=headers,
            timeout=self.settings.external_request_timeout_seconds,
        )
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            data = {"text": response.text}

        return {
            "sent": True,
            "dry_run": False,
            "status_code": response.status_code,
            "response": data,
        }

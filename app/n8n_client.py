"""n8n webhook client for graph database administration jobs."""

from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import Settings

log = logging.getLogger(__name__)


class N8NGraphClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def trigger_graph_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.n8n_graph_webhook_url:
            log.warning("N8N_GRAPH_WEBHOOK_URL not configured; skipping graph job trigger (dry run)")
            return {
                "sent": False,
                "dry_run": True,
                "reason": "N8N_GRAPH_WEBHOOK_URL is not configured",
                "payload": payload,
            }

        log.info("Triggering n8n graph job webhook: %s", self.settings.n8n_graph_webhook_url)
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

        log.info("n8n webhook responded: status=%d", response.status_code)
        return {
            "sent": True,
            "dry_run": False,
            "status_code": response.status_code,
            "response": data,
        }

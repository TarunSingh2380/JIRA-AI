"""Minimal Slack Web API client used by the review workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from app.config import Settings


@dataclass(frozen=True)
class SlackPostResult:
    channel_id: str
    thread_ts: str
    message_ts: str
    sent: bool
    raw: dict[str, Any]


class SlackClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def post_message(self, *, channel_id: str, text: str, thread_ts: str | None = None) -> SlackPostResult:
        if not self.settings.slack_bot_token:
            fallback_ts = thread_ts or f"{datetime.now(timezone.utc).timestamp():.6f}"
            return SlackPostResult(
                channel_id=channel_id,
                thread_ts=fallback_ts,
                message_ts=fallback_ts,
                sent=False,
                raw={"ok": False, "dry_run": True, "reason": "SLACK_BOT_TOKEN is not configured"},
            )

        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.settings.slack_bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "channel": channel_id,
                "text": text,
                **({"thread_ts": thread_ts} if thread_ts else {}),
            },
            timeout=self.settings.external_request_timeout_seconds,
        )
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack chat.postMessage failed: {data}")

        message_ts = data["ts"]
        return SlackPostResult(
            channel_id=channel_id,
            thread_ts=thread_ts or message_ts,
            message_ts=message_ts,
            sent=True,
            raw=data,
        )

"""Minimal Slack Web API client used by the review workflow."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from app.config import Settings

log = logging.getLogger(__name__)


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
            log.warning(
                "SLACK_BOT_TOKEN not configured; skipping post_message to channel=%s (dry run)",
                channel_id,
            )
            fallback_ts = thread_ts or f"{datetime.now(timezone.utc).timestamp():.6f}"
            return SlackPostResult(
                channel_id=channel_id,
                thread_ts=fallback_ts,
                message_ts=fallback_ts,
                sent=False,
                raw={"ok": False, "dry_run": True, "reason": "SLACK_BOT_TOKEN is not configured"},
            )

        log.info(
            "Posting Slack message to channel=%s thread_ts=%s text_chars=%d",
            channel_id,
            thread_ts or "(new thread)",
            len(text),
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
            log.error("Slack chat.postMessage failed: %s", data)
            raise RuntimeError(f"Slack chat.postMessage failed: {data}")

        message_ts = data["ts"]
        log.info("Slack message posted: channel=%s message_ts=%s", channel_id, message_ts)
        return SlackPostResult(
            channel_id=channel_id,
            thread_ts=thread_ts or message_ts,
            message_ts=message_ts,
            sent=True,
            raw=data,
        )

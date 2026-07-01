"""Slack channel health check for the admin panel.

WorkFlow 4 (and the other Slack digests) fan out to channel IDs drawn from two
places — the ``channelid_table`` role map and each ticket's
``assignee_slack_id`` in ``due_date_tracking`` — plus a few channels pinned in
the environment. When the bot was never invited to one of those channels/DMs,
``chat.postMessage`` returns ``not_in_channel`` and the whole n8n Slack node
errors, without telling you *which* ID is at fault.

This module discovers every channel ID the system might post to and, on request,
sends a clearly-marked probe message to each one, flagging the IDs that fail so
an admin can re-invite the bot (or fix the row) from one place.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import Settings
from app.slack_client import SlackClient

log = logging.getLogger(__name__)

DEFAULT_PROBE_MESSAGE = (
    ":wave: *Channel health check* — automated test from the Jira-AI admin panel "
    "to confirm the bot can post here. You can ignore this message."
)


class ChannelHealthError(RuntimeError):
    """Raised when the channel inventory cannot be loaded."""


class ChannelHealthChecker:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.slack = SlackClient(settings)

    # ── Discovery ────────────────────────────────────────────────────────────
    def discover(self) -> list[dict[str, Any]]:
        """Return every known channel ID with a list of where it comes from.

        Each entry: ``{"channel_id": str, "sources": [str, ...]}``. A channel can
        surface from several sources (e.g. it is both a role channel and pinned
        in the environment); they are merged so we probe each ID only once.
        """
        sources: dict[str, list[str]] = {}

        def add(channel_id: Any, label: str) -> None:
            cid = str(channel_id or "").strip()
            if not cid:
                return
            bucket = sources.setdefault(cid, [])
            if label not in bucket:
                bucket.append(label)

        # Config-pinned channels (governor digest, WF7 report, default).
        add(self.settings.governor_notify_channel_id, "env:GOVERNOR_NOTIFY_CHANNEL_ID")
        add(self.settings.rft_estimate_channel_id, "env:RFT_ESTIMATE_CHANNEL_ID")
        add(self.settings.slack_default_channel_id, "env:SLACK_DEFAULT_CHANNEL_ID")

        # Database-backed channels (role map + per-assignee DM IDs).
        for cid, label in self._load_db_channels():
            add(cid, label)

        return [
            {"channel_id": cid, "sources": sources[cid]}
            for cid in sorted(sources)
        ]

    def _load_db_channels(self) -> list[tuple[str, str]]:
        if not self.settings.database_url:
            log.warning("DATABASE_URL not set; skipping DB channel discovery")
            return []
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError as exc:  # pragma: no cover - deployment guard
            raise ChannelHealthError("The 'psycopg2-binary' package is required") from exc

        found: list[tuple[str, str]] = []
        try:
            with psycopg2.connect(self.settings.database_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Role map — grab every row, not just the five WF4 roles, so
                    # newly added roles are covered automatically.
                    try:
                        cursor.execute("SELECT role, channel_id FROM channelid_table")
                        for row in cursor.fetchall():
                            role = str(row.get("role") or "?")
                            found.append((row.get("channel_id"), f"role:{role}"))
                    except Exception as exc:  # noqa: BLE001 - table may be absent
                        log.warning("channelid_table read failed: %s", exc)

                    # Per-assignee DM IDs used by the due-date digests.
                    try:
                        cursor.execute(
                            "SELECT DISTINCT assignee_slack_id FROM due_date_tracking "
                            "WHERE assignee_slack_id IS NOT NULL AND assignee_slack_id <> ''"
                        )
                        for row in cursor.fetchall():
                            found.append((row.get("assignee_slack_id"), "assignee_slack_id"))
                    except Exception as exc:  # noqa: BLE001 - table may be absent
                        log.warning("due_date_tracking read failed: %s", exc)
        except ChannelHealthError:
            raise
        except Exception as exc:  # noqa: BLE001 - connection-level failure
            raise ChannelHealthError(f"channel discovery DB error: {exc}") from exc
        return found

    # ── Probe ────────────────────────────────────────────────────────────────
    def check(
        self,
        *,
        channel_ids: list[str] | None = None,
        message: str | None = None,
    ) -> dict[str, Any]:
        """Send a probe to each channel and flag the failures.

        If ``channel_ids`` is given, only those are probed (still annotated with
        their discovered sources where known); otherwise the full inventory is
        swept.
        """
        inventory = self.discover()
        source_map = {item["channel_id"]: item["sources"] for item in inventory}

        if channel_ids:
            targets = [str(c).strip() for c in channel_ids if str(c).strip()]
        else:
            targets = [item["channel_id"] for item in inventory]

        text = (message or DEFAULT_PROBE_MESSAGE).strip() or DEFAULT_PROBE_MESSAGE
        configured = bool(self.settings.slack_bot_token)

        results: list[dict[str, Any]] = []
        for cid in targets:
            probe = self.slack.probe_channel(channel_id=cid, text=text)
            results.append(
                {
                    "channel_id": cid,
                    "sources": source_map.get(cid, ["adhoc"]),
                    "ok": probe.ok,
                    "error": probe.error,
                    "message_ts": probe.message_ts,
                }
            )

        failed = [r for r in results if not r["ok"]]
        return {
            "configured": configured,
            "checked": len(results),
            "ok_count": len(results) - len(failed),
            "failed_count": len(failed),
            "probe_message": text,
            "results": results,
        }

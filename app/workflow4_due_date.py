"""Workflow4 due-date compliance checker for n8n polling."""

from __future__ import annotations

import logging
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from app.config import Settings


LOGGER = logging.getLogger(__name__)

DONE_STATUSES = {
    "Done",
    "Closed",
    "Resolved",
    "Ready for QA",
    "Ready for Deployment",
}

ROLE_QUERIES = {
    "eng_lead": "SELECT channel_id FROM channelid_table WHERE role = 'eng_lead' LIMIT 1",
    "cto": "SELECT channel_id FROM channelid_table WHERE role = 'cto' LIMIT 1",
    "ceo": "SELECT channel_id FROM channelid_table WHERE role = 'ceo' LIMIT 1",
    "team_channel": "SELECT channel_id FROM channelid_table WHERE role = 'team_channel' LIMIT 1",
    "jira_owner": "SELECT channel_id FROM channelid_table WHERE role = 'jira_owner' LIMIT 1",
}

ALERT_FLAG_COLUMNS = {
    "75_REMAINING": "alert_75_sent",
    "50_REMAINING": "alert_50_sent",
    "25_REMAINING": "alert_25_sent",
    "BREACHED": "alert_0_sent",
}

EXCEEDED_INTERVAL_HOURS = {
    "P0": 1,
    "P1": 24,
    "P2": 336,
    "P3": 168,
    "P4": 168,
}


class Workflow4DueDateChecker:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def check(self) -> dict[str, Any]:
        self._log_step("validate_config", "started")
        if not self.settings.database_url:
            self._log_step("validate_config", "failed", output={"missing": "DATABASE_URL"})
            raise RuntimeError("DATABASE_URL is required for workflow4")
        if not self._jira_is_configured():
            self._log_step("validate_config", "failed", output={"missing": "Jira credentials"})
            raise RuntimeError("Jira credentials are required for workflow4")
        self._log_step(
            "validate_config",
            "completed",
            output={"database_url_configured": True, "jira_configured": True},
        )

        try:
            self._log_step("load_database_driver", "started", input_data={"driver": "psycopg2"})
            import psycopg2
            from psycopg2.extras import RealDictCursor
            self._log_step("load_database_driver", "completed", output={"driver": "psycopg2"})
        except ImportError as exc:
            self._log_step("load_database_driver", "failed", output={"driver": "psycopg2"})
            raise RuntimeError("The 'psycopg2-binary' package is required") from exc

        alerts: list[dict[str, str]] = []
        completed_count = 0

        with psycopg2.connect(self.settings.database_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                self._log_step("fetch_role_channels", "started")
                role_channels = self._fetch_role_channels(cursor)
                self._log_step("fetch_role_channels", "completed", output=role_channels)
                self._log_step("fetch_active_tickets", "started")
                tickets = self._fetch_active_tickets(cursor)
                total_count = len(tickets)
                self._log_step(
                    "fetch_active_tickets",
                    "completed",
                    output={"ticket_count": total_count},
                )
                LOGGER.info("workflow4 started: checking %s active tickets", total_count)

                for ticket in tickets:
                    jira_ticket_id = str(ticket.get("jira_ticket_id") or "")
                    try:
                        self._log_step(
                            "process_ticket",
                            "started",
                            input_data={
                                "jira_ticket_id": jira_ticket_id,
                                "priority": ticket.get("priority"),
                                "due_date": ticket.get("due_date"),
                            },
                        )
                        self._log_step(
                            "check_jira_status",
                            "started",
                            input_data={"jira_ticket_id": jira_ticket_id},
                        )
                        if self._jira_ticket_is_done(jira_ticket_id):
                            self._log_step(
                                "check_jira_status",
                                "completed",
                                output={"jira_ticket_id": jira_ticket_id, "is_done": True},
                            )
                            self._mark_completed(cursor, jira_ticket_id)
                            conn.commit()
                            completed_count += 1
                            self._log_step(
                                "process_ticket",
                                "completed",
                                output={"jira_ticket_id": jira_ticket_id, "result": "completed"},
                            )
                            LOGGER.info("workflow4 %s: completed (ticket is Done)", jira_ticket_id)
                            continue
                        self._log_step(
                            "check_jira_status",
                            "completed",
                            output={"jira_ticket_id": jira_ticket_id, "is_done": False},
                        )

                        self._log_step(
                            "calculate_due_date_progress",
                            "started",
                            input_data={"jira_ticket_id": jira_ticket_id},
                        )
                        progress = self._calculate_progress(ticket)
                        self._log_step(
                            "calculate_due_date_progress",
                            "completed",
                            output={
                                "jira_ticket_id": jira_ticket_id,
                                "today": progress["today"],
                                "due_date": progress["due_date"],
                                "tracking_start": progress["tracking_start"],
                                "elapsed_working_days": progress["elapsed_working_days"],
                                "total_working_days": progress["total_working_days"],
                                "percentage_used": progress["percentage_used"],
                            },
                        )
                        self._log_step(
                            "determine_alert_level",
                            "started",
                            input_data={"jira_ticket_id": jira_ticket_id},
                        )
                        alert_level = self._determine_alert_level(ticket, progress["percentage_used"])
                        self._log_step(
                            "determine_alert_level",
                            "completed",
                            output={"jira_ticket_id": jira_ticket_id, "alert_level": alert_level},
                        )
                        LOGGER.info(
                            "workflow4 %s: %.1f%% used, alert=%s",
                            jira_ticket_id,
                            progress["percentage_used"],
                            alert_level,
                        )
                        if alert_level is None:
                            self._log_step(
                                "process_ticket",
                                "completed",
                                output={"jira_ticket_id": jira_ticket_id, "result": "no_alert_needed"},
                            )
                            continue

                        priority = str(ticket.get("priority") or "").upper()
                        if alert_level == "EXCEEDED":
                            self._log_step(
                                "evaluate_exceeded_interval",
                                "started",
                                input_data={"jira_ticket_id": jira_ticket_id, "priority": priority},
                            )
                            days_overdue = self._count_working_days(
                                progress["due_date"],
                                progress["today"],
                            )
                            LOGGER.info(
                                "workflow4 %s: due date exceeded, days overdue=%s",
                                jira_ticket_id,
                                days_overdue,
                            )
                            if not self._should_send_exceeded(ticket, priority):
                                self._log_step(
                                    "evaluate_exceeded_interval",
                                    "completed",
                                    output={
                                        "jira_ticket_id": jira_ticket_id,
                                        "should_send": False,
                                        "days_overdue": days_overdue,
                                    },
                                )
                                self._log_step(
                                    "process_ticket",
                                    "completed",
                                    output={
                                        "jira_ticket_id": jira_ticket_id,
                                        "result": "exceeded_alert_suppressed",
                                    },
                                )
                                continue
                            self._log_step(
                                "evaluate_exceeded_interval",
                                "completed",
                                output={
                                    "jira_ticket_id": jira_ticket_id,
                                    "should_send": True,
                                    "days_overdue": days_overdue,
                                },
                            )
                        else:
                            days_overdue = None

                        self._log_step(
                            "select_target_channels",
                            "started",
                            input_data={"jira_ticket_id": jira_ticket_id, "alert_level": alert_level},
                        )
                        target_channels = self._target_channels(ticket, role_channels, alert_level)
                        self._log_step(
                            "select_target_channels",
                            "completed",
                            output={"jira_ticket_id": jira_ticket_id, "target_channels": target_channels},
                        )
                        if not target_channels:
                            self._log_step(
                                "process_ticket",
                                "completed",
                                output={"jira_ticket_id": jira_ticket_id, "result": "no_target_channels"},
                            )
                            continue

                        self._log_step(
                            "build_alert_message",
                            "started",
                            input_data={"jira_ticket_id": jira_ticket_id, "alert_level": alert_level},
                        )
                        message = self._build_message(
                            ticket=ticket,
                            alert_level=alert_level,
                            due_date=progress["due_date"],
                            elapsed_working_days=progress["elapsed_working_days"],
                            total_working_days=progress["total_working_days"],
                            days_overdue=days_overdue,
                        )
                        self._log_step(
                            "build_alert_message",
                            "completed",
                            output={
                                "jira_ticket_id": jira_ticket_id,
                                "message_length": len(message),
                            },
                        )
                        for target_channel in target_channels:
                            alerts.append(
                                {
                                    "channel_id": target_channel,
                                    "message": message,
                                }
                            )

                        self._log_step(
                            "mark_alert_sent",
                            "started",
                            input_data={"jira_ticket_id": jira_ticket_id, "alert_level": alert_level},
                        )
                        self._mark_alert_sent(cursor, jira_ticket_id, alert_level)
                        conn.commit()
                        self._log_step(
                            "process_ticket",
                            "completed",
                            output={
                                "jira_ticket_id": jira_ticket_id,
                                "result": "alert_created",
                                "alert_level": alert_level,
                                "target_channel_count": len(target_channels),
                            },
                        )
                    except Exception:
                        conn.rollback()
                        self._log_step(
                            "process_ticket",
                            "failed",
                            output={"jira_ticket_id": jira_ticket_id},
                        )
                        LOGGER.exception("workflow4 %s: failed processing ticket", jira_ticket_id)
                        continue

        LOGGER.info(
            "workflow4 completed: %s alerts, %s completed",
            len(alerts),
            completed_count,
        )
        self._log_step(
            "workflow4_response",
            "completed",
            output={
                "tickets_checked": total_count,
                "alerts_sent": len(alerts),
                "completed_tickets": completed_count,
            },
        )
        return {
            "status": "completed",
            "tickets_checked": total_count,
            "alerts_sent": len(alerts),
            "completed_tickets": completed_count,
            "alerts": alerts,
        }

    def _fetch_role_channels(self, cursor: Any) -> dict[str, str | None]:
        channels: dict[str, str | None] = {}
        for key, query in ROLE_QUERIES.items():
            cursor.execute(query)
            row = cursor.fetchone()
            channels[key] = self._clean_channel(row.get("channel_id")) if row else None
        return channels

    def _fetch_active_tickets(self, cursor: Any) -> list[dict[str, Any]]:
        cursor.execute(
            """
            SELECT *
            FROM due_date_tracking
            WHERE is_completed = FALSE
            ORDER BY due_date ASC
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def _jira_ticket_is_done(self, jira_ticket_id: str) -> bool:
        if not jira_ticket_id:
            raise ValueError("jira_ticket_id is required")

        response = requests.get(
            f"{self.settings.jira_base_url}/rest/api/3/issue/{jira_ticket_id}",
            params={"fields": "status"},
            auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
            headers={"Accept": "application/json"},
            timeout=self.settings.external_request_timeout_seconds,
        )
        response.raise_for_status()
        status_name = response.json().get("fields", {}).get("status", {}).get("name")
        return status_name in DONE_STATUSES

    def _jira_is_configured(self) -> bool:
        return bool(self.settings.jira_base_url and self.settings.jira_email and self.settings.jira_api_token)

    def _mark_completed(self, cursor: Any, jira_ticket_id: str) -> None:
        cursor.execute(
            """
            UPDATE due_date_tracking
            SET is_completed = TRUE
            WHERE jira_ticket_id = %s
            """,
            (jira_ticket_id,),
        )

    def _calculate_progress(self, ticket: dict[str, Any]) -> dict[str, Any]:
        today = date.today()
        due_date = self._coerce_date(ticket.get("due_date"), "due_date")
        tracking_start = self._coerce_date(ticket.get("tracking_start_date"), "tracking_start_date")
        total_working_days = int(ticket.get("total_working_days") or 0)

        elapsed_working_days = self._count_working_days(
            tracking_start,
            min(today, due_date),
        )
        if total_working_days > 0:
            percentage_used = (elapsed_working_days / total_working_days) * 100
        else:
            percentage_used = 100

        return {
            "today": today,
            "due_date": due_date,
            "tracking_start": tracking_start,
            "total_working_days": total_working_days,
            "elapsed_working_days": elapsed_working_days,
            "percentage_used": percentage_used,
        }

    def _coerce_date(self, value: Any, field_name: str) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise ValueError(f"{field_name} must be a date")

    def _count_working_days(self, start: date, end: date) -> int:
        count = 0
        current = start
        while current <= end:
            if current.weekday() < 5:
                count += 1
            current += timedelta(days=1)
        return count

    def _determine_alert_level(self, ticket: dict[str, Any], percentage_used: float) -> str | None:
        today = date.today()
        due_date = self._coerce_date(ticket.get("due_date"), "due_date")
        is_exceeded = today > due_date
        alert_0_sent = ticket.get("alert_0_sent")
        alert_25_sent = ticket.get("alert_25_sent")
        alert_50_sent = ticket.get("alert_50_sent")
        alert_75_sent = ticket.get("alert_75_sent")

        if is_exceeded:
            return "EXCEEDED"
        elif alert_0_sent:
            return None
        elif percentage_used >= 100:
            return "BREACHED"
        elif alert_25_sent:
            return None
        elif percentage_used >= 75:
            return "25_REMAINING"
        elif alert_50_sent:
            return None
        elif percentage_used >= 50:
            return "50_REMAINING"
        elif alert_75_sent:
            return None
        elif percentage_used >= 25:
            return "75_REMAINING"
        else:
            return None

    def _should_send_exceeded(self, ticket: dict[str, Any], priority: str) -> bool:
        exceeded_interval = EXCEEDED_INTERVAL_HOURS.get(priority, 168)
        now_utc = datetime.now(timezone.utc)
        exceeded_alert_sent_at = ticket.get("exceeded_alert_sent_at")
        if exceeded_alert_sent_at is None:
            return True
        if not isinstance(exceeded_alert_sent_at, datetime):
            raise ValueError("exceeded_alert_sent_at must be a timestamp")
        if exceeded_alert_sent_at.tzinfo is None:
            exceeded_alert_sent_at = exceeded_alert_sent_at.replace(tzinfo=timezone.utc)
        hours_since = (now_utc - exceeded_alert_sent_at).total_seconds() / 3600
        return hours_since >= exceeded_interval

    def _target_channels(
        self,
        ticket: dict[str, Any],
        role_channels: dict[str, str | None],
        alert_level: str,
    ) -> list[str]:
        priority = str(ticket.get("priority") or "").upper()
        assignee_slack_id = self._clean_channel(ticket.get("assignee_slack_id"))
        matrix = {
            "P0": {
                "75_REMAINING": [assignee_slack_id],
                "50_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "25_REMAINING": [
                    assignee_slack_id,
                    role_channels["jira_owner"],
                    role_channels["eng_lead"],
                ],
                "BREACHED": [
                    assignee_slack_id,
                    role_channels["jira_owner"],
                    role_channels["eng_lead"],
                    role_channels["cto"],
                    role_channels["ceo"],
                ],
                "EXCEEDED": [role_channels["team_channel"]],
            },
            "P1": {
                "75_REMAINING": [],
                "50_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "25_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "BREACHED": [assignee_slack_id, role_channels["jira_owner"], role_channels["eng_lead"]],
                "EXCEEDED": [role_channels["team_channel"]],
            },
            "P2": {
                "75_REMAINING": [],
                "50_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "25_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "BREACHED": [assignee_slack_id, role_channels["jira_owner"]],
                "EXCEEDED": [role_channels["team_channel"]],
            },
            "P3": {
                "75_REMAINING": [],
                "50_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "25_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "BREACHED": [assignee_slack_id, role_channels["jira_owner"]],
                "EXCEEDED": [role_channels["team_channel"]],
            },
            "P4": {
                "75_REMAINING": [],
                "50_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "25_REMAINING": [assignee_slack_id, role_channels["jira_owner"]],
                "BREACHED": [assignee_slack_id, role_channels["jira_owner"]],
                "EXCEEDED": [role_channels["team_channel"]],
            },
        }
        return [
            channel
            for channel in matrix.get(priority, {}).get(alert_level, [])
            if channel is not None
        ]

    def _clean_channel(self, value: Any) -> str | None:
        channel = str(value or "").strip()
        return channel or None

    def _build_message(
        self,
        *,
        ticket: dict[str, Any],
        alert_level: str,
        due_date: date,
        elapsed_working_days: int,
        total_working_days: int,
        days_overdue: int | None,
    ) -> str:
        jira_ticket_id = str(ticket.get("jira_ticket_id") or "")
        priority = str(ticket.get("priority") or "")
        assignee_slack_id = str(ticket.get("assignee_slack_id") or "")

        if alert_level == "EXCEEDED":
            return (
                f"🚨 *Due Date EXCEEDED — {jira_ticket_id}*\n\n"
                f"*Priority:* {priority}\n"
                f"*Assignee:* <@{assignee_slack_id}>\n"
                f"*Due Date:* {due_date}\n"
                f"*Days Overdue:* {days_overdue} working days\n\n"
                f"👉 https://ramfincorp.atlassian.net/browse/{jira_ticket_id}"
            )

        return (
            f"⚠️ *Due Date Alert — {alert_level}*\n\n"
            f"*Ticket:* {jira_ticket_id}\n"
            f"*Priority:* {priority}\n"
            f"*Assignee:* <@{assignee_slack_id}>\n"
            f"*Due Date:* {due_date}\n"
            f"*Working Days Elapsed:* {elapsed_working_days} of {total_working_days}\n"
            f"*Status:* {alert_level}\n\n"
            f"👉 https://ramfincorp.atlassian.net/browse/{jira_ticket_id}"
        )

    def _mark_alert_sent(self, cursor: Any, jira_ticket_id: str, alert_level: str) -> None:
        if alert_level == "EXCEEDED":
            cursor.execute(
                """
                UPDATE due_date_tracking
                SET exceeded_alert_sent_at = NOW()
                WHERE jira_ticket_id = %s
                """,
                (jira_ticket_id,),
            )
            return

        column = ALERT_FLAG_COLUMNS[alert_level]
        cursor.execute(
            f"""
            UPDATE due_date_tracking
            SET {column} = TRUE
            WHERE jira_ticket_id = %s
            """,
            (jira_ticket_id,),
        )

    def _log_step(
        self,
        step: str,
        status: str,
        *,
        input_data: Any | None = None,
        output: Any | None = None,
    ) -> None:
        LOGGER.info(
            "workflow4 structured log: %s",
            json.dumps(
                {
                    "step": step,
                    "status": status,
                    "input": input_data,
                    "output": output,
                },
                ensure_ascii=False,
                default=str,
            ),
        )

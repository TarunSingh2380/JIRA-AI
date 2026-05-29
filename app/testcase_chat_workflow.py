"""Slack Q&A and edit handling for Jira ticket threads.

The n8n closing flow posts Slack thread replies to /workflow2. This module maps
the Slack thread back to its Jira ticket, loads live ticket data and stored test
cases, asks Claude whether the message is about the ticket, the test cases, or a
test-case edit, then optionally syncs edited test cases back to Jira and
Postgres.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from app.config import Settings
from app.exceptions import LLMConfigurationError

log = logging.getLogger(__name__)

TC_COMMENT_MARKER = "AI-GOVERNOR-TESTCASES-V1"

ROUTE_TOOL = {
    "name": "respond_to_user",
    "description": (
        "Classify the user's Slack thread message and respond. The thread is "
        "attached to a Jira ticket. Decide which kind of help they need: "
        "questions about the ticket (status, assignee, priority, summary, "
        "similar tickets) vs questions about the test cases vs requests to "
        "edit the test cases. Use the ticket and test-case context provided. "
        "For an edit, return the COMPLETE new test-case list, preserving every "
        "case the user didn't explicitly ask to change."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["ticket_question", "testcase_question", "testcase_edit"],
                "description": "Which kind of message this is.",
            },
            "reply": {
                "type": "string",
                "description": "Short Slack-friendly answer (or edit confirmation).",
            },
            "updated_test_cases": {
                "type": "array",
                "description": "Required ONLY when intent=testcase_edit. Full new test-case list.",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "steps": {"type": "array", "items": {"type": "string"}},
                        "expected": {"type": "string"},
                    },
                    "required": ["title", "steps", "expected"],
                },
            },
        },
        "required": ["intent", "reply"],
    },
}

SYSTEM_PROMPT = (
    "You are the AI Governor assistant inside a Slack thread attached to a Jira "
    "ticket. You receive the ticket details, the QA test cases, and recent "
    "thread history. Always call the respond_to_user tool. Classify the user's "
    "message as ticket_question (about the ticket itself), testcase_question "
    "(about the QA cases), or testcase_edit (modify the QA cases). For edits, "
    "return the COMPLETE new test-case list. Keep replies concise and friendly "
    "for Slack. If a question is ambiguous, lean toward the more specific topic "
    "the user named; only ask for clarification when truly unclear."
)


class TestCaseChatWorkflow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is required for /workflow2")

        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("Install psycopg[binary] to use /workflow2") from exc

        self._psycopg = psycopg
        self._dict_row = dict_row

    def handle(
        self,
        *,
        slack_channel_id: str,
        slack_thread_ts: str,
        user_message: str,
    ) -> str:
        started_at = time.perf_counter()

        def finish(reply: str, outcome: str, extra: dict[str, Any] | None = None) -> str:
            output = {
                "outcome": outcome,
                "reply_chars": len(reply),
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            }
            if extra:
                output.update(extra)
            self._log_step("workflow2", "completed", output=output)
            return reply

        self._log_step(
            "api_request",
            "received",
            output={
                "slack_channel_id": slack_channel_id,
                "slack_thread_ts": slack_thread_ts,
                "user_message_chars": len(user_message),
                "user_message_preview": self._preview(user_message),
            },
        )

        self._log_step(
            "1_resolve_ticket",
            "started",
            input_data={"slack_channel_id": slack_channel_id, "slack_thread_ts": slack_thread_ts},
        )
        ticket_row = self.resolve_ticket_from_thread(slack_channel_id, slack_thread_ts)
        if not ticket_row:
            self._log_step(
                "1_resolve_ticket",
                "completed",
                output={"ticket_found": False},
            )
            return finish(
                "I couldn't link this thread to a Jira ticket, so I can't help here.",
                "ticket_not_found",
            )

        ticket_id = str(ticket_row["jira_ticket_id"])
        self._log_step(
            "1_resolve_ticket",
            "completed",
            output={
                "ticket_found": True,
                "ticket_db_id": ticket_row.get("id"),
                "jira_ticket_id": ticket_id,
                "ticket_status": ticket_row.get("status") or "",
                "source": ticket_row.get("_source") or "unknown",
            },
        )

        self._log_step(
            "2_fetch_ticket_context",
            "started",
            input_data={"jira_ticket_id": ticket_id, "jira_configured": self._jira_configured()},
        )
        ticket_live = self.fetch_jira_ticket(ticket_id)
        ticket_context = ticket_live or self._ticket_context_from_row(ticket_row)
        self._log_step(
            "2_fetch_ticket_context",
            "completed",
            output={
                "jira_ticket_id": ticket_id,
                "source": "jira_live" if ticket_live else "db_fallback",
                "summary_chars": len(str(ticket_context.get("summary") or "")),
                "description_chars": len(str(ticket_context.get("description") or "")),
                "status": ticket_context.get("status") or "",
                "priority": ticket_context.get("priority") or "",
                "assignee_present": bool(ticket_context.get("assignee")),
                "labels_count": len(ticket_context.get("labels") or []),
            },
        )

        self._log_step("3_load_test_cases", "started", input_data={"jira_ticket_id": ticket_id})
        test_cases = self.load_test_cases(ticket_id)
        self._log_step(
            "3_load_test_cases",
            "completed",
            output={
                "jira_ticket_id": ticket_id,
                "test_cases_count": len(test_cases),
                "tc_indexes": [tc.get("tc_index") for tc in test_cases[:20]],
            },
        )

        self._log_step(
            "4_load_recent_messages",
            "started",
            input_data={"ticket_db_id": ticket_row.get("id"), "limit": 6},
        )
        history = self.load_recent_messages(ticket_row.get("id"))
        self._log_step(
            "4_load_recent_messages",
            "completed",
            output={
                "ticket_db_id": ticket_row.get("id"),
                "messages_count": len(history),
                "senders": [row.get("sender") for row in history],
            },
        )

        try:
            self._log_step(
                "5_route_with_claude",
                "started",
                input_data={
                    "jira_ticket_id": ticket_id,
                    "model": self.settings.testcase_chat_model,
                    "test_cases_count": len(test_cases),
                    "history_count": len(history),
                    "user_message_chars": len(user_message),
                },
            )
            result = self.reason(user_message, ticket_context, test_cases, history)
        except Exception:
            log.exception("Test-case chat reasoning failed for %s", ticket_id)
            self._log_step(
                "5_route_with_claude",
                "failed",
                input_data={"jira_ticket_id": ticket_id, "model": self.settings.testcase_chat_model},
            )
            return finish(
                "Something went wrong while thinking about that. Try again in a moment.",
                "reasoning_failed",
                {"jira_ticket_id": ticket_id},
            )

        intent = result.get("intent") or "ticket_question"
        base_reply = result.get("reply") or ""
        updated_test_cases = result.get("updated_test_cases")
        self._log_step(
            "5_route_with_claude",
            "completed",
            output={
                "jira_ticket_id": ticket_id,
                "intent": intent,
                "reply_chars": len(base_reply),
                "has_updated_test_cases": isinstance(updated_test_cases, list),
                "updated_test_cases_count": len(updated_test_cases) if isinstance(updated_test_cases, list) else 0,
            },
        )

        if intent == "testcase_edit" and isinstance(result.get("updated_test_cases"), list):
            self._log_step(
                "6_normalize_edit",
                "started",
                input_data={"jira_ticket_id": ticket_id, "incoming_test_cases_count": len(result["updated_test_cases"])},
            )
            new_tcs = self._normalize_test_cases(result["updated_test_cases"])
            self._log_step(
                "6_normalize_edit",
                "completed",
                output={"jira_ticket_id": ticket_id, "normalized_test_cases_count": len(new_tcs)},
            )
            if not test_cases:
                reply = (
                    base_reply
                    + f"\n\nWarning: I don't see any existing test cases stored for {ticket_id}, "
                    "so I can't apply this edit. Please regenerate them first."
                ).strip()
                self._log_step(
                    "7_apply_edit",
                    "blocked",
                    output={"jira_ticket_id": ticket_id, "reason": "no_existing_test_cases"},
                )
                self.record_exchange(ticket_row.get("id"), user_message, reply)
                return finish(
                    reply,
                    "edit_blocked_no_existing_test_cases",
                    {"jira_ticket_id": ticket_id, "intent": intent},
                )

            self._log_step(
                "7_update_jira_comment",
                "started",
                input_data={"jira_ticket_id": ticket_id, "test_cases_count": len(new_tcs)},
            )
            jira_ok = self.update_jira_comment(ticket_id, new_tcs)
            self._log_step(
                "7_update_jira_comment",
                "completed",
                output={"jira_ticket_id": ticket_id, "jira_ok": jira_ok, "test_cases_count": len(new_tcs)},
            )
            self._log_step(
                "8_sync_database",
                "started",
                input_data={"jira_ticket_id": ticket_id, "test_cases_count": len(new_tcs)},
            )
            db_ok = self._sync_database(ticket_id, new_tcs)
            self._log_step(
                "8_sync_database",
                "completed",
                output={"jira_ticket_id": ticket_id, "db_ok": db_ok, "test_cases_count": len(new_tcs)},
            )
            confirm = base_reply or "Updated the test cases."

            if jira_ok and db_ok:
                reply = (
                    f"{confirm}\n\n"
                    f"_Updated {ticket_id}'s test cases ({len(new_tcs)} total) and synced the database._"
                )
            elif jira_ok and not db_ok:
                reply = (
                    f"{confirm}\n\n"
                    "Warning: Jira comment updated, but the DB sync failed. Please check logs."
                )
            elif db_ok and not jira_ok:
                reply = (
                    f"{confirm}\n\n"
                    "Warning: DB saved, but the Jira comment update failed. Please check the ticket."
                )
            else:
                reply = "Warning: Tried to apply that edit but both Jira and DB updates failed. Please check the logs."

            self.record_exchange(ticket_row.get("id"), user_message, reply)
            return finish(
                reply,
                "edit_processed",
                {
                    "jira_ticket_id": ticket_id,
                    "intent": intent,
                    "jira_ok": jira_ok,
                    "db_ok": db_ok,
                    "updated_test_cases_count": len(new_tcs),
                },
            )

        reply = base_reply or "Here's what I found."
        if intent == "testcase_question" and not test_cases:
            reply = f"I don't see any test cases stored for {ticket_id} yet."
        self._log_step(
            "6_answer_question",
            "completed",
            output={
                "jira_ticket_id": ticket_id,
                "intent": intent,
                "reply_chars": len(reply),
                "test_cases_count": len(test_cases),
            },
        )
        self.record_exchange(ticket_row.get("id"), user_message, reply)
        return finish(
            reply,
            "question_answered",
            {"jira_ticket_id": ticket_id, "intent": intent},
        )

    def resolve_ticket_from_thread(self, channel_id: str, thread_ts: str) -> dict[str, Any] | None:
        """Map a Slack thread to the best available ticket row.

        The current n8n closing flow stores the test-case Slack thread directly
        on tickets. Older rows may still live in channelid_table, and the
        existing Jira-AI review flow uses jira_slack_conversations, so those are
        retained as fallbacks.
        """
        with self._connect() as conn:
            if (
                self._table_exists(conn, "tickets")
                and self._column_type(conn, "tickets", "slack_channel_id")
                and self._column_type(conn, "tickets", "slack_thread_ts")
            ):
                row = conn.execute(
                    f"""
                    SELECT {self._ticket_select_columns(conn)}
                    FROM tickets
                    WHERE slack_channel_id = %s AND slack_thread_ts = %s
                    ORDER BY {self._ticket_order_column(conn)} DESC
                    LIMIT 1
                    """,
                    (channel_id, thread_ts),
                ).fetchone()
                if row and row.get("jira_ticket_id"):
                    ticket = self._ticket_row(row)
                    ticket["_source"] = "tickets"
                    return ticket

            if self._table_exists(conn, "channelid_table"):
                channel_order_column = (
                    "created_at" if self._column_type(conn, "channelid_table", "created_at") else "slack_thread_ts"
                )
                row = conn.execute(
                    f"""
                    SELECT jira_payload
                    FROM channelid_table
                    WHERE slack_channel_id = %s AND slack_thread_ts = %s
                    ORDER BY {channel_order_column} DESC
                    LIMIT 1
                    """,
                    (channel_id, thread_ts),
                ).fetchone()
                issue_key = self._issue_key_from_channel_row(row)
                if issue_key:
                    ticket = self._ticket_row_for_issue_key(
                        conn,
                        issue_key,
                        fallback_payload=(row or {}).get("jira_payload"),
                    )
                    ticket["_source"] = "channelid_table"
                    return ticket

            if self._table_exists(conn, "jira_slack_conversations"):
                row = conn.execute(
                    """
                    SELECT jira_issue_key, original_ticket_data, status
                    FROM jira_slack_conversations
                    WHERE slack_channel_id = %s AND slack_thread_ts = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (channel_id, thread_ts),
                ).fetchone()
                if row and row.get("jira_issue_key"):
                    ticket = self._ticket_row_for_issue_key(
                        conn,
                        str(row["jira_issue_key"]),
                        fallback_payload=row.get("original_ticket_data"),
                        fallback_status=row.get("status"),
                    )
                    ticket["_source"] = "jira_slack_conversations"
                    return ticket

        return None

    def load_test_cases(self, jira_ticket_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if not self._table_exists(conn, "test_cases"):
                return []
            rows = conn.execute(
                """
                SELECT tc_index, title, steps, expected, status
                FROM test_cases
                WHERE jira_ticket_id = %s
                ORDER BY tc_index ASC
                """,
                (jira_ticket_id,),
            ).fetchall()

        test_cases: list[dict[str, Any]] = []
        for row in rows:
            steps = self._steps(row.get("steps"))
            test_cases.append(
                {
                    "tc_index": row["tc_index"],
                    "title": row["title"] or f"Test Case {row['tc_index']}",
                    "steps": steps,
                    "expected": row["expected"] or "",
                    "status": row["status"] or "pending",
                }
            )
        return test_cases

    def load_recent_messages(self, ticket_db_id: Any, limit: int = 6) -> list[dict[str, Any]]:
        """Pull recent thread messages so Claude has conversational context."""
        if not ticket_db_id:
            return []
        with self._connect() as conn:
            if not self._table_exists(conn, "messages"):
                return []
            order_column = self._messages_order_column(conn)
            rows = conn.execute(
                f"""
                SELECT sender, message
                FROM messages
                WHERE ticket_id = %s
                ORDER BY {order_column} DESC
                LIMIT %s
                """,
                (ticket_db_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def record_exchange(self, ticket_db_id: Any, user_message: str, bot_reply: str) -> None:
        if not ticket_db_id:
            self._log_step(
                "9_record_exchange",
                "skipped",
                output={"reason": "missing_ticket_db_id"},
            )
            return

        self._log_step(
            "9_record_exchange",
            "started",
            input_data={
                "ticket_db_id": ticket_db_id,
                "user_message_chars": len(user_message),
                "bot_reply_chars": len(bot_reply),
            },
        )
        try:
            user_saved = self.record_message(ticket_db_id, "user", user_message)
            bot_saved = self.record_message(ticket_db_id, "bot", bot_reply)
            self._log_step(
                "9_record_exchange",
                "completed",
                output={
                    "ticket_db_id": ticket_db_id,
                    "user_message_saved": user_saved,
                    "bot_message_saved": bot_saved,
                    "messages_saved": int(user_saved) + int(bot_saved),
                },
            )
        except Exception:
            self._log_step(
                "9_record_exchange",
                "failed",
                input_data={"ticket_db_id": ticket_db_id},
            )
            log.exception("Could not record /workflow2 message exchange for ticket_id=%s", ticket_db_id)

    def record_message(self, ticket_db_id: Any, sender: str, message: str) -> bool:
        if not ticket_db_id:
            return False
        with self._connect() as conn:
            if not self._table_exists(conn, "messages"):
                log.warning("messages table is missing; skipping /workflow2 message persistence")
                return False
            conn.execute(
                "INSERT INTO messages (ticket_id, sender, message) VALUES (%s, %s, %s)",
                (ticket_db_id, sender, message),
            )
        return True

    def upsert_test_cases(self, ticket_id: str, test_cases: list[dict[str, Any]]) -> None:
        with self._connect() as conn:
            with conn.transaction():
                self._ensure_ticket_row(conn, ticket_id)
                steps_expression = self._steps_insert_expression(conn)
                for index, test_case in enumerate(test_cases, start=1):
                    conn.execute(
                        f"""
                        INSERT INTO test_cases (
                            ticket_id,
                            jira_ticket_id,
                            tc_index,
                            subtask_key,
                            title,
                            steps,
                            expected,
                            status
                        )
                        VALUES (
                            (SELECT id FROM tickets WHERE jira_ticket_id = %s LIMIT 1),
                            %s,
                            %s,
                            NULL,
                            %s,
                            {steps_expression},
                            %s,
                            'pending'
                        )
                        ON CONFLICT (jira_ticket_id, tc_index)
                        DO UPDATE SET
                            title = EXCLUDED.title,
                            steps = EXCLUDED.steps,
                            expected = EXCLUDED.expected,
                            updated_at = NOW()
                        """,
                        (
                            ticket_id,
                            ticket_id,
                            index,
                            test_case.get("title") or f"Test Case {index}",
                            json.dumps(test_case.get("steps") or []),
                            test_case.get("expected") or "",
                        ),
                    )
                conn.execute(
                    "DELETE FROM test_cases WHERE jira_ticket_id = %s AND tc_index > %s",
                    (ticket_id, len(test_cases)),
                )

    def update_jira_comment(self, ticket_id: str, test_cases: list[dict[str, Any]]) -> bool:
        if not self._jira_configured():
            self._log_step(
                "7_update_jira_comment",
                "skipped",
                output={"jira_ticket_id": ticket_id, "reason": "jira_not_configured"},
            )
            log.warning("Jira is not configured; skipping test-case comment update for %s", ticket_id)
            return False

        body = render_comment_body(ticket_id, test_cases)
        comment_id = self.find_existing_tc_comment(ticket_id)
        if comment_id:
            method = requests.put
            url = f"{self.settings.jira_base_url}/rest/api/2/issue/{ticket_id}/comment/{comment_id}"
        else:
            method = requests.post
            url = f"{self.settings.jira_base_url}/rest/api/2/issue/{ticket_id}/comment"

        action = "update" if comment_id else "create"
        self._log_step(
            "7_jira_comment_request",
            "started",
            input_data={
                "jira_ticket_id": ticket_id,
                "action": action,
                "comment_found": bool(comment_id),
                "comment_id": comment_id,
                "body_chars": len(body),
                "test_cases_count": len(test_cases),
            },
        )
        try:
            response = method(
                url,
                auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json={"body": body},
                timeout=self.settings.external_request_timeout_seconds,
            )
            if response.status_code >= 400:
                self._log_step(
                    "7_jira_comment_request",
                    "failed",
                    output={
                        "jira_ticket_id": ticket_id,
                        "action": action,
                        "status_code": response.status_code,
                        "response_preview": self._preview(response.text, limit=300),
                    },
                )
                log.warning("Jira test-case comment update failed for %s: %s", ticket_id, response.text[:500])
                return False
            self._log_step(
                "7_jira_comment_request",
                "completed",
                output={
                    "jira_ticket_id": ticket_id,
                    "action": action,
                    "status_code": response.status_code,
                    "comment_id": comment_id,
                },
            )
            return True
        except requests.RequestException:
            self._log_step(
                "7_jira_comment_request",
                "failed",
                input_data={"jira_ticket_id": ticket_id, "action": action},
            )
            log.exception("Jira test-case comment update failed for %s", ticket_id)
            return False

    def find_existing_tc_comment(self, ticket_id: str) -> str | None:
        self._log_step(
            "7_fetch_jira_comments",
            "started",
            input_data={"jira_ticket_id": ticket_id, "marker": TC_COMMENT_MARKER},
        )
        try:
            response = requests.get(
                f"{self.settings.jira_base_url}/rest/api/2/issue/{ticket_id}/comment?maxResults=100",
                auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
                headers={"Accept": "application/json"},
                timeout=self.settings.external_request_timeout_seconds,
            )
            if response.status_code >= 400:
                self._log_step(
                    "7_fetch_jira_comments",
                    "failed",
                    output={
                        "jira_ticket_id": ticket_id,
                        "status_code": response.status_code,
                        "response_preview": self._preview(response.text, limit=300),
                    },
                )
                log.warning("Could not fetch Jira comments for %s: %s", ticket_id, response.text[:500])
                return None
        except requests.RequestException:
            self._log_step(
                "7_fetch_jira_comments",
                "failed",
                input_data={"jira_ticket_id": ticket_id},
            )
            log.exception("Could not fetch Jira comments for %s", ticket_id)
            return None

        comments = response.json().get("comments", [])
        for comment in comments:
            body = comment.get("body") or ""
            if TC_COMMENT_MARKER in self._comment_text(body):
                self._log_step(
                    "7_fetch_jira_comments",
                    "completed",
                    output={
                        "jira_ticket_id": ticket_id,
                        "status_code": response.status_code,
                        "comments_count": len(comments),
                        "comment_found": True,
                        "comment_id": str(comment["id"]),
                    },
                )
                return str(comment["id"])
        self._log_step(
            "7_fetch_jira_comments",
            "completed",
            output={
                "jira_ticket_id": ticket_id,
                "status_code": response.status_code,
                "comments_count": len(comments),
                "comment_found": False,
            },
        )
        return None

    def fetch_jira_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        """Live-fetch the ticket from Jira so ticket questions use current data."""
        if not self._jira_configured():
            self._log_step(
                "2_jira_ticket_request",
                "skipped",
                output={"jira_ticket_id": ticket_id, "reason": "jira_not_configured"},
            )
            return None

        self._log_step(
            "2_jira_ticket_request",
            "started",
            input_data={"jira_ticket_id": ticket_id},
        )
        try:
            response = requests.get(
                f"{self.settings.jira_base_url}/rest/api/3/issue/{ticket_id}",
                params={"fields": "summary,status,priority,assignee,reporter,duedate,description,labels"},
                auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
                headers={"Accept": "application/json"},
                timeout=self.settings.external_request_timeout_seconds,
            )
            if response.status_code >= 400:
                self._log_step(
                    "2_jira_ticket_request",
                    "failed",
                    output={
                        "jira_ticket_id": ticket_id,
                        "status_code": response.status_code,
                        "response_preview": self._preview(response.text, limit=300),
                    },
                )
                log.warning("Could not fetch Jira ticket %s: %s", ticket_id, response.text[:500])
                return None
        except requests.RequestException:
            self._log_step(
                "2_jira_ticket_request",
                "failed",
                input_data={"jira_ticket_id": ticket_id},
            )
            log.exception("Could not fetch Jira ticket %s", ticket_id)
            return None

        fields = (response.json() or {}).get("fields", {})
        self._log_step(
            "2_jira_ticket_request",
            "completed",
            output={
                "jira_ticket_id": ticket_id,
                "status_code": response.status_code,
                "fields_count": len(fields),
            },
        )
        return {
            "issueKey": ticket_id,
            "summary": fields.get("summary") or "",
            "status": ((fields.get("status") or {}).get("name") or ""),
            "priority": ((fields.get("priority") or {}).get("name") or ""),
            "assignee": ((fields.get("assignee") or {}).get("displayName") or ""),
            "reporter": ((fields.get("reporter") or {}).get("displayName") or ""),
            "dueDate": fields.get("duedate") or "",
            "labels": fields.get("labels") or [],
            "description": self._jira_description_text(fields.get("description")),
            "url": f"{self.settings.jira_base_url}/browse/{ticket_id}",
        }

    def reason(
        self,
        user_message: str,
        ticket: dict[str, Any],
        test_cases: list[dict[str, Any]],
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if self.settings.llm_provider.lower().strip() == "mock":
            return {
                "intent": "ticket_question",
                "reply": "Mock mode is enabled, so I would answer the thread without changing test cases.",
            }

        if not self.settings.anthropic_api_key:
            raise LLMConfigurationError("ANTHROPIC_API_KEY is required for /workflow2")

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise LLMConfigurationError("The 'anthropic' package is required for /workflow2") from exc

        tc_context = json.dumps(
            [
                {
                    "tc_index": tc.get("tc_index"),
                    "title": tc.get("title"),
                    "steps": tc.get("steps") or [],
                    "expected": tc.get("expected") or "",
                }
                for tc in test_cases
            ],
            indent=2,
            ensure_ascii=False,
        )
        ticket_context = {key: value for key, value in ticket.items() if key != "description"}
        if ticket.get("description"):
            ticket_context["description"] = str(ticket["description"])[:4000]
        ticket_blob = json.dumps(ticket_context, indent=2, ensure_ascii=False)
        history_blob = "\n".join(
            f"  {row.get('sender')}: {str(row.get('message') or '')[:300]}" for row in history
        ) or "  (no prior messages)"
        user_block = (
            f"Ticket details:\n{ticket_blob}\n\n"
            f"Test cases ({len(test_cases)}):\n{tc_context}\n\n"
            f"Recent thread history (oldest first):\n{history_blob}\n\n"
            f"User message:\n{user_message}"
        )
        self._log_step(
            "5_build_claude_context",
            "completed",
            output={
                "jira_ticket_id": ticket.get("issueKey") or "",
                "ticket_context_chars": len(ticket_blob),
                "test_case_context_chars": len(tc_context),
                "history_context_chars": len(history_blob),
                "user_block_chars": len(user_block),
                "has_description": bool(ticket.get("description")),
            },
        )
        client = Anthropic(
            api_key=self.settings.anthropic_api_key,
            timeout=self.settings.llm_timeout_seconds,
        )
        message = client.messages.create(
            model=self.settings.testcase_chat_model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=[ROUTE_TOOL],
            tool_choice={"type": "tool", "name": "respond_to_user"},
            messages=[{"role": "user", "content": user_block}],
            temperature=0.1,
        )
        for block in message.content:
            if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "respond_to_user":
                return dict(block.input)
        return {"intent": "ticket_question", "reply": "Sorry, I couldn't process that."}

    def _log_step(
        self,
        step: str,
        status: str,
        *,
        input_data: Any | None = None,
        output: Any | None = None,
    ) -> None:
        payload = {
            "step": step,
            "status": status,
            "input": input_data,
            "output": output,
        }
        log.info("workflow2 structured log: %s", json.dumps(payload, ensure_ascii=False, default=str))

    def _preview(self, value: Any, limit: int = 160) -> str:
        text = " ".join(str(value or "").split())
        if len(text) <= limit:
            return text
        return f"{text[:limit]}..."

    def _sync_database(self, ticket_id: str, test_cases: list[dict[str, Any]]) -> bool:
        try:
            self.upsert_test_cases(ticket_id, test_cases)
            return True
        except Exception:
            log.exception("Postgres test-case sync failed for %s", ticket_id)
            return False

    def _connect(self):
        return self._psycopg.connect(self.settings.database_url, row_factory=self._dict_row)

    def _table_exists(self, conn: Any, table_name: str) -> bool:
        row = conn.execute("SELECT to_regclass(%s) AS table_name", (f"public.{table_name}",)).fetchone()
        return bool(row and row.get("table_name"))

    def _column_type(self, conn: Any, table_name: str, column_name: str) -> str:
        row = conn.execute(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
            LIMIT 1
            """,
            (table_name, column_name),
        ).fetchone()
        return str(row["data_type"]) if row and row.get("data_type") else ""

    def _ticket_select_columns(self, conn: Any) -> str:
        columns = [
            column
            for column in ("id", "jira_ticket_id", "status", "slack_channel_id", "slack_thread_ts", "jira_payload")
            if self._column_type(conn, "tickets", column)
        ]
        return ", ".join(columns or ["id", "jira_ticket_id"])

    def _ticket_order_column(self, conn: Any) -> str:
        for column in ("id", "created_at", "jira_ticket_id"):
            if self._column_type(conn, "tickets", column):
                return column
        return "jira_ticket_id"

    def _ticket_row(
        self,
        row: dict[str, Any],
        *,
        fallback_payload: Any | None = None,
        fallback_status: Any | None = None,
    ) -> dict[str, Any]:
        ticket = dict(row)
        ticket.setdefault("id", None)
        ticket.setdefault("status", fallback_status or "")
        ticket.setdefault("jira_payload", fallback_payload)
        if fallback_payload is not None and not ticket.get("jira_payload"):
            ticket["jira_payload"] = fallback_payload
        if fallback_status is not None and not ticket.get("status"):
            ticket["status"] = fallback_status
        return ticket

    def _ticket_row_for_issue_key(
        self,
        conn: Any,
        issue_key: str,
        *,
        fallback_payload: Any | None = None,
        fallback_status: Any | None = None,
    ) -> dict[str, Any]:
        if not self._table_exists(conn, "tickets") or not self._column_type(conn, "tickets", "jira_ticket_id"):
            return {
                "id": None,
                "jira_ticket_id": issue_key,
                "status": fallback_status or "",
                "jira_payload": fallback_payload,
            }

        row = conn.execute(
            f"""
            SELECT {self._ticket_select_columns(conn)}
            FROM tickets
            WHERE jira_ticket_id = %s
            ORDER BY {self._ticket_order_column(conn)} DESC
            LIMIT 1
            """,
            (issue_key,),
        ).fetchone()
        if row:
            return self._ticket_row(row, fallback_payload=fallback_payload, fallback_status=fallback_status)

        ticket_db_id = None
        try:
            ticket_db_id = self._ensure_ticket_row(conn, issue_key)
        except Exception:
            log.exception("Could not create fallback ticket row for %s", issue_key)

        return {
            "id": ticket_db_id,
            "jira_ticket_id": issue_key,
            "status": fallback_status or "",
            "jira_payload": fallback_payload,
        }

    def _messages_order_column(self, conn: Any) -> str:
        for column in ("created_at", "sent_at", "id"):
            if self._column_type(conn, "messages", column):
                return column
        return "ticket_id"

    def _steps_insert_expression(self, conn: Any) -> str:
        column_type = self._column_type(conn, "test_cases", "steps")
        if column_type == "jsonb":
            return "%s::jsonb"
        if column_type == "json":
            return "%s::json"
        return "%s"

    def _ensure_ticket_row(self, conn: Any, ticket_id: str) -> Any:
        if not self._table_exists(conn, "tickets"):
            raise RuntimeError("tickets table is missing")
        row = conn.execute(
            """
            INSERT INTO tickets (jira_ticket_id)
            VALUES (%s)
            ON CONFLICT (jira_ticket_id)
            DO UPDATE SET jira_ticket_id = EXCLUDED.jira_ticket_id
            RETURNING id
            """,
            (ticket_id,),
        ).fetchone()
        return row.get("id") if row else None

    def _issue_key_from_channel_row(self, row: dict[str, Any] | None) -> str | None:
        if not row:
            return None
        for key in ("issue_key", "key"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        payload = row.get("jira_payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        if isinstance(payload, dict):
            for key in ("issueKey", "key", "issue_key", "jira_issue_key"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def _jira_configured(self) -> bool:
        return bool(self.settings.jira_base_url and self.settings.jira_email and self.settings.jira_api_token)

    def _ticket_context_from_row(self, ticket_row: dict[str, Any]) -> dict[str, Any]:
        payload = self._json_object(ticket_row.get("jira_payload"))
        fields = self._json_object(payload.get("fields")) if payload else {}

        status = payload.get("status") or fields.get("status") or ticket_row.get("status") or ""
        priority = payload.get("priority") or fields.get("priority") or ""
        assignee = payload.get("assignee") or fields.get("assignee") or ""
        reporter = payload.get("reporter") or fields.get("reporter") or ""
        description = (
            payload.get("description")
            or fields.get("description")
            or payload.get("descriptionText")
            or payload.get("body")
            or ""
        )

        ticket_id = str(
            ticket_row.get("jira_ticket_id")
            or payload.get("issueKey")
            or payload.get("key")
            or payload.get("jira_issue_key")
            or ""
        )
        return {
            "issueKey": ticket_id,
            "summary": payload.get("summary") or fields.get("summary") or "",
            "status": self._named_value(status),
            "priority": self._named_value(priority),
            "assignee": self._named_value(assignee),
            "reporter": self._named_value(reporter),
            "dueDate": payload.get("dueDate") or payload.get("duedate") or fields.get("duedate") or "",
            "labels": payload.get("labels") or fields.get("labels") or [],
            "description": self._jira_description_text(description),
            "url": f"{self.settings.jira_base_url}/browse/{ticket_id}" if self.settings.jira_base_url else "",
        }

    def _json_object(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _named_value(self, value: Any) -> str:
        if isinstance(value, dict):
            for key in ("displayName", "name", "value", "key"):
                item = value.get(key)
                if isinstance(item, str) and item.strip():
                    return item.strip()
            return ""
        return str(value or "")

    def _jira_description_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value

        parts: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                text = node.get("text")
                if isinstance(text, str):
                    parts.append(text)
                for child in node.get("content") or []:
                    walk(child)
            elif isinstance(node, list):
                for child in node:
                    walk(child)

        walk(value)
        if parts:
            return " ".join(part.strip() for part in parts if part.strip())
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)

    def _steps(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return [value]
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
            return [str(parsed)]
        return [str(value)]

    def _normalize_test_cases(self, test_cases: Any) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        if not isinstance(test_cases, list):
            return normalized
        for index, item in enumerate(test_cases, start=1):
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "title": str(item.get("title") or f"Test Case {index}"),
                    "steps": self._steps(item.get("steps")),
                    "expected": str(item.get("expected") or ""),
                }
            )
        return normalized

    def _comment_text(self, body: Any) -> str:
        if isinstance(body, str):
            return body
        if isinstance(body, dict):
            return json.dumps(body, ensure_ascii=False)
        return str(body)


def render_comment_body(ticket_id: str, test_cases: list[dict[str, Any]]) -> str:
    """Render Jira wiki markup compatible with the existing n8n comment shape."""
    blocks = []
    for index, test_case in enumerate(test_cases, start=1):
        title = test_case.get("title") or f"Test Case {index}"
        block = f"*[TC {index}] {title}*"
        steps = test_case.get("steps") or []
        if steps:
            numbered = "\n".join(f"  {step_index + 1}. {step}" for step_index, step in enumerate(steps))
            block += f"\n_Steps:_\n{numbered}"
        expected = test_case.get("expected")
        if expected:
            block += f"\n_Expected:_ {expected}"
        blocks.append(block)

    body = "\n\n----\n\n".join(blocks)
    return (
        f"h3. Auto-generated Test Cases ({len(test_cases)})\n"
        f"_Generated by AI Governor RepoTree for {ticket_id}._\n"
        f"{{anchor:{TC_COMMENT_MARKER}}}\n\n"
        f"{body}"
    )

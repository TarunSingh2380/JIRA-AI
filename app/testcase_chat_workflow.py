"""Slack Q&A and edit handling for Jira test cases.

The n8n closing flow posts Slack thread replies to /workflow2. This module maps
the Slack thread back to its Jira ticket, loads the stored test cases, asks
Claude whether the message is a question or an edit request, then optionally
syncs the edited test cases back to Jira and Postgres.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from app.config import Settings
from app.exceptions import LLMConfigurationError

log = logging.getLogger(__name__)

TC_COMMENT_MARKER = "AI-GOVERNOR-TESTCASES-V1"

CLASSIFY_TOOL = {
    "name": "respond_to_user",
    "description": (
        "Respond to a user's message about a ticket's QA test cases. Decide "
        "whether they are asking a QUESTION (just answer) or requesting an EDIT "
        "(modify the test cases). For an edit, return the COMPLETE new set of "
        "test cases reflecting their request - additions, deletions, and changes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["question", "edit"],
                "description": "question = answer only; edit = test cases must change.",
            },
            "reply": {
                "type": "string",
                "description": "Short Slack-friendly reply to send the user.",
            },
            "updated_test_cases": {
                "type": "array",
                "description": "Only for intent=edit. The full new set of test cases.",
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
    "You are the AI Governor QA assistant inside a Slack thread. The thread is "
    "attached to a Jira ticket and a set of auto-generated QA test cases. Users "
    "ask questions about the test cases or request improvements. Always call the "
    "respond_to_user tool. For an edit, return the COMPLETE updated test-case "
    "list, not just the delta, preserving cases the user did not ask to change. "
    "Keep replies concise and friendly for Slack."
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
        ticket_id = self.resolve_ticket_from_thread(slack_channel_id, slack_thread_ts)
        if not ticket_id:
            return "I couldn't link this thread to a Jira ticket, so I can't help with its test cases here."

        test_cases = self.load_test_cases(ticket_id)
        if not test_cases:
            return f"I don't see any test cases stored for {ticket_id} yet."

        try:
            result = self.reason(user_message, ticket_id, test_cases)
        except Exception:
            log.exception("Test-case chat reasoning failed for %s", ticket_id)
            return "Something went wrong while thinking about that. Try again in a moment."

        if result.get("intent") == "edit" and isinstance(result.get("updated_test_cases"), list):
            new_tcs = self._normalize_test_cases(result["updated_test_cases"])
            jira_ok = self.update_jira_comment(ticket_id, new_tcs)
            db_ok = self._sync_database(ticket_id, new_tcs)
            confirm = result.get("reply") or "Updated the test cases."

            if jira_ok and db_ok:
                return (
                    f"{confirm}\n\n"
                    f"_Updated the test cases on {ticket_id} ({len(new_tcs)} total) and synced the database._"
                )
            if jira_ok and not db_ok:
                return (
                    f"{confirm}\n\n"
                    "Warning: Updated the Jira comment, but the database sync failed. "
                    "Please re-run or check logs."
                )
            if db_ok and not jira_ok:
                return (
                    f"{confirm}\n\n"
                    "Warning: Saved to the database, but updating the Jira comment failed. "
                    "Please check the ticket."
                )
            return "Warning: I tried to apply that edit but both the Jira and database updates failed. Please check the logs."

        return result.get("reply") or "Here's what I found."

    def resolve_ticket_from_thread(self, channel_id: str, thread_ts: str) -> str | None:
        """Map a Slack thread to a Jira issue key.

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
                    """
                    SELECT jira_ticket_id
                    FROM tickets
                    WHERE slack_channel_id = %s AND slack_thread_ts = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (channel_id, thread_ts),
                ).fetchone()
                if row and row.get("jira_ticket_id"):
                    return str(row["jira_ticket_id"])

            if self._table_exists(conn, "channelid_table"):
                row = conn.execute(
                    """
                    SELECT jira_payload
                    FROM channelid_table
                    WHERE slack_channel_id = %s AND slack_thread_ts = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (channel_id, thread_ts),
                ).fetchone()
                issue_key = self._issue_key_from_channel_row(row)
                if issue_key:
                    return issue_key

            if self._table_exists(conn, "jira_slack_conversations"):
                row = conn.execute(
                    """
                    SELECT jira_issue_key
                    FROM jira_slack_conversations
                    WHERE slack_channel_id = %s AND slack_thread_ts = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (channel_id, thread_ts),
                ).fetchone()
                if row and row.get("jira_issue_key"):
                    return str(row["jira_issue_key"])

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

        try:
            response = method(
                url,
                auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json={"body": body},
                timeout=self.settings.external_request_timeout_seconds,
            )
            if response.status_code >= 400:
                log.warning("Jira test-case comment update failed for %s: %s", ticket_id, response.text[:500])
                return False
            return True
        except requests.RequestException:
            log.exception("Jira test-case comment update failed for %s", ticket_id)
            return False

    def find_existing_tc_comment(self, ticket_id: str) -> str | None:
        try:
            response = requests.get(
                f"{self.settings.jira_base_url}/rest/api/2/issue/{ticket_id}/comment?maxResults=100",
                auth=HTTPBasicAuth(self.settings.jira_email, self.settings.jira_api_token),
                headers={"Accept": "application/json"},
                timeout=self.settings.external_request_timeout_seconds,
            )
            if response.status_code >= 400:
                log.warning("Could not fetch Jira comments for %s: %s", ticket_id, response.text[:500])
                return None
        except requests.RequestException:
            log.exception("Could not fetch Jira comments for %s", ticket_id)
            return None

        for comment in response.json().get("comments", []):
            body = comment.get("body") or ""
            if TC_COMMENT_MARKER in self._comment_text(body):
                return str(comment["id"])
        return None

    def reason(self, user_message: str, ticket_id: str, test_cases: list[dict[str, Any]]) -> dict[str, Any]:
        if self.settings.llm_provider.lower().strip() == "mock":
            return {"intent": "question", "reply": "Mock mode is enabled, so I would answer without changing test cases."}

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
        user_block = (
            f"Ticket: {ticket_id}\n\n"
            f"Current test cases:\n{tc_context}\n\n"
            f"User message:\n{user_message}"
        )
        client = Anthropic(
            api_key=self.settings.anthropic_api_key,
            timeout=self.settings.llm_timeout_seconds,
        )
        message = client.messages.create(
            model=self.settings.testcase_chat_model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=[CLASSIFY_TOOL],
            tool_choice={"type": "tool", "name": "respond_to_user"},
            messages=[{"role": "user", "content": user_block}],
            temperature=0.1,
        )
        for block in message.content:
            if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "respond_to_user":
                return dict(block.input)
        return {"intent": "question", "reply": "Sorry, I couldn't process that."}

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

    def _steps_insert_expression(self, conn: Any) -> str:
        column_type = self._column_type(conn, "test_cases", "steps")
        if column_type == "jsonb":
            return "%s::jsonb"
        if column_type == "json":
            return "%s::json"
        return "%s"

    def _ensure_ticket_row(self, conn: Any, ticket_id: str) -> None:
        if not self._table_exists(conn, "tickets"):
            raise RuntimeError("tickets table is missing")
        conn.execute(
            """
            INSERT INTO tickets (jira_ticket_id)
            VALUES (%s)
            ON CONFLICT (jira_ticket_id) DO NOTHING
            """,
            (ticket_id,),
        )

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

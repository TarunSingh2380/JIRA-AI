"""Unit tests for app.rca.intake — extraction normalization + LLM injection."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.rca import intake
from app.rca.intake import TicketIntake
from tests.rca_helpers import make_settings


def _ticket(**over) -> TicketIntake:
    base = dict(
        key="RFT-1", summary="500 on /api/pay", description="NullPointer in charge()",
        status="Open", issue_type="Bug", priority="High", components=["payments"],
        labels=[], affected_versions=["1.2.0"], fix_versions=[], environment="prod",
        comments=["stacktrace: PaymentService.charge line 42"], attachments=[],
        linked_issues=[], raw={},
    )
    base.update(over)
    return TicketIntake(**base)


class FakeLLM:
    def __init__(self, payload):
        self._payload = payload
        self.calls = 0

    def complete(self, system, user, *, max_tokens=4096):
        self.calls += 1
        self.last_user = user
        return self._payload


class NormalizationTests(unittest.TestCase):
    def test_as_str_list(self):
        self.assertEqual(intake._as_str_list(["a", " b ", "", 3]), ["a", "b", "3"])
        self.assertEqual(intake._as_str_list("solo"), ["solo"])
        self.assertEqual(intake._as_str_list(None), [])

    def test_normalize_frames_mixed(self):
        frames = intake._normalize_frames([
            {"file": "svc/pay.py", "line": "42", "symbol": "charge", "raw": "at charge"},
            "raw frame string",
            {"file": None, "line": None, "symbol": None, "raw": ""},
        ])
        self.assertEqual(frames[0]["line"], 42)
        self.assertEqual(frames[0]["file"], "svc/pay.py")
        self.assertEqual(frames[1]["raw"], "raw frame string")
        self.assertIsNone(frames[1]["file"])


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.settings = make_settings(Path("/tmp"))

    def test_extract_signals_happy_path(self):
        payload = json.dumps({
            "error_messages": ["NullPointerException", ""],
            "stack_frames": [{"file": "svc/pay.py", "line": 42, "symbol": "charge", "raw": "x"}],
            "mentioned_endpoints": ["/api/pay"],
            "repro_steps": ["call /api/pay"],
            "suspected_area": "payments",
        })
        llm = FakeLLM(payload)
        out = intake.extract_signals(self.settings, _ticket(), llm_client=llm)
        self.assertEqual(llm.calls, 1)
        self.assertEqual(out["error_messages"], ["NullPointerException"])  # blank dropped
        self.assertEqual(out["stack_frames"][0]["line"], 42)
        self.assertEqual(out["suspected_area"], "payments")
        # the ticket content reached the prompt
        self.assertIn("RFT-1", llm.last_user)
        self.assertIn("/api/pay", llm.last_user)

    def test_extract_signals_bad_json_returns_empty_schema(self):
        out = intake.extract_signals(self.settings, _ticket(), llm_client=FakeLLM("not json at all"))
        self.assertEqual(out["error_messages"], [])
        self.assertEqual(out["stack_frames"], [])
        self.assertEqual(out["suspected_area"], "")

    def test_extract_signals_partial_keys(self):
        out = intake.extract_signals(
            self.settings, _ticket(),
            llm_client=FakeLLM(json.dumps({"error_messages": ["boom"]})),
        )
        self.assertEqual(out["error_messages"], ["boom"])
        self.assertEqual(out["mentioned_endpoints"], [])  # filled from schema default

    def test_intake_user_message_includes_sections(self):
        msg = intake._intake_user_message(_ticket(comments=["c1"], linked_issues=[
            {"key": "RFT-2", "relation": "blocks", "summary": "other"}]))
        self.assertIn("COMPONENTS: payments", msg)
        self.assertIn("COMMENTS:", msg)
        self.assertIn("LINKED ISSUES:", msg)
        self.assertIn("RFT-2", msg)


if __name__ == "__main__":
    unittest.main()

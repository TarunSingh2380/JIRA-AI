"""Unit tests for app.rca.rca_document and app.rca.eval scoring."""
from __future__ import annotations

import unittest

from app.rca import eval as rca_eval
from app.rca import rca_document as D
from app.rca.eval import TicketLabel


def _diag(confidence, suggested_fix=None):
    return {
        "root_cause": {"repo": "svc", "file": "a.py", "symbol": "f", "lines": "1-9"},
        "what_happened": "wh", "explanation": "ex", "five_whys": ["w1", "w2"],
        "final_root_cause": "frc", "confidence": confidence,
        "alternative_hypotheses": [], "evidence": [{"type": "t", "detail": "d"}],
        "impact": {"affected": "users", "impact_type": "x", "description": "y"},
        "expectation_vs_reality": {"development": {"expected": "e", "actual": "a", "gap": "g"}},
        "contributing_factors": {"code_issue": "ci", "configuration_issue": "Not applicable"},
        "preventive_actions": ["pa"], "lessons_learned": {"do_differently": "dd"},
        "suggested_fix": suggested_fix,
        "ownership": {"original_developer": "Dev A", "blame_lines": "a.py:1-9", "last_commit_sha": "deadbeef"},
    }


class DocumentTests(unittest.TestCase):
    def test_area_only_resolution_when_no_fix(self):
        doc = D.build_document({"key": "OPS-1", "summary": "s"}, {}, _diag(0.7))
        md = D.render_markdown(doc)
        self.assertIn("## 7. Resolution", md)
        self.assertIn("Diagnosis-only", md)
        self.assertNotIn("```", md)  # no fix code block

    def test_suggested_fix_rendered_with_review_note(self):
        fix = {"description": "pass customerID", "code": "waiverAmt(leadID, customerID)",
               "confidence_basis": "read the call site", "human_review_required": True}
        doc = D.build_document({"key": "OPS-2", "summary": "s"}, {}, _diag(0.97, fix))
        md = D.render_markdown(doc)
        self.assertIn("waiverAmt(leadID, customerID)", md)
        self.assertIn("requires human review", md.lower())

    def test_all_nine_sections_present(self):
        doc = D.build_document({"key": "OPS-3", "summary": "s"}, {}, _diag(0.8))
        md = D.render_markdown(doc)
        for i, name in enumerate([
            "Issue Summary", "Impact Assessment", "Ownership", "Root Cause Analysis",
            "Expectation vs Reality", "Contributing Factors", "Resolution",
            "Preventive Actions", "Lessons Learned"], 1):
            self.assertIn(f"## {i}. {name}", md)
        # "Not applicable" factor is suppressed
        self.assertNotIn("Configuration Issue", md)
        # ownership from blame surfaces
        self.assertIn("Dev A", md)

    def test_render_docx_bytes(self):
        try:
            import docx  # noqa: F401
        except ImportError:
            self.skipTest("python-docx not installed in this environment")
        doc = D.build_document({"key": "OPS-4", "summary": "s"}, {}, _diag(0.8))
        data = D.render_docx(doc)
        self.assertTrue(data.startswith(b"PK"))  # .docx is a zip


class EvalScoringTests(unittest.TestCase):
    def test_score_case_hit_at_k(self):
        label = TicketLabel("OPS-9", "OPS", "s", "d", {"src/pay.py", "src/util.py"})
        case = rca_eval._score_case(label, ["src/other.py", "src/pay.py", "z.py"], [1, 3, 5])
        self.assertFalse(case.hit_at[1])   # rank1 miss
        self.assertTrue(case.hit_at[3])    # rank3 hit (pay.py at index 1)
        self.assertTrue(case.hit_at[5])

    def test_score_case_total_miss(self):
        label = TicketLabel("OPS-9", "OPS", "s", "d", {"src/pay.py"})
        case = rca_eval._score_case(label, ["a.py", "b.py"], [1, 3])
        self.assertFalse(case.hit_at[1])
        self.assertFalse(case.hit_at[3])


if __name__ == "__main__":
    unittest.main()

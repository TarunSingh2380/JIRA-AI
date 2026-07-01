"""Unit tests for app.rca.rca_document and app.rca.eval scoring."""
from __future__ import annotations

import unittest

from app.rca import eval as rca_eval
from app.rca import rca_document as D
from app.rca import synthesis
from app.rca.eval import TicketLabel

_NUMERIC = {"High": 0.95, "Medium": 0.75, "Low": 0.3}


def _diag(confidence_label, recommended_fix=None, *, insufficient=False,
          contributing_factors=None, evidence=None):
    return {
        "insufficient_data": insufficient,
        "issue_classification": "Runtime Bug",
        "confidence_label": confidence_label,
        "confidence": _NUMERIC[confidence_label],
        "facts": ["f1", "f2"],
        "inferences": ["i1"],
        "unknowns": ["u1"],
        "root_cause": (synthesis.INSUFFICIENT_DATA_MESSAGE if insufficient
                       else "Null deref in a.py because f() returns None."),
        "root_cause_location": {"repo": "svc", "file": "a.py", "symbol": "f", "lines": "1-9"},
        "evidence": evidence if evidence is not None else [
            {"type": "code", "detail": "d", "ref": "a.py:5"},
            {"type": "log", "detail": "e", "ref": "log:1"},
        ],
        "contributing_factors": contributing_factors or [],
        "recommended_fix": recommended_fix,
    }


class DocumentTests(unittest.TestCase):
    def test_diagnosis_only_when_no_fix(self):
        doc = D.build_document({"key": "OPS-1", "summary": "s"}, {}, _diag("Medium"))
        md = D.render_markdown(doc)
        self.assertIn("## RECOMMENDED FIX", md)
        self.assertIn(synthesis.NO_FIX_MESSAGE, md)

    def test_fix_rendered_at_high(self):
        doc = D.build_document({"key": "OPS-2", "summary": "s"}, {},
                               _diag("High", "Guard against a None return from f()."))
        md = D.render_markdown(doc)
        self.assertIn("Guard against a None return from f().", md)
        self.assertNotIn(synthesis.NO_FIX_MESSAGE, md)

    def test_output_format_sections(self):
        doc = D.build_document({"key": "OPS-3", "summary": "s"}, {}, _diag("High"))
        md = D.render_markdown(doc)
        self.assertIn("**Issue Classification:** Runtime Bug", md)
        self.assertIn("**Confidence:** High", md)
        for heading in ["## FACTS", "## INFERENCES", "## UNKNOWNS",
                        "## ROOT CAUSE", "## EVIDENCE", "## RECOMMENDED FIX"]:
            self.assertIn(heading, md)
        # No supported contributing factors → section is omitted.
        self.assertNotIn("## CONTRIBUTING FACTORS", md)
        # Evidence ref is surfaced.
        self.assertIn("a.py:5", md)

    def test_contributing_factors_shown_when_present(self):
        doc = D.build_document({"key": "OPS-3b", "summary": "s"}, {},
                               _diag("High", contributing_factors=["No regression test covered f()"]))
        md = D.render_markdown(doc)
        self.assertIn("## CONTRIBUTING FACTORS", md)
        self.assertIn("No regression test covered f()", md)

    def test_insufficient_data_only_states_that(self):
        doc = D.build_document({"key": "OPS-5", "summary": "s"}, {}, _diag("Low", insufficient=True))
        md = D.render_markdown(doc)
        self.assertIn(synthesis.INSUFFICIENT_DATA_MESSAGE, md)
        self.assertNotIn("## FACTS", md)          # no fabricated sections
        self.assertNotIn("## RECOMMENDED FIX", md)

    def test_render_docx_bytes(self):
        try:
            import docx  # noqa: F401
        except ImportError:
            self.skipTest("python-docx not installed in this environment")
        doc = D.build_document({"key": "OPS-4", "summary": "s"}, {}, _diag("Medium"))
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

"""Unit tests for the RCA engine (Phases D–I): retrieval RRF, synthesis gate,
agent loop, tools scope, store lifecycle, document fix-mode."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.rca import agent, retrieval, store, synthesis, tools
from app.rca.retrieval import Candidate
from tests.rca_helpers import init_repo, commit, make_settings


# ── Phase E: RRF fusion ───────────────────────────────────────────────────────

class RRFTests(unittest.TestCase):
    def test_fuse_accumulates_and_tags(self):
        fused = {}
        retrieval._fuse(fused, [Candidate("r", "a.py"), Candidate("r", "b.py")], "grep")
        retrieval._fuse(fused, [Candidate("r", "a.py")], "semantic")
        a = fused[("r", "a.py")]
        # a.py surfaced by two retrievers → higher score, both tags
        self.assertEqual(a.retrievers, {"grep", "semantic"})
        self.assertGreater(a.score, fused[("r", "b.py")].score)

    def test_fuse_enriches_line_info(self):
        fused = {}
        retrieval._fuse(fused, [Candidate("r", "a.py")], "grep")
        retrieval._fuse(fused, [Candidate("r", "a.py", symbol="foo", start_line=10)], "stack")
        self.assertEqual(fused[("r", "a.py")].symbol, "foo")
        self.assertEqual(fused[("r", "a.py")].start_line, 10)


# ── Phase G: synthesis normalization + fix gate ───────────────────────────────

class FakeLLM:
    def __init__(self, payload):
        self.payload = payload
    def complete(self, system, user, *, max_tokens=4096):
        return self.payload


class SynthesisTests(unittest.TestCase):
    def setUp(self):
        self.settings = make_settings(Path("/tmp"))

    def _diag(self, confidence, with_fix, *, evidence_count=2, insufficient=False):
        import json
        d = {
            "insufficient_data": insufficient,
            "issue_classification": "Runtime Bug",
            "confidence": confidence,  # High | Medium | Low
            "facts": ["f1", "f2"],
            "inferences": ["i1"],
            "unknowns": ["u1"],
            "root_cause": "Null deref in a.py because f() returns None on empty input.",
            "root_cause_location": {"repo": "svc", "file": "a.py", "symbol": "f", "lines": "1-9"},
            "evidence": [{"type": "code", "detail": "d", "ref": f"a.py:{i}"}
                         for i in range(evidence_count)],
            "contributing_factors": [],
            "recommended_fix": "Guard against a None return from f()." if with_fix else None,
        }
        return json.dumps(d)

    def test_fix_dropped_below_high(self):
        out = synthesis.synthesize(
            self.settings, ticket={}, extracted={}, candidates=[], investigation="",
            trace=[], llm_client=FakeLLM(self._diag("Medium", with_fix=True)))
        self.assertIsNone(out["recommended_fix"])  # only High gets a fix
        self.assertEqual(out["confidence_label"], "Medium")

    def test_fix_kept_at_high(self):
        out = synthesis.synthesize(
            self.settings, ticket={}, extracted={}, candidates=[], investigation="",
            trace=[], llm_client=FakeLLM(self._diag("High", with_fix=True)))
        self.assertIsNotNone(out["recommended_fix"])
        self.assertEqual(out["confidence_label"], "High")
        self.assertEqual(out["confidence"], 0.95)  # internal numeric for the gate

    def test_single_evidence_forces_undetermined(self):
        # RULE 5: <2 independent evidence items → no asserted root cause.
        out = synthesis.synthesize(
            self.settings, ticket={}, extracted={}, candidates=[], investigation="",
            trace=[], llm_client=FakeLLM(self._diag("High", with_fix=True, evidence_count=1)))
        self.assertEqual(out["root_cause"], "Undetermined.")
        self.assertEqual(out["confidence_label"], "Low")
        self.assertIsNone(out["recommended_fix"])

    def test_insufficient_data_short_circuits(self):
        out = synthesis.synthesize(
            self.settings, ticket={}, extracted={}, candidates=[], investigation="",
            trace=[], llm_client=FakeLLM(self._diag("High", with_fix=True, insufficient=True)))
        self.assertEqual(out["root_cause"], synthesis.INSUFFICIENT_DATA_MESSAGE)
        self.assertEqual(out["confidence_label"], "Low")
        self.assertIsNone(out["recommended_fix"])

    def test_classification_defaults_to_cannot_determine(self):
        import json
        bad = json.dumps({"issue_classification": "banana", "confidence": "High",
                          "root_cause": "x", "evidence": [{"type": "a", "detail": "b"}]})
        out = synthesis.synthesize(
            self.settings, ticket={}, extracted={}, candidates=[], investigation="",
            trace=[], llm_client=FakeLLM(bad))
        self.assertEqual(out["issue_classification"], "Cannot Determine")

    def test_user_message_handles_large_observations(self):
        # Regression: a large tool observation must not break JSON building.
        big = {"matches": [{"text": "x" * 50} for _ in range(200)]}
        trace = [{"tool": "grep_codebase", "input": {"repo": "svc"}, "observation": big}]
        msg = synthesis._user_message({}, {}, [], "found it", trace)
        self.assertIn("found it", msg)
        self.assertIn("truncated", msg)  # large observation safely truncated

    def test_truncate_observation_small_passthrough(self):
        obs = {"count": 1}
        self.assertEqual(synthesis._truncate_observation(obs, 1500), obs)

    def test_bad_json_normalizes_to_undetermined(self):
        out = synthesis.synthesize(
            self.settings, ticket={}, extracted={}, candidates=[], investigation="",
            trace=[], llm_client=FakeLLM("not json"))
        self.assertEqual(out["confidence_label"], "Low")
        self.assertEqual(out["root_cause"], "Undetermined.")
        self.assertEqual(out["issue_classification"], "Cannot Determine")


# ── Phase F: agent loop with fakes ────────────────────────────────────────────

class FakeBlock(SimpleNamespace):
    pass


class FakeResp(SimpleNamespace):
    pass


class ScriptedClient:
    """Returns a tool_use turn, then a final text turn."""
    def __init__(self):
        self.calls = 0
        self.messages = self

    def create(self, **kwargs):
        self.calls += 1
        usage = SimpleNamespace(input_tokens=10, output_tokens=5)
        if self.calls == 1:
            tu = FakeBlock(type="tool_use", id="t1", name="read_file",
                           input={"repo": "svc", "path": "a.py"})
            return FakeResp(content=[tu], stop_reason="tool_use", usage=usage)
        txt = FakeBlock(type="text", text="Root cause is in a.py line 1.")
        return FakeResp(content=[txt], stop_reason="end_turn", usage=usage)


class FakeToolCtx:
    def __init__(self):
        self.dispatched = []
    def dispatch(self, name, args):
        self.dispatched.append((name, args))
        return {"content": "line 1: bug"}


class AgentLoopTests(unittest.TestCase):
    def test_loop_runs_tool_then_summarizes(self):
        settings = make_settings(Path("/tmp"))
        events = []
        res = agent.run_investigation(
            settings, ticket_summary="bug", extracted={}, candidates=[],
            allowed_repos=["svc"], on_event=events.append,
            client=ScriptedClient(), tool_context=FakeToolCtx())
        self.assertIn("a.py", res.summary)
        self.assertEqual(res.stop_reason, "end_turn")
        self.assertEqual(len(res.agent_trace), 1)
        self.assertEqual(res.agent_trace[0]["tool"], "read_file")
        self.assertEqual(len(events), 1)
        self.assertEqual(res.input_tokens, 20)  # two calls × 10


# ── Phase F: tool repo-scope enforcement ──────────────────────────────────────

class ToolScopeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.settings = make_settings(self.root)
        init_repo(self.root, "svc", {"a.py": "SECRET=1\n"})
        commit(self.root / "svc", "init")

    def tearDown(self):
        self._tmp.cleanup()

    def test_out_of_scope_repo_blocked(self):
        ctx = tools.ToolContext(self.settings, allowed_repos=["svc"])
        out = ctx.dispatch("grep_codebase", {"repo": "other", "pattern": "x"})
        self.assertIn("error", out)
        self.assertIn("out of scope", out["error"])

    def test_in_scope_grep_works(self):
        ctx = tools.ToolContext(self.settings, allowed_repos=["svc"])
        out = ctx.dispatch("grep_codebase", {"repo": "svc", "pattern": "SECRET"})
        self.assertEqual(out["count"], 1)

    def test_unknown_tool(self):
        ctx = tools.ToolContext(self.settings, allowed_repos=["svc"])
        self.assertIn("error", ctx.dispatch("rm_rf", {}))


# ── Phase H: store lifecycle (in-memory, no DB) ───────────────────────────────

class StoreTests(unittest.TestCase):
    def setUp(self):
        # no DATABASE_URL → store uses in-memory mirror only
        import dataclasses
        self.settings = dataclasses.replace(
            make_settings(Path("/tmp")),
            database_url_override="", db_host="", db_name="", db_user="",
        )

    def test_create_and_transition(self):
        st = store.RCARunStore(self.settings)
        run = st.create("OPS-1")
        self.assertEqual(run.status, store.STATUS_QUEUED)
        st.touch(run, status=store.STATUS_INVESTIGATING)
        self.assertEqual(st.get(run.run_id).status, store.STATUS_INVESTIGATING)
        st.add_trace_event(run, {"tool": "read_file"})
        self.assertEqual(len(st.get(run.run_id).agent_trace), 1)

    def test_list_recent_in_memory(self):
        st = store.RCARunStore(self.settings)
        st.create("OPS-1")
        st.create("OPS-2")
        recent = st.list_recent()
        self.assertEqual(len(recent), 2)


if __name__ == "__main__":
    unittest.main()

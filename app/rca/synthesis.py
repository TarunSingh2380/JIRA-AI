"""Phase G — structured synthesis (DIAGNOSIS-first).

Turns the intake + retrieval candidates + agent findings into one structured
diagnosis that fills the house RCA template (9 sections) plus the machine schema
(root_cause / explanation / confidence / alternatives / evidence).

Fix policy: the system is diagnosis-first. A concrete `suggested_fix` is emitted
ONLY when confidence ≥ 0.95 (configurable); otherwise the resolution names the
suspected change area only. Any suggested fix is advisory — it is never applied,
never written to a worktree, and carries a human-review flag.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.config import Settings
from app.json_utils import parse_model_json

log = logging.getLogger(__name__)

_SYSTEM = """\
You are synthesizing a root-cause diagnosis for a production defect, to be
rendered into the team's standard 9-section RCA document.

You are given the ticket, extracted signals, retrieved candidate code locations,
and a read-only investigation summary with the evidence gathered. Produce ONLY a
JSON object (no prose, no fences) with EXACTLY these keys:

{
  "root_cause": {"repo": str, "file": str, "symbol": str|null, "lines": str|null},
  "what_happened": str,                      // §4.1 factual narrative
  "explanation": str,                        // why the defect occurs, causal terms
  "five_whys": [str, ...],                   // §4.2, 1-5 ordered "why" answers
  "final_root_cause": str,                   // single clear statement
  "confidence": number,                      // 0.0-1.0
  "alternative_hypotheses": [                // when confidence is low, give >1
    {"root_cause": {"repo","file","symbol","lines"}, "explanation": str, "confidence": number}
  ],
  "evidence": [{"type": str, "detail": str}],// blame line, ticket key, error string, call path...
  "impact": {"affected": str, "impact_type": str, "description": str},
  "expectation_vs_reality": {
    "development": {"expected": str, "actual": str, "gap": str},
    "code_review": {"expected": str, "actual": str, "gap": str},
    "qa_testing": {"expected": str, "actual": str, "gap": str},
    "requirement": {"expected": str, "actual": str, "gap": str}
  },
  "contributing_factors": {
    "code_issue": str, "configuration_issue": str, "infrastructure_issue": str,
    "qa_miss": str, "process_gap": str, "human_error": str, "requirement_ambiguity": str
  },
  "preventive_actions": [str, ...],
  "lessons_learned": {"do_differently": str, "process_change": str},
  "suggested_fix": null | {"description": str, "code": str, "confidence_basis": str}
}

Rules:
- Ground every claim in the investigation evidence. Cite file:line, commit, ticket
  key, or call path in the evidence array. Do not invent locations.
- root_cause.lines is a range like "42-58" when known, else null.
- If you are not confident, LOWER the confidence and provide multiple
  alternative_hypotheses rather than one over-confident answer.
- suggested_fix MUST be null UNLESS you are at least 95% certain of the correct
  fix from the code you actually read. When unsure, set it to null and let the
  resolution name only the suspected area. A non-null suggested_fix is a proposal
  for a human to review — never a final or applied change.
- For contributing_factors, use "Not applicable" for factors that do not apply.
"""

_SCHEMA_KEYS = (
    "root_cause", "what_happened", "explanation", "five_whys", "final_root_cause",
    "confidence", "alternative_hypotheses", "evidence", "impact",
    "expectation_vs_reality", "contributing_factors", "preventive_actions",
    "lessons_learned", "suggested_fix",
)


def _user_message(ticket: dict[str, Any], extracted: dict[str, Any],
                  candidates: list[dict[str, Any]], investigation: str,
                  trace: list[dict[str, Any]]) -> str:
    # trim the trace to the observations that carry signal
    trimmed = [
        {"tool": t.get("tool"), "input": t.get("input"),
         "observation": json.loads(json.dumps(t.get("observation"))[:1500])}
        for t in trace[-20:]
    ]
    return (
        "TICKET\n" + json.dumps(ticket, indent=2)[:3000] + "\n\n"
        "EXTRACTED SIGNALS\n" + json.dumps(extracted, indent=2) + "\n\n"
        "RETRIEVAL CANDIDATES\n" + json.dumps(candidates, indent=2)[:3000] + "\n\n"
        "INVESTIGATION SUMMARY (read-only agent)\n" + (investigation or "(none)") + "\n\n"
        "INVESTIGATION TRACE (recent tool observations)\n"
        + json.dumps(trimmed, indent=2)[:6000]
    )


def synthesize(
    settings: Settings,
    *,
    ticket: dict[str, Any],
    extracted: dict[str, Any],
    candidates: list[dict[str, Any]],
    investigation: str,
    trace: list[dict[str, Any]],
    llm_client: Any = None,
) -> dict[str, Any]:
    """Produce the structured diagnosis dict. Injectable client for tests."""
    if llm_client is None:
        from app.llm_client import AnthropicLLMClient
        llm_client = AnthropicLLMClient(
            settings,
            timeout_override=settings.llm_test_case_timeout_seconds,
        )
        llm_client.settings = _with_model(settings, settings.rca_synthesis_model)

    raw = llm_client.complete(
        _SYSTEM,
        _user_message(ticket, extracted, candidates, investigation, trace),
        max_tokens=4000,
    )
    try:
        parsed = parse_model_json(raw)
    except Exception as exc:
        log.warning("RCA synthesis JSON parse failed: %s", exc)
        parsed = {}

    return _normalize(parsed, settings)


def _with_model(settings: Settings, model: str) -> Settings:
    import dataclasses
    return dataclasses.replace(settings, llm_model=model)


def _normalize(parsed: dict[str, Any], settings: Settings) -> dict[str, Any]:
    out: dict[str, Any] = {k: parsed.get(k) for k in _SCHEMA_KEYS}

    rc = out.get("root_cause") or {}
    out["root_cause"] = {
        "repo": str(rc.get("repo") or ""), "file": str(rc.get("file") or ""),
        "symbol": rc.get("symbol"), "lines": rc.get("lines"),
    }
    try:
        out["confidence"] = max(0.0, min(1.0, float(out.get("confidence") or 0.0)))
    except (TypeError, ValueError):
        out["confidence"] = 0.0

    out["five_whys"] = _str_list(out.get("five_whys"))
    out["preventive_actions"] = _str_list(out.get("preventive_actions"))
    out["evidence"] = _evidence_list(out.get("evidence"))
    out["alternative_hypotheses"] = out.get("alternative_hypotheses") or []
    out["what_happened"] = str(out.get("what_happened") or "")
    out["explanation"] = str(out.get("explanation") or "")
    out["final_root_cause"] = str(out.get("final_root_cause") or "")
    out["impact"] = out.get("impact") or {}
    out["expectation_vs_reality"] = out.get("expectation_vs_reality") or {}
    out["contributing_factors"] = out.get("contributing_factors") or {}
    out["lessons_learned"] = out.get("lessons_learned") or {}

    # Enforce the ≥95% gate in code regardless of what the model returned.
    fix = out.get("suggested_fix")
    if out["confidence"] < settings.rca_confidence_threshold_for_fix or not isinstance(fix, dict):
        out["suggested_fix"] = None
    else:
        out["suggested_fix"] = {
            "description": str(fix.get("description") or ""),
            "code": str(fix.get("code") or ""),
            "confidence_basis": str(fix.get("confidence_basis") or ""),
            "human_review_required": True,  # always advisory
        }
    return out


def _str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _evidence_list(value: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if isinstance(value, list):
        for e in value:
            if isinstance(e, dict):
                out.append({"type": str(e.get("type") or ""),
                            "detail": str(e.get("detail") or "")})
            elif isinstance(e, str) and e.strip():
                out.append({"type": "note", "detail": e.strip()})
    return out

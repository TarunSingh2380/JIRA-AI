"""Phase G — evidence-first root-cause synthesis.

Turns the intake + retrieval candidates + agent findings into a strict,
evidence-grounded diagnosis. The contract (see `_SYSTEM`) optimizes for being
CORRECT, not for producing a complete report:

* the defect is classified into exactly one category;
* facts, inferences and unknowns are kept separate;
* a root cause is asserted ONLY with ≥2 independent pieces of evidence, else it
  stays "Undetermined";
* confidence is categorical (High/Medium/Low) — never an invented probability;
* if the required evidence is unavailable, the whole run is flagged
  INSUFFICIENT DATA and nothing is speculated;
* a concrete fix is proposed ONLY at High confidence; otherwise diagnosis-only.

Any suggested fix is advisory — never applied, never written to a worktree.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.config import Settings
from app.json_utils import parse_model_json

log = logging.getLogger(__name__)

# The one-of classification set (RULE 3). Anything else normalizes to
# "Cannot Determine".
ISSUE_CLASSES = (
    "Runtime Bug", "Missing Implementation", "Configuration Issue",
    "Infrastructure Issue", "Deployment Issue", "Data Issue", "Requirement Gap",
    "Third-party Dependency", "Performance Issue", "Security Issue",
    "Cannot Determine",
)

CONFIDENCE_LEVELS = ("High", "Medium", "Low")

# Categorical confidence → internal numeric, used ONLY for the existing delivery
# gate (RCA_CONFIDENCE_THRESHOLD) and fix gate (RCA_CONFIDENCE_THRESHOLD_FOR_FIX).
# It is never shown to the user (RULE 6 — no fake probabilities).
_CONFIDENCE_NUMERIC = {"High": 0.95, "Medium": 0.75, "Low": 0.3}

INSUFFICIENT_DATA_MESSAGE = (
    "INSUFFICIENT DATA: Target code or evidence required for RCA is unavailable. "
    "Root cause cannot be determined."
)

NO_FIX_MESSAGE = "Diagnosis only. Insufficient evidence to recommend a safe fix."

_SYSTEM = """\
You are an Enterprise Software Root Cause Analysis (RCA) Engine.
Identify the most probable root cause of a software defect using ONLY verifiable
evidence from source code, git history, logs, stack traces, test failures,
configuration, deployment artifacts and the ticket itself.
Never optimize for producing an RCA. Optimize for being CORRECT.

You are given the ticket, extracted signals, retrieved candidate code locations,
and a read-only investigation summary + trace with the evidence actually
gathered. Produce ONLY a JSON object (no prose, no fences) with EXACTLY:

{
  "insufficient_data": bool,        // true if target code/PR/repo/evidence is unavailable
  "issue_classification": str,      // EXACTLY one of the categories below
  "confidence": "High"|"Medium"|"Low",
  "facts": [str, ...],              // only directly observed evidence
  "inferences": [str, ...],         // logical conclusions supported by the facts
  "unknowns": [str, ...],           // evidence that is missing
  "root_cause": str,                // ONE concise paragraph, or exactly "Undetermined."
  "root_cause_location": {"repo": str, "file": str, "symbol": str|null, "lines": str|null},
  "evidence": [{"type": str, "detail": str, "ref": str}],  // ref = file:line / commit / log / stack / ticket
  "contributing_factors": [str, ...],   // optional; ONLY if supported by evidence
  "recommended_fix": str|null       // non-null ONLY when confidence is High
}

Classification (choose exactly one): Runtime Bug, Missing Implementation,
Configuration Issue, Infrastructure Issue, Deployment Issue, Data Issue,
Requirement Gap, Third-party Dependency, Performance Issue, Security Issue,
Cannot Determine.

Hard rules:
1. EVIDENCE FIRST — every conclusion must be directly supported by evidence you
   can point to. If you cannot point to evidence, do not state it. Never infer
   infrastructure, deployment, architecture, developer mistakes, QA failures or
   process gaps without direct evidence.
2. NO GHOST DATA — if the suspected code/PR/repo is unavailable, set
   "insufficient_data": true and put "Undetermined." in root_cause. Do not
   speculate.
3. CLASSIFY FIRST — a feature that was never implemented is NOT a runtime bug
   (use "Missing Implementation"). Match the analysis to the class.
4. FACTS ≠ INFERENCES — keep them in their separate arrays. unknowns lists what
   is missing.
5. EVIDENCE THRESHOLD — do NOT assert a root cause unless it is supported by at
   least TWO independent pieces of evidence (e.g. stack trace + code, git diff +
   failing test, logs + config, ticket + implementation). One clue is never
   enough; if you only have one, set root_cause to "Undetermined." and
   confidence "Low".
6. NO FAKE CERTAINTY — confidence is High only with direct evidence, Medium with
   partial evidence, Low when the cause cannot be proven. Never output a numeric
   percentage.
7. DYNAMIC SIZE — match depth to the defect. A trivial UI/CSS bug gets 1-2
   facts and a one-sentence root cause; a complex P1 gets more. Do not pad.
8. ROOT CAUSE ONLY — missing tests, "QA missed it", "code review missed it",
   missing docs, "developer error", process gaps are NOT root causes on their
   own. Include them only under contributing_factors and only with evidence.
9. GIT BLAME identifies who last changed a line, NOT who is responsible. Never
   attribute blame to a person based on git history.
10. NO GENERIC RECOMMENDATIONS — recommended_fix must directly address THIS
    defect. Never say "improve QA / testing / reviews / docs" unless the
    evidence demonstrates that specific failure.
11. recommended_fix is non-null ONLY when confidence is High AND root_cause is
    not "Undetermined." It is an advisory proposal for a human — never applied.

It is better to return root_cause "Undetermined." than an incorrect one. Never
reward completeness over correctness.
"""

_SCHEMA_KEYS = (
    "insufficient_data", "issue_classification", "confidence", "facts",
    "inferences", "unknowns", "root_cause", "root_cause_location", "evidence",
    "contributing_factors", "recommended_fix",
)


def _truncate_observation(observation: Any, limit: int) -> Any:
    """Return the observation compactly: the object if small, else a truncated
    string. Never produces invalid JSON (no slicing of serialized text)."""
    try:
        dumped = json.dumps(observation)
    except (TypeError, ValueError):
        return str(observation)[:limit]
    if len(dumped) <= limit:
        return observation
    return dumped[:limit] + "…(truncated)"


def _user_message(ticket: dict[str, Any], extracted: dict[str, Any],
                  candidates: list[dict[str, Any]], investigation: str,
                  trace: list[dict[str, Any]]) -> str:
    # trim the trace to the observations that carry signal. Truncate each
    # observation as a STRING (slicing the JSON text and re-parsing would yield
    # invalid JSON); keep it as a plain string so the outer dumps stays valid.
    trimmed = [
        {"tool": t.get("tool"), "input": t.get("input"),
         "observation": _truncate_observation(t.get("observation"), 1500)}
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

    # Location is kept for linking/blame; it is not asserted as the root cause.
    rc = out.get("root_cause_location") or {}
    out["root_cause_location"] = {
        "repo": str(rc.get("repo") or ""), "file": str(rc.get("file") or ""),
        "symbol": rc.get("symbol"), "lines": rc.get("lines"),
    }

    out["issue_classification"] = _one_of(
        out.get("issue_classification"), ISSUE_CLASSES, "Cannot Determine")
    label = _one_of(out.get("confidence"), CONFIDENCE_LEVELS, "Low")

    out["facts"] = _str_list(out.get("facts"))
    out["inferences"] = _str_list(out.get("inferences"))
    out["unknowns"] = _str_list(out.get("unknowns"))
    out["contributing_factors"] = _str_list(out.get("contributing_factors"))
    out["evidence"] = _evidence_list(out.get("evidence"))
    out["root_cause"] = str(out.get("root_cause") or "").strip()

    insufficient = bool(out.get("insufficient_data"))

    # RULE 2 — no ghost data. An INSUFFICIENT DATA run states only that.
    if insufficient:
        out["root_cause"] = INSUFFICIENT_DATA_MESSAGE
        label = "Low"
    else:
        # RULE 5 — a root cause needs ≥2 independent evidence items. Fewer than
        # that (or an empty/undetermined statement) collapses to Undetermined.
        undetermined = (not out["root_cause"]
                        or out["root_cause"].lower().startswith("undetermined"))
        if len(out["evidence"]) < 2 or undetermined:
            out["root_cause"] = "Undetermined."
            label = "Low"

    out["confidence_label"] = label
    out["confidence"] = _CONFIDENCE_NUMERIC[label]  # internal gate only

    # RULE 11 — a fix is offered ONLY at High confidence with a determined cause.
    determined = out["root_cause"] not in ("Undetermined.", INSUFFICIENT_DATA_MESSAGE)
    fix = out.get("recommended_fix")
    if label == "High" and determined and isinstance(fix, str) and fix.strip():
        out["recommended_fix"] = fix.strip()
    else:
        out["recommended_fix"] = None
    return out


def _one_of(value: Any, allowed: tuple[str, ...], default: str) -> str:
    text = str(value or "").strip()
    for candidate in allowed:
        if text.lower() == candidate.lower():
            return candidate
    return default


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
                            "detail": str(e.get("detail") or ""),
                            "ref": str(e.get("ref") or "")})
            elif isinstance(e, str) and e.strip():
                out.append({"type": "note", "detail": e.strip(), "ref": ""})
    return out

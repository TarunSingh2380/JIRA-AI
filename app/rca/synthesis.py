"""Phase G — evidence-first root-cause synthesis.

Turns the intake + retrieval candidates + agent findings into a strict,
evidence-grounded diagnosis. The contract (see `_SYSTEM`) optimizes for being
CORRECT, not for producing a complete report:

* the defect is classified into exactly one category;
* facts, inferences and unknowns are kept separate;
* a root cause is asserted ONLY with ≥2 independent pieces of evidence, else it
  stays "Undetermined";
* a root cause is CONFIRMED (header "ROOT CAUSE") only when it explains every
  symptom, has ≥2 independent evidence sources, and has no contradictory evidence;
  otherwise it is reported as "MOST LIKELY ROOT CAUSE" with the evidence still
  required to confirm it;
* confidence is categorical (High/Medium/Low) — never an invented probability;
* if the required evidence is unavailable, the whole run is flagged
  INSUFFICIENT DATA and nothing is speculated;
* the NEXT ACTION matches confidence — a fix at High, verification steps at
  Medium, additional evidence required at Low;
* authorship (introducing commit) is reported ONLY from git history, never
  inferred, never framed as blame.

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

# Evidence is grouped into these fixed buckets in the output (RULE 11).
EVIDENCE_CATEGORIES = ("Code", "Git", "Logs", "Tests", "Configuration", "Ticket")

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
  "root_cause_confirmed": bool,     // true ONLY if all three checks in RULE 5 hold
  "root_cause_location": {"repo": str, "file": str, "symbol": str|null, "lines": str|null},
  "introduced_by": {"name": str|null, "commit": str|null, "date": str|null}|null,  // ONLY from git history (RULE 10)
  "evidence": [{"category": "Code"|"Git"|"Logs"|"Tests"|"Configuration"|"Ticket", "detail": str, "ref": str}],
  "contributing_factors": [str, ...],       // optional; ONLY if supported by evidence
  "additional_evidence_required": [str, ...],  // what is still needed to confirm / before a fix
  "verification_steps": [str, ...],            // checks to run before changing code (Medium confidence)
  "recommended_fix": str|null       // the EXACT code change; non-null ONLY at High confidence (RULE 14)
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
5. ROOT CAUSE VERIFICATION — a root cause is CONFIRMED only when ALL THREE hold:
   (a) it explains EVERY observed symptom; (b) it is supported by at least TWO
   INDEPENDENT evidence sources (e.g. stack trace + code, git diff + failing
   test, logs + config, ticket + implementation); (c) NO contradictory evidence
   exists. If all three hold, set root_cause_confirmed=true. If you have a
   leading candidate but any check fails, KEEP it in root_cause, set
   root_cause_confirmed=false, and list exactly what would confirm it in
   additional_evidence_required. If you have no evidence-backed candidate, set
   root_cause="Undetermined." and root_cause_confirmed=false.
6. NO FAKE CERTAINTY — confidence is High ONLY when the root cause is confirmed
   (RULE 5) with direct evidence; Medium for a leading-but-unconfirmed cause; Low
   when the cause cannot be established. Never output a numeric percentage.
7. DYNAMIC SIZE — match depth to the defect. A trivial UI/CSS bug gets 1-2
   facts and a one-sentence root cause; a complex P1 gets more. Do not pad.
8. ROOT CAUSE ONLY — missing tests, "QA missed it", "code review missed it",
   missing docs, "developer error", process gaps are NOT root causes on their
   own. Include them only under contributing_factors and only with evidence.
9. GIT BLAME identifies who last changed a line, NOT who is responsible. Never
   attribute blame to a person based on git history.
10. AUTHORSHIP — if the introducing (or last-modifying) commit for the
    root-cause lines is identifiable from git history in the evidence or trace,
    populate introduced_by {name, commit, date}. Report authorship ONLY when
    supported by git history; never infer responsibility; never attribute blame
    based solely on git blame. If the introducing commit cannot be determined,
    set introduced_by to null.
11. EVIDENCE CATEGORIES — every evidence item has a category: exactly one of
    Code, Git, Logs, Tests, Configuration, Ticket. Put each item in its single
    best-fitting category with a precise ref (file:line / commit / log line /
    test name / config key / ticket field).
12. NEXT ACTION MATCHES CONFIDENCE — High: recommended_fix = the exact code
    change. Medium: verification_steps = the checks to run before any code change
    (recommended_fix null). Low: additional_evidence_required = the specific
    evidence still needed (recommended_fix null, verification_steps empty).
13. NO GENERIC RECOMMENDATIONS — recommended_fix / verification_steps must
    directly address THIS defect. Never say "improve QA / testing / reviews /
    docs" unless the evidence demonstrates that specific failure.
14. recommended_fix is non-null ONLY when confidence is High AND
    root_cause_confirmed is true AND root_cause is not "Undetermined." It is an
    advisory proposal for a human — never applied.

It is better to return root_cause "Undetermined." than an incorrect one. Never
reward completeness over correctness.
"""

_SCHEMA_KEYS = (
    "insufficient_data", "issue_classification", "confidence", "facts",
    "inferences", "unknowns", "root_cause", "root_cause_confirmed",
    "root_cause_location", "introduced_by", "evidence", "contributing_factors",
    "additional_evidence_required", "verification_steps", "recommended_fix",
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
    out["additional_evidence_required"] = _str_list(out.get("additional_evidence_required"))
    out["verification_steps"] = _str_list(out.get("verification_steps"))
    out["evidence"] = _evidence_list(out.get("evidence"))
    out["introduced_by"] = _introduced_by(out.get("introduced_by"))
    out["root_cause"] = str(out.get("root_cause") or "").strip()
    confirmed = bool(out.get("root_cause_confirmed"))

    insufficient = bool(out.get("insufficient_data"))

    # RULE 2 — no ghost data. An INSUFFICIENT DATA run states only that.
    if insufficient:
        out["root_cause"] = INSUFFICIENT_DATA_MESSAGE
        label, confirmed, status = "Low", False, "insufficient"
    else:
        # RULE 5 — a root cause needs ≥2 independent evidence items. Fewer than
        # that (or an empty/undetermined statement) collapses to Undetermined.
        undetermined = (not out["root_cause"]
                        or out["root_cause"].lower().startswith("undetermined"))
        if len(out["evidence"]) < 2 or undetermined:
            out["root_cause"] = "Undetermined."
            label, confirmed, status = "Low", False, "undetermined"
        elif confirmed:
            # Verified: explains the symptoms, ≥2 evidence, no contradiction.
            status = "confirmed"
        else:
            # RULE 5 — a leading candidate that isn't fully verified is reported
            # as MOST LIKELY, and (RULE 6) cannot be High confidence.
            status = "most_likely"
            if label == "High":
                label = "Medium"

    out["root_cause_confirmed"] = confirmed
    out["root_cause_status"] = status
    out["confidence_label"] = label
    out["confidence"] = _CONFIDENCE_NUMERIC[label]  # internal gate only

    # RULE 12 — NEXT ACTION matches confidence. Keep only the fields for the tier
    # so the renderer shows exactly one action.
    determined = out["root_cause"] not in ("Undetermined.", INSUFFICIENT_DATA_MESSAGE)
    fix = out.get("recommended_fix")
    if label == "High" and confirmed and determined and isinstance(fix, str) and fix.strip():
        out["recommended_fix"] = fix.strip()   # RULE 14
    else:
        out["recommended_fix"] = None
    if label != "Medium":
        out["verification_steps"] = []          # verification is the Medium action
    if label == "High" and confirmed:
        out["additional_evidence_required"] = []  # nothing left to confirm
    return out


def _introduced_by(value: Any) -> Optional[dict[str, Optional[str]]]:
    """Normalize authorship to {name, commit, date} or None (RULE 10). Only a
    real commit reference counts; a bare name with no commit is dropped so we
    never present unsupported authorship."""
    if not isinstance(value, dict):
        return None
    commit = str(value.get("commit") or "").strip()
    if not commit:
        return None
    name = str(value.get("name") or "").strip()
    date = str(value.get("date") or "").strip()
    return {"name": name or None, "commit": commit, "date": date or None}


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
                ref = str(e.get("ref") or "")
                out.append({
                    "category": _evidence_category(
                        e.get("category") or e.get("type"), ref),
                    "detail": str(e.get("detail") or ""),
                    "ref": ref,
                })
            elif isinstance(e, str) and e.strip():
                out.append({"category": _evidence_category(None, ""),
                            "detail": e.strip(), "ref": ""})
    return out


# Legacy `type` keywords → the fixed category buckets (RULE 11). Anything that
# doesn't match a non-code bucket is treated as Code.
_CATEGORY_KEYWORDS = (
    ("Git", ("git", "commit", "blame", "history", "diff", "pr ", "pull")),
    ("Logs", ("log",)),
    ("Tests", ("test", "spec", "assert")),
    ("Configuration", ("config", "env", "setting", "yaml", ".env")),
    ("Ticket", ("ticket", "repro", "jira", "comment")),
)


def _evidence_category(raw: Any, ref: str) -> str:
    text = str(raw or "").strip()
    for category in EVIDENCE_CATEGORIES:
        if text.lower() == category.lower():
            return category  # explicit, valid category
    hay = f"{text} {ref}".lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(k in hay for k in keywords):
            return category
    return "Code"

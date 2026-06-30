"""Render a diagnosis into the team's house RCA template (9 sections).

build_document() shapes the structured diagnosis into the nine canonical
sections; render_markdown() produces the human/Jira text; render_docx() produces
a Word document matching the senior-team format (reusing markdown_to_docx_bytes).

Section 7 (Resolution) reflects the diagnosis-first policy: it states the
suspected change area, and includes suggested fix code ONLY when synthesis
emitted one (confidence ≥ the fix threshold) — always flagged as an advisory
proposal for human review, never an applied change.
"""
from __future__ import annotations

from typing import Any

_FACTOR_LABELS = [
    ("code_issue", "Code Issue"),
    ("configuration_issue", "Configuration Issue"),
    ("infrastructure_issue", "Infrastructure Issue"),
    ("qa_miss", "QA Miss"),
    ("process_gap", "Process Gap"),
    ("human_error", "Human Error"),
    ("requirement_ambiguity", "Requirement Ambiguity"),
]

_EVR_LABELS = [
    ("development", "Development"),
    ("code_review", "Code Review"),
    ("qa_testing", "QA Testing"),
    ("requirement", "Requirement"),
]


def build_document(ticket: dict[str, Any], extracted: dict[str, Any],
                   diagnosis: dict[str, Any], agent_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assemble the 9-section document model from the diagnosis."""
    rc = diagnosis.get("root_cause") or {}
    ownership = diagnosis.get("ownership") or {}
    loc = _format_location(rc)

    return {
        "title": f"{ticket.get('key', '')} – {ticket.get('summary', '')}".strip(" –"),
        "key": ticket.get("key", ""),
        "confidence": diagnosis.get("confidence"),
        "root_cause_location": loc,
        "sections": {
            "issue_summary": {
                "title": ticket.get("summary", ""),
                "brief_description": diagnosis.get("what_happened", ""),
                "environment": ticket.get("environment", "Production"),
                "module": diagnosis.get("impact", {}).get("module") or loc,
                "detected_in": ticket.get("issue_type", ""),
            },
            "impact_assessment": diagnosis.get("impact", {}),
            "ownership": {
                "original_developer": ownership.get("original_developer", "N/A"),
                "blame": ownership.get("blame_lines", ""),
                "last_commit": ownership.get("last_commit_sha", ""),
            },
            "root_cause_analysis": {
                "what_happened": diagnosis.get("what_happened", ""),
                "five_whys": diagnosis.get("five_whys", []),
                "explanation": diagnosis.get("explanation", ""),
                "final_root_cause": diagnosis.get("final_root_cause", ""),
                "location": loc,
                "alternative_hypotheses": diagnosis.get("alternative_hypotheses", []),
            },
            "expectation_vs_reality": diagnosis.get("expectation_vs_reality", {}),
            "contributing_factors": diagnosis.get("contributing_factors", {}),
            "resolution": _resolution(diagnosis),
            "preventive_actions": diagnosis.get("preventive_actions", []),
            "lessons_learned": diagnosis.get("lessons_learned", {}),
        },
        "evidence": diagnosis.get("evidence", []),
        "agent_meta": agent_meta or {},
    }


def _format_location(rc: dict[str, Any]) -> str:
    parts = []
    if rc.get("repo"):
        parts.append(rc["repo"])
    file_sym = rc.get("file") or ""
    if rc.get("symbol"):
        file_sym = f"{file_sym} :: {rc['symbol']}" if file_sym else rc["symbol"]
    if file_sym:
        parts.append(file_sym)
    loc = " / ".join(parts)
    if rc.get("lines"):
        loc += f" (lines {rc['lines']})"
    return loc or "Not localized"


def _resolution(diagnosis: dict[str, Any]) -> dict[str, Any]:
    fix = diagnosis.get("suggested_fix")
    if fix:
        return {
            "mode": "suggested_fix",
            "description": fix.get("description", ""),
            "code": fix.get("code", ""),
            "confidence_basis": fix.get("confidence_basis", ""),
            "note": "AI-suggested fix (confidence ≥ threshold). Advisory only — "
                    "requires human review; not applied.",
        }
    return {
        "mode": "area_only",
        "description": "Diagnosis-only: suspected change area identified below. "
                       "A concrete fix was withheld (confidence below the fix "
                       "threshold). Resolution to be implemented by the developer.",
        "area": diagnosis.get("root_cause", {}),
    }


# ── markdown rendering (drives both on-screen text and the docx) ──────────────

def render_markdown(document: dict[str, Any]) -> str:
    s = document["sections"]
    out: list[str] = []
    conf = document.get("confidence")
    conf_str = f"{conf:.0%}" if isinstance(conf, (int, float)) else "N/A"

    out.append(f"# Root Cause Analysis (RCA) — {document.get('key', '')}")
    out.append(f"_AI-generated diagnosis · confidence {conf_str} · "
               f"root cause: {document.get('root_cause_location')}_\n")

    iss = s["issue_summary"]
    out.append("## 1. Issue Summary")
    out.append(f"- **Title:** {iss.get('title','')}")
    out.append(f"- **Brief Description:** {iss.get('brief_description','')}")
    out.append(f"- **Environment:** {iss.get('environment','')}")
    out.append(f"- **Module / Service / API / DB:** {iss.get('module','')}\n")

    imp = s["impact_assessment"]
    out.append("## 2. Impact Assessment")
    out.append(f"- **Affected:** {imp.get('affected','')}")
    out.append(f"- **Impact Type:** {imp.get('impact_type','')}")
    out.append(f"- **Description:** {imp.get('description','')}\n")

    own = s["ownership"]
    out.append("## 3. Ownership & Accountability")
    out.append(f"- **Original Developer (from git blame):** {own.get('original_developer','N/A')}")
    if own.get("blame"):
        out.append(f"- **Blamed lines:** {own.get('blame')} (commit {own.get('last_commit','')[:10]})")
    out.append("")

    rca = s["root_cause_analysis"]
    out.append("## 4. Root Cause Analysis")
    out.append("### 4.1 What Happened")
    out.append(rca.get("what_happened", "") + "\n")
    out.append("### 4.2 Why Did It Happen (5 Whys)")
    for i, why in enumerate(rca.get("five_whys", []), 1):
        out.append(f"{i}. {why}")
    out.append("")
    out.append(f"**Final Root Cause:** {rca.get('final_root_cause','')}")
    out.append(f"**Location:** {rca.get('location','')}")
    if rca.get("explanation"):
        out.append(f"\n{rca.get('explanation')}")
    alts = rca.get("alternative_hypotheses", [])
    if alts:
        out.append("\n**Alternative Hypotheses:**")
        for a in alts:
            ac = a.get("confidence")
            acs = f"{ac:.0%}" if isinstance(ac, (int, float)) else ""
            out.append(f"- ({acs}) {_format_location(a.get('root_cause', {}))} — "
                       f"{a.get('explanation','')}")
    out.append("")

    evr = s["expectation_vs_reality"]
    out.append("## 5. Expectation vs Reality")
    for key, label in _EVR_LABELS:
        block = evr.get(key) or {}
        if any(block.get(k) for k in ("expected", "actual", "gap")):
            out.append(f"**{label}**")
            out.append(f"- Expected: {block.get('expected','')}")
            out.append(f"- Actual: {block.get('actual','')}")
            out.append(f"- Gap: {block.get('gap','')}")
    out.append("")

    cf = s["contributing_factors"]
    out.append("## 6. Contributing Factors")
    for key, label in _FACTOR_LABELS:
        val = cf.get(key)
        if val and str(val).strip().lower() not in ("", "not applicable", "n/a", "none"):
            out.append(f"- **{label}:** {val}")
    out.append("")

    res = s["resolution"]
    out.append("## 7. Resolution")
    out.append(res.get("description", ""))
    if res.get("mode") == "suggested_fix":
        out.append(f"\n_{res.get('note','')}_")
        if res.get("code"):
            out.append("\n```\n" + res["code"] + "\n```")
        if res.get("confidence_basis"):
            out.append(f"\n**Why high confidence:** {res['confidence_basis']}")
    out.append("")

    out.append("## 8. Preventive Actions")
    for action in s["preventive_actions"]:
        out.append(f"- {action}")
    out.append("")

    ll = s["lessons_learned"]
    out.append("## 9. Lessons Learned")
    if ll.get("do_differently"):
        out.append(f"- **What we should do differently:** {ll.get('do_differently')}")
    if ll.get("process_change"):
        out.append(f"- **Process/system change to prevent recurrence:** {ll.get('process_change')}")
    out.append("")

    ev = document.get("evidence", [])
    if ev:
        out.append("## Evidence Trail")
        for e in ev:
            out.append(f"- **{e.get('type','')}:** {e.get('detail','')}")

    return "\n".join(out)


def render_docx(document: dict[str, Any]) -> bytes:
    from app.markdown_docx import markdown_to_docx_bytes
    md = render_markdown(document)
    return markdown_to_docx_bytes(md, title=f"RCA — {document.get('key','')}")

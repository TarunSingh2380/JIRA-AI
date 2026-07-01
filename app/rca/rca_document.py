"""Render an evidence-first diagnosis into the RCA output contract.

build_document() shapes the structured diagnosis into the delivery model;
render_markdown() produces the human/Jira text following the fixed OUTPUT FORMAT
(Issue Classification → Confidence → FACTS → INFERENCES → UNKNOWNS → ROOT CAUSE
→ EVIDENCE → CONTRIBUTING FACTORS → RECOMMENDED FIX); render_docx() produces the
Word version.

An INSUFFICIENT DATA run (RULE 2) renders ONLY that single line — no facts,
inferences or fabricated sections. A fix is shown ONLY at High confidence; every
other run states "Diagnosis only. Insufficient evidence to recommend a safe fix."
"""
from __future__ import annotations

from typing import Any

from app.rca.synthesis import INSUFFICIENT_DATA_MESSAGE, NO_FIX_MESSAGE


def build_document(ticket: dict[str, Any], extracted: dict[str, Any],
                   diagnosis: dict[str, Any], agent_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assemble the delivery model from the evidence-first diagnosis."""
    loc = _format_location(diagnosis.get("root_cause_location") or {})
    root_cause = str(diagnosis.get("root_cause") or "Undetermined.")
    return {
        "title": f"{ticket.get('key', '')} – {ticket.get('summary', '')}".strip(" –"),
        "key": ticket.get("key", ""),
        "insufficient_data": root_cause == INSUFFICIENT_DATA_MESSAGE,
        "issue_classification": diagnosis.get("issue_classification", "Cannot Determine"),
        "confidence_label": diagnosis.get("confidence_label", "Low"),
        "root_cause": root_cause,
        "root_cause_location": loc,
        "facts": diagnosis.get("facts", []),
        "inferences": diagnosis.get("inferences", []),
        "unknowns": diagnosis.get("unknowns", []),
        "evidence": diagnosis.get("evidence", []),
        "contributing_factors": diagnosis.get("contributing_factors", []),
        "recommended_fix": diagnosis.get("recommended_fix"),
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


# ── markdown rendering (drives both on-screen text and the docx) ──────────────

def render_markdown(document: dict[str, Any]) -> str:
    key = document.get("key", "")

    # RULE 2 — an INSUFFICIENT DATA run states only that. No fabricated sections.
    if document.get("insufficient_data"):
        return (f"# Root Cause Analysis (RCA) — {key}\n\n"
                f"{INSUFFICIENT_DATA_MESSAGE}")

    classification = document.get("issue_classification", "Cannot Determine")
    confidence = document.get("confidence_label", "Low")
    out: list[str] = []

    out.append(f"# Root Cause Analysis (RCA) — {key}")
    out.append(f"_AI-generated diagnosis · {classification} · confidence {confidence}_\n")

    out.append(f"**Issue Classification:** {classification}")
    out.append(f"**Confidence:** {confidence}\n")

    _bullets(out, "FACTS", document.get("facts", []))
    _bullets(out, "INFERENCES", document.get("inferences", []))
    _bullets(out, "UNKNOWNS", document.get("unknowns", []))

    out.append("## ROOT CAUSE")
    out.append(document.get("root_cause", "Undetermined.") + "\n")

    out.append("## EVIDENCE")
    ev = document.get("evidence", [])
    if ev:
        for e in ev:
            ref = f" — `{e.get('ref')}`" if e.get("ref") else ""
            label = e.get("type") or "evidence"
            out.append(f"- **{label}:** {e.get('detail','')}{ref}")
    else:
        out.append("- None available.")
    out.append("")

    cf = document.get("contributing_factors", [])
    if cf:
        _bullets(out, "CONTRIBUTING FACTORS", cf)

    out.append("## RECOMMENDED FIX")
    fix = document.get("recommended_fix")
    if fix:
        out.append(fix)
    else:
        out.append(NO_FIX_MESSAGE)

    return "\n".join(out)


def _bullets(out: list[str], heading: str, items: list[Any]) -> None:
    """Append a `## heading` section of bullet items; skip when empty."""
    items = [str(i).strip() for i in (items or []) if str(i).strip()]
    if not items:
        return
    out.append(f"## {heading}")
    for item in items:
        out.append(f"- {item}")
    out.append("")


def render_docx(document: dict[str, Any]) -> bytes:
    from app.markdown_docx import markdown_to_docx_bytes
    md = render_markdown(document)
    return markdown_to_docx_bytes(md, title=f"RCA — {document.get('key','')}")

"""Judge original vs AI-governor test cases with a fresh Claude instance per ticket.

Each ticket is judged by an independent, single-turn Anthropic API call (no shared
context across tickets), so every judgement is a clean-room "new Claude instance".
Produces per ticket: original score /10, AI-gov score /10, a detailed quality-diff
explanation, and a CEO-facing summary.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from anthropic import Anthropic  # noqa: E402

IN_JSON = ROOT / "scripts_tc_compare" / "data_gathered.json"
OUT_JSON = ROOT / "scripts_tc_compare" / "data_judged.json"
MODEL = os.getenv("JUDGE_MODEL", "claude-opus-4-5")

SYSTEM = """You are a senior QA engineering leader acting as an impartial judge.
You are given ONE Jira ticket, its ORIGINAL human-written test cases, and a set of
AI-generated ("AI Governor") test cases. Judge their quality independently and fairly.

Score each set out of 10 using these criteria, weighted by importance:
- Coverage (happy path, negative, edge/boundary, security/permissions)
- Concrete, verifiable expected results and assertions
- Clear step-by-step structure and unambiguous wording
- Traceability to the ticket's behaviour / acceptance criteria
- Test data, preconditions, and setup
- Grounding in the actual system (routes, files, services, tables) and automation readiness

Be calibrated: a sparse Slack-style note or a link to an external sheet with little
substance is low (2-4). A thorough, grounded, well-structured suite is high (8-10).
Reward substance, not length. Do not invent facts not present in the inputs.

Return ONLY a JSON object, no prose, with exactly these keys:
{
  "original_score": <number 0-10, one decimal allowed>,
  "ai_gov_score": <number 0-10, one decimal allowed>,
  "detailed_difference": "<a detailed, specific explanation of the quality difference, citing concrete aspects of both sets>",
  "ceo_summary": "<2-4 sentences a CEO can read: what the gap means in plain business terms (risk, effort saved, coverage)>"
}"""


def build_user_prompt(rec: dict) -> str:
    original = rec.get("original_test_cases") or "(No original test cases found.)"
    ai_gov = rec.get("ai_gov_test_cases") or "(AI governor produced no output.)"
    return (
        f"TICKET: {rec.get('ticket_key')} — {rec.get('summary')}\n"
        f"ISSUE TYPE: {rec.get('issue_type')}\n\n"
        f"TICKET DESCRIPTION / CONTEXT:\n{(rec.get('description') or '(none)')[:6000]}\n\n"
        f"===== ORIGINAL (human) TEST CASES =====\n{original[:14000]}\n\n"
        f"===== AI GOVERNOR TEST CASES =====\n{ai_gov[:18000]}\n\n"
        "Judge both sets now and return the JSON object."
    )


def parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError(f"No JSON found in: {text[:200]}")
    return json.loads(m.group(0))


def main() -> None:
    records = json.loads(IN_JSON.read_text())
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY missing")

    out = []
    for i, rec in enumerate(records, 1):
        key = rec.get("ticket_key")
        # Fresh client => fresh, isolated Claude instance per ticket.
        client = Anthropic(api_key=api_key, timeout=300)
        t0 = time.time()
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                temperature=0.0,
                system=SYSTEM,
                messages=[{"role": "user", "content": build_user_prompt(rec)}],
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
            verdict = parse_json(text)
            rec = dict(rec)
            rec["original_score"] = verdict.get("original_score")
            rec["ai_gov_score"] = verdict.get("ai_gov_score")
            rec["detailed_difference"] = verdict.get("detailed_difference", "")
            rec["ceo_summary"] = verdict.get("ceo_summary", "")
            rec["judge_error"] = ""
            print(
                f"[{i}/{len(records)}] {key} judged in {time.time()-t0:.0f}s "
                f"orig={rec['original_score']} ai={rec['ai_gov_score']}",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            rec = dict(rec)
            rec["original_score"] = None
            rec["ai_gov_score"] = None
            rec["detailed_difference"] = ""
            rec["ceo_summary"] = ""
            rec["judge_error"] = str(exc)[:500]
            print(f"[{i}/{len(records)}] {key} JUDGE FAILED: {exc}", flush=True)

        out.append(rec)
        OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print(f"\nDone judging {len(out)} tickets -> {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()

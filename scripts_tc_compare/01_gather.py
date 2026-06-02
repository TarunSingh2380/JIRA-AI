"""Gather original + AI-governor test cases for the 22 test-case tickets.

- Original test cases are extracted from the Postgres jira_ticket_cache using the
  same helpers the production comparison report uses.
- AI-governor test cases are produced by the running RepoTree pipeline via the
  live API at API_BASE/testcases/generate.

Writes incremental progress to OUT_JSON so the (slow) generation can resume.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import requests  # noqa: E402

from app.config import settings  # noqa: E402
from app.jira_ticket_insights import _include_ticket, _scan_ticket  # noqa: E402
from app.jira_ticket_insights import (  # noqa: E402
    DEFAULT_EXCLUDED_PROJECT_KEYS,
    _normalized_project_keys,
    _normalize_space,
    _project_where_clause,
)
from app.test_case_comparison_report import (  # noqa: E402
    _test_case_source_texts,
    _ticket_generation_payload,
)

API_BASE = os.getenv("TC_API_BASE", "http://127.0.0.1:8000")
OUT_JSON = ROOT / "scripts_tc_compare" / "data_gathered.json"


def load_test_case_rows() -> list[dict]:
    import psycopg
    from psycopg.rows import dict_row

    excluded = _normalized_project_keys(DEFAULT_EXCLUDED_PROJECT_KEYS)
    where, params = _project_where_clause(None, excluded)
    with psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=20) as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT ticket_key, project_key, summary, description, status,
                       issue_type, labels, updated_at, fetched_at, data
                FROM jira_ticket_cache
                {where}
                ORDER BY updated_at DESC NULLS LAST, fetched_at DESC NULLS LAST
                """,
                params,
            ).fetchall()
        ]

    selected = []
    for row in rows:
        insight = _scan_ticket(dict(row), settings.jira_base_url)
        if _include_ticket(insight, "test_cases"):
            selected.append((row, insight))
    return selected


def original_test_cases_text(row: dict) -> str:
    source_texts = _test_case_source_texts(row)
    seen = set()
    parts = []
    for source, text in source_texts:
        t = _normalize_space(text)
        if not t or t in seen:
            continue
        seen.add(t)
        parts.append(f"[{source}] {t}")
    return "\n\n".join(parts).strip()


def generate_ai_gov(payload: dict) -> dict:
    body = {
        "ticket": {
            "key": payload["key"],
            "summary": payload["summary"],
            "issueType": payload.get("issueType", ""),
            "description": payload.get("description", ""),
            "acceptanceCriteria": payload.get("acceptanceCriteria", ""),
            "labels": payload.get("labels", []),
            "components": payload.get("components", []),
        },
        "style": "plain",
        "embedding_model": "codebase_bge_m3",
        "top_k": 15,
        "include_semantic_context": True,
    }
    r = requests.post(f"{API_BASE}/testcases/generate", json=body, timeout=600)
    r.raise_for_status()
    return r.json()


def main() -> None:
    selected = load_test_case_rows()
    print(f"Found {len(selected)} tickets with test cases", flush=True)

    existing = {}
    if OUT_JSON.exists():
        existing = {d["ticket_key"]: d for d in json.loads(OUT_JSON.read_text())}

    results = []
    for i, (row, insight) in enumerate(selected, 1):
        key = str(row.get("ticket_key") or "")
        prior = existing.get(key)
        if prior and prior.get("ai_gov_test_cases") and not prior.get("ai_gov_error"):
            print(f"[{i}/{len(selected)}] {key} cached, skip", flush=True)
            results.append(prior)
            continue

        original = original_test_cases_text(row)
        gen_payload = _ticket_generation_payload(row)
        description = gen_payload.get("description", "")

        record = {
            "ticket_key": key,
            "project_key": str(row.get("project_key") or ""),
            "summary": str(row.get("summary") or ""),
            "issue_type": str(row.get("issue_type") or ""),
            "status": str(row.get("status") or ""),
            "url": insight.get("url") or "",
            "description": description,
            "original_test_cases": original,
            "ai_gov_test_cases": "",
            "grounded_repos": [],
            "semantic_hits_count": 0,
            "files_touched_count": 0,
            "ai_gov_error": "",
        }

        t0 = time.time()
        try:
            data = generate_ai_gov(gen_payload)
            record["ai_gov_test_cases"] = data.get("test_cases") or ""
            record["grounded_repos"] = data.get("grounded_repos") or []
            record["semantic_hits_count"] = int(data.get("semantic_hits_count") or 0)
            record["files_touched_count"] = int(data.get("files_touched_count") or 0)
            dt = time.time() - t0
            print(
                f"[{i}/{len(selected)}] {key} OK in {dt:.0f}s "
                f"(repos={record['grounded_repos']}, {len(record['ai_gov_test_cases'])} chars)",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            record["ai_gov_error"] = str(exc)[:1000]
            print(f"[{i}/{len(selected)}] {key} FAILED: {exc}", flush=True)

        results.append(record)
        OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    ok = sum(1 for r in results if r.get("ai_gov_test_cases") and not r.get("ai_gov_error"))
    print(f"\nDone. {ok}/{len(results)} AI-gov generations succeeded. -> {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()

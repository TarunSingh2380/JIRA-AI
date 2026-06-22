"""LLM-backed effort estimation for the WF7 RFT estimate report.

For each ticket (with an Original Estimate) we ground the model in the ticket
fields plus best-effort codebase context, then ask it to predict the realistic
effort an *average experienced developer* would need. We compare that against
the Jira Original Estimate and flag tickets that drift beyond a threshold.

Predictions are cached in ``rft_estimate_predictions`` keyed by a content hash
(summary + description + issue type + original estimate), so the daily run only
calls the LLM for new/changed tickets — subsequent runs are near-free.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

from app.config import Settings
from app.json_utils import parse_model_json
from app.llm_client import build_llm_client

LOGGER = logging.getLogger(__name__)

# Bump when the prompt / output shape changes so cached rows regenerate.
_PROMPT_VERSION = "v2"

_SYSTEM_PROMPT = (
    "You are a senior engineering estimator. Estimate how long a single average "
    "experienced developer (mid-to-senior, familiar with the stack but not this "
    "exact ticket) would realistically need to fully deliver the work: "
    "implementation, self-test, code review fixes. Use the ticket details and any "
    "codebase context provided. Account for complexity, unknowns, integration and "
    "testing — not just the happy-path coding time. You are also given the team's "
    "current Original Estimate; compare your realistic estimate against it. "
    "Respond with STRICT JSON only:\n"
    '{"predicted_hours": <number, working hours>, '
    '"confidence": "low|medium|high", '
    '"reason": "<= 12 words: the main driver, or why confidence is not high", '
    '"explanation": "1-2 complete sentences explaining why your estimate is '
    'higher/lower than (or matches) the current Original Estimate"}'
)


def _connect(settings: Settings):
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(settings.database_url, row_factory=dict_row)


def ensure_predictions_schema(settings: Settings) -> None:
    if not settings.database_url:
        return
    with _connect(settings) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rft_estimate_predictions (
                jira_ticket_id   TEXT PRIMARY KEY,
                content_hash     TEXT NOT NULL,
                original_seconds BIGINT,
                predicted_hours  DOUBLE PRECISION,
                confidence       TEXT,
                rationale        TEXT,
                flag             TEXT,
                updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        # Self-healing columns added after the initial release.
        conn.execute("ALTER TABLE rft_estimate_predictions ADD COLUMN IF NOT EXISTS reason TEXT")
        conn.execute("ALTER TABLE rft_estimate_predictions ADD COLUMN IF NOT EXISTS explanation TEXT")
        conn.commit()


def _content_hash(ticket: dict[str, Any]) -> str:
    raw = _PROMPT_VERSION + "|" + "|".join(
        str(ticket.get(k, ""))
        for k in ("summary", "description", "issue_type", "estimate_seconds")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_cache(settings: Settings, keys: list[str]) -> dict[str, dict[str, Any]]:
    if not keys:
        return {}
    try:
        with _connect(settings) as conn:
            rows = conn.execute(
                "SELECT * FROM rft_estimate_predictions WHERE jira_ticket_id = ANY(%s)",
                (keys,),
            ).fetchall()
        return {r["jira_ticket_id"]: r for r in rows}
    except Exception as exc:  # noqa: BLE001
        LOGGER.debug("prediction cache read skipped: %s", exc)
        return {}


def _store(settings: Settings, key: str, h: str, ticket: dict[str, Any], pred: dict[str, Any]) -> None:
    try:
        with _connect(settings) as conn:
            conn.execute(
                """
                INSERT INTO rft_estimate_predictions
                    (jira_ticket_id, content_hash, original_seconds,
                     predicted_hours, confidence, reason, explanation, flag, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (jira_ticket_id) DO UPDATE SET
                    content_hash     = EXCLUDED.content_hash,
                    original_seconds = EXCLUDED.original_seconds,
                    predicted_hours  = EXCLUDED.predicted_hours,
                    confidence       = EXCLUDED.confidence,
                    reason           = EXCLUDED.reason,
                    explanation      = EXCLUDED.explanation,
                    flag             = EXCLUDED.flag,
                    updated_at       = NOW()
                """,
                (
                    key,
                    h,
                    ticket.get("estimate_seconds"),
                    pred.get("predicted_hours"),
                    pred.get("confidence"),
                    pred.get("reason"),
                    pred.get("explanation"),
                    pred.get("flag"),
                ),
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        LOGGER.debug("prediction cache write skipped for %s: %s", key, exc)


def _codebase_context(settings: Settings, ticket: dict[str, Any]) -> str:
    """Best-effort codebase context from repograph; '' if unavailable."""
    try:
        from app.graph_context import GraphContextClient

        ctx = GraphContextClient(settings).fetch_context(ticket_data=ticket)
        items = ctx.get("items", []) or []
        if not items:
            return ""
        text = json.dumps(items, ensure_ascii=False)
        return text[:2500]
    except Exception as exc:  # noqa: BLE001
        LOGGER.debug("codebase context unavailable for %s: %s", ticket.get("key"), exc)
        return ""


def _flag(predicted_seconds: float, original_seconds: float, threshold_pct: int) -> tuple[str, float]:
    if not original_seconds:
        return "n/a", 0.0
    delta_pct = (predicted_seconds - original_seconds) / original_seconds * 100.0
    if delta_pct > threshold_pct:
        return "UNDER", delta_pct      # original estimate too low — needs more time
    if delta_pct < -threshold_pct:
        return "OVER", delta_pct       # original estimate too high
    return "OK", delta_pct


def _predict_one(settings, llm, ticket: dict[str, Any]) -> Optional[dict[str, Any]]:
    context = _codebase_context(settings, ticket)
    user = json.dumps(
        {
            "ticket": {
                "key": ticket.get("key"),
                "summary": ticket.get("summary"),
                "description": (ticket.get("description") or "")[:4000],
                "issue_type": ticket.get("issue_type"),
                "original_estimate": ticket.get("estimate"),
            },
            "codebase_context": context or "none available",
        },
        ensure_ascii=False,
    )
    try:
        raw = llm.complete(_SYSTEM_PROMPT, user, max_tokens=400)
        parsed = parse_model_json(raw)
        hours = float(parsed.get("predicted_hours"))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("estimate prediction failed for %s: %s", ticket.get("key"), exc)
        return None
    return {
        "predicted_hours": round(hours, 2),
        "confidence": str(parsed.get("confidence", "")).lower()[:10],
        "reason": str(parsed.get("reason", ""))[:140],
        "explanation": str(parsed.get("explanation", ""))[:400],
    }


def analyze_tickets(settings: Settings, tickets: list[dict[str, Any]]) -> dict[str, Any]:
    """Enrich each ticket in place with predicted_hours/predicted/delta_pct/flag.

    Returns {"analyzed": int, "flagged": int, "llm": bool}. Never raises — on any
    failure the ticket simply carries no prediction (flag 'n/a').
    """
    threshold = settings.rft_estimate_flag_threshold_pct
    if not settings.database_url:
        # Cache needs a DB; we can still analyze live but won't persist.
        LOGGER.info("rft analysis: no DATABASE_URL — predictions will not be cached")
    else:
        ensure_predictions_schema(settings)

    cache = _load_cache(settings, [t["key"] for t in tickets])

    try:
        llm = build_llm_client(settings)
        llm_ok = True
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("rft analysis: LLM unavailable (%s); listing without predictions", exc)
        llm = None
        llm_ok = False

    analyzed = 0
    flagged = 0
    budget = settings.rft_estimate_max_analyze

    for ticket in tickets:
        key = ticket["key"]
        h = _content_hash(ticket)
        pred: Optional[dict[str, Any]] = None

        cached = cache.get(key)
        if cached and cached.get("content_hash") == h and cached.get("predicted_hours") is not None:
            pred = {
                "predicted_hours": float(cached["predicted_hours"]),
                "confidence": cached.get("confidence") or "",
                "reason": cached.get("reason") or "",
                "explanation": cached.get("explanation") or "",
            }
        elif llm_ok and budget > 0:
            pred = _predict_one(settings, llm, ticket)
            budget -= 1

        if pred is None:
            ticket["predicted_hours"] = None
            ticket["predicted"] = "—"
            ticket["delta_pct"] = None
            ticket["flag"] = "n/a"
            ticket["confidence"] = ""
            ticket["reason"] = ""
            ticket["explanation"] = ""
            continue

        predicted_seconds = pred["predicted_hours"] * 3600.0
        flag, delta_pct = _flag(predicted_seconds, float(ticket["estimate_seconds"]), threshold)
        ticket["predicted_hours"] = pred["predicted_hours"]
        ticket["predicted"] = _fmt_hours(pred["predicted_hours"])
        ticket["delta_pct"] = round(delta_pct)
        ticket["flag"] = flag
        ticket["confidence"] = pred["confidence"]
        ticket["reason"] = pred["reason"]
        ticket["explanation"] = pred["explanation"]
        analyzed += 1
        if flag in ("UNDER", "OVER"):
            flagged += 1

        if settings.database_url and not (cached and cached.get("content_hash") == h):
            _store(settings, key, h, ticket, {**pred, "flag": flag})

    return {"analyzed": analyzed, "flagged": flagged, "llm": llm_ok}


def _fmt_hours(hours: float) -> str:
    """Compact 'Xd Yh' using Jira's 8h working day."""
    seconds = int(round(hours * 3600))
    if seconds <= 0:
        return "0h"
    parts: list[str] = []
    for label, size in (("w", 5 * 8 * 3600), ("d", 8 * 3600), ("h", 3600), ("m", 60)):
        if seconds >= size:
            qty, seconds = divmod(seconds, size)
            parts.append(f"{qty}{label}")
    return " ".join(parts[:2]) or "0h"

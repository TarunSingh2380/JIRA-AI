"""Phase H — RCA pipeline orchestration (read-only end to end).

Ties the phases together for one Jira key:
  C intake → similar tickets → D localize → ensure fix links →
  E retrieve → F agent investigation → G synthesize → ownership (git blame) →
  delivery decision (deliver vs low_confidence) → optional Jira comment (dry-run).

Nothing here writes to a repo, runs code, or applies a change.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.config import Settings
from app.rca import (
    agent, fix_links, intake as intake_mod, localize, repos as repo_access,
    retrieval, synthesis,
)
from app.rca.store import (
    RCARun, RCARunStore, STATUS_DELIVERED, STATUS_FAILED, STATUS_INVESTIGATING,
    STATUS_LOW_CONFIDENCE, STATUS_SYNTHESIZING,
)

log = logging.getLogger(__name__)


def _similar_ticket_keys(settings: Settings, summary: str, description: str,
                         project_key: str, limit: int = 5) -> list[str]:
    try:
        from app.similar_ticket_finder import SimilarTicketFinder
        finder = SimilarTicketFinder(settings)
        res = finder.find_similar(summary, description, project_key=project_key)
        return [t.get("ticket_key") for t in res.get("tickets", []) if t.get("ticket_key")][:limit]
    except Exception as exc:
        log.warning("similar-ticket lookup failed: %s", exc)
        return []


def _ownership_from_blame(settings: Settings, root_cause: dict[str, Any]) -> dict[str, Any]:
    """Derive Original Developer from git blame on the root-cause lines."""
    repo, path, lines = root_cause.get("repo"), root_cause.get("file"), root_cause.get("lines")
    if not (repo and path and lines):
        return {}
    try:
        start, _, end = str(lines).partition("-")
        s = int(start.strip())
        e = int(end.strip()) if end.strip() else s
        blame = repo_access.git_blame(settings, repo, path, s, e)
    except Exception:
        return {}
    if not blame:
        return {}
    # most frequent author across the blamed lines
    authors: dict[str, int] = {}
    for b in blame:
        a = b.get("author") or ""
        if a:
            authors[a] = authors.get(a, 0) + 1
    if not authors:
        return {}
    original = max(authors, key=authors.get)
    last = blame[-1]
    return {"original_developer": original, "last_commit_sha": last.get("sha"),
            "blame_lines": f"{path}:{s}-{e}"}


def run_pipeline(
    settings: Settings,
    store: RCARunStore,
    run: RCARun,
    *,
    intake_client: Any = None,
    synthesis_client: Any = None,
) -> RCARun:
    """Execute the full RCA pipeline for an already-created run. Read-only."""
    try:
        store.touch(run, status=STATUS_INVESTIGATING)

        # ── C: intake & extraction ──────────────────────────────────────────
        ticket_obj = intake_mod.fetch_ticket(settings, run.jira_key)
        extracted = intake_mod.extract_signals(settings, ticket_obj, llm_client=intake_client)
        ticket = ticket_obj.to_dict()
        project_key = run.jira_key.rsplit("-", 1)[0] if "-" in run.jira_key else run.jira_key
        query_text = f"{ticket_obj.summary}\n{ticket_obj.description}".strip()

        # ── similar tickets (signal for D & E) ──────────────────────────────
        similar_keys = _similar_ticket_keys(
            settings, ticket_obj.summary, ticket_obj.description, project_key)
        # ensure their fix links exist for the retrieval signal
        for key in similar_keys:
            if not fix_links.get_links(settings, key):
                fix_links.link_ticket(settings, key)

        # ── D: localize ─────────────────────────────────────────────────────
        candidates_repos = localize.localize(
            settings, ticket_key=run.jira_key, components=ticket_obj.components,
            project_key=project_key, query_text=query_text,
            similar_ticket_keys=similar_keys,
        )
        run.localized_repos = [
            {"repo": c.repo, "score": round(c.score, 3), "reasons": c.reasons}
            for c in candidates_repos
        ]
        repo_names = [c.repo for c in candidates_repos] or repo_access.list_repos(settings)[:3]
        store.touch(run)

        # ── E: hybrid retrieval ─────────────────────────────────────────────
        candidates = retrieval.retrieve(
            settings, repos=repo_names,
            error_messages=extracted.get("error_messages", []),
            stack_frames=extracted.get("stack_frames", []),
            query_text=query_text, similar_ticket_keys=similar_keys,
        )
        run.candidates = [c.to_dict() for c in candidates]
        store.touch(run)

        # ── F: agentic investigation (read-only) ────────────────────────────
        agent_res = agent.run_investigation(
            settings, ticket_summary=ticket_obj.summary, extracted=extracted,
            candidates=run.candidates, allowed_repos=repo_names,
            on_event=lambda ev: store.add_trace_event(run, ev),
        )
        run.agent_trace = agent_res.agent_trace
        store.touch(run, status=STATUS_SYNTHESIZING)

        # ── G: synthesis ────────────────────────────────────────────────────
        diagnosis = synthesis.synthesize(
            settings, ticket=ticket, extracted=extracted, candidates=run.candidates,
            investigation=agent_res.summary, trace=run.agent_trace,
            llm_client=synthesis_client,
        )
        diagnosis["ownership"] = _ownership_from_blame(settings, diagnosis.get("root_cause", {}))
        run.diagnosis = diagnosis
        run.confidence = diagnosis.get("confidence")

        # ── build the house-template document ───────────────────────────────
        from app.rca import rca_document
        run.document = rca_document.build_document(ticket, extracted, diagnosis,
                                                   agent_meta={
                                                       "iterations": agent_res.iterations,
                                                       "stop_reason": agent_res.stop_reason,
                                                   })

        # ── delivery decision ───────────────────────────────────────────────
        deliver = (run.confidence or 0.0) >= settings.rca_confidence_threshold
        final_status = STATUS_DELIVERED if deliver else STATUS_LOW_CONFIDENCE
        store.touch(run, status=final_status)

        if deliver and settings.rca_jira_post_enabled:
            _post_to_jira(settings, run)

        log.info("RCA run %s finished: status=%s confidence=%s",
                 run.run_id, final_status, run.confidence)
        return run

    except Exception as exc:  # surface failure on the run, never crash the worker
        log.exception("RCA run %s failed", run.run_id)
        run.error = f"{type(exc).__name__}: {exc}"[:1000]
        store.touch(run, status=STATUS_FAILED)
        return run


def _post_to_jira(settings: Settings, run: RCARun) -> None:
    """Post the diagnosis as a Jira comment (only when explicitly enabled)."""
    try:
        from app.rca import rca_document
        body = rca_document.render_markdown(run.document)
        from app.jira_client import JiraClient  # existing client
        JiraClient(settings).add_comment(run.jira_key, body)
        log.info("RCA diagnosis posted to Jira %s", run.jira_key)
    except Exception as exc:
        log.warning("RCA Jira post failed for %s: %s", run.jira_key, exc)

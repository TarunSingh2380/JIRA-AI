"""Orchestrate a Neo4j graph build for the active repositories.

Selects active repos (activity score >= threshold) from the same discovery used
by the Repositories tab, optionally restricted to an explicit name list, then
writes the git + code layers. Emits progress events so a background job can
surface live status to the admin UI.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from app.config import settings
from app.repository_discovery import discover_graph_repositories

from .code_layer import build_code_layer
from .config import GraphBuildConfig
from .git_layer import build_git_layer
from .writer import Neo4jWriter

log = logging.getLogger(__name__)

ProgressFn = Callable[[dict[str, Any]], None]

WipeMode = str  # "all" | "managed" | "none"


def select_active_repositories(
    cfg: GraphBuildConfig,
    selected_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    repos = discover_graph_repositories(settings)
    active = [r for r in repos if (r.get("activity_score") or 0) >= cfg.activity_min_score]
    if selected_names:
        wanted = {n for n in selected_names}
        active = [r for r in active if r.get("name") in wanted]
    active.sort(key=lambda r: r.get("activity_score") or 0, reverse=True)
    return active


def build_graph(
    *,
    cfg: GraphBuildConfig | None = None,
    selected_names: list[str] | None = None,
    wipe_mode: WipeMode = "managed",
    include_code: bool = True,
    progress: ProgressFn | None = None,
) -> dict[str, Any]:
    cfg = cfg or GraphBuildConfig.from_settings()
    emit = progress or (lambda _e: None)

    if not cfg.neo4j_password:
        raise RuntimeError("NEO4J_PASSWORD is not configured on the server.")

    active = select_active_repositories(cfg, selected_names)
    emit({"phase": "discovery", "level": "info", "repos_total": len(active),
          "message": f"{len(active)} active repositories selected"})
    if not active:
        return {"repositories": 0, "counts": {}, "repo_names": []}

    started = time.time()
    with Neo4jWriter(
        uri=cfg.neo4j_uri, user=cfg.neo4j_user, password=cfg.neo4j_password,
        database=cfg.neo4j_database, batch_size=cfg.write_batch_size,
    ) as writer:
        writer.verify()
        emit({"phase": "connect", "level": "info",
              "message": f"Connected to Neo4j at {cfg.neo4j_uri}"})

        if wipe_mode == "all":
            emit({"phase": "wipe", "level": "info", "message": "Wiping entire database…"})
            writer.wipe_all()
        elif wipe_mode == "managed":
            emit({"phase": "wipe", "level": "info",
                  "message": "Wiping managed labels (preserving Jira/embeddings)…"})
            writer.wipe(cfg.managed_labels)
        writer.ensure_schema()

        total = len(active)
        for idx, repo in enumerate(active, start=1):
            name = repo.get("name", "repo")
            emit({"phase": "repository", "level": "info", "repo": name,
                  "repos_done": idx - 1, "repos_total": total,
                  "message": f"Building {name} ({idx}/{total})"})
            tracked = build_git_layer(writer, repo, cfg)
            if include_code:
                build_code_layer(writer, repo, tracked, cfg)
            emit({"phase": "repository_done", "level": "info", "repo": name,
                  "repos_done": idx, "repos_total": total,
                  "message": f"Finished {name} ({idx}/{total})"})

        counts = dict(writer.counts)

    elapsed = round(time.time() - started, 1)
    emit({"phase": "done", "level": "info", "repos_done": len(active),
          "repos_total": len(active),
          "message": f"Graph build finished in {elapsed}s ({len(active)} repos)"})
    return {
        "repositories": len(active),
        "repo_names": [r.get("name") for r in active],
        "counts": counts,
        "elapsed_seconds": elapsed,
    }

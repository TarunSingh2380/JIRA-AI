"""Discover top-level local Git repositories for graph build workflows."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

from app.config import Settings

log = logging.getLogger(__name__)


def discover_graph_repositories(settings: Settings) -> list[dict[str, Any]]:
    root = Path(settings.repository_search_root).expanduser().resolve()
    host_root = Path(settings.repository_host_root)
    excluded_names = {
        name.strip()
        for name in settings.excluded_repository_names.split(",")
        if name.strip()
    }

    log.info("Discovering repositories under %s (excluded: %s)", root, excluded_names or "none")

    repositories: list[dict[str, Any]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue

        if child.name.startswith(".") or child.name in excluded_names:
            log.debug("Skipping directory: %s", child.name)
            continue

        if _is_git_repository(child):
            host_path = host_root / child.name
            repositories.append(_repository_info(scan_path=child, host_path=host_path))
            log.debug("Found git repository: %s", child.name)

    repositories.sort(key=lambda repo: repo["path"])
    log.info("Discovered %d repositories", len(repositories))
    return repositories


def _is_git_repository(path: Path) -> bool:
    return (path / ".git").exists()


def _repository_info(*, scan_path: Path, host_path: Path) -> dict[str, Any]:
    remote_url = _git(scan_path, "config", "--get", "remote.origin.url")
    branch = _git(scan_path, "rev-parse", "--abbrev-ref", "HEAD")
    current_commit = _git(scan_path, "rev-parse", "HEAD")
    return {
        "name": scan_path.name,
        "path": str(host_path),
        "container_path": str(scan_path),
        "local_clone_available": True,
        "remote_url": remote_url or "",
        "branch": branch or "",
        "current_commit": current_commit or "",
        "pull_command": f"git -C {host_path} pull --ff-only",
    }


def _git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=path,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None
    return result.stdout.strip() or None

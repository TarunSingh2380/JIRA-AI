"""Discover top-level local Git repositories for graph build workflows."""

from __future__ import annotations

import logging
import math
import subprocess
import time
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
        **_git_activity(scan_path),
    }


# Window (days) over which commit frequency is measured for the activity score.
_ACTIVITY_WINDOW_DAYS = 90
# Recency decay half-life (days): a repo whose last commit is this old keeps half
# of the recency portion of its score.
_RECENCY_HALFLIFE_DAYS = 30
# Commits within the window that earn the full frequency portion of the score.
_FREQUENCY_SATURATION = 25


def _git_activity(path: Path) -> dict[str, Any]:
    """Compute a 0-100 activity score plus the raw signals behind it.

    The score blends recency (how long since the last commit, decayed
    exponentially) and frequency (commit volume over a recent window) so that a
    repo someone touched once long ago scores low while one under steady
    development scores high.
    """
    now = time.time()

    last_raw = _git(path, "log", "-1", "--format=%ct")
    last_ts = int(last_raw) if last_raw and last_raw.isdigit() else None

    # One log call covers the whole window; we derive 30/90-day counts and the
    # distinct-author count from it instead of issuing several git invocations.
    since = f"{_ACTIVITY_WINDOW_DAYS} days ago"
    log_raw = _git(path, "log", f"--since={since}", "--format=%ct|%ae") or ""
    commits_90d = 0
    commits_30d = 0
    authors: set[str] = set()
    cutoff_30d = now - 30 * 86400
    for line in log_raw.splitlines():
        ts_str, _, author = line.partition("|")
        if not ts_str.isdigit():
            continue
        commits_90d += 1
        if int(ts_str) >= cutoff_30d:
            commits_30d += 1
        if author:
            authors.add(author)

    if last_ts is None:
        days_since_last = None
        recency = 0.0
    else:
        days_since_last = max(0.0, (now - last_ts) / 86400)
        recency = 60.0 * math.pow(0.5, days_since_last / _RECENCY_HALFLIFE_DAYS)

    frequency = 40.0 * min(1.0, commits_90d / _FREQUENCY_SATURATION)
    score = int(round(recency + frequency))

    return {
        "activity_score": score,
        "last_commit_ts": last_ts,
        "last_commit_days": round(days_since_last, 1) if days_since_last is not None else None,
        "commits_30d": commits_30d,
        "commits_90d": commits_90d,
        "authors_90d": len(authors),
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

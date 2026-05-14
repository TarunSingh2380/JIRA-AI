"""Local-filesystem repo discovery.

Replaces the GitHub-API-based discovery from the original design.

We walk SEARCH_ROOT looking for directories that contain a `.git` subdirectory
(or `.git` file pointing at one — gitlink/worktree case). For each, we extract
the metadata we can from the local clone alone:

  - full_name        from `git config --get remote.origin.url` (or repo path if no remote)
  - name             basename of the repo dir
  - owner            owner inferred from remote URL
  - default_branch   from `git symbolic-ref refs/remotes/origin/HEAD`, fallback to 'main'
  - private          unknown locally → set None (or fold into 'unknown')
  - language         not derivable without language detection; left None for Stage 1
  - description      not available locally; left None

No network calls. No tokens. Fully offline.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import settings

log = logging.getLogger(__name__)


@dataclass(slots=True)
class RepoInfo:
    full_name: str          # "owner/name" if we can parse the remote; else dir-path-derived
    name: str               # basename
    owner: str              # parsed from remote URL, or 'local' if no remote
    default_branch: str
    private: Optional[bool] # always None in local mode — we just don't know
    language: Optional[str] # None in local mode
    description: Optional[str]
    url: Optional[str]      # the remote URL if present
    clone_url: Optional[str]
    local_path: Path        # where the repo actually lives on disk


# ─── Discovery ───────────────────────────────────────────────────────────

def discover_repos(
    root: Path,
    *,
    max_depth: int = 3,
    skip_dirs: Optional[set[str]] = None,
) -> list[RepoInfo]:
    """Walk `root` looking for git repos.

    A "git repo" is any directory containing either a `.git/` subdir (normal clone)
    or a `.git` file (gitlink / worktree). We don't descend into a repo once found.
    """
    skip_dirs = skip_dirs or set()
    root = root.resolve()
    found: list[RepoInfo] = []
    seen_paths: set[Path] = set()

    def walk(dir_path: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = list(dir_path.iterdir())
        except (PermissionError, OSError) as e:
            log.debug("Cannot list %s: %s", dir_path, e)
            return

        # Is THIS directory a git repo? (.git as dir or file)
        if _is_git_repo(dir_path):
            if dir_path in seen_paths:
                return
            seen_paths.add(dir_path)
            info = _read_repo_metadata(dir_path)
            if info is not None:
                found.append(info)
            return  # don't descend into a repo's children

        for entry in entries:
            # is_dir without following symlinks (compatible across 3.9–3.12)
            try:
                if not entry.is_dir() or entry.is_symlink():
                    continue
            except OSError:
                continue
            if entry.name.startswith(".") and entry.name != ".":
                continue
            if entry.name in skip_dirs:
                continue
            walk(entry, depth + 1)

    walk(root, 0)
    log.info("Discovered %d git repositories under %s", len(found), root)
    return found


def _is_git_repo(path: Path) -> bool:
    """True if `path` is the root of a git working tree."""
    git_path = path / ".git"
    if not git_path.exists():
        return False
    # `.git` can be a directory (normal) or a file (worktree gitlink). Both count.
    return True


def _git(args: list[str], cwd: Path) -> Optional[str]:
    """Run a git command and return stdout (trimmed), or None on failure."""
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            timeout=15,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


# Matches:
#   https://github.com/owner/name.git
#   https://github.com/owner/name
#   git@github.com:owner/name.git
#   git@github.com:owner/name
#   ssh://git@github.com/owner/name(.git)
_REMOTE_PATTERNS = [
    re.compile(r"^https?://[^/]+/(?P<owner>[^/]+)/(?P<name>[^/]+?)(?:\.git)?/?$"),
    re.compile(r"^git@[^:]+:(?P<owner>[^/]+)/(?P<name>[^/]+?)(?:\.git)?/?$"),
    re.compile(r"^ssh://[^/]+/(?P<owner>[^/]+)/(?P<name>[^/]+?)(?:\.git)?/?$"),
]


def _parse_remote_url(url: str) -> Optional[tuple[str, str]]:
    """Return (owner, name) parsed from a git remote URL, or None."""
    for pat in _REMOTE_PATTERNS:
        m = pat.match(url)
        if m:
            return m.group("owner"), m.group("name")
    return None


def _read_repo_metadata(repo_path: Path) -> Optional[RepoInfo]:
    """Extract the metadata we can from a local repo, no network."""
    # Remote URL — optional but useful
    remote_url = _git(["config", "--get", "remote.origin.url"], repo_path)
    owner = "local"
    name = repo_path.name
    if remote_url:
        parsed = _parse_remote_url(remote_url)
        if parsed:
            owner, name = parsed

    # Default branch — try in this order:
    # 1. origin/HEAD symbolic ref (most reliable)
    # 2. main / master existence
    # 3. fallback to 'main'
    default_branch = "main"
    head_ref = _git(["symbolic-ref", "refs/remotes/origin/HEAD"], repo_path)
    if head_ref and head_ref.startswith("refs/remotes/origin/"):
        default_branch = head_ref[len("refs/remotes/origin/"):]
    else:
        for candidate in ("main", "master", "develop"):
            if _git(["rev-parse", "--verify", "--quiet", candidate], repo_path) is not None:
                default_branch = candidate
                break

    # full_name: prefer owner/name from URL; else dir-path-derived
    full_name = f"{owner}/{name}" if remote_url else f"local/{name}"

    return RepoInfo(
        full_name=full_name,
        name=name,
        owner=owner,
        default_branch=default_branch,
        private=None,
        language=None,
        description=None,
        url=remote_url,
        clone_url=remote_url,
        local_path=repo_path,
    )


# Convenience wrapper for the runner.
def discover_from_settings() -> list[RepoInfo]:
    return discover_repos(
        settings.search_root,
        max_depth=settings.max_search_depth,
        skip_dirs=settings.skip_dir_set,
    )

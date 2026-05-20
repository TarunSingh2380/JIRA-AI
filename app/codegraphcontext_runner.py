"""CodeGraphContext integration helpers.

CGC provides a richer tree-sitter based code graph than our lightweight local
parser. We run it as a CLI subprocess so the integration stays isolated from
our app lifecycle and can be disabled if the package is unavailable.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

from app.config import settings


async def index_repository_with_codegraphcontext(repo: dict[str, Any]) -> tuple[bool, str]:
    """Index one repository with CodeGraphContext into the configured Neo4j DB."""
    repo_path = repo.get("container_path") or repo.get("path")
    if not repo_path:
        return False, "repository path missing"
    if not Path(repo_path).exists():
        return False, f"repository path not found: {repo_path}"

    command = [
        "codegraphcontext",
        "--database",
        "neo4j",
        "index",
        str(repo_path),
        "--force",
    ]
    env = {
        **os.environ,
        "DEFAULT_DATABASE": "neo4j",
        "NEO4J_URI": settings.neo4j_uri,
        "NEO4J_USERNAME": settings.neo4j_user,
        "NEO4J_PASSWORD": settings.neo4j_password,
        "NEO4J_DATABASE": settings.neo4j_database,
        "LIBRARY_LOG_LEVEL": "WARNING",
    }

    try:
        result = await asyncio.to_thread(
            subprocess.run,
            command,
            cwd=repo_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=settings.codegraphcontext_timeout_seconds,
        )
    except FileNotFoundError:
        return False, "codegraphcontext CLI not installed"
    except subprocess.TimeoutExpired as exc:
        return False, f"CodeGraphContext indexing timed out after {exc.timeout}s"
    except Exception as exc:
        return False, str(exc)

    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if result.returncode != 0:
        return False, output[-4000:] or f"codegraphcontext exited with {result.returncode}"
    return True, output[-4000:] or "CodeGraphContext indexing completed"

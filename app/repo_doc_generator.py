"""Generate repository documentation (onboarding guide, architecture overview).

The document is grounded in the same RepoTree artifacts the test-case pipeline
uses: the per-repo architecture map (`per_repo/<name>.md`) and the Repomix packed
source (`packed/<name>.xml`). Both are fed to the in-process LLM with a
document-specific prompt, so the output cites real files, routes, tables, env keys,
and dependencies instead of inventing them.
"""
from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable

from app.repo_tree_integration import repo_tree_runtime

log = logging.getLogger(__name__)

# How much packed-source context to feed the model. ~450K chars ≈ ~110K tokens,
# comfortably inside the model context window alongside the arch map and prompt.
_PACKED_CONTEXT_MAX_CHARS = 450_000
_DIRECTORY_PREVIEW_MAX_CHARS = 24_000
_DOC_MAX_OUTPUT_TOKENS = 16_000


# ============================================================
# Document type registry
# ============================================================

_ONBOARDING_SYSTEM = dedent("""
    You are a senior staff engineer writing an authoritative onboarding guide for a
    repository that a brand-new developer has never seen. You work ONLY from the
    repository context provided (its architecture map and packed source). Every fact
    must be grounded in a real file, route, table, env key, dependency, or config
    value visible in that context. Do not invent endpoints, tables, env vars, or
    behaviour. If something is ambiguous or missing, say so explicitly rather than
    guessing.

    While reading, actively hunt for INCONSISTENCIES and record them (these are high
    value to a new dev): dependencies installed but never instantiated; routes or
    cron jobs that are commented out; scripts that reference files (docker-compose,
    migrations, .env.example) that do not exist; route files present but not mounted;
    two competing approaches for the same concern.

    OUTPUT: Markdown only. Start with:

        # Onboarding Guide - <repo name>

        **Repository:** `<repo name>`
        **Updated:** <today's date YYYY-MM-DD>

    Then produce these sections IN THIS ORDER. Adapt section names to the repo's
    actual stack, but keep the intent and the table-driven style. Prefer tables over
    prose. Keep entries concrete and short.

    1. ## Purpose — 2-4 sentences: what this service owns in business terms, and
       whether it is a simple CRUD API or a stateful workflow engine.
    2. ## Specific Modules And Packages — table | Area | Module or package | Purpose |
       citing real package names AND real file paths.
    3. ## Local Setup — numbered steps (runtime version, install, .env creation —
       note if no committed `.env.example` exists, run command, health-check) plus a
       table | Dependency | Required for | Important env keys | using REAL env names.
    4. ## Setup Inconsistencies And Resolution — table | Inconsistency | Where it
       appears | Impact | Recommended resolution |. If genuinely none, say so.
    5. ## Running Migrations — real migration commands and where migrations live;
       note if the directory is empty/absent.
    6. Active Route Modules — table of only the modules actually mounted/registered.
    7. ## Request Format Conventions — auth/content-type conventions per client type,
       with short `http` snippets.
    8. Public surface — list EVERY entry in the repo's public surface, grouped into
       `###` subsections, each a table | Method | Endpoint | Sample format |
       High-level purpose |. For an HTTP API these are REST endpoints; for a frontend
       use routes/pages; for a CLI use commands; for a library use exported API. Add a
       `### Not Currently Mounted` table for files/blocks that exist but are commented
       out or unmounted.
    9. ## Application Schedulers And Queues — table | Scheduler or queue | Code
       location | Current state | What it does |. Distinguish active vs installed-
       but-unused.
    10. ## Database Tables And Collections — table grouped BY PURPOSE |
        Purpose | Tables or collections | Notes | using real model/table names.
    11. ## Major Features And Working Description — table | Feature | Primary modules
        | How it works | naming real route/controller/service/table files.
    12. ## Other Services And Integrations — table | Service | Module/config | Used
        for | Recommendation | for every external/sister-service dependency.
    13. ## Feature Entry Points — table | Task | Start here | with concrete file paths.
    14. ## Troubleshooting — table | Symptom | Check | tying failures back to the
        specific files/env/services and to the inconsistencies found.

    Reference env KEY NAMES only, never values. Be exhaustive on endpoints and
    tables; be terse in wording. If a section does not apply to this repo's stack,
    replace it with the closest equivalent and note why. Choose one concrete `##`
    heading per section that fits the stack; never copy the parenthetical guidance
    above literally into a heading.
""").strip()


_ARCHITECTURE_SYSTEM = dedent("""
    You are a principal engineer writing an architecture overview of a repository for
    engineers who need to reason about how it is built. Work ONLY from the provided
    repository context (architecture map and packed source). Ground every statement
    in real files, modules, routes, tables, or dependencies. Do not invent anything;
    flag gaps explicitly.

    OUTPUT: Markdown only. Start with:

        # Architecture Overview - <repo name>

        **Repository:** `<repo name>`
        **Updated:** <today's date YYYY-MM-DD>

    Then produce these sections IN THIS ORDER, table-driven where possible and terse:

    1. ## System Summary — what the service does and its role in the wider system.
    2. ## Tech Stack — table | Layer | Technology | Where used | (language, framework,
       datastores, queues, key libraries) citing real packages/files.
    3. ## High-Level Architecture — the main components/layers and how a request or
       job flows through them end to end (entry point → middleware → controller →
       service → data/integrations). Reference real file paths.
    4. ## Module Map — table | Module / directory | Responsibility | Key files |.
    5. ## Data Stores And Models — datastores used and the main tables/collections
       grouped by purpose, with real names.
    6. ## External Integrations And Sister Services — table | Integration | Module /
       config | Purpose |.
    7. ## Async Processing — schedulers, queues, workers, and background jobs;
       distinguish active vs installed-but-unused.
    8. ## Cross-Cutting Concerns — auth, validation, logging/observability, error
       handling, configuration — naming the real modules that implement each.
    9. ## Architectural Risks And Inconsistencies — table | Risk / inconsistency |
       Evidence | Impact | Suggested action |.
    10. ## Extension Points — where and how to safely add new functionality.

    Reference env KEY NAMES only, never values. Be concrete and grounded.
""").strip()


_DOC_TYPES: dict[str, dict[str, Any]] = {
    "onboarding_guide": {
        "label": "Onboarding Guide",
        "system": _ONBOARDING_SYSTEM,
        "filename": "ONBOARDING_GUIDE",
    },
    "architecture_overview": {
        "label": "Architecture Overview",
        "system": _ARCHITECTURE_SYSTEM,
        "filename": "ARCHITECTURE_OVERVIEW",
    },
}


def list_document_types() -> list[dict[str, str]]:
    return [{"id": key, "label": spec["label"]} for key, spec in _DOC_TYPES.items()]


# ============================================================
# Repo discovery (only repos with usable RepoTree artifacts)
# ============================================================

def list_doc_repositories() -> list[dict[str, Any]]:
    """Return configured repos that have an architecture map and/or packed source."""
    state = repo_tree_runtime()
    cfg = state.config
    repos: list[dict[str, Any]] = []
    for repo in cfg.repos:
        arch = cfg.per_repo_dir / f"{repo.name}.md"
        packed = cfg.packed_dir / f"{repo.name}.xml"
        has_arch = arch.exists()
        has_packed = packed.exists()
        repos.append(
            {
                "name": repo.name,
                "description": repo.description or "",
                "has_architecture_map": has_arch,
                "has_packed_source": has_packed,
                "ready": has_arch or has_packed,
            }
        )
    repos.sort(key=lambda r: (not r["ready"], r["name"].lower()))
    return repos


# ============================================================
# Context building from RepoTree artifacts
# ============================================================

def _load_architecture_map(per_repo_dir: Path, name: str) -> str:
    f = per_repo_dir / f"{name}.md"
    if not f.exists():
        return ""
    try:
        return f.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _load_packed_context(packed_dir: Path, name: str, *, max_chars: int) -> str:
    """Build a context blob from a Repomix packed XML: directory structure followed
    by as many full file blocks as fit within `max_chars`."""
    packed = packed_dir / f"{name}.xml"
    if not packed.exists():
        return ""
    try:
        text = packed.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    parts: list[str] = []
    budget = max_chars

    dir_match = re.search(r"<directory_structure>\s*(.*?)\s*</directory_structure>", text, re.S)
    if dir_match:
        structure = dir_match.group(1).strip()[:_DIRECTORY_PREVIEW_MAX_CHARS]
        block = f"## Directory Structure\n```text\n{structure}\n```"
        parts.append(block)
        budget -= len(block)

    parts.append("## Source Files")
    for match in re.finditer(r'<file path="([^"]+)">(.*?)</file>', text, re.S):
        if budget <= 0:
            parts.append("\n_(remaining files omitted to fit the context budget)_")
            break
        path = match.group(1)
        body = match.group(2).strip()
        block = f"\n### {path}\n```\n{body}\n```"
        if len(block) > budget:
            block = block[:budget] + "\n```\n_(file truncated)_"
            budget = 0
        else:
            budget -= len(block)
        parts.append(block)

    return "\n".join(parts)


def _build_repo_context(cfg: Any, name: str) -> tuple[str, dict[str, int]]:
    arch = _load_architecture_map(cfg.per_repo_dir, name)
    packed = _load_packed_context(cfg.packed_dir, name, max_chars=_PACKED_CONTEXT_MAX_CHARS)
    sections: list[str] = []
    if arch:
        sections.append("# RepoTree Architecture Map\n" + arch)
    if packed:
        sections.append("# Repomix Packed Source\n" + packed)
    context = "\n\n".join(sections)
    stats = {
        "architecture_context_chars": len(arch),
        "packed_context_chars": len(packed),
    }
    return context, stats


# ============================================================
# Entry point
# ============================================================

def generate_repo_document(repo_name: str, doc_type: str = "onboarding_guide") -> tuple[str, str]:
    """Generate a Markdown document for `repo_name`.

    Returns (filename, markdown). Raises ValueError for bad input/missing artifacts.
    """
    spec = _DOC_TYPES.get(doc_type)
    if not spec:
        raise ValueError(
            f"Unknown document type '{doc_type}'. Available: {', '.join(_DOC_TYPES)}"
        )

    state = repo_tree_runtime()
    cfg = state.config
    valid_names = {r.name for r in cfg.repos}
    if repo_name not in valid_names:
        raise ValueError(
            f"Repository '{repo_name}' is not configured in RepoTree. "
            f"Configured repos: {', '.join(sorted(valid_names))}"
        )

    context, stats = _build_repo_context(cfg, repo_name)
    if not context.strip():
        raise ValueError(
            f"No architecture map or packed source found for '{repo_name}'. "
            f"Run /scan/initial and the Repomix reindex for this repo first."
        )

    user = dedent(f"""
        Repository name: {repo_name}
        Today's date: {date.today().isoformat()}

        Use the repository context below as your only source of truth. Produce the
        requested document now.

        ===== REPOSITORY CONTEXT =====
        {context}
    """).strip()

    log.info(
        "Generating %s for repo=%s (arch=%d chars, packed=%d chars)",
        doc_type, repo_name, stats["architecture_context_chars"], stats["packed_context_chars"],
    )
    result = state.llm.complete(
        system=spec["system"],
        user=user,
        cache_system=True,
        max_tokens=_DOC_MAX_OUTPUT_TOKENS,
    )
    markdown = (result.text or "").strip()
    if not markdown:
        raise RuntimeError("The model returned an empty document")

    stamp = date.today().strftime("%Y%m%d")
    filename = f"{spec['filename']}-{repo_name}-{stamp}.md"
    return filename, markdown

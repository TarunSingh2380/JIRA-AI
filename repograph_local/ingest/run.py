"""Stage 1 ingestion runner (local-mode).

Usage:
  python -m ingest.run                       # ingest everything under SEARCH_ROOT
  python -m ingest.run --list                # just list what would be ingested
  python -m ingest.run --only node_crm,ramfincorp-backend  # filter
  python -m ingest.run --fetch-first         # run `git fetch` on each repo first
  python -m ingest.run -v                    # verbose logging
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from config import settings
from ingest.git_history import ingest_repo, make_driver
from ingest.local_repos import RepoInfo, discover_from_settings

console = Console()


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )
    for noisy in ("neo4j", "neo4j.io"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def filter_repos(repos: list[RepoInfo], only: Optional[set[str]]) -> list[RepoInfo]:
    if not only:
        return repos
    return [
        r for r in repos
        if r.name in only or r.full_name in only or str(r.local_path) in only
    ]


def print_repo_table(repos: list[RepoInfo]) -> None:
    t = Table(title=f"Repos under {settings.search_root}  (found {len(repos)})")
    t.add_column("full_name")
    t.add_column("default_branch")
    t.add_column("remote")
    t.add_column("local_path")
    for r in repos:
        t.add_row(
            r.full_name,
            r.default_branch,
            (r.url or "—")[:60],
            str(r.local_path),
        )
    console.print(t)


async def _run(
    *,
    only: Optional[set[str]],
    list_only: bool,
    fetch_first: bool,
) -> int:
    repos = discover_from_settings()
    repos = filter_repos(repos, only)

    if not repos:
        console.print(f"[red]No git repos found under {settings.search_root}[/red]")
        console.print(
            "Check that SEARCH_ROOT in .env points at the right directory, "
            "and that MAX_SEARCH_DEPTH is big enough.",
        )
        return 2

    if list_only:
        print_repo_table(repos)
        return 0

    print_repo_table(repos)
    console.print(
        f"[cyan]Ingesting {len(repos)} repos with concurrency={settings.ingest_concurrency}"
        f"{', fetch-first=ON' if fetch_first else ''}[/cyan]"
    )

    driver = make_driver()
    sem = asyncio.Semaphore(settings.ingest_concurrency)
    total_commits = 0
    total_branches = 0
    failures: list[tuple[str, str]] = []

    async def _one(repo: RepoInfo, advance) -> None:
        nonlocal total_commits, total_branches
        async with sem:
            try:
                stats = await ingest_repo(driver, repo, fetch_first=fetch_first)
                total_commits += stats["commits"]
                total_branches += stats["branches"]
            except Exception as exc:  # noqa: BLE001
                logging.exception("Failed: %s", repo.full_name)
                failures.append((repo.full_name, str(exc)[:200]))
            finally:
                advance()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Ingesting repos", total=len(repos))

        def advance() -> None:
            progress.update(task, advance=1)

        try:
            await asyncio.gather(*(_one(r, advance) for r in repos))
        finally:
            await driver.close()

    console.print()
    console.rule("[bold]Ingest summary[/bold]")
    console.print(f"Repos:    {len(repos) - len(failures)} / {len(repos)} OK")
    console.print(f"Commits:  {total_commits:,}")
    console.print(f"Branches: {total_branches:,}")
    if failures:
        ft = Table(title="Failures")
        ft.add_column("repo")
        ft.add_column("error")
        for name, err in failures:
            ft.add_row(name, err)
        console.print(ft)
        return 1
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Ingest local git repos into Neo4j (Stage 1, local mode).")
    p.add_argument("--only", help="Comma-separated repo names or full_names to limit to")
    p.add_argument("--list", action="store_true", help="List discovered repos and exit")
    p.add_argument("--fetch-first", action="store_true",
                   help="Run `git fetch --all --tags --prune` on each repo before walking")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    setup_logging(args.verbose)
    only = set(s.strip() for s in args.only.split(",")) if args.only else None
    return asyncio.run(_run(only=only, list_only=args.list, fetch_first=args.fetch_first))


if __name__ == "__main__":
    sys.exit(main())

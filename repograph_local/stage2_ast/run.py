"""Stage 2 AST ingestion runner (CGC-backed).

Usage:
  python -m stage2_ast.run                      # all repos under SEARCH_ROOT
  python -m stage2_ast.run --list               # list repos, then exit
  python -m stage2_ast.run --only agrimfincapindia,node_crm
  python -m stage2_ast.run -v                   # verbose logging
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
from ingest.local_repos import RepoInfo, discover_from_settings
from stage2_ast.cgc_bridge import ingest_ast_for_repo

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
    return [r for r in repos if r.name in only or r.full_name in only]


def print_repo_table(repos: list[RepoInfo]) -> None:
    t = Table(title=f"Repos ({len(repos)} found)")
    t.add_column("full_name")
    t.add_column("default_branch")
    t.add_column("local_path")
    for r in repos:
        t.add_row(r.full_name, r.default_branch, str(r.local_path))
    console.print(t)


async def _run(*, only: Optional[set[str]], list_only: bool) -> int:
    repos = discover_from_settings()
    repos = filter_repos(repos, only)

    if not repos:
        console.print(f"[red]No git repos found under {settings.search_root}[/red]")
        return 2

    if list_only:
        print_repo_table(repos)
        return 0

    print_repo_table(repos)
    console.print(
        f"[cyan]Running CGC AST ingest for {len(repos)} repo(s) "
        f"(concurrency={settings.ingest_concurrency})[/cyan]"
    )

    sem = asyncio.Semaphore(settings.ingest_concurrency)
    failures: list[tuple[str, str]] = []
    totals = {"functions": 0, "classes": 0, "calls": 0, "extends": 0, "errors": 0}

    async def _one(repo: RepoInfo, advance) -> None:
        async with sem:
            try:
                result = await ingest_ast_for_repo(settings, repo)
                for key in totals:
                    totals[key] += result.get(key, 0)
            except Exception as exc:
                logging.exception("AST ingest failed: %s", repo.full_name)
                failures.append((repo.full_name, str(exc)[:200]))
            finally:
                advance()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(), MofNCompleteColumn(),
        TaskProgressColumn(), TimeElapsedColumn(),
        console=console, transient=False,
    ) as progress:
        task = progress.add_task("AST ingest", total=len(repos))
        await asyncio.gather(*(_one(r, lambda: progress.update(task, advance=1)) for r in repos))

    console.print()
    console.rule("[bold]AST Ingest Summary[/bold]")
    console.print(f"Repos:     {len(repos) - len(failures)} / {len(repos)} OK")
    console.print(f"Functions: {totals['functions']:,}")
    console.print(f"Classes:   {totals['classes']:,}")
    console.print(f"CALLS:     {totals['calls']:,}")
    console.print(f"EXTENDS:   {totals['extends']:,}")
    console.print(f"Errors:    {totals['errors']:,}")

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
    p = argparse.ArgumentParser(
        description="Stage 2 AST ingest — parse repos with CGC and write to Neo4j."
    )
    p.add_argument("--only", help="Comma-separated repo names or full_names")
    p.add_argument("--list", action="store_true", help="List repos and exit")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    setup_logging(args.verbose)
    only = set(s.strip() for s in args.only.split(",")) if args.only else None
    return asyncio.run(_run(only=only, list_only=args.list))


if __name__ == "__main__":
    sys.exit(main())

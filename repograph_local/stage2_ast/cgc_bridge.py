"""Stage 2 AST bridge — CodeGraphContext (CGC) integration.

Uses CGC's tree-sitter pipeline to parse every source file in a repo and
writes :Function / :Class nodes plus :CALLS / :EXTENDS / :METHOD_OF /
:DEFINED_IN edges into our existing Neo4j schema (Stage-2 labels).

Stage 1 already created :Repo and :File nodes; this module adds the
symbol-level overlay on top of them.

Standalone CLI:
    cd repograph_local
    python -m stage2_ast.run

FastAPI endpoint (added to service/main.py):
    POST /ast/ingest
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

log = logging.getLogger("uvicorn.error")


# ─── Parser helper (no database dependency) ───────────────────────────────────

class _ParserHelper:
    """Thin wrapper around CGC's tree-sitter parsers with no Neo4j coupling."""

    PARSERS: Dict[str, str] = {
        ".py": "python",    ".ipynb": "python",
        ".js": "javascript", ".jsx": "javascript",
        ".mjs": "javascript", ".cjs": "javascript",
        ".ts": "typescript", ".d.ts": "typescript",
        ".tsx": "tsx",      ".go": "go",
        ".rs": "rust",      ".cpp": "cpp",
        ".h": "cpp",        ".hpp": "cpp",
        ".hh": "cpp",       ".c": "c",
        ".java": "java",    ".rb": "ruby",
        ".cs": "c_sharp",   ".php": "php",
        ".kt": "kotlin",    ".scala": "scala",
        ".sc": "scala",     ".swift": "swift",
        ".hs": "haskell",   ".dart": "dart",
        ".lua": "lua",      ".ex": "elixir",
        ".exs": "elixir",
    }

    GENERIC_EXTENSIONS = {
        ".toml", ".sh", ".yaml", ".yml", ".json", ".ini",
        ".cfg", ".md", ".txt", ".env", ".bat", ".ps1",
        ".dockerignore", ".gitignore",
    }
    GENERIC_FILENAMES = {"Dockerfile", "Makefile"}

    def __init__(self) -> None:
        self._cache = threading.local()

    def get_parser(self, extension: str):
        from codegraphcontext.tools.tree_sitter_parser import TreeSitterParser

        lang = self.PARSERS.get(extension)
        if not lang:
            return None
        if not hasattr(self._cache, "parsers"):
            self._cache.parsers = {}
        if lang not in self._cache.parsers:
            try:
                self._cache.parsers[lang] = TreeSitterParser(lang)
            except Exception as exc:
                log.debug("Parser init failed for %s: %s", lang, exc)
                self._cache.parsers[lang] = None
        return self._cache.parsers.get(lang)

    def parse_file(self, repo_path: Path, path: Path, is_dependency: bool = False) -> Dict:
        ext = path.suffix
        if path.name.endswith(".d.ts"):
            ext = ".d.ts"
        if ext in self.GENERIC_EXTENSIONS or path.name in self.GENERIC_FILENAMES:
            return {"path": str(path), "error": f"generic:{ext}", "unsupported": False}
        parser = self.get_parser(ext)
        if not parser:
            return {"path": str(path), "error": f"no-parser:{ext}", "unsupported": True}
        try:
            return parser.parse(path, is_dependency)
        except Exception as exc:
            return {"path": str(path), "error": str(exc)}

    def add_minimal_file_node(self, file_path: Path, repo_path: Path, is_dependency: bool = False) -> None:
        pass  # Stage 1 already created File nodes


# ─── Neo4j writer (our schema) ────────────────────────────────────────────────

class Stage2Neo4jWriter:
    """
    Implements CGC's GraphWriter interface, writing into our Stage-2 Neo4j schema.

    Maps CGC's absolute-path-based model to our relative-path model:
      qualified_name = "{repo_full_name}:{rel_file_path}::{name}@{start_line}"
    """

    def __init__(self, sync_driver, repo_full_name: str, repo_root: Path) -> None:
        self.driver = sync_driver
        self.repo_full_name = repo_full_name
        self.repo_root = repo_root.resolve()
        # (abs_path_str, fn_name, line_number) -> qualified_name
        self._fn_index: dict[tuple[str, str, int], str] = {}
        self.stats: Dict[str, int] = {
            "functions": 0, "classes": 0,
            "calls": 0, "extends": 0, "errors": 0,
        }

    # ── path helpers ──────────────────────────────────────────────────────────

    def _rel(self, abs_path: Any) -> str:
        try:
            return str(Path(abs_path).resolve().relative_to(self.repo_root))
        except ValueError:
            return str(abs_path)

    def _qn(self, rel: str, name: str, line: int) -> str:
        return f"{self.repo_full_name}:{rel}::{name}@{line}"

    # ── no-op stubs for CGC methods we don't need ─────────────────────────────

    def add_repository_to_graph(self, *a, **kw) -> None: pass
    def add_minimal_file_node(self, *a, **kw) -> None: pass
    def write_cpp_class_function_links(self, *a, **kw) -> None: pass
    def write_spring_inject_links(self, *a, **kw) -> None: pass
    def write_spring_endpoint_properties(self, *a, **kw) -> None: pass
    def write_maven_build_graph(self, *a, **kw) -> None: pass
    def write_gradle_build_graph(self, *a, **kw) -> None: pass
    def write_orm_mappings(self, *a, **kw) -> None: pass
    def write_query_links(self, *a, **kw) -> None: pass
    def write_spring_data_repo_links(self, *a, **kw) -> None: pass
    def write_mybatis_links(self, *a, **kw) -> None: pass

    # ── core writes ───────────────────────────────────────────────────────────

    def add_file_to_graph(
        self,
        file_data: Dict[str, Any],
        repo_name: str,
        imports_map: dict,
        repo_path_str: Optional[str] = None,
    ) -> None:
        abs_path = str(Path(file_data["path"]).resolve())
        rel = self._rel(abs_path)
        lang = file_data.get("lang") or ""

        with self.driver.session() as s:
            for fn in file_data.get("functions", []):
                self._write_function(s, fn, rel, lang, abs_path)
            for cls in file_data.get("classes", []):
                self._write_class(s, cls, rel, lang, abs_path)

    def _write_function(self, s, fn: dict, rel: str, lang: str, abs_path: str) -> None:
        name = fn.get("name", "")
        line = int(fn.get("line_number") or 0)
        end_line = int(fn.get("end_line_number") or line)
        qn = self._qn(rel, name, line)
        self._fn_index[(abs_path, name, line)] = qn
        try:
            s.run(
                """
                MERGE (fn:Function {qualified_name: $qn})
                SET fn.name = $name,
                    fn.file_path = $rel,
                    fn.repo_full_name = $repo,
                    fn.start_line = $start,
                    fn.end_line = $end,
                    fn.language = $lang
                WITH fn
                OPTIONAL MATCH (f:File {path: $rel, repo_full_name: $repo})
                FOREACH (_ IN CASE WHEN f IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (fn)-[:DEFINED_IN]->(f)
                )
                """,
                qn=qn, name=name, rel=rel, repo=self.repo_full_name,
                start=line, end=end_line, lang=lang,
            )
            self.stats["functions"] += 1
        except Exception as exc:
            log.debug("Function write error %s: %s", qn, exc)
            self.stats["errors"] += 1

    def _write_class(self, s, cls: dict, rel: str, lang: str, abs_path: str) -> None:
        name = cls.get("name", "")
        line = int(cls.get("line_number") or 0)
        qn = self._qn(rel, name, line)
        try:
            s.run(
                """
                MERGE (cl:Class {qualified_name: $qn})
                SET cl.name = $name,
                    cl.file_path = $rel,
                    cl.repo_full_name = $repo,
                    cl.start_line = $line,
                    cl.language = $lang
                """,
                qn=qn, name=name, rel=rel, repo=self.repo_full_name,
                line=line, lang=lang,
            )
            self.stats["classes"] += 1

            for method in cls.get("methods", []) or []:
                mname = method.get("name", "")
                mline = int(method.get("line_number") or 0)
                mend = int(method.get("end_line_number") or mline)
                mqn = self._qn(rel, mname, mline)
                self._fn_index[(abs_path, mname, mline)] = mqn
                try:
                    s.run(
                        """
                        MERGE (fn:Function {qualified_name: $mqn})
                        SET fn.name = $mname,
                            fn.file_path = $rel,
                            fn.repo_full_name = $repo,
                            fn.start_line = $mline,
                            fn.end_line = $mend,
                            fn.language = $lang
                        WITH fn
                        MATCH (cl:Class {qualified_name: $cqn})
                        MERGE (fn)-[:METHOD_OF]->(cl)
                        """,
                        mqn=mqn, mname=mname, rel=rel, repo=self.repo_full_name,
                        mline=mline, mend=mend, lang=lang, cqn=qn,
                    )
                    self.stats["functions"] += 1
                except Exception as exc:
                    log.debug("Method write error %s: %s", mqn, exc)
                    self.stats["errors"] += 1
        except Exception as exc:
            log.debug("Class write error %s: %s", qn, exc)
            self.stats["errors"] += 1

    def write_function_call_groups(
        self,
        fn_to_fn: List[Dict] = None,
        fn_to_class: List[Dict] = None,
        fn_to_interface: List[Dict] = None,
        fn_to_object: List[Dict] = None,
        file_to_fn: List[Dict] = None,
        file_to_class: List[Dict] = None,
        file_to_interface: List[Dict] = None,
        file_to_object: List[Dict] = None,
    ) -> None:
        rows = fn_to_fn or []
        if not rows:
            return
        with self.driver.session() as s:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                c_path = row.get("caller_file_path")
                c_name = row.get("caller_name")
                c_line = int(row.get("caller_line_number") or 0)
                d_path = row.get("called_file_path")
                d_name = row.get("called_name")
                d_line = int(row.get("called_line_number") or 0)
                if not all([c_path, c_name, d_path, d_name]):
                    continue
                caller_qn = self._fn_index.get((c_path, c_name, c_line))
                called_qn = self._fn_index.get((d_path, d_name, d_line))
                if not (caller_qn and called_qn):
                    continue
                try:
                    s.run(
                        """
                        MATCH (a:Function {qualified_name: $cqn})
                        MATCH (b:Function {qualified_name: $dqn})
                        MERGE (a)-[:CALLS]->(b)
                        """,
                        cqn=caller_qn, dqn=called_qn,
                    )
                    self.stats["calls"] += 1
                except Exception as exc:
                    log.debug("CALLS write error: %s", exc)
                    self.stats["errors"] += 1

    def write_inheritance_links(
        self,
        inheritance_batch: List[Dict[str, Any]],
        csharp_files: List[Dict[str, Any]],
        imports_map: dict,
    ) -> None:
        with self.driver.session() as s:
            for row in inheritance_batch or []:
                c_name = row.get("child_class")
                c_path = row.get("child_file_path")
                p_name = row.get("parent_class")
                p_path = row.get("resolved_parent_file_path")
                if not all([c_name, c_path, p_name, p_path]):
                    continue
                if p_path == "__external__":
                    continue
                c_line = int(row.get("child_line_number") or 0)
                p_line = int(row.get("parent_line_number") or 0)
                c_qn = self._qn(self._rel(c_path), c_name, c_line)
                p_qn = self._qn(self._rel(p_path), p_name, p_line)
                try:
                    s.run(
                        """
                        MATCH (child:Class {qualified_name: $cqn})
                        MATCH (parent:Class {qualified_name: $pqn})
                        MERGE (child)-[:EXTENDS]->(parent)
                        """,
                        cqn=c_qn, pqn=p_qn,
                    )
                    self.stats["extends"] += 1
                except Exception as exc:
                    log.debug("EXTENDS write error: %s", exc)
                    self.stats["errors"] += 1


# ─── Orchestrator ─────────────────────────────────────────────────────────────

async def ingest_ast_for_repo(settings, repo) -> Dict[str, Any]:
    """
    Run CGC tree-sitter indexing for *repo* and persist AST nodes into Neo4j.

    Parameters
    ----------
    settings : config.Settings  (neo4j_uri / neo4j_user / neo4j_password)
    repo     : ingest.local_repos.RepoInfo

    Returns
    -------
    dict  {"repo": str, "functions": int, "classes": int,
           "calls": int, "extends": int, "errors": int}
    """
    from codegraphcontext.core.jobs import JobManager
    from codegraphcontext.tools.indexing.pipeline import run_tree_sitter_index_async

    repo_path = Path(repo.local_path).resolve()
    if not repo_path.is_dir():
        raise ValueError(f"Repo path not found: {repo_path}")

    sync_driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        writer = Stage2Neo4jWriter(sync_driver, repo.full_name, repo_path)
        helper = _ParserHelper()

        await run_tree_sitter_index_async(
            path=repo_path,
            is_dependency=False,
            job_id=None,
            cgcignore_path=None,
            writer=writer,
            job_manager=JobManager(),
            parsers=_ParserHelper.PARSERS,
            get_parser=helper.get_parser,
            parse_file=helper.parse_file,
            add_minimal_file_node=helper.add_minimal_file_node,
        )

        log.info(
            "AST ingest [%s]: %d fn, %d cls, %d calls, %d extends, %d err",
            repo.full_name,
            writer.stats["functions"], writer.stats["classes"],
            writer.stats["calls"], writer.stats["extends"],
            writer.stats["errors"],
        )
        return {"repo": repo.full_name, **writer.stats}
    finally:
        sync_driver.close()

"""Markdown code analysis reports for selected local repositories."""

from __future__ import annotations

import ast
import json
import math
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Settings


_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
    "env",
    "vendor",
    "qdrant_storage",
}

_SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".sh",
    ".sql",
    ".html",
    ".css",
    ".scss",
    ".sass",
    ".vue",
    ".svelte",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
}

_LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C/C++",
    ".cc": "C/C++",
    ".cpp": "C/C++",
    ".h": "C/C++",
    ".hpp": "C/C++",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".md": "Markdown",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
}

_IMPORTANT_FILES = {
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "go.mod",
    "Cargo.toml",
    "composer.json",
    "composer.lock",
    "pom.xml",
    "build.gradle",
    "Makefile",
    "README.md",
    ".env.example",
}

_ENTRYPOINT_CANDIDATES = {
    "main.py",
    "app.py",
    "api.py",
    "manage.py",
    "server.js",
    "index.js",
    "index.ts",
    "src/index.js",
    "src/index.ts",
    "src/main.js",
    "src/main.ts",
    "cmd/main.go",
    "artisan",
    "public/index.php",
    "index.php",
}

_MANIFEST_NAMES = {
    "package.json",
    "composer.json",
    "requirements.txt",
    "pyproject.toml",
}

_DOC_EXTENSIONS = {".md", ".rst", ".adoc"}

_SECURITY_KEYWORDS = {
    "auth",
    "authentication",
    "authorization",
    "jwt",
    "token",
    "secret",
    "password",
    "permission",
    "privilege",
    "admin",
    "oauth",
    "saml",
}

_DB_KEYWORDS = {
    "db",
    "database",
    "postgres",
    "mysql",
    "mongo",
    "redis",
    "sql",
    "migration",
    "repository",
    "dao",
    "model",
}

_EVENT_KEYWORDS = {
    "event",
    "events",
    "consumer",
    "producer",
    "kafka",
    "rabbit",
    "queue",
    "topic",
    "stream",
    "pubsub",
    "celery",
}

_API_KEYWORDS = {"api", "route", "routes", "router", "controller", "endpoint", "rest", "graphql"}

_COMPLEXITY_KEYWORDS = (
    "if",
    "elif",
    "else if",
    "for",
    "while",
    "case",
    "catch",
    "except",
    "&&",
    "||",
    "?",
)

_EMBEDDING_MODEL_ALIASES = {
    "codebase_bge_m3": ["codebase_bge_m3", "bge-m3", "BAAI/bge-m3", "BGE-M3 (568M)"],
    "codebase_qwen3_0_6b": ["codebase_qwen3_0_6b", "qwen3:0.6b", "Qwen/Qwen3-Embedding-0.6B"],
    "codebase_mxbai_large": ["codebase_mxbai_large", "mxbai-embed-large", "mixedbread-ai/mxbai-embed-large-v1"],
    "bge-m3": ["bge-m3", "BAAI/bge-m3", "BGE-M3 (568M)"],
    "qwen3-embedding-0.6b": [
        "qwen3-embedding-0.6b",
        "Qwen/Qwen3-Embedding-0.6B",
        "Qwen3-Embedding-0.6B",
    ],
    "mxbai-embed-large-v1": [
        "mxbai-embed-large-v1",
        "mixedbread-ai/mxbai-embed-large-v1",
        "mxbai-embed-large-v1 (335M)",
    ],
}


async def build_code_analysis_report(
    *,
    settings: Settings,
    selected_repositories: list[dict[str, Any]],
    include_graph_context: bool = True,
    embedding_model: str = "codebase_bge_m3",
) -> tuple[str, str]:
    """Build a Markdown report and return (filename, markdown)."""
    graph_context = {}
    graph_error = ""
    if include_graph_context:
        try:
            graph_context = await _load_graph_context(
                settings,
                [repo["name"] for repo in selected_repositories],
                embedding_model,
            )
            await _merge_codegraphcontext_context(settings, graph_context, selected_repositories)
            _merge_qdrant_codebase_context(
                settings,
                graph_context,
                selected_repositories,
                embedding_model,
            )
            if "__graph_errors__" in graph_context:
                graph_error = "; ".join(graph_context["__graph_errors__"].get("graph_query_errors", []))
        except Exception as exc:
            graph_error = str(exc)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    repo_count = len(selected_repositories)
    title = "Code Analysis Report"
    filename = _report_filename(selected_repositories, embedding_model)

    lines = [
        f"# {title}",
        "",
        f"Generated: {generated_at}",
        f"Repositories selected: {repo_count}",
        f"Embedding model selected: {embedding_model}",
        "",
        "## Executive Summary",
        "",
        (
            "This report combines local clone inspection with graph database context "
            "from the repository ingestion pipeline. Graph-backed sections reflect "
            "the latest successful graph build."
        ),
        "",
    ]
    if graph_error:
        lines.extend(
            [
                f"Graph context note: `{_escape_inline(graph_error)}`",
                "",
            ]
        )

    inventory = []
    local_stats_by_name = {}
    for repo in selected_repositories:
        stats = _inspect_local_repository(repo)
        local_stats_by_name[repo["name"]] = stats
        graph = graph_context.get(repo["name"], {})
        inventory.append(
            [
                repo["name"],
                repo.get("branch") or "-",
                (repo.get("current_commit") or "-")[:12],
                str(stats["total_files"]),
                str(stats["source_lines"]),
                str(graph.get("total_commits") or 0),
            ]
        )

    lines.extend(
        [
            "## Repository Inventory",
            "",
            _markdown_table(
                ["Repository", "Branch", "Commit", "Files", "Source Lines", "Graph Commits"],
                inventory,
            ),
            "",
        ]
    )

    for repo in selected_repositories:
        name = repo["name"]
        stats = local_stats_by_name[name]
        graph = graph_context.get(name, {})
        lines.extend(_repository_section(repo, stats, graph))

    return filename, "\n".join(lines).rstrip() + "\n"


async def _load_graph_context(
    settings: Settings,
    repo_names: list[str],
    embedding_model: str,
) -> dict[str, dict[str, Any]]:
    from neo4j import AsyncGraphDatabase

    base_query = """
    MATCH (r:Repo)
    WHERE r.full_name IN $repo_names
       OR (r.name IN $repo_names AND NOT coalesce(r.full_name, '') CONTAINS '/')
    CALL {
        WITH r
        OPTIONAL MATCH (r)<-[:IN_REPO]-(c:Commit)
        RETURN count(c) AS total_commits,
               toString(max(c.committed_at)) AS last_commit_at,
               sum(coalesce(c.additions, 0)) AS total_additions,
               sum(coalesce(c.deletions, 0)) AS total_deletions
    }
    CALL {  
        WITH r
        OPTIONAL MATCH (r)<-[:IN_REPO]-(f:File)
        RETURN count(f) AS graph_files,
               count(CASE WHEN f.current = true THEN f END) AS current_files
    }
    CALL {
        WITH r
        OPTIONAL MATCH (r)<-[:IN_REPO]-(c:Commit)-[:AUTHORED_BY]->(a:Author)
        WITH a, count(c) AS commits
        WHERE a IS NOT NULL
        ORDER BY commits DESC
        LIMIT 10
        RETURN collect({name: coalesce(a.name, a.email), email: a.email, commits: commits}) AS authors
    }
    CALL {
        WITH r
        OPTIONAL MATCH (r)<-[:IN_REPO]-(f:File)<-[t:TOUCHES]-(:Commit)
        WITH f.path AS path, count(t) AS touches
        WHERE path IS NOT NULL
        ORDER BY touches DESC
        LIMIT 15
        RETURN collect({path: path, touches: touches}) AS hot_files
    }
    CALL {
        WITH r
        OPTIONAL MATCH (r)<-[:IN_REPO]-(f:File)
        WITH f.extension AS extension, count(f) AS files
        WHERE extension IS NOT NULL
        ORDER BY files DESC
        LIMIT 10
        RETURN collect({extension: extension, files: files}) AS graph_extension_mix
    }
    CALL {
        WITH r
        OPTIONAL MATCH (r)<-[:IN_REPO]-(c:Commit)
        WITH c
        ORDER BY c.committed_at DESC
        LIMIT 12
        RETURN collect({
            sha: coalesce(c.short_sha, substring(c.sha, 0, 12)),
            summary: c.summary,
            committed_at: toString(c.committed_at)
        }) AS recent_commits
    }
    RETURN r.name AS name,
           r.full_name AS full_name,
           r.url AS url,
           r.local_path AS local_path,
           r.description AS description,
           r.language AS language,
           r.default_branch AS default_branch,
           total_commits,
           last_commit_at,
           total_additions,
           total_deletions,
           graph_files,
           current_files,
           authors,
           hot_files,
           graph_extension_mix,
           recent_commits
    """
    ast_query = """
    MATCH (r:Repo)
    WHERE r.full_name IN $repo_names
       OR (r.name IN $repo_names AND NOT coalesce(r.full_name, '') CONTAINS '/')
    CALL {
        WITH r
        OPTIONAL MATCH (fn:Function)
        WHERE fn.repo_full_name = r.full_name
        RETURN count(fn) AS functions
    }
    CALL {
        WITH r
        OPTIONAL MATCH (cl:Class)
        WHERE cl.repo_full_name = r.full_name
        RETURN count(cl) AS classes
    }
    CALL {
        WITH r
        OPTIONAL MATCH (m:Module)
        WHERE m.repo_full_name = r.full_name
        WITH r, count(m) AS module_nodes
        OPTIONAL MATCH (f:File)
        WHERE f.repo_full_name = r.full_name
        WITH module_nodes, count(f) AS file_nodes
        RETURN CASE WHEN module_nodes > 0 THEN module_nodes ELSE file_nodes END AS modules
    }
    CALL {
        WITH r
        OPTIONAL MATCH (caller:Function)-[rel:CALLS]->(callee:Function)
        WHERE caller.repo_full_name = r.full_name AND callee.repo_full_name = r.full_name
        RETURN count(rel) AS call_edges
    }
    CALL {
        WITH r
        OPTIONAL MATCH (source:Module)-[rel:IMPORTS]->(target:Module)
        WHERE source.repo_full_name = r.full_name AND target.repo_full_name = r.full_name
        WITH r, count(rel) AS module_import_edges
        OPTIONAL MATCH (source_file:File)-[file_rel:IMPORTS]->(target_file:File)
        WHERE source_file.repo_full_name = r.full_name AND target_file.repo_full_name = r.full_name
        WITH module_import_edges, count(file_rel) AS file_import_edges
        RETURN module_import_edges + file_import_edges AS import_edges
    }
    CALL {
        WITH r
        MATCH (m:File)
        WHERE m.repo_full_name = r.full_name
        OPTIONAL MATCH (m)-[:IMPORTS]->(dep:File)
        WHERE dep.repo_full_name = r.full_name
        WITH r, m, count(DISTINCT dep) AS out_degree
        OPTIONAL MATCH (parent:File)-[:IMPORTS]->(m)
        WHERE parent.repo_full_name = r.full_name
        WITH m, out_degree, count(DISTINCT parent) AS in_degree
        WITH m, in_degree, out_degree, in_degree + out_degree AS degree
        WHERE degree > 0
        ORDER BY degree DESC
        LIMIT 12
        RETURN collect({
            name: m.path,
            file_path: m.path,
            in_degree: in_degree,
            out_degree: out_degree,
            degree: degree
        }) AS module_centrality
    }
    CALL {
        WITH r
        MATCH (fn:Function)
        WHERE fn.repo_full_name = r.full_name
        OPTIONAL MATCH (fn)-[:CALLS]->(callee:Function)
        WHERE callee.repo_full_name = r.full_name
        WITH r, fn, count(DISTINCT callee) AS out_degree
        OPTIONAL MATCH (caller:Function)-[:CALLS]->(fn)
        WHERE caller.repo_full_name = r.full_name
        WITH fn, out_degree, count(DISTINCT caller) AS in_degree
        WITH fn, in_degree, out_degree, in_degree + out_degree AS degree
        ORDER BY degree DESC
        LIMIT 12
        RETURN collect({
            name: fn.qualified_name,
            file_path: fn.file_path,
            in_degree: in_degree,
            out_degree: out_degree,
            degree: degree
        }) AS function_centrality
    }
    CALL {
        WITH r
        MATCH (caller:Function)-[:CALLS]->(callee:Function)
        WHERE caller.repo_full_name = r.full_name AND callee.repo_full_name = r.full_name
        RETURN collect({
            caller: caller.qualified_name,
            callee: callee.qualified_name,
            caller_file: caller.file_path,
            callee_file: callee.file_path
        })[..20] AS function_edges
    }
    CALL {
        WITH r
        MATCH p = (m:Module)-[:IMPORTS*2..5]->(m)
        WHERE m.repo_full_name = r.full_name
        WITH [n IN nodes(p) | coalesce(n.qualified_name, n.file_path)] AS cycle
        LIMIT 8
        RETURN collect(cycle) AS circular_dependencies
    }
    CALL {
        WITH r
        MATCH p = (cl:Class)-[:EXTENDS*1..6]->(base:Class)
        WHERE cl.repo_full_name = r.full_name AND base.repo_full_name = r.full_name
        WITH cl, length(p) AS depth
        ORDER BY depth DESC
        LIMIT 8
        RETURN collect({class_name: cl.qualified_name, depth: depth, file_path: cl.file_path}) AS inheritance_depth
    }
    RETURN r.name AS name,
           r.full_name AS full_name,
           functions,
           classes,
           modules,
           call_edges,
           import_edges,
           module_centrality,
           function_centrality,
           function_edges,
           circular_dependencies,
           inheritance_depth
    """
    embedding_query = """
    MATCH (r:Repo)
    WHERE r.full_name IN $repo_names
       OR (r.name IN $repo_names AND NOT coalesce(r.full_name, '') CONTAINS '/')
    CALL {
        WITH r
        OPTIONAL MATCH (all_docs:EmbeddingDocument)
        WHERE all_docs.repo_full_name = r.full_name
        WITH coalesce(all_docs.embedding_model_key, all_docs.embedding_model, 'unknown') AS model_key,
             count(all_docs) AS documents
        WHERE model_key IS NOT NULL
        ORDER BY documents DESC
        RETURN collect({model: model_key, documents: documents}) AS available_embedding_models
    }
    OPTIONAL MATCH (d:EmbeddingDocument)
    WHERE d.repo_full_name = r.full_name
      AND (
        coalesce(d.embedding_model_key, '') = $embedding_model
        OR coalesce(d.embedding_model, '') IN $embedding_model_aliases
        OR coalesce(d.embedding_model_label, '') IN $embedding_model_aliases
      )
    WITH r, d, available_embedding_models
    ORDER BY d.kind, d.title
    WITH r, available_embedding_models, count(d) AS embedding_documents, collect(d)[..250] AS docs
    RETURN r.name AS name,
           r.full_name AS full_name,
           available_embedding_models,
           embedding_documents,
           [doc IN docs WHERE doc IS NOT NULL | {
               id: doc.id,
               source_document_id: doc.source_document_id,
               kind: doc.kind,
               source_key: doc.source_key,
               title: doc.title,
               text: doc.text,
               metadata_json: doc.metadata_json,
               embedding_model_key: doc.embedding_model_key,
               embedding_model_label: doc.embedding_model_label,
               embedding_model: doc.embedding_model,
               dimensions: doc.embedding_dimensions,
               embedding: doc.embedding
           }] AS embedding_docs
    """
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    context: dict[str, dict[str, Any]] = {}
    query_errors: list[str] = []

    def merge_row(row: dict[str, Any]) -> None:
        key = row.get("name") or row.get("full_name")
        if not key:
            return
        target = context.setdefault(key, {})
        _merge_graph_row(target, row)
        full_name = row.get("full_name")
        if full_name:
            context[full_name] = target

    try:
        async with driver.session(database=settings.neo4j_database) as session:
            for label, query in (
                ("base graph", base_query),
                ("AST graph", ast_query),
                ("embedding graph", embedding_query),
            ):
                try:
                    result = await session.run(
                        query,
                        repo_names=repo_names,
                        embedding_model=embedding_model,
                        embedding_model_aliases=_embedding_model_aliases(embedding_model),
                    )
                    async for row in result:
                        merge_row(dict(row))
                except Exception as exc:
                    query_errors.append(f"{label}: {exc}")
    finally:
        await driver.close()

    for value in context.values():
        if query_errors:
            value["graph_query_errors"] = query_errors
        _summarize_embedding_docs(value)
    if query_errors and not context:
        context["__graph_errors__"] = {"graph_query_errors": query_errors}
    return context


def _merge_qdrant_codebase_context(
    settings: Settings,
    graph_context: dict[str, dict[str, Any]],
    repositories: list[dict[str, Any]],
    embedding_model: str,
) -> None:
    if not settings.qdrant_url or not embedding_model.startswith("codebase_"):
        return
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import FieldCondition, Filter, MatchValue
    except ImportError:
        return

    try:
        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
        existing = {collection.name for collection in client.get_collections().collections}
        if embedding_model not in existing:
            return
        for repo in repositories:
            repo_name = repo.get("name") or ""
            points, _ = client.scroll(
                collection_name=embedding_model,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="repo_name", match=MatchValue(value=repo_name)),
                    ]
                ),
                limit=250,
                with_payload=True,
                with_vectors=True,
            )
            docs = []
            for point in points:
                payload = point.payload or {}
                docs.append(
                    {
                        "id": payload.get("id") or str(point.id),
                        "kind": "file",
                        "source_key": payload.get("path"),
                        "title": payload.get("path"),
                        "text": payload.get("text"),
                        "metadata": payload,
                        "embedding_model_key": embedding_model,
                        "embedding_model": payload.get("model_name") or embedding_model,
                        "embedding_model_label": embedding_model,
                        "dimensions": len(point.vector or []),
                        "embedding": point.vector or [],
                    }
                )
            if docs:
                graph = graph_context.setdefault(repo_name, {})
                graph["embedding_docs"] = docs
                graph["embedding_documents"] = len(docs)
                available = graph.setdefault("available_embedding_models", [])
                available.append({"model": embedding_model, "documents": len(docs)})
                _summarize_embedding_docs(graph)
    except Exception as exc:
        errors = graph_context.setdefault("__graph_errors__", {}).setdefault("graph_query_errors", [])
        errors.append(f"qdrant codebase embeddings: {exc}")


async def _merge_codegraphcontext_context(
    settings: Settings,
    graph_context: dict[str, dict[str, Any]],
    repositories: list[dict[str, Any]],
) -> None:
    """Merge graph data written by CodeGraphContext's Neo4j backend."""
    from neo4j import AsyncGraphDatabase

    repo_path_to_name: dict[str, str] = {}
    for repo in repositories:
        name = repo.get("name") or ""
        for value in (repo.get("container_path"), repo.get("path")):
            if value:
                repo_path_to_name[str(Path(value).resolve())] = name
    if not repo_path_to_name:
        return

    query = """
    MATCH (r:Repository)
    WHERE r.path IN $repo_paths
    CALL {
        WITH r
        MATCH (f:File)
        WHERE f.path STARTS WITH r.path
        RETURN count(f) AS cgc_files
    }
    CALL {
        WITH r
        MATCH (fn:Function)
        WHERE fn.path STARTS WITH r.path
        RETURN count(fn) AS cgc_functions
    }
    CALL {
        WITH r
        MATCH (cl:Class)
        WHERE cl.path STARTS WITH r.path
        RETURN count(cl) AS cgc_classes
    }
    CALL {
        WITH r
        MATCH (file:File)-[imp:IMPORTS]->(m:Module)
        WHERE file.path STARTS WITH r.path
        RETURN count(DISTINCT m) AS cgc_modules,
               count(imp) AS cgc_import_edges
    }
    CALL {
        WITH r
        MATCH (caller:Function)-[rel:CALLS]->(callee:Function)
        WHERE caller.path STARTS WITH r.path AND callee.path STARTS WITH r.path
        RETURN count(rel) AS cgc_call_edges
    }
    CALL {
        WITH r
        MATCH (fn:Function)
        WHERE fn.path STARTS WITH r.path
        OPTIONAL MATCH (fn)-[:CALLS]->(callee:Function)
        WHERE callee.path STARTS WITH r.path
        WITH r, fn, count(DISTINCT callee) AS out_degree
        OPTIONAL MATCH (caller:Function)-[:CALLS]->(fn)
        WHERE caller.path STARTS WITH r.path
        WITH fn, out_degree, count(DISTINCT caller) AS in_degree
        WITH fn, in_degree, out_degree, in_degree + out_degree AS degree
        WHERE degree > 0
        ORDER BY degree DESC
        LIMIT 12
        RETURN collect({
            name: fn.name,
            file_path: fn.path,
            in_degree: in_degree,
            out_degree: out_degree,
            degree: degree
        }) AS cgc_function_centrality
    }
    CALL {
        WITH r
        MATCH (caller:Function)-[:CALLS]->(callee:Function)
        WHERE caller.path STARTS WITH r.path AND callee.path STARTS WITH r.path
        RETURN collect({
            caller: caller.name,
            callee: callee.name,
            caller_file: caller.path,
            callee_file: callee.path
        })[..20] AS cgc_function_edges
    }
    CALL {
        WITH r
        MATCH (file:File)-[imp:IMPORTS]->(module:Module)
        WHERE file.path STARTS WITH r.path
        WITH module, count(imp) AS refs
        ORDER BY refs DESC
        LIMIT 12
        RETURN collect({
            name: module.name,
            file_path: module.name,
            in_degree: refs,
            out_degree: 0,
            degree: refs
        }) AS cgc_module_centrality
    }
    RETURN r.path AS repo_path,
           cgc_files,
           cgc_functions,
           cgc_classes,
           cgc_modules,
           cgc_import_edges,
           cgc_call_edges,
           cgc_function_centrality,
           cgc_function_edges,
           cgc_module_centrality
    """
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        async with driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, repo_paths=list(repo_path_to_name))
            async for row in result:
                data = dict(row)
                repo_path = data.get("repo_path")
                name = repo_path_to_name.get(repo_path)
                if not name:
                    continue
                graph = graph_context.setdefault(name, {})
                graph["codegraphcontext_available"] = True
                graph["graph_files"] = max(int(graph.get("graph_files") or 0), int(data.get("cgc_files") or 0))
                graph["functions"] = max(int(graph.get("functions") or 0), int(data.get("cgc_functions") or 0))
                graph["classes"] = max(int(graph.get("classes") or 0), int(data.get("cgc_classes") or 0))
                graph["modules"] = max(int(graph.get("modules") or 0), int(data.get("cgc_modules") or 0))
                graph["import_edges"] = max(int(graph.get("import_edges") or 0), int(data.get("cgc_import_edges") or 0))
                graph["call_edges"] = max(int(graph.get("call_edges") or 0), int(data.get("cgc_call_edges") or 0))
                graph["function_centrality"] = _merge_unique_list(
                    graph.get("function_centrality") or [],
                    _relativize_cgc_rows(data.get("cgc_function_centrality") or [], repo_path),
                )
                graph["function_edges"] = _merge_unique_list(
                    graph.get("function_edges") or [],
                    _relativize_cgc_rows(data.get("cgc_function_edges") or [], repo_path),
                )
                graph["module_centrality"] = _merge_unique_list(
                    graph.get("module_centrality") or [],
                    data.get("cgc_module_centrality") or [],
                )
    except Exception as exc:
        errors = graph_context.setdefault("__graph_errors__", {}).setdefault("graph_query_errors", [])
        errors.append(f"CodeGraphContext graph: {exc}")
    finally:
        await driver.close()


def _relativize_cgc_rows(rows: list[dict[str, Any]], repo_path: str) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        item = dict(row)
        for key in ("file_path", "caller_file", "callee_file"):
            if item.get(key):
                item[key] = _relative_to_repo_path(str(item[key]), repo_path)
        normalized.append(item)
    return normalized


def _relative_to_repo_path(path: str, repo_path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(repo_path).resolve()))
    except Exception:
        return path


def _merge_graph_row(target: dict[str, Any], row: dict[str, Any]) -> None:
    """Merge duplicate Repo rows without letting sparse legacy nodes win."""
    max_numeric_fields = {
        "total_commits",
        "total_additions",
        "total_deletions",
        "graph_files",
        "current_files",
        "functions",
        "classes",
        "modules",
        "call_edges",
        "import_edges",
        "embedding_documents",
    }
    list_fields = {
        "authors",
        "hot_files",
        "graph_extension_mix",
        "recent_commits",
        "available_embedding_models",
        "module_centrality",
        "function_centrality",
        "function_edges",
        "circular_dependencies",
        "inheritance_depth",
        "embedding_docs",
    }
    for key, value in row.items():
        if value in (None, "", [], {}):
            continue
        if key in max_numeric_fields:
            target[key] = max(int(target.get(key) or 0), int(value or 0))
        elif key in list_fields and isinstance(value, list):
            target[key] = _merge_unique_list(target.get(key) or [], value)
        elif key not in target or target.get(key) in (None, "", [], {}):
            target[key] = value


def _merge_unique_list(existing: list[Any], incoming: list[Any]) -> list[Any]:
    seen = set()
    merged = []
    for item in [*existing, *incoming]:
        marker = json.dumps(item, sort_keys=True, default=str) if isinstance(item, (dict, list)) else str(item)
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(item)
    return merged


def _inspect_local_repository(repo: dict[str, Any]) -> dict[str, Any]:
    root_value = repo.get("container_path") or repo.get("path")
    root = Path(root_value) if root_value else Path("/path/not/configured")
    extensions: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    directories: Counter[str] = Counter()
    import_dependencies: Counter[str] = Counter()
    important_files = []
    documentation_files = []
    entry_points = []
    large_files = []
    complex_units = []
    source_files = []
    api_files = []
    db_files = []
    event_files = []
    security_files = []
    duplicate_names: dict[str, list[str]] = {}
    total_files = 0
    source_lines = 0

    if root.exists():
        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                dirname for dirname in dirnames
                if dirname not in _SKIP_DIRS and not dirname.startswith(".cache")
            ]
            rel_root = Path(current_root).relative_to(root)
            top_dir = str(rel_root.parts[0]) if rel_root.parts else "."
            for filename in filenames:
                path = Path(current_root) / filename
                rel_path = path.relative_to(root)
                if any(part in _SKIP_DIRS for part in rel_path.parts):
                    continue
                total_files += 1
                rel_str = str(rel_path)
                directories[top_dir] += 1
                ext = path.suffix.lower() or "[no extension]"
                extensions[ext] += 1
                language = _LANGUAGE_BY_EXTENSION.get(path.suffix.lower())
                if language:
                    languages[language] += 1
                if filename in _IMPORTANT_FILES or rel_str in _IMPORTANT_FILES:
                    important_files.append(rel_str)
                if filename in _MANIFEST_NAMES and _manifest_depth(rel_path) <= 4:
                    important_files.append(rel_str)
                if filename in _ENTRYPOINT_CANDIDATES or rel_str in _ENTRYPOINT_CANDIDATES:
                    entry_points.append(rel_str)
                if path.suffix.lower() in _DOC_EXTENSIONS:
                    documentation_files.append(rel_str)
                if path.suffix.lower() in _SOURCE_EXTENSIONS:
                    analysis = _analyze_source_file(path, rel_str)
                    source_lines += analysis["lines"]
                    source_files.append(
                        {
                            "path": rel_str,
                            "lines": analysis["lines"],
                            "complexity": analysis["file_complexity"],
                            "extension": path.suffix.lower(),
                        }
                    )
                    if analysis["lines"] >= 250:
                        large_files.append(
                            {
                                "path": rel_str,
                                "lines": analysis["lines"],
                                "complexity": analysis["file_complexity"],
                            }
                        )
                    complex_units.extend(analysis["complex_units"])
                    import_dependencies.update(analysis["imports"])
                if _path_has_keyword(rel_str, _API_KEYWORDS):
                    api_files.append(rel_str)
                if _path_has_keyword(rel_str, _DB_KEYWORDS):
                    db_files.append(rel_str)
                if _path_has_keyword(rel_str, _EVENT_KEYWORDS):
                    event_files.append(rel_str)
                if _path_has_keyword(rel_str, _SECURITY_KEYWORDS):
                    security_files.append(rel_str)
                duplicate_names.setdefault(filename.lower(), []).append(rel_str)

    package_data = _read_package_data(root)
    readme_summary = _read_readme_summary(root)
    docker_entrypoints = _read_docker_entrypoints(root)
    package_entrypoints = package_data.get("entry_points", [])
    if docker_entrypoints:
        entry_points.extend(docker_entrypoints)
    if package_entrypoints:
        entry_points.extend(package_entrypoints)

    return {
        "root": root,
        "total_files": total_files,
        "source_lines": source_lines,
        "extensions": extensions.most_common(12),
        "languages": languages.most_common(8),
        "directories": directories.most_common(10),
        "all_directories": directories,
        "important_files": sorted(set(important_files))[:20],
        "documentation_files": sorted(set(documentation_files))[:30],
        "entry_points": sorted(set(entry_points))[:20],
        "large_files": sorted(large_files, key=lambda f: (f["lines"], f["complexity"]), reverse=True)[:15],
        "complex_units": sorted(complex_units, key=lambda f: (f["complexity"], f["lines"]), reverse=True)[:15],
        "source_files": source_files,
        "import_dependencies": import_dependencies.most_common(20),
        "api_files": sorted(set(api_files))[:20],
        "db_files": sorted(set(db_files))[:20],
        "event_files": sorted(set(event_files))[:20],
        "security_files": sorted(set(security_files))[:20],
        "duplicate_filenames": [
            {"name": name, "paths": paths[:8], "count": len(paths)}
            for name, paths in sorted(
                duplicate_names.items(),
                key=lambda item: len(item[1]),
                reverse=True,
            )
            if len(paths) > 1 and name not in {"index.js", "index.ts", "__init__.py"}
        ][:12],
        "package_data": package_data,
        "framework_hints": _framework_hints(root, source_files, package_data),
        "readme_summary": readme_summary,
        "git_recent": _git_recent_commits(root),
        "git_branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD") or repo.get("branch") or "",
        "git_status": _git(root, "status", "--short") or "",
    }


def _repository_section(repo: dict[str, Any], stats: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    name = repo["name"]
    remote_url = repo.get("remote_url") or graph.get("url") or ""
    local_path = repo.get("path") or graph.get("local_path") or ""
    technologies = _main_technologies(stats, graph)
    architecture = _detect_architecture(stats, graph)
    semantic_clusters = _semantic_clusters(graph.get("embedding_docs", []))
    duplicate_pairs = _similar_embedding_pairs(graph.get("embedding_docs", []))
    recommendations = _suggest_improvements(stats, graph, semantic_clusters, duplicate_pairs)
    purpose = _repo_purpose(repo, stats, graph, technologies)
    domain = _infer_domain(repo, stats, graph)
    application_shape = _application_shape(stats, architecture)

    lines = [
        f"## {name}",
        "",
        "### 1. Repository Overview",
        "",
        _markdown_table(
            ["Field", "Analysis"],
            [
                ["Purpose of repo", purpose],
                ["Domain/problem solved", domain],
                ["Main technologies", ", ".join(technologies) or "-"],
                ["Framework/platform hints", ", ".join(stats.get("framework_hints", [])) or "-"],
                ["Architecture shape", application_shape],
                ["Monolith vs microservice", _monolith_microservice_assessment(stats, architecture)],
                ["Main entry points", "<br>".join(stats["entry_points"]) or "-"],
                ["Local path", local_path or "-"],
                ["Remote", remote_url or "-"],
                ["Branch / commit", f"{stats.get('git_branch') or '-'} / {(repo.get('current_commit') or '-')[:12]}"],
            ],
        ),
        "",
        "### 2. Repository Structure Analysis",
        "",
        _markdown_table(
            ["Directory/module", "Responsibility", "Files"],
            _directory_responsibility_rows(stats),
        ),
        "",
        _bullet_list(
            [
                f"Layering signal: {_layering_summary(stats)}",
                f"Feature grouping signal: {_feature_grouping_summary(stats)}",
                f"Key project/config files: {', '.join(stats['important_files'][:8]) or 'none detected'}",
                f"Detected manifests: {', '.join(stats.get('package_data', {}).get('manifests', [])[:8]) or 'none detected'}",
            ]
        ),
        "",
        "### 3. Semantic Clustering Analysis",
        "",
        _semantic_cluster_section(semantic_clusters, graph),
        "",
        "### 4. Dependency Graph Insights",
        "",
        _dependency_graph_section(stats, graph),
        "",
        "### 5. Architectural Pattern Detection",
        "",
        _markdown_table(
            ["Pattern", "Evidence", "Confidence"],
            architecture or [["No strong pattern detected", "Directory and graph evidence is sparse.", "low"]],
        ),
        "",
        "### 6. Code Complexity Analysis",
        "",
        _complexity_section(stats, graph),
        "",
        "### 7. Semantic Search Quality",
        "",
        _semantic_search_quality_section(graph, semantic_clusters),
        "",
        "### 8. Graph Schema Description",
        "",
        _graph_schema_section(),
        "",
        "### 9. Retrieval-Augmented Generation Readiness",
        "",
        _rag_readiness_section(stats, graph),
        "",
        "### 10. Cross-Reference Intelligence",
        "",
        _cross_reference_section(stats, graph),
        "",
        "### 11. Hotspot Detection",
        "",
        _hotspot_section(stats, graph, semantic_clusters),
        "",
        "### 12. Duplicate / Similar Logic Detection",
        "",
        _duplicate_logic_section(stats, duplicate_pairs),
        "",
        "### 13. Documentation Coverage",
        "",
        _documentation_section(stats, graph),
        "",
        "### 14. Security & Risk Analysis",
        "",
        _security_risk_section(stats, graph),
        "",
        "### 15. Suggested Improvements",
        "",
        _bullet_list(recommendations),
        "",
        "### Appendix: Recent Activity",
        "",
        "Primary contributors from graph:",
        "",
        _markdown_table(
            ["Contributor", "Email", "Commits"],
            [
                [a.get("name") or "-", a.get("email") or "-", str(a.get("commits") or 0)]
                for a in graph.get("authors", [])
            ] or [["-", "-", "0"]],
        ),
        "",
        "Recent graph commits:",
        "",
        _markdown_table(
            ["Commit", "Date", "Summary"],
            [
                [c.get("sha") or "-", c.get("committed_at") or "-", c.get("summary") or "-"]
                for c in graph.get("recent_commits", [])
            ] or [["-", "-", "No graph commits found."]],
        ),
        "",
        "Recent local git commits:",
        "",
        _markdown_table(
            ["Commit", "Date", "Author", "Summary"],
            stats["git_recent"] or [["-", "-", "-", "No local git commits found."]],
        ),
        "",
        "Working tree notes:",
        "",
    ]
    if stats["git_status"]:
        lines.extend(["```text", stats["git_status"][:4000], "```", ""])
    else:
        lines.extend(["Working tree is clean or status could not be read.", ""])
    return lines


def _summarize_embedding_docs(graph: dict[str, Any]) -> None:
    docs = graph.get("embedding_docs") or []
    kind_counts: Counter[str] = Counter()
    model_counts: Counter[str] = Counter()
    dimensions: Counter[str] = Counter()
    for doc in docs:
        kind = doc.get("kind") or "unknown"
        model = (
            doc.get("embedding_model_label")
            or doc.get("embedding_model_key")
            or doc.get("embedding_model")
            or "unknown"
        )
        vector = doc.get("embedding") or []
        dimension = doc.get("dimensions") or (len(vector) if isinstance(vector, list) else 0)
        kind_counts[kind] += 1
        model_counts[model] += 1
        dimensions[str(dimension or "unknown")] += 1
        metadata = doc.get("metadata_json")
        if isinstance(metadata, str):
            try:
                doc["metadata"] = json.loads(metadata)
            except json.JSONDecodeError:
                doc["metadata"] = {}
        elif isinstance(metadata, dict):
            doc["metadata"] = metadata
        else:
            doc["metadata"] = {}
    graph["embedding_kind_counts"] = kind_counts.most_common()
    graph["embedding_models"] = model_counts.most_common()
    graph["embedding_dimensions"] = dimensions.most_common()


def _embedding_model_aliases(model_key: str) -> list[str]:
    aliases = _EMBEDDING_MODEL_ALIASES.get(model_key, [model_key])
    return _dedupe([model_key, *aliases])


def _main_technologies(stats: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    technologies = []
    for language, _ in stats.get("languages", [])[:5]:
        technologies.append(language)
    technologies.extend(stats.get("package_data", {}).get("technologies", []))
    technologies.extend(stats.get("framework_hints", []))
    graph_language = graph.get("language")
    if graph_language:
        technologies.append(graph_language)
    return _dedupe(technologies)[:12]


def _repo_purpose(
    repo: dict[str, Any],
    stats: dict[str, Any],
    graph: dict[str, Any],
    technologies: list[str],
) -> str:
    if graph.get("description"):
        return str(graph["description"])
    if stats.get("readme_summary"):
        return stats["readme_summary"]
    tech = ", ".join(technologies[:4]) or "the detected stack"
    domain = _infer_domain(repo, stats, graph)
    return f"Inferred repository for {domain.lower()} using {tech}."


def _infer_domain(repo: dict[str, Any], stats: dict[str, Any], graph: dict[str, Any]) -> str:
    haystack = " ".join(
        [
            repo.get("name", ""),
            graph.get("description") or "",
            stats.get("readme_summary") or "",
            " ".join(path for path in stats.get("important_files", [])),
            " ".join(path for path in stats.get("api_files", [])),
            " ".join(path for path in stats.get("event_files", [])),
            " ".join(path for path in stats.get("security_files", [])),
        ]
    ).lower()
    domains = [
        (("payment", "checkout", "invoice", "razorpay", "stripe", "billing"), "Payments / fintech workflow"),
        (("jira", "ticket", "slack", "workflow", "review"), "Developer workflow automation"),
        (("auth", "identity", "oauth", "jwt", "permission"), "Authentication and authorization"),
        (("order", "cart", "catalog", "inventory"), "Commerce / order management"),
        (("analytics", "report", "dashboard", "metric"), "Analytics and reporting"),
        (("ml", "model", "embedding", "rag", "llm", "ai"), "AI / semantic retrieval tooling"),
        (("api", "backend", "service", "server"), "Backend application service"),
        (("web", "frontend", "react", "next", "vue"), "Frontend web application"),
    ]
    for keywords, label in domains:
        if any(keyword in haystack for keyword in keywords):
            return label
    return "General software application or library"


def _detect_architecture(stats: dict[str, Any], graph: dict[str, Any]) -> list[list[str]]:
    dirs = {name.lower() for name in stats.get("all_directories", Counter()).keys()}
    source_paths = [item["path"].lower() for item in stats.get("source_files", [])]
    files = " ".join(source_paths[:1000])
    rows: list[list[str]] = []

    def add(pattern: str, evidence: list[str], confidence: str) -> None:
        rows.append([pattern, "; ".join(evidence), confidence])

    has_controllers = bool(dirs & {"controllers", "controller"}) or any("/controllers/" in path for path in source_paths)
    has_models = bool(dirs & {"models", "model"}) or any("/models/" in path for path in source_paths)
    has_views = bool(dirs & {"views", "templates"}) or any("/views/" in path or path.endswith(".blade.php") for path in source_paths)
    if has_controllers and has_models:
        evidence = ["controller/model paths detected"]
        if has_views:
            evidence.append("view/template layer present")
        add("MVC", evidence, "medium" if "view/template layer present" in evidence else "low")

    layer_hits = []
    if dirs & {"api", "routes", "routers", "controllers"} or any(part in files for part in ("/routes/", "/controllers/", "/api/")):
        layer_hits.append("interface/API layer")
    if dirs & {"core", "domain", "services", "service", "business"} or any(part in files for part in ("/services/", "/jobs/")):
        layer_hits.append("business/domain layer")
    if dirs & {"db", "database", "repositories", "repository", "models", "dao", "persistence"} or any(part in files for part in ("/models/", "/database/", "/migrations/")):
        layer_hits.append("persistence layer")
    if len(layer_hits) >= 2:
        add("Layered architecture", layer_hits, "high" if len(layer_hits) >= 3 else "medium")

    if dirs & {"domain"} and dirs & {"application", "usecases", "use_cases"} and dirs & {"infrastructure", "infra"}:
        add("Clean Architecture", ["domain/application/infrastructure separation"], "high")
    elif dirs & {"domain"} and dirs & {"infrastructure", "infra"}:
        add("Clean Architecture", ["partial domain/infrastructure separation"], "medium")

    if dirs & _EVENT_KEYWORDS or stats.get("event_files"):
        add("Event-driven system", ["event/consumer/producer paths detected"], "medium")

    if dirs & {"commands", "queries", "command", "query", "handlers"}:
        add("CQRS", ["command/query/handler naming detected"], "medium")

    if dirs & {"repositories", "repository", "dao"} or "repository" in files:
        add("Repository pattern", ["repository/DAO naming detected"], "medium")

    if "service_locator" in files or "servicelocator" in files or "global_container" in files:
        add("Service locator anti-pattern", ["service locator style identifiers detected"], "medium")

    if (graph.get("import_edges") or 0) > 0 and (graph.get("modules") or 0) > 0:
        density = graph["import_edges"] / max(graph["modules"], 1)
        if density > 3:
            add("Highly connected module graph", [f"import edge density {density:.2f}"], "medium")

    return rows


def _application_shape(stats: dict[str, Any], architecture: list[list[str]]) -> str:
    patterns = {row[0] for row in architecture}
    if "Event-driven system" in patterns and "Layered architecture" in patterns:
        return "Layered service with event-driven responsibilities"
    if "Clean Architecture" in patterns:
        return "Clean/layered application structure"
    if "MVC" in patterns:
        return "MVC-style web application"
    if stats.get("package_data", {}).get("is_library"):
        return "Reusable library/package"
    return "Service or application repository"


def _monolith_microservice_assessment(stats: dict[str, Any], architecture: list[list[str]]) -> str:
    dirs = {name.lower() for name in stats.get("all_directories", Counter()).keys()}
    if dirs & {"apps", "packages", "services"} and len(dirs & {"apps", "packages", "services"}) >= 1:
        return "Potential monorepo or multi-service workspace"
    if stats.get("total_files", 0) > 5000 or len(dirs) > 40:
        return "Likely monolith or broad platform repository"
    if stats.get("total_files", 0) > 1000 and len(dirs) >= 5:
        return "Likely monolith or broad platform repository"
    if stats.get("entry_points") and ("Event-driven system" in {row[0] for row in architecture} or stats.get("api_files")):
        return "Likely microservice or focused backend service"
    if stats.get("package_data", {}).get("is_library"):
        return "Library/package rather than deployable service"
    return "Insufficient evidence; appears to be a focused repository"


def _directory_responsibility_rows(stats: dict[str, Any]) -> list[list[str]]:
    rows = []
    for directory, count in stats.get("directories", []):
        rows.append([directory, _role_for_directory(directory), str(count)])
    return rows or [["-", "No local directories detected", "0"]]


def _role_for_directory(directory: str) -> str:
    name = directory.lower()
    if name == ".":
        return "Repository root, configuration, entry points, and documentation"
    if name in {"api", "routes", "routers", "controllers", "controller"}:
        return "External interface and request routing"
    if name in {"core", "domain", "services", "service", "business"}:
        return "Business logic and domain behavior"
    if name in {"db", "database", "models", "repositories", "repository", "dao", "persistence"}:
        return "Persistence, data access, and storage models"
    if name in {"events", "event", "consumers", "consumer", "producers", "producer", "workers", "jobs"}:
        return "Asynchronous processing and event flow"
    if name in {"tests", "test", "__tests__", "spec"}:
        return "Automated tests"
    if name in {"docs", "documentation"}:
        return "Human-facing documentation"
    if name in {"config", "settings"}:
        return "Runtime configuration"
    if name in {"src", "app", "lib"}:
        return "Primary source tree"
    return "Feature or implementation area inferred from path"


def _layering_summary(stats: dict[str, Any]) -> str:
    roles = [_role_for_directory(name) for name, _ in stats.get("directories", [])]
    paths = [item["path"].lower() for item in stats.get("source_files", [])]
    has_interface = any("External interface" in role for role in roles) or any(
        marker in path for path in paths for marker in ("/routes/", "/controllers/", "/api/")
    )
    has_persistence = any("Persistence" in role for role in roles) or any(
        marker in path for path in paths for marker in ("/models/", "/database/", "/migrations/")
    )
    has_business = any(marker in path for path in paths for marker in ("/services/", "/jobs/", "/app/"))
    if has_interface and has_persistence and has_business:
        return "interface, business, and persistence boundaries are visible"
    if has_interface:
        return "interface layer is visible; persistence/domain boundaries are less explicit"
    return "layering is not obvious from top-level directories"


def _feature_grouping_summary(stats: dict[str, Any]) -> str:
    directories = [name for name, _ in stats.get("directories", []) if name != "."]
    if len(directories) >= 12:
        return "many top-level areas; feature ownership may be distributed across directories"
    if directories:
        return f"primary feature areas appear to be {', '.join(directories[:6])}"
    return "no clear feature grouping detected"


def _semantic_clusters(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vector_docs = [
        doc for doc in docs
        if isinstance(doc.get("embedding"), list) and len(doc.get("embedding") or []) >= 8
    ][:180]
    clusters: list[dict[str, Any]] = []
    threshold = 0.78
    for doc in vector_docs:
        vector = doc["embedding"]
        best_cluster = None
        best_score = 0.0
        for cluster in clusters:
            score = _cosine_similarity(vector, cluster["centroid"])
            if score > best_score:
                best_score = score
                best_cluster = cluster
        if best_cluster and best_score >= threshold:
            best_cluster["docs"].append(doc)
            n = len(best_cluster["docs"])
            best_cluster["centroid"] = [
                (old * (n - 1) + new) / n
                for old, new in zip(best_cluster["centroid"], vector)
            ]
        else:
            clusters.append({"docs": [doc], "centroid": vector[:]})

    useful = []
    for cluster in clusters:
        if len(cluster["docs"]) < 2:
            continue
        docs_in_cluster = cluster["docs"][:8]
        useful.append(
            {
                "label": _cluster_label(docs_in_cluster),
                "kind": _dominant([doc.get("kind") or "unknown" for doc in docs_in_cluster]),
                "size": len(cluster["docs"]),
                "avg_similarity": _average_pair_similarity(docs_in_cluster),
                "members": [_embedding_doc_label(doc) for doc in docs_in_cluster],
            }
        )
    useful.sort(key=lambda item: (item["size"], item["avg_similarity"]), reverse=True)
    return useful[:12]


def _semantic_cluster_section(clusters: list[dict[str, Any]], graph: dict[str, Any]) -> str:
    if not graph.get("embedding_docs"):
        available = [
            item for item in (graph.get("available_embedding_models") or [])
            if item.get("documents")
        ]
        if available:
            models = ", ".join(f"{item.get('model')} ({item.get('documents')})" for item in available)
            return (
                "No `EmbeddingDocument` rows were found for the selected model. "
                f"Available model documents for this repository: {models}."
            )
        return "No `EmbeddingDocument` rows were found for this repository. Rebuild semantic embeddings before using clustering."
    if not clusters:
        return (
            "Embedding documents exist, but there were not enough vector-bearing documents with strong similarity "
            "to form clusters. This often means the repo has sparse embeddings or only high-level repo/commit docs."
        )
    rows = [
        [
            cluster["label"],
            cluster["kind"],
            str(cluster["size"]),
            f"{cluster['avg_similarity']:.2f}",
            "<br>".join(cluster["members"][:5]),
        ]
        for cluster in clusters
    ]
    return _markdown_table(["Cluster", "Dominant kind", "Items", "Avg similarity", "Examples"], rows)


def _dependency_graph_section(stats: dict[str, Any], graph: dict[str, Any]) -> str:
    parts = [
        _markdown_table(
            ["Metric", "Value"],
            [
                ["Modules indexed", str(graph.get("modules") or 0)],
                ["Module import edges", str(graph.get("import_edges") or 0)],
                ["Functions indexed", str(graph.get("functions") or 0)],
                ["Function call edges", str(graph.get("call_edges") or 0)],
                ["Circular dependencies found", str(len(graph.get("circular_dependencies") or []))],
            ],
        ),
        "",
        "Most connected modules:",
        "",
        _centrality_table(graph.get("module_centrality", [])),
        "",
        "Most connected functions:",
        "",
        _centrality_table(graph.get("function_centrality", [])),
        "",
        "Top local imports/dependencies:",
        "",
        _counter_table("Dependency", "References", stats.get("import_dependencies", [])),
    ]
    cycles = graph.get("circular_dependencies") or []
    if cycles:
        parts.extend(["", "Circular dependency samples:", "", _bullet_list([" -> ".join(cycle) for cycle in cycles])])
    return "\n".join(parts)


def _centrality_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return _markdown_table(["Node", "File", "In-degree", "Out-degree", "Centrality"], [["-", "-", "0", "0", "0"]])
    return _markdown_table(
        ["Node", "File", "In-degree", "Out-degree", "Centrality"],
        [
            [
                row.get("name") or "-",
                row.get("file_path") or "-",
                str(row.get("in_degree") or 0),
                str(row.get("out_degree") or 0),
                str(row.get("degree") or 0),
            ]
            for row in rows[:10]
        ],
    )


def _complexity_section(stats: dict[str, Any], graph: dict[str, Any]) -> str:
    density = (graph.get("import_edges") or 0) / max(graph.get("modules") or 1, 1)
    parts = [
        _markdown_table(
            ["Metric", "Value"],
            [
                ["Files inspected", str(stats.get("total_files") or 0)],
                ["Approximate source/config lines", str(stats.get("source_lines") or 0)],
                ["Large files >=250 lines", str(len(stats.get("large_files") or []))],
                ["Complex units detected", str(len(stats.get("complex_units") or []))],
                ["Module dependency density", f"{density:.2f}"],
                ["Deep inheritance samples", str(len(graph.get("inheritance_depth") or []))],
            ],
        ),
        "",
        "Largest files:",
        "",
        _markdown_table(
            ["Path", "Lines", "Estimated complexity"],
            [
                [item["path"], str(item["lines"]), str(item["complexity"])]
                for item in stats.get("large_files", [])[:10]
            ] or [["-", "0", "0"]],
        ),
        "",
        "Highest-complexity local units:",
        "",
        _markdown_table(
            ["Kind", "Name", "Path", "Lines", "Cyclomatic estimate"],
            [
                [
                    item.get("kind") or "unit",
                    item.get("name") or "-",
                    item.get("path") or "-",
                    str(item.get("lines") or 0),
                    str(item.get("complexity") or 0),
                ]
                for item in stats.get("complex_units", [])[:10]
            ] or [["-", "-", "-", "0", "0"]],
        ),
    ]
    inheritance = graph.get("inheritance_depth") or []
    if inheritance:
        parts.extend(
            [
                "",
                "Deepest inheritance paths:",
                "",
                _markdown_table(
                    ["Class", "File", "Depth"],
                    [
                        [item.get("class_name") or "-", item.get("file_path") or "-", str(item.get("depth") or 0)]
                        for item in inheritance
                    ],
                ),
            ]
        )
    return "\n".join(parts)


def _semantic_search_quality_section(graph: dict[str, Any], clusters: list[dict[str, Any]]) -> str:
    docs = graph.get("embedding_docs") or []
    model = ", ".join(f"{name} ({count})" for name, count in graph.get("embedding_models", [])) or "-"
    dimensions = ", ".join(f"{name} ({count})" for name, count in graph.get("embedding_dimensions", [])) or "-"
    kind_counts = ", ".join(f"{name}: {count}" for name, count in graph.get("embedding_kind_counts", [])) or "-"
    available_models = ", ".join(
        f"{item.get('model')} ({item.get('documents')})"
        for item in graph.get("available_embedding_models", [])
        if item.get("documents")
    ) or "-"
    if not docs:
        assessment = "Not ready: no repository embedding documents are available."
    elif clusters:
        assessment = "Good baseline: vector-bearing documents form meaningful semantic neighborhoods."
    else:
        assessment = "Partial: embeddings exist, but clustering signal is weak or too sparse."
    retrieval_examples = [
        "Find authentication or permission flows",
        "Find persistence/database access paths",
        "Find event consumers/producers and retry logic",
        "Find files related to a recent high-touch area",
    ]
    return "\n".join(
        [
            _markdown_table(
                ["Item", "Value"],
                [
                    ["Embedding model", model],
                    ["Available models in Neo4j", available_models],
                    ["Embedding dimensions", dimensions],
                    ["Documents by kind", kind_counts],
                    ["Chunking strategy", "One `EmbeddingDocument` per graph item such as repo, commit, file, or future function chunks."],
                    ["Similarity effectiveness", assessment],
                ],
            ),
            "",
            "Retrieval examples to validate quality:",
            "",
            _bullet_list(retrieval_examples),
        ]
    )


def _graph_schema_section() -> str:
    node_table = _markdown_table(
        ["Node type", "Description", "Key metadata"],
        [
            ["Repo", "Repository identity and source metadata", "full_name, name, owner, language, url, local_path"],
            ["Commit", "Git commit history", "sha, summary, authored_at, committed_at, additions, deletions"],
            ["Author", "Commit or PR author", "email, name"],
            ["File", "Repository file", "repo_full_name, path, extension, current"],
            ["Function", "AST function definition", "qualified_name, file_path, start_line, end_line, ast_hash"],
            ["Class", "AST class definition", "qualified_name, file_path, start_line, end_line, ast_hash"],
            ["Module", "AST/import module", "qualified_name, file_path, language"],
            ["EmbeddingDocument", "Vector-search document linked to source graph item", "kind, source_key, title, text, embedding_model_key, embedding_model, embedding_dimensions"],
            ["JiraTicket", "Jira ticket node when Jira graph sync is enabled", "key, summary, status, priority, assignee"],
        ],
    )
    edge_table = _markdown_table(
        ["Relationship", "Meaning"],
        [
            ["IN_REPO", "Commit, File, Branch, or PR belongs to a repository"],
            ["AUTHORED_BY", "Commit or PR was authored by an Author"],
            ["PARENT", "Commit parent relationship"],
            ["TOUCHES", "Commit changed a File, with change type/additions/deletions"],
            ["DEFINED_IN", "Function/Class belongs to a File"],
            ["CALLS", "Function invokes another Function"],
            ["METHOD_OF", "Function is a method of a Class"],
            ["EXTENDS", "Class inheritance relationship"],
            ["IMPORTS", "Module imports another Module"],
            ["EMBEDS", "EmbeddingDocument represents a Repo, Commit, File, or JiraTicket"],
        ],
    )
    return f"{node_table}\n\n{edge_table}"


def _rag_readiness_section(stats: dict[str, Any], graph: dict[str, Any]) -> str:
    embedding_count = graph.get("embedding_documents") or 0
    graph_files = graph.get("graph_files") or 0
    functions = graph.get("functions") or 0
    coverage = embedding_count / max(graph_files + functions, 1)
    readiness = "high" if embedding_count and coverage >= 0.8 else "medium" if embedding_count else "low"
    notes = [
        f"Hybrid retrieval readiness: {readiness}",
        f"Graph + vector retrieval: {'available' if embedding_count else 'not yet available for this repo'}",
        f"Metadata filtering: repo_full_name, kind, source_key, title, and JSON metadata are available on embedding documents.",
        f"Context window efficiency: {'good' if embedding_count and graph_files else 'limited until file/function chunks are embedded'}",
    ]
    if functions == 0:
        notes.append("AST function chunks are not indexed yet, so function-level retrieval will be limited.")
    if stats.get("source_lines", 0) > 100_000 and embedding_count < graph_files:
        notes.append("Large source footprint suggests chunk-level source embeddings would improve retrieval precision.")
    return _bullet_list(notes)


def _cross_reference_section(stats: dict[str, Any], graph: dict[str, Any]) -> str:
    function_edges = graph.get("function_edges") or []
    rows = [
        [
            edge.get("caller") or "-",
            edge.get("callee") or "-",
            edge.get("caller_file") or "-",
        ]
        for edge in function_edges[:10]
    ]
    parts = [
        "Function call samples:",
        "",
        _markdown_table(["Caller", "Callee", "Caller file"], rows or [["-", "-", "No function call edges indexed."]]),
        "",
        "API / database / event lineage hints from local paths:",
        "",
        _markdown_table(
            ["Flow area", "Detected files"],
            [
                ["API endpoints", "<br>".join(stats.get("api_files", [])[:8]) or "-"],
                ["Database/persistence", "<br>".join(stats.get("db_files", [])[:8]) or "-"],
                ["Events/queues", "<br>".join(stats.get("event_files", [])[:8]) or "-"],
            ],
        ),
    ]
    return "\n".join(parts)


def _hotspot_section(
    stats: dict[str, Any],
    graph: dict[str, Any],
    clusters: list[dict[str, Any]],
) -> str:
    central_nodes = (graph.get("module_centrality") or [])[:5] + (graph.get("function_centrality") or [])[:5]
    return "\n".join(
        [
            "Change-prone files from git graph:",
            "",
            _markdown_table(
                ["Path", "Touches"],
                [[f.get("path") or "-", str(f.get("touches") or 0)] for f in graph.get("hot_files", [])[:10]]
                or [["-", "0"]],
            ),
            "",
            "Architectural hotspots by centrality:",
            "",
            _markdown_table(
                ["Node", "File", "Centrality"],
                [
                    [n.get("name") or "-", n.get("file_path") or "-", str(n.get("degree") or 0)]
                    for n in central_nodes
                ] or [["-", "-", "0"]],
            ),
            "",
            "Semantic hotspots:",
            "",
            _markdown_table(
                ["Cluster", "Items", "Average similarity"],
                [[c["label"], str(c["size"]), f"{c['avg_similarity']:.2f}"] for c in clusters[:8]]
                or [["-", "0", "0.00"]],
            ),
            "",
            "Local complexity hotspots:",
            "",
            _markdown_table(
                ["Path", "Lines", "Complexity"],
                [
                    [item["path"], str(item["lines"]), str(item["complexity"])]
                    for item in stats.get("large_files", [])[:8]
                ] or [["-", "0", "0"]],
            ),
        ]
    )


def _duplicate_logic_section(stats: dict[str, Any], duplicate_pairs: list[dict[str, Any]]) -> str:
    parts = [
        "High-similarity embedding pairs:",
        "",
        _markdown_table(
            ["Similarity", "Item A", "Item B"],
            [
                [f"{pair['similarity']:.2f}", pair["a"], pair["b"]]
                for pair in duplicate_pairs[:12]
            ] or [["-", "No high-similarity pairs found.", "-"]],
        ),
        "",
        "Repeated filenames that may indicate duplicated responsibilities:",
        "",
        _markdown_table(
            ["Filename", "Count", "Examples"],
            [
                [item["name"], str(item["count"]), "<br>".join(item["paths"][:5])]
                for item in stats.get("duplicate_filenames", [])[:10]
            ] or [["-", "0", "-"]],
        ),
    ]
    return "\n".join(parts)


def _documentation_section(stats: dict[str, Any], graph: dict[str, Any]) -> str:
    docs = stats.get("documentation_files") or []
    top_dirs = [name for name, _ in stats.get("directories", []) if name != "."]
    ratio = len(docs) / max(len(top_dirs), 1)
    if ratio >= 0.8:
        assessment = "Good: documentation coverage broadly matches visible module count."
    elif docs:
        assessment = "Partial: documentation exists, but several modules may be undocumented."
    else:
        assessment = "Low: no Markdown/RST/AsciiDoc files were detected."
    undocumented = [
        directory for directory in top_dirs
        if not any(doc.startswith(f"{directory}/") for doc in docs)
    ][:10]
    return "\n".join(
        [
            _markdown_table(
                ["Metric", "Value"],
                [
                    ["Documentation files", str(len(docs))],
                    ["Top-level code/module directories", str(len(top_dirs))],
                    ["Coverage assessment", assessment],
                    ["README summary", stats.get("readme_summary") or "-"],
                    ["Embedding docs available", str(graph.get("embedding_documents") or 0)],
                ],
            ),
            "",
            "Potentially undocumented modules:",
            "",
            _bullet_list(undocumented or ["No obvious undocumented top-level modules detected."]),
        ]
    )


def _security_risk_section(stats: dict[str, Any], graph: dict[str, Any]) -> str:
    integrations = _external_integration_hints(stats)
    risk_notes = []
    if stats.get("security_files"):
        risk_notes.append("Security-sensitive paths exist; review auth, permission, token, and admin flows.")
    if integrations:
        risk_notes.append("External integrations are present; validate timeout, retry, and credential handling.")
    if graph.get("function_centrality"):
        risk_notes.append("High-centrality functions should have tests and guardrail checks because failures can fan out.")
    if not risk_notes:
        risk_notes.append("No obvious security-sensitive path names were detected; this is not a substitute for SAST/secret scanning.")
    return "\n".join(
        [
            _markdown_table(
                ["Risk area", "Evidence"],
                [
                    ["Sensitive paths", "<br>".join(stats.get("security_files", [])[:12]) or "-"],
                    ["External integrations/dependencies", ", ".join(integrations[:20]) or "-"],
                    ["Auth bypass graph evidence", "Requires populated AST call graph; not directly provable from current local scan."],
                    ["Dependency risks", "Review lockfiles and package manifests listed in key project files."],
                ],
            ),
            "",
            _bullet_list(risk_notes),
        ]
    )


def _suggest_improvements(
    stats: dict[str, Any],
    graph: dict[str, Any],
    clusters: list[dict[str, Any]],
    duplicate_pairs: list[dict[str, Any]],
) -> list[str]:
    suggestions = []
    if stats.get("large_files"):
        suggestions.append("Split oversized modules and move cohesive responsibilities into smaller units.")
    if graph.get("circular_dependencies"):
        suggestions.append("Reduce circular imports by introducing stable interfaces or moving shared contracts to lower-level modules.")
    if duplicate_pairs:
        suggestions.append("Review high-similarity embedding pairs and merge repeated business logic where ownership overlaps.")
    if clusters and any(cluster["size"] >= 5 for cluster in clusters):
        suggestions.append("Use semantic clusters as refactoring candidates; large clusters can reveal hidden coupling or broad responsibilities.")
    if not graph.get("functions"):
        suggestions.append("Run or implement the AST ingestion layer so Function/Class/Module nodes can power call-chain and complexity analysis.")
    if not graph.get("embedding_documents"):
        suggestions.append("Rebuild semantic embeddings for this repository to enable clustering, duplicate detection, and hybrid RAG retrieval.")
    if graph.get("module_centrality"):
        suggestions.append("Add focused tests around high-centrality modules because they act as dependency bottlenecks.")
    if len(stats.get("documentation_files", [])) < max(1, len(stats.get("directories", [])) // 4):
        suggestions.append("Add module-level documentation for top-level directories to reduce code/documentation drift.")
    if stats.get("security_files"):
        suggestions.append("Add explicit security flow tests for auth, token, permission, and admin code paths.")
    if not suggestions:
        suggestions.append("Keep graph and embedding rebuilds in CI so this report remains fresh after major code changes.")
    return suggestions


def _similar_embedding_pairs(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vector_docs = [
        doc for doc in docs
        if isinstance(doc.get("embedding"), list)
        and len(doc.get("embedding") or []) >= 8
        and (doc.get("kind") or "") in {"file", "function", "service", "commit"}
    ][:160]
    pairs = []
    for i, left in enumerate(vector_docs):
        for right in vector_docs[i + 1:]:
            similarity = _cosine_similarity(left["embedding"], right["embedding"])
            if similarity >= 0.92:
                pairs.append(
                    {
                        "similarity": similarity,
                        "a": _embedding_doc_label(left),
                        "b": _embedding_doc_label(right),
                    }
                )
    pairs.sort(key=lambda item: item["similarity"], reverse=True)
    return pairs[:20]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if not mag_a or not mag_b:
        return 0.0
    return dot / (mag_a * mag_b)


def _average_pair_similarity(docs: list[dict[str, Any]]) -> float:
    scores = []
    for i, left in enumerate(docs):
        for right in docs[i + 1:]:
            scores.append(_cosine_similarity(left["embedding"], right["embedding"]))
    return sum(scores) / len(scores) if scores else 0.0


def _cluster_label(docs: list[dict[str, Any]]) -> str:
    labels = [_embedding_doc_label(doc) for doc in docs]
    prefixes = [label.split("/", 1)[0] for label in labels if "/" in label]
    if prefixes:
        common = _dominant(prefixes)
        if common:
            return common
    tokens = []
    for label in labels:
        tokens.extend(re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", label.lower()))
    stop = {"src", "app", "index", "test", "tests", "file", "commit"}
    ranked = [token for token, _ in Counter(t for t in tokens if t not in stop).most_common(3)]
    return " / ".join(ranked) if ranked else "semantic group"


def _embedding_doc_label(doc: dict[str, Any]) -> str:
    metadata = doc.get("metadata") or {}
    return (
        metadata.get("path")
        or doc.get("title")
        or doc.get("source_key")
        or doc.get("id")
        or "embedding document"
    )


def _dominant(values: list[str]) -> str:
    return Counter(values).most_common(1)[0][0] if values else ""


def _external_integration_hints(stats: dict[str, Any]) -> list[str]:
    hints = []
    integration_terms = {
        "requests",
        "httpx",
        "axios",
        "boto3",
        "aws-sdk",
        "stripe",
        "razorpay",
        "kafka",
        "redis",
        "postgres",
        "mysql",
        "mongodb",
        "slack",
        "jira",
        "openai",
        "anthropic",
    }
    for dep, _ in stats.get("import_dependencies", []):
        if dep.lower() in integration_terms:
            hints.append(dep)
    hints.extend(stats.get("package_data", {}).get("external_integrations", []))
    return _dedupe(hints)


def _analyze_source_file(path: Path, rel_path: str) -> dict[str, Any]:
    text = _read_text_if_small(path)
    if text is None:
        return {"lines": 0, "file_complexity": 0, "complex_units": [], "imports": []}
    lines = text.count("\n") + (1 if text else 0)
    file_complexity = _estimate_complexity(text)
    imports = _extract_imports(text, path.suffix.lower())
    complex_units = []
    if path.suffix.lower() == ".py":
        complex_units = _python_complexity_units(text, rel_path)
    elif path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx"}:
        complex_units = _simple_function_units(text, rel_path)
    elif path.suffix.lower() == ".php":
        complex_units = _php_complexity_units(text, rel_path)
    if file_complexity >= 25:
        complex_units.append(
            {
                "kind": "file",
                "name": Path(rel_path).name,
                "path": rel_path,
                "lines": lines,
                "complexity": file_complexity,
            }
        )
    return {
        "lines": lines,
        "file_complexity": file_complexity,
        "complex_units": complex_units,
        "imports": imports,
    }


def _read_text_if_small(path: Path, max_bytes: int = 1_500_000) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _estimate_complexity(text: str) -> int:
    lower = text.lower()
    score = 1
    for keyword in _COMPLEXITY_KEYWORDS:
        if keyword in {"&&", "||", "?"}:
            score += lower.count(keyword)
        else:
            score += len(re.findall(rf"\b{re.escape(keyword)}\b", lower))
    return score


def _python_complexity_units(text: str, rel_path: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    units = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            units.append(
                {
                    "kind": "function",
                    "name": node.name,
                    "path": rel_path,
                    "lines": max(0, (getattr(node, "end_lineno", node.lineno) or node.lineno) - node.lineno + 1),
                    "complexity": _python_node_complexity(node),
                }
            )
        elif isinstance(node, ast.ClassDef):
            method_count = sum(isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) for child in node.body)
            units.append(
                {
                    "kind": "class",
                    "name": node.name,
                    "path": rel_path,
                    "lines": max(0, (getattr(node, "end_lineno", node.lineno) or node.lineno) - node.lineno + 1),
                    "complexity": _python_node_complexity(node) + method_count,
                }
            )
    return [unit for unit in units if unit["complexity"] >= 8 or unit["lines"] >= 120]


def _python_node_complexity(node: ast.AST) -> int:
    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.ExceptHandler,
        ast.BoolOp,
        ast.IfExp,
        ast.Match,
        ast.With,
        ast.AsyncWith,
    )
    return 1 + sum(isinstance(child, branch_nodes) for child in ast.walk(node))


def _simple_function_units(text: str, rel_path: str) -> list[dict[str, Any]]:
    units = []
    patterns = [
        re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\("),
        re.compile(r"\bconst\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
        re.compile(r"\b([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{"),
    ]
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        name = None
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                name = match.group(1)
                break
        if not name:
            continue
        if name in {"if", "for", "while", "switch", "catch", "function"}:
            continue
        window = "\n".join(lines[idx - 1: min(len(lines), idx + 80)])
        complexity = _estimate_complexity(window)
        if complexity >= 8:
            units.append(
                {
                    "kind": "function",
                    "name": name,
                    "path": rel_path,
                    "lines": min(80, max(1, len(lines) - idx + 1)),
                    "complexity": complexity,
                }
            )
    return units[:25]


def _php_complexity_units(text: str, rel_path: str) -> list[dict[str, Any]]:
    units = []
    lines = text.splitlines()
    patterns = [
        re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    ]
    for idx, line in enumerate(lines, start=1):
        name = None
        kind = "function"
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                name = match.group(1)
                if pattern.pattern.startswith("\\bclass"):
                    kind = "class"
                break
        if not name:
            continue
        window = "\n".join(lines[idx - 1: min(len(lines), idx + 120)])
        complexity = _estimate_complexity(window)
        if complexity >= 8:
            units.append(
                {
                    "kind": kind,
                    "name": name,
                    "path": rel_path,
                    "lines": min(120, max(1, len(lines) - idx + 1)),
                    "complexity": complexity,
                }
            )
    return units[:25]


def _extract_imports(text: str, extension: str) -> list[str]:
    imports = []
    if extension == ".py":
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("import "):
                imports.extend(part.strip().split(" ")[0].split(".")[0] for part in stripped[7:].split(","))
            elif stripped.startswith("from "):
                parts = stripped.split()
                if len(parts) >= 2:
                    imports.append(parts[1].split(".")[0])
    elif extension in {".js", ".jsx", ".ts", ".tsx"}:
        for match in re.finditer(r"(?:from\s+|require\()\s*['\"]([^'\"]+)['\"]", text):
            value = match.group(1)
            if value.startswith("."):
                continue
            imports.append(value.split("/")[0] if not value.startswith("@") else "/".join(value.split("/")[:2]))
    elif extension == ".php":
        for match in re.finditer(r"^\s*use\s+([^;]+);", text, flags=re.MULTILINE):
            value = match.group(1).strip().lstrip("\\")
            if value:
                imports.append(value.split("\\")[0])
        for match in re.finditer(r"\b(?:include|include_once|require|require_once)\s*(?:\(|\s)\s*['\"]([^'\"]+)['\"]", text):
            value = match.group(1)
            if not value.startswith("."):
                imports.append(value.split("/")[0])
    return [item for item in imports if item and item not in {"__future__"}]


def _framework_hints(
    root: Path,
    source_files: list[dict[str, Any]],
    package_data: dict[str, Any],
) -> list[str]:
    hints = []
    paths = {item.get("path", "").replace("\\", "/") for item in source_files}
    technologies = set(package_data.get("technologies", []))
    if "Laravel" in technologies or {
        "artisan",
        "app/Http/Kernel.php",
        "bootstrap/app.php",
        "config/app.php",
    } & paths:
        hints.append("Laravel")
    if any(path.endswith(".blade.php") or "/resources/views/" in path for path in paths):
        hints.append("Blade templates")
    if any("/routes/" in path or path.startswith("routes/") for path in paths):
        hints.append("Route-driven web/API layer")
    if any("/app/Jobs/" in path or "/jobs/" in path.lower() for path in paths):
        hints.append("Background jobs/queues")
    if any("/app/Models/" in path or "/models/" in path.lower() for path in paths):
        hints.append("ORM/model layer")
    if (root / ".github" / "workflows").exists():
        hints.append("GitHub Actions")
    return _dedupe(hints)


def _read_package_data(root: Path) -> dict[str, Any]:
    data: dict[str, Any] = {
        "technologies": [],
        "entry_points": [],
        "external_integrations": [],
        "is_library": False,
        "manifests": [],
    }
    if not root.exists():
        return data

    for package_json in _find_manifests(root, "package.json"):
        rel = str(package_json.relative_to(root))
        data["manifests"].append(rel)
        try:
            package = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, json.JSONDecodeError):
            package = {}
        dependencies = {
            **(package.get("dependencies") or {}),
            **(package.get("devDependencies") or {}),
        }
        data["technologies"].extend(_technology_from_dependencies(dependencies.keys()))
        data["external_integrations"].extend(_integration_from_dependencies(dependencies.keys()))
        scripts = package.get("scripts") or {}
        for name, command in list(scripts.items())[:8]:
            data["entry_points"].append(f"{rel} script `{name}`: {command}")
        data["is_library"] = data["is_library"] or bool(package.get("main") or package.get("exports"))

    for composer_json in _find_manifests(root, "composer.json"):
        rel = str(composer_json.relative_to(root))
        data["manifests"].append(rel)
        try:
            composer = json.loads(composer_json.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, json.JSONDecodeError):
            composer = {}
        dependencies = {
            **(composer.get("require") or {}),
            **(composer.get("require-dev") or {}),
        }
        data["technologies"].extend(_technology_from_dependencies(dependencies.keys()))
        data["external_integrations"].extend(_integration_from_dependencies(dependencies.keys()))
        data["is_library"] = data["is_library"] or bool(composer.get("type") == "library")
        scripts = composer.get("scripts") or {}
        if isinstance(scripts, dict):
            for name in list(scripts.keys())[:8]:
                data["entry_points"].append(f"{rel} script `{name}`")

    for requirements in _find_manifests(root, "requirements.txt"):
        rel = str(requirements.relative_to(root))
        data["manifests"].append(rel)
        packages = []
        for line in requirements.read_text(encoding="utf-8", errors="ignore").splitlines():
            clean = line.strip()
            if clean and not clean.startswith("#"):
                packages.append(re.split(r"[<>=~!]", clean, 1)[0].strip().lower())
        data["technologies"].extend(_technology_from_dependencies(packages))
        data["external_integrations"].extend(_integration_from_dependencies(packages))

    for pyproject in _find_manifests(root, "pyproject.toml"):
        rel = str(pyproject.relative_to(root))
        data["manifests"].append(rel)
        text = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
        data["is_library"] = data["is_library"] or "[project]" in text or "[tool.poetry]" in text
        data["technologies"].extend(_technology_from_dependencies(re.findall(r"[a-z0-9_.-]+", text)))

    if (root / "Dockerfile").exists():
        data["technologies"].append("Docker")
    if (root / "docker-compose.yml").exists() or (root / "compose.yml").exists():
        data["technologies"].append("Docker Compose")

    data["technologies"] = _dedupe(data["technologies"])
    data["entry_points"] = _dedupe(data["entry_points"])
    data["external_integrations"] = _dedupe(data["external_integrations"])
    data["manifests"] = _dedupe(data["manifests"])
    return data


def _find_manifests(root: Path, filename: str, max_depth: int = 4) -> list[Path]:
    manifests = []
    for path in root.rglob(filename):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        if _manifest_depth(rel) > max_depth:
            continue
        manifests.append(path)
    return sorted(manifests, key=lambda item: (len(item.relative_to(root).parts), str(item)))[:20]


def _manifest_depth(path: Path) -> int:
    return max(0, len(path.parts) - 1)


def _technology_from_dependencies(dependencies: Any) -> list[str]:
    mapping = {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "pydantic": "Pydantic",
        "sqlalchemy": "SQLAlchemy",
        "psycopg": "PostgreSQL",
        "psycopg2": "PostgreSQL",
        "asyncpg": "PostgreSQL",
        "neo4j": "Neo4j",
        "qdrant-client": "Qdrant",
        "kafka-python": "Kafka",
        "confluent-kafka": "Kafka",
        "celery": "Celery",
        "redis": "Redis",
        "react": "React",
        "next": "Next.js",
        "vue": "Vue",
        "express": "Express",
        "nestjs": "NestJS",
        "typeorm": "TypeORM",
        "prisma": "Prisma",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "php": "PHP",
        "laravel/framework": "Laravel",
        "illuminate/": "Laravel",
        "guzzlehttp": "Guzzle",
        "aws/aws-sdk-php": "AWS SDK for PHP",
        "firebase/php-jwt": "JWT",
        "predis": "Redis",
        "phpoffice": "Office document tooling",
    }
    found = []
    for dep in dependencies:
        dep_l = str(dep).lower()
        for key, value in mapping.items():
            if key in dep_l:
                found.append(value)
    return found


def _integration_from_dependencies(dependencies: Any) -> list[str]:
    mapping = {
        "requests": "HTTP APIs",
        "httpx": "HTTP APIs",
        "axios": "HTTP APIs",
        "boto3": "AWS",
        "aws-sdk": "AWS",
        "stripe": "Stripe",
        "razorpay": "Razorpay",
        "slack": "Slack",
        "jira": "Jira",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "kafka": "Kafka",
        "redis": "Redis",
        "sentry": "Sentry",
        "guzzlehttp": "HTTP APIs",
        "aws/aws-sdk-php": "AWS",
        "firebase": "Firebase",
        "predis": "Redis",
        "mysql": "MySQL",
    }
    found = []
    for dep in dependencies:
        dep_l = str(dep).lower()
        for key, value in mapping.items():
            if key in dep_l:
                found.append(value)
    return found


def _read_readme_summary(root: Path) -> str:
    for name in ("README.md", "README.rst", "README.adoc", "readme.md"):
        path = root / name
        if not path.exists():
            continue
        text = _read_text_if_small(path, max_bytes=300_000) or ""
        paragraphs = []
        current = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
                continue
            if stripped.startswith(("#", "=", "-", "![", "[!")):
                continue
            current.append(stripped)
            if len(" ".join(current)) > 500:
                break
        if current:
            paragraphs.append(" ".join(current))
        for paragraph in paragraphs:
            if len(paragraph) > 40:
                return paragraph[:700]
    return ""


def _read_docker_entrypoints(root: Path) -> list[str]:
    path = root / "Dockerfile"
    text = _read_text_if_small(path, max_bytes=200_000) if path.exists() else None
    if not text:
        return []
    entries = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith(("CMD ", "ENTRYPOINT ")):
            entries.append(f"Dockerfile {stripped}")
    return entries[:5]


def _path_has_keyword(path: str, keywords: set[str]) -> bool:
    lowered = path.lower()
    parts = set(re.split(r"[/_.-]+", lowered))
    return bool(parts & keywords) or any(keyword in lowered for keyword in keywords)


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        clean = str(value).strip()
        if not clean or clean.lower() in seen:
            continue
        seen.add(clean.lower())
        out.append(clean)
    return out


def _git_recent_commits(root: Path) -> list[list[str]]:
    output = _git(
        root,
        "log",
        "-n",
        "10",
        "--date=short",
        "--pretty=format:%h%x09%ad%x09%an%x09%s",
    )
    rows = []
    for line in (output or "").splitlines():
        parts = line.split("\t", 3)
        if len(parts) == 4:
            rows.append(parts)
    return rows


def _git(root: Path, *args: str) -> str | None:
    if not root.exists():
        return None
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _count_lines(path: Path) -> int:
    try:
        if path.stat().st_size > 1_000_000:
            return 0
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    escaped_headers = [_escape_cell(header) for header in headers]
    out = [
        "| " + " | ".join(escaped_headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        padded = [*(str(cell) for cell in row), *([""] * max(0, len(headers) - len(row)))]
        out.append("| " + " | ".join(_escape_cell(cell) for cell in padded[:len(headers)]) + " |")
    return "\n".join(out)


def _counter_table(label: str, count_label: str, rows: list[tuple[str, int]]) -> str:
    if not rows:
        return _markdown_table([label, count_label], [["-", "0"]])
    return _markdown_table([label, count_label], [[name, str(count)] for name, count in rows])


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {_escape_inline(item)}" for item in items)


def _escape_cell(value: Any) -> str:
    return _escape_inline(str(value)).replace("|", "\\|").replace("\n", "<br>")


def _escape_inline(value: str) -> str:
    return value.replace("\r", " ").strip()


def _report_filename(repositories: list[dict[str, Any]], embedding_model: str = "codebase_bge_m3") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    if len(repositories) == 1:
        slug = _slug(repositories[0]["name"])
    else:
        slug = f"{len(repositories)}-repositories"
    model_slug = _slug(embedding_model)
    return f"code-analysis-{slug}-{model_slug}-{stamp}.md"


def _slug(value: str) -> str:
    chars = [c.lower() if c.isalnum() else "-" for c in value]
    return "-".join("".join(chars).split("-")) or "repositories"

"""Centralised settings loader (local-mode).

All other modules import `settings` from here. Reads .env on import.

This version assumes:
  - Repos are already cloned on the local filesystem under SEARCH_ROOT
  - Neo4j is reachable via NEO4J_URI (typically bolt://localhost:7687)
  - No GitHub API access needed for Stage 1
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str
    neo4j_database: str = "neo4j"

    # Qdrant (Stage 3)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None

    # Local repo discovery
    search_root: Path = Field(default=Path("/home/ubuntu"))
    max_search_depth: int = 3              # how deep under SEARCH_ROOT to look for .git folders
    skip_dirs: str = ".repo-cache,node_modules,.venv,venv,env,dist,build,__pycache__"

    # Ingestion tuning
    ingest_concurrency: int = 4            # walking pygit2 is CPU-bound; modest concurrency is best
    commit_batch_size: int = 500           # commits per Neo4j transaction
    since_days: Optional[int] = None       # None = full history

    @field_validator("since_days", mode="before")
    @classmethod
    def _blank_since_days_means_full_history(cls, value: object) -> object:
        if isinstance(value, str) and (not value.strip() or value.lstrip().startswith("#")):
            return None
        return value

    # Stage 3
    anthropic_api_key: Optional[str] = None
    embed_model: str = "voyage-code-3"
    bge_m3_model_name: str = "BAAI/bge-m3"
    semantic_embedding_dimensions: int = 1024
    semantic_embed_batch_size: int = 32
    semantic_max_docs_per_run: int = 0
    voyage_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Service
    service_port: int = 8088
    service_host: str = "0.0.0.0"

    @property
    def skip_dir_set(self) -> set[str]:
        return {s.strip() for s in self.skip_dirs.split(",") if s.strip()}


settings = Settings()

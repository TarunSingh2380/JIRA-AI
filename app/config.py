"""Application configuration loaded from environment variables.

This file centralizes settings such as prompt folder path, default prompt,
LLM provider, model name, API keys, and timeout values so the rest of the
project does not read environment variables directly.
"""

import os
from dataclasses import dataclass
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv(encoding="utf-8-sig")


def _similar_ticket_match_threshold() -> float:
    raw = os.getenv("SIMILAR_TICKET_MATCH_THRESHOLD", "0.68").strip()
    if raw.endswith("%"):
        raw = raw[:-1].strip()
    try:
        value = float(raw)
    except ValueError:
        return 0.68
    if value > 1:
        value = value / 100
    return min(max(value, 0.0), 1.0)


@dataclass(frozen=True)
class Settings:
    prompt_dir: str = os.getenv("PROMPT_DIR", "Prompt")
    default_prompt: str = os.getenv("DEFAULT_PROMPT", "ticket_prompt")
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    testcase_chat_model: str = os.getenv(
        "TESTCASE_CHAT_MODEL",
        os.getenv("ANTHROPIC_MODEL", os.getenv("LLM_MODEL", "claude-sonnet-4-5")),
    )
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    llm_test_case_timeout_seconds: int = int(os.getenv("LLM_TEST_CASE_TIMEOUT_SECONDS", "300"))
    database_url_override: str = os.getenv("DATABASE_URL", "")
    db_host: str = os.getenv("DB_HOST", "")
    db_port: str = os.getenv("DB_PORT", "5432")
    db_name: str = os.getenv("DB_NAME", "")
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
    slack_default_channel_id: str = os.getenv("SLACK_DEFAULT_CHANNEL_ID", "")
    jira_base_url: str = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_project_keys: str = os.getenv("JIRA_PROJECT_KEYS", "")
    jira_approved_transition_name: str = os.getenv("JIRA_APPROVED_TRANSITION_NAME", "")
    repograph_base_url: str = os.getenv("REPOGRAPH_BASE_URL", "http://127.0.0.1:8088").rstrip("/")
    repo_tree_base_url: str = os.getenv(
        "REPO_TREE_BASE_URL",
        os.getenv("REPOTREE_BASE_URL", ""),
    ).rstrip("/")
    repo_tree_timeout_seconds: int = int(os.getenv("REPO_TREE_TIMEOUT_SECONDS", "300"))
    external_request_timeout_seconds: int = int(os.getenv("EXTERNAL_REQUEST_TIMEOUT_SECONDS", "15"))
    n8n_graph_webhook_url: str = os.getenv("N8N_GRAPH_WEBHOOK_URL", "")
    n8n_api_key: str = os.getenv("N8N_API_KEY", "")
    repository_search_root: str = os.getenv("REPOSITORY_SEARCH_ROOT", "/home/ubuntu")
    repository_host_root: str = os.getenv("REPOSITORY_HOST_ROOT", os.getenv("REPOSITORY_SEARCH_ROOT", "/home/ubuntu"))
    excluded_repository_names: str = os.getenv("EXCLUDED_REPOSITORY_NAMES", "JIRA-AI")
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    graph_job_repo_timeout_seconds: int = int(os.getenv("GRAPH_JOB_REPO_TIMEOUT_SECONDS", "3600"))
    graph_job_commit_batch_size: int = int(os.getenv("GRAPH_JOB_COMMIT_BATCH_SIZE", "500"))
    graph_job_limit_jira_issues: int = int(os.getenv("GRAPH_JOB_LIMIT_JIRA_ISSUES", "0"))
    graph_job_build_embeddings: bool = os.getenv("GRAPH_JOB_BUILD_EMBEDDINGS", "true").lower() in {"1", "true", "yes", "on"}
    graph_job_repo_concurrency: int = int(os.getenv("GRAPH_JOB_REPO_CONCURRENCY", "4"))
    codegraphcontext_enabled: bool = os.getenv("CODEGRAPHCONTEXT_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    codegraphcontext_timeout_seconds: int = int(os.getenv("CODEGRAPHCONTEXT_TIMEOUT_SECONDS", "1800"))

    # Neo4j (for Jira ticket graph)
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # Qdrant (vector store for embeddings)
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")

    # Ollama (local embedding model)
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")
    ollama_embed_timeout_seconds: int = int(os.getenv("OLLAMA_EMBED_TIMEOUT_SECONDS", "600"))
    ollama_embed_batch_size: int = int(os.getenv("OLLAMA_EMBED_BATCH_SIZE", "4"))
    ollama_embed_concurrency: int = int(os.getenv("OLLAMA_EMBED_CONCURRENCY", "1"))
    codebase_embed_max_chars: int = int(os.getenv("CODEBASE_EMBED_MAX_CHARS", "2000"))
    codebase_embed_max_files_per_repo: int = int(os.getenv("CODEBASE_EMBED_MAX_FILES_PER_REPO", "1000"))

    # Jira ticket cache TTL in hours (0 = always re-fetch)
    jira_cache_ttl_hours: int = int(os.getenv("JIRA_CACHE_TTL_HOURS", "1"))
    similar_ticket_match_threshold: float = _similar_ticket_match_threshold()

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override

        if not all([self.db_host, self.db_port, self.db_name, self.db_user]):
            return ""

        username = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        credentials = f"{username}:{password}" if password else username
        return f"postgresql://{credentials}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()

"""Application configuration loaded from environment variables.

This file centralizes settings such as prompt folder path, default prompt,
LLM provider, model name, API keys, and timeout values so the rest of the
project does not read environment variables directly.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    prompt_dir: str = os.getenv("PROMPT_DIR", "Prompt")
    default_prompt: str = os.getenv("DEFAULT_PROMPT", "ticket_prompt")
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    database_url: str = os.getenv("DATABASE_URL", "")
    slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
    slack_default_channel_id: str = os.getenv("SLACK_DEFAULT_CHANNEL_ID", "")
    jira_base_url: str = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_approved_transition_name: str = os.getenv("JIRA_APPROVED_TRANSITION_NAME", "")
    repograph_base_url: str = os.getenv("REPOGRAPH_BASE_URL", "http://127.0.0.1:8088").rstrip("/")
    external_request_timeout_seconds: int = int(os.getenv("EXTERNAL_REQUEST_TIMEOUT_SECONDS", "15"))
    n8n_graph_webhook_url: str = os.getenv("N8N_GRAPH_WEBHOOK_URL", "")
    n8n_api_key: str = os.getenv("N8N_API_KEY", "")
    repository_search_root: str = os.getenv("REPOSITORY_SEARCH_ROOT", "/home/ubuntu")
    repository_host_root: str = os.getenv("REPOSITORY_HOST_ROOT", os.getenv("REPOSITORY_SEARCH_ROOT", "/home/ubuntu"))
    excluded_repository_names: str = os.getenv("EXCLUDED_REPOSITORY_NAMES", "JIRA-AI")


settings = Settings()

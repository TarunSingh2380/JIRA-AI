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


settings = Settings()

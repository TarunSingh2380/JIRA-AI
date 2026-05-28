"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv(encoding="utf-8-sig")


@dataclass(frozen=True)
class Settings:
    prompt_dir: str = os.getenv("PROMPT_DIR", "Prompt")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    database_url_override: str = os.getenv("DATABASE_URL", "")
    db_host: str = os.getenv("DB_HOST", "")
    db_port: str = os.getenv("DB_PORT", "5432")
    db_name: str = os.getenv("DB_NAME", "")
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    jira_base_url: str = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    external_request_timeout_seconds: int = int(os.getenv("EXTERNAL_REQUEST_TIMEOUT_SECONDS", "15"))

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

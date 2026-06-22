"""Tiny key-value settings store for runtime-editable config.

Backs admin-panel toggles that must survive restarts without a redeploy (e.g.
the WF7 RFT-estimate sprint filter). One self-healing table ``app_settings``;
values are plain strings, callers parse as needed.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.config import Settings

LOGGER = logging.getLogger(__name__)


def _connect(settings: Settings):
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(settings.database_url, row_factory=dict_row)


def ensure_app_settings_schema(settings: Settings) -> None:
    if not settings.database_url:
        return
    with _connect(settings) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key        TEXT PRIMARY KEY,
                value      TEXT,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.commit()


def get_setting(settings: Settings, key: str, default: Optional[str] = None) -> Optional[str]:
    if not settings.database_url:
        return default
    try:
        with _connect(settings) as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key = %s", (key,)
            ).fetchone()
        if row and row.get("value") is not None:
            return row["value"]
    except Exception as exc:  # noqa: BLE001 - never let config reads crash a request
        LOGGER.debug("get_setting(%s) failed: %s", key, exc)
    return default


def set_setting(settings: Settings, key: str, value: str) -> None:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required to persist settings")
    ensure_app_settings_schema(settings)
    with _connect(settings) as conn:
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, updated_at = NOW()
            """,
            (key, value),
        )
        conn.commit()

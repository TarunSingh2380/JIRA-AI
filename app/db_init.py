"""Database migration runner.

Reads every *.sql file from the migrations/ directory (sorted by name) and
applies them to the configured PostgreSQL database. Each migration is tracked
in the `schema_migrations` table so it runs exactly once.

Call `run_migrations()` at application startup (FastAPI lifespan).
"""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"

_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT         PRIMARY KEY,
    applied_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
)
"""


def run_migrations(database_url: str) -> None:
    """Apply all pending SQL migrations in order. Safe to call on every startup."""
    if not database_url:
        log.warning("DATABASE_URL not set — skipping migrations")
        return

    try:
        import psycopg
    except ImportError:
        log.warning("psycopg not installed — skipping migrations")
        return

    if not MIGRATIONS_DIR.is_dir():
        log.warning("Migrations directory not found at %s", MIGRATIONS_DIR)
        return

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        log.info("No migration files found in %s", MIGRATIONS_DIR)
        return

    try:
        with psycopg.connect(database_url, autocommit=True) as conn:
            conn.execute(_CREATE_MIGRATIONS_TABLE)

            applied: set[str] = {
                row[0]
                for row in conn.execute("SELECT filename FROM schema_migrations").fetchall()
            }

            for path in migration_files:
                if path.name in applied:
                    log.debug("Migration already applied: %s", path.name)
                    continue

                log.info("Applying migration: %s", path.name)
                sql = path.read_text(encoding="utf-8")
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)",
                    (path.name,),
                )
                log.info("Migration applied: %s", path.name)

    except Exception as exc:
        log.error("Migration failed: %s", exc)
        raise

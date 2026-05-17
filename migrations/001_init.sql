-- Initial schema: all core tables for graph admin, Jira cache, and pull logs.

CREATE TABLE IF NOT EXISTS github_repositories (
    id                BIGSERIAL    PRIMARY KEY,
    name              TEXT         NOT NULL,
    full_name         TEXT         NOT NULL,
    container_path    TEXT         NOT NULL UNIQUE,
    host_path         TEXT         NOT NULL,
    remote_url        TEXT         NOT NULL DEFAULT '',
    branch            TEXT         NOT NULL DEFAULT '',
    current_commit    TEXT         NOT NULL DEFAULT '',
    last_seen         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS graph_jobs (
    job_id        UUID         PRIMARY KEY,
    action        VARCHAR(50)  NOT NULL,
    status        VARCHAR(50)  NOT NULL,
    repos_total   INTEGER      NOT NULL DEFAULT 0,
    repos_done    INTEGER      NOT NULL DEFAULT 0,
    jira_total    INTEGER      NOT NULL DEFAULT 0,
    jira_done     INTEGER      NOT NULL DEFAULT 0,
    error_msg     TEXT,
    notes         TEXT,
    options       JSONB        NOT NULL DEFAULT '{}',
    totals        JSONB        NOT NULL DEFAULT '{}',
    progress      JSONB        NOT NULL DEFAULT '{}',
    repositories  JSONB        NOT NULL DEFAULT '[]',
    jira_tickets  JSONB        NOT NULL DEFAULT '[]',
    logs          JSONB        NOT NULL DEFAULT '[]',
    started_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_graph_jobs_updated_at ON graph_jobs (updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_graph_jobs_status     ON graph_jobs (status);

CREATE TABLE IF NOT EXISTS github_pull_log (
    id              BIGSERIAL    PRIMARY KEY,
    job_id          UUID         NOT NULL REFERENCES graph_jobs (job_id) ON DELETE CASCADE,
    repo_name       TEXT         NOT NULL,
    container_path  TEXT         NOT NULL,
    success         BOOLEAN      NOT NULL,
    output          TEXT         NOT NULL DEFAULT '',
    pulled_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jira_projects (
    key           TEXT         PRIMARY KEY,
    name          TEXT         NOT NULL,
    project_type  TEXT,
    description   TEXT,
    lead_name     TEXT,
    lead_email    TEXT,
    data          JSONB        NOT NULL DEFAULT '{}',
    fetched_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jira_ticket_cache (
    ticket_key      TEXT         PRIMARY KEY,
    project_key     TEXT         NOT NULL,
    summary         TEXT         NOT NULL DEFAULT '',
    description     TEXT         NOT NULL DEFAULT '',
    status          TEXT         NOT NULL DEFAULT '',
    issue_type      TEXT         NOT NULL DEFAULT '',
    priority        TEXT         NOT NULL DEFAULT '',
    assignee_email  TEXT,
    assignee_name   TEXT,
    reporter_email  TEXT,
    reporter_name   TEXT,
    labels          TEXT[]       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ,
    data            JSONB        NOT NULL DEFAULT '{}',
    fetched_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jira_ticket_cache_project ON jira_ticket_cache (project_key);
CREATE INDEX IF NOT EXISTS idx_jira_ticket_cache_status  ON jira_ticket_cache (status);
CREATE INDEX IF NOT EXISTS idx_jira_ticket_cache_fetched ON jira_ticket_cache (fetched_at DESC);

CREATE TABLE IF NOT EXISTS jira_fetch_log (
    id             BIGSERIAL    PRIMARY KEY,
    project_key    TEXT         NOT NULL,
    ticket_count   INTEGER      NOT NULL DEFAULT 0,
    from_cache     BOOLEAN      NOT NULL DEFAULT FALSE,
    force_refresh  BOOLEAN      NOT NULL DEFAULT FALSE,
    duration_ms    INTEGER      NOT NULL DEFAULT 0,
    error          TEXT,
    fetched_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jira_fetch_log_project   ON jira_fetch_log (project_key);
CREATE INDEX IF NOT EXISTS idx_jira_fetch_log_fetched   ON jira_fetch_log (fetched_at DESC);

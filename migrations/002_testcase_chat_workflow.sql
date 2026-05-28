-- Persistence expected by the /workflow2 test-case Q&A/edit flow.

CREATE TABLE IF NOT EXISTS tickets (
    id              BIGSERIAL    PRIMARY KEY,
    jira_ticket_id  TEXT         NOT NULL,
    slack_channel_id TEXT,
    slack_thread_ts  TEXT,
    summary         TEXT         NOT NULL DEFAULT '',
    status          TEXT         NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

ALTER TABLE tickets ADD COLUMN IF NOT EXISTS jira_ticket_id TEXT;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS slack_channel_id TEXT;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS slack_thread_ts TEXT;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS summary TEXT NOT NULL DEFAULT '';
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT '';
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS idx_tickets_jira_ticket_id_unique
ON tickets (jira_ticket_id);

CREATE INDEX IF NOT EXISTS idx_tickets_slack_thread
ON tickets (slack_channel_id, slack_thread_ts, id DESC);

CREATE TABLE IF NOT EXISTS channelid_table (
    id                 BIGSERIAL    PRIMARY KEY,
    slack_channel_id   TEXT         NOT NULL,
    slack_thread_ts    TEXT         NOT NULL,
    jira_payload       JSONB        NOT NULL DEFAULT '{}',
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

ALTER TABLE channelid_table ADD COLUMN IF NOT EXISTS slack_channel_id TEXT;
ALTER TABLE channelid_table ADD COLUMN IF NOT EXISTS slack_thread_ts TEXT;
ALTER TABLE channelid_table ADD COLUMN IF NOT EXISTS jira_payload JSONB NOT NULL DEFAULT '{}';
ALTER TABLE channelid_table ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_channelid_table_slack_thread
ON channelid_table (slack_channel_id, slack_thread_ts, created_at DESC);

CREATE TABLE IF NOT EXISTS test_cases (
    id              BIGSERIAL    PRIMARY KEY,
    ticket_id       BIGINT       REFERENCES tickets (id) ON DELETE CASCADE,
    jira_ticket_id  TEXT         NOT NULL,
    tc_index        INTEGER      NOT NULL,
    subtask_key     TEXT,
    title           TEXT         NOT NULL DEFAULT '',
    steps           JSONB        NOT NULL DEFAULT '[]',
    expected        TEXT         NOT NULL DEFAULT '',
    status          TEXT         NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS ticket_id BIGINT REFERENCES tickets (id) ON DELETE CASCADE;
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS jira_ticket_id TEXT;
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS tc_index INTEGER;
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS subtask_key TEXT;
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS title TEXT NOT NULL DEFAULT '';
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS steps JSONB NOT NULL DEFAULT '[]';
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS expected TEXT NOT NULL DEFAULT '';
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS idx_test_cases_jira_ticket_index_unique
ON test_cases (jira_ticket_id, tc_index);

CREATE INDEX IF NOT EXISTS idx_test_cases_ticket_id
ON test_cases (ticket_id);

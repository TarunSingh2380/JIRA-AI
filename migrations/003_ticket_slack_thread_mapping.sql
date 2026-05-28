-- Current Workflow2 maps Slack test-case replies through tickets.

ALTER TABLE tickets ADD COLUMN IF NOT EXISTS slack_channel_id TEXT;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS slack_thread_ts TEXT;

CREATE INDEX IF NOT EXISTS idx_tickets_slack_thread
ON tickets (slack_channel_id, slack_thread_ts, id DESC);

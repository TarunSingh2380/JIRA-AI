# Jira AI Ticket Analyzer

This project takes Jira ticket metadata JSON, injects it into a selected system prompt, sends it to an LLM, and returns the model output.

## Structure

- `Prompt/` stores stable system prompt templates. Jira metadata is sent separately as a user message.
- `app/` contains reusable application code.
- `main.py` runs local analysis from a JSON file.
- `api.py` serves the analyzer through FastAPI.
- `jiraData.py` remains the Jira export script.
- `test_jiraAPI.py` remains the Jira API POC script.

## Environment

Create `.env` and set:

```text
OPENAI_API_KEY=your_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

For local dry runs without calling an external LLM:

```text
LLM_PROVIDER=mock
```

## Local Run

```bash
python main.py --ticket-json jira_ticket_exports/YOUR_FILE.json --prompt default_system_prompt
```

## API Run

```bash
uvicorn api:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Graph DB admin UI:

```text
http://127.0.0.1:8000/graph-admin
```

RepoTree is bundled into this project as `repo_architect/` plus
`repo_tree/config` and `repo_tree/workspace`. Its APIs are exposed by the same
JIRA-AI process, so you do not need a separate RepoTree checkout or second
uvicorn port for scans, Repomix reindexing, or test-case generation.

## Docker Run

Build and run the API:

```bash
docker compose up -d --build
```

If your server does not have the Compose plugin installed, install it first:

```bash
sudo apt install docker-compose-v2
```

Open:

```text
http://SERVER_IP:8000/graph-admin
```

The compose file mounts the server's existing cloned repositories from `/home/ubuntu` into the app container at `/host-repos`. The mount is writable so local graph jobs can run `git fetch`/`git pull` before ingestion. The n8n payload still sends host paths such as `/home/ubuntu/ramfincorp-backend`, so n8n can also run pull commands on the server paths.

For Docker, set these values in `.env`:

```text
DATABASE_URL=postgresql://USER:PASSWORD@host.docker.internal:5432/jira_ai
REPOSITORY_SEARCH_ROOT=/host-repos
REPOSITORY_HOST_ROOT=/home/ubuntu
EXCLUDED_REPOSITORY_NAMES=JIRA-AI
REPO_TREE_SRC_PATH=/app
REPO_TREE_CONFIG_PATH=/app/repo_tree/config/repos.yaml
REPO_TREE_WORKSPACE_DIR=/app/repo_tree/workspace
```

If n8n runs directly on the host, use `host.docker.internal` in the webhook URL from inside Docker:

```text
N8N_GRAPH_WEBHOOK_URL=http://host.docker.internal:5678/webhook/graph-db-admin
```

If you want Compose to run a local Postgres container too, set:

```text
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/jira_ai
```

Then start with:

```bash
docker compose --profile local-db up -d --build
```

Useful commands:

```bash
docker compose logs -f jira-ai-api
docker compose restart jira-ai-api
docker compose down
```

## Endpoints

- `GET /health`
- `GET /prompts`
- `GET /graph-admin`
- `GET /graph-admin/repositories`
- `POST /graph-admin/trigger`
- `POST /graph-admin/jobs`
- `GET /graph-admin/jobs`
- `GET /graph-admin/jobs/{job_id}`
- `WS /graph-admin/jobs/{job_id}/ws`
- `POST /chat`
- `POST /analyze-ticket`
- `POST /analyze-ticket/test-cases`
- `POST /workflow/jira-review`
- `POST /workflow/slack-reply`
- `POST /workflow/slack-events`
- `POST /workflow1`
- `POST /workflow2`
- `POST /workflow2/reply`
- `POST /workflow3`
- `POST /workflow4`
- `POST /scan/initial` (RepoTree, in-process)
- `POST /scan/nightly` (RepoTree, in-process)
- `POST /repomix/reindex` (RepoTree, in-process)
- `POST /testcases/generate` (RepoTree, in-process)
- `GET /jobs` (RepoTree, in-process)
- `GET /jobs/{job_id}` (RepoTree, in-process)
- `GET /repo-tree/health`

Example request:

```json
{
  "prompt_name": "readiness_review",
  "ticket_data": {
    "key": "ABC-123",
    "title": "Example Jira ticket",
    "description": "Ticket details here"
  }
}
```

## Graph DB Admin UI

The admin page triggers n8n graph jobs for every top-level Git repository already cloned under `REPOSITORY_SEARCH_ROOT`, excluding `JIRA-AI` by default. Each trigger sends n8n the local clone path, remote URL, current branch, current commit, Jira flags, and instructions to run `git pull --ff-only` before rebuilding graph context.

The API also supports local graph jobs at `/graph-admin/jobs`. These run inside the API process, stream progress over the job WebSocket, persist repository metadata, run optional `git pull`, and optionally fetch Jira ticket history into Neo4j.
Graph job state is persisted to Postgres when `DATABASE_URL` is configured, so refreshing `/graph-admin` restores the latest job status, logs, repository progress, and Jira ticket snapshot instead of resetting to an empty in-memory view.

The repositories tab also supports downloadable code analysis reports. Select one or more repositories and click **Download Code Analysis** to generate a Markdown document from local clone inspection plus Neo4j graph context when available. The backing endpoint is `POST /graph-admin/code-analysis-report`.

The Ticket Insights tab can download a Jira test-case quantity, quality, and clarity Excel workbook. The sheet excludes `AIGOV` by default, compares already-present ticket test cases against actual `/testcases/generate` output for a bounded sample of filtered tickets, includes the auto-detected `grounded_repos` from RepoTree/Anthropic using Repomix directory previews, and uses Anthropic Opus (`TEST_CASE_COMPARISON_MODEL`) to write a narrative tab. Add `format=md` to the endpoint if you need the older Markdown report.

Environment:

```text
N8N_GRAPH_WEBHOOK_URL=https://your-n8n-host/webhook/graph-db-admin
N8N_API_KEY=optional-shared-secret
JIRA_PROJECT_KEYS=ABC,DEF
JIRA_EXCLUDED_PROJECT_KEYS=AIGOV
TEST_CASE_COMPARISON_MODEL=claude-opus-4-5
TEST_CASE_COMPARISON_MAX_TOKENS=6000
TEST_CASE_COMPARISON_PIPELINE_LIMIT=5
TEST_CASE_COMPARISON_PIPELINE_TOP_K=15
REPOSITORY_SEARCH_ROOT=/home/ubuntu
REPOSITORY_HOST_ROOT=/home/ubuntu
EXCLUDED_REPOSITORY_NAMES=JIRA-AI
NEO4J_URI=bolt://host.docker.internal:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j
GRAPH_JOB_REPO_TIMEOUT_SECONDS=900
GRAPH_JOB_COMMIT_BATCH_SIZE=500
GRAPH_JOB_LIMIT_JIRA_ISSUES=0
GRAPH_JOB_BUILD_EMBEDDINGS=true
SIMILAR_TICKET_MATCH_THRESHOLD=0.68
REPO_TREE_SRC_PATH=/home/ubuntu/JIRA-AI
REPO_TREE_CONFIG_PATH=/home/ubuntu/JIRA-AI/repo_tree/config/repos.yaml
REPO_TREE_WORKSPACE_DIR=/home/ubuntu/JIRA-AI/repo_tree/workspace
```

`JIRA_PROJECT_KEYS` is optional when the Jira API user can discover projects
with Browse Projects permission. Set it to a comma-separated list such as
`QTM` when you want to ingest selected projects or when global project
discovery returns no projects. The `JIRA_EMAIL`/`JIRA_API_TOKEN` pair must
authenticate as a Jira user that can browse those projects.

Actions sent to n8n:

```text
update
regenerate
create_new
jira_tickets_only
```

If `N8N_GRAPH_WEBHOOK_URL` is not configured, the UI returns a dry-run payload so you can verify the repository list before wiring n8n.

n8n should treat the repository paths as existing local clones. It should not clone them again.

When embeddings are enabled, graph jobs create Jira ticket embeddings in
Qdrant through the configured Ollama embedding model. Repository graph creation
and Neo4j `EmbeddingDocument` rebuilds no longer use Repograph, because that
path only covered Python repositories.

Test-case generation now calls the bundled RepoTree code in-process. RepoTree
uses the existing Qdrant codebase collections plus its Repomix maps, so this
flow no longer depends on Neo4j graph traversal. Set `REPO_TREE_BASE_URL` only
if you intentionally want to fall back to a remote RepoTree service.

## Jira Review + Slack Follow-up Workflow

The workflow endpoints implement the loop in `Workflow.png`:

1. Jira webhook/n8n calls `POST /workflow/jira-review` with ticket metadata.
2. The API reviews the ticket with the configured LLM prompt.
3. If the ticket is good, the API comments on Jira and optionally transitions it with `JIRA_APPROVED_TRANSITION_NAME`.
4. If the ticket needs updates, the API posts a Slack thread starter and stores the thread/ticket context in Postgres.
5. Slack thread replies call `POST /workflow/slack-reply`.
6. The API loads the stored ticket context, previous review, chat history, and optional codebase context, then replies in the same Slack thread.

Required environment for the workflow:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jira_ai
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_DEFAULT_CHANNEL_ID=C1234567890
JIRA_APPROVED_TRANSITION_NAME=LLM APPROVED
```

`SLACK_BOT_TOKEN` and Jira credentials can be omitted for dry runs. Postgres is required because Slack thread state is the source of truth for follow-up replies.

Initial review request:

```json
{
  "slack_channel_id": "C1234567890",
  "ticket_data": {
    "key": "ABC-123",
    "summary": "[CRM] | Fix lead search",
    "description": ""
  }
}
```

Slack reply request, if your automation sends a normalized payload:

```json
{
  "user": "U123",
  "channel": "C1234567890",
  "thread_ts": "1715000000.000100",
  "text": "I added the reproduction steps, validation plan, and rollback details.",
  "event_ts": "1715000100.000200"
}
```

Slack Events API can also point directly at `POST /workflow/slack-events`. The endpoint handles Slack URL verification, ignores bot messages, and processes only messages that include `thread_ts`.

## Jira AI Workflows 1-4

The merged workflow endpoints are available alongside the existing analyzer,
graph admin, and Slack follow-up APIs:

- `POST /workflow1` reviews a Jira payload with `Prompt/workflow1_prompt.txt`.
- `POST /workflow2/reply` handles workflow-specific Slack thread replies with `Prompt/workflow2_prompt.txt`.
- `POST /workflow3` checks SLA usage and returns Slack alert payloads.
- `POST /workflow4` checks due-date compliance and returns Slack alert payloads.

`POST /workflow2` is kept for the existing AI Governor test-case Slack reply
flow, so existing n8n integrations using that endpoint continue to work.

## AI Governor Test-case Slack Replies

The n8n closing flow can post Slack thread replies to `POST /workflow2`:

```json
{
  "user_id": "U123",
  "slack_channel_id": "C1234567890",
  "slack_thread_ts": "1715000000.000100",
  "user_message": "Can you add an edge case for duplicate webhooks?"
}
```

The API resolves the Slack thread to its Jira ticket from `tickets.slack_channel_id`
and `tickets.slack_thread_ts`. It also falls back to older `channelid_table` rows
and the existing `jira_slack_conversations` table. It loads the live Jira ticket,
recent thread messages, and `test_cases`, asks Claude whether the reply is a
ticket question, test-case question, or test-case edit, and for edits updates
both the Jira test-case comment and the Postgres rows.

Required environment:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jira_ai
ANTHROPIC_API_KEY=your_key
LLM_PROVIDER=anthropic
TESTCASE_CHAT_MODEL=claude-sonnet-4-5
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your-token
```

Response:

```json
{
  "slack_channel_id": "C1234567890",
  "slack_thread_ts": "1715000000.000100",
  "reply": "Updated the test cases..."
}
```

## Simple Slack Chat

The old standalone `api2.py` chat endpoint now lives in the main app:

```json
{
  "userid": "U123",
  "channelId": "C1234567890",
  "threadid": "1715000000.000100",
  "user message": "Can you help me update this ticket?"
}
```

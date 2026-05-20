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
- `POST /workflow/jira-review`
- `POST /workflow/slack-reply`
- `POST /workflow/slack-events`

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

Environment:

```text
N8N_GRAPH_WEBHOOK_URL=https://your-n8n-host/webhook/graph-db-admin
N8N_API_KEY=optional-shared-secret
JIRA_PROJECT_KEYS=ABC,DEF
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
```

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

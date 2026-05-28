# Jira AI Workflows

FastAPI service for the active Jira workflow endpoints only:

- `POST /workflow1`
- `POST /workflow2`
- `POST /workflow3`
- `POST /workflow4`

## Project Structure

- `api.py` wires the four workflow endpoints.
- `app/workflow1_reviewer.py` handles Jira review and initial DB persistence.
- `app/workflow2_replier.py` handles Slack thread follow-up replies.
- `app/workflow3_sla.py` checks SLA usage and prepares alerts.
- `app/workflow4_due_date.py` checks due-date compliance and prepares alerts.
- `Prompt/workflow1_prompt.txt` and `Prompt/workflow2_prompt.txt` are the active prompt templates.

## Environment

Required as applicable for the workflows:

```text
ANTHROPIC_API_KEY=your_key
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DB_NAME
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email
JIRA_API_TOKEN=your-token
```

`DATABASE_URL` can also be built from:

```text
DB_HOST=
DB_PORT=5432
DB_NAME=
DB_USER=
DB_PASSWORD=
```

## Run

```bash
uvicorn api:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Docker

```bash
docker compose up -d --build
```

For the optional local Postgres container:

```bash
docker compose --profile local-db up -d --build
```

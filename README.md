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

Create `.env` from `.env.example` and set:

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

## Endpoints

- `GET /health`
- `GET /prompts`
- `POST /analyze-ticket`

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

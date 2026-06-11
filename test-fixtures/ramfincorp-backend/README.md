# RamFincorp Backend JIRA-AI Fixture

This folder contains a dummy Jira ticket and PRD for testing JIRA-AI against the local `ramfincorp-backend` repository.

Files:

- `ticket-ram-be-9001-bureau-decision-audit.json` - raw Jira-style ticket data.
- `manual-jira-ticket-ram-be-9001.md` - copy-paste fields for creating the ticket manually in Jira.
- `prd-ram-be-9001-bureau-decision-audit.md` - PRD referenced by the ticket.

## Manual Jira Creation

Open `manual-jira-ticket-ram-be-9001.md` and copy the field values into Jira. The description block is written as plain Markdown/Jira-friendly text and can be pasted directly into the Jira description editor.

## Suggested JIRA-AI Calls

Set the path once:

```bash
TICKET_JSON=/home/ubuntu/JIRA-AI/test-fixtures/ramfincorp-backend/ticket-ram-be-9001-bureau-decision-audit.json
```

Review workflow:

```bash
curl -s http://127.0.0.1:8000/workflow1 \
  -H "Content-Type: application/json" \
  --data-binary @"$TICKET_JSON"
```

Ticket analyzer:

```bash
jq '{ticket_data: .}' "$TICKET_JSON" > /tmp/ram-be-9001-analyze.json

curl -s http://127.0.0.1:8000/analyze-ticket \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/ram-be-9001-analyze.json
```

Note: this checkout currently has `DEFAULT_PROMPT=ticket_prompt` in `.env`, but `Prompt/ticket_prompt.txt` is not present. Add that prompt or set `DEFAULT_PROMPT` to an existing prompt before testing `/analyze-ticket`.

Test-case generation:

```bash
jq '{ticket_data: ., repo: "ramfincorp-backend", style: "plain", top_k: 15}' "$TICKET_JSON" > /tmp/ram-be-9001-testcases.json

curl -s http://127.0.0.1:8000/analyze-ticket/test-cases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JIRA_AI_TOKEN" \
  --data-binary @/tmp/ram-be-9001-testcases.json
```

Similar-ticket search:

```bash
jq '{summary: .summary, description: .description, project_key: .project.key}' "$TICKET_JSON" > /tmp/ram-be-9001-similar.json

curl -s http://127.0.0.1:8000/analyze-ticket/similar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JIRA_AI_TOKEN" \
  --data-binary @/tmp/ram-be-9001-similar.json
```

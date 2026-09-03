# AI Governor — Technical Implementation Guide

> Complete technical reference for the JIRA-AI (AI Governor) platform built for Ram Fincorp.
> Covers architecture, codebase structure, database schemas, API endpoints, n8n workflows, and deployment.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Codebase Structure](#2-codebase-structure)
3. [API Endpoints Reference](#3-api-endpoints-reference)
4. [n8n Workflows](#4-n8n-workflows)
5. [Database Schema](#5-database-schema)
6. [LLM Prompts](#6-llm-prompts)
7. [Frontend (React Dashboard)](#7-frontend-react-dashboard)
8. [External Integrations](#8-external-integrations)
9. [Deployment & Infrastructure](#9-deployment--infrastructure)
10. [Environment Variables](#10-environment-variables)

---

## 1. Architecture Overview

```
┌──────────────┐    Webhook     ┌──────────────┐   HTTP POST    ┌──────────────────┐
│    Jira       │──────────────▶│    n8n        │──────────────▶│  FastAPI (api.py) │
│  (Cloud)      │               │  (Orchestr.)  │◀──────────────│  Port 8000        │
└──────────────┘               └──────────────┘   JSON resp.   └────────┬─────────┘
                                      │                                  │
                                      ▼                                  ▼
                               ┌──────────────┐               ┌──────────────────┐
                               │    Slack      │               │   Claude / LLM    │
                               │  (Bot DMs)    │               │   (Anthropic API) │
                               └──────────────┘               └──────────────────┘
                                                                        │
                                      ┌─────────────────────────────────┤
                                      ▼                                 ▼
                               ┌──────────────┐               ┌──────────────────┐
                               │  PostgreSQL   │               │  Qdrant (Vector)  │
                               │  (Main DB)    │               │  + Ollama (Embed) │
                               └──────────────┘               └──────────────────┘
```

**Key principle:** n8n handles orchestration (triggers, fan-out, Slack posting). FastAPI handles all intelligence (LLM calls, retrieval, DB operations). No AI logic lives in n8n.

**Tech stack:**
- **Backend:** Python 3.12, FastAPI, uvicorn
- **LLM:** Anthropic Claude (Opus, Sonnet), OpenAI (fallback)
- **Orchestration:** n8n (self-hosted, Docker)
- **Database:** PostgreSQL 16
- **Vector Search:** Qdrant + Ollama (bge-m3) + FlagEmbedding
- **Graph DB:** Neo4j (code knowledge graph)
- **Frontend:** React 18, Vite 5, react-router-dom 6
- **Deployment:** Docker on AWS EC2, behind Caddy reverse proxy
- **External APIs:** Jira Cloud, Slack Bot, GitHub, Google Docs, Zoho Desk

---

## 2. Codebase Structure

```
JIRA-AI/
├── api.py                          # Main FastAPI app (~2400 lines, ~95 endpoints)
├── main.py                         # Local CLI runner
├── requirements.txt                # Python dependencies (30 packages)
├── Dockerfile                      # Python 3.12-slim + Node 22 + repomix
├── docker-compose.yml              # jira-ai-api service + optional postgres
├── .env                            # Environment variables (not in git)
├── .gitignore
├── .dockerignore
│
├── app/                            # Core application code
│   ├── __init__.py
│   ├── config.py                   # Settings dataclass (120+ env vars)
│   ├── schemas.py                  # Pydantic request/response models
│   ├── auth.py                     # JWT auth, RBAC, user CRUD
│   ├── exceptions.py               # Custom exceptions
│   ├── json_utils.py               # JSON helpers
│   │
│   ├── # ── LLM & Prompts ──
│   ├── llm_client.py               # LLM provider abstraction (Anthropic/OpenAI)
│   ├── prompt_store.py             # Prompt template loader (from Prompt/ dir)
│   ├── ticket_analyzer.py          # Core ticket analysis engine
│   │
│   ├── # ── Workflow Handlers ──
│   ├── workflow1_reviewer.py       # WF1: Ticket validation (Claude Opus)
│   ├── workflow2_replier.py        # WF2: Slack thread reply handler
│   ├── testcase_chat_workflow.py   # WF2/5/5b: Test case Q&A + edit (Claude Sonnet)
│   ├── workflow3_sla.py            # WF3: SLA monitoring & alerts
│   ├── workflow4_aigov.py          # WF4: Due-date compliance tracking
│   ├── workflow4_due_date.py       # WF4: Due-date helper functions
│   ├── workflow_governor_notify.py # Governor notification sender
│   │
│   ├── # ── Test Cases ──
│   ├── test_case_generator.py      # Test case generation from tickets
│   ├── testcase_document.py        # Test case document export (DOCX)
│   ├── testcase_embeddings.py      # Test case vector embeddings
│   ├── testcase_regression_finder.py # Regression detection via vectors
│   ├── test_case_comparison_report.py # TC comparison reports
│   ├── dev_pr_gate.py              # Dev PR gate for test cases
│   │
│   ├── # ── Ticket Intelligence ──
│   ├── similar_ticket_finder.py    # 3-tier similarity search (BGE-M3 → Ollama → keyword)
│   ├── jira_ticket_insights.py     # Ticket analysis insights
│   ├── story_subtasks.py           # Story-to-subtask breakdown
│   │
│   ├── # ── Jira Integration ──
│   ├── jira_client.py              # Jira REST API client
│   ├── jira_fetcher.py             # Jira ticket fetching & caching
│   ├── jira_graph.py               # Jira graph integration
│   │
│   ├── # ── Slack Integration ──
│   ├── slack_client.py             # Slack Bot API client
│   ├── slack_review_workflow.py    # Slack review flow
│   ├── channel_health.py           # Slack channel health checks
│   ├── conversation_store.py       # Postgres conversation storage
│   │
│   ├── # ── Code Graph (Neo4j) ──
│   ├── graph_context.py            # Graph context client
│   ├── graph_job.py                # Graph job state
│   ├── graph_job_runner.py         # Graph job execution
│   ├── neo4j_job_runner.py         # Neo4j build runner
│   ├── codebase_graph.py           # Codebase graph logic
│   ├── neo4j_graph/
│   │   ├── __init__.py
│   │   ├── analytics.py            # Graph analytics queries
│   │   ├── builder.py              # Graph build orchestrator
│   │   ├── code_layer.py           # Code node/relationship creation
│   │   ├── config.py               # Neo4j config
│   │   ├── git_layer.py            # Git commit/file relationships
│   │   ├── snapshots.py            # Graph build snapshots
│   │   ├── ticket_context.py       # Ticket context from graph
│   │   └── writer.py               # Neo4j write operations
│   │
│   ├── # ── RCA (Root Cause Analysis) ──
│   ├── rca/
│   │   ├── __init__.py
│   │   ├── agent.py                # Agentic investigation loop
│   │   ├── code_chunker.py         # Source code chunking
│   │   ├── code_index.py           # Code index state management
│   │   ├── eval.py                 # RCA evaluation
│   │   ├── fix_links.py            # Fix link tracking
│   │   ├── intake.py               # Bug ticket intake
│   │   ├── localize.py             # Repo localization
│   │   ├── rca_document.py         # RCA document builder
│   │   ├── repos.py                # Repo access for RCA
│   │   ├── retrieval.py            # Code retrieval
│   │   ├── runner.py               # RCA pipeline runner
│   │   ├── store.py                # RCA run persistence
│   │   ├── synthesis.py            # Diagnosis synthesis
│   │   └── tools.py                # Agentic tool definitions
│   │
│   ├── # ── Vector & Embeddings ──
│   ├── qdrant_store.py             # Qdrant vector store client
│   ├── ollama_embedder.py          # Ollama embedding client
│   ├── flag_embedder.py            # FlagEmbedding (bge-m3)
│   ├── embedding_status.py         # Embedding status tracking
│   │
│   ├── # ── Document Generation ──
│   ├── doc_review.py               # Google Docs PRD/TechDoc review (WF6)
│   ├── repo_doc_generator.py       # Repository documentation generation
│   ├── repo_doc_jobs.py            # Doc generation job management
│   ├── repo_doc_usage.py           # Doc gen usage/cost tracking
│   ├── markdown_docx.py            # Markdown to DOCX converter
│   ├── code_analysis_report.py     # Code analysis reports
│   │
│   ├── # ── Estimates & Utilization ──
│   ├── rft_calibration.py          # RFT estimate calibration
│   ├── rft_estimate_analysis.py    # RFT estimate LLM prediction
│   ├── rft_estimates.py            # RFT estimate report (WF7)
│   ├── utilization.py              # Ticket status history/utilization
│   │
│   ├── # ── Other Integrations ──
│   ├── github_client.py            # GitHub API client
│   ├── n8n_monitor.py              # n8n workflow monitoring
│   ├── repository_discovery.py     # Git repo discovery
│   ├── repo_tree_integration.py    # RepoTree integration
│   ├── email_sender.py             # SMTP email sender
│   ├── app_settings.py             # Runtime app settings (DB-backed)
│   ├── ring_studio.py              # Ring Studio (image generation)
│   └── zoho_client.py              # Zoho Desk API client
│
├── repo_architect/                 # RepoTree/Repomix code analysis subsystem
│   ├── __init__.py
│   ├── config.py
│   ├── combiner.py
│   ├── differ.py
│   ├── embeddings.py
│   ├── llm.py
│   ├── packer.py
│   ├── patcher.py
│   ├── prompts.py
│   ├── reindex.py
│   ├── scanner.py
│   ├── sections.py
│   ├── state.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                  # RepoTree API endpoints
│   │   ├── jobs.py
│   │   └── models.py
│   └── testcases/
│       ├── __init__.py
│       ├── detect.py
│       └── generate.py
│
├── frontend/                       # React Admin SPA (Vite + React 18)
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx                # Entry point
│       ├── App.jsx                 # Router
│       ├── auth.jsx                # Auth context
│       ├── api.js                  # API client
│       ├── styles.css
│       ├── components/
│       │   ├── Header.jsx
│       │   ├── ProtectedRoute.jsx
│       │   ├── EmbeddingsStatus.jsx
│       │   ├── JobProgress.jsx
│       │   └── JobSidebar.jsx
│       ├── lib/
│       │   ├── format.js
│       │   ├── graphJob.js
│       │   ├── markdown.js
│       │   └── tabs.js
│       ├── pages/
│       │   ├── AdminDashboard.jsx
│       │   ├── Documentation.jsx
│       │   ├── Home.jsx
│       │   ├── Login.jsx
│       │   └── Users.jsx
│       └── tabs/
│           ├── ChannelHealth.jsx
│           ├── Insights.jsx
│           ├── JiraTickets.jsx
│           ├── Logs.jsx
│           ├── Neo4jGraph.jsx
│           ├── RCA.jsx
│           ├── Repositories.jsx
│           ├── RingStudio.jsx
│           ├── SimilarTickets.jsx
│           ├── TestCases.jsx
│           ├── Utilization.jsx
│           ├── Workflows.jsx
│           └── ZohoTickets.jsx
│
├── Prompt/                         # LLM prompt templates
│   ├── workflow1_prompt.txt        # Ticket review prompt
│   └── workflow2_prompt.txt        # Follow-up conversation prompt
│
├── N8N flows/                      # n8n workflow JSON exports
│   ├── WorkFlow 1 - Ticket Validation (1).json
│   ├── WorkFlow 2 - Test Case Q&A + Edit (1).json
│   ├── WorkFlow 3 - SLA Monitor (1).json
│   ├── WorkFlow 4 - Due Date Compliance Tracking (v2, 15m timeout).json
│   ├── AI Governor - Closing Flow (WorkFlow 5) v3 (phase-aware).json
│   ├── AI Governor - Dev Test Cases (Code Review) WF5b.json
│   ├── WorkFlow 6 - PRD_TechDoc Review.json
│   ├── WorkFlow 7 - RFT Estimate Report (1).json
│   └── WorkFlow 8 - Status Transition Logger (1).json
│
├── scripts/                        # Utility scripts
│   ├── build_frontend.sh
│   ├── build_testcase_embeddings.py
│   ├── create_admin.py
│   ├── google_oauth_setup.py
│   ├── zoho_oauth_setup.py
│   └── sql/
│       └── 2026-07-27_test_cases_phase.sql
│
├── scripts_tc_compare/             # Test-case comparison pipeline
│   ├── 01_gather.py
│   ├── 02_judge.py
│   └── 03_build_xlsx.py
│
├── tests/                          # Unit tests (RCA subsystem)
│   ├── __init__.py
│   ├── rca_helpers.py
│   ├── test_rca_code_chunker.py
│   ├── test_rca_code_index.py
│   ├── test_rca_document.py
│   ├── test_rca_engine.py
│   ├── test_rca_fix_links.py
│   ├── test_rca_intake.py
│   └── test_rca_repos.py
│
├── repo_tree/                      # RepoTree workspace
│   ├── config/repos.yaml
│   └── workspace/                  # Generated docs, packed XML, state
│
├── docs/
│   └── google_oauth_setup.md
│
└── ring_images/                    # Generated Ring Studio images
```

---

## 3. API Endpoints Reference

All endpoints are defined in `api.py` unless otherwise noted. Auth endpoints are in `app/auth.py`. RepoTree endpoints are in `repo_architect/api/app.py`.

### Workflow Endpoints

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | `/workflow1` | `workflow1_review()` | Ticket validation — LLM reviews ticket quality |
| POST | `/workflow2` | `workflow2_reply()` | Slack thread reply — test case Q&A + edit |
| POST | `/workflow3/sla-check` | `workflow3_sla_check()` | SLA monitoring check |
| POST | `/workflow4/due-date-check` | `workflow4_due_date()` | Due-date compliance check |
| POST | `/workflow4/aigov` | `workflow4_aigov()` | AI Governor due-date orchestration |
| POST | `/workflow5/closing` | `workflow5_closing()` | Ticket closing flow (test case generation) |
| POST | `/workflow6/doc-review` | `workflow6_doc_review()` | PRD/TechDoc review |
| POST | `/workflow7/rft-estimate` | `workflow7_rft_estimate()` | RFT estimate report |
| POST | `/workflow8/status-transition` | `workflow8_status_transition()` | Status transition logging |

### Ticket Analysis

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze-ticket` | Analyze a single Jira ticket |
| POST | `/analyze-ticket/similar` | Find similar tickets (vector search) |
| POST | `/analyze-ticket/regression` | Find regression test cases |
| GET | `/ticket-insights/{ticket_key}` | Get ticket insights |
| POST | `/story-subtasks` | Break story into subtasks |

### Test Cases

| Method | Path | Description |
|--------|------|-------------|
| GET | `/test-cases/{ticket_key}` | Get test cases for a ticket |
| POST | `/test-cases/generate` | Generate test cases |
| POST | `/test-cases/compare` | Compare test case sets |
| GET | `/test-cases/document/{ticket_key}` | Export test cases as DOCX |
| POST | `/test-cases/embeddings/build` | Build test case embeddings |
| GET | `/test-cases/embeddings/status` | Get embedding build status |

### Jira

| Method | Path | Description |
|--------|------|-------------|
| GET | `/jira/projects` | List Jira projects |
| GET | `/jira/tickets` | Search/list tickets |
| GET | `/jira/ticket/{key}` | Get single ticket |
| POST | `/jira/fetch` | Trigger ticket fetch/cache |
| GET | `/jira/fetch/status` | Get fetch status |

### Slack

| Method | Path | Description |
|--------|------|-------------|
| POST | `/slack/channel-health` | Check channel health |
| GET | `/slack/channel-health/status` | Get health status |

### RCA (Root Cause Analysis)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/rca/run` | Start RCA investigation |
| GET | `/rca/runs` | List RCA runs |
| GET | `/rca/run/{run_id}` | Get RCA run details |
| POST | `/rca/code-index/build` | Build code index for repos |
| GET | `/rca/code-index/status` | Get index build status |
| GET | `/rca/fix-links/{ticket_key}` | Get fix links for ticket |

### Graph & Repositories

| Method | Path | Description |
|--------|------|-------------|
| GET | `/repositories` | List discovered repos |
| POST | `/graph/build` | Start graph build job |
| GET | `/graph/jobs` | List graph jobs |
| GET | `/graph/job/{job_id}` | Get job status |
| GET | `/graph/analytics` | Get graph analytics |
| GET | `/graph/snapshots` | Get graph snapshots |

### Documentation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/docs/generate` | Generate repo documentation |
| GET | `/docs/jobs` | List doc gen jobs |
| GET | `/docs/usage` | Get doc gen usage/cost |
| POST | `/doc-review` | Review Google Doc (WF6) |
| GET | `/doc-reviews` | List doc reviews |

### Auth & Users (in `app/auth.py`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | JWT login |
| POST | `/auth/register` | Create user (admin only) |
| GET | `/auth/me` | Get current user |
| GET | `/auth/users` | List users |
| PUT | `/auth/users/{id}` | Update user |
| DELETE | `/auth/users/{id}` | Delete user |

### n8n Monitoring

| Method | Path | Description |
|--------|------|-------------|
| GET | `/n8n/workflows` | List n8n workflows |
| GET | `/n8n/executions` | List recent executions |

### Utilization & Estimates

| Method | Path | Description |
|--------|------|-------------|
| GET | `/utilization` | Get ticket utilization stats |
| GET | `/utilization/status-history` | Get status transition history |
| POST | `/rft-estimate/analyze` | Run RFT estimate analysis |
| GET | `/rft-estimate/predictions` | Get estimate predictions |

### Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/settings` | Get app settings |
| PUT | `/settings` | Update settings |
| GET | `/prompts` | List available prompts |

### Other

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ring-studio/generate` | Generate ring images |
| GET | `/ring-studio/gallery` | List generated images |
| GET | `/zoho/tickets` | List Zoho Desk tickets |
| POST | `/governor/notify` | Send governor notification |
| POST | `/email/send` | Send email via SMTP |

---

## 4. n8n Workflows

### WF1 — Ticket Validation (LIVE, not fully active)

**Trigger:** Jira webhook on ticket create/update
**Flow:**
```
Jira Webhook → Extract Jira Fields → POST /workflow1 → Extract API Response
    → Is Satisfied?
        TRUE  → Similar Ticket Search → If similar found?
                    TRUE  → Send similar ticket alert to Slack
                    FALSE → Jira Transition to "JIRA GOV APPROVED" (id: 3)
                            → Set Priority on Jira
                            → Assign User on Jira
                            → Insert sla_tracking record
        FALSE → Postgres SELECT (check existing thread)
                → Has thread?
                    TRUE  → Reply in existing Slack thread
                    FALSE → Send new Slack DM to reporter
                → Extract thread_ts → Update tickets table with thread info
```
**API endpoint:** `POST /workflow1`
**LLM model:** Claude Opus
**Known issues:**
- Hardcoded Jira credentials in JavaScript Code nodes
- Hardcoded default assignee accountId
- "JIRA GOV APPROVED" state must exist in Jira workflow
- `channelid_table` must have all team members for Slack DMs to work

### WF2 — Test Case Q&A + Edit (LIVE)

**Trigger:** Slack message in thread (via Slack trigger)
**Flow:** Slack trigger → Filter bot messages → POST /workflow2 → Reply in Slack thread
**API endpoint:** `POST /workflow2`
**LLM model:** Claude Sonnet
**Purpose:** Handles follow-up conversations in Slack threads for both ticket review feedback and test case Q&A.

### WF3 — SLA Monitor (NOT LIVE)

**Trigger:** Scheduled (cron)
**Flow:** Calls `/workflow3/sla-check` → Checks SLA deadlines → Sends escalation alerts (75%/50%/25%/0%) to eng lead, CTO, CEO via Slack
**API endpoint:** `POST /workflow3/sla-check`

### WF4 — Due Date Compliance Tracking (LIVE, 15m timeout variant)

**Trigger:** Scheduled every 15 minutes
**Flow:** Calls `/workflow4/aigov` → Scans active tickets → Checks due dates → Sends compliance digests to Jira owner and team leads
**API endpoint:** `POST /workflow4/aigov`

### WF5 — Closing Flow (LIVE, phase-aware)

**Trigger:** Jira ticket transitions to QA status
**Flow:** Detects ticket closure → Generates QA test cases → Posts to Slack thread → Stores in DB
**API endpoint:** `POST /workflow5/closing`
**LLM model:** Claude Sonnet

### WF5b — Dev Test Cases / Code Review (LIVE, with PR Gate)

**Trigger:** Jira ticket transitions to code review
**Flow:** Similar to WF5 but generates developer-focused test cases with PR gate integration
**API endpoint:** `POST /workflow5/closing` (same endpoint, different phase)

### WF6 — PRD/TechDoc Review (LIVE)

**Trigger:** Manual or webhook
**Flow:** Reads Google Doc → LLM reviews against PRD/TechDoc quality criteria → Returns review
**API endpoint:** `POST /workflow6/doc-review`

### WF7 — RFT Estimate Report (NOT LIVE)

**Trigger:** Scheduled
**Flow:** Fetches sprint tickets → LLM estimates effort → Compares with actual → Generates report
**API endpoint:** `POST /workflow7/rft-estimate`

### WF8 — Status Transition Logger (NOT LIVE)

**Trigger:** Jira webhook on status change
**Flow:** Logs every ticket status transition to `ticket_status_history` table
**API endpoint:** `POST /workflow8/status-transition`

---

## 5. Database Schema

PostgreSQL 16. No migration framework (Alembic). Tables are created inline in Python code using `CREATE TABLE IF NOT EXISTS`. Schema evolution uses `ALTER TABLE ADD COLUMN IF NOT EXISTS` (self-healing).

### Core Tables (created by n8n or first workflow execution)

#### `tickets`

The central ticket tracking table. Created externally (likely by initial n8n setup or manual SQL).

```sql
-- Schema inferred from INSERT/SELECT usage across codebase
CREATE TABLE tickets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jira_ticket_id  TEXT UNIQUE NOT NULL,
    email           TEXT,
    assigned_user_id TEXT,
    slack_channel_id TEXT,
    slack_thread_ts  TEXT,
    llm_review      TEXT,
    status          TEXT DEFAULT 'open',
    jira_payload    JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**Used by:** WF1 (upsert), WF2 (lookup), WF4 (upsert), WF5/5b (lookup), n8n flows (update slack_thread_ts)

#### `messages`

Conversation messages linked to tickets.

```sql
-- Schema inferred from INSERT usage
CREATE TABLE messages (
    id         BIGSERIAL PRIMARY KEY,
    ticket_id  UUID REFERENCES tickets(id),
    sender     TEXT NOT NULL,           -- 'bot' or 'user'
    message    TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Used by:** WF1 (insert bot review), WF2 (insert user + bot messages), n8n flows (insert)

#### `test_cases`

Generated test cases per ticket, with phase support (QA vs dev).

```sql
-- Schema inferred from INSERT/SELECT + migration script
CREATE TABLE test_cases (
    id              BIGSERIAL PRIMARY KEY,
    jira_ticket_id  TEXT NOT NULL,
    tc_index        INTEGER NOT NULL,
    phase           VARCHAR(8) NOT NULL DEFAULT 'qa',  -- 'qa' or 'dev'
    title           TEXT,
    description     TEXT,
    steps           TEXT,
    expected_result TEXT,
    priority        TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (jira_ticket_id, phase, tc_index)
);
```

**Migration:** `scripts/sql/2026-07-27_test_cases_phase.sql` adds the `phase` column and re-indexes the unique constraint.

#### `channelid_table`

Maps Jira display names to Slack channel IDs. Looked up by `slack_user_name`.

```sql
-- Schema inferred from SELECT/INSERT usage
CREATE TABLE channelid_table (
    slack_user_name TEXT PRIMARY KEY,
    email_id        TEXT,
    channel_id      TEXT NOT NULL,
    role            TEXT,               -- 'eng_lead', 'cto', 'ceo', 'team_channel', 'jira_owner'
    jira_account_id TEXT,
    display_name    TEXT
);
```

**Lookup query (WF1):**
```sql
SELECT email_id, slack_user_name, channel_id
FROM channelid_table
WHERE lower(trim(leading '@' from slack_user_name)) = lower(trim(leading '@' from $1))
LIMIT 1
```

**Role-based queries (WF3/WF4):**
```sql
SELECT channel_id FROM channelid_table WHERE role = 'eng_lead' LIMIT 1
SELECT channel_id FROM channelid_table WHERE role = 'cto' LIMIT 1
SELECT channel_id FROM channelid_table WHERE role = 'ceo' LIMIT 1
SELECT channel_id FROM channelid_table WHERE role = 'team_channel' LIMIT 1
SELECT channel_id FROM channelid_table WHERE role = 'jira_owner' LIMIT 1
```

#### `sla_tracking`

SLA deadline tracking per ticket (created by n8n WF1 SATISFIED path).

```sql
-- Schema inferred from n8n INSERT query
CREATE TABLE sla_tracking (
    id                BIGSERIAL PRIMARY KEY,
    ticket_id         UUID REFERENCES tickets(id),
    jira_ticket_id    TEXT UNIQUE NOT NULL,
    priority          TEXT,
    assignee_slack_id TEXT,
    sla_start_time    TIMESTAMPTZ,
    sla_deadline      TIMESTAMPTZ,
    sla_window_hours  INTEGER,
    alert_75_sent     BOOLEAN DEFAULT FALSE,
    alert_50_sent     BOOLEAN DEFAULT FALSE,
    alert_25_sent     BOOLEAN DEFAULT FALSE,
    alert_0_sent      BOOLEAN DEFAULT FALSE,
    is_resolved       BOOLEAN DEFAULT FALSE
);
```

#### `due_date_tracking`

Due-date compliance tracking (created by WF1 API + WF4).

```sql
-- Schema from workflow1_reviewer.py and workflow4_aigov.py
CREATE TABLE due_date_tracking (
    id                  BIGSERIAL PRIMARY KEY,
    ticket_id           UUID REFERENCES tickets(id),
    jira_ticket_id      TEXT UNIQUE NOT NULL,
    priority            TEXT,
    assignee_slack_id   TEXT,
    due_date            DATE,
    tracking_start_date DATE,
    total_working_days  INTEGER,
    alert_75_sent       BOOLEAN DEFAULT FALSE,
    alert_50_sent       BOOLEAN DEFAULT FALSE,
    alert_25_sent       BOOLEAN DEFAULT FALSE,
    alert_0_sent        BOOLEAN DEFAULT FALSE,
    exceeded_alert_sent_at TIMESTAMPTZ,
    is_completed        BOOLEAN DEFAULT FALSE,
    dev_due_date        DATE,
    qa_due_date         DATE,
    live_due_date       DATE
);
```

### Tables Created by Python Code (self-healing)

#### `app_settings` — `app/app_settings.py:31`

```sql
CREATE TABLE IF NOT EXISTS app_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `app_users` — `app/auth.py:177`

```sql
CREATE TABLE IF NOT EXISTS app_users (
    id            SERIAL PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'viewer',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Roles:** admin, developer, qa, viewer, documentation, usermgr

#### `jira_slack_conversations` — `app/conversation_store.py:53`

```sql
CREATE TABLE IF NOT EXISTS jira_slack_conversations (
    id                  BIGSERIAL PRIMARY KEY,
    slack_thread_ts     TEXT NOT NULL UNIQUE,
    slack_channel_id    TEXT NOT NULL,
    jira_issue_key      TEXT NOT NULL,
    original_ticket_data JSONB NOT NULL,
    previous_review     JSONB NOT NULL,
    status              TEXT NOT NULL,
    messages            JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `testcase_threads` — `scripts/sql/2026-07-27_test_cases_phase.sql:60`

```sql
CREATE TABLE IF NOT EXISTS testcase_threads (
    slack_channel_id TEXT NOT NULL,
    slack_thread_ts  TEXT NOT NULL,
    jira_ticket_id   TEXT NOT NULL,
    phase            VARCHAR(8) NOT NULL DEFAULT 'qa',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (slack_channel_id, slack_thread_ts)
);
```

#### `channel_health_status` — `app/channel_health.py:55`

```sql
CREATE TABLE IF NOT EXISTS channel_health_status (
    channel_id      TEXT PRIMARY KEY,
    ok              BOOLEAN NOT NULL,
    error           TEXT,
    message_ts      TEXT,
    last_checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `doc_artifacts` — `app/repo_doc_usage.py:96`

```sql
CREATE TABLE IF NOT EXISTS doc_artifacts (
    id              SERIAL PRIMARY KEY,
    repo            TEXT NOT NULL,
    doc_type        TEXT NOT NULL,
    context_hash    TEXT NOT NULL,
    filename        TEXT NOT NULL,
    markdown        TEXT NOT NULL,
    model           TEXT,
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens     INTEGER NOT NULL DEFAULT 0,
    cache_creation_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd        NUMERIC(12, 6) NOT NULL DEFAULT 0,
    created_by      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repo, doc_type, context_hash)
);
```

#### `doc_generation_usage` — `app/repo_doc_usage.py:117`

```sql
CREATE TABLE IF NOT EXISTS doc_generation_usage (
    id              SERIAL PRIMARY KEY,
    user_email      TEXT,
    repo            TEXT NOT NULL,
    doc_type        TEXT NOT NULL,
    reused          BOOLEAN NOT NULL DEFAULT FALSE,
    model           TEXT,
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens     INTEGER NOT NULL DEFAULT 0,
    cache_creation_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd        NUMERIC(12, 6) NOT NULL DEFAULT 0,
    context_hash    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### `doc_reviews` — `app/doc_review.py:530`

```sql
CREATE TABLE IF NOT EXISTS doc_reviews (
    id           BIGSERIAL PRIMARY KEY,
    doc_id       TEXT NOT NULL,
    doc_title    TEXT,
    doc_type     TEXT NOT NULL DEFAULT 'prd',
    review_text  TEXT NOT NULL,
    model        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    content_hash TEXT,
    review_count INTEGER DEFAULT 1,
    updated_at   TIMESTAMPTZ DEFAULT now()
);
```

#### `neo4j_graph_snapshots` — `app/neo4j_graph/snapshots.py:33`

```sql
CREATE TABLE IF NOT EXISTS neo4j_graph_snapshots (
    id                 BIGSERIAL PRIMARY KEY,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    node_total         BIGINT,
    relationship_total BIGINT,
    repository_count   INT,
    metrics            JSONB NOT NULL
);
```

#### `rca_runs` — `app/rca/store.py:73`

```sql
CREATE TABLE IF NOT EXISTS rca_runs (
    run_id          TEXT PRIMARY KEY,
    jira_key        TEXT NOT NULL,
    status          TEXT NOT NULL,
    localized_repos JSONB NOT NULL DEFAULT '[]'::jsonb,
    candidates      JSONB NOT NULL DEFAULT '[]'::jsonb,
    diagnosis       JSONB,
    confidence      REAL,
    agent_trace     JSONB NOT NULL DEFAULT '[]'::jsonb,
    document        JSONB,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `rca_code_index_state` — `app/rca/code_index.py:90`

```sql
CREATE TABLE IF NOT EXISTS rca_code_index_state (
    repo         TEXT PRIMARY KEY,
    commit_sha   TEXT NOT NULL,
    chunk_count  INTEGER NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `rca_ticket_fix_links` — `app/rca/fix_links.py:57`

```sql
CREATE TABLE IF NOT EXISTS rca_ticket_fix_links (
    id            BIGSERIAL PRIMARY KEY,
    ticket_key    TEXT NOT NULL,
    repo          TEXT NOT NULL,
    commit_sha    TEXT NOT NULL,
    changed_files JSONB NOT NULL DEFAULT '[]'::jsonb,
    source        TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (ticket_key, repo, commit_sha)
);
-- INDEX: idx_rca_fix_links_key ON rca_ticket_fix_links (ticket_key)
```

#### `rca_repo_map` — `app/rca/localize.py:48`

```sql
CREATE TABLE IF NOT EXISTS rca_repo_map (
    id         BIGSERIAL PRIMARY KEY,
    component  TEXT NOT NULL,
    repo       TEXT NOT NULL,
    weight     REAL NOT NULL DEFAULT 1.0,
    source     TEXT NOT NULL DEFAULT 'manual',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (component, repo)
);
-- INDEX: idx_rca_repo_map_component ON rca_repo_map (lower(component))
```

#### `rft_estimate_predictions` — `app/rft_estimate_analysis.py:66`

```sql
CREATE TABLE IF NOT EXISTS rft_estimate_predictions (
    jira_ticket_id   TEXT PRIMARY KEY,
    content_hash     TEXT NOT NULL,
    original_seconds BIGINT,
    predicted_hours  DOUBLE PRECISION,
    confidence       TEXT,
    rationale        TEXT,
    flag             TEXT,
    reason           TEXT,        -- added via ALTER
    explanation      TEXT,        -- added via ALTER
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `ring_studio_generations` — `app/ring_studio.py:998`

```sql
CREATE TABLE IF NOT EXISTS ring_studio_generations (
    id BIGSERIAL PRIMARY KEY,
    style_no TEXT NOT NULL UNIQUE,
    ring_size TEXT,
    metal_weight TEXT,
    gross_weight TEXT,
    estimated BOOLEAN NOT NULL DEFAULT FALSE,
    note TEXT,
    reference JSONB NOT NULL DEFAULT '{}'::jsonb,
    images JSONB NOT NULL DEFAULT '[]'::jsonb,
    cost_usd DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `story_subtasks` — `app/story_subtasks.py:36`

```sql
CREATE TABLE IF NOT EXISTS story_subtasks (
    subtask_key         VARCHAR(50) PRIMARY KEY,
    story_key           VARCHAR(50) NOT NULL,
    project_key         VARCHAR(20),
    issue_type          VARCHAR(50),
    summary             TEXT,
    status              VARCHAR(100),
    assignee_name       VARCHAR(255),
    assignee_email      VARCHAR(255),
    assignee_account_id VARCHAR(128),
    dev_due_date        DATE,
    qa_due_date         DATE,
    system_due_date     DATE,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `ticket_status_history` — `app/utilization.py:79`

```sql
CREATE TABLE IF NOT EXISTS ticket_status_history (
    id             BIGSERIAL PRIMARY KEY,
    jira_ticket_id TEXT NOT NULL,
    project_key    TEXT,
    issue_type     TEXT,
    from_status    TEXT,
    to_status      TEXT NOT NULL,
    assignee_name  TEXT,
    source         TEXT DEFAULT 'webhook',
    changed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- INDEX: ix_tsh_ticket ON ticket_status_history (jira_ticket_id)
```

### Tables Referenced but Schema Unknown

These tables are referenced in queries but their CREATE TABLE is not in the codebase. They may be created by n8n, by manual SQL, or by an earlier version of the code:

| Table | Referenced In | Usage |
|-------|---------------|-------|
| `jira_projects` | `app/jira_fetcher.py` | Cached Jira project metadata |
| `jira_ticket_cache` | `app/jira_fetcher.py` | Cached Jira ticket data |
| `jira_fetch_log` | `app/jira_fetcher.py` | Jira fetch operation log |
| `graph_jobs` | `app/graph_job_runner.py` | Graph build job tracking |
| `github_repositories` | `app/graph_job_runner.py` | Discovered GitHub repos |
| `github_pull_log` | `app/graph_job_runner.py` | Git pull operation log |

### Qdrant Collections (Vector DB)

| Collection | Used By | Content |
|------------|---------|---------|
| `tickets` | `similar_ticket_finder.py` | Ticket embeddings for similarity search |
| `test_cases` | `testcase_regression_finder.py` | Test case embeddings for regression detection |
| `rca_code_chunks` | `app/rca/` | Code chunk embeddings for RCA retrieval |
| Per-repo collections | `repo_architect/embeddings.py` | Codebase embeddings per repository |

---

## 6. LLM Prompts

Prompts are stored as `.txt` files in the `Prompt/` directory and loaded by `PromptStore` (`app/prompt_store.py`).

### `workflow1_prompt.txt` — Ticket Validation

**Model:** Claude Opus | **Max tokens:** 1024

The prompt instructs Claude to act as a Jira ticket reviewer for a mid-sized payday loan NBFC (Ram Fincorp). It evaluates:
- Summary clarity
- Description detail
- Acceptance criteria
- Assignee assignment
- Priority correctness
- Issue type appropriateness

**Input variables:** `{issueKey}`, `{summary}`, `{description}`, `{assignee}`, `{dueDate}`, `{priority}`, `{issueType}`, `{status}`, `{reporter}`

**Output format:** Raw JSON with `nature` (satisfied/unsatisfied), `llm_review`, `priority` (P0-P4), `priority_explain`

**Special rules:**
- Due date is intentionally ignored when determining nature
- Priority is independently calculated (not copied from input)
- Priority scale: P0 (Critical) → P4 (Trivial), calibrated for NBFC context

### `workflow2_prompt.txt` — Follow-up Conversation

**Model:** Claude Sonnet | **Max tokens:** varies

Used for Slack thread conversations. Receives conversation history and ticket context, responds to user questions about ticket review feedback.

---

## 7. Frontend (React Dashboard)

**Stack:** React 18, Vite 5, react-router-dom 6
**Build:** `npm run build` outputs to `frontend/dist/`, served by FastAPI at `/`
**Auth:** JWT-based login, stored in localStorage

### Routes

| Path | Page | Access |
|------|------|--------|
| `/login` | Login | Public |
| `/` | Home (tabbed dashboard) | Authenticated |
| `/docs-portal` | Documentation portal | documentation role |
| `/users` | User management | admin, usermgr |

### Dashboard Tabs (RBAC-controlled)

| Tab | Component | Roles |
|-----|-----------|-------|
| Repositories | `Repositories.jsx` | admin |
| Jira Tickets | `JiraTickets.jsx` | admin, developer, qa |
| Insights | `Insights.jsx` | admin, developer |
| Logs | `Logs.jsx` | admin |
| Test Cases | `TestCases.jsx` | admin, developer, qa |
| Similar Tickets | `SimilarTickets.jsx` | admin, developer |
| Neo4j Graph | `Neo4jGraph.jsx` | admin |
| RCA | `RCA.jsx` | admin, developer |
| Workflows | `Workflows.jsx` | admin |
| Channel Health | `ChannelHealth.jsx` | admin |
| Utilization | `Utilization.jsx` | admin |
| Ring Studio | `RingStudio.jsx` | admin |
| Zoho Tickets | `ZohoTickets.jsx` | admin |

---

## 8. External Integrations

### Jira Cloud
- **REST API v2** for ticket CRUD, transitions, comments
- **Webhooks** trigger n8n workflows on ticket create/update/transition
- **Custom fields:** dev_due_date, qa_due_date, live_due_date (configurable via env vars)
- **Custom status:** "JIRA GOV APPROVED" (required for WF1 SATISFIED path)

### Slack
- **Bot API** (`xoxb-` token) for sending DMs, replying in threads
- **Channel health checks** via test message send/delete
- **DM channel IDs** stored in `channelid_table`, looked up by Jira display name

### GitHub
- **REST API** for PR analysis, repo discovery, code review context
- **SSH key** mounted in Docker for `git pull` operations
- **PAT** for API calls

### Google Docs (WF6)
- **OAuth 2.0** with refresh token for reading Google Docs
- **Setup script:** `scripts/google_oauth_setup.py`
- **Reads doc content** for PRD/TechDoc review by LLM

### Zoho Desk
- **OAuth 2.0** with refresh token
- **Setup script:** `scripts/zoho_oauth_setup.py`
- **Ticket viewer** in dashboard

### Neo4j
- **Code knowledge graph** built from GitHub repos
- **Git layer:** commits, files, authors
- **Code layer:** functions, classes, imports (via tree-sitter parsing)
- **Ticket context:** links Jira tickets to code via commit messages

### Qdrant
- **Vector similarity search** for tickets, test cases, code chunks
- **Embedding models:** BGE-M3 (FlagEmbedding), Ollama (fallback)

### Ollama
- **Local embedding server** running on EC2
- **Model:** bge-m3 for embeddings
- **Used by:** similar ticket finder, test case regression finder, RCA code retrieval

### n8n
- **Self-hosted** at `https://ai.ramfincorp.co.in/n8n/`
- **API monitoring** via n8n REST API (JWT auth)
- **9 workflows** managing the full ticket lifecycle

---

## 9. Deployment & Infrastructure

### Production URLs
- **API:** `https://ai.ramfincorp.co.in/` (port 8000 behind Caddy)
- **n8n:** `https://ai.ramfincorp.co.in/n8n/`
- **Jira:** `https://ramfincorp.atlassian.net/`

### EC2 Instance Layout

```
/home/ubuntu/
├── JIRA-AI/                    # This project
├── [other repos]/              # Cloned for Neo4j graph + RCA
├── .ssh/                       # GitHub SSH key (mounted in Docker)
└── docker containers:
    ├── jira-ai-api             # FastAPI app (port 8000)
    ├── n8n                     # n8n orchestration
    ├── postgres                # PostgreSQL 16
    ├── qdrant                  # Vector DB (port 6333)
    ├── ollama                  # Embedding server (port 11434)
    ├── neo4j                   # Graph DB
    └── caddy                   # Reverse proxy (HTTPS)
```

### Docker Setup

**Dockerfile** (`Dockerfile`):
- Base: `python:3.12-slim`
- Installs: git, ssh, Node 22, repomix (npm global)
- Builds: React frontend (`npm run build`)
- Entrypoint: `uvicorn api:app --host 0.0.0.0 --port 8000 --ws wsproto`

**docker-compose.yml:**
- Service `jira-ai-api`: builds from Dockerfile, port 8000, mounts host repos + SSH key + ring images
- Service `postgres`: PostgreSQL 16-alpine (profile: local-db, for local dev only)
- Uses `host.docker.internal` for Ollama and Qdrant (running on host)

### Build & Deploy

```bash
# Build and start
docker compose build
docker compose up -d

# View logs
docker compose logs -f jira-ai-api

# Rebuild after code changes
docker compose build && docker compose up -d
```

### First-time Setup

1. Copy `.env.example` to `.env` and fill in all credentials
2. `docker compose up -d` to start the API
3. Admin user is auto-seeded from `ADMIN_EMAIL` / `ADMIN_PASSWORD` env vars
4. Import n8n workflows from `N8N flows/` directory
5. Configure Jira webhooks to point to n8n webhook URLs
6. Populate `channelid_table` with team members' Slack channel IDs
7. Run `scripts/google_oauth_setup.py` if using WF6 (Google Docs review)

---

## 10. Environment Variables

All variables are read by the `Settings` dataclass in `app/config.py`. Required variables are marked with *.

### Core

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL`* | PostgreSQL connection string | `postgresql://user:pass@host:5432/jira_ai` |
| `JWT_SECRET`* | Secret for JWT token signing | Random string |
| `ADMIN_EMAIL` | Auto-seeded admin email | `admin@company.com` |
| `ADMIN_PASSWORD` | Auto-seeded admin password | `ChangeMe!123` |

### LLM

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY`* | Anthropic API key | — |
| `ANTHROPIC_MODEL` | Default Anthropic model | `claude-sonnet-4-20250514` |
| `LLM_PROVIDER` | LLM provider | `anthropic` |
| `LLM_MODEL` | Default model | — |
| `LLM_TIMEOUT_SECONDS` | LLM call timeout | `120` |
| `OPENAI_API_KEY` | OpenAI API key (fallback) | — |
| `TESTCASE_CHAT_MODEL` | Model for test case Q&A | `claude-sonnet-4-20250514` |

### Jira

| Variable | Description |
|----------|-------------|
| `JIRA_BASE_URL`* | `https://company.atlassian.net` |
| `JIRA_EMAIL`* | Jira API email |
| `JIRA_API_TOKEN`* | Jira API token |
| `JIRA_PROJECT_KEYS` | Comma-separated project keys to monitor |
| `JIRA_APPROVED_TRANSITION_NAME` | Name of the AI-approved transition |

### Slack

| Variable | Description |
|----------|-------------|
| `SLACK_BOT_TOKEN`* | Slack bot token (`xoxb-...`) |
| `SLACK_DEFAULT_CHANNEL_ID` | Default Slack channel for notifications |
| `GOVERNOR_NOTIFY_CHANNEL_ID` | Channel for governor alerts |

### Vector & Embeddings

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` |
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_EMBED_MODEL` | Embedding model name | `bge-m3` |
| `SIMILAR_TICKET_MATCH_THRESHOLD` | Similarity threshold | `0.68` |

### Neo4j

| Variable | Description |
|----------|-------------|
| `NEO4J_URI` | Neo4j connection URI |
| `NEO4J_USER` | Neo4j username |
| `NEO4J_PASSWORD` | Neo4j password |

### n8n

| Variable | Description |
|----------|-------------|
| `N8N_BASE_URL` | n8n API base URL |
| `N8N_API_KEY` | n8n API key (JWT) |

### Google (WF6)

| Variable | Description |
|----------|-------------|
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth client secret |
| `GOOGLE_OAUTH_REFRESH_TOKEN` | OAuth refresh token |

### GitHub

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT |
| `GITHUB_ORG` | GitHub organization name |

### SMTP

| Variable | Description |
|----------|-------------|
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | SMTP port |
| `SMTP_USER` | SMTP username |
| `SMTP_PASSWORD` | SMTP password |

For the complete list of 120+ environment variables, see `app/config.py`.

---

## Dependencies

### Python (`requirements.txt`)

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
wsproto>=1.2.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
python-dotenv>=1.0.0
python-dateutil>=2.9.0
python-multipart
openai>=1.30.0
anthropic>=0.40.0
requests>=2.31.0
google-api-python-client>=2.120.0
google-auth>=2.28.0
google-auth-oauthlib>=1.2.0
pyyaml>=6.0
openpyxl>=3.1.5
python-docx>=1.1.0
tenacity>=8.2.0
psycopg[binary]>=3.2.0
psycopg2-binary>=2.9.9
qdrant-client>=1.10.0
FlagEmbedding>=1.2.9
PyJWT>=2.8.0
bcrypt>=4.1.0
email-validator>=2.1.0
neo4j>=5.20,<7
tree-sitter==0.23.2
tree-sitter-language-pack==0.7.4
```

### Frontend (`frontend/package.json`)

- React 18
- Vite 5
- react-router-dom 6

### System-level (installed in Dockerfile)

- Node.js 22
- repomix (npm global)
- git, openssh-client

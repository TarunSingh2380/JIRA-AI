# repograph (local-mode)

A queryable graph of your repos, built from pre-cloned working trees on
your server. No GitHub API access required.

## Assumptions

- Your repos are already cloned somewhere on the server (e.g. `/home/ubuntu/*`).
- Neo4j is running and reachable on `bolt://localhost:7687`.
- Python 3.11+ is available.

## Setup (one-time)

```bash
# 1. Copy this folder onto your server, then:
cd repograph

# 2. Configure
cp .env.example .env
$EDITOR .env       # set NEO4J_PASSWORD and SEARCH_ROOT

# 3. Install Python deps in a venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Apply the schema (constraints + indexes)
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" < schema/cypher_init.cypher
```

## Run the ingest

```bash
# Dry run — list what would be ingested
python -m ingest.run --list

# Real run — walk every git repo found under SEARCH_ROOT
python -m ingest.run

# Pull latest commits from origin before walking (recommended for first run)
python -m ingest.run --fetch-first

# Filter to specific repos by name
python -m ingest.run --only node_crm,ramfincorp-backend

# Verbose logging
python -m ingest.run -v
```

The ingest is idempotent: re-running picks up only new commits.

## Verify it worked

Open Neo4j Browser at `http://YOUR_SERVER:7474` (or use cypher-shell):

```cypher
// How many of each label?
MATCH (n) RETURN labels(n) AS label, count(*) AS n ORDER BY n DESC;

// Commit count per repo
MATCH (r:Repo)<-[:IN_REPO]-(c:Commit)
RETURN r.full_name, count(c) ORDER BY count(c) DESC;
```

More queries in `query/sample_queries.cypher`.

## Optional: run the HTTP service

```bash
uvicorn service.main:app --host 0.0.0.0 --port 8088
```

Then:
```bash
curl http://localhost:8088/health
curl http://localhost:8088/repos
curl 'http://localhost:8088/files/touched_recently?keyword=razorpay&days=180'
```

## BGE-M3 semantic embeddings

Stage 3 stores dense BGE-M3 vectors directly in Neo4j on `EmbeddingDocument`
nodes. Each document is linked back to the graph item it represents:
`Repo`, `Commit`, `File`, or `JiraTicket`.

Configure:

```text
BGE_M3_MODEL_NAME=BAAI/bge-m3
SEMANTIC_EMBEDDING_DIMENSIONS=1024
SEMANTIC_EMBED_BATCH_SIZE=32
SEMANTIC_MAX_DOCS_PER_RUN=0
```

Build or refresh embeddings:

```bash
curl -X POST http://localhost:8088/embeddings/rebuild \
  -H 'Content-Type: application/json' \
  -d '{"kinds":["repo","commit","file","jira_ticket"],"batch_size":32}'
```

Search:

```bash
curl -X POST http://localhost:8088/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query":"payment retry failures","top_k":10}'
```

## Re-running

```bash
python -m ingest.run --fetch-first     # picks up new commits since last run
```

Schedule it via cron every 15 minutes if you want a near-live graph.

## Project layout

```
.
├── .env.example                # config template
├── config.py                   # pydantic settings (env loader)
├── requirements.txt
├── README.md
├── schema/
│   └── cypher_init.cypher      # constraints, indexes, schema docs
├── ingest/
│   ├── local_repos.py          # discovers .git folders under SEARCH_ROOT
│   ├── git_history.py          # pygit2 walker + Neo4j writers
│   └── run.py                  # CLI entry point
├── query/
│   └── sample_queries.cypher   # useful queries to verify ingest
├── service/
│   └── main.py                 # FastAPI service
├── stage2_ast/
│   └── README.py               # implementation plan for tree-sitter overlay
└── stage3_semantic/
    └── README.py               # implementation plan for LlamaIndex layer
```

## Troubleshooting

**"No git repos found"** — Check `SEARCH_ROOT` and `MAX_SEARCH_DEPTH` in
`.env`. The default search depth is 3, which handles `/home/ubuntu/<repo>`
fine but not deeply-nested layouts.

**`UNAUTHORIZED` connecting to Neo4j** — Your password didn't make it
into `.env`, or you haven't changed the default `neo4j/neo4j` first-time
password yet. Use `cypher-shell` interactively once to set a password,
then put it in `.env`.

**Some repos fail with "Diff stats failed"** — The walker logs and
moves on; that commit's stats will be zero but the commit itself
will still be in the graph. Usually caused by malformed historical
commits and is safe to ignore.

**Re-run takes a long time despite being idempotent** — pygit2 still
walks every commit; Neo4j's `MERGE` is what dedupes. To skip already-walked
commits, set `SINCE_DAYS=7` in `.env` for daily delta runs.

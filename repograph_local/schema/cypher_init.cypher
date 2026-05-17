// schema/cypher_init.cypher
// Run once after `docker compose up` to set up uniqueness constraints and indexes.
// Re-runnable: every statement uses IF NOT EXISTS.
//
// Apply with:
//   cypher-shell -u neo4j -p $NEO4J_PASSWORD -f schema/cypher_init.cypher
// Or paste the whole file into Neo4j Browser.

// ─────────────────────────────────────────────────────────────────────
// Node uniqueness constraints (also create indexes automatically)
// ─────────────────────────────────────────────────────────────────────

// Stage 1 — git history layer
CREATE CONSTRAINT repo_full_name IF NOT EXISTS
  FOR (r:Repo) REQUIRE r.full_name IS UNIQUE;

CREATE CONSTRAINT commit_sha IF NOT EXISTS
  FOR (c:Commit) REQUIRE c.sha IS UNIQUE;

CREATE CONSTRAINT file_path_in_repo IF NOT EXISTS
  FOR (f:File) REQUIRE (f.repo_full_name, f.path) IS UNIQUE;

CREATE CONSTRAINT author_email IF NOT EXISTS
  FOR (a:Author) REQUIRE a.email IS UNIQUE;

CREATE CONSTRAINT pr_id IF NOT EXISTS
  FOR (p:PullRequest) REQUIRE (p.repo_full_name, p.number) IS UNIQUE;

CREATE CONSTRAINT branch_id IF NOT EXISTS
  FOR (b:Branch) REQUIRE (b.repo_full_name, b.name) IS UNIQUE;

CREATE CONSTRAINT embedding_document_id IF NOT EXISTS
  FOR (d:EmbeddingDocument) REQUIRE d.id IS UNIQUE;

// Stage 2 — code-structure layer (used by tree-sitter overlay)
CREATE CONSTRAINT function_qualified IF NOT EXISTS
  FOR (fn:Function) REQUIRE fn.qualified_name IS UNIQUE;

CREATE CONSTRAINT class_qualified IF NOT EXISTS
  FOR (cl:Class) REQUIRE cl.qualified_name IS UNIQUE;

CREATE CONSTRAINT module_qualified IF NOT EXISTS
  FOR (m:Module) REQUIRE m.qualified_name IS UNIQUE;

// ─────────────────────────────────────────────────────────────────────
// Secondary indexes — for the queries we'll actually run
// ─────────────────────────────────────────────────────────────────────

CREATE INDEX commit_committed_at IF NOT EXISTS
  FOR (c:Commit) ON (c.committed_at);

CREATE INDEX commit_short_sha IF NOT EXISTS
  FOR (c:Commit) ON (c.short_sha);

CREATE INDEX file_extension IF NOT EXISTS
  FOR (f:File) ON (f.extension);

CREATE INDEX pr_merged_at IF NOT EXISTS
  FOR (p:PullRequest) ON (p.merged_at);

CREATE INDEX pr_state IF NOT EXISTS
  FOR (p:PullRequest) ON (p.state);

CREATE INDEX function_file IF NOT EXISTS
  FOR (fn:Function) ON (fn.file_path);

CREATE VECTOR INDEX embedding_document_vector IF NOT EXISTS
  FOR (d:EmbeddingDocument) ON (d.embedding)
  OPTIONS {indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
  }};

// ─────────────────────────────────────────────────────────────────────
// Schema documentation as a comment block — kept here so the contract
// between ingestion code and queries stays in one place.
// ─────────────────────────────────────────────────────────────────────
//
// NODES
//   (:Repo {full_name, name, owner, default_branch,
//           private, language, created_at, pushed_at,
//           description, url, ingested_at})
//   (:Commit {sha, short_sha, message, summary,
//             authored_at, committed_at,
//             additions, deletions, files_changed_count})
//   (:File {repo_full_name, path, extension, current})
//   (:Author {email, name})
//   (:PullRequest {repo_full_name, number, title, state,
//                  created_at, merged_at, base, head, url})
//   (:Branch {repo_full_name, name, head_sha})
//   (:EmbeddingDocument {id, kind, source_key, repo_full_name,
//                        title, text, metadata_json, embedding,
//                        embedding_model, embedding_dimensions, embedded_at})
//
//   // Stage 2
//   (:Function {qualified_name, name, file_path, repo_full_name,
//               start_line, end_line, ast_hash, language})
//   (:Class    {qualified_name, name, file_path, repo_full_name,
//               start_line, end_line, ast_hash, language})
//   (:Module   {qualified_name, file_path, repo_full_name, language})
//
// EDGES
//   (:Commit)-[:IN_REPO]->(:Repo)
//   (:Commit)-[:AUTHORED_BY]->(:Author)
//   (:Commit)-[:PARENT]->(:Commit)
//   (:Commit)-[:TOUCHES {change_type, additions, deletions}]->(:File)
//   (:File)-[:IN_REPO]->(:Repo)
//   (:Branch)-[:HEAD]->(:Commit)
//   (:Branch)-[:IN_REPO]->(:Repo)
//   (:PullRequest)-[:IN_REPO]->(:Repo)
//   (:PullRequest)-[:MERGED_AS]->(:Commit)
//   (:PullRequest)-[:AUTHORED_BY]->(:Author)
//   (:EmbeddingDocument)-[:EMBEDS]->(:Repo|:Commit|:File|:JiraTicket)
//
//   // Stage 2
//   (:Function)-[:DEFINED_IN]->(:File)
//   (:Function)-[:CALLS]->(:Function)
//   (:Class)-[:DEFINED_IN]->(:File)
//   (:Function)-[:METHOD_OF]->(:Class)
//   (:Class)-[:EXTENDS]->(:Class)
//   (:Module)-[:IMPORTS]->(:Module)

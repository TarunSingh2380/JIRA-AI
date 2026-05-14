// query/sample_queries.cypher
// Run any of these in Neo4j Browser (http://localhost:7474) to verify
// the ingest worked and see how to query the graph.

// ─── Sanity: count things ──────────────────────────────────────────────

// How many of each node label?
CALL apoc.meta.stats() YIELD labels, relTypesCount, propertyKeyCount
RETURN labels, relTypesCount, propertyKeyCount;

// Or, without APOC:
MATCH (n) RETURN labels(n) AS label, count(*) AS n ORDER BY n DESC;

// Total commits per repo
MATCH (r:Repo)<-[:IN_REPO]-(c:Commit)
RETURN r.full_name AS repo, count(c) AS commits
ORDER BY commits DESC;


// ─── Activity views ────────────────────────────────────────────────────

// Top contributors across all repos
MATCH (a:Author)<-[:AUTHORED_BY]-(c:Commit)
RETURN a.name AS author, a.email AS email, count(c) AS commits
ORDER BY commits DESC LIMIT 25;

// Commits in the last 30 days, per repo
MATCH (r:Repo)<-[:IN_REPO]-(c:Commit)
WHERE c.committed_at > datetime() - duration({days: 30})
RETURN r.full_name AS repo, count(c) AS recent_commits
ORDER BY recent_commits DESC;

// Most-touched files across the org over all history
MATCH (f:File)<-[t:TOUCHES]-(c:Commit)
RETURN f.repo_full_name AS repo, f.path AS file, count(t) AS touch_count
ORDER BY touch_count DESC LIMIT 50;


// ─── Things that get the bot useful answers ───────────────────────────

// "What has Priyanshu changed recently in allthingsgood-backend?"
MATCH (a:Author {name: "Priyanshu"})<-[:AUTHORED_BY]-(c:Commit)-[:IN_REPO]->(r:Repo)
WHERE r.full_name ENDS WITH "allthingsgood-backend"
  AND c.committed_at > datetime() - duration({days: 90})
MATCH (c)-[t:TOUCHES]->(f:File)
RETURN c.short_sha, c.summary, c.committed_at, collect(f.path)[..10] AS files
ORDER BY c.committed_at DESC LIMIT 25;

// "Who has touched payment-related files recently?"
MATCH (c:Commit)-[:TOUCHES]->(f:File)
WHERE toLower(f.path) CONTAINS "razorpay"
   OR toLower(f.path) CONTAINS "payu"
   OR toLower(f.path) CONTAINS "payment"
WITH c, f
WHERE c.committed_at > datetime() - duration({days: 180})
MATCH (c)-[:AUTHORED_BY]->(a:Author)
RETURN a.name AS author, count(DISTINCT c) AS commits,
       collect(DISTINCT f.path)[..5] AS sample_files
ORDER BY commits DESC LIMIT 20;

// Commit-by-commit history of a specific file (great for "when did this break?")
MATCH (f:File {repo_full_name: "ramfincorp/allthingsgood-backend",
               path: "apps/orders/services/sync.py"})
MATCH (c:Commit)-[t:TOUCHES]->(f)
MATCH (c)-[:AUTHORED_BY]->(a:Author)
RETURN c.committed_at, c.short_sha, a.name, t.change_type,
       t.additions, t.deletions, c.summary
ORDER BY c.committed_at DESC LIMIT 50;


// ─── Cross-repo patterns ──────────────────────────────────────────────

// Authors who commit to many repos (likely platform / infra people)
MATCH (a:Author)<-[:AUTHORED_BY]-(:Commit)-[:IN_REPO]->(r:Repo)
WITH a, count(DISTINCT r) AS repo_count
WHERE repo_count >= 3
RETURN a.name AS author, a.email AS email, repo_count
ORDER BY repo_count DESC;

// Files with the same path across different repos (potential shared concepts)
MATCH (f1:File), (f2:File)
WHERE f1.path = f2.path
  AND f1.repo_full_name < f2.repo_full_name      // dedupe pairs
WITH f1.path AS path, collect(DISTINCT f1.repo_full_name + "," + f2.repo_full_name) AS pairs
WHERE size(pairs) > 0
RETURN path, pairs[..5] AS sample_pairs LIMIT 30;

"""Stage 3 — LlamaIndex semantic layer.

This stage adds:
  - Code chunks (one per Function from Stage 2) embedded into Qdrant.
  - Commit-message embeddings (for similarity over commit history).
  - GraphRAG queries: natural-language → Cypher + vector retrieval → answer.

Architecture sketch:

    LlamaIndex PropertyGraphIndex
        ├── property_graph_store = Neo4jPropertyGraphStore(...)
        ├── vector_store         = QdrantVectorStore(...)
        ├── embed_model          = VoyageEmbedding('voyage-code-3')
        └── llm                  = Anthropic('claude-sonnet-4-6')

    .from_existing(...)            # connect to the already-ingested graph
    .as_query_engine(...)          # GraphRAG-style query path
    .as_retriever(...)             # for the /search/semantic endpoint

Concrete steps to implement:
  1. Install Stage-3 deps (commented out in requirements.txt for now).
  2. Build a "node ingestor" that, for every :Function node in Neo4j:
       - Reads its source from the cached repo mirror at HEAD.
       - Chunks it (use tree-sitter boundaries from Stage 2; do NOT use
         LlamaIndex's default token splitter, which splits mid-function).
       - Embeds with Voyage code-3 (or Jina v2 for self-hosted).
       - Writes to Qdrant with metadata {qualified_name, file_path,
         repo_full_name, ast_hash}.
  3. Wire LlamaIndex's PropertyGraphIndex to use both stores.
  4. Implement the /search/semantic and /ask endpoints in service/main.py.

Cost & rate notes (for ~330k Functions × 1 embedding each):
  - Voyage code-3 is ~$0.06/M tokens. ~500 tokens/function avg.
    → 330k × 500 × $0.06/1M ≈ $10 one-time, then incremental by ast_hash.
  - Anthropic Sonnet for GraphRAG answers ≈ $3/M input, $15/M output.
    A typical query consumes ~5k input + 1k output ≈ $0.03/query.

Incremental re-embedding:
  When a commit changes a function, the new ast_hash differs. Re-embed
  ONLY that function. The watcher loop is: (a) listen for new commits in
  Neo4j, (b) diff ast_hash, (c) re-embed deltas.
"""

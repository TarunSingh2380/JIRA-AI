"""Stage 2 — tree-sitter AST overlay for JavaScript / TypeScript.

For each File node already in the graph (Stage 1), parse the current
working-tree contents and emit :Function / :Class / :Module nodes,
plus :CALLS / :IMPORTS / :METHOD_OF / :EXTENDS edges.

To implement:
  1. Use tree-sitter-languages bundle: get_parser('typescript'),
     get_parser('javascript'), get_parser('tsx').
  2. For each File whose extension ∈ {ts, tsx, js, jsx, mjs}:
     a. Read its content from the cached mirror's working tree (or use
        pygit2 to fetch the blob at the current HEAD).
     b. Parse to AST.
     c. Walk the AST with tree-sitter queries to find:
          - function_declaration, method_definition, arrow_function (named)
          - class_declaration
          - import_statement, export_statement
          - call_expression  → for :CALLS edges
     d. Compute ast_hash for each Function (SHA-256 of the tree-sitter
        S-expression). Skip re-emitting if the hash is unchanged — this
        is how incremental re-ingestion stays cheap.
  3. Batch-MERGE into Neo4j using the Stage-2 node labels already in
     schema/cypher_init.cypher.

Call resolution is the trickiest piece. Approaches in increasing order
of fidelity (and effort):
  - Same-file: just match `name(...)` to a function defined in the same module.
  - Same-package: walk imports, resolve relative paths.
  - Full type-aware resolution: use ts-morph (Node.js) for TypeScript.

Recommendation: ship a working same-file + same-package resolver first.
That covers ~70% of real call edges in a Node.js codebase, and the
remaining 30% are mostly external library calls that we don't care
about for the PR Quality Gate anyway.

This file is a placeholder. When you're ready to implement, copy the
shape of ingest/git_history.py — same async + batched MERGE pattern.
"""

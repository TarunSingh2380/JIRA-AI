# Code Analysis Report

Generated: 2026-05-19 11:26 UTC
Repositories selected: 1
Embedding model selected: codebase_bge_m3

## Executive Summary

This report combines local clone inspection with graph database context from the repository ingestion pipeline. Graph-backed sections reflect the latest successful graph build.

## Repository Inventory

| Repository | Branch | Commit | Files | Source Lines | Graph Commits |
| --- | --- | --- | --- | --- | --- |
| agrimfincapindia | main | 15af4ccbc3e1 | 83 | 12604 | 0 |

## agrimfincapindia

### 1. Repository Overview

| Field | Analysis |
| --- | --- |
| Purpose of repo | A professional, responsive website for Agrim Fincap Private Limited built with React and Vite. |
| Domain/problem solved | Backend application service |
| Main technologies | JavaScript, CSS, Markdown, JSON, Next.js, React |
| Framework/platform hints | - |
| Architecture shape | Service or application repository |
| Monolith vs microservice | Likely microservice or focused backend service |
| Main entry points | package.json script `build`: next build<br>package.json script `dev`: next dev<br>package.json script `lint`: next lint<br>package.json script `start`: next start<br>pages/index.js |
| Local path | /home/ubuntu/agrimfincapindia |
| Remote | git@github.com:Ram-Fincorp/agrimfincapindia.git |
| Branch / commit | main / 15af4ccbc3e1 |

### 2. Repository Structure Analysis

| Directory/module | Responsibility | Files |
| --- | --- | --- |
| src | Primary source tree | 33 |
| temp_docx | Feature or implementation area inferred from path | 19 |
| . | Repository root, configuration, entry points, and documentation | 14 |
| pages | Feature or implementation area inferred from path | 14 |
| public | Feature or implementation area inferred from path | 3 |

- Layering signal: layering is not obvious from top-level directories
- Feature grouping signal: primary feature areas appear to be src, temp_docx, pages, public
- Key project/config files: .env.example, README.md, package-lock.json, package.json
- Detected manifests: package.json

### 3. Semantic Clustering Analysis

| Cluster | Dominant kind | Items | Avg similarity | Examples |
| --- | --- | --- | --- | --- |
| src | file | 27 | 0.78 | src/components/Footer.jsx<br>src/pages/TermsConditions.jsx<br>src/components/Contact.jsx<br>src/components/TrustIndicators.jsx<br>src/components/Services.jsx |
| pages | file | 7 | 0.83 | pages/contact-us.js<br>pages/privacy-policy.js<br>pages/_app.js<br>pages/services.js<br>pages/about-us.js |

### 4. Dependency Graph Insights

| Metric | Value |
| --- | --- |
| Modules indexed | 0 |
| Module import edges | 0 |
| Functions indexed | 0 |
| Function call edges | 0 |
| Circular dependencies found | 0 |

Most connected modules:

| Node | File | In-degree | Out-degree | Centrality |
| --- | --- | --- | --- | --- |
| - | - | 0 | 0 | 0 |

Most connected functions:

| Node | File | In-degree | Out-degree | Centrality |
| --- | --- | --- | --- | --- |
| - | - | 0 | 0 | 0 |

Top local imports/dependencies:

| Dependency | References |
| --- | --- |
| react | 21 |
| next | 9 |
| react-dom | 1 |

### 5. Architectural Pattern Detection

| Pattern | Evidence | Confidence |
| --- | --- | --- |
| No strong pattern detected | Directory and graph evidence is sparse. | low |

### 6. Code Complexity Analysis

| Metric | Value |
| --- | --- |
| Files inspected | 83 |
| Approximate source/config lines | 12604 |
| Large files >=250 lines | 12 |
| Complex units detected | 2 |
| Module dependency density | 0.00 |
| Deep inheritance samples | 0 |

Largest files:

| Path | Lines | Estimated complexity |
| --- | --- | --- |
| package-lock.json | 5387 | 151 |
| src/components/Hero.css | 525 | 1 |
| src/pages/ServicesPage.jsx | 346 | 27 |
| src/pages/ContactUs.jsx | 336 | 10 |
| src/pages/LendingPolicy.jsx | 325 | 7 |
| src/pages/AboutUs.jsx | 302 | 15 |
| src/components/Footer.css | 296 | 1 |
| src/components/About.css | 275 | 1 |
| src/pages/CreditPolicy.jsx | 264 | 13 |
| src/components/Header.css | 262 | 1 |

Highest-complexity local units:

| Kind | Name | Path | Lines | Cyclomatic estimate |
| --- | --- | --- | --- | --- |
| file | package-lock.json | package-lock.json | 5387 | 151 |
| file | ServicesPage.jsx | src/pages/ServicesPage.jsx | 346 | 27 |

### 7. Semantic Search Quality

| Item | Value |
| --- | --- |
| Embedding model | codebase_bge_m3 (37) |
| Available models in Neo4j | codebase_bge_m3 (37) |
| Embedding dimensions | 1024 (37) |
| Documents by kind | file: 37 |
| Chunking strategy | One `EmbeddingDocument` per graph item such as repo, commit, file, or future function chunks. |
| Similarity effectiveness | Good baseline: vector-bearing documents form meaningful semantic neighborhoods. |

Retrieval examples to validate quality:

- Find authentication or permission flows
- Find persistence/database access paths
- Find event consumers/producers and retry logic
- Find files related to a recent high-touch area

### 8. Graph Schema Description

| Node type | Description | Key metadata |
| --- | --- | --- |
| Repo | Repository identity and source metadata | full_name, name, owner, language, url, local_path |
| Commit | Git commit history | sha, summary, authored_at, committed_at, additions, deletions |
| Author | Commit or PR author | email, name |
| File | Repository file | repo_full_name, path, extension, current |
| Function | AST function definition | qualified_name, file_path, start_line, end_line, ast_hash |
| Class | AST class definition | qualified_name, file_path, start_line, end_line, ast_hash |
| Module | AST/import module | qualified_name, file_path, language |
| EmbeddingDocument | Vector-search document linked to source graph item | kind, source_key, title, text, embedding_model_key, embedding_model, embedding_dimensions |
| JiraTicket | Jira ticket node when Jira graph sync is enabled | key, summary, status, priority, assignee |

| Relationship | Meaning |
| --- | --- |
| IN_REPO | Commit, File, Branch, or PR belongs to a repository |
| AUTHORED_BY | Commit or PR was authored by an Author |
| PARENT | Commit parent relationship |
| TOUCHES | Commit changed a File, with change type/additions/deletions |
| DEFINED_IN | Function/Class belongs to a File |
| CALLS | Function invokes another Function |
| METHOD_OF | Function is a method of a Class |
| EXTENDS | Class inheritance relationship |
| IMPORTS | Module imports another Module |
| EMBEDS | EmbeddingDocument represents a Repo, Commit, File, or JiraTicket |

### 9. Retrieval-Augmented Generation Readiness

- Hybrid retrieval readiness: high
- Graph + vector retrieval: available
- Metadata filtering: repo_full_name, kind, source_key, title, and JSON metadata are available on embedding documents.
- Context window efficiency: good
- AST function chunks are not indexed yet, so function-level retrieval will be limited.

### 10. Cross-Reference Intelligence

Function call samples:

| Caller | Callee | Caller file |
| --- | --- | --- |
| - | - | No function call edges indexed. |

API / database / event lineage hints from local paths:

| Flow area | Detected files |
| --- | --- |
| API endpoints | pages/interest-rates.js<br>src/pages/InterestRate.jsx |
| Database/persistence | - |
| Events/queues | - |

### 11. Hotspot Detection

Change-prone files from git graph:

| Path | Touches |
| --- | --- |
| - | 0 |

Architectural hotspots by centrality:

| Node | File | Centrality |
| --- | --- | --- |
| - | - | 0 |

Semantic hotspots:

| Cluster | Items | Average similarity |
| --- | --- | --- |
| src | 27 | 0.78 |
| pages | 7 | 0.83 |

Local complexity hotspots:

| Path | Lines | Complexity |
| --- | --- | --- |
| package-lock.json | 5387 | 151 |
| src/components/Hero.css | 525 | 1 |
| src/pages/ServicesPage.jsx | 346 | 27 |
| src/pages/ContactUs.jsx | 336 | 10 |
| src/pages/LendingPolicy.jsx | 325 | 7 |
| src/pages/AboutUs.jsx | 302 | 15 |
| src/components/Footer.css | 296 | 1 |
| src/components/About.css | 275 | 1 |

### 12. Duplicate / Similar Logic Detection

High-similarity embedding pairs:

| Similarity | Item A | Item B |
| --- | --- | --- |
| 0.94 | pages/lending-policy.js | pages/credit-policy.js |
| 0.93 | pages/services.js | pages/index.js |

Repeated filenames that may indicate duplicated responsibilities:

| Filename | Count | Examples |
| --- | --- | --- |
| agrim fincap draft.docx | 2 | Agrim Fincap Draft.docx<br>temp_docx/Agrim Fincap Draft.docx |
| [content_types].xml | 2 | temp_docx/[Content_Types].xml<br>temp_docx/temp_docx/[Content_Types].xml |
| document.xml | 2 | temp_docx/word/document.xml<br>temp_docx/temp_docx/word/document.xml |
| settings.xml | 2 | temp_docx/word/settings.xml<br>temp_docx/temp_docx/word/settings.xml |
| numbering.xml | 2 | temp_docx/word/numbering.xml<br>temp_docx/temp_docx/word/numbering.xml |
| fonttable.xml | 2 | temp_docx/word/fontTable.xml<br>temp_docx/temp_docx/word/fontTable.xml |
| styles.xml | 2 | temp_docx/word/styles.xml<br>temp_docx/temp_docx/word/styles.xml |
| document.xml.rels | 2 | temp_docx/word/_rels/document.xml.rels<br>temp_docx/temp_docx/word/_rels/document.xml.rels |
| theme1.xml | 2 | temp_docx/word/theme/theme1.xml<br>temp_docx/temp_docx/word/theme/theme1.xml |
| .rels | 2 | temp_docx/temp_docx/_rels/.rels<br>temp_docx/_rels/.rels |

### 13. Documentation Coverage

| Metric | Value |
| --- | --- |
| Documentation files | 4 |
| Top-level code/module directories | 4 |
| Coverage assessment | Good: documentation coverage broadly matches visible module count. |
| README summary | A professional, responsive website for Agrim Fincap Private Limited built with React and Vite. |
| Embedding docs available | 37 |

Potentially undocumented modules:

- src
- temp_docx
- pages
- public

### 14. Security & Risk Analysis

| Risk area | Evidence |
| --- | --- |
| Sensitive paths | - |
| External integrations/dependencies | - |
| Auth bypass graph evidence | Requires populated AST call graph; not directly provable from current local scan. |
| Dependency risks | Review lockfiles and package manifests listed in key project files. |

- No obvious security-sensitive path names were detected; this is not a substitute for SAST/secret scanning.

### 15. Suggested Improvements

- Split oversized modules and move cohesive responsibilities into smaller units.
- Review high-similarity embedding pairs and merge repeated business logic where ownership overlaps.
- Use semantic clusters as refactoring candidates; large clusters can reveal hidden coupling or broad responsibilities.
- Run or implement the AST ingestion layer so Function/Class/Module nodes can power call-chain and complexity analysis.

### Appendix: Recent Activity

Primary contributors from graph:

| Contributor | Email | Commits |
| --- | --- | --- |
| - | - | 0 |

Recent graph commits:

| Commit | Date | Summary |
| --- | --- | --- |
| - | - | - |

Recent local git commits:

| Commit | Date | Author | Summary |
| --- | --- | --- | --- |
| 15af4cc | 2025-09-11 | Rajendra Vishwakarma | Remove unused variable in build error |
| 27c3f3d | 2025-09-10 | Rajendra Vishwakarma | Update all seo related tag and content |
| e77bee4 | 2025-09-10 | Rajendra Vishwakarma | loan calculator functional and some design changes |
| b11f4a0 | 2025-09-10 | Rajendra Vishwakarma | Update content for privacy policy |
| 85f51e6 | 2025-09-10 | Rajendra Vishwakarma | Change privacy policy content update |
| 49bd3fe | 2025-09-09 | Rajendra Vishwakarma | Home and service chnages update |
| 404daa0 | 2025-09-09 | Rajendra Vishwakarma | Merge branch 'master' of github.com:Ram-Fincorp/agrimfincapindia |
| 88ae284 | 2025-09-09 | Rajendra Vishwakarma | Build dir configuration |
| 4caa2c5 | 2025-09-09 | sandeepsinghram999 | Update README.md |
| cc52cd5 | 2025-09-09 | Rajendra Vishwakarma | Initial commit |

Working tree notes:

Working tree is clean or status could not be read.

# SearchX --- Project Context & Development Guide

**Document:** `PROJECT_CONTEXT.md`\
**Version:** 1.0\
**Status:** Initial project baseline\
**Purpose:** This is the single source of truth for planning,
implementing, testing, and maintaining SearchX.

> **Instruction to the AI coding agent:** Read this file before making
> changes. Keep it accurate as the codebase evolves. Implement only the
> module explicitly assigned by the user. Do not generate the entire
> application in one step.

------------------------------------------------------------------------

## 1. Project Overview

**SearchX** is an educational, industry-inspired document search engine.
It demonstrates the core ideas used in information-retrieval systems:
collecting documents, extracting and cleaning text, building an inverted
index, processing queries, ranking results, and presenting them through
a web application.

SearchX is **not** intended to crawl or index the entire public
internet, and it is not a replacement for Google. The first release will
search a controlled collection of permitted websites and/or documents.
The system should be designed so that its capabilities can be expanded
gradually.

### Core user journey

1.  An administrator adds an allowed website URL or imports documents.
2.  The crawler/importer collects page or document content.
3.  The processing pipeline extracts and normalizes text.
4.  The indexing engine builds and stores a searchable inverted index.
5.  A user enters a query in the SearchX web interface.
6.  The query is normalized and matched against the index.
7.  Matching documents are ranked by relevance.
8.  The interface displays titles, URLs, snippets, and pagination.

### Main engineering goals

-   Implement the search fundamentals ourselves rather than hiding them
    behind a hosted search service.
-   Use C++ for the core indexing and retrieval engine.
-   Keep components modular, testable, and connected through explicit
    interfaces.
-   Measure performance rather than making unsupported performance
    claims.
-   Make the project understandable enough that the student can explain
    every major design decision in an interview.

------------------------------------------------------------------------

## 2. Technology Stack

Use the following stack unless the user explicitly approves a change.

  -----------------------------------------------------------------------
  Area                    Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Core search engine      C++ (C++17 or newer)    Tokenization support
                                                  where appropriate,
                                                  inverted index, query
                                                  matching, ranking

  Crawler and document    Python 3                Fetch permitted pages,
  ingestion                                       discover links, extract
                                                  source content

  Backend API             Python + FastAPI        API endpoints,
                                                  orchestration,
                                                  validation,
                                                  authentication for
                                                  admin features

  Frontend                React                   Search homepage,
                                                  results page, admin
                                                  interface

  Primary database        PostgreSQL              Document metadata,
                                                  crawl jobs, source
                                                  configuration,
                                                  analytics

  Cache                   Redis                   Optional caching of
                                                  repeated search queries
                                                  and short-lived
                                                  operational data

  Testing                 C++ test framework +    Unit, integration, and
                          pytest + frontend tests end-to-end validation

  Containerization        Docker / Docker Compose Repeatable local
                                                  development and
                                                  deployment

  Version control         Git                     Small, reviewable
                                                  commits for each
                                                  completed milestone
  -----------------------------------------------------------------------

### Stack boundaries

-   The C++ engine owns the core retrieval logic: index construction,
    index lookup, query matching, and ranking.
-   Python owns crawling, ingestion orchestration, and the FastAPI
    service.
-   PostgreSQL stores durable document metadata and operational records.
-   Redis is an optimization, not the source of truth. Search must still
    work when Redis is unavailable.
-   React is a client of the API. It must not contain search-ranking or
    indexing business logic.
-   Do not add Elasticsearch, OpenSearch, a hosted vector database, or
    another search engine as a replacement for the custom C++ engine.
    Optional comparisons may be added later only with approval.

------------------------------------------------------------------------

## 3. Scope and Delivery Strategy

Build SearchX in stages. First make a reliable single-machine search
engine. Only after it works and has benchmarks should distributed
features be considered.

### Version 1 --- Working search engine

-   Controlled website/document ingestion.
-   HTML text extraction and normalization.
-   C++ inverted index.
-   Basic AND/OR keyword retrieval.
-   TF-IDF ranking.
-   BM25 ranking.
-   Search API.
-   React search interface.
-   PostgreSQL persistence for metadata and index-related records.
-   Unit and integration tests.
-   Docker-based local setup.

### Version 2 --- Quality and usability

-   Search snippets with matched terms.
-   Pagination and filters.
-   Autocomplete using a Trie or a well-defined prefix index.
-   Search history and basic analytics.
-   Crawl status and admin dashboard.
-   Redis query caching with invalidation rules.
-   Better error handling and observability.

### Version 3 --- Advanced engineering

-   Parallel document processing and multithreaded indexing.
-   Persistent index segments and safe index rebuilds.
-   Incremental re-indexing.
-   Benchmark suite and performance profiling.
-   Index sharding and distributed query execution as a later
    research/engineering extension.
-   Fault handling and recovery strategy.

Do not claim that SearchX is distributed, fault-tolerant, or
production-scale until those features have actually been implemented and
tested.

------------------------------------------------------------------------

## 4. Major Modules

### Module A --- Project Foundation

Responsibilities: - Create a clean repository structure. - Define build
and run instructions. - Set coding conventions and configuration
management. - Add environment-variable handling and `.env.example`. -
Add logging and a consistent error-handling approach. - Add Docker
Compose when the basic services are ready.

Acceptance criteria: - A new developer can follow the README and run the
starter project. - Secrets are not committed. - Build/test commands are
documented. - The project has a clear separation between C++, Python
backend/crawler, frontend, and tests.

### Module B --- Document Model and Ingestion Contract

Define a common document representation used across components.

Suggested logical fields: - `document_id`: stable unique identifier. -
`source_url`: canonical source URL, if applicable. - `title`: extracted
title. - `content`: cleaned text. - `description`: optional summary or
metadata. - `language`: optional detected language. - `fetched_at`:
ingestion timestamp. - `content_hash`: hash used to detect unchanged or
duplicate content. - `status`: ingestion/indexing state.

The exact C++ and Python representations may differ, but their
serialized/API contract must be documented and tested.

Acceptance criteria: - Required fields and optional fields are
explicit. - Invalid or empty documents are handled safely. - Duplicate
detection has a documented rule.

### Module C --- Text Processing

Responsibilities: - Extract readable text from HTML. - Remove scripts,
styles, navigation noise, and irrelevant markup where practical. -
Normalize case and whitespace. - Tokenize text consistently. - Handle
punctuation and Unicode deliberately. - Support stopword filtering as a
configurable option. - Keep original title/content for display and
normalized tokens for indexing.

Important: - Do not silently apply stemming or lemmatization unless
selected and documented. If enabled, apply the same normalization to
indexed documents and user queries. - Preserve enough positional
information if phrase search or snippets will need it later.

Acceptance criteria: - Unit tests cover punctuation, mixed case, empty
text, repeated words, and non-ASCII input. - The same normalization
rules are used for documents and queries.

### Module D --- C++ Inverted Index Engine

This is the central learning and engineering module.

Core concepts: - Term dictionary. - Posting lists mapping terms to
document IDs. - Term frequency per document. - Optional token positions
for phrase search. - Document metadata lookup. - Index build, lookup,
update, and removal operations.

Illustrative conceptual structure:

``` text
"python" -> [(doc_1, term_frequency=2), (doc_3, term_frequency=1)]
"search" -> [(doc_2, term_frequency=1)]
```

Implementation expectations: - Use appropriate C++ data structures (for
example, unordered maps and vectors) and explain the trade-offs. - Avoid
scanning every document for every query once the inverted index
exists. - Define how document IDs are assigned and kept stable. - Define
behavior for duplicate documents and re-indexing. - Keep the engine
independent from FastAPI and React. - Expose a documented interface to
Python. Choose and justify a suitable integration mechanism (for
example, a small command-line process with a defined JSON protocol or a
native binding). Do not mix multiple approaches without need.

Acceptance criteria: - Index can be built from a known set of
documents. - Single-term and multi-term queries return correct document
IDs. - Empty, unknown, and repeated query terms are handled. - Unit
tests verify posting lists and query results. - Complexity of key
operations is documented. - C++ build instructions are reproducible.

### Module E --- Retrieval and Ranking

Implement in stages:

1.  Boolean/keyword retrieval (AND and OR behavior must be explicit).
2.  TF-IDF scoring.
3.  BM25 scoring.
4.  Sort by descending score with deterministic tie-breaking.

Ranking requirements: - Document frequency and corpus statistics must be
calculated correctly. - BM25 parameters (such as `k1` and `b`) must be
configurable or documented. - Avoid arbitrary scores presented as real
relevance values. - Add tests with small hand-checkable corpora. -
Compare ranking output for representative queries.

Acceptance criteria: - Given a known test corpus, expected ranking order
is verified. - TF-IDF and BM25 are separately selectable for testing. -
Ranking behavior and limitations are documented.

### Module F --- Web Crawler

Responsibilities: - Accept an administrator-supplied seed URL. - Crawl
only approved domains or explicitly allowed URLs. - Respect
`robots.txt`, site terms, rate limits, and a configurable delay. - Set a
descriptive User-Agent. - Limit crawl depth, page count, response size,
and request timeout. - Detect visited/canonical URLs and avoid loops. -
Handle redirects, HTTP errors, malformed pages, and unsupported content
types. - Store crawl status and timestamps. - Extract links only for
discovery; never bypass authentication or access controls.

Safety and operational rules: - Do not crawl private networks,
localhost, internal IP ranges, login-protected pages, or sites that
disallow crawling. - Do not attempt to evade rate limits, CAPTCHAs, bot
protections, or access controls. - Start with a small allowlist and low
request rate. - Provide a manual document-import path so the search
engine can be tested without crawling external sites.

Acceptance criteria: - Crawler can process a small, permitted test
site. - Domain restrictions and depth/page limits are enforced. -
Duplicate URLs are not repeatedly fetched. - Failures are logged and do
not crash the whole job.

### Module G --- FastAPI Backend

Responsibilities: - Coordinate ingestion, indexing, and search. -
Validate inputs and return consistent JSON responses. - Expose API
documentation through FastAPI's OpenAPI support. - Keep business logic
out of route handlers where practical. - Add safe admin-only operations
for managing sources and crawl jobs.

Suggested API surface (final paths may change after design review):

  ------------------------------------------------------------------------------
  Method                  Endpoint                       Purpose
  ----------------------- ------------------------------ -----------------------
  `GET`                   `/api/health`                  Health check

  `GET`                   `/api/search?q=...`            Search indexed
                                                         documents

  `GET`                   `/api/suggestions?q=...`       Autocomplete
                                                         suggestions

  `GET`                   `/api/documents/{id}`          Retrieve document
                                                         metadata

  `POST`                  `/api/admin/sources`           Add an allowed crawl
                                                         source

  `POST`                  `/api/admin/crawl-jobs`        Start a crawl job

  `GET`                   `/api/admin/crawl-jobs/{id}`   Check crawl status

  `GET`                   `/api/admin/analytics`         Retrieve basic
                                                         search/index analytics
  ------------------------------------------------------------------------------

Acceptance criteria: - Request validation and error responses are
consistent. - API tests cover success and failure cases. - Search API
calls the C++ engine through the chosen integration contract. - Admin
endpoints are not left publicly writable without authentication.

### Module H --- PostgreSQL and Redis

PostgreSQL stores durable application data, such as: - Documents and
source metadata. - Crawl jobs and crawl results. - Index
generation/version metadata. - Search query analytics, subject to
privacy-conscious retention.

Redis may store: - Repeated query results. - Short-lived suggestions or
counters. - Temporary job coordination only if justified.

Requirements: - Define schema and migrations. - Add indexes based on
actual query patterns. - Use parameterized queries/ORM safely. - Define
cache key format, TTL, and invalidation behavior. - Cache must never
make stale index results appear indefinitely. - App should degrade
gracefully if Redis is unavailable.

Acceptance criteria: - Database can be initialized from documented
migrations. - CRUD and integration tests pass. - Cache hit/miss behavior
is tested. - No secrets or production credentials are committed.

### Module I --- React Frontend

Pages/components: - Search homepage. - Search input with loading and
error states. - Search results page. - Result card with title, URL,
snippet, and score where appropriate. - Pagination. - Optional filters
and autocomplete. - Admin pages for sources and crawl-job status. -
Basic analytics dashboard.

Requirements: - Responsive and accessible UI. - Clear empty, loading,
and error states. - API calls isolated in a service layer. - No
fake/hardcoded search results in the completed application. - Do not
expose admin operations to unauthorized users.

Acceptance criteria: - Search flow works against the real backend. - UI
handles no results and API errors. - Basic component and integration
tests exist.

### Module J --- Testing, Benchmarking, and Deployment

Testing layers: - C++ unit tests for tokenization, index, retrieval, and
ranking. - Python unit tests for crawler and processing. - FastAPI
integration tests. - React component tests. - End-to-end test for ingest
→ index → search → display. - Security and input-validation checks for
admin/crawler operations.

Benchmarking: - Use a reproducible, documented corpus. - Measure index
build time, query latency, memory use, and throughput. - Record
hardware/software environment and corpus size. - Compare before/after
optimization. - Never invent benchmark numbers.

Deployment: - Dockerize services in a staged manner. - Provide
`.env.example`. - Provide setup, migration, test, and run commands. -
Include health checks and logs. - Document known limitations.

------------------------------------------------------------------------

## 5. High-Level Architecture and Data Flow

### Ingestion and indexing flow

``` text
Admin adds approved source / imports documents
                 |
                 v
        Python Crawler / Importer
                 |
                 v
       HTML and Document Extraction
                 |
                 v
        Text Normalization Pipeline
                 |
                 v
          Canonical Document
                 |
          +------+------+
          |             |
          v             v
      PostgreSQL    C++ Index Engine
      Metadata      Inverted Index
                        |
                        v
                 Ranking Statistics
```

### User search flow

``` text
User
 |
 v
React Search UI
 |
 v
FastAPI Search Endpoint
 |
 v
Query Validation and Normalization
 |
 v
Redis Cache (optional lookup)
 |
 v
C++ Retrieval and Ranking Engine
 |
 v
Document Metadata Lookup
 |
 v
JSON Search Response
 |
 v
React Results UI
```

The exact implementation may evolve, but the contracts between
components must remain explicit and documented.

------------------------------------------------------------------------

## 6. Initial Repository Structure

Use this as a target structure, not a reason to create every file
immediately. Create directories only when their module is being
implemented.

``` text
SearchX/
├── PROJECT_CONTEXT.md
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── docs/
│   └── decisions/
│
├── core-engine/
│   ├── CMakeLists.txt
│   ├── include/
│   ├── src/
│   └── tests/
│
├── crawler/
│   ├── app/
│   ├── tests/
│   └── requirements.txt
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   └── db/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   └── package.json
│
├── scripts/
└── benchmarks/
```

Do not create empty placeholder files for every future module. Build the
structure incrementally.

------------------------------------------------------------------------

## 7. Development Order and Milestones

Follow this sequence unless a dependency requires a documented
adjustment.

  -----------------------------------------------------------------------
  Milestone               Work                    Definition of done
  ----------------------- ----------------------- -----------------------
  0                       Inspect environment and Toolchain checked;
                          initialize repository   repository and
                                                  conventions agreed

  1                       Document model and text Shared document
                          normalization           contract and
                                                  normalization tests

  2                       C++ inverted index      Build index and
                                                  retrieve correct
                                                  document IDs

  3                       Query processing and    AND/OR query behavior
                          Boolean retrieval       tested

  4                       TF-IDF and BM25 ranking Ranking tests pass on a
                                                  small corpus

  5                       Index persistence       Index can be saved,
                                                  loaded, and validated

  6                       Python document         Permitted sample
                          importer and controlled pages/documents
                          crawler                 ingested

  7                       FastAPI integration     Search API calls the
                                                  real C++ engine

  8                       PostgreSQL persistence  Metadata and crawl
                                                  state persist

  9                       React search UI         End-to-end user search
                                                  works

  10                      Redis cache and admin   Cache and admin flows
                          features                tested

  11                      Performance and         Benchmarks, profiling,
                          reliability             failure tests
                                                  documented

  12                      Docker and final        Reproducible setup and
                          documentation           complete README
  -----------------------------------------------------------------------

**Important:** Do not begin with the React UI. Prove that the core
search engine works first.

------------------------------------------------------------------------

## 8. Rules for the AI Coding Agent

These rules apply to every task in this repository.

### Before coding

1.  Read this file and inspect the current repository.
2.  Identify the exact module requested by the user.
3.  Summarize the current implementation relevant to that module.
4.  Explain the proposed files, interfaces, dependencies, and data flow.
5.  Identify risks and test cases.
6.  Wait for user approval before making substantial code changes.

### While coding

1.  Implement only the assigned module and necessary integration points.
2.  Follow the agreed stack and architecture.
3.  Prefer small, readable, maintainable changes.
4.  Do not rewrite unrelated files or modules.
5.  Do not add dependencies without explaining why.
6.  Do not hardcode sample results as if they were real functionality.
7.  Do not claim tests passed unless they were actually run.
8.  Do not claim a feature is complete if it is only a stub.
9.  Keep secrets in environment variables; never commit credentials.
10. Explain important code in beginner-friendly language.

### After coding

1.  Run relevant formatting, build, and test commands.
2.  Report exactly what was changed.
3.  Report tests run and their actual results.
4.  Explain how to run or manually verify the feature.
5.  List known limitations and next steps.
6.  Update this `PROJECT_CONTEXT.md` to reflect the actual codebase.
7.  Update the module status table below.
8.  Show the user the documentation changes made.

### Module boundaries

-   Do not start another module unless the user asks.
-   Do not silently change public interfaces. If a change is needed,
    explain it and update all affected callers and tests.
-   Keep API schemas and C++/Python integration contracts synchronized.
-   Prefer a small working vertical slice over many incomplete modules.

### Git discipline

-   Recommend a Git commit after a verified milestone.
-   Never run destructive Git commands (such as hard reset, force push,
    or deleting branches) without explicit user approval.
-   Do not overwrite user work.
-   Keep commits small and descriptive.

------------------------------------------------------------------------

## 9. Module Status Tracker

Update this table after each verified milestone. Do not mark a module
complete merely because files were generated.

  Module                                  Status        Notes
  --------------------------------------- ------------- -------
  Project foundation                      Verified      Repository initialized on branch main, .gitignore, README.md, docs/decisions configured and verified
  Document model and ingestion contract   Verified      Canonical Document & Token models with SHA-256 deduplication and C++ struct consistency; tests passing
  Text processing                         Verified      HTML text extraction, Unicode NFKC normalization, positional tokenization, and query tokenizer; tests passing
  C++ inverted index                      Verified      InvertedIndex implemented with term dictionary, positional postings, duplicate rejection, Boolean AND/OR lookup, and corpus statistics; all CTest unit tests passing
  Query processing                        Verified      Boolean AND/OR query candidate retrieval implemented and verified in C++ Ranker
  TF-IDF ranking                          Verified      Sublinear TF and smooth IDF formula verified against hand-calculated test corpus
  BM25 ranking                            Verified      Okapi BM25 scoring with configurable k1, b parameters, length normalization, and deterministic tie-breaking verified
  Index persistence                       Verified      Binary serialization and deserialization with header/footer verification, integrity checks, and error rollback; all CTest unit tests passing
  Python crawler/importer                 Not started   
  FastAPI backend                         Not started   
  PostgreSQL                              Not started   
  Redis cache                             Not started   
  React frontend                          Not started   
  Admin dashboard                         Not started   
  Testing and benchmarks                  Not started   
  Docker and deployment                   Not started   

Allowed statuses: `Not started`, `In progress`, `Implemented`,
`Verified`, `Blocked`.

Use `Verified` only when the relevant tests or manual checks have
actually passed.

------------------------------------------------------------------------

## 10. Technical Decisions Log

Record important decisions here, including date, decision, reason, and
affected modules.

  --------------------------------------------------------------------------
  Date              Decision             Reason            Affected modules
  ----------------- -------------------- ----------------- -----------------
  Initial           C++ owns the custom  Demonstrates data Core engine
                    retrieval/indexing   structures and    
                    core                 algorithm         
                                         implementation    

  Initial           Python handles       Suitable          Crawler, backend
                    crawling and API     ecosystem for     
                    orchestration        HTTP, parsing,    
                                         and FastAPI       

  Initial           PostgreSQL is the    Reliable          Backend, database
                    durable metadata     relational        
                    store                persistence       

  Initial           Redis is optional    Performance       Backend, cache
                    cache only           optimization      
                                         without becoming  
                                         source of truth   

  Initial           Start with a         Keeps scope       All
                    controlled corpus    achievable and    
                    and single-machine   testable          
                    design                                 
  --------------------------------------------------------------------------

Do not change these decisions silently. Propose alternatives and get
user approval before major architectural changes.

------------------------------------------------------------------------

## 11. Definition of Project Completion

SearchX Version 1 is complete only when:

-   A user can search a real, ingested document corpus through the React
    UI.
-   Documents can be imported and/or crawled from permitted sources.
-   Text processing and indexing work end to end.
-   The custom C++ inverted index is used for retrieval.
-   TF-IDF and BM25 ranking are implemented and tested.
-   Document metadata persists across application restarts.
-   Search API returns real results, not mock data.
-   Error cases are handled.
-   Unit and integration tests are documented and pass.
-   A reproducible setup and run guide exists.
-   The student can explain the architecture, algorithms, trade-offs,
    limitations, and measured performance.

------------------------------------------------------------------------

## 12. First Task for the AI Agent

When this file is first opened in the coding environment:

**Do not start implementing the whole project.**

First:

1.  Read this complete document.
2.  Inspect the available development environment (C++ compiler, CMake,
    Python, Node.js, Git, Docker).
3.  Inspect the repository, if one already exists. Do not overwrite
    existing work.
4.  Explain the project in simple language and summarize the
    architecture.
5.  Propose the initial repository setup and the first milestone only.
6.  Identify any missing tools or setup steps.
7.  Wait for the user's approval before creating or modifying project
    files.

The first implementation milestone, after approval, is **Project
Foundation + Document Model + Text Normalization**. Then proceed to the
C++ inverted index.

------------------------------------------------------------------------

**End of SearchX Project Context --- Version 1.0**

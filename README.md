# SearchX

SearchX is an educational, industry-inspired document search engine built to demonstrate core information-retrieval concepts from first principles: web crawling and document ingestion, text normalization, custom C++ inverted index construction, Boolean query retrieval, TF-IDF and BM25 relevance ranking, and interactive web presentation.

---

## Architecture Overview

```text
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
                 Ranking Statistics (TF-IDF & BM25)
```

### Search Flow

```text
User  --->  React UI  --->  FastAPI Backend  --->  Redis Cache (optional)
                                    |
                                    v
                           C++ Retrieval Engine
                                    |
                                    v
                             Ranked Results
```

---

## Technology Stack

- **Core Engine:** C++ (C++17 or newer) — Inverted index, posting lists, Boolean query processor, TF-IDF and BM25 ranking.
- **Crawler & Ingestion:** Python 3 — HTML parsing, text extraction, URL canonicalization, and crawl politeness (`robots.txt`, rate limits).
- **Backend API:** Python + FastAPI — REST endpoints, query validation, and orchestration.
- **Frontend:** React — Search interface, autocomplete suggestions, result snippets, and admin monitoring.
- **Database:** PostgreSQL — Durable storage for document metadata, crawl jobs, and analytics.
- **Cache:** Redis — Ephemeral query caching with strict invalidation (optional degradation).
- **Build System:** CMake + Ninja for C++.

---

## Repository Structure

```text
SearchX/
├── PROJECT_CONTEXT.md          # Single source of truth for planning, architecture & status
├── README.md                   # Project overview and setup instructions
├── .gitignore                  # Multi-stack gitignore rules
├── docs/                       # Architectural decisions and design documentation
│   └── decisions/              # Architecture Decision Records (ADRs)
├── core-engine/                # C++ inverted index and ranking engine (Milestone 2+)
├── crawler/                    # Python crawler and document importer (Milestone 6)
├── backend/                    # FastAPI orchestration service (Milestone 7)
└── frontend/                   # React search user interface (Milestone 9)
```

---

## Development Prerequisites

- **C++ Compiler:** Modern GCC / MinGW-w64 (UCRT) supporting C++17 or newer.
- **Build Tool:** CMake 3.20+ and Ninja.
- **Python:** Python 3.10+ with `pip`.
- **Node.js:** Node.js v18+ with `npm`.
- **Git:** Git 2.x+.

---

## Project Context & Single Source of Truth

For detailed requirements, milestone definitions, architecture boundaries, and the module tracker, refer to [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md).

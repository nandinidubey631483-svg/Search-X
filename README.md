# SearchX

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-passing-brightgreen?logo=github-actions)](.github/workflows/ci.yml)
[![CodeQL Security](https://img.shields.io/badge/CodeQL-passing-brightgreen?logo=github)](.github/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![C++](https://img.shields.io/badge/C%2B%2B-17-blue?logo=c%2B%2B)](core-engine/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python)](backend/)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](frontend/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker)](docker-compose.yml)

SearchX is an educational, industry-inspired document search engine built to demonstrate core information-retrieval concepts from first principles: web crawling and document ingestion, text normalization, custom C++ inverted index construction, Boolean query retrieval, TF-IDF and BM25 relevance ranking, Redis caching, PostgreSQL persistence, and a modern, high-performance web interface.

---

## Architecture Overview

```text
       [ Admin / Seed Sources / Web Crawler ]
                         |
                         v
       [ Python Crawler & Ingestion Pipeline ]
       - Domain Allowlisting & SSRF DNS Guard
       - Robots.txt Politeness & Depth Bounds
                         |
                         v
       [ HTML Parsing & Text Normalization ]
       - Unicode NFKC Normalization & Lowercasing
       - Positional Tokenization & Term Offsets
                         |
           +-------------+-------------+
           |                           |
           v                           v
  [ PostgreSQL 16 ]            [ C++ Core Engine ]
  - Document Metadata          - Positional Inverted Index
  - Crawl Job Logs             - Binary Index File (.bin)
  - Query Analytics            - Okapi BM25 & TF-IDF Scoring
           |                           |
           +-------------+-------------+
                         |
                         v
              [ FastAPI Backend API ]
              - Query Orchestration & Validation
              - Subprocess CLI Bridge to C++ Core
              - Redis Query & Suggestion Cache (5m TTL)
                         ^
                         | (JSON REST API via Reverse Proxy)
                         v
                 [ Nginx Alpine ]
                         ^
                         | (HTTP / Port 3000)
                         v
             [ React 18 + Vite Frontend ]
             - Search Hero & Live Autocomplete
             - Category Views (Web, Images, Docs, News, Scholar)
             - Lightbox Media Viewer & Dynamic Ambient Canvas
             - Full Admin Control Center
```

---

## Technology Stack

| Layer | Technology | Key Capabilities |
| :--- | :--- | :--- |
| **Core Retrieval Engine** | **C++ (C++17)** | Inverted index, positional posting lists, Boolean query processor (AND/OR), TF-IDF, Okapi BM25 scoring, binary serialization. |
| **Crawler & Ingestion** | **Python 3.12** | Controlled crawler, DNS-resolved SSRF guard, canonicalization, HTML text extraction, Unicode NFKC tokenization. |
| **Backend Service** | **FastAPI + Uvicorn** | High-performance asynchronous REST API, request validation, C++ CLI orchestration, admin endpoints. |
| **Query Cache** | **Redis 7** | Sub-millisecond query result caching, prefix suggestion caching, automatic TTL expiration, write-through invalidation. |
| **Primary Database** | **PostgreSQL 16** | Durable document catalog, crawl job execution history, atomic search query counter analytics. |
| **Frontend UI** | **React 18 + Vite** | Modern responsive interface, Lucide SVG iconography, hardware-accelerated ambient animations, image lightbox. |
| **Web Server / Proxy** | **Nginx Alpine** | Gzip static compression, SPA client routing fallback, `/api/` reverse proxy. |
| **Containerization** | **Docker & Compose** | Multi-stage production builds, non-root security execution, container healthchecks. |

---

## Quick Start with Docker Compose

The simplest way to build, seed, and run the entire production SearchX stack is with Docker Compose.

### 1. Clone & Configure Environment

```bash
git clone https://github.com/your-username/Searchx.git
cd Searchx
cp .env.example .env
```

### 2. Launch All Services

```bash
docker compose up --build -d
```

This automatically orchestrates:
- **`postgres`** on port `5432` with healthchecks and persistent volume `searchx_postgres_data`.
- **`redis`** on port `6379` with healthchecks and persistent volume `searchx_redis_data`.
- **`backend`** on port `8000` (compiling the C++ engine in Stage 1 and launching FastAPI in Stage 2).
- **`frontend`** on port `3000` (building React assets with Vite and serving via Nginx).

### 3. Access the Application

- **Web Search UI:** [http://localhost:3000](http://localhost:3000)
- **Admin Dashboard:** [http://localhost:3000](http://localhost:3000) (Click **Admin Dashboard** in top navigation)
- **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Healthcheck:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## Local Development Setup

If developing without Docker, you can run each service natively on your machine:

### Prerequisites

- **C++ Compiler:** GCC/MinGW-w64 or Clang supporting C++17.
- **CMake & Ninja:** CMake 3.20+ and Ninja build system.
- **Python:** Python 3.10+ with `pip`.
- **Node.js:** Node.js v18+ with `npm`.

### 1. Build the C++ Core Retrieval Engine

```bash
cd core-engine
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
ctest --test-dir build --output-on-failure
cd ..
```

### 2. Set Up the Python Backend

```bash
# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Seed Document Corpus & Build Initial Index

```bash
# Ingest educational documents into SQLite and C++ binary inverted index
python scripts/seed_corpus.py
```

### 4. Start the FastAPI Backend Server

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Start the React Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status, C++ engine binary connectivity, and document count. |
| `GET` | `/api/search` | Search query endpoint with `q`, `mode` (`bm25` or `tfidf`), `op` (`AND` or `OR`), `page`, and `page_size`. |
| `GET` | `/api/suggestions` | Prefix term autocomplete recommendations (`q` query string). |
| `GET` | `/api/documents/{doc_id}` | Retrieve complete document details, metadata, and full text body. |
| `GET` | `/api/admin/sources` | List approved crawl domains (requires `X-Admin-Key` header). |
| `POST` | `/api/admin/sources` | Add new domain to the crawler allowlist. |
| `POST` | `/api/admin/crawl` | Trigger controlled background crawl job with depth and page constraints. |
| `GET` | `/api/admin/analytics` | Search volume, top queries, and Redis cache hit/miss performance metrics. |

---

## Search Features & Capabilities

- **BM25 & TF-IDF Relevance:** Configurable ranking model with length normalization and smooth inverse document frequency.
- **Typo-Tolerance & "Did You Mean?" Engine:** Damerau-Levenshtein edit-distance ($\le 2$) with corpus document frequency weighting, automatic zero-hit fallback search, and interactive suggestion banners.
- **Boolean Precision:** Supports strict `AND` intersection for exact matching or `OR` union for high recall.
- **Positional Snippet Extraction:** Dynamically extracts the most relevant text excerpt highlighting queried terms.
- **Category Navigation Directory:** Explore indexed resources across **Web**, **Images**, **Documents**, **News**, and **Scholar**.
- **Visual Media Lightbox:** High-resolution technical schematics and image inspection with full-screen zoom, metadata, and asset download.
- **Ambient Canvas:** Hardware-accelerated 60fps CSS aurora mesh orbs, rotating ambient rays, and drifting tech matrix grid.
- **Production Redis Caching:** 5-minute TTL query cache with instantaneous cache-hit response times (<1.5ms).

---

## Running Test Suites

SearchX enforces comprehensive test coverage across every component:

```bash
# 1. Run C++ Engine Unit Tests (Document, Inverted Index, BM25/TF-IDF, Binary Serialization)
ctest --test-dir core-engine/build --output-on-failure

# 2. Run Python Backend & Crawler Tests (65 test cases)
pytest backend/tests crawler/tests -v

# 3. Run React Frontend Unit Tests (16 test suites)
npm --prefix frontend test

# 4. Verify Frontend Production Build
npm --prefix frontend run build
```

---

## Continuous Integration & Security Analysis

SearchX includes a production multi-platform CI/CD and CodeQL security suite configured in [`.github/workflows/`](.github/workflows/):

- **Cross-Platform C++ Matrix**: Compiles the C++17 core engine and runs CTest verification suites across both `ubuntu-latest` and `windows-latest`.
- **Python Backend & Crawler Tests**: Runs 57 Pytest test cases across Python 3.11 and 3.12 on Linux & Windows environments.
- **Frontend Verification**: Tests all 15 Vitest suites and compiles optimized production Vite assets.
- **Docker Compose & Multi-Stage Image Builds**: Validates `docker compose config`, `backend/Dockerfile` multi-stage build, and `frontend/Dockerfile` Nginx bundle.
- **CodeQL Security Scanning**: Automated semantic code analysis for C++, Python, and JavaScript detecting memory bugs, buffer overflows, and SSRF flaws.

---

## License

Educational and research project developed under the MIT License.

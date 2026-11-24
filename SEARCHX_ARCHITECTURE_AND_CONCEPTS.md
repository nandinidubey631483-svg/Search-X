# SearchX: Architecture, Core Concepts & Data Structures Guide

This document serves as an exhaustive technical guide to **SearchX**. It explains every core concept, data structure, mathematical formula, algorithmic decision, and architectural boundary implemented across the entire system — from C++ low-level memory layout to the React frontend.

---

## Table of Contents

1. [High-Level Architecture & System Topology](#1-high-level-architecture--system-topology)
2. [C++ Retrieval Core: Inverted Index & Memory Layout](#2-c-retrieval-core-inverted-index--memory-layout)
   - [What is an Inverted Index?](#what-is-an-inverted-index)
   - [Data Structures Used & Algorithmic Complexities](#data-structures-used--algorithmic-complexities)
   - [Positional Indexing & Memory Optimization](#positional-indexing--memory-optimization)
   - [Fast Document Removal & Deduplication](#fast-document-removal--deduplication)
3. [Relevance Ranking & Scoring Mathematics](#3-relevance-ranking--scoring-mathematics)
   - [Boolean Query Matching (AND / OR)](#boolean-query-matching-and--or)
   - [TF-IDF (Term Frequency – Inverse Document Frequency)](#tf-idf-term-frequency--inverse-document-frequency)
   - [Okapi BM25 Ranking](#okapi-bm25-ranking)
   - [Deterministic Tie-Breaking](#deterministic-tie-breaking)
4. [Binary Serialization & Persistence Protocol](#4-binary-serialization--persistence-protocol)
5. [Crawler, Parser & Security Pipeline](#5-crawler-parser--security-pipeline)
   - [SSRF (Server-Side Request Forgery) Defense](#ssrf-server-side-request-forgery-defense)
   - [Domain Allowlisting & Politeness Engine](#domain-allowlisting--politeness-engine)
   - [Unicode Normalization & Positional Tokenizer](#unicode-normalization--positional-tokenizer)
6. [Spell Checking & Query Correction](#6-spell-checking--query-correction)
   - [Damerau-Levenshtein Distance](#damerau-levenshtein-distance)
   - [Vocabulary-Weighted Candidate Ranking](#vocabulary-weighted-candidate-ranking)
7. [Caching & Performance Layer (Redis)](#7-caching--performance-layer-redis)
8. [Relational Data Catalog (PostgreSQL / SQLite)](#8-relational-data-catalog-postgresql--sqlite)
9. [IPC Bridge: Python FastAPI to C++ Engine](#9-ipc-bridge-python-fastapi-to-c-engine)
10. [Frontend & Secure Authentication Architecture](#10-frontend--secure-authentication-architecture)
11. [Concept Cross-Reference Matrix](#11-concept-cross-reference-matrix)
12. [Complete Repository Structure & File-by-File Breakdown](#12-complete-repository-structure--file-by-file-breakdown)
    - [Project Directory Tree](#project-directory-tree)
    - [Core Retrieval Engine (`core-engine/`)](#core-retrieval-engine-core-engine)
    - [FastAPI Backend Service (`backend/`)](#fastapi-backend-service-backend)
    - [Web Crawler & Ingestion Pipeline (`crawler/`)](#web-crawler--ingestion-pipeline-crawler)
    - [React Frontend Application (`frontend/`)](#react-frontend-application-frontend)
    - [Automation & Deployment Scripts (`scripts/`)](#automation--deployment-scripts-scripts)
    - [Root Infrastructure & Configuration Files](#root-infrastructure--configuration-files)


---

## 1. High-Level Architecture & System Topology

SearchX decouples heavy computation, persistent storage, and interactive presentation into discrete layers:

```mermaid
flowchart TD
    subgraph UI ["Client Layer (Browser)"]
        ReactApp["React 18 + Vite (SPA)"]
        PublicSearch["Public Search & Autocomplete"]
        AdminDashboard["Admin Control Center (In-Memory Key)"]
    end

    subgraph BackendGateway ["API & Orchestration Layer (Python)"]
        FastAPI["FastAPI REST Service"]
        SearchSvc["Search Service Coordinator"]
        CrawlerSvc["Crawler Service & Dispatcher"]
        SpellChecker["Spell Checker (Damerau-Levenshtein)"]
    end

    subgraph CacheDB ["Persistence & Caching"]
        RedisCache[("Redis 7: LRU Query Cache (300s TTL)")]
        PostgresDB[("PostgreSQL 16: Catalog, Jobs & Query Counts")]
    end

    subgraph CoreEngine ["High-Performance Retrieval Core (C++17)"]
        CPPEngine["searchx_engine CLI Executable"]
        InvertedIndex["Positional Inverted Index (In-Memory)"]
        Ranker["Relevance Ranker (BM25 / TF-IDF)"]
        BinaryDisk[("Binary Index Segment (.bin)")]
    end

    ReactApp -->|HTTP REST / JSON| FastAPI
    FastAPI --> SearchSvc
    FastAPI --> CrawlerSvc
    SearchSvc --> RedisCache
    SearchSvc --> SpellChecker
    SearchSvc -->|CLI Subprocess IPC| CPPEngine
    CrawlerSvc --> PostgresDB
    SearchSvc --> PostgresDB
    CPPEngine --> InvertedIndex
    InvertedIndex --> Ranker
    InvertedIndex <-->|Binary Serialization| BinaryDisk
```

---

## 2. C++ Retrieval Core: Inverted Index & Memory Layout

The retrieval engine is implemented in standard C++17 located in `core-engine/`. It delivers sub-millisecond document lookups and scoring without garbage collection pauses.

### What is an Inverted Index?

In a conventional database, documents are mapped to their text (**Forward Index**):
```text
Document 1 -> ["information", "retrieval", "basics"]
Document 2 -> ["probabilistic", "retrieval", "bm25"]
```
To find which documents contain `"retrieval"`, a forward index requires scanning every document: $O(N \times L)$ time complexity ($N$ documents, length $L$).

An **Inverted Index** reverses this mapping by indexing each distinct **term** to the list of documents where it appears (the **Posting List**):
```text
"basics"        -> [ Doc 1 ]
"bm25"          -> [ Doc 2 ]
"information"   -> [ Doc 1 ]
"probabilistic" -> [ Doc 2 ]
"retrieval"     -> [ Doc 1, Doc 2 ]
```
With an inverted index, searching for `"retrieval"` is an $O(1)$ dictionary lookup plus traversal of the matched postings list.

---

### Data Structures Used & Algorithmic Complexities

The `searchx::InvertedIndex` class (`core-engine/include/inverted_index.hpp`) uses specialized standard data structures selected for algorithmic efficiency and hardware cache locality:

| Component | Concrete C++ Data Structure | Purpose | Time Complexity | Space Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Term Dictionary** | `std::unordered_map<std::string, std::vector<Posting>>` | Maps vocabulary term strings to their postings list. | $O(1)$ average lookup, $O(L)$ worst-case ($L$ = term length). | $O(V)$ where $V$ is vocabulary size. |
| **Posting List** | `std::vector<Posting>` | Contiguous dynamic array holding document appearances for a term. | Sequential iteration $O(P)$, append $O(1)$ amortized. | $O(P)$ contiguous elements. |
| **Document Catalog** | `std::unordered_map<uint32_t, Document>` | Fast retrieval of document metadata using internal integer IDs. | Lookup $O(1)$, Insert $O(1)$, Delete $O(1)$. | $O(N)$ where $N$ is document count. |
| **ID Resolvers** | `std::unordered_map<std::string, uint32_t>` | Bi-directional translation between string ID (e.g. `"doc_ir_1"`) and internal 32-bit `doc_id`. | Lookup $O(1)$ average. | $O(N)$ |
| **Deduplication Map** | `std::unordered_map<std::string, uint32_t>` | Maps SHA-256 content hash to existing `doc_id` to block duplicate ingestion. | Lookup $O(1)$ average. | $O(N)$ |
| **Document Lengths** | `std::unordered_map<uint32_t, uint32_t>` | Stores token count for each document for BM25 length normalization. | Lookup $O(1)$. | $O(N)$ |
| **Document Terms** | `std::unordered_map<uint32_t, std::unordered_set<std::string>>` | Tracks distinct terms present in each document for fast document deletion. | Lookup $O(1)$. | $O(\sum \text{unique terms per doc})$ |

#### Why `std::vector<Posting>` instead of `std::list`?
- **Cache Locality**: A linked list (`std::list`) allocates each node independently on the heap, causing CPU cache misses when traversing postings. A dynamic array (`std::vector`) is contiguous in virtual memory; pre-fetching hardware pulls multiple postings directly into the CPU L1/L2 cache lines.
- **Space Overhead**: `std::list` incurs a 16-byte pointer overhead (forward and backward pointers on 64-bit systems) for *every* posting. `std::vector` has zero per-element pointer overhead.

---

### Positional Indexing & Memory Optimization

Every posting in SearchX is a `searchx::Posting`:
```cpp
struct Posting {
    uint32_t doc_id = 0;              // 4 bytes: internal document identifier
    uint32_t term_frequency = 0;       // 4 bytes: number of occurrences in this doc
    std::vector<uint32_t> positions;   // Token offset positions (0-indexed)
};
```

**Why keep `positions`?**
1. **Phrase Searches**: Enables verifying whether `"information"` and `"retrieval"` appear adjacently (`pos("retrieval") == pos("information") + 1`).
2. **Proximity Scoring**: Enables boosting documents where query terms appear close together.
3. **Snippet Generation**: Allows fast localization of matched terms in large text bodies without re-scanning raw strings.

---

### Fast Document Removal & Deduplication

Inverted index removal is notoriously expensive in naive implementations because finding which postings lists contain a deleted document requires traversing the entire vocabulary: $O(V \times P)$.

SearchX solves this by maintaining a reverse document-to-terms index:
```cpp
std::unordered_map<uint32_t, std::unordered_set<std::string>> doc_terms_;
```
When `remove_document(string_doc_id)` is invoked:
1. It looks up `doc_id` in $O(1)$.
2. It retrieves the exact set of terms that document contained ($T_{doc}$).
3. It visits **only** those specific postings lists in `dictionary_` and deletes the matching `doc_id` using the C++ erase-remove idiom:
   ```cpp
   postings.erase(
       std::remove_if(postings.begin(), postings.end(),
                      [doc_id](const Posting& p) { return p.doc_id == doc_id; }),
       postings.end()
   );
   ```
4. If a postings list becomes empty, the term is pruned from `dictionary_`.
5. Running corpus statistics (`total_corpus_tokens_`, `doc_lengths_`) are updated in $O(1)$.

---

## 3. Relevance Ranking & Scoring Mathematics

SearchX provides two classic Information Retrieval ranking algorithms implemented in `core-engine/src/ranking.cpp`: **TF-IDF** and **Okapi BM25**.

### Boolean Query Matching (AND / OR)

Candidate document selection occurs before scoring:

1. **MatchMode::ANY_TERM (Boolean OR)**:
   - Takes the union of candidate document IDs across all query terms.
   - Any document containing at least one term is scored.
2. **MatchMode::ALL_TERMS (Boolean AND)**:
   - Computes the strict set intersection across all query terms.
   - Only documents containing *all* query terms proceed to ranking.
   - Implemented via sorted two-pointer intersection:
     ```cpp
     // Two sorted postings lists P1 and P2 can be intersected in O(|P1| + |P2|)
     while (it1 != p1.end() && it2 != p2.end()) {
         if (it1->doc_id == it2->doc_id) {
             result.push_back(it1->doc_id);
             ++it1; ++it2;
         } else if (it1->doc_id < it2->doc_id) {
             ++it1;
         } else {
             ++it2;
         }
     }
     ```

---

### TF-IDF (Term Frequency – Inverse Document Frequency)

TF-IDF measures how important a word is to a document in a collection.

#### 1. Term Frequency (Logarithmic Sub-linear Scaling)
Raw term frequency ($\text{tf}$) can bias long documents containing repeated words. SearchX uses sub-linear logarithmic dampening:
$$\text{TF}(t, d) = \begin{cases} 1 + \ln(\text{tf}(t, d)) & \text{if } \text{tf}(t, d) > 0 \\ 0 & \text{otherwise} \end{cases}$$
*Intuition: A document with 10 occurrences of a word is more relevant than one with 1 occurrence, but not 10 times more relevant.*

#### 2. Inverse Document Frequency (Smoothed IDF)
Words that appear across almost all documents (e.g. "the", "is") carry little discriminatory power.
$$\text{IDF}(t) = \ln\left(1.0 + \frac{N}{\text{df}(t)}\right)$$
- $N$: Total number of documents in corpus.
- $\text{df}(t)$: Document frequency (number of documents containing term $t$).
- The $+1.0$ smoothing prevents division by zero and ensures non-negative scores.

#### 3. Total TF-IDF Score
$$\text{Score}_{\text{TF-IDF}}(d, Q) = \sum_{t \in Q} \text{TF}(t, d) \times \text{IDF}(t)$$

---

### Okapi BM25 Ranking

Okapi BM25 is a non-linear probabilistic ranking function that improves upon TF-IDF by addressing **term frequency saturation** and **document length normalization**.

$$\text{Score}_{\text{BM25}}(d, Q) = \sum_{t \in Q} \text{IDF}_{\text{BM25}}(t) \times \frac{\text{tf}(t, d) \cdot (k_1 + 1)}{\text{tf}(t, d) + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{\text{avgdl}}\right)}$$

```text
       Score Contribution
              ^
              |               /--- (TF-IDF: unbounded linear/log growth)
              |             /
              |      .-----+------ (BM25: asymptote at (k1 + 1))
              |    /
              |  /
              +-----------------------------> Term Frequency (tf)
```

#### Breakdown of Terms:

1. **BM25 Probabilistic IDF**:
   $$\text{IDF}_{\text{BM25}}(t) = \ln\left(\frac{N - \text{df}(t) + 0.5}{\text{df}(t) + 0.5} + 1.0\right)$$
   Standard Robertson-Spärck Jones IDF formula with $+1.0$ floor to guarantee non-negative weights for common terms.

2. **Term Frequency Saturation ($k_1 = 1.2$)**:
   - In TF-IDF, a document repeating a term 100 times continues to accumulate score.
   - In BM25, as $\text{tf} \to \infty$, the TF component asymptotes to $(k_1 + 1) = 2.2$. Extra repetitions produce diminishing returns.

3. **Document Length Normalization ($b = 0.75$)**:
   - $\frac{|d|}{\text{avgdl}}$: Ratio of document length to the average document length across the entire corpus.
   - When $|d| > \text{avgdl}$, the denominator increases, penalizing verbose documents.
   - When $|d| < \text{avgdl}$, short concise documents receive a relative boost.
   - $b = 0.75$ balances length penalization against topic breadth.

---

### Deterministic Tie-Breaking

To avoid non-deterministic result ordering across multiple identical scores:
```cpp
struct ScoredResult {
    uint32_t doc_id;
    std::string string_doc_id;
    double score;

    bool operator<(const ScoredResult& other) const {
        constexpr double EPS = 1e-9;
        if (std::abs(score - other.score) > EPS) {
            return score > other.score; // Higher scores first
        }
        return doc_id < other.doc_id;   // Stable tie-breaker: lower doc_id first
    }
};
```

---

## 4. Binary Serialization & Persistence Protocol

To eliminate slow re-indexing on application restarts, SearchX implements a zero-overhead binary persistence protocol in `core-engine/src/index_serializer.cpp`.

### Binary Wire Format Specification

```text
+-----------------------+------------------------------------------------------+
| Field                 | Type / Length                                        |
+-----------------------+------------------------------------------------------+
| MAGIC_HEADER          | 12 bytes: "SEARCHX_IDX\x01"                          |
| Format Version        | uint32_t (4 bytes)                                   |
| Total Documents (N)   | uint64_t (8 bytes)                                   |
| Total Corpus Tokens   | uint64_t (8 bytes)                                   |
| Next Doc ID Counter   | uint32_t (4 bytes)                                   |
+-----------------------+------------------------------------------------------+
| Document Table:       | Repeated N times:                                    |
|   - doc_id            |   uint32_t                                           |
|   - string_doc_id     |   uint32_t length + UTF-8 bytes                      |
|   - url               |   uint32_t length + UTF-8 bytes                      |
|   - title             |   uint32_t length + UTF-8 bytes                      |
|   - content_hash      |   uint32_t length + UTF-8 bytes                      |
|   - fetched_at        |   uint32_t length + UTF-8 bytes                      |
|   - status            |   uint32_t length + UTF-8 bytes                      |
|   - token_count       |   uint32_t                                           |
+-----------------------+------------------------------------------------------+
| Vocabulary Size (V)   | uint64_t (8 bytes)                                   |
+-----------------------+------------------------------------------------------+
| Inverted Dictionary:  | Repeated V times:                                    |
|   - Term String       |   uint32_t length + UTF-8 bytes                      |
|   - Postings Count (P)|   uint32_t                                           |
|   - Postings List     |   Repeated P times:                                  |
|       - doc_id        |     uint32_t                                         |
|       - tf            |     uint32_t                                         |
|       - pos_count (K) |     uint32_t                                         |
|       - positions     |     K x uint32_t contiguous array                    |
+-----------------------+------------------------------------------------------+
| MAGIC_FOOTER          | 11 bytes: "SEARCHX_END"                              |
+-----------------------+------------------------------------------------------+
```

### Defensive Deserialization Guards

To prevent crashes from corrupted or malicious `.bin` files:
1. **Magic Header & Footer Check**: Verifies file integrity before and after parsing.
2. **Allocation Bounds Guard**:
   - `MAX_DOC_COUNT = 10,000,000`
   - `MAX_VOCAB_SIZE = 10,000,000`
   - `MAX_POSTINGS_PER_TERM = 10,000,000`
   - `MAX_POSITIONS_PER_POSTING = 1,000,000`
   - `MAX_STRING_LEN = 52,428,800` (50 MB)
3. **Transaction State Preservation**: If deserialization fails halfway (e.g. truncated file), the original index state is preserved rather than left partially corrupted.

---

## 5. Crawler, Parser & Security Pipeline

Located in `crawler/app/`, the crawler extracts text and outbound links while enforcing strict enterprise security controls.

### SSRF (Server-Side Request Forgery) Defense

The crawler implements a custom DNS-resolving security guard (`crawler/app/crawler.py`). Before fetching any HTTP target, it performs pre-request DNS resolution to verify that the destination IP does not belong to private, loopback, or cloud-metadata network spaces:

```python
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback IPv4
    ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),   # Link-Local / AWS Metadata (169.254.169.254)
    ipaddress.ip_network("::1/128"),          # Loopback IPv6
    ipaddress.ip_network("fc00::/7"),         # Unique Local IPv6
]
```

### Domain Allowlisting & Politeness Engine

- **Strict Whitelist**: Crawling only fetches pages whose domain is explicitly permitted in `admin_sources`.
- **`robots.txt` Compliance**: Automatically parses and honors `User-agent: *` `Disallow:` directives using Python's `urllib.robotparser`.
- **Bounded Ingestion**: Enforces strict `max_depth` (BFS tree depth) and `max_pages` limits to prevent crawler trap loops.

---

### Unicode Normalization & Positional Tokenizer

Implemented in `crawler/app/tokenization.py`:

```mermaid
flowchart LR
    RawHTML["Raw HTML Text"] --> Unescape["HTML Entity Unescaping"]
    Unescape --> NFKC["Unicode NFKC Normalization"]
    NFKC --> Lower["Lowercasing & Accent Stripping"]
    Lower --> Regex["Positional Regex Tokenizer"]
    Regex --> CleanTokens["List of Token(term, position, start, end)"]
```

1. **NFKC (Compatibility Decomposition + Canonical Composition)**:
   - Resolves stylistic ligatures: `"ﬁ"` $\to$ `"fi"`.
   - Normalizes full-width characters: `"Ｆｕｌｌ"` $\to$ `"Full"`.
2. **Positional Character Offsets**:
   - Captures `(char_start, char_end)` to enable snippet highlighting directly against original document HTML.

---

## 6. Spell Checking & Query Correction

Implemented in `backend/app/services/spell_checker.py`, providing real-time "Did you mean?" suggestions.

### Damerau-Levenshtein Distance

Traditional Levenshtein distance considers insertions, deletions, and substitutions. SearchX uses **Damerau-Levenshtein distance**, which also supports **adjacent transpositions** (e.g. typing `"teh"` instead of `"the"`):

| Operation | Example | Cost |
| :--- | :--- | :--- |
| **Insertion** | `colr` $\to$ `color` | 1 |
| **Deletion** | `pythoon` $\to$ `python` | 1 |
| **Substitution** | `indax` $\to$ `index` | 1 |
| **Transposition** | `serach` $\to$ `search` | 1 |

### Vocabulary-Weighted Candidate Ranking

For misspelled words, the engine searches the indexed vocabulary for terms with an edit distance $\le 2$. When multiple candidates exist (e.g. `"teh"` $\to$ `"the"`, `"ten"`, `"tea"`), candidates are ranked by their corpus document frequency ($\text{df}$):

$$\text{Rank}(w) = \frac{\text{df}(w)}{\text{EditDistance}(w_{input}, w) + 1}$$

If an initial query produces zero search results, SearchX automatically executes a fallback search on the auto-corrected query.

---

## 7. Caching & Performance Layer (Redis)

Implemented in `backend/app/cache/redis_cache.py`:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FastAPI as Backend (FastAPI)
    participant Redis as Redis Cache
    participant Core as C++ Core Engine

    User->>FastAPI: GET /api/search?q=bm25&algo=bm25
    FastAPI->>Redis: GET search:bm25:bm25:any:10:0
    alt Cache Hit (Sub-millisecond)
        Redis-->>FastAPI: Cached JSON Results
        FastAPI-->>User: 200 OK (from Cache)
    else Cache Miss
        Redis-->>FastAPI: null
        FastAPI->>Core: Exec searchx_engine search ...
        Core-->>FastAPI: Ranked JSON
        FastAPI->>Redis: SETEX search:bm25:... 300s
        FastAPI-->>User: 200 OK (from Core Engine)
    end
```

- **Cache-Aside Pattern**: Queries check Redis first. On cache misses, results are computed by the C++ engine and stored with a 300-second (5-minute) TTL.
- **Write-Invalidation**: Whenever a new document is indexed or crawled, the entire query cache is invalidated to ensure consistency.
- **Graceful Degradation**: If Redis is unreachable, the system automatically falls back to direct engine retrieval without dropping requests.

---

## 8. Relational Data Catalog (PostgreSQL / SQLite)

Managed by SQLAlchemy in `backend/app/db/`:

```mermaid
erDiagram
    DOCUMENTS ||--o{ SEARCH_QUERIES : relates_to
    SOURCES ||--o{ CRAWL_JOBS : triggers
    
    DOCUMENTS {
        string document_id PK
        string url
        string title
        text content
        string content_hash
        string status
        timestamp fetched_at
    }

    SOURCES {
        string domain PK
        boolean enabled
        timestamp created_at
    }

    CRAWL_JOBS {
        string job_id PK
        string status
        int pages_crawled
        int documents_indexed
        json errors
        timestamp created_at
    }

    SEARCH_QUERIES {
        string query PK
        int count
        timestamp last_searched
    }
```

- **Atomic Query Telemetry**: Query counts are updated using database upserts:
  ```sql
  INSERT INTO search_queries (query, count, last_searched)
  VALUES (:q, 1, NOW())
  ON CONFLICT (query) DO UPDATE SET
      count = search_queries.count + 1,
      last_searched = NOW();
  ```

---

## 9. IPC Bridge: Python FastAPI to C++ Engine

FastAPI communicates with the compiled C++ retrieval engine using high-throughput subprocess IPC (`backend/app/services/search_service.py`):

```text
[FastAPI Backend]
       |
       | 1. Generates Tab-Delimited Ingestion Payload (TSV)
       v
[Temporary Ingestion TSV]
  DOC \t doc_1 \t https://... \t Title \t Hash \t Date \t Status \t Raw Content
  TOKENS \t term1:0:0:5 \t term2:1:6:11 ...
       |
       | 2. Executes: searchx_engine index searchx_index.bin payload.tsv
       v
[C++ Core Engine CLI]
       |
       | 3. High-Speed Memory Parse & Posting Insertion
       v
[Binary Index (.bin)]
```

- **Zero Serialization Overhead**: Pre-tokenized documents are streamed to C++ using tab-delimited formatting, eliminating JSON encoding/decoding bottlenecks during bulk ingestion.

---

## 10. Frontend & Secure Authentication Architecture

The user interface (`frontend/src/`) is built on React 18, Vite, and scoped CSS:

### Strict In-Memory Admin Authentication

```mermaid
flowchart TD
    UserKey["User Types Admin API Key"] --> Validate["api.listSources(key)"]
    Validate -->|200 OK| InMemState["Store in React useState('') ONLY"]
    Validate -->|401 Unauthorized| Reject["Reject & Display Error Banner"]
    InMemState --> SessionActive["In-Memory Admin Session Active"]
    SessionActive -->|Lock / Tab Close / Refresh| Wiped["Key Completely Wiped from RAM"]
    InMemState -.->|FORBIDDEN| LocalStorage["localStorage / Cookies (NEVER STORED)"]
```

1. **Zero Client-Side Persistence**:
   - The admin secret is stored solely in React component state.
   - It is never written to `localStorage`, `sessionStorage`, cookies, or JavaScript bundles.
2. **Authenticated Headers**:
   - Protected endpoints receive credentials via the standard `X-Admin-API-Key: <key>` request header.
3. **Public Search Independence**:
   - Public search endpoints (`/api/search`, `/api/suggestions`, `/api/health`, `/api/documents`) require no authentication tokens, ensuring zero friction for end users.

---

## 11. Concept Cross-Reference Matrix

Quick reference mapping theoretical Computer Science concepts to their concrete code locations in SearchX:

| Theoretical Concept | Concrete Implementation in SearchX | File Path |
| :--- | :--- | :--- |
| **Inverted Index** | `class InvertedIndex` | [core-engine/include/inverted_index.hpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/include/inverted_index.hpp) |
| **Hash Table Dictionary** | `std::unordered_map<std::string, std::vector<Posting>>` | [core-engine/include/inverted_index.hpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/include/inverted_index.hpp) |
| **Contiguous Memory Array** | `std::vector<Posting>` | [core-engine/include/inverted_index.hpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/include/inverted_index.hpp) |
| **Positional Indexing** | `Posting::positions` | [core-engine/include/inverted_index.hpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/include/inverted_index.hpp) |
| **Boolean AND Intersection** | `InvertedIndex::lookup_and` (Two-pointer merge) | [core-engine/src/inverted_index.cpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/src/inverted_index.cpp) |
| **Boolean OR Union** | `InvertedIndex::lookup_or` (Hash set union) | [core-engine/src/inverted_index.cpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/src/inverted_index.cpp) |
| **TF-IDF Relevance Scoring** | `Ranker::compute_tf_idf_term` | [core-engine/src/ranking.cpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/src/ranking.cpp) |
| **Okapi BM25 Ranking** | `Ranker::compute_bm25_term` | [core-engine/src/ranking.cpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/src/ranking.cpp) |
| **Binary Serialization** | `IndexSerializer::save` / `IndexSerializer::load` | [core-engine/src/index_serializer.cpp](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/core-engine/src/index_serializer.cpp) |
| **SSRF Network Defense** | `Crawler::_is_safe_ip` (Pre-flight DNS check) | [crawler/app/crawler.py](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/crawler/app/crawler.py) |
| **Unicode NFKC Normalization**| `TextProcessor::normalize_text` | [crawler/app/tokenization.py](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/crawler/app/tokenization.py) |
| **Damerau-Levenshtein Distance**| `SpellChecker::damerau_levenshtein` | [backend/app/services/spell_checker.py](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/backend/app/services/spell_checker.py) |
| **Cache-Aside / LRU Eviction** | `QueryCache::get_search` / `set_search` | [backend/app/cache/redis_cache.py](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/backend/app/cache/redis_cache.py) |
| **Atomic Database Upsert** | `DatabaseRepository::record_query` | [backend/app/db/repository.py](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/backend/app/db/repository.py) |
| **In-Memory UI Authentication** | `AdminDashboard` React State Isolation | [frontend/src/components/AdminDashboard.jsx](file:///c:/Users/Dell/OneDrive/Desktop/Searchx/frontend/src/components/AdminDashboard.jsx) |

---

## 12. Complete Repository Structure & File-by-File Breakdown

This section documents every directory and file in SearchX, detailing its primary responsibility and how it interacts with the rest of the system.

### Project Directory Tree

```text
Searchx/
├── .github/
│   └── workflows/
│       ├── ci.yml                          # Continuous Integration pipeline (build, test, verify)
│       └── codeql.yml                      # Automated security vulnerability & code analysis
├── backend/
│   ├── Dockerfile                          # Multi-stage production Docker build (C++ compile + FastAPI)
│   ├── requirements.txt                    # Python backend production dependencies
│   ├── app/
│   │   ├── config.py                       # Global settings & environment security guards
│   │   ├── main.py                         # FastAPI app entry point, middleware & routing
│   │   ├── api/
│   │   │   ├── routes_search.py            # Public search, suggestions, health & document endpoints
│   │   │   └── routes_admin.py             # Protected admin endpoints (sources, crawl jobs, analytics)
│   │   ├── cache/
│   │   │   └── redis_cache.py              # Redis query caching & mock fallback implementation
│   │   ├── db/
│   │   │   ├── database.py                 # SQLAlchemy engine, connection pooling & schema bootstrap
│   │   │   ├── models.py                   # SQLAlchemy ORM table declarations
│   │   │   ├── repository.py               # Database repository layer (CRUD & atomic analytics)
│   │   │   └── migrations/
│   │   │       └── 001_initial_schema.sql  # Database DDL schema migration script
│   │   ├── models/
│   │   │   └── schemas.py                  # Pydantic data schemas (DTO validation)
│   │   └── services/
│   │       ├── crawler_service.py          # Background crawler orchestrator & DB/index bridge
│   │       ├── search_service.py           # Core search orchestration, C++ CLI bridge & snippets
│   │       └── spell_checker.py            # Damerau-Levenshtein typo correction & suggestions
│   └── tests/
│       ├── test_api.py                     # Integration tests for FastAPI endpoints & auth
│       ├── test_config.py                  # Unit tests for settings & production admin key rules
│       ├── test_database.py                # Unit tests for database models & repository CRUD
│       ├── test_e2e.py                     # Full end-to-end integration tests (ingestion to search)
│       ├── test_redis_cache.py             # Unit tests for Redis cache & TTL expiration
│       └── test_spell_checker.py           # Unit tests for spell checker & candidate ranking
├── core-engine/
│   ├── CMakeLists.txt                      # CMake build script for C++17 engine library, CLI & CTest
│   ├── include/
│   │   ├── document.hpp                    # Document & Token structs and memory models
│   │   ├── index_serializer.hpp            # Binary format constants & serializer interface
│   │   ├── inverted_index.hpp              # InvertedIndex class declaration & postings memory layout
│   │   └── ranking.hpp                     # Ranker class, BM25 / TF-IDF formulas & ScoredResult struct
│   ├── src/
│   │   ├── document.cpp                    # Document model methods (token counting, formatting)
│   │   ├── engine_cli.cpp                  # CLI entrypoint executable for external process calls
│   │   ├── index_serializer.cpp            # Low-level binary serialization & deserialization logic
│   │   ├── inverted_index.cpp              # Inverted index algorithms (AND/OR lookups, fast deletions)
│   │   └── ranking.cpp                     # BM25 & TF-IDF scoring engines & tie-breaking comparator
│   └── tests/
│       ├── test_document.cpp               # CTest unit tests for Document and Token representations
│       ├── test_inverted_index.cpp         # CTest unit tests for index building & Boolean lookups
│       ├── test_ranking.cpp                # CTest unit tests for BM25 and TF-IDF relevance ordering
│       └── test_persistence.cpp            # CTest unit tests for binary roundtrip & corruption resilience
├── crawler/
│   ├── requirements.txt                    # Python crawler dependencies (httpx, bs4, lxml)
│   ├── app/
│   │   ├── crawler.py                      # Asynchronous BFS web crawler with SSRF & robots guards
│   │   ├── models.py                       # Crawler data models (Document, CrawlResult)
│   │   ├── parser.py                       # HTML parser (text extraction & outbound link resolution)
│   │   └── tokenization.py                 # Text normalizer (Unicode NFKC, lowercasing, regex tokens)
│   └── tests/
│       ├── test_crawler.py                 # Unit tests for crawler BFS traversal & SSRF blocks
│       ├── test_parser.py                  # Unit tests for HTML text extraction & link scraping
│       └── test_tokenization.py            # Unit tests for Unicode normalization & token offsets
├── frontend/
│   ├── index.html                          # Single-page application HTML entrypoint
│   ├── package.json                        # Node.js dependencies (React 18, Vite, Vitest)
│   ├── vite.config.js                      # Vite development & production build configuration
│   ├── public/
│   │   ├── favicon.svg                     # Browser tab brand icon
│   │   └── searchx-hero-bg.jpg             # High-resolution hero background asset
│   └── src/
│       ├── App.jsx                         # Main React layout, tab switching, search coordinator
│       ├── index.css                       # Scoped CSS stylesheets, themes & SaaS control center styling
│       ├── main.jsx                        # React root component DOM mount script
│       ├── components/
│       │   ├── AdminDashboard.jsx          # Admin UI with strict in-memory auth & domain whitelist
│       │   ├── DocumentModal.jsx           # Fullscreen modal dialog displaying document metadata
│       │   ├── Icons.jsx                   # High-performance inline SVG icons (Lucide-inspired)
│       │   ├── ImageLightboxModal.jsx      # Lightbox viewer for media search queries
│       │   ├── Navbar.jsx                  # Header navigation, category selector & dark theme toggle
│       │   ├── Pagination.jsx              # Search result pagination controls
│       │   ├── SearchBar.jsx               # Search query input with autocomplete dropdown & filters
│       │   ├── SearchResultCard.jsx        # Ranked result item card with term highlighting
│       │   └── SmartImage.jsx              # Robust image component with fallback handling
│       ├── services/
│       │   └── api.js                      # REST API client (fetch wrapper with X-Admin-API-Key)
│       └── tests/
│           ├── api.test.js                 # Frontend API client unit tests
│           ├── components.test.jsx         # UI component unit tests (SearchBar, Card, Pagination)
│           └── integration.test.jsx        # Frontend integration flows (Search, Admin Auth, Whitelist)
├── scripts/
│   ├── benchmark.py                        # Benchmark script testing QPS, latency, and memory load
│   ├── seed_corpus.py                      # Corpus seeder indexing 53 educational CS/IR documents
│   └── start.sh                            # Production Docker startup entrypoint with $PORT support
├── .env.example                            # Configuration environment variable template
├── docker-compose.yml                      # Production Docker Compose orchestration file
├── nginx.conf                              # Production Nginx reverse-proxy & static asset config
├── PROJECT_CONTEXT.md                      # Engineering design specification & acceptance criteria
├── README.md                               # Repository overview, technology badges & setup guide
└── SEARCHX_ARCHITECTURE_AND_CONCEPTS.md    # This deep-dive architectural & concepts reference
```

---

### Core Retrieval Engine (`core-engine/`)

The C++ retrieval core provides memory-efficient, deterministic search without garbage collection overhead.

- **`CMakeLists.txt`**: Configures C++17 compilation with optimization flags (`-O3`), defines the `searchx_core` static library, the `searchx_engine` executable, and configures CTest test targets.
- **`include/document.hpp`**: Declares `searchx::Document` (title, URL, content hash, timestamps, token count) and `searchx::Token` (term string, integer position, character offsets).
- **`include/inverted_index.hpp`**: Declares `searchx::Posting` and `searchx::InvertedIndex`. Outlines memory structures: the hash dictionary, posting lists, document catalogs, and Boolean lookup signatures.
- **`include/ranking.hpp`**: Declares the `searchx::Ranker` class, configuration parameters (`BM25Params` with $k_1, b$), matching modes (`MatchMode`), and `ScoredResult` with deterministic tie-breaking.
- **`include/index_serializer.hpp`**: Declares `searchx::IndexSerializer`, file magic header/footer constants, versioning numbers, and binary save/load declarations.
- **`src/inverted_index.cpp`**: Implements index construction, inverted dictionary population, two-pointer sorted intersection for Boolean AND, hash set union for Boolean OR, and reverse-mapping document removal (`doc_terms_`).
- **`src/ranking.cpp`**: Implements logarithmic TF-IDF calculation and Okapi BM25 ranking formulas with document length normalization and corpus statistics.
- **`src/index_serializer.cpp`**: Implements custom binary serialization and deserialization with bounded allocation guards (`MAX_DOC_COUNT`, `MAX_VOCAB_SIZE`) and exception safety.
- **`src/engine_cli.cpp`**: Command-line interface executable that accepts subcommands (`search`, `index`, `vocab`, `stats`, `document`) and streams JSON output back to Python.
- **`tests/test_document.cpp`**: Unit tests verifying token position storage, document field preservation, and equality checks.
- **`tests/test_inverted_index.cpp`**: Unit tests verifying single-term lookups, multi-term Boolean AND/OR queries, document updates, and removals.
- **`tests/test_ranking.cpp`**: Unit tests validating TF-IDF and BM25 score calculation, length normalization penalization, and tie-breaking order.
- **`tests/test_persistence.cpp`**: Unit tests verifying binary disk roundtrips, state preservation on failure, corrupted magic headers, truncated files, and missing footers.

---

### FastAPI Backend Service (`backend/`)

The backend coordinates query orchestration, caching, persistent database catalogs, and administrative controls.

- **`Dockerfile`**: Multi-stage Linux Docker build:
  - *Stage 1 (Builder)*: Uses Debian Bookworm with GCC/CMake to compile the C++ engine in Release mode and run CTest.
  - *Stage 2 (Runtime)*: Minimal Python 3.12 image with psycopg, Uvicorn, and copied C++ engine binaries.
- **`requirements.txt`**: Specifies production Python dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `psycopg[binary]`, `redis`, `pydantic`).
- **`app/config.py`**: Central application configuration using `pydantic-settings`. Enforces strict production rules (e.g. prohibiting the default `searchx-admin-secret` in production environments).
- **`app/main.py`**: FastAPI entrypoint configuring CORS middleware for the frontend, lifespan handlers that run SQL database migrations on boot, and route registration.
- **`app/api/routes_search.py`**: Public search controller handling `/api/search` (ranked search), `/api/suggestions` (prefix autocomplete), `/api/health` (system telemetry), and `/api/documents/{id}` (document lookup).
- **`app/api/routes_admin.py`**: Protected controller enforcing `X-Admin-API-Key` authentication on administrative endpoints: `/api/admin/sources`, `/api/admin/crawl-jobs`, and `/api/admin/analytics`.
- **`app/cache/redis_cache.py`**: Redis client manager handling query result caching (SHA-256 parameter keys, 300s TTL), suggestions caching, write-invalidation, and in-memory mock fallback.
- **`app/db/database.py`**: SQLAlchemy engine initializer supporting PostgreSQL and SQLite with automatic `postgres://` to `postgresql://` URI normalization.
- **`app/db/models.py`**: SQLAlchemy ORM entities: `DocumentModel`, `SourceModel`, `CrawlJobModel`, and `SearchQueryModel`.
- **`app/db/repository.py`**: Repository layer abstracting database access; handles document persistence, crawl job logging, domain whitelist lookups, and atomic query counter increments.
- **`app/db/migrations/001_initial_schema.sql`**: Production SQL migration script declaring tables, primary keys, foreign keys, and indexes.
- **`app/models/schemas.py`**: Pydantic DTO models validating API inputs and serializing responses.
- **`app/services/search_service.py`**: Main search coordinator: checks Redis cache, invokes C++ engine subprocesses via CLI, generates contextual snippets around search terms, and triggers spell correction fallbacks.
- **`app/services/crawler_service.py`**: Coordinates background crawl tasks, batches crawled pages, formats tab-delimited ingestion payloads, and triggers C++ index updates.
- **`app/services/spell_checker.py`**: Provides typo detection and suggestion generation using Damerau-Levenshtein edit distance weighted by corpus term frequency.
- **`tests/test_api.py`**: Integration tests testing all public and protected HTTP endpoints, headers, and C++ search integration.
- **`tests/test_config.py`**: Security tests validating environment variable guards and admin key validation.
- **`tests/test_database.py`**: Database tests validating repository CRUD operations and atomic search query upserts.
- **`tests/test_e2e.py`**: Full-system end-to-end integration tests (crawling to database persistence to C++ ranking).
- **`tests/test_redis_cache.py`**: Cache tests validating key generation, cache hits/misses, TTL expiration, and cache invalidation.
- **`tests/test_spell_checker.py`**: Spell checker unit tests verifying typo correction, transposition handling, and candidate ranking.

---

### Web Crawler & Ingestion Pipeline (`crawler/`)

The crawler module safely fetches, parses, normalizes, and tokenizes web documents for ingestion.

- **`requirements.txt`**: Specifies crawler libraries (`httpx`, `beautifulsoup4`, `lxml`).
- **`app/crawler.py`**: Asynchronous BFS web crawler engine. Features:
  - Pre-request DNS resolution blocking SSRF targets (private RFC1918, loopback, AWS metadata).
  - Domain whitelist checking against permitted sources.
  - `robots.txt` parsing and politeness enforcement.
  - Configurable BFS `max_depth` and `max_pages` bounds.
- **`app/models.py`**: Core dataclass models: `Document` (id, title, url, content, content_hash) and `CrawlResult` (pages crawled, indexed count, errors).
- **`app/parser.py`**: HTML parser using BeautifulSoup and lxml; strips boilerplate tags (`<script>`, `<style>`, `<nav>`), extracts page titles, cleans body text, and extracts outbound links.
- **`app/tokenization.py`**: Text normalization pipeline:
  - Unicode NFKC normalization and lowercasing.
  - Positional regex tokenization returning `Token(term, position, char_start, char_end)`.
- **`tests/test_crawler.py`**: Unit tests testing crawler queue traversal, domain filtering, and SSRF IP blocking.
- **`tests/test_parser.py`**: Unit tests validating HTML text extraction, entity decoding, and hyperlink resolution.
- **`tests/test_tokenization.py`**: Unit tests verifying token position counting, Unicode normalization, and punctuation stripping.

---

### React Frontend Application (`frontend/`)

Modern, responsive user interface built on React 18, Vite, and scoped CSS.

- **`index.html`**: Root HTML5 document with mobile viewport optimization and search meta tags.
- **`package.json`**: NPM dependencies (React 18, Vite, Vitest, Testing Library).
- **`vite.config.js`**: Vite configuration supporting JSX transformation and Vitest test runner setup.
- **`src/main.jsx`**: JavaScript entrypoint that mounts the React root DOM node.
- **`src/App.jsx`**: Main application component managing search query state, active view routing (Web, Images, Docs, News, Scholar, Admin), and health check telemetry.
- **`src/index.css`**: Comprehensive CSS styling: responsive design, light/dark themes, animations, search result cards, and the admin dashboard.
- **`src/services/api.js`**: Isolated API service layer wrapping browser `fetch` calls; attaches `X-Admin-API-Key` headers for protected operations.
- **`src/components/Navbar.jsx`**: Top header navigation with SearchX brand logo, category switcher, and dark/light mode toggle.
- **`src/components/SearchBar.jsx`**: Primary search input with instant autocomplete suggestions, search filter dropdowns (Algorithm: BM25/TF-IDF, Match Mode: Any/All), and speech/lens UI buttons.
- **`src/components/SearchResultCard.jsx`**: Renders individual ranked search results with title, URL, contextual snippet with bold term highlighting, and relevance score badge.
- **`src/components/Pagination.jsx`**: Numbered pagination navigation bar with previous/next page buttons.
- **`src/components/DocumentModal.jsx`**: Modal dialog displaying full document contents and metadata when a user clicks "View Full Document".
- **`src/components/ImageLightboxModal.jsx`**: Lightbox media viewer for exploring image search results with high-resolution previews.
- **`src/components/SmartImage.jsx`**: Image loader with smooth lazy-loading and graceful fallback when images fail to load.
- **`src/components/AdminDashboard.jsx`**: Control center featuring:
  - Strict in-memory authentication login gate (never persisted to `localStorage`).
  - Permitted crawl domain whitelist management (add, enable, disable).
  - Web crawler dispatch form (seeds, depth, page limits) and job telemetry.
  - Redis cache and query frequency analytics visualization.
- **`src/components/Icons.jsx`**: High-performance SVG icons (Lucide-inspired) avoiding heavy third-party icon libraries.
- **`src/tests/api.test.js`**: Unit tests verifying frontend API client parameter serialization and header attachments.
- **`src/tests/components.test.jsx`**: Component tests verifying SearchBar, SearchResultCard, and Pagination user interactions.
- **`src/tests/integration.test.jsx`**: Flow tests verifying homepage rendering, search execution, zero-results handling, admin authentication gate, in-memory isolation, and domain whitelist addition.

---

### Automation & Deployment Scripts (`scripts/`)

- **`scripts/start.sh`**: Production container entrypoint script for Render/Docker:
  - Runs database migrations and seeds initial corpus documents via `scripts/seed_corpus.py`.
  - Starts Uvicorn server bound to `0.0.0.0` on dynamically allocated `${PORT:-8000}`.
- **`scripts/seed_corpus.py`**: Corpus ingestion script that parses and indexes 53 comprehensive Computer Science and Information Retrieval documents into PostgreSQL and the C++ engine index segment.
- **`scripts/benchmark.py`**: Performance evaluation script that measures search query latency (p50, p95, p99), throughput (queries per second), and memory footprint under concurrent load.

---

### Root Infrastructure & Configuration Files

- **`docker-compose.yml`**: Declarative multi-container configuration orchestrating PostgreSQL 16, Redis 7, Backend (FastAPI + C++ engine), and Frontend (Nginx + React) on an internal bridge network.
- **`nginx.conf`**: Production Nginx configuration providing Gzip static asset compression, SPA route fallback (`try_files $uri /index.html`), and `/api/` reverse-proxy forwarding.
- **`.env.example`**: Reference template documenting all configurable environment variables (`ENVIRONMENT`, `SEARCHX_ADMIN_KEY`, `DATABASE_URL`, `REDIS_URL`, `SEARCHX_CACHE_TTL`).
- **`PROJECT_CONTEXT.md`**: Master system specification, architectural guidelines, and module acceptance criteria.
- **`README.md`**: Project presentation document with badges, architecture summary, and quick-start instructions.
- **`SEARCHX_ARCHITECTURE_AND_CONCEPTS.md`**: Complete deep-dive architectural, mathematical, and data structures documentation.


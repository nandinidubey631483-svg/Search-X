# ADR 0001: Document Model and Text Normalization Contract

- **Status:** Accepted
- **Date:** 2026-11-23
- **Deciders:** Engineering Team
- **Consulted:** `PROJECT_CONTEXT.md` (Modules B & C)

---

## 1. Context and Problem Statement

SearchX requires a clear boundary and shared data contract between the Python ingestion/crawler subsystem and the C++ inverted index engine. Without a strictly defined serialization contract and normalization standard:
- Document representations might drift between storage, crawler, and core search.
- Text normalization for documents during indexing might diverge from query normalization during search, leading to false negatives (unmatched search terms) or false positives.

---

## 2. Decision: Canonical Document Model

A document in SearchX represents an individual searchable unit (such as a crawled web page or an imported document).

### Schema Specification

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `document_id` | `string` | **Yes** | Stable, unique identifier (UUIDv4 or deterministic hash of canonical URL). Non-empty. |
| `source_url` | `string` | No | Canonical HTTP/HTTPS or file URL. Empty string if not applicable. |
| `title` | `string` | **Yes** | Human-readable document title (sanitized text). Defaults to empty or URL if unavailable. |
| `content` | `string` | **Yes** | Extracted, cleaned plain text (no HTML markup/scripts). Non-empty for indexing. |
| `description` | `string` | No | Optional summary or meta description. |
| `language` | `string` | No | ISO 639-1 language code (e.g., `en`). Default: `"en"`. |
| `content_hash` | `string` | **Yes** | Hex-encoded SHA-256 digest of the UTF-8 `content`. Used for deduplication. |
| `fetched_at` | `string` | **Yes** | ISO 8601 UTC timestamp string (e.g. `2026-11-23T09:00:00Z`). |
| `status` | `string` | **Yes** | State: `"ingested"`, `"indexed"`, `"failed"`, or `"archived"`. |

### Deduplication Rules
- If an ingested document's `content_hash` matches an existing active document with the same `source_url`, it is considered unchanged and redundant re-indexing is avoided.
- If two different URLs produce identical `content_hash` values, they are marked as duplicate content; the system retains the canonical URL.

---

## 3. Decision: Text Normalization and Tokenization Pipeline

Both indexed documents and incoming user queries MUST pass through the exact same normalization rules to ensure predictable, deterministic keyword matching.

### Pipeline Stages
1. **HTML Stripping (Ingestion only):**
   - Strip all `<script>`, `<style>`, `<noscript>`, and HTML comment tags.
   - Extract plain text while converting block elements (`<p>`, `<div>`, `<br>`, `<h1>`-`<h6>`, `<li>`) into line/space separators.
   - Decode HTML entities (e.g. `&amp;` $\to$ `&`, `&lt;` $\to$ `<`).
2. **Unicode Normalization:**
   - Apply Unicode **NFKC** (Compatibility Decomposition followed by Canonical Composition) normalization.
3. **Case Folding:**
   - Lowercase all characters (`lower()` in Python / standard lowercase in C++).
4. **Tokenization & Offsets:**
   - Split tokens along whitespace and punctuation boundaries.
   - Preserve alphanumeric characters (`[a-zA-Z0-9]`).
   - Words containing internal apostrophes or hyphens (e.g. `user's`, `state-of-the-art`) are preserved or normalized consistently.
   - Record positional metadata for each token:
     - `term`: The normalized lowercase string.
     - `position`: Zero-indexed integer indicating token order in the stream.
     - `char_start`: Starting character index in the cleaned content.
     - `char_end`: Ending character index in the cleaned content.
5. **Stopword Filtering (Configurable):**
   - Optional stopword filtering using a standard English stopword list.
   - When enabled, stopword tokens may be skipped or preserved with positional gaps depending on phrase search configuration.
6. **No Silent Stemming:**
   - No stemming (e.g. Porter/Snowball) or lemmatization is applied unless explicitly configured and enabled for both document and query pipelines.

---

## 4. Cross-Language Consistency Contract

- **Python Implementation:**
  - `crawler/app/models.py`: `Document` dataclass with serialization to/from JSON.
  - `crawler/app/text_processor.py`: `TextProcessor` class exposing `clean_html()`, `normalize_text()`, and `tokenize()`.
- **C++ Implementation:**
  - `core-engine/include/document.hpp`: `Document` and `Token` structs mirroring the field names, types, and semantics.
  - Standard JSON serialization guarantees interoperability between Python API and C++ engine.

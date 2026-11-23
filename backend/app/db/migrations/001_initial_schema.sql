-- =============================================================================
-- SearchX Database Schema - Migration 001
-- Target: PostgreSQL 14+ (Compatible with standard ANSI SQL / SQLite)
-- =============================================================================

-- 1. Documents Metadata Table
CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR(128) PRIMARY KEY,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    language VARCHAR(16) DEFAULT 'en',
    content_hash VARCHAR(64) NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(32) DEFAULT 'ingested'
);

CREATE INDEX IF NOT EXISTS ix_documents_source_url ON documents (source_url);
CREATE INDEX IF NOT EXISTS ix_documents_content_hash ON documents (content_hash);

-- 2. Crawl Sources Table
CREATE TABLE IF NOT EXISTS sources (
    domain VARCHAR(255) PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Crawl Jobs Table
CREATE TABLE IF NOT EXISTS crawl_jobs (
    job_id VARCHAR(64) PRIMARY KEY,
    status VARCHAR(32) NOT NULL,
    seed_urls TEXT NOT NULL,
    allowed_domains TEXT,
    pages_crawled INTEGER DEFAULT 0,
    documents_indexed INTEGER DEFAULT 0,
    errors TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_crawl_jobs_status ON crawl_jobs (status);

-- 4. Query Analytics Table (with UNIQUE constraint on query_text for atomic upserts)
CREATE TABLE IF NOT EXISTS query_analytics (
    id SERIAL PRIMARY KEY,
    query_text VARCHAR(255) UNIQUE NOT NULL,
    count INTEGER DEFAULT 1,
    last_queried_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_query_analytics_count ON query_analytics (count DESC);

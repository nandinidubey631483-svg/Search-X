"""
Unit tests for SearchX Database Persistence Layer (Module H).
Validates schema creation, transactional CRUD, deduplication, atomic query analytics,
and rollback behavior on SQLite / PostgreSQL.
"""
from datetime import datetime, timezone
from pathlib import Path
import pytest

from crawler.app.models import Document
from backend.app.db.database import Database
from backend.app.db.models import (
    CrawlJobModel,
    DocumentModel,
    QueryAnalyticsModel,
    SourceModel,
)
from backend.app.db.repository import DatabaseRepository


@pytest.fixture
def test_db(tmp_path: Path) -> Database:
    """Provide an isolated SQLite database file per test."""
    db_file = tmp_path / "test_searchx.db"
    db = Database(f"sqlite:///{db_file.as_posix()}")
    db.create_tables()
    return db


@pytest.fixture
def repo(test_db: Database) -> DatabaseRepository:
    """Provide repository wired to isolated test database."""
    return DatabaseRepository(db=test_db)


def test_schema_creation_and_drop(tmp_path: Path):
    """Verify table creation and cleanup."""
    db_file = tmp_path / "lifecycle.db"
    db = Database(f"sqlite:///{db_file.as_posix()}")
    
    # Create tables
    db.create_tables()
    with db.session() as s:
        # Tables should exist and be queryable
        assert s.query(DocumentModel).count() == 0
        assert s.query(SourceModel).count() == 0
        assert s.query(CrawlJobModel).count() == 0
        assert s.query(QueryAnalyticsModel).count() == 0

    # Drop tables
    db.drop_tables()


def test_document_crud_and_deduplication(repo: DatabaseRepository):
    """Verify single and batch document persistence, retrieval, and content hash lookup."""
    doc1 = Document.create(
        document_id="doc_001",
        source_url="https://example.com/page1",
        title="Page One",
        content="This is the first document body.",
        description="First description",
        language="en",
    )

    # Save document
    repo.save_document(doc1)
    assert repo.count_documents() == 1

    # Retrieve document
    fetched = repo.get_document("doc_001")
    assert fetched is not None
    assert fetched.document_id == "doc_001"
    assert fetched.title == "Page One"
    assert fetched.source_url == "https://example.com/page1"
    assert fetched.content == "This is the first document body."
    assert fetched.content_hash == doc1.content_hash

    # Deduplication / lookup by content hash
    found_by_hash = repo.find_by_content_hash(doc1.content_hash)
    assert found_by_hash is not None
    assert found_by_hash.document_id == "doc_001"
    assert repo.find_by_content_hash("nonexistent_hash") is None

    # Update document
    doc1_updated = Document.create(
        document_id="doc_001",
        source_url="https://example.com/page1",
        title="Page One Updated",
        content="Updated content body.",
        description="Updated description",
        language="en",
    )
    repo.save_document(doc1_updated)
    assert repo.count_documents() == 1
    refetched = repo.get_document("doc_001")
    assert refetched.title == "Page One Updated"
    assert refetched.content == "Updated content body."
    assert refetched.content_hash == doc1_updated.content_hash

    # Batch save
    doc2 = Document.create(
        document_id="doc_002",
        source_url="https://example.com/page2",
        title="Page Two",
        content="Second content body.",
    )
    doc3 = Document.create(
        document_id="doc_003",
        source_url="https://example.com/page3",
        title="Page Three",
        content="Third content body.",
    )
    count = repo.save_documents([doc2, doc3])
    assert count == 2
    assert repo.count_documents() == 3
    assert repo.get_document("doc_002") is not None
    assert repo.get_document("doc_003") is not None
    assert repo.get_document("nonexistent") is None


def test_sources_crud(repo: DatabaseRepository):
    """Verify source registration, enabling/disabling, and permission checking."""
    # Add sources
    repo.save_source("example.com", enabled=True)
    repo.save_source("docs.python.org", enabled=True)
    repo.save_source("forbidden.com", enabled=False)

    sources = repo.list_sources()
    assert len(sources) == 3

    assert repo.is_domain_allowed("example.com") is True
    assert repo.is_domain_allowed("EXAMPLE.COM") is True  # Case insensitive
    assert repo.is_domain_allowed("docs.python.org") is True
    assert repo.is_domain_allowed("forbidden.com") is False
    assert repo.is_domain_allowed("unregistered.org") is False

    # Update source status
    repo.save_source("forbidden.com", enabled=True)
    assert repo.is_domain_allowed("forbidden.com") is True


def test_crawl_job_lifecycle(repo: DatabaseRepository):
    """Verify crawl job creation, updating, and JSON error serialization."""
    job_id = "job_test_001"
    now = datetime.now(timezone.utc)

    # Initial running state
    job = repo.save_crawl_job(
        job_id=job_id,
        status="running",
        seed_urls=["https://example.com"],
        allowed_domains=["example.com"],
        pages_crawled=0,
        documents_indexed=0,
    )
    assert job.status == "running"

    fetched = repo.get_crawl_job(job_id)
    assert fetched is not None
    assert fetched.job_id == job_id
    assert fetched.status == "running"
    assert fetched.pages_crawled == 0

    # Completion update
    completed_job = repo.save_crawl_job(
        job_id=job_id,
        status="completed",
        seed_urls=["https://example.com"],
        allowed_domains=["example.com"],
        pages_crawled=5,
        documents_indexed=4,
        errors={"https://example.com/broken": "404 Not Found"},
        completed_at=now,
    )
    assert completed_job.status == "completed"
    assert completed_job.pages_crawled == 5
    assert completed_job.documents_indexed == 4

    fetched_completed = repo.get_crawl_job(job_id)
    assert fetched_completed.status == "completed"
    assert fetched_completed.pages_crawled == 5
    assert fetched_completed.documents_indexed == 4
    assert "404 Not Found" in fetched_completed.errors


def test_query_analytics_safe_atomic_counter(repo: DatabaseRepository):
    """Verify atomic counter increments and top-query ranking."""
    # First query occurrence
    c1 = repo.record_query("information retrieval")
    assert c1 == 1

    # Second occurrence of same query
    c2 = repo.record_query("information retrieval")
    assert c2 == 2

    # Third occurrence with irregular case and padding
    c3 = repo.record_query("  Information Retrieval  ")
    assert c3 == 3

    # Different queries
    repo.record_query("inverted index")
    repo.record_query("inverted index")
    repo.record_query("bm25 ranking")

    # Check top queries
    top = repo.get_top_queries(limit=10)
    assert top == {
        "information retrieval": 3,
        "inverted index": 2,
        "bm25 ranking": 1,
    }

    # Top queries limit
    top_limited = repo.get_top_queries(limit=2)
    assert len(top_limited) == 2
    assert "information retrieval" in top_limited
    assert "inverted index" in top_limited

    # Total queries count
    assert repo.total_queries_count() == 6

    # Empty query should be a no-op
    assert repo.record_query("   ") == 0
    assert repo.total_queries_count() == 6


def test_transaction_rollback_on_error(test_db: Database):
    """Verify that uncommitted operations roll back automatically on exception."""
    with pytest.raises(RuntimeError):
        with test_db.session() as session:
            record = DocumentModel(
                document_id="rollback_doc",
                source_url="https://fail.com",
                title="Fail Doc",
                content="This should not persist",
                content_hash="fail_hash",
            )
            session.add(record)
            session.flush()
            # Explicitly raise exception to trigger rollback
            raise RuntimeError("Transaction failure test")

    # Verify document was rolled back and is not in database
    with test_db.session() as session:
        found = session.query(DocumentModel).filter(DocumentModel.document_id == "rollback_doc").first()
        assert found is None

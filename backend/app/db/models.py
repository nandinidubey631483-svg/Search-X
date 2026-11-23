"""
SQLAlchemy ORM models for SearchX.
Defines schemas for documents, sources, crawl jobs, and query analytics.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentModel(Base):
    """Stores durable document metadata and content hashes."""
    __tablename__ = "documents"

    document_id = Column(String(128), primary_key=True)
    source_url = Column(Text, nullable=False, index=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String(16), default="en")
    content_hash = Column(String(64), nullable=False, index=True)
    fetched_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    status = Column(String(32), default="ingested")


class SourceModel(Base):
    """Stores allowed domain sources for crawling."""
    __tablename__ = "sources"

    domain = Column(String(255), primary_key=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class CrawlJobModel(Base):
    """Tracks crawl job execution state and results."""
    __tablename__ = "crawl_jobs"

    job_id = Column(String(64), primary_key=True)
    status = Column(String(32), nullable=False, index=True)
    seed_urls = Column(Text, nullable=False)  # JSON-encoded list of strings
    allowed_domains = Column(Text, nullable=True)  # JSON-encoded list of strings
    pages_crawled = Column(Integer, default=0, nullable=False)
    documents_indexed = Column(Integer, default=0, nullable=False)
    errors = Column(Text, nullable=True)  # JSON-encoded dictionary
    created_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class QueryAnalyticsModel(Base):
    """Stores search query frequencies with unique constraint for atomic upserts."""
    __tablename__ = "query_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(String(255), unique=True, nullable=False, index=True)
    count = Column(Integer, default=1, nullable=False)
    last_queried_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

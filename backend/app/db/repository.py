"""
Database Repository providing transactional CRUD and safe atomic operations.
Complies with PROJECT_CONTEXT.md Module H.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from crawler.app.models import Document, DocumentStatus

from .database import Database, get_database
from .models import CrawlJobModel, DocumentModel, QueryAnalyticsModel, SourceModel


class DatabaseRepository:
    """Encapsulates durable persistence operations for documents, sources, crawl jobs, and analytics."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_database()

    # --------------------------------------------------------------------------
    # Documents CRUD
    # --------------------------------------------------------------------------

    def save_document(self, doc: Document) -> None:
        """Insert or update a document in the database."""
        with self.db.session() as session:
            existing = session.query(DocumentModel).filter(DocumentModel.document_id == doc.document_id).first()
            if existing:
                existing.title = doc.title
                existing.source_url = doc.source_url
                existing.content = doc.content
                existing.description = doc.description
                existing.language = doc.language
                existing.content_hash = doc.content_hash
                existing.status = doc.status
            else:
                record = DocumentModel(
                    document_id=doc.document_id,
                    source_url=doc.source_url,
                    title=doc.title,
                    content=doc.content,
                    description=doc.description,
                    language=doc.language,
                    content_hash=doc.content_hash,
                    status=doc.status,
                    fetched_at=datetime.now(timezone.utc),
                )
                session.add(record)

    def save_documents(self, docs: List[Document]) -> int:
        """Batch save documents in a single transaction."""
        if not docs:
            return 0
        with self.db.session() as session:
            count = 0
            for doc in docs:
                existing = session.query(DocumentModel).filter(DocumentModel.document_id == doc.document_id).first()
                if existing:
                    existing.title = doc.title
                    existing.source_url = doc.source_url
                    existing.content = doc.content
                    existing.content_hash = doc.content_hash
                    existing.status = doc.status
                else:
                    record = DocumentModel(
                        document_id=doc.document_id,
                        source_url=doc.source_url,
                        title=doc.title,
                        content=doc.content,
                        description=doc.description,
                        language=doc.language,
                        content_hash=doc.content_hash,
                        status=doc.status,
                        fetched_at=datetime.now(timezone.utc),
                    )
                    session.add(record)
                count += 1
            return count

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        with self.db.session() as session:
            row = session.query(DocumentModel).filter(DocumentModel.document_id == doc_id).first()
            if not row:
                return None
            return Document(
                document_id=row.document_id,
                source_url=row.source_url,
                title=row.title,
                content=row.content,
                description=row.description or "",
                language=row.language or "en",
                content_hash=row.content_hash,
                fetched_at=row.fetched_at.isoformat() if row.fetched_at else "",
                status=row.status or "ingested",
            )

    def find_by_content_hash(self, content_hash: str) -> Optional[Document]:
        """Check for existing duplicate document by content hash."""
        with self.db.session() as session:
            row = session.query(DocumentModel).filter(DocumentModel.content_hash == content_hash).first()
            if not row:
                return None
            return Document(
                document_id=row.document_id,
                source_url=row.source_url,
                title=row.title,
                content=row.content,
                content_hash=row.content_hash,
                fetched_at=row.fetched_at.isoformat() if row.fetched_at else "",
                status=row.status or "ingested",
            )

    def count_documents(self) -> int:
        """Count total persisted documents."""
        with self.db.session() as session:
            return session.query(DocumentModel).count()

    # --------------------------------------------------------------------------
    # Sources CRUD
    # --------------------------------------------------------------------------

    def save_source(self, domain: str, enabled: bool = True) -> SourceModel:
        """Add or update an allowed crawl source."""
        clean_domain = domain.strip().lower()
        with self.db.session() as session:
            source = session.query(SourceModel).filter(SourceModel.domain == clean_domain).first()
            if source:
                source.enabled = enabled
            else:
                source = SourceModel(domain=clean_domain, enabled=enabled)
                session.add(source)
                session.flush()
            return SourceModel(domain=source.domain, enabled=source.enabled, created_at=source.created_at)

    def list_sources(self) -> List[SourceModel]:
        """List all configured crawl sources."""
        with self.db.session() as session:
            rows = session.query(SourceModel).all()
            return [SourceModel(domain=r.domain, enabled=r.enabled, created_at=r.created_at) for r in rows]

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is present and enabled."""
        clean_domain = domain.strip().lower()
        with self.db.session() as session:
            row = session.query(SourceModel).filter(SourceModel.domain == clean_domain).first()
            return bool(row and row.enabled)

    # --------------------------------------------------------------------------
    # Crawl Jobs CRUD
    # --------------------------------------------------------------------------

    def save_crawl_job(
        self,
        job_id: str,
        status: str,
        seed_urls: List[str],
        allowed_domains: Optional[List[str]],
        pages_crawled: int = 0,
        documents_indexed: int = 0,
        errors: Optional[Dict[str, str]] = None,
        completed_at: Optional[datetime] = None,
    ) -> CrawlJobModel:
        """Persist or update a crawl job state."""
        with self.db.session() as session:
            job = session.query(CrawlJobModel).filter(CrawlJobModel.job_id == job_id).first()
            if job:
                job.status = status
                job.pages_crawled = pages_crawled
                job.documents_indexed = documents_indexed
                job.errors = json.dumps(errors or {})
                if completed_at:
                    job.completed_at = completed_at
            else:
                job = CrawlJobModel(
                    job_id=job_id,
                    status=status,
                    seed_urls=json.dumps(seed_urls),
                    allowed_domains=json.dumps(allowed_domains or []),
                    pages_crawled=pages_crawled,
                    documents_indexed=documents_indexed,
                    errors=json.dumps(errors or {}),
                    created_at=datetime.now(timezone.utc),
                    completed_at=completed_at,
                )
                session.add(job)
                session.flush()

            return CrawlJobModel(
                job_id=job.job_id,
                status=job.status,
                seed_urls=job.seed_urls,
                allowed_domains=job.allowed_domains,
                pages_crawled=job.pages_crawled,
                documents_indexed=job.documents_indexed,
                errors=job.errors,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )

    def get_crawl_job(self, job_id: str) -> Optional[CrawlJobModel]:
        """Fetch crawl job by ID."""
        with self.db.session() as session:
            r = session.query(CrawlJobModel).filter(CrawlJobModel.job_id == job_id).first()
            if not r:
                return None
            return CrawlJobModel(
                job_id=r.job_id,
                status=r.status,
                seed_urls=r.seed_urls,
                allowed_domains=r.allowed_domains,
                pages_crawled=r.pages_crawled,
                documents_indexed=r.documents_indexed,
                errors=r.errors,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )

    # --------------------------------------------------------------------------
    # Analytics Safe Counter Upsert
    # --------------------------------------------------------------------------

    def record_query(self, query_text: str) -> int:
        """
        Atomically update query frequency counter.
        Uses safe update-first with fallback insert to guarantee concurrency safety.
        """
        clean = query_text.strip().lower()
        if not clean:
            return 0

        now = datetime.now(timezone.utc)
        with self.db.session() as session:
            # 1. Attempt atomic update on existing record
            updated = (
                session.query(QueryAnalyticsModel)
                .filter(QueryAnalyticsModel.query_text == clean)
                .update(
                    {
                        QueryAnalyticsModel.count: QueryAnalyticsModel.count + 1,
                        QueryAnalyticsModel.last_queried_at: now,
                    },
                    synchronize_session=False,
                )
            )

            # 2. If record did not exist, insert initial record
            if not updated:
                try:
                    record = QueryAnalyticsModel(query_text=clean, count=1, last_queried_at=now)
                    session.add(record)
                    session.flush()
                except Exception:
                    # Rare race condition: record was inserted concurrently, retry update
                    session.rollback()
                    session.query(QueryAnalyticsModel).filter(
                        QueryAnalyticsModel.query_text == clean
                    ).update(
                        {
                            QueryAnalyticsModel.count: QueryAnalyticsModel.count + 1,
                            QueryAnalyticsModel.last_queried_at: now,
                        },
                        synchronize_session=False,
                    )

            row = session.query(QueryAnalyticsModel).filter(QueryAnalyticsModel.query_text == clean).first()
            return row.count if row else 1

    def get_top_queries(self, limit: int = 10) -> Dict[str, int]:
        """Fetch the most frequently executed queries."""
        with self.db.session() as session:
            rows = (
                session.query(QueryAnalyticsModel)
                .order_by(QueryAnalyticsModel.count.desc())
                .limit(limit)
                .all()
            )
            return {r.query_text: r.count for r in rows}

    def total_queries_count(self) -> int:
        """Sum of all executed query counts."""
        with self.db.session() as session:
            from sqlalchemy import func
            total = session.query(func.sum(QueryAnalyticsModel.count)).scalar()
            return int(total) if total is not None else 0

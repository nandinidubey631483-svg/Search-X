"""
Crawler Service for SearchX Backend.
Manages crawl sources and executes crawl jobs, indexing results into the search engine.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from crawler.app.crawler import CrawlConfig, Crawler
from crawler.app.models import Document

from ..db.repository import DatabaseRepository
from ..models.schemas import CrawlJobCreate, CrawlJobResponse, SourceCreate, SourceResponse
from .search_service import SearchEngineService

logger = logging.getLogger("searchx.backend.crawler")


class CrawlerService:
    """Manages crawl sources and executes crawl jobs."""

    def __init__(
        self,
        search_service: SearchEngineService,
        repository: Optional[DatabaseRepository] = None,
    ) -> None:
        self.search_service = search_service
        self.repository = repository or DatabaseRepository()
        self.sources: Dict[str, bool] = {
            "example.com": True,
            "docs.python.org": True,
        }
        self.jobs: Dict[str, CrawlJobResponse] = {}

        # Seed default sources in DB if sources table is empty
        if self.repository:
            try:
                existing = self.repository.list_sources()
                if not existing:
                    self.repository.save_source("example.com", True)
                    self.repository.save_source("docs.python.org", True)
            except Exception as e:
                logger.warning(f"Could not seed default sources: {e}")

    def get_sources(self) -> List[SourceResponse]:
        """List all configured crawl sources."""
        if self.repository:
            try:
                db_sources = self.repository.list_sources()
                if db_sources:
                    return [SourceResponse(domain=s.domain, enabled=s.enabled) for s in db_sources]
            except Exception as e:
                logger.warning(f"Failed to read sources from DB: {e}")
        return [SourceResponse(domain=domain, enabled=enabled) for domain, enabled in self.sources.items()]

    def add_source(self, source: SourceCreate) -> SourceResponse:
        """Add or update an allowed crawl source."""
        domain_clean = source.domain.strip().lower()
        self.sources[domain_clean] = source.enabled
        if self.repository:
            try:
                self.repository.save_source(domain_clean, source.enabled)
            except Exception as e:
                logger.warning(f"Failed to save source in DB: {e}")
        return SourceResponse(domain=domain_clean, enabled=source.enabled)

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is explicitly enabled."""
        if self.repository:
            try:
                return self.repository.is_domain_allowed(domain)
            except Exception as e:
                logger.warning(f"Failed to check domain allowance in DB: {e}")
        return self.sources.get(domain.lower(), False)

    def start_crawl_job(self, req: CrawlJobCreate) -> CrawlJobResponse:
        """Execute a controlled crawl job and index resulting documents."""
        job_id = f"job_{uuid.uuid4().hex[:8]}"

        # Determine allowed domains
        allowed = set(req.allowed_domains or [])
        if not allowed:
            if self.repository:
                try:
                    db_sources = self.repository.list_sources()
                    allowed = {s.domain for s in db_sources if s.enabled}
                except Exception:
                    allowed = {d for d, enabled in self.sources.items() if enabled}
            else:
                # Fall back to enabled system sources
                allowed = {d for d, enabled in self.sources.items() if enabled}

        if self.repository:
            try:
                self.repository.save_crawl_job(
                    job_id=job_id,
                    status="running",
                    seed_urls=req.seed_urls,
                    allowed_domains=list(allowed),
                )
            except Exception as e:
                logger.warning(f"Failed to record starting crawl job: {e}")

        config = CrawlConfig(
            seed_urls=req.seed_urls,
            allowed_domains=allowed,
            max_depth=req.max_depth,
            max_pages=req.max_pages,
            delay_seconds=0.0,  # Fast local execution
        )

        crawler = Crawler(config=config, text_processor=self.search_service.text_processor)
        crawl_result = crawler.run()

        # Index crawled documents into C++ engine
        indexed_count = 0
        if crawl_result.documents:
            indexed_count = self.search_service.index_documents(crawl_result.documents)

        now = datetime.now(timezone.utc)
        if self.repository:
            try:
                self.repository.save_crawl_job(
                    job_id=job_id,
                    status="completed",
                    seed_urls=req.seed_urls,
                    allowed_domains=list(allowed),
                    pages_crawled=crawl_result.pages_crawled,
                    documents_indexed=indexed_count,
                    errors=crawl_result.failed_urls,
                    completed_at=now,
                )
            except Exception as e:
                logger.warning(f"Failed to record completed crawl job: {e}")

        job_resp = CrawlJobResponse(
            job_id=job_id,
            status="completed",
            pages_crawled=crawl_result.pages_crawled,
            documents_indexed=indexed_count,
            errors=crawl_result.failed_urls,
        )
        self.jobs[job_id] = job_resp
        return job_resp

    def get_job(self, job_id: str) -> Optional[CrawlJobResponse]:
        """Retrieve crawl job status and statistics."""
        if self.repository:
            try:
                job_model = self.repository.get_crawl_job(job_id)
                if job_model:
                    err_dict = {}
                    if job_model.errors:
                        try:
                            err_dict = json.loads(job_model.errors)
                        except Exception:
                            err_dict = {}
                    return CrawlJobResponse(
                        job_id=job_model.job_id,
                        status=job_model.status,
                        pages_crawled=job_model.pages_crawled,
                        documents_indexed=job_model.documents_indexed,
                        errors=err_dict,
                    )
            except Exception as e:
                logger.warning(f"Failed to get crawl job from DB: {e}")
        return self.jobs.get(job_id)

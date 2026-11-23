"""
Crawler Service for SearchX Backend.
Manages crawl sources and executes crawl jobs, indexing results into the search engine.
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Set

from crawler.app.crawler import CrawlConfig, Crawler
from crawler.app.models import Document

from ..models.schemas import CrawlJobCreate, CrawlJobResponse, SourceCreate, SourceResponse
from .search_service import SearchEngineService


class CrawlerService:
    """Manages crawl sources and executes crawl jobs."""

    def __init__(self, search_service: SearchEngineService) -> None:
        self.search_service = search_service
        self.sources: Dict[str, bool] = {
            "example.com": True,
            "docs.python.org": True,
        }
        self.jobs: Dict[str, CrawlJobResponse] = {}

    def get_sources(self) -> List[SourceResponse]:
        """List all configured crawl sources."""
        return [SourceResponse(domain=domain, enabled=enabled) for domain, enabled in self.sources.items()]

    def add_source(self, source: SourceCreate) -> SourceResponse:
        """Add or update an allowed crawl source."""
        domain_clean = source.domain.strip().lower()
        self.sources[domain_clean] = source.enabled
        return SourceResponse(domain=domain_clean, enabled=source.enabled)

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is explicitly enabled."""
        return self.sources.get(domain.lower(), False)

    def start_crawl_job(self, req: CrawlJobCreate) -> CrawlJobResponse:
        """Execute a controlled crawl job and index resulting documents."""
        job_id = f"job_{uuid.uuid4().hex[:8]}"

        # Determine allowed domains
        allowed = set(req.allowed_domains or [])
        if not allowed:
            # Fall back to enabled system sources
            allowed = {d for d, enabled in self.sources.items() if enabled}

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
        return self.jobs.get(job_id)

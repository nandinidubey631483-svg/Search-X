"""Pydantic request and response schemas for SearchX API."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    document_id: str
    title: str
    url: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    total_hits: int
    page: int
    limit: int
    algorithm: str
    results: List[SearchResultItem]
    did_you_mean: Optional[str] = None
    is_auto_corrected: bool = False


class SuggestionResponse(BaseModel):
    query: str
    suggestions: List[str]


class DocumentResponse(BaseModel):
    document_id: str
    title: str
    source_url: str
    content: str
    description: str
    language: str
    fetched_at: str
    status: str


class IndexStats(BaseModel):
    total_documents: int
    vocabulary_size: int
    average_document_length: float


class HealthResponse(BaseModel):
    status: str
    version: str
    index_stats: IndexStats


class SourceCreate(BaseModel):
    domain: str = Field(..., min_length=3, description="Allowed domain name, e.g. example.com")
    enabled: bool = True


class SourceResponse(BaseModel):
    domain: str
    enabled: bool


class CrawlJobCreate(BaseModel):
    seed_urls: List[str] = Field(..., min_length=1)
    allowed_domains: Optional[List[str]] = None
    max_depth: int = Field(default=2, ge=0, le=5)
    max_pages: int = Field(default=20, ge=1, le=200)


class CrawlJobResponse(BaseModel):
    job_id: str
    status: str
    pages_crawled: int
    documents_indexed: int
    errors: Dict[str, str] = Field(default_factory=dict)


class CacheStats(BaseModel):
    hits: int = 0
    misses: int = 0
    hit_ratio: float = 0.0
    enabled: bool = True


class AnalyticsResponse(BaseModel):
    total_searches: int
    top_queries: Dict[str, int]
    index_stats: IndexStats
    cache_stats: Optional[CacheStats] = None

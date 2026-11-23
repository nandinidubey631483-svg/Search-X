"""Admin operations: allowed crawl sources, crawl jobs, and analytics."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status

from ..config import settings
from ..models.schemas import (
    AnalyticsResponse,
    CrawlJobCreate,
    CrawlJobResponse,
    SourceCreate,
    SourceResponse,
)
from ..services.crawler_service import CrawlerService
from .routes_search import get_search_service

router = APIRouter(prefix="/admin", tags=["Admin"])

# Singleton crawler service instance
_crawler_service = CrawlerService(search_service=get_search_service())


def get_crawler_service() -> CrawlerService:
    return _crawler_service


def verify_admin_auth(
    x_admin_api_key: Optional[str] = Header(None, alias="X-Admin-API-Key"),
    authorization: Optional[str] = Header(None),
) -> None:
    """Enforce authentication on all administrative endpoints."""
    # Check X-Admin-API-Key header
    if x_admin_api_key and x_admin_api_key == settings.ADMIN_API_KEY:
        return

    # Check Authorization: Bearer <key>
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == settings.ADMIN_API_KEY:
            return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: valid admin API key required in 'X-Admin-API-Key' or 'Authorization: Bearer <token>'",
    )


@router.get("/sources", response_model=List[SourceResponse], dependencies=[Depends(verify_admin_auth)])
def list_sources(service: CrawlerService = Depends(get_crawler_service)) -> List[SourceResponse]:
    """List all allowed crawl sources."""
    return service.get_sources()


@router.post("/sources", response_model=SourceResponse, dependencies=[Depends(verify_admin_auth)])
def add_source(source: SourceCreate, service: CrawlerService = Depends(get_crawler_service)) -> SourceResponse:
    """Add or update an allowed crawl source domain."""
    return service.add_source(source)


@router.post("/crawl-jobs", response_model=CrawlJobResponse, dependencies=[Depends(verify_admin_auth)])
def start_crawl_job(job_req: CrawlJobCreate, service: CrawlerService = Depends(get_crawler_service)) -> CrawlJobResponse:
    """Trigger a controlled crawl job and index documents into C++ engine."""
    return service.start_crawl_job(job_req)


@router.get("/crawl-jobs/{job_id}", response_model=CrawlJobResponse, dependencies=[Depends(verify_admin_auth)])
def get_crawl_job_status(job_id: str, service: CrawlerService = Depends(get_crawler_service)) -> CrawlJobResponse:
    """Check status and statistics of a crawl job."""
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Crawl job '{job_id}' not found")
    return job


@router.get("/analytics", response_model=AnalyticsResponse, dependencies=[Depends(verify_admin_auth)])
def get_search_analytics(search_svc=Depends(get_search_service)) -> AnalyticsResponse:
    """Retrieve search query frequencies and index analytics."""
    return search_svc.get_analytics()

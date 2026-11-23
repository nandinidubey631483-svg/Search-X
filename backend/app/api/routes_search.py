"""Public search and document API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import settings
from ..models.schemas import (
    DocumentResponse,
    HealthResponse,
    SearchResponse,
    SuggestionResponse,
)
from ..services.search_service import SearchEngineService

router = APIRouter(tags=["Search"])

# Singleton service instance (can be overridden in tests via app.dependency_overrides)
_search_service = SearchEngineService()


def get_search_service() -> SearchEngineService:
    return _search_service


@router.get("/health", response_model=HealthResponse)
def health_check(service: SearchEngineService = Depends(get_search_service)) -> HealthResponse:
    """System health check and index status."""
    stats = service.get_stats()
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        index_stats=stats,
    )


@router.get("/search", response_model=SearchResponse)
def search_documents(
    q: str = Query(..., min_length=1, description="Search query string"),
    algo: str = Query("bm25", pattern="^(bm25|tf_idf)$", description="Ranking algorithm: bm25 or tf_idf"),
    mode: str = Query("any", pattern="^(any|all)$", description="Candidate match mode: any (OR) or all (AND)"),
    limit: int = Query(10, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: SearchEngineService = Depends(get_search_service),
) -> SearchResponse:
    """Execute ranked document search using C++ core retrieval engine."""
    clean_q = q.strip()
    if not clean_q:
        raise HTTPException(status_code=400, detail="Query cannot be whitespace only")
    return service.search(query=clean_q, algo=algo, mode=mode, limit=limit, offset=offset)


@router.get("/suggestions", response_model=SuggestionResponse)
def get_suggestions(
    q: str = Query(..., min_length=1, description="Prefix to autocomplete"),
    limit: int = Query(5, ge=1, le=20, description="Max suggestions to return"),
    service: SearchEngineService = Depends(get_search_service),
) -> SuggestionResponse:
    """Fetch term autocomplete suggestions from index vocabulary."""
    suggestions = service.get_suggestions(prefix=q, limit=limit)
    return SuggestionResponse(query=q, suggestions=suggestions)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    service: SearchEngineService = Depends(get_search_service),
) -> DocumentResponse:
    """Retrieve document metadata by stable document ID."""
    doc = service.get_document(doc_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    return doc

"""
SearchX FastAPI Application Entrypoint.
Coordinates Search, Crawl Management, and Administration endpoints.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes_admin import router as admin_router
from .api.routes_search import router as search_router
from .config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Educational, industry-inspired document search engine API powered by custom C++ retrieval core.",
)

# CORS middleware for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes under /api
app.include_router(search_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/api/health",
    }

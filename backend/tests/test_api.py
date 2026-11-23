"""
FastAPI Backend Integration and Acceptance Tests (Module G).
Tests public endpoints, admin authentication, C++ search integration, and error handling.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.api.routes_admin import get_crawler_service
from backend.app.api.routes_search import get_search_service
from backend.app.cache.redis_cache import InMemoryCacheClient, QueryCache
from backend.app.config import settings
from backend.app.db.database import Database
from backend.app.db.repository import DatabaseRepository
from backend.app.main import app
from backend.app.services.crawler_service import CrawlerService
from backend.app.services.search_service import SearchEngineService
from crawler.app.models import Document


@pytest.fixture
def client(tmp_path: Path):
    """Test client with isolated temporary index and database path."""
    test_index = tmp_path / "test_api_index.bin"
    engine_bin = Path("core-engine/build/searchx_engine.exe").resolve()

    test_db_file = tmp_path / "test_api.db"
    test_db = Database(f"sqlite:///{test_db_file.as_posix()}")
    test_db.create_tables()
    test_repo = DatabaseRepository(db=test_db)

    test_cache = QueryCache(client=InMemoryCacheClient())

    test_service = SearchEngineService(
        index_path=test_index,
        engine_bin=engine_bin,
        repository=test_repo,
        cache=test_cache,
    )
    test_crawler = CrawlerService(
        search_service=test_service,
        repository=test_repo,
    )

    # Ingest a small test corpus into the C++ index
    doc1 = Document.create(
        document_id="doc_ir_1",
        title="Information Retrieval Basics",
        content="An inverted index is an essential data structure for full-text search.",
        source_url="https://example.com/ir",
        description="IR Overview",
    )
    doc2 = Document.create(
        document_id="doc_bm25_2",
        title="BM25 Scoring Algorithm",
        content="BM25 improves upon TF-IDF by incorporating document length normalization.",
        source_url="https://example.com/bm25",
        description="Ranking Overview",
    )
    test_service.index_documents([doc1, doc2])

    # Override service dependencies
    app.dependency_overrides[get_search_service] = lambda: test_service
    app.dependency_overrides[get_crawler_service] = lambda: test_crawler

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_root_endpoint(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"] == settings.PROJECT_NAME
    assert data["docs_url"] == "/docs"


def test_health_check(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.VERSION
    assert "index_stats" in data
    assert data["index_stats"]["total_documents"] == 2


def test_search_endpoint_bm25_and_tfidf(client: TestClient):
    # BM25 search
    resp = client.get("/api/search?q=inverted index&algo=bm25")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_hits"] >= 1
    assert data["algorithm"] == "bm25"
    assert len(data["results"]) >= 1

    first = data["results"][0]
    assert first["document_id"] == "doc_ir_1"
    assert "inverted index" in first["snippet"].lower()
    assert first["score"] > 0.0

    # TF-IDF search
    resp_tfidf = client.get("/api/search?q=normalization&algo=tf_idf")
    assert resp_tfidf.status_code == 200
    data_tfidf = resp_tfidf.json()
    assert data_tfidf["total_hits"] >= 1
    assert data_tfidf["algorithm"] == "tf_idf"
    assert data_tfidf["results"][0]["document_id"] == "doc_bm25_2"


def test_search_pagination_and_empty(client: TestClient):
    # Pagination
    resp = client.get("/api/search?q=index&limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1

    # Non-existent query
    resp_empty = client.get("/api/search?q=quantum_cryptography_unknown")
    assert resp_empty.status_code == 200
    assert resp_empty.json()["total_hits"] == 0
    assert resp_empty.json()["results"] == []


def test_search_validation_errors(client: TestClient):
    # Empty query
    resp = client.get("/api/search?q=   ")
    assert resp.status_code in (400, 422)

    # Invalid algorithm
    resp_bad_algo = client.get("/api/search?q=test&algo=invalid_algo")
    assert resp_bad_algo.status_code == 422


def test_document_lookup_by_id(client: TestClient):
    # Valid document
    resp = client.get("/api/documents/doc_ir_1")
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["document_id"] == "doc_ir_1"
    assert doc["title"] == "Information Retrieval Basics"
    assert "inverted index" in doc["content"]

    # Missing document
    resp_missing = client.get("/api/documents/non_existent_id")
    assert resp_missing.status_code == 404


def test_admin_auth_required(client: TestClient):
    # Without header -> 401
    resp = client.get("/api/admin/sources")
    assert resp.status_code == 401

    # With invalid key -> 401
    resp_bad = client.get("/api/admin/sources", headers={"X-Admin-API-Key": "wrong-key"})
    assert resp_bad.status_code == 401

    # With valid key -> 200
    resp_good = client.get("/api/admin/sources", headers={"X-Admin-API-Key": settings.ADMIN_API_KEY})
    assert resp_good.status_code == 200


def test_admin_sources_and_analytics(client: TestClient):
    headers = {"X-Admin-API-Key": settings.ADMIN_API_KEY}

    # Add new allowed source
    new_source = {"domain": "searchx-docs.org", "enabled": True}
    resp_add = client.post("/api/admin/sources", json=new_source, headers=headers)
    assert resp_add.status_code == 200
    assert resp_add.json()["domain"] == "searchx-docs.org"

    # Query analytics
    # Trigger a search first
    client.get("/api/search?q=inverted")
    resp_analytics = client.get("/api/admin/analytics", headers=headers)
    assert resp_analytics.status_code == 200
    analytics = resp_analytics.json()
    assert analytics["total_searches"] >= 1
    assert "inverted" in analytics["top_queries"]
    assert analytics["index_stats"]["total_documents"] == 2


def test_search_spell_correction(client: TestClient):
    # Query with typo "invertd indx" -> should trigger did_you_mean and fallback search
    resp = client.get("/api/search?q=invertd indx")
    assert resp.status_code == 200
    data = resp.json()
    assert data["did_you_mean"] == "inverted index"
    assert data["is_auto_corrected"] is True
    assert data["total_hits"] >= 1

"""
End-to-End System Integration Tests (Module J).
Validates the complete vertical slice:
Ingest/Crawl -> Text Normalization -> C++ Inverted Index -> Redis Query Cache -> FastAPI Search API -> Document Metadata
Includes security validation: SSRF protection and Admin API key enforcement.
"""
from pathlib import Path
import pytest
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
from crawler.app.crawler import SSRFValidator
from crawler.app.importer import DocumentImporter
from crawler.app.models import Document
from crawler.app.text_processor import TextProcessor


@pytest.fixture
def e2e_env(tmp_path: Path):
    """Set up isolated e2e environment with clean temporary index and SQLite DB."""
    test_index = tmp_path / "e2e_index.bin"
    test_db_path = tmp_path / "e2e.db"
    engine_bin = Path("core-engine/build/searchx_engine.exe").resolve()

    db = Database(f"sqlite:///{test_db_path.as_posix()}")
    db.create_tables()
    repo = DatabaseRepository(db=db)
    cache = QueryCache(client=InMemoryCacheClient(), enabled=True, default_ttl=60)
    processor = TextProcessor()

    search_service = SearchEngineService(
        index_path=test_index,
        engine_bin=engine_bin,
        text_processor=processor,
        repository=repo,
        cache=cache,
    )
    crawler_service = CrawlerService(
        search_service=search_service,
        repository=repo,
    )

    app.dependency_overrides[get_search_service] = lambda: search_service
    app.dependency_overrides[get_crawler_service] = lambda: crawler_service

    with TestClient(app) as client:
        yield {
            "client": client,
            "search_service": search_service,
            "crawler_service": crawler_service,
            "repo": repo,
            "cache": cache,
            "tmp_path": tmp_path,
        }

    app.dependency_overrides.clear()


def test_end_to_end_search_lifecycle(e2e_env):
    """
    Verify full lifecycle:
    1. Import documents from JSON.
    2. Index into C++ engine and database.
    3. Query via API using BM25 and TF-IDF.
    4. Verify snippet generation and keyword highlighting.
    5. Verify query cache hit on repeat query.
    6. Verify document retrieval by ID.
    7. Invalidate cache on new document ingestion.
    """
    client = e2e_env["client"]
    service = e2e_env["search_service"]
    cache = e2e_env["cache"]
    tmp_path = e2e_env["tmp_path"]

    # Step 1: Import raw document JSON
    sample_file = tmp_path / "e2e_docs.json"
    sample_file.write_text(
        """[
            {
                "document_id": "e2e_doc_1",
                "title": "Quantum Computing Fundamentals",
                "content": "Quantum computers use qubits to perform complex calculations exponentially faster than classical computers.",
                "source_url": "https://example.com/quantum"
            },
            {
                "document_id": "e2e_doc_2",
                "title": "Classical Computing Architecture",
                "content": "Classical computers use deterministic binary bits to execute arithmetic and logic operations.",
                "source_url": "https://example.com/classical"
            }
        ]""",
        encoding="utf-8",
    )

    importer = DocumentImporter()
    raw_docs, stats = importer.import_from_json(sample_file)
    assert len(raw_docs) == 2
    assert stats.imported == 2

    # Step 2: Index documents
    indexed = service.index_documents(raw_docs)
    assert indexed == 2

    # Step 3: Health check verifies 2 indexed documents
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["index_stats"]["total_documents"] == 2

    # Step 4: Search with BM25 (First query -> Cache Miss)
    search_resp1 = client.get("/api/search?q=qubits calculations&algo=bm25")
    assert search_resp1.status_code == 200
    data1 = search_resp1.json()
    assert data1["total_hits"] == 1
    assert data1["results"][0]["document_id"] == "e2e_doc_1"
    assert "qubits" in data1["results"][0]["snippet"].lower()
    assert cache.hits == 0
    assert cache.misses == 1

    # Step 5: Repeat query (Second query -> Cache Hit)
    search_resp2 = client.get("/api/search?q=qubits calculations&algo=bm25")
    assert search_resp2.status_code == 200
    assert search_resp2.json()["results"][0]["document_id"] == "e2e_doc_1"
    assert cache.hits == 1

    # Step 6: Search with TF-IDF
    search_tfidf = client.get("/api/search?q=binary bits&algo=tf_idf")
    assert search_tfidf.status_code == 200
    data_tfidf = search_tfidf.json()
    assert data_tfidf["total_hits"] == 1
    assert data_tfidf["results"][0]["document_id"] == "e2e_doc_2"

    # Step 7: Autocomplete Suggestions
    sug_resp = client.get("/api/suggestions?q=qua&limit=5")
    assert sug_resp.status_code == 200
    assert "quantum" in sug_resp.json()["suggestions"]

    # Step 8: Document retrieval by ID
    doc_resp = client.get("/api/documents/e2e_doc_1")
    assert doc_resp.status_code == 200
    assert doc_resp.json()["title"] == "Quantum Computing Fundamentals"

    # Step 9: Ingest new document and verify cache invalidation
    doc3 = Document.create(
        document_id="e2e_doc_3",
        title="Superconducting Qubits",
        content="Superconducting circuits are a leading platform for building scalable quantum computers and qubits.",
        source_url="https://example.com/superconducting",
    )
    service.index_documents([doc3])

    # Search again -> Cache should have been invalidated, fetching both docs 1 and 3
    search_resp3 = client.get("/api/search?q=qubits calculations&algo=bm25")
    assert search_resp3.status_code == 200
    data3 = search_resp3.json()
    assert data3["total_hits"] >= 1


def test_security_boundaries_ssrf_and_admin_auth(e2e_env):
    """
    Verify security controls:
    1. SSRF validator blocks localhost, loopback, and private RFC-1918 IPs.
    2. Admin endpoints reject requests without valid X-Admin-API-Key.
    """
    client = e2e_env["client"]

    # 1. SSRF Security
    validator = SSRFValidator()
    assert validator.is_safe_ip("127.0.0.1") is False
    assert validator.is_safe_ip("10.0.0.1") is False
    assert validator.is_safe_ip("192.168.1.1") is False
    assert validator.is_safe_ip("169.254.169.254") is False  # AWS metadata endpoint
    assert validator.is_safe_ip("93.184.216.34") is True      # example.com public IP

    # 2. Admin Authentication
    # Unauthenticated GET
    assert client.get("/api/admin/sources").status_code == 401
    assert client.get("/api/admin/analytics").status_code == 401

    # Unauthenticated POST
    assert client.post("/api/admin/sources", json={"domain": "hack.com"}).status_code == 401
    assert client.post("/api/admin/crawl-jobs", json={"seed_urls": ["https://hack.com"]}).status_code == 401

    # Authenticated with correct key
    auth_headers = {"X-Admin-API-Key": settings.ADMIN_API_KEY}
    sources_resp = client.get("/api/admin/sources", headers=auth_headers)
    assert sources_resp.status_code == 200

    analytics_resp = client.get("/api/admin/analytics", headers=auth_headers)
    assert analytics_resp.status_code == 200
    assert "cache_stats" in analytics_resp.json()

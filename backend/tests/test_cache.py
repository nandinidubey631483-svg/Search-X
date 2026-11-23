"""
Unit and integration tests for Redis Query Cache layer (Module H / Cache Milestone).
Verifies:
- Cache key formatting and determinism
- Cache hit and miss accounting
- TTL expiration behavior
- Invalidation upon index updates (preventing stale results)
- Graceful degradation when Redis is down/unreachable
- End-to-end SearchEngineService cache hit/miss and invalidation
"""
import time
from pathlib import Path
import pytest

from backend.app.cache.redis_cache import (
    InMemoryCacheClient,
    QueryCache,
    RedisCacheClient,
)
from backend.app.services.search_service import SearchEngineService
from crawler.app.models import Document


@pytest.fixture
def mem_cache() -> QueryCache:
    """Fixture providing isolated in-memory QueryCache."""
    client = InMemoryCacheClient()
    return QueryCache(client=client, enabled=True, default_ttl=60)


def test_cache_key_generation(mem_cache: QueryCache):
    """Verify deterministic cache key construction."""
    key1 = mem_cache.make_search_key("bm25", "any", 10, 0, ["information", "retrieval"])
    key2 = mem_cache.make_search_key("bm25", "any", 10, 0, ["INFORMATION", "  retrieval  "])
    key_diff_algo = mem_cache.make_search_key("tf_idf", "any", 10, 0, ["information", "retrieval"])
    key_diff_limit = mem_cache.make_search_key("bm25", "any", 20, 0, ["information", "retrieval"])

    assert key1 == key2, "Keys should normalize terms and be case-insensitive"
    assert key1 != key_diff_algo
    assert key1 != key_diff_limit
    assert key1.startswith("searchx:query:bm25:any:10:0:")

    suggest_key = mem_cache.make_suggest_key(" PYTH ", 5)
    assert suggest_key == "searchx:suggest:pyth:5"


def test_cache_hit_and_miss_accounting(mem_cache: QueryCache):
    """Verify hit and miss tracking and serialization."""
    key = "searchx:query:test:key"

    # Initial get is a miss
    assert mem_cache.get_search(key) is None
    assert mem_cache.hits == 0
    assert mem_cache.misses == 1

    # Store search response payload
    sample_data = {
        "query": "python",
        "total_hits": 1,
        "page": 1,
        "limit": 10,
        "algorithm": "bm25",
        "results": [
            {
                "document_id": "doc_1",
                "title": "Python Language",
                "url": "https://python.org",
                "snippet": "Python is a programming language...",
                "score": 1.25,
            }
        ],
    }
    saved = mem_cache.set_search(key, sample_data)
    assert saved is True

    # Subsequent get is a hit
    cached = mem_cache.get_search(key)
    assert cached is not None
    assert cached["query"] == "python"
    assert cached["results"][0]["document_id"] == "doc_1"
    assert mem_cache.hits == 1
    assert mem_cache.misses == 1

    # Hit ratio check
    stats = mem_cache.get_stats()
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.hit_ratio == 0.5
    assert stats.enabled is True


def test_suggestions_caching(mem_cache: QueryCache):
    """Verify autocomplete suggestion caching."""
    key = mem_cache.make_suggest_key("alg", 5)

    assert mem_cache.get_suggest(key) is None
    assert mem_cache.misses == 1

    suggestions = ["algebra", "algorithm", "algorithmic"]
    assert mem_cache.set_suggest(key, suggestions) is True

    cached = mem_cache.get_suggest(key)
    assert cached == suggestions
    assert mem_cache.hits == 1


def test_ttl_expiration(mem_cache: QueryCache):
    """Verify entries expire after TTL elapses."""
    key = "searchx:query:expiring:key"
    mem_cache.set_search(key, {"query": "short_lived"}, ttl=1)

    # Immediate check -> hit
    assert mem_cache.get_search(key) is not None

    # Wait for TTL to expire
    time.sleep(1.1)

    # Post-TTL check -> miss (expired)
    assert mem_cache.get_search(key) is None


def test_cache_invalidation_on_index_update(mem_cache: QueryCache):
    """Verify cache invalidation purges all queries and suggestions."""
    mem_cache.set_search("searchx:query:bm25:any:10:0:hash1", {"query": "test1"})
    mem_cache.set_search("searchx:query:bm25:any:10:0:hash2", {"query": "test2"})
    mem_cache.set_suggest("searchx:suggest:pref:5", ["prefix1", "prefix2"])

    # Non-search key should not be purged
    mem_cache.client.set("searchx:other:keep", "keep_value")

    # Invalidate search cache
    purged = mem_cache.invalidate_search_cache()
    assert purged == 3

    assert mem_cache.get_search("searchx:query:bm25:any:10:0:hash1") is None
    assert mem_cache.get_search("searchx:query:bm25:any:10:0:hash2") is None
    assert mem_cache.get_suggest("searchx:suggest:pref:5") is None
    assert mem_cache.client.get("searchx:other:keep") == "keep_value"


def test_cache_disabled_mode():
    """Verify cache is completely bypassed when enabled=False."""
    cache = QueryCache(client=InMemoryCacheClient(), enabled=False)

    key = "searchx:query:test"
    assert cache.set_search(key, {"data": 123}) is False
    assert cache.get_search(key) is None
    assert cache.hits == 0
    assert cache.misses == 0


def test_graceful_degradation_when_redis_unavailable():
    """Verify system does not crash and degrades to no-op when Redis is down."""
    # Attempt connecting to invalid host/port
    client = RedisCacheClient("redis://127.0.0.1:9999/0")
    assert client.is_available() is False

    cache = QueryCache(client=client, enabled=True)
    assert cache.get_search("searchx:query:test") is None
    assert cache.set_search("searchx:query:test", {"val": 1}) is False
    assert cache.invalidate_search_cache() == 0


def test_search_service_caching_and_invalidation_e2e(tmp_path: Path):
    """
    End-to-end integration test:
    1. First search incurs engine call and cache miss.
    2. Second identical search hits cache.
    3. Indexing a new document invalidates cache.
    4. Third search incurs engine call (cache miss) and returns updated corpus results.
    """
    test_index = tmp_path / "test_cache_service_idx.bin"
    engine_bin = Path("core-engine/build/searchx_engine.exe").resolve()
    cache = QueryCache(client=InMemoryCacheClient(), enabled=True)

    service = SearchEngineService(
        index_path=test_index,
        engine_bin=engine_bin,
        cache=cache,
    )

    doc1 = Document.create(
        document_id="doc_cache_1",
        title="Distributed Systems",
        content="Caching improves retrieval latency and throughput.",
        source_url="https://example.com/caching",
    )
    service.index_documents([doc1])

    # Initial query -> Cache miss (calls engine)
    res1 = service.search(query="caching", algo="bm25")
    assert res1.total_hits == 1
    assert cache.hits == 0
    assert cache.misses == 1

    # Repeat query -> Cache hit (served from cache)
    res2 = service.search(query="caching", algo="bm25")
    assert res2.total_hits == 1
    assert cache.hits == 1
    assert cache.misses == 1
    assert res1.results[0].document_id == res2.results[0].document_id

    # Suggestions caching
    sug_misses_before = cache.misses
    sug1 = service.get_suggestions(prefix="cach", limit=5)
    assert "caching" in sug1
    assert cache.misses == sug_misses_before + 1  # First suggestion lookup is a miss

    sug_hits_before = cache.hits
    sug2 = service.get_suggestions(prefix="cach", limit=5)
    assert sug2 == sug1
    assert cache.hits == sug_hits_before + 1  # Second suggestion lookup is a hit

    # Index new document -> triggers automatic cache invalidation
    doc2 = Document.create(
        document_id="doc_cache_2",
        title="Redis Caching Patterns",
        content="Redis query caching with TTL and invalidation.",
        source_url="https://example.com/redis",
    )
    service.index_documents([doc2])

    # Query again -> Cache miss (because invalidation wiped previous search cache)
    res3 = service.search(query="caching", algo="bm25")
    assert res3.total_hits == 2  # Both doc1 and doc2 matched
    assert cache.misses == sug_misses_before + 2  # New search miss occurred after invalidation

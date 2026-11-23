"""
Redis and In-Memory Query Caching Layer for SearchX.
Complies with PROJECT_CONTEXT.md Module H specifications.

Responsibilities:
- Cache repeated query results and autocomplete suggestions with configurable TTL.
- Enforce cache invalidation upon document indexing to eliminate stale results.
- Provide graceful degradation: when Redis is unreachable, system operates seamlessly as cache-miss.
- Provide in-memory cache client for isolated automated testing without requiring an external Redis server.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from ..config import settings
from ..models.schemas import CacheStats

logger = logging.getLogger("searchx.backend.cache")


class InMemoryCacheClient:
    """Thread-safe in-memory cache with TTL support for testing and local fallback."""

    def __init__(self) -> None:
        self._store: Dict[str, tuple[str, Optional[float]]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            val, expiry = entry
            if expiry is not None and time.time() > expiry:
                del self._store[key]
                return None
            return val

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        with self._lock:
            expiry = (time.time() + ex) if ex is not None else None
            self._store[key] = (value, expiry)
            return True

    def delete(self, *keys: str) -> int:
        with self._lock:
            count = 0
            for k in keys:
                if k in self._store:
                    del self._store[k]
                    count += 1
            return count

    def keys(self, pattern: str = "*") -> List[str]:
        with self._lock:
            now = time.time()
            valid_keys: List[str] = []
            for k, (_, expiry) in list(self._store.items()):
                if expiry is not None and now > expiry:
                    del self._store[k]
                elif fnmatch.fnmatch(k, pattern):
                    valid_keys.append(k)
            return valid_keys

    def flushdb(self) -> bool:
        with self._lock:
            self._store.clear()
            return True

    def is_available(self) -> bool:
        return True


class RedisCacheClient:
    """Real Redis client with non-blocking resilience and graceful fallback."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._redis = None
        self._available = False
        try:
            import redis
            self._redis = redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
            # Test connectivity
            self._redis.ping()
            self._available = True
        except Exception as e:
            logger.warning(f"Redis is unavailable at {url} ({e}); caching will gracefully degrade to no-op.")
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def get(self, key: str) -> Optional[str]:
        if not self._available or not self._redis:
            return None
        try:
            return self._redis.get(key)
        except Exception as e:
            logger.debug(f"Redis get error for {key}: {e}")
            return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if not self._available or not self._redis:
            return False
        try:
            return bool(self._redis.set(key, value, ex=ex))
        except Exception as e:
            logger.debug(f"Redis set error for {key}: {e}")
            return False

    def delete(self, *keys: str) -> int:
        if not self._available or not self._redis or not keys:
            return 0
        try:
            return int(self._redis.delete(*keys))
        except Exception as e:
            logger.debug(f"Redis delete error: {e}")
            return 0

    def keys(self, pattern: str = "*") -> List[str]:
        if not self._available or not self._redis:
            return []
        try:
            return list(self._redis.keys(pattern))
        except Exception as e:
            logger.debug(f"Redis keys error: {e}")
            return []

    def flushdb(self) -> bool:
        if not self._available or not self._redis:
            return False
        try:
            return bool(self._redis.flushdb())
        except Exception as e:
            logger.debug(f"Redis flushdb error: {e}")
            return False


class QueryCache:
    """Coordinates search result and suggestion caching, TTLs, and invalidation."""

    def __init__(
        self,
        client: Optional[Any] = None,
        enabled: Optional[bool] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        self.enabled = settings.CACHE_ENABLED if enabled is None else enabled
        self.default_ttl = settings.CACHE_TTL if default_ttl is None else default_ttl
        self.hits = 0
        self.misses = 0

        if client is not None:
            self.client = client
        elif settings.REDIS_URL.startswith("memory://"):
            self.client = InMemoryCacheClient()
        else:
            self.client = RedisCacheClient(settings.REDIS_URL)

    @staticmethod
    def make_search_key(algo: str, mode: str, limit: int, offset: int, terms: List[str]) -> str:
        """Create a deterministic cache key for search queries."""
        clean_terms = " ".join(t.lower().strip() for t in terms)
        query_hash = hashlib.sha256(clean_terms.encode("utf-8")).hexdigest()[:16]
        return f"searchx:query:{algo}:{mode}:{limit}:{offset}:{query_hash}"

    @staticmethod
    def make_suggest_key(prefix: str, limit: int) -> str:
        """Create a cache key for autocomplete prefix queries."""
        clean_prefix = prefix.lower().strip()
        return f"searchx:suggest:{clean_prefix}:{limit}"

    def get_search(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached search response dict if available."""
        if not self.enabled:
            return None

        val = self.client.get(key)
        if val is not None:
            try:
                self.hits += 1
                return json.loads(val)
            except json.JSONDecodeError:
                self.client.delete(key)

        self.misses += 1
        return None

    def set_search(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store serialized search response dict in cache."""
        if not self.enabled:
            return False

        ex = ttl if ttl is not None else self.default_ttl
        try:
            serialized = json.dumps(data)
            return self.client.set(key, serialized, ex=ex)
        except Exception as e:
            logger.debug(f"Failed to cache search response: {e}")
            return False

    def get_suggest(self, key: str) -> Optional[List[str]]:
        """Retrieve cached suggestions list if available."""
        if not self.enabled:
            return None

        val = self.client.get(key)
        if val is not None:
            try:
                self.hits += 1
                return json.loads(val)
            except json.JSONDecodeError:
                self.client.delete(key)

        self.misses += 1
        return None

    def set_suggest(self, key: str, suggestions: List[str], ttl: Optional[int] = None) -> bool:
        """Store autocomplete suggestions in cache."""
        if not self.enabled:
            return False

        ex = ttl if ttl is not None else self.default_ttl
        try:
            serialized = json.dumps(suggestions)
            return self.client.set(key, serialized, ex=ex)
        except Exception as e:
            logger.debug(f"Failed to cache suggestions: {e}")
            return False

    def invalidate_search_cache(self) -> int:
        """
        Invalidate all query and suggestion cache entries.
        Guarantees stale search results never appear after new documents are indexed.
        """
        query_keys = self.client.keys("searchx:query:*")
        suggest_keys = self.client.keys("searchx:suggest:*")
        all_keys = list(set(query_keys + suggest_keys))
        if all_keys:
            deleted = self.client.delete(*all_keys)
            logger.info(f"Invalidated {deleted} cached search keys upon indexing update.")
            return deleted
        return 0

    def clear(self) -> None:
        """Clear all searchx:* keys in cache."""
        keys = self.client.keys("searchx:*")
        if keys:
            self.client.delete(*keys)

    def get_stats(self) -> CacheStats:
        """Compute cache hit/miss statistics and hit ratio."""
        total = self.hits + self.misses
        ratio = round((self.hits / total), 4) if total > 0 else 0.0
        return CacheStats(
            hits=self.hits,
            misses=self.misses,
            hit_ratio=ratio,
            enabled=self.enabled and self.client.is_available(),
        )


# Default singleton instance
_default_cache = QueryCache()


def get_cache() -> QueryCache:
    return _default_cache

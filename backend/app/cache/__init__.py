"""Redis and in-memory query cache module for SearchX."""
from .redis_cache import QueryCache, get_cache

__all__ = ["QueryCache", "get_cache"]

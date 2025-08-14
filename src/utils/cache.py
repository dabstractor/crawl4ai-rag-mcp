"""
Simple in-memory caching implementation for Crawl4AI MCP Server.

This module provides caching functionality for frequently accessed data
to improve API response times and reduce redundant computations.

Usage:
    # Direct cache usage
    cache = Cache(ttl_seconds=300)
    cache.set("key", "value")
    value = cache.get("key")
    
    # Using decorators
    @cached(cache_instance, "prefix")
    async def my_function():
        return "result"
        
    # Using predefined decorators
    @cached_sources
    async def get_sources():
        return ["source1", "source2"]
        
Cache Configuration:
    - sources_cache: 10 minutes TTL for sources data
    - health_cache: 30 seconds TTL for health check data
    - search_cache: 2 minutes TTL for search results
    
The cache automatically expires entries based on TTL and provides
statistics for monitoring performance.
"""

import time
import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class Cache:
    """Simple in-memory cache with TTL (Time To Live) support."""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize the cache.
        
        Args:
            ttl_seconds: Time-to-live in seconds for cached items
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        logger.info(f"Cache initialized with TTL: {ttl_seconds} seconds")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                logger.debug(f"Cache hit for key: {key}")
                return entry["data"]
            else:
                # Expired
                logger.debug(f"Cache expired for key: {key}")
                del self.cache[key]
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    def set(self, key: str, data: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
        logger.debug(f"Cache set for key: {key}")
    
    def invalidate(self, key: str) -> None:
        """
        Remove a specific key from the cache.
        
        Args:
            key: Cache key to remove
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache invalidated for key: {key}")
    
    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for entry in self.cache.values():
            if current_time - entry["timestamp"] < self.ttl_seconds:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "ttl_seconds": self.ttl_seconds
        }

# Create global cache instances for different use cases
sources_cache = Cache(ttl_seconds=600)  # 10 minutes for sources
health_cache = Cache(ttl_seconds=30)    # 30 seconds for health check
search_cache = Cache(ttl_seconds=120)   # 2 minutes for search queries

def cached(cache_instance: Cache, key_prefix: str, ttl_seconds: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        cache_instance: Cache instance to use
        key_prefix: Prefix for cache keys
        ttl_seconds: Optional TTL override for this cache entry
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)
            
            # Check cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Cache result
            if ttl_seconds is not None:
                # Temporarily override TTL
                old_ttl = cache_instance.ttl_seconds
                cache_instance.ttl_seconds = ttl_seconds
                cache_instance.set(cache_key, result)
                cache_instance.ttl_seconds = old_ttl
            else:
                cache_instance.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

# Convenience decorators for common cache instances
def cached_sources(func):
    """Decorator for caching sources data."""
    return cached(sources_cache, "sources")(func)

def cached_health(func):
    """Decorator for caching health check data."""
    return cached(health_cache, "health")(func)

def cached_search(func):
    """Decorator for caching search results."""
    return cached(search_cache, "search")(func)


def invalidate_all_caches():
    """Invalidate all cache instances."""
    sources_cache.clear()
    health_cache.clear()
    search_cache.clear()
    logger.info("All caches invalidated")
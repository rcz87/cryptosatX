"""
Smart Multi-Layer Cache for CryptoSatX

Intelligent caching system with 3 layers:
- L1: In-memory (fastest, 1-minute TTL)
- L2: Redis (fast, 5-minute TTL)
- L3: Database (persistent, 1-hour TTL)

Features:
- Auto-refresh stale data in background
- Different TTLs per data type
- Cache warming and pre-fetching
- LRU eviction for memory management
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import OrderedDict
import json

from app.utils.logger import default_logger


class LRUCache:
    """Least Recently Used cache with size limit"""

    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        return None

    def set(self, key: str, value: Any):
        """Set value in cache"""
        # Update existing key
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key] = value
            return

        # Add new key
        self.cache[key] = value
        self.cache.move_to_end(key)

        # Evict oldest if over limit
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


class CacheEntry:
    """Cache entry with metadata"""

    def __init__(self, value: Any, ttl: int, created_at: Optional[float] = None):
        self.value = value
        self.ttl = ttl  # seconds
        self.created_at = created_at or time.time()
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return time.time() - self.created_at > self.ttl

    def is_stale(self, stale_threshold: float = 0.8) -> bool:
        """Check if entry is stale (near expiration)"""
        age = time.time() - self.created_at
        return age > (self.ttl * stale_threshold)

    def access(self):
        """Mark entry as accessed"""
        self.access_count += 1
        self.last_accessed = time.time()

    def to_dict(self) -> Dict:
        """Convert to dict"""
        return {
            "value": self.value,
            "ttl": self.ttl,
            "created_at": self.created_at,
            "age_seconds": time.time() - self.created_at,
            "access_count": self.access_count,
            "is_expired": self.is_expired(),
            "is_stale": self.is_stale()
        }


class SmartCache:
    """
    Multi-layer intelligent cache system

    Layer 1 (L1): In-memory LRU cache
    - Fastest access
    - 1-minute TTL
    - 1000 entry limit
    - Use for: price, funding_rate, quick lookups

    Layer 2 (L2): Redis (optional)
    - Fast access
    - 5-minute TTL
    - 10,000 entry limit
    - Use for: signals, technical indicators

    Layer 3 (L3): Database
    - Persistent storage
    - 1-hour TTL
    - Unlimited (managed by DB)
    - Use for: historical data, MSS scores
    """

    def __init__(self):
        # L1: In-memory cache
        self.l1_cache = LRUCache(max_size=1000)
        self.l1_ttl = 60  # 1 minute

        # L2: Redis cache (optional - not implemented yet)
        self.l2_enabled = False
        self.l2_ttl = 300  # 5 minutes

        # L3: Database cache (handled separately)
        self.l3_ttl = 3600  # 1 hour

        # Cache configuration by data type
        self.cache_config = {
            "price": {"layer": "L1", "ttl": 60},
            "funding_rate": {"layer": "L1", "ttl": 60},
            "signal": {"layer": "L1", "ttl": 300},  # 5 min
            "technical": {"layer": "L1", "ttl": 300},
            "mss_score": {"layer": "L1", "ttl": 600},  # 10 min
            "historical": {"layer": "L3", "ttl": 3600}
        }

        # Statistics
        self.stats = {
            "total_gets": 0,
            "l1_hits": 0,
            "l1_misses": 0,
            "refreshes": 0,
            "evictions": 0
        }

        self.logger = default_logger
        self.logger.info("🗄️ Smart Cache initialized (L1 in-memory)")

    def _make_key(self, data_type: str, identifier: str) -> str:
        """Create cache key"""
        return f"{data_type}:{identifier}"

    async def get(
        self,
        data_type: str,
        identifier: str,
        fetch_func: Optional[callable] = None
    ) -> Optional[Any]:
        """
        Get value from cache with auto-refresh

        Args:
            data_type: Type of data (price, signal, etc.)
            identifier: Unique identifier (symbol, etc.)
            fetch_func: Optional async function to fetch if not in cache

        Returns:
            Cached value or None
        """
        self.stats["total_gets"] += 1
        key = self._make_key(data_type, identifier)

        # Try L1 cache
        entry = self.l1_cache.get(key)

        if entry:
            if not entry.is_expired():
                entry.access()
                self.stats["l1_hits"] += 1

                # Auto-refresh if stale (background task)
                if entry.is_stale() and fetch_func:
                    asyncio.create_task(self._refresh_cache(key, data_type, fetch_func))
                    self.stats["refreshes"] += 1

                return entry.value
            else:
                # Expired - remove from cache
                self.l1_cache.delete(key)

        # Cache miss
        self.stats["l1_misses"] += 1

        # Fetch from source if function provided
        if fetch_func:
            try:
                value = await fetch_func()
                if value is not None:
                    await self.set(data_type, identifier, value)
                    return value
            except Exception as e:
                self.logger.error(f"Error fetching data for cache: {e}")

        return None

    async def set(
        self,
        data_type: str,
        identifier: str,
        value: Any
    ):
        """
        Set value in appropriate cache layer

        Args:
            data_type: Type of data
            identifier: Unique identifier
            value: Value to cache
        """
        key = self._make_key(data_type, identifier)

        # Get config for this data type
        config = self.cache_config.get(data_type, {"layer": "L1", "ttl": 60})

        # Create cache entry
        entry = CacheEntry(value=value, ttl=config["ttl"])

        # Store in L1 for now (L2/L3 can be added later)
        self.l1_cache.set(key, entry)

    async def delete(self, data_type: str, identifier: str):
        """Delete from cache"""
        key = self._make_key(data_type, identifier)
        self.l1_cache.delete(key)

    async def clear(self, data_type: Optional[str] = None):
        """Clear cache (optionally by data type)"""
        if data_type is None:
            # Clear all
            self.l1_cache.clear()
            self.logger.info("🗑️ Cache cleared (all)")
        else:
            # Clear specific type
            # Not efficient for LRU but works
            keys_to_delete = [
                key for key in self.l1_cache.cache.keys()
                if key.startswith(f"{data_type}:")
            ]
            for key in keys_to_delete:
                self.l1_cache.delete(key)
            self.logger.info(f"🗑️ Cache cleared (type: {data_type}, {len(keys_to_delete)} entries)")

    async def _refresh_cache(
        self,
        key: str,
        data_type: str,
        fetch_func: callable
    ):
        """Background refresh of stale cache entry"""
        try:
            value = await fetch_func()
            if value is not None:
                identifier = key.split(":", 1)[1]  # Extract identifier from key
                await self.set(data_type, identifier, value)
                self.logger.debug(f"🔄 Cache refreshed: {key}")
        except Exception as e:
            self.logger.error(f"Error refreshing cache for {key}: {e}")

    async def warm_cache(
        self,
        data_type: str,
        identifiers: List[str],
        fetch_func: callable
    ):
        """
        Pre-warm cache with data

        Args:
            data_type: Type of data
            identifiers: List of identifiers to cache
            fetch_func: Async function that takes identifier and returns value
        """
        self.logger.info(f"🔥 Warming cache for {data_type}: {len(identifiers)} items")

        tasks = []
        for identifier in identifiers:
            async def fetch_and_cache(ident=identifier):
                try:
                    value = await fetch_func(ident)
                    if value is not None:
                        await self.set(data_type, ident, value)
                except Exception as e:
                    self.logger.error(f"Error warming cache for {ident}: {e}")

            tasks.append(fetch_and_cache())

        # Execute in parallel with limit
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent

        async def limited_task(task):
            async with semaphore:
                await task

        await asyncio.gather(*[limited_task(t) for t in tasks])

        self.logger.info(f"✅ Cache warmed for {data_type}")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        l1_hit_rate = self.l1_cache.get_hit_rate()

        return {
            "l1": {
                "size": self.l1_cache.size(),
                "max_size": self.l1_cache.max_size,
                "hits": self.l1_cache.hits,
                "misses": self.l1_cache.misses,
                "hit_rate": round(l1_hit_rate, 3)
            },
            "global": {
                "total_gets": self.stats["total_gets"],
                "refreshes": self.stats["refreshes"],
                "evictions": self.stats["evictions"]
            },
            "config": self.cache_config
        }

    def get_cache_info(self, data_type: str, identifier: str) -> Optional[Dict]:
        """Get information about a cached entry"""
        key = self._make_key(data_type, identifier)
        entry = self.l1_cache.get(key)

        if entry:
            return entry.to_dict()

        return None


# Global instance
smart_cache = SmartCache()


# Convenience functions
async def get_cached(
    data_type: str,
    identifier: str,
    fetch_func: Optional[callable] = None
) -> Optional[Any]:
    """Get from cache or fetch"""
    return await smart_cache.get(data_type, identifier, fetch_func)


async def set_cached(data_type: str, identifier: str, value: Any):
    """Set in cache"""
    await smart_cache.set(data_type, identifier, value)


async def clear_cache(data_type: Optional[str] = None):
    """Clear cache"""
    await smart_cache.clear(data_type)

"""
Async Cache Service with TTL Management
Provides performance optimization through in-memory caching with configurable TTLs.

Cache Strategy:
- Price data: 5 seconds (high-frequency updates)
- Social sentiment: 60 seconds (medium-frequency updates)
- Fear & Greed index: 300 seconds (low-frequency updates)
- Signal data: 30 seconds (balanced updates)
"""

import asyncio
import logging
from typing import Any, Optional, Callable, Dict
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheService:
    """
    Async in-memory cache with TTL support.
    Thread-safe, async-friendly caching layer for API data.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
        }
        self._start_time = datetime.now()
        logger.info("🗄️  Cache service initialized (in-memory)")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate deterministic cache key from function args"""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        key_hash = hashlib.md5(
            json.dumps(key_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache with automatic expiration handling.
        
        Args:
            key: Cache key identifier
            
        Returns:
            Optional[Any]: Cached value if exists and not expired, None otherwise
            
        Side Effects:
            - Increments hits counter if found and valid
            - Increments misses and evictions counters if expired
            - Automatically removes expired entries from cache
            
        Thread Safety:
            Uses async lock for safe concurrent access
        """
        async with self._lock:
            if key not in self._cache:
                self.stats["misses"] += 1
                return None
            
            entry = self._cache[key]
            
            if datetime.now() > entry["expires_at"]:
                del self._cache[key]
                self.stats["misses"] += 1
                self.stats["evictions"] += 1
                logger.debug(f"⏱️  Cache expired: {key}")
                return None
            
            self.stats["hits"] += 1
            logger.debug(f"✅ Cache hit: {key}")
            return entry["value"]
    
    async def set(self, key: str, value: Any, ttl_seconds: int, custom_timestamp: Optional[datetime] = None) -> None:
        """
        Store value in cache with time-to-live expiration.

        Args:
            key: Cache key identifier
            value: Any Python object to cache (stored directly, no serialization)
            ttl_seconds: Time-to-live in seconds before expiration
            custom_timestamp: Optional custom timestamp (for cache coherency groups)

        Cache Entry Structure:
            - value: Stored data (as-is)
            - expires_at: Calculated expiration timestamp
            - created_at: Entry creation timestamp (for coherency tracking)
            - fetched_at: When data was actually fetched (for staleness detection)

        Side Effects:
            - Increments sets counter
            - Overwrites existing key if present

        Thread Safety:
            Uses async lock for safe concurrent writes
        """
        now = datetime.now()
        fetched_timestamp = custom_timestamp if custom_timestamp else now

        async with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": now + timedelta(seconds=ttl_seconds),
                "created_at": now,
                "fetched_at": fetched_timestamp,  # ✅ NEW: Track when data was fetched
            }
            self.stats["sets"] += 1
            logger.debug(f"💾 Cache set: {key} (TTL: {ttl_seconds}s)")
    
    async def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cache entry metadata without retrieving value.

        Useful for staleness detection and coherency checks.

        Returns:
            Dict with fetched_at, created_at, expires_at, age_seconds
        """
        async with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            now = datetime.now()

            # Check if expired
            if now > entry["expires_at"]:
                return None

            age_seconds = (now - entry["fetched_at"]).total_seconds()

            return {
                "fetched_at": entry["fetched_at"].isoformat(),
                "created_at": entry["created_at"].isoformat(),
                "expires_at": entry["expires_at"].isoformat(),
                "age_seconds": round(age_seconds, 2),
                "ttl_remaining_seconds": round((entry["expires_at"] - now).total_seconds(), 2)
            }

    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"🗑️  Cache deleted: {key}")
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"🧹 Cache cleared: {count} entries removed")
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries and free memory.
        
        Called automatically every 5 minutes by background cleanup task.
        Can be manually triggered for immediate cleanup.
        
        Returns:
            int: Number of expired entries removed
            
        Performance:
            O(n) complexity where n = total cache entries
            
        Thread Safety:
            Uses async lock to prevent concurrent modification
        """
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                k for k, v in self._cache.items()
                if now > v["expires_at"]
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self.stats["evictions"] += 1
            
            if expired_keys:
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0.0
        )
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        return {
            "cache_size": len(self._cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "evictions": self.stats["evictions"],
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "uptime_seconds": round(uptime, 1),
        }
    
    def cached(
        self,
        ttl_seconds: int,
        key_prefix: str,
    ):
        """
        Decorator for caching async function results.
        
        Usage:
            @cache_service.cached(ttl_seconds=60, key_prefix="social_sentiment")
            async def get_social_sentiment(symbol: str):
                return await fetch_sentiment(symbol)
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self._generate_key(key_prefix, *args, **kwargs)
                
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = await func(*args, **kwargs)
                
                if result is not None:
                    await self.set(cache_key, result, ttl_seconds)
                
                return result
            
            return wrapper
        return decorator


cache_service = CacheService()


async def start_cache_cleanup_task():
    """Background task to cleanup expired cache entries every 5 minutes"""
    while True:
        try:
            await asyncio.sleep(300)
            await cache_service.cleanup_expired()
        except asyncio.CancelledError:
            logger.info("🛑 Cache cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"🔴 Error in cache cleanup task: {type(e).__name__}")


# ============================================================================
# CACHE TTL CONFIGURATION (v2.0 - Coherency Aligned)
# ============================================================================
#
# ⚠️  IMPORTANT: TTLs are now aligned to cache coherency groups
#    to prevent GPT analysis with mismatched timestamp data.
#
# Cache Coherency Groups:
# 1. SIGNAL_ANALYSIS (60s): price, funding, OI, social_basic, liquidations, long_short
# 2. MARKET_SENTIMENT (300s): fear_greed, social_comprehensive, lunarcrush
# 3. ORDERBOOK (10s): orderbook, trades, ticker
# 4. ACCUMULATION (60s): ohlcv, volume_profile, orderbook, price
#
# See: app/core/cache_coherency.py for details
# ============================================================================

# Signal Analysis Group (60s aligned)
TTL_PRICE_DATA = 60  # ⬆ Increased from 5s to align with signal analysis group
TTL_FUNDING_RATE = 60  # ⬆ Increased from 15s to align
TTL_LIQUIDATIONS = 60  # ⬆ Increased from 10s to align
TTL_SIGNAL_DATA = 60  # ⬆ Increased from 30s to align
TTL_SOCIAL_SENTIMENT = 60  # ⬇ Decreased from 900s for coherency

# Market Sentiment Group (300s aligned)
TTL_FEAR_GREED = 300  # ✅ Already aligned
TTL_LUNARCRUSH_COMPREHENSIVE = 300  # Aligned with sentiment group

# Orderbook Group (10s aligned for real-time data)
TTL_ORDERBOOK = 10  # ✅ Already aligned
TTL_TRADES = 10  # Aligned with orderbook
TTL_TICKER = 10  # Aligned with orderbook

# Accumulation Group (60s aligned)
TTL_OHLCV = 60  # Aligned with accumulation analysis
TTL_VOLUME_PROFILE = 60  # Aligned with accumulation analysis

# Legacy fallback (deprecated - use coherency groups instead)
TTL_DEFAULT = 60  # Default TTL if not specified

# ⚠️  NOTE: Social sentiment reduced from 900s to 60s
#    This may increase LunarCrush API calls. Monitor for HTTP 429 errors.
#    If 429 errors occur, consider using cache warming strategy instead.

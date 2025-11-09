"""
Redis Cache Service for CryptoSatX
Provides caching layer for API responses and computed data
"""
import json
import os
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.utils.logger import default_logger


class CacheService:
    """
    Redis-based caching service with TTL support
    Features:
    - Automatic serialization/deserialization
    - TTL management
    - Cache invalidation patterns
    - Performance metrics
    """
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: Optional[redis.Redis] = None
        self.logger = default_logger
        self._connected = False
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            self.logger.info("Redis cache connected successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._connected and self.redis_client is not None
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl_seconds, serialized_value)
            return True
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern
        
        Args:
            pattern: Redis pattern (e.g., "signals:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_connected():
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            self.logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            self.logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for key
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        if not self.is_connected():
            return -2
        
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            self.logger.error(f"Cache TTL error for key {key}: {e}")
            return -2
    
    # Specialized cache methods for CryptoSatX
    
    async def cache_signal(self, symbol: str, signal_data: Dict, ttl_seconds: int = 300) -> bool:
        """
        Cache trading signal data
        
        Args:
            symbol: Cryptocurrency symbol
            signal_data: Signal response data
            ttl_seconds: Cache duration (default: 5 minutes)
            
        Returns:
            True if cached successfully
        """
        key = f"signal:{symbol.upper()}"
        return await self.set(key, signal_data, ttl_seconds)
    
    async def get_cached_signal(self, symbol: str) -> Optional[Dict]:
        """
        Get cached trading signal
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Cached signal data or None
        """
        key = f"signal:{symbol.upper()}"
        return await self.get(key)
    
    async def cache_market_data(self, symbol: str, provider: str, data: Dict, ttl_seconds: int = 900) -> bool:
        """
        Cache market data from specific provider
        
        Args:
            symbol: Cryptocurrency symbol
            provider: Data provider name (coinapi, coinglass, etc.)
            data: Market data
            ttl_seconds: Cache duration (default: 15 minutes)
            
        Returns:
            True if cached successfully
        """
        key = f"market:{provider}:{symbol.upper()}"
        return await self.set(key, data, ttl_seconds)
    
    async def get_cached_market_data(self, symbol: str, provider: str) -> Optional[Dict]:
        """
        Get cached market data
        
        Args:
            symbol: Cryptocurrency symbol
            provider: Data provider name
            
        Returns:
            Cached market data or None
        """
        key = f"market:{provider}:{symbol.upper()}"
        return await self.get(key)
    
    async def cache_social_data(self, symbol: str, data: Dict, ttl_seconds: int = 1800) -> bool:
        """
        Cache social sentiment data
        
        Args:
            symbol: Cryptocurrency symbol
            data: Social sentiment data
            ttl_seconds: Cache duration (default: 30 minutes)
            
        Returns:
            True if cached successfully
        """
        key = f"social:{symbol.upper()}"
        return await self.set(key, data, ttl_seconds)
    
    async def get_cached_social_data(self, symbol: str) -> Optional[Dict]:
        """
        Get cached social sentiment data
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Cached social data or None
        """
        key = f"social:{symbol.upper()}"
        return await self.get(key)
    
    async def invalidate_symbol_cache(self, symbol: str) -> int:
        """
        Invalidate all cache entries for a symbol
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Number of keys invalidated
        """
        symbol = symbol.upper()
        patterns = [
            f"signal:{symbol}",
            f"market:*:{symbol}",
            f"social:{symbol}"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.delete_pattern(pattern)
            total_deleted += deleted
        
        self.logger.info(f"Invalidated {total_deleted} cache entries for {symbol}")
        return total_deleted
    
    async def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.is_connected():
            return {"connected": False}
        
        try:
            info = await self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "used_memory_peak": info.get("used_memory_peak_human", "N/A"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate percentage"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    async def cleanup_expired_keys(self) -> int:
        """
        Manually trigger cleanup of expired keys
        Note: Redis handles this automatically, but this can be useful for monitoring
        
        Returns:
            Number of keys scanned (not necessarily deleted)
        """
        if not self.is_connected():
            return 0
        
        try:
            # This is a rough estimate - Redis doesn't expose exact expired key count
            info = await self.redis_client.info("keyspace")
            total_keys = 0
            for db_stats in info.values():
                if isinstance(db_stats, dict):
                    total_keys += db_stats.get("keys", 0)
            
            self.logger.info(f"Scanned {total_keys} keys for expired entries")
            return total_keys
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return 0


# Singleton instance
cache_service = CacheService()

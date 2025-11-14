"""
Cache Management Routes
Provides endpoints for monitoring cache performance dan manual cache control.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.services.cached_data_service import cached_data_service
from app.core.cache_service import cache_service
from app.utils.logger import default_logger

router = APIRouter()
logger = default_logger


@router.get("/cache/stats", summary="Get Cache Statistics")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get comprehensive cache statistics untuk monitoring performance.
    
    Returns:
    - cache_size: Number of cached entries
    - hits: Total cache hits
    - misses: Total cache misses
    - hit_rate_percent: Cache hit rate percentage
    - total_requests: Total cache requests
    - sets: Total cache writes
    - evictions: Total expired entries removed
    """
    try:
        stats = await cached_data_service.get_cache_stats()
        
        return {
            "ok": True,
            "data": stats,
            "performance_grade": _get_performance_grade(stats["hit_rate_percent"]),
            "recommendations": _get_cache_recommendations(stats),
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")


@router.post("/cache/clear", summary="Clear All Cache")
async def clear_cache() -> Dict[str, Any]:
    """
    Clear all cached data. Use with caution!
    This will force fresh API calls untuk all subsequent requests until cache rebuilds.
    """
    try:
        await cache_service.clear()
        
        return {
            "ok": True,
            "message": "Cache cleared successfully",
            "warning": "All subsequent requests will hit external APIs until cache rebuilds"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.post("/cache/invalidate/{symbol}", summary="Invalidate Symbol Cache")
async def invalidate_symbol_cache(symbol: str) -> Dict[str, Any]:
    """
    Invalidate all cache entries untuk specific cryptocurrency symbol.
    Useful when you need fresh data untuk particular asset.
    
    Args:
    - symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
    """
    try:
        symbol = symbol.upper()
        await cached_data_service.invalidate_symbol_cache(symbol)
        
        return {
            "ok": True,
            "symbol": symbol,
            "message": f"Cache invalidated for {symbol}",
            "affected_keys": [
                "price",
                "liquidations",
                "social_sentiment",
                "long_short_ratio",
                "funding_rate"
            ]
        }
    except Exception as e:
        logger.error(f"Error invalidating cache for {symbol}: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache for {symbol}")


@router.post("/cache/cleanup", summary="Manual Cache Cleanup")
async def manual_cache_cleanup() -> Dict[str, Any]:
    """
    Manually trigger cleanup of expired cache entries.
    Normally runs automatically every 5 minutes.
    """
    try:
        removed_count = await cache_service.cleanup_expired()
        
        return {
            "ok": True,
            "removed_entries": removed_count,
            "message": f"Cleaned up {removed_count} expired cache entries"
        }
    except Exception as e:
        logger.error(f"Error during cache cleanup: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to cleanup cache")


def _get_performance_grade(hit_rate: float) -> str:
    """Calculate performance grade based on cache hit rate"""
    if hit_rate >= 90:
        return "A+ (Excellent)"
    elif hit_rate >= 80:
        return "A (Very Good)"
    elif hit_rate >= 70:
        return "B (Good)"
    elif hit_rate >= 60:
        return "C (Fair)"
    elif hit_rate >= 50:
        return "D (Poor)"
    else:
        return "F (Needs Improvement)"


def _get_cache_recommendations(stats: Dict[str, Any]) -> List[str]:
    """Provide caching recommendations based on statistics"""
    recommendations = []
    hit_rate = stats.get("hit_rate_percent", 0)
    cache_size = stats.get("cache_size", 0)
    
    if hit_rate < 60:
        recommendations.append("Low cache hit rate. Consider increasing TTL values for stable data.")
    
    if cache_size > 10000:
        recommendations.append("Large cache size. Consider reducing TTL atau implementing LRU eviction.")
    
    if cache_size == 0 and stats.get("total_requests", 0) > 0:
        recommendations.append("Cache is empty but receiving requests. Check cache service initialization.")
    
    if hit_rate >= 80:
        recommendations.append("Excellent cache performance! Current TTL values are optimal.")
    
    if not recommendations:
        recommendations.append("Cache performance is within normal parameters.")
    
    return recommendations

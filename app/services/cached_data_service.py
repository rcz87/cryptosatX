"""
Cached Data Service - Performance Optimization Layer
Wraps critical data fetching functions dengan in-memory caching untuk reduce API calls dan improve response time.

Caching Strategy:
- Price data: 5 seconds (real-time updates needed)
- Liquidations: 10 seconds (fast-moving data)
- Funding rate: 15 seconds (moderately fast updates)
- Social sentiment: 60 seconds (slower updates)
- Fear & Greed: 300 seconds (slow-changing indicator)
"""

import logging
from typing import Dict, Any, Optional
from app.core.cache_service import (
    cache_service,
    TTL_PRICE_DATA,
    TTL_SOCIAL_SENTIMENT,
    TTL_FEAR_GREED,
    TTL_FUNDING_RATE,
    TTL_LIQUIDATIONS,
)

logger = logging.getLogger(__name__)


class CachedDataService:
    """
    Cached wrapper untuk critical data fetching functions.
    Provides transparent caching layer dengan automatic TTL management.
    Uses decorator-based caching for consistent key generation.
    """
    
    def __init__(self):
        logger.info("🚀 Cached data service initialized")
    
    @cache_service.cached(ttl_seconds=TTL_PRICE_DATA, key_prefix="price")
    async def get_spot_price_cached(self, symbol: str) -> Dict[str, Any]:
        """
        Get spot price with 5-second cache using decorator-based caching.
        Cache key automatically generated from function args for consistency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with price data from cache or fresh API call
        """
        from app.services.coinapi_service import coinapi_service
        
        logger.debug(f"💸 Price fetch: {symbol}")
        fresh_data = await coinapi_service.get_spot_price(symbol)
        return fresh_data
    
    @cache_service.cached(ttl_seconds=TTL_LIQUIDATIONS, key_prefix="liq")
    async def get_liquidation_data_cached(
        self, symbol: str, exchange: str = "Binance"
    ) -> Dict[str, Any]:
        """
        Get liquidation data with 10-second cache using decorator-based caching.
        
        Args:
            symbol: Cryptocurrency symbol
            exchange: Exchange name
            
        Returns:
            Dict with liquidation data from cache or fresh API call
        """
        from app.services.coinglass_premium_service import coinglass_premium_service
        
        logger.debug(f"💥 Liquidation fetch: {symbol}")
        fresh_data = await coinglass_premium_service.get_liquidation_data(symbol, exchange)
        return fresh_data
    
    @cache_service.cached(ttl_seconds=TTL_FEAR_GREED, key_prefix="fear_greed")
    async def get_fear_greed_cached(self) -> Dict[str, Any]:
        """
        Get Fear & Greed index with 300-second (5-minute) cache using decorator-based caching.
        
        Returns:
            Dict with fear & greed data from cache or fresh API call
        """
        from app.services.coinglass_premium_service import coinglass_premium_service
        
        logger.debug(f"😱 Fear & Greed fetch")
        fresh_data = await coinglass_premium_service.get_fear_greed_index()
        return fresh_data
    
    @cache_service.cached(ttl_seconds=TTL_SOCIAL_SENTIMENT, key_prefix="social")
    async def get_social_sentiment_cached(self, symbol: str) -> Dict[str, Any]:
        """
        Get social sentiment with 60-second (1-minute) cache using decorator-based caching.
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Dict with social sentiment from cache or fresh API call
        """
        from app.services.lunarcrush_service import lunarcrush_service
        
        logger.debug(f"📱 Social sentiment fetch: {symbol}")
        fresh_data = await lunarcrush_service.get_social_score(symbol)
        return fresh_data
    
    @cache_service.cached(ttl_seconds=TTL_FUNDING_RATE, key_prefix="ls_ratio")
    async def get_long_short_ratio_cached(
        self, symbol: str, exchange: str = "Binance"
    ) -> Dict[str, Any]:
        """
        Get long/short ratio with 15-second cache using decorator-based caching.
        
        Args:
            symbol: Cryptocurrency symbol
            exchange: Exchange name
            
        Returns:
            Dict with long/short ratio from cache or fresh API call
        """
        from app.services.coinglass_premium_service import coinglass_premium_service
        
        logger.debug(f"📊 Long/Short ratio fetch: {symbol}")
        fresh_data = await coinglass_premium_service.get_long_short_ratio(symbol, exchange)
        return fresh_data
    
    @cache_service.cached(ttl_seconds=TTL_FUNDING_RATE, key_prefix="funding")
    async def get_funding_rate_cached(
        self, symbol: str, exchange: str = "Binance"
    ) -> Dict[str, Any]:
        """
        Get funding rate with 15-second cache using decorator-based caching.
        
        Args:
            symbol: Cryptocurrency symbol  
            exchange: Exchange name
            
        Returns:
            Dict with funding rate from cache or fresh API call
        """
        from app.services.coinglass_service import coinglass_service
        
        logger.debug(f"💸 Funding rate fetch: {symbol}")
        fresh_data = await coinglass_service.get_funding_and_oi(symbol)
        return fresh_data
    
    async def invalidate_symbol_cache(self, symbol: str) -> int:
        """
        Invalidate all cache entries untuk specific symbol.
        Uses prefix-based matching to catch decorator-generated keys.
        
        Args:
            symbol: Cryptocurrency symbol to invalidate
            
        Returns:
            Number of cache entries invalidated
        """
        symbol = symbol.upper()
        
        async with cache_service._lock:
            keys_to_delete = []
            for cache_key in list(cache_service._cache.keys()):
                if any(prefix in cache_key for prefix in ["price:", "liq:", "social:", "ls_ratio:", "funding:"]):
                    keys_to_delete.append(cache_key)
            
            for key in keys_to_delete:
                del cache_service._cache[key]
                cache_service.stats["evictions"] += 1
        
        logger.info(f"🗑️  Invalidated {len(keys_to_delete)} cache entries for {symbol}")
        return len(keys_to_delete)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics untuk monitoring"""
        return cache_service.get_stats()


cached_data_service = CachedDataService()

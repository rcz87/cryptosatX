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
    """
    
    def __init__(self):
        logger.info("🚀 Cached data service initialized")
    
    async def get_spot_price_cached(self, symbol: str) -> Dict[str, Any]:
        """
        Get spot price with 5-second cache
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with price data from cache or fresh API call
        """
        from app.services.coinapi_service import coinapi_service
        
        cache_key = f"price:{symbol.upper()}"
        cached_data = await cache_service.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"💰 Price cache HIT: {symbol}")
            return cached_data
        
        logger.debug(f"💸 Price cache MISS: {symbol} - fetching fresh data")
        fresh_data = await coinapi_service.get_spot_price(symbol)
        
        if fresh_data.get("success"):
            await cache_service.set(cache_key, fresh_data, TTL_PRICE_DATA)
        
        return fresh_data
    
    async def get_liquidation_data_cached(
        self, symbol: str, exchange: str = "Binance"
    ) -> Dict[str, Any]:
        """
        Get liquidation data with 10-second cache
        
        Args:
            symbol: Cryptocurrency symbol
            exchange: Exchange name
            
        Returns:
            Dict with liquidation data from cache or fresh API call
        """
        from app.services.coinglass_premium_service import coinglass_premium_service
        
        cache_key = f"liq:{symbol.upper()}:{exchange}"
        cached_data = await cache_service.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"💥 Liquidation cache HIT: {symbol}")
            return cached_data
        
        logger.debug(f"💥 Liquidation cache MISS: {symbol} - fetching fresh data")
        fresh_data = await coinglass_premium_service.get_liquidation_data(symbol, exchange)
        
        if fresh_data.get("success"):
            await cache_service.set(cache_key, fresh_data, TTL_LIQUIDATIONS)
        
        return fresh_data
    
    async def get_fear_greed_cached(self) -> Dict[str, Any]:
        """
        Get Fear & Greed index with 300-second (5-minute) cache
        
        Returns:
            Dict with fear & greed data from cache or fresh API call
        """
        from app.services.coinglass_premium_service import coinglass_premium_service
        
        cache_key = "fear_greed:global"
        cached_data = await cache_service.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"😱 Fear & Greed cache HIT")
            return cached_data
        
        logger.debug(f"😱 Fear & Greed cache MISS - fetching fresh data")
        fresh_data = await coinglass_premium_service.get_fear_greed_index()
        
        if fresh_data.get("success"):
            await cache_service.set(cache_key, fresh_data, TTL_FEAR_GREED)
        
        return fresh_data
    
    async def get_social_sentiment_cached(self, symbol: str) -> Dict[str, Any]:
        """
        Get social sentiment with 60-second (1-minute) cache
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Dict with social sentiment from cache or fresh API call
        """
        from app.services.lunarcrush_service import lunarcrush_service
        
        cache_key = f"social:{symbol.upper()}"
        cached_data = await cache_service.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"📱 Social sentiment cache HIT: {symbol}")
            return cached_data
        
        logger.debug(f"📱 Social sentiment cache MISS: {symbol} - fetching fresh data")
        fresh_data = await lunarcrush_service.get_social_score(symbol)
        
        if fresh_data.get("success"):
            await cache_service.set(cache_key, fresh_data, TTL_SOCIAL_SENTIMENT)
        
        return fresh_data
    
    async def get_long_short_ratio_cached(
        self, symbol: str, exchange: str = "Binance"
    ) -> Dict[str, Any]:
        """
        Get long/short ratio with 15-second cache
        
        Args:
            symbol: Cryptocurrency symbol
            exchange: Exchange name
            
        Returns:
            Dict with long/short ratio from cache or fresh API call
        """
        from app.services.coinglass_premium_service import coinglass_premium_service
        
        cache_key = f"ls_ratio:{symbol.upper()}:{exchange}"
        cached_data = await cache_service.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"📊 Long/Short ratio cache HIT: {symbol}")
            return cached_data
        
        logger.debug(f"📊 Long/Short ratio cache MISS: {symbol} - fetching fresh data")
        fresh_data = await coinglass_premium_service.get_long_short_ratio(symbol, exchange)
        
        if fresh_data.get("success"):
            await cache_service.set(cache_key, fresh_data, TTL_FUNDING_RATE)
        
        return fresh_data
    
    async def get_funding_rate_cached(
        self, symbol: str, exchange: str = "Binance"
    ) -> Dict[str, Any]:
        """
        Get funding rate with 15-second cache
        
        Args:
            symbol: Cryptocurrency symbol  
            exchange: Exchange name
            
        Returns:
            Dict with funding rate from cache or fresh API call
        """
        from app.services.coinglass_service import coinglass_service
        
        cache_key = f"funding:{symbol.upper()}:{exchange}"
        cached_data = await cache_service.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"💸 Funding rate cache HIT: {symbol}")
            return cached_data
        
        logger.debug(f"💸 Funding rate cache MISS: {symbol} - fetching fresh data")
        fresh_data = await coinglass_service.get_funding_and_oi(symbol)
        
        if fresh_data.get("success"):
            await cache_service.set(cache_key, fresh_data, TTL_FUNDING_RATE)
        
        return fresh_data
    
    async def invalidate_symbol_cache(self, symbol: str) -> None:
        """
        Invalidate all cache entries untuk specific symbol
        
        Args:
            symbol: Cryptocurrency symbol to invalidate
        """
        symbol = symbol.upper()
        keys_to_delete = [
            f"price:{symbol}",
            f"liq:{symbol}:Binance",
            f"social:{symbol}",
            f"ls_ratio:{symbol}:Binance",
            f"funding:{symbol}:Binance",
        ]
        
        for key in keys_to_delete:
            await cache_service.delete(key)
        
        logger.info(f"🗑️  Invalidated cache for {symbol}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics untuk monitoring"""
        return cache_service.get_stats()


cached_data_service = CachedDataService()

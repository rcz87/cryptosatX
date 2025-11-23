"""
Cache Warming Service
=====================

Pre-loads cache dengan data sebelum GPT analysis untuk:
- Faster response times
- Coherent timestamps
- Reduced API call latency
- Batch optimization

Author: CryptoSatX Intelligence Engine
Version: 1.0.0
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from app.core.cache_coherency import cache_coherency, SIGNAL_ANALYSIS_GROUP
from app.core.cache_service import cache_service
from app.utils.logger import logger


class CacheWarmingService:
    """
    Intelligent cache warming untuk GPT signal analysis.

    Features:
    - Pre-warm cache before GPT analysis
    - Batch warming untuk multiple coins
    - Coherency group warming (all data same timestamp)
    - Smart warming based on usage patterns
    - Background warming tasks
    """

    VERSION = "1.0.0"

    def __init__(self):
        # Warming statistics
        self.stats = {
            "total_warmed": 0,
            "total_coins": 0,
            "total_time_saved": 0.0,
            "cache_hit_improvement": 0.0
        }

        # Track which coins are frequently analyzed
        self._coin_access_counts: Dict[str, int] = {}

        logger.info(f"✅ CacheWarmingService initialized (v{self.VERSION})")

    async def warm_for_gpt_analysis(
        self,
        symbol: str,
        data_fetchers: Optional[Dict[str, Callable]] = None
    ) -> Dict[str, Any]:
        """
        Warm cache untuk GPT signal analysis dengan coherency.

        Pre-fetches all data yang dibutuhkan GPT dalam signal analysis group
        dengan SAME timestamp untuk perfect coherency.

        Args:
            symbol: Crypto symbol to warm
            data_fetchers: Optional dict of custom fetch functions

        Returns:
            Warming result with metadata

        Example:
            >>> result = await cache_warming.warm_for_gpt_analysis("BTC")
            >>> print(result["warmed_members"])  # 6 (all signal analysis group)
            >>> print(result["coherent"])  # True
        """
        logger.info(f"🔥 Warming cache for GPT analysis: {symbol}")

        # Use default fetchers if not provided
        if data_fetchers is None:
            data_fetchers = self._get_default_fetchers(symbol)

        # Warm the signal analysis coherency group
        result = await cache_coherency.warm_group_cache(
            group_name="signal_analysis",
            symbol=symbol,
            fetch_callbacks=data_fetchers
        )

        # Track warming
        self.stats["total_warmed"] += result["warmed_members"]
        self.stats["total_coins"] += 1
        self._coin_access_counts[symbol] = self._coin_access_counts.get(symbol, 0) + 1

        logger.info(
            f"✅ Cache warmed for {symbol}: "
            f"{result['warmed_members']} members, "
            f"{result['failed_members']} failed"
        )

        return result

    async def warm_batch(
        self,
        symbols: List[str],
        max_concurrent: int = 10,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Warm cache untuk multiple coins in parallel.

        Optimized untuk bulk warming before scanning many coins.

        Args:
            symbols: List of symbols to warm
            max_concurrent: Max concurrent warming operations
            progress_callback: Optional callback for progress updates

        Returns:
            Batch warming result

        Example:
            >>> result = await cache_warming.warm_batch(["BTC", "ETH", "SOL"])
            >>> print(f"Warmed {result['successful']}/{result['total']}")
        """
        logger.info(f"🔥 Batch warming {len(symbols)} coins (max_concurrent: {max_concurrent})")

        start_time = asyncio.get_event_loop().time()

        # Create warming tasks
        semaphore = asyncio.Semaphore(max_concurrent)

        async def warm_with_limit(sym: str):
            async with semaphore:
                try:
                    return await self.warm_for_gpt_analysis(sym)
                except Exception as e:
                    logger.error(f"Failed to warm {sym}: {e}")
                    return {"error": str(e), "symbol": sym}

        # Execute all warming tasks
        results = await asyncio.gather(*[warm_with_limit(sym) for sym in symbols])

        # Analyze results
        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]

        elapsed = asyncio.get_event_loop().time() - start_time

        batch_result = {
            "total": len(symbols),
            "successful": len(successful),
            "failed": len(failed),
            "failed_symbols": [r["symbol"] for r in failed],
            "total_time_seconds": round(elapsed, 2),
            "avg_time_per_coin": round(elapsed / len(symbols), 3) if symbols else 0,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(
            f"✅ Batch warming complete: {len(successful)}/{len(symbols)} successful "
            f"in {elapsed:.2f}s"
        )

        # Call progress callback if provided
        if progress_callback:
            await progress_callback(batch_result)

        return batch_result

    async def warm_top_coins(
        self,
        top_n: int = 20,
        coin_provider: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Warm cache untuk top N coins by market cap or volume.

        Args:
            top_n: Number of top coins to warm
            coin_provider: Optional custom coin provider function

        Returns:
            Warming result
        """
        logger.info(f"🔥 Warming top {top_n} coins")

        # Get top coins
        if coin_provider:
            top_coins = await coin_provider(top_n)
        else:
            # Use default top coins provider
            from app.services.top_coins_provider import top_coins_provider
            top_coins = await top_coins_provider.get_top_coins()
            top_coins = top_coins[:top_n]

        # Warm batch
        return await self.warm_batch(top_coins, max_concurrent=10)

    async def warm_frequently_accessed(
        self,
        threshold: int = 3,
        max_coins: int = 50
    ) -> Dict[str, Any]:
        """
        Warm cache untuk coins yang frequently accessed.

        Smart warming based on usage patterns.

        Args:
            threshold: Minimum access count to trigger warming
            max_coins: Max number of coins to warm

        Returns:
            Warming result
        """
        # Get frequently accessed coins
        frequent_coins = [
            symbol for symbol, count in self._coin_access_counts.items()
            if count >= threshold
        ]

        # Sort by access count (most accessed first)
        frequent_coins.sort(
            key=lambda s: self._coin_access_counts[s],
            reverse=True
        )

        # Limit to max_coins
        frequent_coins = frequent_coins[:max_coins]

        if not frequent_coins:
            logger.info("No frequently accessed coins to warm")
            return {
                "total": 0,
                "successful": 0,
                "failed": 0
            }

        logger.info(
            f"🔥 Warming {len(frequent_coins)} frequently accessed coins "
            f"(threshold: {threshold} accesses)"
        )

        return await self.warm_batch(frequent_coins, max_concurrent=10)

    async def background_warming_task(
        self,
        interval_minutes: int = 5,
        top_n: int = 20
    ):
        """
        Background task untuk periodic cache warming.

        Runs indefinitely, warming top coins every N minutes.

        Args:
            interval_minutes: Warming interval
            top_n: Number of top coins to warm

        Usage:
            >>> asyncio.create_task(cache_warming.background_warming_task())
        """
        logger.info(
            f"🔄 Starting background warming task "
            f"(interval: {interval_minutes}min, top_n: {top_n})"
        )

        while True:
            try:
                # Wait first to avoid immediate warming on startup
                await asyncio.sleep(interval_minutes * 60)

                logger.info(f"🔥 Background warming triggered")
                result = await self.warm_top_coins(top_n=top_n)

                logger.info(
                    f"✅ Background warming complete: "
                    f"{result['successful']}/{result['total']} coins warmed"
                )

            except asyncio.CancelledError:
                logger.info("🛑 Background warming task cancelled")
                break
            except Exception as e:
                logger.error(f"🔴 Background warming error: {e}")
                # Continue on error, will retry after interval

    def _get_default_fetchers(self, symbol: str) -> Dict[str, Callable]:
        """
        Get default data fetchers untuk signal analysis group.

        These fetch functions correspond to SIGNAL_ANALYSIS_GROUP members:
        - price
        - funding_rate
        - open_interest
        - social_basic
        - liquidations
        - long_short_ratio
        """
        # Import here to avoid circular dependency
        from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService
        from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService
        from app.services.lunarcrush_service import LunarCrushService

        coinapi = CoinAPIComprehensiveService()
        coinglass = CoinglassComprehensiveService()
        lunarcrush = LunarCrushService()

        return {
            "price": lambda: coinapi.get_spot_price(symbol),
            "funding_rate": lambda: coinglass.get_funding_rate(symbol),
            "open_interest": lambda: coinglass.get_open_interest(symbol),
            "social_basic": lambda: lunarcrush.get_coin_metrics(symbol),
            "liquidations": lambda: coinglass.get_liquidations(symbol),
            "long_short_ratio": lambda: coinglass.get_long_short_ratio(symbol)
        }

    async def estimate_time_savings(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Estimate time savings dari pre-warming vs on-demand fetching.

        Args:
            symbol: Symbol to analyze

        Returns:
            Estimation report
        """
        # Test on-demand fetching time (no cache)
        await cache_service.clear()  # Clear cache

        start = asyncio.get_event_loop().time()
        fetchers = self._get_default_fetchers(symbol)

        # Fetch all sequentially (worst case)
        for fetcher in fetchers.values():
            try:
                await fetcher()
            except:
                pass

        sequential_time = asyncio.get_event_loop().time() - start

        # Test parallel fetching with warming
        await cache_service.clear()

        start = asyncio.get_event_loop().time()
        await self.warm_for_gpt_analysis(symbol)
        parallel_time = asyncio.get_event_loop().time() - start

        # Subsequent access (from cache)
        start = asyncio.get_event_loop().time()
        for key in ["price", "funding_rate", "social_basic"]:
            await cache_service.get(f"{key}:{symbol}")
        cache_access_time = asyncio.get_event_loop().time() - start

        savings = sequential_time - parallel_time
        improvement = (savings / sequential_time * 100) if sequential_time > 0 else 0

        return {
            "symbol": symbol,
            "sequential_fetch_time": round(sequential_time, 3),
            "parallel_warm_time": round(parallel_time, 3),
            "cache_access_time": round(cache_access_time, 3),
            "time_saved_seconds": round(savings, 3),
            "improvement_percent": round(improvement, 1),
            "recommendation": (
                "Warming beneficial" if savings > 0.5
                else "Marginal benefit" if savings > 0.1
                else "Not beneficial"
            )
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get warming statistics"""
        return {
            **self.stats,
            "frequently_accessed_coins": len([
                c for c in self._coin_access_counts.values() if c >= 3
            ]),
            "top_accessed_coins": sorted(
                self._coin_access_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "version": self.VERSION
        }


# Global singleton
cache_warming_service = CacheWarmingService()

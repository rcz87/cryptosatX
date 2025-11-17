"""
Dynamic Top Coins Provider
Fetches and caches top N coins by market cap from multiple sources
Auto-updates daily to keep list fresh
"""
import asyncio
import httpx
from typing import List, Optional
from datetime import datetime, timedelta
from app.utils.logger import default_logger as logger
from app.utils.retry_helper import retry_with_backoff, RetryConfig, CircuitBreaker


class TopCoinsProvider:
    """
    Provides dynamically updated list of top coins by market cap

    Features:
    - Multiple data sources (CoinGecko, Coinglass fallback)
    - Auto-refresh every 24 hours
    - Cached results for performance
    - Retry logic with circuit breaker
    - Fallback to hardcoded list if all sources fail
    """

    def __init__(self, top_n: int = 100, cache_ttl_hours: int = 24):
        self.top_n = top_n
        self.cache_ttl_hours = cache_ttl_hours

        self._cached_coins: Optional[List[str]] = None
        self._cache_timestamp: Optional[datetime] = None

        # Circuit breakers for each source
        self.coingecko_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=300  # 5 minutes
        )

        self.coinglass_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=300
        )

        # Hardcoded fallback (updated manually but serves as safety net)
        self.fallback_top_100 = [
            "BTC", "ETH", "USDT", "BNB", "SOL", "USDC", "XRP", "DOGE", "ADA", "TRX",
            "AVAX", "SHIB", "TON", "DOT", "LINK", "MATIC", "BCH", "ICP", "UNI", "LTC",
            "DAI", "ATOM", "ETC", "FIL", "ARB", "OKB", "APT", "LDO", "OP", "INJ",
            "MKR", "HBAR", "VET", "QNT", "NEAR", "GRT", "AAVE", "STX", "RUNE", "ALGO",
            "FTM", "SAND", "MANA", "XTZ", "EGLD", "THETA", "AXS", "SNX", "EOS", "FLOW",
            "XLM", "APE", "CHZ", "KLAY", "MINA", "CRV", "ZEC", "CFX", "FXS", "CAKE",
            "NEO", "BSV", "ZIL", "DASH", "ENJ", "BAT", "LRC", "GMX", "DYDX", "COMP",
            "GALA", "XMR", "1INCH", "KCS", "WAVES", "HNT", "IOTA", "YFI", "CELO", "NEXO",
            "AR", "FET", "KAVA", "BTT", "ROSE", "IMX", "BLUR", "AUDIO", "ONT", "JST",
            "WOO", "SXP", "ANKR", "RVN", "MASK", "OMG", "ZRX", "BAL", "SKL", "PEOPLE"
        ]

        logger.info(f"TopCoinsProvider initialized: top_{top_n}, cache_ttl={cache_ttl_hours}h")

    async def get_top_coins(self, force_refresh: bool = False) -> List[str]:
        """
        Get top N coins by market cap

        Args:
            force_refresh: Force refresh even if cache is valid

        Returns:
            List of coin symbols
        """
        # Check cache
        if not force_refresh and self._is_cache_valid():
            logger.debug(f"Using cached top {self.top_n} coins")
            return self._cached_coins[:self.top_n]

        # Fetch fresh data
        logger.info(f"Fetching fresh top {self.top_n} coins list...")

        coins = await self._fetch_from_sources()

        if coins:
            # Update cache
            self._cached_coins = coins
            self._cache_timestamp = datetime.utcnow()
            logger.info(f"✅ Updated top coins cache with {len(coins)} coins")
            return coins[:self.top_n]

        # All sources failed - use fallback
        logger.warning("All sources failed - using fallback list")
        return self.fallback_top_100[:self.top_n]

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self._cached_coins or not self._cache_timestamp:
            return False

        age = datetime.utcnow() - self._cache_timestamp
        return age < timedelta(hours=self.cache_ttl_hours)

    async def _fetch_from_sources(self) -> Optional[List[str]]:
        """Try fetching from multiple sources with fallback"""

        # Try CoinGecko first (free, no API key needed)
        coins = await self._fetch_from_coingecko()
        if coins:
            return coins

        # Fallback to Coinglass
        coins = await self._fetch_from_coinglass()
        if coins:
            return coins

        return None

    @retry_with_backoff(
        config=RetryConfig(max_attempts=2, initial_delay=1.0),
        exceptions=(httpx.HTTPError, httpx.TimeoutException)
    )
    async def _fetch_from_coingecko(self) -> Optional[List[str]]:
        """
        Fetch top coins from CoinGecko API

        Endpoint: https://api.coingecko.com/api/v3/coins/markets
        """
        if not self.coingecko_breaker.can_attempt():
            logger.warning("CoinGecko circuit breaker is OPEN")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": self.top_n,
                        "page": 1,
                        "sparkline": "false"
                    }
                )

                if response.status_code != 200:
                    self.coingecko_breaker.record_failure()
                    logger.error(f"CoinGecko API error: {response.status_code}")
                    return None

                data = response.json()

                # Extract symbols and convert to uppercase
                coins = [coin["symbol"].upper() for coin in data if coin.get("symbol")]

                self.coingecko_breaker.record_success()
                logger.info(f"✅ Fetched {len(coins)} coins from CoinGecko")

                return coins

        except Exception as e:
            self.coingecko_breaker.record_failure()
            logger.error(f"CoinGecko fetch failed: {e}")
            return None

    @retry_with_backoff(
        config=RetryConfig(max_attempts=2, initial_delay=1.0),
        exceptions=(httpx.HTTPError, httpx.TimeoutException)
    )
    async def _fetch_from_coinglass(self) -> Optional[List[str]]:
        """
        Fetch top coins from Coinglass (fallback source)

        Uses existing Coinglass service
        """
        if not self.coinglass_breaker.can_attempt():
            logger.warning("Coinglass circuit breaker is OPEN")
            return None

        try:
            from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService

            coinglass = CoinglassComprehensiveService()
            result = await coinglass.get_supported_coins()

            if not result.get("success"):
                self.coinglass_breaker.record_failure()
                return None

            # Get coins and sort by some criteria (if available)
            # For now, just take first N
            coins_data = result.get("data", [])

            if isinstance(coins_data, list):
                coins = [coin.get("symbol", "").upper() for coin in coins_data]
                coins = [c for c in coins if c]  # Filter empty

                self.coinglass_breaker.record_success()
                logger.info(f"✅ Fetched {len(coins)} coins from Coinglass")

                return coins[:self.top_n]

            self.coinglass_breaker.record_failure()
            return None

        except Exception as e:
            self.coinglass_breaker.record_failure()
            logger.error(f"Coinglass fetch failed: {e}")
            return None

    async def force_refresh(self):
        """Force refresh the coin list"""
        logger.info("Force refreshing top coins list...")
        return await self.get_top_coins(force_refresh=True)

    def get_cache_info(self) -> dict:
        """Get cache status information"""
        if not self._cache_timestamp:
            return {
                "cached": False,
                "age_hours": None,
                "coins_count": 0,
                "next_refresh": "pending"
            }

        age = datetime.utcnow() - self._cache_timestamp
        age_hours = age.total_seconds() / 3600
        ttl_remaining = self.cache_ttl_hours - age_hours

        return {
            "cached": True,
            "age_hours": round(age_hours, 2),
            "coins_count": len(self._cached_coins) if self._cached_coins else 0,
            "next_refresh_hours": round(max(0, ttl_remaining), 2),
            "cache_valid": self._is_cache_valid()
        }


# Global instance
top_coins_provider = TopCoinsProvider(top_n=100, cache_ttl_hours=24)

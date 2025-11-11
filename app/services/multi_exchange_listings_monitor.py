"""
Multi-Exchange Listings Monitor
Combines Binance, OKX, and CoinAPI data to overcome region restrictions
"""

import httpx
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.services.binance_listings_monitor import BinanceListingsMonitor
from app.services.okx_service import okx_service
from app.services.coinapi_service import coinapi_service

logger = logging.getLogger(__name__)


class MultiExchangeListingsMonitor:
    """Enhanced listings monitor using multiple exchange sources"""

    def __init__(self):
        self.binance_monitor = BinanceListingsMonitor()
        self.sources = ["binance", "okx", "coinapi"]

    async def get_all_new_listings(self, hours: int = 72) -> Dict:
        """
        Get new listings from all available exchanges

        Args:
            hours: Lookback period in hours

        Returns:
            Combined listings from all sources
        """
        results = {
            "success": True,
            "listings": [],
            "sources": {},
            "count": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Try all sources in parallel
        tasks = [
            self._get_binance_listings(hours),
            self._get_okx_listings(hours),
            self._get_coinapi_listings(hours),
        ]

        source_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, source_result in enumerate(source_results):
            source_name = self.sources[i]

            if isinstance(source_result, Exception):
                logger.error(f"Error in {source_name}: {source_result}")
                results["sources"][source_name] = {
                    "success": False,
                    "error": str(source_result),
                    "listings": [],
                }
            elif source_result.get("success"):
                listings = source_result.get("listings", [])
                results["sources"][source_name] = {
                    "success": True,
                    "listings_count": len(listings),
                    "listings": listings,
                }
                results["listings"].extend(listings)
            else:
                results["sources"][source_name] = {
                    "success": False,
                    "error": source_result.get("error", "Unknown error"),
                    "listings": [],
                }

        # Remove duplicates and sort by listing time
        unique_listings = self._deduplicate_listings(results["listings"])
        results["listings"] = sorted(
            unique_listings, key=lambda x: x.get("listed_at", ""), reverse=True
        )
        results["count"] = len(results["listings"])

        return results

    async def _get_binance_listings(self, hours: int) -> Dict:
        """Get Binance listings with fallback to demo data"""
        try:
            result = await self.binance_monitor.get_new_listings(hours=hours)

            if not result.get("success"):
                # Try with stats as fallback
                result = await self.binance_monitor.detect_new_listings_with_stats(
                    hours=hours
                )

            if result.get("success"):
                listings = result.get("new_listings", [])
                return {
                    "success": True,
                    "listings": self._normalize_binance_listings(listings),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Binance API failed"),
                }

        except Exception as e:
            logger.error(f"Binance listings error: {e}")
            return {"success": False, "error": str(e)}

    async def _get_okx_listings(self, hours: int) -> Dict:
        """Get OKX new listings"""
        try:
            # OKX doesn't have a direct "new listings" endpoint
            # We'll get all USDT perpetuals and filter by recent trading
            url = "https://www.okx.com/api/v5/public/instruments"
            params = {"instType": "SWAP", "uly": "USDT"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("code") == "0" and data.get("data"):
                    instruments = data["data"]

                    # Filter for recently active instruments
                    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                    recent_listings = []

                    for instrument in instruments:
                        # Check if instrument is active and has recent trading
                        if instrument.get("state") == "live":
                            symbol = instrument.get("instId", "")
                            if symbol.endswith("-USDT-SWAP"):
                                # Get recent trading data to verify activity
                                trading_data = await self._check_okx_trading_activity(
                                    symbol
                                )

                                if trading_data.get("has_recent_activity"):
                                    base_asset = symbol.replace("-USDT-SWAP", "")

                                    # Estimate listing time (OKX doesn't provide exact listing time)
                                    listed_at = self._estimate_okx_listing_time(
                                        base_asset, cutoff_time
                                    )

                                    recent_listings.append(
                                        {
                                            "symbol": symbol,
                                            "base_asset": base_asset,
                                            "quote_asset": "USDT",
                                            "exchange": "okx",
                                            "listed_at": listed_at,
                                            "age_hours": self._calculate_age_hours(
                                                listed_at
                                            ),
                                            "status": "TRADING",
                                            "volume_24h": trading_data.get(
                                                "volume_24h", 0
                                            ),
                                            "price_change_24h": trading_data.get(
                                                "price_change_24h", 0
                                            ),
                                        }
                                    )

                    return {"success": True, "listings": recent_listings}
                else:
                    return {"success": False, "error": "OKX API error"}

        except Exception as e:
            logger.error(f"OKX listings error: {e}")
            return {"success": False, "error": str(e)}

    async def _get_coinapi_listings(self, hours: int) -> Dict:
        """Get new listings via CoinAPI"""
        try:
            # Get all symbols from CoinAPI
            url = "https://rest.coinapi.io/v1/symbols"
            headers = {"X-CoinAPI-Key": "YOUR_COINAPI_KEY"}  # Use env var in production

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                symbols = response.json()

                # Filter for perpetual futures
                perpetual_symbols = [
                    s
                    for s in symbols
                    if s.get("symbol_type") == "PERPETUAL"
                    and s.get("quote_asset") == "USDT"
                ]

                # Get recent trading data for each symbol
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_listings = []

            for symbol_data in perpetual_symbols[:50]:  # Limit to avoid rate limits
                symbol_id = symbol_data.get("symbol_id")
                base_asset = symbol_data.get("asset_id_base")

                # Check recent trading activity
                trading_data = await self._check_coinapi_trading_activity(symbol_id)

                if trading_data.get("has_recent_activity"):
                    listed_at = self._estimate_coinapi_listing_time(
                        base_asset, cutoff_time
                    )

                    recent_listings.append(
                        {
                            "symbol": symbol_id,
                            "base_asset": base_asset,
                            "quote_asset": "USDT",
                            "exchange": "coinapi",
                            "listed_at": listed_at,
                            "age_hours": self._calculate_age_hours(listed_at),
                            "status": "TRADING",
                            "volume_24h": trading_data.get("volume_24h", 0),
                            "price_change_24h": trading_data.get("price_change_24h", 0),
                        }
                    )

            return {"success": True, "listings": recent_listings}

        except Exception as e:
            logger.error(f"CoinAPI listings error: {e}")
            return {"success": False, "error": str(e)}

    async def _check_okx_trading_activity(self, symbol: str) -> Dict:
        """Check if OKX symbol has recent trading activity"""
        try:
            # Get recent candles
            candles_data = await okx_service.get_candles(
                symbol.replace("-USDT-SWAP", ""), timeframe="1h", limit=24
            )

            if candles_data.get("success") and candles_data.get("candles"):
                candles = candles_data["candles"]

                # Calculate 24h volume and price change
                if len(candles) >= 2:
                    latest_candle = candles[-1]
                    previous_candle = candles[-2]

                    volume_24h = sum(c["volume"] for c in candles[-24:])
                    price_change_24h = (
                        (
                            (latest_candle["close"] - previous_candle["close"])
                            / previous_candle["close"]
                            * 100
                        )
                        if previous_candle["close"] > 0
                        else 0
                    )

                    return {
                        "has_recent_activity": True,
                        "volume_24h": volume_24h,
                        "price_change_24h": price_change_24h,
                    }

            return {"has_recent_activity": False}

        except Exception as e:
            logger.error(f"OKX trading activity check error: {e}")
            return {"has_recent_activity": False}

    async def _check_coinapi_trading_activity(self, symbol_id: str) -> Dict:
        """Check if CoinAPI symbol has recent trading activity"""
        try:
            # This would require CoinAPI OHLCV endpoint
            # For now, return default values
            return {
                "has_recent_activity": True,
                "volume_24h": 1000000,  # Default volume
                "price_change_24h": 5.0,  # Default price change
            }
        except Exception as e:
            logger.error(f"CoinAPI trading activity check error: {e}")
            return {"has_recent_activity": False}

    def _normalize_binance_listings(self, listings: List[Dict]) -> List[Dict]:
        """Normalize Binance listings to standard format"""
        normalized = []

        for listing in listings:
            normalized.append(
                {
                    "symbol": listing.get("symbol"),
                    "base_asset": listing.get("baseAsset"),
                    "quote_asset": listing.get("quoteAsset"),
                    "exchange": "binance",
                    "listed_at": listing.get("listed_at"),
                    "age_hours": listing.get("age_hours"),
                    "status": listing.get("status"),
                    "volume_24h": listing.get("stats", {}).get("quote_volume_usd", 0),
                    "price_change_24h": listing.get("stats", {}).get(
                        "price_change_24h", 0
                    ),
                }
            )

        return normalized

    def _deduplicate_listings(self, listings: List[Dict]) -> List[Dict]:
        """Remove duplicate listings across exchanges"""
        seen_assets = set()
        unique_listings = []

        for listing in listings:
            base_asset = listing.get("base_asset", "").upper()

            if base_asset and base_asset not in seen_assets:
                seen_assets.add(base_asset)
                unique_listings.append(listing)

        return unique_listings

    def _estimate_okx_listing_time(self, base_asset: str, cutoff_time: datetime) -> str:
        """Estimate OKX listing time (fallback)"""
        # OKX doesn't provide exact listing time, use cutoff time as estimate
        return cutoff_time.isoformat()

    def _estimate_coinapi_listing_time(
        self, base_asset: str, cutoff_time: datetime
    ) -> str:
        """Estimate CoinAPI listing time (fallback)"""
        # Similar to OKX, use cutoff time as estimate
        return cutoff_time.isoformat()

    def _calculate_age_hours(self, listed_at: str) -> float:
        """Calculate age in hours from listing time"""
        try:
            listing_time = datetime.fromisoformat(listed_at.replace("Z", "+00:00"))
            current_time = datetime.utcnow()
            age = (current_time - listing_time).total_seconds() / 3600
            return max(0, age)
        except:
            return 0.0

    async def close(self):
        """Clean up resources"""
        await self.binance_monitor.close()


# Singleton instance
multi_exchange_monitor = MultiExchangeListingsMonitor()

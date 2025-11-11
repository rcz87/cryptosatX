"""
Binance New Listings Monitor
Automatically detect and analyze new perpetual futures listings on Binance
"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio


class BinanceListingsMonitor:
    """
    Monitor Binance for new perpetual futures listings
    Auto-trigger MSS analysis for early entry signals
    """

    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self._client: Optional[httpx.AsyncClient] = None
        self._known_symbols: set = set()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=10.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._client

    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_all_perpetual_symbols(self) -> Dict:
        """
        Get all current perpetual futures symbols from Binance
        Returns list of USDT perpetual pairs
        """
        try:
            client = await self._get_client()

            # Get exchange info with timeout
            response = await client.get(
                f"{self.base_url}/fapi/v1/exchangeInfo",
                timeout=5.0,  # Shorter timeout for faster failure
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Binance API HTTP {response.status_code} - Service may be unavailable",
                }

            data = response.json()
            symbols = data.get("symbols", [])

            # Filter for USDT perpetual pairs that are trading
            perpetual_symbols = []
            for symbol_info in symbols:
                symbol = symbol_info.get("symbol", "")
                status = symbol_info.get("status", "")
                contract_type = symbol_info.get("contractType", "")

                # Only USDT perpetuals that are trading
                if (
                    symbol.endswith("USDT")
                    and status == "TRADING"
                    and contract_type == "PERPETUAL"
                ):

                    perpetual_symbols.append(
                        {
                            "symbol": symbol,
                            "baseAsset": symbol_info.get("baseAsset", ""),
                            "quoteAsset": symbol_info.get("quoteAsset", ""),
                            "onboardDate": symbol_info.get("onboardDate"),
                            "status": status,
                        }
                    )

            return {
                "success": True,
                "symbols": perpetual_symbols,
                "total": len(perpetual_symbols),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except httpx.ConnectTimeout:
            return {
                "success": False,
                "error": "Binance API timeout - Check network connection or firewall settings",
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"Binance API connection error: {str(e)}",
            }
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    async def get_demo_new_listings(self, hours: int = 72) -> Dict:
        """
        Demo fallback data when Binance API is unavailable
        Returns sample new listings for testing
        """
        # Sample demo data for testing
        demo_listings = [
            {
                "symbol": "ZKUSDT",
                "baseAsset": "ZK",
                "quoteAsset": "USDT",
                "onboardDate": int(
                    (datetime.utcnow() - timedelta(hours=36)).timestamp() * 1000
                ),
                "status": "TRADING",
                "age_hours": 36.5,
                "listed_at": (datetime.utcnow() - timedelta(hours=36.5)).isoformat(),
                "stats": {
                    "price_change_24h": 12.5,
                    "quote_volume_usd": 152750000,
                    "trades_24h": 45231,
                    "current_price": 0.2456,
                },
            },
            {
                "symbol": "PORTALUSDT",
                "baseAsset": "PORTAL",
                "quoteAsset": "USDT",
                "onboardDate": int(
                    (datetime.utcnow() - timedelta(hours=48)).timestamp() * 1000
                ),
                "status": "TRADING",
                "age_hours": 48.2,
                "listed_at": (datetime.utcnow() - timedelta(hours=48.2)).isoformat(),
                "stats": {
                    "price_change_24h": 8.3,
                    "quote_volume_usd": 89500000,
                    "trades_24h": 32156,
                    "current_price": 1.234,
                },
            },
            {
                "symbol": "AEVOUSDT",
                "baseAsset": "AEVO",
                "quoteAsset": "USDT",
                "onboardDate": int(
                    (datetime.utcnow() - timedelta(hours=72)).timestamp() * 1000
                ),
                "status": "TRADING",
                "age_hours": 72.1,
                "listed_at": (datetime.utcnow() - timedelta(hours=72.1)).isoformat(),
                "stats": {
                    "price_change_24h": -2.1,
                    "quote_volume_usd": 45600000,
                    "trades_24h": 18923,
                    "current_price": 0.789,
                },
            },
        ]

        # Filter by hours
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        filtered_listings = [
            listing
            for listing in demo_listings
            if datetime.fromisoformat(listing["listed_at"].replace("Z", "+00:00"))
            >= cutoff_time
        ]

        return {
            "success": True,
            "new_listings": filtered_listings,
            "count": len(filtered_listings),
            "lookback_hours": hours,
            "demo_mode": True,
            "message": "Demo data - Binance API unavailable",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_new_listings(self, hours: int = 72) -> Dict:
        """
        Get perpetual futures listed in the last N hours

        Args:
            hours: Look back period in hours (default 72 = 3 days)

        Returns:
            List of newly listed perpetual contracts
        """
        try:
            # Get all symbols
            result = await self.get_all_perpetual_symbols()

            if not result.get("success"):
                return result

            all_symbols = result.get("symbols", [])

            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            cutoff_timestamp = int(cutoff_time.timestamp() * 1000)

            # Filter by onboard date
            new_listings = []
            for symbol_info in all_symbols:
                onboard_date = symbol_info.get("onboardDate")

                if onboard_date and onboard_date >= cutoff_timestamp:
                    # Calculate age in hours
                    age_ms = datetime.utcnow().timestamp() * 1000 - onboard_date
                    age_hours = age_ms / (1000 * 60 * 60)

                    symbol_info["age_hours"] = round(age_hours, 1)
                    symbol_info["listed_at"] = datetime.fromtimestamp(
                        onboard_date / 1000
                    ).isoformat()

                    new_listings.append(symbol_info)

            # Sort by onboard date (newest first)
            new_listings.sort(key=lambda x: x.get("onboardDate", 0), reverse=True)

            return {
                "success": True,
                "new_listings": new_listings,
                "count": len(new_listings),
                "lookback_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_24h_stats(self, symbol: str) -> Dict:
        """
        Get 24h ticker stats for a symbol
        Useful for detecting volume spikes on new listings
        """
        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.base_url}/fapi/v1/ticker/24hr", params={"symbol": symbol}
            )

            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}

            data = response.json()

            return {
                "success": True,
                "symbol": symbol,
                "price_change_percent": float(data.get("priceChangePercent", 0)),
                "volume": float(data.get("volume", 0)),
                "quote_volume": float(data.get("quoteVolume", 0)),
                "high_price": float(data.get("highPrice", 0)),
                "low_price": float(data.get("lowPrice", 0)),
                "last_price": float(data.get("lastPrice", 0)),
                "count": int(data.get("count", 0)),  # Number of trades
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def detect_new_listings_with_stats(self, hours: int = 24) -> Dict:
        """
        Detect new listings and enrich with trading stats
        Perfect for identifying early entry opportunities

        Args:
            hours: Look back period (default 24h for very recent)

        Returns:
            New listings with volume, price change, and trade activity
        """
        try:
            # Get new listings
            listings_result = await self.get_new_listings(hours=hours)

            if not listings_result.get("success"):
                # Fallback to demo data if Binance API unavailable
                return await self.get_demo_new_listings(hours=hours)

            new_listings = listings_result.get("new_listings", [])

            if not new_listings:
                return {
                    "success": True,
                    "new_listings": [],
                    "count": 0,
                    "message": f"No new listings in the last {hours} hours",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Fetch stats for each new listing concurrently
            enriched_listings = []

            for listing in new_listings:
                symbol = listing.get("symbol")

                # Get 24h stats
                stats = await self.get_24h_stats(symbol)

                if stats.get("success"):
                    listing["stats"] = {
                        "price_change_24h": stats.get("price_change_percent"),
                        "volume_24h": stats.get("volume"),
                        "quote_volume_usd": stats.get("quote_volume"),
                        "trades_24h": stats.get("count"),
                        "current_price": stats.get("last_price"),
                    }
                else:
                    listing["stats"] = None

                enriched_listings.append(listing)

            # Sort by quote volume (highest first) - proxy for retail interest
            enriched_listings.sort(
                key=lambda x: (
                    x.get("stats", {}).get("quote_volume_usd", 0)
                    if x.get("stats")
                    else 0
                ),
                reverse=True,
            )

            return {
                "success": True,
                "new_listings": enriched_listings,
                "count": len(enriched_listings),
                "lookback_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

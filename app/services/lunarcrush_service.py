"""
LunarCrush Service
Provides social sentiment and community engagement metrics
"""

import os
import httpx
from typing import Dict, Optional


class LunarCrushService:
    """Service for interacting with LunarCrush API"""

    def __init__(self):
        self.api_key = os.getenv("LUNARCRUSH_API_KEY", "")
        self.base_url = "https://lunarcrush.com/api4/public"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def get_social_score(self, symbol: str) -> Dict:
        """
        Get social sentiment score for a cryptocurrency

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with symbol and socialScore (0-100 scale)
        """
        try:
            # Normalize symbol
            symbol = symbol.upper()

            # LunarCrush endpoint for coin metrics
            # Note: Individual coin endpoint only has /v1 (v2 only exists for /list)
            url = f"{self.base_url}/coins/{symbol}/v1"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()

                # Extract social score metrics
                social_score = 0.0
                if data.get("data"):
                    coin_data = data["data"]
                    # LunarCrush provides galaxy_score (0-100) and alt_rank
                    # We'll use galaxy_score as our social score
                    social_score = float(coin_data.get("galaxy_score", 0))

                    # Alternative: combine multiple metrics
                    # social_volume = coin_data.get("social_volume", 0)
                    # sentiment = coin_data.get("average_sentiment", 0)

                return {
                    "symbol": symbol,
                    "socialScore": social_score,
                    "source": "lunarcrush",
                    "success": True,
                }

        except httpx.HTTPStatusError as e:
            print(f"LunarCrush HTTP error for {symbol}: {e}")
            return self._get_default_response(
                symbol, f"HTTP error: {e.response.status_code}"
            )
        except httpx.RequestError as e:
            print(f"LunarCrush request error for {symbol}: {e}")
            return self._get_default_response(symbol, f"Request error: {str(e)}")
        except Exception as e:
            print(f"LunarCrush unexpected error for {symbol}: {e}")
            return self._get_default_response(symbol, f"Unexpected error: {str(e)}")

    def _get_default_response(self, symbol: str, error: str = "") -> Dict:
        """Return safe default response on error"""
        return {
            "symbol": symbol,
            "socialScore": 50.0,  # Neutral score on error
            "source": "lunarcrush",
            "success": False,
            "error": error,
        }

    async def get_market_data(self, symbol: str) -> Dict:
        """
        Get comprehensive market data for a symbol
        This method provides all available LunarCrush data in one call

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with comprehensive market data
        """
        try:
            # Get social score data
            social_data = await self.get_social_score(symbol)

            if not social_data.get("success"):
                return social_data

            # Add additional market metrics
            market_data = {
                "symbol": symbol,
                "socialScore": social_data.get("socialScore", 50.0),
                "source": "lunarcrush",
                "success": True,
                "metrics": {
                    "socialScore": social_data.get("socialScore", 50.0),
                    "sentiment": "neutral",  # Default sentiment
                },
            }

            return market_data

        except Exception as e:
            print(f"LunarCrush market data error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "socialScore": 50.0,
                "source": "lunarcrush",
                "success": False,
                "error": str(e),
            }

    async def get_coins_list(
        self,
        limit: int = 100,
        sort: str = "market_cap_rank",
        min_galaxy_score: Optional[float] = None,
        max_alt_rank: Optional[int] = None,
        min_sentiment: Optional[float] = None,
        min_social_volume: Optional[int] = None,
        categories: Optional[str] = None,
    ) -> Dict:
        """
        Get list of coins with comprehensive LunarCrush metrics (API v4)
        
        Total coins available: 7,634+
        
        Args:
            limit: Number of coins to return (default: 100, max: 1000)
            sort: Sort field (market_cap_rank, galaxy_score, alt_rank, social_volume_24h)
            min_galaxy_score: Minimum galaxy score (0-100)
            max_alt_rank: Maximum alt rank (lower is better)
            min_sentiment: Minimum sentiment score (0-100)
            min_social_volume: Minimum 24h social volume
            categories: Filter by categories (e.g., "layer-1,defi")
        
        Returns:
            Dict with coins list and rich metadata including:
            - Galaxy Score (LunarCrush quality metric)
            - AltRank (momentum indicator)
            - Social metrics (volume, dominance, interactions)
            - Market data (price, market cap, volume)
            - Sentiment scores
        """
        try:
            url = f"{self.base_url}/coins/list/v1"
            
            # Build query parameters
            params = {
                "limit": min(limit, 1000),
                "sort": sort,
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get("data"):
                    return {
                        "success": False,
                        "error": "No data returned from API",
                    }
                
                coins = data["data"]
                
                # Apply filters
                if min_galaxy_score is not None:
                    coins = [c for c in coins if c.get("galaxy_score", 0) >= min_galaxy_score]
                
                if max_alt_rank is not None:
                    coins = [c for c in coins if c.get("alt_rank", 9999) <= max_alt_rank]
                
                if min_sentiment is not None:
                    coins = [c for c in coins if c.get("sentiment", 0) >= min_sentiment]
                
                if min_social_volume is not None:
                    coins = [c for c in coins if c.get("social_volume_24h", 0) >= min_social_volume]
                
                if categories:
                    category_list = [cat.strip().lower() for cat in categories.split(",")]
                    coins = [
                        c for c in coins 
                        if any(cat in c.get("categories", "").lower() for cat in category_list)
                    ]
                
                # Build response
                return {
                    "success": True,
                    "config": data.get("config", {}),
                    "totalCoins": len(coins),
                    "totalAvailable": data.get("config", {}).get("total_rows", 0),
                    "filters": {
                        "min_galaxy_score": min_galaxy_score,
                        "max_alt_rank": max_alt_rank,
                        "min_sentiment": min_sentiment,
                        "min_social_volume": min_social_volume,
                        "categories": categories,
                    },
                    "coins": coins,
                }
        
        except httpx.HTTPStatusError as e:
            print(f"LunarCrush coins list HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
            }
        except Exception as e:
            print(f"LunarCrush coins list error: {e}")
            return {
                "success": False,
                "error": str(e),
            }


# Singleton instance
lunarcrush_service = LunarCrushService()

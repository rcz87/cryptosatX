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


# Singleton instance
lunarcrush_service = LunarCrushService()

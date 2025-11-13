"""
CoinAPI Service
Provides real-time spot price data for cryptocurrencies
"""

import os
import httpx
from typing import Dict, Optional


class CoinAPIService:
    """Service for interacting with CoinAPI"""

    def __init__(self):
        self.api_key = os.getenv("COINAPI_KEY", "")
        self.base_url = "https://rest.coinapi.io/v1"
        self.headers = {"X-CoinAPI-Key": self.api_key}

    async def get_spot_price(self, symbol: str) -> Dict:
        """
        Get spot price for a given cryptocurrency symbol

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with symbol, price, and source
        """
        try:
            # Normalize symbol to uppercase
            symbol = symbol.upper()

            # CoinAPI endpoint for exchange rate
            url = f"{self.base_url}/exchangerate/{symbol}/USDT"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()

                return {
                    "symbol": symbol,
                    "price": float(data.get("rate", 0)),
                    "source": "coinapi",
                    "success": True,
                }

        except httpx.HTTPStatusError as e:
            print(f"CoinAPI HTTP error for {symbol}: {e}")
            return self._get_default_response(
                symbol, f"HTTP error: {e.response.status_code}"
            )
        except httpx.RequestError as e:
            print(f"CoinAPI request error for {symbol}: {e}")
            return self._get_default_response(symbol, f"Request error: {str(e)}")
        except Exception as e:
            print(f"CoinAPI unexpected error for {symbol}: {e}")
            return self._get_default_response(symbol, f"Unexpected error: {str(e)}")

    def _get_default_response(self, symbol: str, error: str = "") -> Dict:
        """Return safe default response on error"""
        return {
            "symbol": symbol,
            "price": 0.0,
            "source": "coinapi",
            "success": False,
            "error": error,
        }

    async def get_market_data(self, symbol: str) -> Dict:
        """
        Get comprehensive market data for a symbol

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with market data including price, volume, etc.
        """
        # For now, return spot price data
        # This can be extended to include more comprehensive data
        price_data = await self.get_spot_price(symbol)

        if price_data.get("success"):
            return {
                "symbol": symbol,
                "price": price_data.get("price", 0.0),
                "source": "coinapi",
                "success": True,
                "timestamp": price_data.get("timestamp", ""),
                "volume": 0.0,  # Placeholder - can be added with additional API calls
                "market_cap": 0.0,  # Placeholder - can be added with additional API calls
                "change_24h": 0.0,  # Placeholder - can be added with additional API calls
            }
        else:
            return {
                "symbol": symbol,
                "price": 0.0,
                "source": "coinapi",
                "success": False,
                "error": price_data.get("error", "Unknown error"),
            }

    async def get_quote(self, symbol: str) -> Dict:
        """
        Get current quote for a symbol (alias to get_spot_price for RPC compatibility)
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with symbol, price, and source
        """
        return await self.get_spot_price(symbol)


# Singleton instance
coinapi_service = CoinAPIService()

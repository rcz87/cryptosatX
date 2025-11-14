"""
Coinglass v4 Service
Provides funding rate and open interest data for crypto futures
"""

import os

from app.utils.logger import get_logger

# Initialize module logger
logger = get_logger(__name__)
import httpx
from typing import Dict, Optional


class CoinglassService:
    """Service for interacting with Coinglass API v4"""

    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY", "")
        self.base_url = "https://open-api-v4.coinglass.com"
        self.headers = {"CG-API-KEY": self.api_key, "accept": "application/json"}

    async def test_connection(self) -> Dict:
        """
        Test API connection by fetching supported coins

        Returns:
            Dict with connection status
        """
        try:
            url = f"{self.base_url}/api/futures/supported-coins"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code != 200:
                    logger.error(f"Coinglass connection test failed:")
                    logger.info(f"Status code: {response.status_code}")
                    logger.info(f"Response: {response.text}")
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text,
                    }

                data = response.json()
                return {
                    "success": True,
                    "status_code": 200,
                    "coins_count": (
                        len(data.get("data", []))
                        if isinstance(data.get("data"), list)
                        else 0
                    ),
                }
        except Exception as e:
            logger.error(f"Coinglass connection error: {e}")
            return {"success": False, "error": str(e)}

    async def get_funding_rate(self, symbol: str) -> Dict:
        """
        Get current funding rate for a cryptocurrency

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with symbol and fundingRate
        """
        try:
            # Normalize symbol
            symbol = symbol.upper()

            # Coinglass v4 API endpoint
            url = f"{self.base_url}/api/futures/funding-rates"
            params = {"symbol": symbol}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()

                # Extract funding rate from v4 response
                funding_rate = 0.0
                if data.get("code") == "0" and data.get("data"):
                    funding_data = data["data"]
                    if isinstance(funding_data, list) and len(funding_data) > 0:
                        # Get average funding rate across exchanges
                        rates = [
                            float(item.get("rate", 0))
                            for item in funding_data
                            if item.get("rate")
                        ]
                        funding_rate = sum(rates) / len(rates) if rates else 0.0
                    elif isinstance(funding_data, dict):
                        funding_rate = float(funding_data.get("rate", 0))

                return {
                    "symbol": symbol,
                    "fundingRate": funding_rate,
                    "source": "coinglass",
                    "success": True,
                }

        except Exception as e:
            logger.error(f"Coinglass funding rate error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "fundingRate": 0.0,
                "source": "coinglass",
                "success": False,
                "error": str(e),
            }

    async def get_open_interest(self, symbol: str) -> Dict:
        """
        Get current open interest for a cryptocurrency

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with symbol and openInterest
        """
        try:
            # Normalize symbol
            symbol = symbol.upper()

            # Coinglass v4 API endpoint
            url = f"{self.base_url}/api/futures/open-interest-aggregated-ohlc"
            params = {"symbol": symbol, "interval": "0"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()

                # Extract open interest from v4 response
                open_interest = 0.0
                if data.get("code") == "0" and data.get("data"):
                    oi_data = data["data"]
                    if isinstance(oi_data, list) and len(oi_data) > 0:
                        # Get the latest OI value
                        latest = oi_data[-1]
                        open_interest = (
                            float(latest.get("c", 0))
                            if isinstance(latest, dict)
                            else 0.0
                        )
                    elif isinstance(oi_data, dict):
                        open_interest = float(oi_data.get("openInterest", 0))

                return {
                    "symbol": symbol,
                    "openInterest": open_interest,
                    "source": "coinglass",
                    "success": True,
                }

        except Exception as e:
            logger.error(f"Coinglass open interest error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "openInterest": 0.0,
                "source": "coinglass",
                "success": False,
                "error": str(e),
            }

    async def get_funding_and_oi(self, symbol: str) -> Dict:
        """
        Get both funding rate and open interest using coins-markets endpoint
        This is more efficient as it gets both metrics in one API call

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            Combined dict with both metrics
        """
        try:
            # Normalize symbol
            symbol = symbol.upper()

            # Use the coins-markets endpoint which provides comprehensive data
            url = f"{self.base_url}/api/futures/coins-markets"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code != 200:
                    logger.error(f"Coinglass coins-markets error for {symbol}:")
                    logger.info(f"Status code: {response.status_code}")
                    logger.info(f"Response: {response.text[:500]}")
                    return self._get_default_combined_response(
                        symbol, f"HTTP {response.status_code}"
                    )

                data = response.json()

                # Response format: {"code": "0", "msg": "success", "data": [...]}
                if data.get("code") == "0" and data.get("data"):
                    # Find the matching symbol in the data array
                    for coin_data in data["data"]:
                        if coin_data.get("symbol") == symbol:
                            # Extract funding rate (average by OI or volume)
                            funding_rate = float(
                                coin_data.get("avg_funding_rate_by_oi", 0)
                            )

                            # Extract open interest in USD
                            open_interest = float(coin_data.get("open_interest_usd", 0))

                            return {
                                "symbol": symbol,
                                "fundingRate": funding_rate,
                                "openInterest": open_interest,
                                "price": float(coin_data.get("current_price", 0)),
                                "source": "coinglass",
                                "success": True,
                            }

                    # Symbol not found in response
                    return self._get_default_combined_response(
                        symbol, f"Symbol {symbol} not found in market data"
                    )
                else:
                    return self._get_default_combined_response(
                        symbol, f"Invalid response: {data.get('msg', 'Unknown error')}"
                    )

        except Exception as e:
            logger.error(f"Coinglass funding+OI error for {symbol}: {e}")
            return self._get_default_combined_response(symbol, str(e))

    def _get_default_combined_response(self, symbol: str, error: str = "") -> Dict:
        """Return safe default response for combined funding+OI query"""
        return {
            "symbol": symbol,
            "fundingRate": 0.0,
            "openInterest": 0.0,
            "source": "coinglass",
            "success": False,
            "error": error,
        }

    async def get_market_data(self, symbol: str) -> Dict:
        """
        Get comprehensive market data for a symbol
        This method provides all available Coinglass data in one call

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with comprehensive market data
        """
        try:
            # Get combined funding and OI data
            combined_data = await self.get_funding_and_oi(symbol)

            if not combined_data.get("success"):
                return combined_data

            # Add additional market metrics
            market_data = {
                "symbol": symbol,
                "fundingRate": combined_data.get("fundingRate", 0.0),
                "openInterest": combined_data.get("openInterest", 0.0),
                "price": combined_data.get("price", 0.0),
                "source": "coinglass",
                "success": True,
                "metrics": {
                    "fundingRate": combined_data.get("fundingRate", 0.0),
                    "openInterest": combined_data.get("openInterest", 0.0),
                    "price": combined_data.get("price", 0.0),
                },
            }

            return market_data

        except Exception as e:
            logger.error(f"Coinglass market data error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "fundingRate": 0.0,
                "openInterest": 0.0,
                "price": 0.0,
                "source": "coinglass",
                "success": False,
                "error": str(e),
            }


# Singleton instance
coinglass_service = CoinglassService()

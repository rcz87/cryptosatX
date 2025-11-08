"""
Coinglass v4 Service
Provides funding rate and open interest data for crypto futures
"""
import os
import httpx
from typing import Dict, Optional


class CoinglassService:
    """Service for interacting with Coinglass API v4"""
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY", "")
        self.base_url = "https://open-api-v4.coinglass.com/public/v2"
        self.headers = {
            "CG-API-KEY": self.api_key,
            "accept": "application/json"
        }
    
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
            
            # Coinglass expects format like 'BTC' without USDT
            url = f"{self.base_url}/funding"
            params = {"symbol": symbol}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract funding rate from response
                # Coinglass v4 structure may vary, adapting to common format
                funding_rate = 0.0
                if data.get("success") and data.get("data"):
                    # Try to extract the weighted average funding rate
                    funding_data = data["data"]
                    if isinstance(funding_data, list) and len(funding_data) > 0:
                        funding_rate = float(funding_data[0].get("rate", 0))
                    elif isinstance(funding_data, dict):
                        funding_rate = float(funding_data.get("uMarginList", [{}])[0].get("rate", 0) if funding_data.get("uMarginList") else 0)
                
                return {
                    "symbol": symbol,
                    "fundingRate": funding_rate,
                    "source": "coinglass",
                    "success": True
                }
                
        except Exception as e:
            print(f"Coinglass funding rate error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "fundingRate": 0.0,
                "source": "coinglass",
                "success": False,
                "error": str(e)
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
            
            url = f"{self.base_url}/open_interest"
            params = {"symbol": symbol}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract open interest from response
                open_interest = 0.0
                if data.get("success") and data.get("data"):
                    oi_data = data["data"]
                    if isinstance(oi_data, dict):
                        # Sum up open interest across exchanges
                        open_interest = float(oi_data.get("openInterest", 0))
                    elif isinstance(oi_data, list) and len(oi_data) > 0:
                        open_interest = float(oi_data[0].get("openInterest", 0))
                
                return {
                    "symbol": symbol,
                    "openInterest": open_interest,
                    "source": "coinglass",
                    "success": True
                }
                
        except Exception as e:
            print(f"Coinglass open interest error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "openInterest": 0.0,
                "source": "coinglass",
                "success": False,
                "error": str(e)
            }
    
    async def get_funding_and_oi(self, symbol: str) -> Dict:
        """
        Get both funding rate and open interest in one call
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Combined dict with both metrics
        """
        funding = await self.get_funding_rate(symbol)
        oi = await self.get_open_interest(symbol)
        
        return {
            "symbol": symbol,
            "fundingRate": funding.get("fundingRate", 0.0),
            "openInterest": oi.get("openInterest", 0.0),
            "source": "coinglass",
            "success": funding.get("success", False) and oi.get("success", False)
        }


# Singleton instance
coinglass_service = CoinglassService()

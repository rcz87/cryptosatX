"""
OKX Public API Service
Provides candlestick/OHLCV data, funding rates, and open interest without requiring authentication
"""
import httpx
from typing import Dict, List, Optional
from app.utils.symbol_normalizer import normalize_symbol, Provider
from app.utils.logger import logger


class OKXService:
    """Service for interacting with OKX public API"""
    
    def __init__(self):
        self.base_url = "https://www.okx.com/api/v5"
    
    def _normalize_to_swap_inst_id(self, symbol: str) -> str:
        """
        Normalize symbol to OKX perpetual swap format using universal normalizer
        
        Args:
            symbol: Symbol in any format (BTC, BTCUSDT, bitcoin, etc.)
            
        Returns:
            OKX instrument ID like 'BTC-USDT-SWAP'
        """
        return normalize_symbol(symbol, Provider.OKX)
    
    async def get_candles(self, symbol: str, timeframe: str = "15m", limit: int = 100) -> Dict:
        """
        Get candlestick data for a cryptocurrency pair
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'BTCUSDT', 'bitcoin')
            timeframe: Timeframe for candles (1m, 5m, 15m, 1H, 4H, 1D)
            limit: Number of candles to retrieve (max 300)
            
        Returns:
            Dict with symbol and OHLCV data
        """
        try:
            # Use universal normalizer - get base symbol first, then format for OKX spot
            from app.utils.symbol_normalizer import get_base_symbol
            base_sym = get_base_symbol(symbol)
            inst_id = f"{base_sym}-USDT"
            
            # Map timeframe to OKX format
            bar_mapping = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1H",
                "1H": "1H",
                "4h": "4H",
                "4H": "4H",
                "1d": "1D",
                "1D": "1D"
            }
            bar = bar_mapping.get(timeframe, "15m")
            
            url = f"{self.base_url}/market/candles"
            params = {
                "instId": inst_id,
                "bar": bar,
                "limit": min(limit, 300)  # OKX max is 300
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Parse OKX candle response
                # Format: [timestamp, open, high, low, close, volume, volumeCcy, volumeCcyQuote, confirm]
                candles = []
                if data.get("code") == "0" and data.get("data"):
                    for candle in data["data"]:
                        candles.append({
                            "timestamp": int(candle[0]),
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5])
                        })
                
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "candles": candles,
                    "count": len(candles),
                    "source": "okx",
                    "success": True
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OKX HTTP error for {symbol}: {e}")
            return self._get_default_response(symbol, timeframe, f"HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"OKX request error for {symbol}: {e}")
            return self._get_default_response(symbol, timeframe, f"Request error: {str(e)}")
        except Exception as e:
            logger.error(f"OKX unexpected error for {symbol}: {e}")
            return self._get_default_response(symbol, timeframe, f"Unexpected error: {str(e)}")
    
    def _get_default_response(self, symbol: str, timeframe: str, error: str = "") -> Dict:
        """Return safe default response on error"""
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": [],
            "count": 0,
            "source": "okx",
            "success": False,
            "error": error
        }
    
    async def get_funding_rate(self, symbol: str) -> Dict:
        """
        Get current funding rate for a perpetual swap
        Public endpoint - no authentication required
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'SOL')
            
        Returns:
            Dict with uniform schema:
            {
                "success": bool,
                "source": "okx",
                "symbol": str,
                "fundingRate": float,
                "nextFundingTime": str,
                "error": str (optional)
            }
        """
        try:
            inst_id = self._normalize_to_swap_inst_id(symbol)
            url = f"{self.base_url}/public/funding-rate"
            params = {"instId": inst_id}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "source": "okx",
                        "symbol": symbol,
                        "fundingRate": 0.0,
                        "error": f"HTTP {response.status_code}"
                    }
                
                data = response.json()
                
                if data.get("code") != "0":
                    return {
                        "success": False,
                        "source": "okx",
                        "symbol": symbol,
                        "fundingRate": 0.0,
                        "error": f"OKX error: {data.get('msg', 'Unknown')}"
                    }
                
                if not data.get("data") or len(data["data"]) == 0:
                    return {
                        "success": False,
                        "source": "okx",
                        "symbol": symbol,
                        "fundingRate": 0.0,
                        "error": "No funding rate data"
                    }
                
                funding_data = data["data"][0]
                
                return {
                    "success": True,
                    "source": "okx",
                    "symbol": symbol,
                    "fundingRate": float(funding_data.get("fundingRate", 0.0)),
                    "nextFundingRate": float(funding_data.get("nextFundingRate", 0.0)),
                    "nextFundingTime": funding_data.get("nextFundingTime", ""),
                    "fundingTime": funding_data.get("fundingTime", "")
                }
                
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "source": "okx",
                "symbol": symbol,
                "fundingRate": 0.0,
                "error": f"HTTP error: {e.response.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "source": "okx",
                "symbol": symbol,
                "fundingRate": 0.0,
                "error": str(e)
            }
    
    async def get_open_interest(self, symbol: str) -> Dict:
        """
        Get current open interest for a perpetual swap
        Public endpoint - no authentication required
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'SOL')
            
        Returns:
            Dict with uniform schema:
            {
                "success": bool,
                "source": "okx",
                "symbol": str,
                "openInterest": float,
                "openInterestCcy": float,
                "error": str (optional)
            }
        """
        try:
            inst_id = self._normalize_to_swap_inst_id(symbol)
            url = f"{self.base_url}/public/open-interest"
            params = {
                "instType": "SWAP",
                "instId": inst_id
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "source": "okx",
                        "symbol": symbol,
                        "openInterest": 0.0,
                        "error": f"HTTP {response.status_code}"
                    }
                
                data = response.json()
                
                if data.get("code") != "0":
                    return {
                        "success": False,
                        "source": "okx",
                        "symbol": symbol,
                        "openInterest": 0.0,
                        "error": f"OKX error: {data.get('msg', 'Unknown')}"
                    }
                
                if not data.get("data") or len(data["data"]) == 0:
                    return {
                        "success": False,
                        "source": "okx",
                        "symbol": symbol,
                        "openInterest": 0.0,
                        "error": "No open interest data"
                    }
                
                oi_data = data["data"][0]
                
                return {
                    "success": True,
                    "source": "okx",
                    "symbol": symbol,
                    "openInterest": float(oi_data.get("oi", 0.0)),
                    "openInterestCcy": float(oi_data.get("oiCcy", 0.0)),
                    "timestamp": oi_data.get("ts", "")
                }
                
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "source": "okx",
                "symbol": symbol,
                "openInterest": 0.0,
                "error": f"HTTP error: {e.response.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "source": "okx",
                "symbol": symbol,
                "openInterest": 0.0,
                "error": str(e)
            }


# Singleton instance
okx_service = OKXService()

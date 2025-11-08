"""
OKX Public API Service
Provides candlestick/OHLCV data without requiring authentication
"""
import httpx
from typing import Dict, List, Optional


class OKXService:
    """Service for interacting with OKX public API"""
    
    def __init__(self):
        self.base_url = "https://www.okx.com/api/v5"
    
    async def get_candles(self, symbol: str, timeframe: str = "15m", limit: int = 100) -> Dict:
        """
        Get candlestick data for a cryptocurrency pair
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            timeframe: Timeframe for candles (1m, 5m, 15m, 1H, 4H, 1D)
            limit: Number of candles to retrieve (max 300)
            
        Returns:
            Dict with symbol and OHLCV data
        """
        try:
            # Normalize symbol to OKX format (e.g., BTC-USDT)
            symbol = symbol.upper()
            if not symbol.endswith("-USDT"):
                inst_id = f"{symbol}-USDT"
            else:
                inst_id = symbol
            
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
            print(f"OKX HTTP error for {symbol}: {e}")
            return self._get_default_response(symbol, timeframe, f"HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            print(f"OKX request error for {symbol}: {e}")
            return self._get_default_response(symbol, timeframe, f"Request error: {str(e)}")
        except Exception as e:
            print(f"OKX unexpected error for {symbol}: {e}")
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


# Singleton instance
okx_service = OKXService()

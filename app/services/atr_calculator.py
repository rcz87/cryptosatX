"""
ATR (Average True Range) Calculator
Measures market volatility for position sizing and stop loss placement
Phase 2: Risk Model V2 - Volatility-Adjusted Position Sizing
"""

import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.utils.logger import logger


class ATRCalculator:
    """
    Calculate Average True Range (ATR) for volatility measurement
    ATR measures the average price movement over a period
    Used for:
    - Volatility-adjusted position sizing
    - Dynamic stop loss placement
    - Risk-reward optimization
    """

    def __init__(self):
        self._http_client = None
        self.default_period = 14  # Standard ATR period
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client (lazy initialization)"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def get_ohlc_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> Optional[List[Dict]]:
        """
        Fetch OHLC (candlestick) data from OKX
        
        Args:
            symbol: Trading pair (e.g., BTC, ETH)
            timeframe: Candle interval (1h, 4h, 1d)
            limit: Number of candles to fetch (max 300)
        
        Returns:
            List of candles with [timestamp, open, high, low, close, volume]
        """
        try:
            # OKX interval mapping
            interval_map = {
                "1h": "1H",
                "4h": "4H",
                "1d": "1D",
                "15m": "15m",
                "1H": "1H",
                "4H": "4H",
                "1D": "1D"
            }
            
            okx_interval = interval_map.get(timeframe, "1H")
            
            # OKX uses USDT pairs with dash separator
            inst_id = f"{symbol}-USDT"
            
            url = f"https://www.okx.com/api/v5/market/candles"
            params = {
                "instId": inst_id,
                "bar": okx_interval,
                "limit": min(limit, 300)
            }
            
            client = await self._get_client()
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("code") == "0" and data.get("data"):
                    candles = data["data"]
                    
                    # Parse OKX format: [timestamp, open, high, low, close, volume, ...]
                    parsed = []
                    for candle in candles:
                        parsed.append({
                            "timestamp": int(candle[0]),
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5])
                        })
                    
                    # OKX returns newest first, reverse to get chronological order
                    return list(reversed(parsed))
                
            # Fallback to Binance if OKX fails
            return await self._get_binance_ohlc(symbol, timeframe, limit)

        except Exception as e:
            logger.error(f"Failed to fetch OHLC from OKX: {e}")
            # Try Binance fallback
            return await self._get_binance_ohlc(symbol, timeframe, limit)

    async def _get_binance_ohlc(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> Optional[List[Dict]]:
        """
        Fallback: Fetch OHLC data from Binance Futures
        """
        try:
            # Binance interval mapping
            interval_map = {
                "1h": "1h",
                "4h": "4h",
                "1d": "1d",
                "15m": "15m",
                "1H": "1h",
                "4H": "4h",
                "1D": "1d"
            }
            
            binance_interval = interval_map.get(timeframe, "1h")
            
            url = "https://fapi.binance.com/fapi/v1/klines"
            params = {
                "symbol": f"{symbol}USDT",
                "interval": binance_interval,
                "limit": min(limit, 1000)
            }
            
            client = await self._get_client()
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                candles = response.json()
                
                # Parse Binance format
                parsed = []
                for candle in candles:
                    parsed.append({
                        "timestamp": candle[0],
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5])
                    })
                
                return parsed
            
            return None
        
        except Exception as e:
            logger.error(f" Failed to fetch OHLC from Binance: {e}")
            return None

    def calculate_true_range(
        self,
        candles: List[Dict]
    ) -> List[float]:
        """
        Calculate True Range for each candle
        
        True Range = max of:
        1. Current High - Current Low
        2. |Current High - Previous Close|
        3. |Current Low - Previous Close|
        
        Returns list of TR values
        """
        true_ranges = []
        
        for i, candle in enumerate(candles):
            high = candle["high"]
            low = candle["low"]
            
            if i == 0:
                # First candle: TR = high - low
                tr = high - low
            else:
                prev_close = candles[i - 1]["close"]
                
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
            
            true_ranges.append(tr)
        
        return true_ranges

    def calculate_atr(
        self,
        true_ranges: List[float],
        period: int = 14
    ) -> Optional[float]:
        """
        Calculate Average True Range (ATR)
        
        Args:
            true_ranges: List of True Range values
            period: Number of periods to average (default: 14)
        
        Returns:
            ATR value or None if insufficient data
        """
        if len(true_ranges) < period:
            logger.warning(f" Insufficient data for ATR calculation: {len(true_ranges)} < {period}")
            return None
        
        # Use the last N periods for ATR calculation
        recent_tr = true_ranges[-period:]
        atr = sum(recent_tr) / len(recent_tr)
        
        return atr

    async def get_atr(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: int = 14
    ) -> Optional[Dict]:
        """
        Get ATR for a symbol across a specific timeframe
        
        Returns:
            Dict with ATR value, percentage, and metadata
        """
        try:
            # Fetch OHLC data (need period + buffer for accurate calculation)
            candles = await self.get_ohlc_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=period + 50  # Buffer for calculation
            )
            
            if not candles or len(candles) < period:
                logger.error(f" Insufficient OHLC data for {symbol} {timeframe}")
                return None
            
            # Calculate True Range
            true_ranges = self.calculate_true_range(candles)
            
            # Calculate ATR
            atr_value = self.calculate_atr(true_ranges, period=period)
            
            if not atr_value:
                return None
            
            # Get current price for percentage calculation (defensive)
            current_price = candles[-1].get("close") if candles and len(candles) > 0 else None
            
            if not current_price or current_price <= 0:
                logger.error(f" Invalid current price for {symbol}: {current_price}")
                return None
            
            atr_percentage = (atr_value / current_price) * 100
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "atr": round(atr_value, 8),
                "atr_percentage": round(atr_percentage, 4),
                "current_price": current_price,
                "period": period,
                "data_points": len(candles)
            }
        
        except Exception as e:
            logger.error(f" Failed to calculate ATR for {symbol}: {e}")
            return None

    async def get_multi_timeframe_atr(
        self,
        symbol: str,
        timeframes: List[str] = None
    ) -> Dict:
        """
        Get ATR across multiple timeframes
        Useful for multi-timeframe analysis
        
        Default timeframes: 1h, 4h, 1d
        """
        if timeframes is None:
            timeframes = ["1h", "4h", "1d"]
        
        results = {}
        
        for tf in timeframes:
            atr_data = await self.get_atr(symbol=symbol, timeframe=tf)
            if atr_data:
                results[tf] = atr_data
        
        # Calculate average volatility across timeframes
        if results:
            avg_atr_pct = sum(r["atr_percentage"] for r in results.values()) / len(results)
            
            return {
                "symbol": symbol,
                "timeframes": results,
                "average_volatility": round(avg_atr_pct, 4),
                "volatility_classification": self._classify_volatility(avg_atr_pct)
            }
        else:
            return {
                "symbol": symbol,
                "error": "Failed to calculate ATR for any timeframe"
            }

    def _classify_volatility(self, atr_percentage: float) -> str:
        """
        Classify volatility level based on ATR percentage
        
        Thresholds (approximate for crypto):
        - Very Low: < 1%
        - Low: 1-2%
        - Normal: 2-4%
        - High: 4-6%
        - Very High: > 6%
        """
        if atr_percentage < 1.0:
            return "VERY_LOW"
        elif atr_percentage < 2.0:
            return "LOW"
        elif atr_percentage < 4.0:
            return "NORMAL"
        elif atr_percentage < 6.0:
            return "HIGH"
        else:
            return "VERY_HIGH"

    async def close(self):
        """Close HTTP client"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()


# Global instance
atr_calculator = ATRCalculator()

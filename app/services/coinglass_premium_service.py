"""
Coinglass Premium Service
Premium endpoints for advanced trading signal generation
Requires Coinglass Standard plan or higher
"""
import os
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta


class CoinglassPremiumService:
    """Service for Coinglass premium endpoints (Standard plan+)"""
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY", "")
        self.base_url = "https://open-api-v4.coinglass.com"
        self.headers = {
            "CG-API-KEY": self.api_key,
            "accept": "application/json"
        }
        # Shared async client for connection pooling
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create shared async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def get_liquidation_data(self, symbol: str, interval: str = "h4") -> Dict:
        """
        Get liquidation volume data (longs vs shorts liquidated)
        Endpoint: /api/futures/liquidation/symbol
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')
            interval: Time interval (h1, h4, h12, h24)
            
        Returns:
            Dict with liquidation volumes for longs and shorts
        """
        try:
            symbol = symbol.upper()
            client = await self._get_client()
            
            url = f"{self.base_url}/api/futures/liquidation/symbol"
            params = {
                "symbol": symbol,
                "interval": interval
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"Liquidation API error for {symbol}: {response.status_code}")
                return self._default_liquidation_response(symbol)
            
            data = response.json()
            
            if data.get("code") == "0" and data.get("data"):
                liq_data = data["data"]
                
                # Calculate total liquidations (24h)
                total_long_liq = 0.0
                total_short_liq = 0.0
                
                if isinstance(liq_data, list):
                    # Sum recent liquidations
                    for entry in liq_data[-24:]:  # Last 24 periods
                        total_long_liq += float(entry.get("buyVolUsd", 0))
                        total_short_liq += float(entry.get("sellVolUsd", 0))
                
                # Calculate liquidation imbalance
                total_liq = total_long_liq + total_short_liq
                long_liq_pct = (total_long_liq / total_liq * 100) if total_liq > 0 else 50.0
                
                return {
                    "symbol": symbol,
                    "longLiquidations": total_long_liq,
                    "shortLiquidations": total_short_liq,
                    "totalLiquidations": total_liq,
                    "longLiqPct": long_liq_pct,
                    "imbalance": "long" if long_liq_pct > 55 else "short" if long_liq_pct < 45 else "balanced",
                    "source": "coinglass_liquidation",
                    "success": True
                }
            
            return self._default_liquidation_response(symbol)
            
        except Exception as e:
            print(f"Liquidation error for {symbol}: {e}")
            return self._default_liquidation_response(symbol)
    
    async def get_long_short_ratio(self, symbol: str) -> Dict:
        """
        Get long/short ratio from account positions
        Endpoint: /api/futures/long-short-accounts
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Dict with long/short ratios
        """
        try:
            symbol = symbol.upper()
            client = await self._get_client()
            
            url = f"{self.base_url}/api/futures/long-short-accounts"
            params = {"symbol": symbol}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return self._default_ls_ratio_response(symbol)
            
            data = response.json()
            
            if data.get("code") == "0" and data.get("data"):
                ls_data = data["data"]
                
                # Get latest long/short percentages
                if isinstance(ls_data, list) and len(ls_data) > 0:
                    latest = ls_data[-1]  # Most recent
                    long_pct = float(latest.get("longRate", 50.0))
                    short_pct = float(latest.get("shortRate", 50.0))
                    
                    # Determine sentiment
                    if long_pct > 60:
                        sentiment = "very_bullish"
                    elif long_pct > 52:
                        sentiment = "bullish"
                    elif long_pct < 40:
                        sentiment = "very_bearish"
                    elif long_pct < 48:
                        sentiment = "bearish"
                    else:
                        sentiment = "neutral"
                    
                    return {
                        "symbol": symbol,
                        "longAccountPct": long_pct,
                        "shortAccountPct": short_pct,
                        "ratio": long_pct / short_pct if short_pct > 0 else 1.0,
                        "sentiment": sentiment,
                        "source": "coinglass_ls_ratio",
                        "success": True
                    }
            
            return self._default_ls_ratio_response(symbol)
            
        except Exception as e:
            print(f"Long/Short ratio error for {symbol}: {e}")
            return self._default_ls_ratio_response(symbol)
    
    async def get_oi_trend(self, symbol: str, limit: int = 24) -> Dict:
        """
        Get Open Interest trend (24h change)
        Endpoint: /api/futures/ohlc-aggregated-history
        
        Args:
            symbol: Cryptocurrency symbol
            limit: Number of data points to fetch
            
        Returns:
            Dict with OI trend analysis
        """
        try:
            symbol = symbol.upper()
            client = await self._get_client()
            
            url = f"{self.base_url}/api/futures/ohlc-aggregated-history"
            params = {
                "symbol": symbol,
                "interval": "h1",
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return self._default_oi_trend_response(symbol)
            
            data = response.json()
            
            if data.get("code") == "0" and data.get("data"):
                oi_history = data["data"]
                
                if isinstance(oi_history, list) and len(oi_history) >= 2:
                    # Get first and last OI values
                    first_oi = float(oi_history[0].get("openInterest", 0))
                    last_oi = float(oi_history[-1].get("openInterest", 0))
                    
                    # Calculate percentage change
                    oi_change_pct = ((last_oi - first_oi) / first_oi * 100) if first_oi > 0 else 0
                    
                    # Determine trend
                    if oi_change_pct > 5:
                        trend = "strong_increase"
                    elif oi_change_pct > 1:
                        trend = "increase"
                    elif oi_change_pct < -5:
                        trend = "strong_decrease"
                    elif oi_change_pct < -1:
                        trend = "decrease"
                    else:
                        trend = "stable"
                    
                    return {
                        "symbol": symbol,
                        "currentOI": last_oi,
                        "previousOI": first_oi,
                        "oiChangePct": oi_change_pct,
                        "trend": trend,
                        "timeframe": f"{limit}h",
                        "source": "coinglass_oi_trend",
                        "success": True
                    }
            
            return self._default_oi_trend_response(symbol)
            
        except Exception as e:
            print(f"OI trend error for {symbol}: {e}")
            return self._default_oi_trend_response(symbol)
    
    async def get_top_trader_ratio(self, symbol: str) -> Dict:
        """
        Get top trader long/short positioning
        Endpoint: /api/futures/top-long-short-position-ratio
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Dict with top trader positioning
        """
        try:
            symbol = symbol.upper()
            client = await self._get_client()
            
            url = f"{self.base_url}/api/futures/top-long-short-position-ratio"
            params = {"symbol": symbol}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return self._default_top_trader_response(symbol)
            
            data = response.json()
            
            if data.get("code") == "0" and data.get("data"):
                trader_data = data["data"]
                
                if isinstance(trader_data, list) and len(trader_data) > 0:
                    latest = trader_data[-1]
                    
                    long_pct = float(latest.get("longRate", 50.0))
                    short_pct = float(latest.get("shortRate", 50.0))
                    
                    # Smart money bias
                    if long_pct > 55:
                        bias = "long"
                    elif short_pct > 55:
                        bias = "short"
                    else:
                        bias = "neutral"
                    
                    return {
                        "symbol": symbol,
                        "topTraderLongPct": long_pct,
                        "topTraderShortPct": short_pct,
                        "smartMoneyBias": bias,
                        "confidence": abs(long_pct - 50),  # Distance from neutral
                        "source": "coinglass_top_traders",
                        "success": True
                    }
            
            return self._default_top_trader_response(symbol)
            
        except Exception as e:
            print(f"Top trader error for {symbol}: {e}")
            return self._default_top_trader_response(symbol)
    
    async def get_fear_greed_index(self) -> Dict:
        """
        Get Crypto Fear & Greed Index
        Endpoint: /api/index/fear-greed
        
        Returns:
            Dict with fear & greed index value
        """
        try:
            client = await self._get_client()
            
            url = f"{self.base_url}/api/index/fear-greed"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return self._default_fear_greed_response()
            
            data = response.json()
            
            if data.get("code") == "0" and data.get("data"):
                fg_data = data["data"]
                
                if isinstance(fg_data, list) and len(fg_data) > 0:
                    latest = fg_data[0]
                    
                    value = int(latest.get("value", 50))
                    
                    # Classify sentiment
                    if value >= 75:
                        sentiment = "extreme_greed"
                    elif value >= 60:
                        sentiment = "greed"
                    elif value >= 40:
                        sentiment = "neutral"
                    elif value >= 25:
                        sentiment = "fear"
                    else:
                        sentiment = "extreme_fear"
                    
                    return {
                        "value": value,
                        "sentiment": sentiment,
                        "classification": latest.get("valueClassification", ""),
                        "contrarian_signal": "buy" if value < 25 else "sell" if value > 75 else "hold",
                        "source": "coinglass_fear_greed",
                        "success": True
                    }
            
            return self._default_fear_greed_response()
            
        except Exception as e:
            print(f"Fear & Greed error: {e}")
            return self._default_fear_greed_response()
    
    # Default responses for error handling
    def _default_liquidation_response(self, symbol: str) -> Dict:
        return {
            "symbol": symbol,
            "longLiquidations": 0,
            "shortLiquidations": 0,
            "totalLiquidations": 0,
            "longLiqPct": 50.0,
            "imbalance": "unknown",
            "source": "coinglass_liquidation",
            "success": False
        }
    
    def _default_ls_ratio_response(self, symbol: str) -> Dict:
        return {
            "symbol": symbol,
            "longAccountPct": 50.0,
            "shortAccountPct": 50.0,
            "ratio": 1.0,
            "sentiment": "neutral",
            "source": "coinglass_ls_ratio",
            "success": False
        }
    
    def _default_oi_trend_response(self, symbol: str) -> Dict:
        return {
            "symbol": symbol,
            "currentOI": 0,
            "previousOI": 0,
            "oiChangePct": 0,
            "trend": "unknown",
            "timeframe": "24h",
            "source": "coinglass_oi_trend",
            "success": False
        }
    
    def _default_top_trader_response(self, symbol: str) -> Dict:
        return {
            "symbol": symbol,
            "topTraderLongPct": 50.0,
            "topTraderShortPct": 50.0,
            "smartMoneyBias": "neutral",
            "confidence": 0,
            "source": "coinglass_top_traders",
            "success": False
        }
    
    def _default_fear_greed_response(self) -> Dict:
        return {
            "value": 50,
            "sentiment": "neutral",
            "classification": "Neutral",
            "contrarian_signal": "hold",
            "source": "coinglass_fear_greed",
            "success": False
        }


# Singleton instance
coinglass_premium = CoinglassPremiumService()

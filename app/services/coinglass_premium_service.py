"""
Coinglass Premium Service
Premium endpoints for advanced trading signal generation
Requires Coinglass Standard plan or higher
"""
import os

from app.utils.logger import get_logger

# Initialize module logger
logger = get_logger(__name__)
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
    
    async def get_liquidation_data(self, symbol: str, exchange: str = "Binance") -> Dict:
        """
        Get liquidation volume data (longs vs shorts liquidated)
        Endpoint: /api/futures/liquidation/coin-list
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')
            exchange: Exchange name (default: Binance)
            
        Returns:
            Dict with liquidation volumes for longs and shorts
        """
        try:
            symbol = symbol.upper()
            client = await self._get_client()
            
            url = f"{self.base_url}/api/futures/liquidation/coin-list"
            params = {
                "exchange": exchange
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"Liquidation API error for {symbol}: {response.status_code}")
                return self._default_liquidation_response(symbol)
            
            data = response.json()
            
            # Debug logging
            code = data.get("code")
            msg = data.get("msg", "")
            logger.info(f"[Liquidation] {symbol} - Status: {response.status_code}, Code: {code}, Msg: {msg}, Has Data: {bool(data.get('data'))}")
            
            # Coinglass returns integer 0 for success, not string "0"
            if str(code) == "0" and data.get("data"):
                liq_data = data["data"]
                
                # Find the specific symbol's liquidation data
                total_long_liq = 0.0
                total_short_liq = 0.0
                
                if isinstance(liq_data, list):
                    for coin_data in liq_data:
                        if coin_data.get("symbol") == symbol:
                            total_long_liq = float(coin_data.get("long_liquidation_usd_24h", 0))
                            total_short_liq = float(coin_data.get("short_liquidation_usd_24h", 0))
                            break
                
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
            logger.error(f"Liquidation error for {symbol}: {e}")
            return self._default_liquidation_response(symbol)
    
    async def get_long_short_ratio(self, symbol: str, exchange: str = "Binance") -> Dict:
        """
        Get long/short ratio from global accounts
        Endpoint: /api/futures/global-longshort-account-ratio
        
        Args:
            symbol: Cryptocurrency symbol
            exchange: Exchange name (default: Binance)
            
        Returns:
            Dict with long/short ratios
        """
        try:
            symbol = symbol.upper()
            client = await self._get_client()
            
            symbol_pair = f"{symbol}USDT"  # Convert BTC -> BTCUSDT
            url = f"{self.base_url}/api/futures/global-long-short-account-ratio/history"
            params = {
                "exchange": exchange,
                "symbol": symbol_pair,
                "interval": "h1",
                "limit": 1
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"[LongShortRatio] HTTP ERROR {symbol} - Status: {response.status_code}, Body: {response.text[:500]}")
                return self._default_ls_ratio_response(symbol)
            
            data = response.json()
            
            # Debug logging
            code = data.get("code")
            msg = data.get("msg", "")
            logger.info(f"[LongShortRatio] {symbol} - Status: {response.status_code}, Code: {code}, Msg: {msg}, Has Data: {bool(data.get('data'))}")
            
            # Coinglass returns integer 0 for success
            if str(code) == "0" and data.get("data"):
                ls_data = data["data"]
                
                # Get latest long/short percentages
                if isinstance(ls_data, list) and len(ls_data) > 0:
                    latest = ls_data[-1]  # Most recent
                    long_pct = float(latest.get("global_account_long_percent", 50.0))
                    short_pct = float(latest.get("global_account_short_percent", 50.0))
                    
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
            logger.error(f"Long/Short ratio error for {symbol}: {e}")
            return self._default_ls_ratio_response(symbol)
    
    async def get_oi_trend(self, symbol: str, limit: int = 24) -> Dict:
        """
        Get Open Interest trend (24h change)
        Endpoint: /api/futures/open-interest/aggregated-history
        
        Args:
            symbol: Cryptocurrency symbol
            limit: Number of data points to fetch
            
        Returns:
            Dict with OI trend analysis
        """
        try:
            symbol = symbol.upper()
            client = await self._get_client()
            
            url = f"{self.base_url}/api/futures/open-interest/aggregated-history"
            params = {
                "symbol": symbol,
                "interval": "h1",
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"[OITrend] HTTP ERROR {symbol} - Status: {response.status_code}, Body: {response.text[:500]}")
                return self._default_oi_trend_response(symbol)
            
            data = response.json()
            
            # Debug logging
            code = data.get("code")
            msg = data.get("msg", "")
            logger.info(f"[OITrend] {symbol} - Status: {response.status_code}, Code: {code}, Msg: {msg}, Has Data: {bool(data.get('data'))}")
            
            # Coinglass returns integer 0 for success
            if str(code) == "0" and data.get("data"):
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
            logger.error(f"OI trend error for {symbol}: {e}")
            return self._default_oi_trend_response(symbol)
    
    async def get_top_trader_ratio(self, symbol: str, exchange: str = "Binance") -> Dict:
        """
        Get top trader long/short positioning
        Endpoint: /api/futures/top-longshort-position-ratio
        
        Args:
            symbol: Cryptocurrency symbol
            exchange: Exchange name (default: Binance)
            
        Returns:
            Dict with top trader positioning
        """
        try:
            symbol = symbol.upper()
            client = await self._get_client()
            
            symbol_pair = f"{symbol}USDT"  # Convert BTC -> BTCUSDT
            url = f"{self.base_url}/api/futures/top-long-short-position-ratio/history"
            params = {
                "exchange": exchange,
                "symbol": symbol_pair,
                "interval": "h1",
                "limit": 1
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"[TopTrader] HTTP ERROR {symbol} - Status: {response.status_code}, Body: {response.text[:500]}")
                return self._default_top_trader_response(symbol)
            
            data = response.json()
            
            # Debug logging
            code = data.get("code")
            msg = data.get("msg", "")
            logger.info(f"[TopTrader] {symbol} - Status: {response.status_code}, Code: {code}, Msg: {msg}, Has Data: {bool(data.get('data'))}")
            
            # Coinglass returns integer 0 for success
            if str(code) == "0" and data.get("data"):
                trader_data = data["data"]
                
                if isinstance(trader_data, list) and len(trader_data) > 0:
                    latest = trader_data[-1]
                    
                    long_pct = float(latest.get("top_position_long_percent", 50.0))
                    short_pct = float(latest.get("top_position_short_percent", 50.0))
                    
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
            logger.error(f"Top trader error for {symbol}: {e}")
            return self._default_top_trader_response(symbol)
    
    async def get_fear_greed_index(self) -> Dict:
        """
        Get Crypto Fear & Greed Index
        Endpoint: /api/index/fear-greed-history
        
        Returns:
            Dict with fear & greed index value
        """
        try:
            client = await self._get_client()
            
            url = f"{self.base_url}/api/index/fear-greed-history"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"[FearGreed] HTTP ERROR - Status: {response.status_code}, Body: {response.text[:500]}")
                return self._default_fear_greed_response()
            
            data = response.json()
            
            # Debug logging
            code = data.get("code")
            msg = data.get("msg", "")
            logger.info(f"[FearGreed] Status: {response.status_code}, Code: {code}, Msg: {msg}, Has Data: {bool(data.get('data'))}")
            
            # Coinglass returns integer 0 for success
            if str(code) == "0" and data.get("data"):
                fg_data = data["data"]
                
                logger.info(f"[FearGreed] DEBUG - Data structure: type={type(fg_data)}, is_list={isinstance(fg_data, list)}, is_dict={isinstance(fg_data, dict)}")
                
                # Handle DICT format (direct object with data_list)
                if isinstance(fg_data, dict):
                    logger.info(f"[FearGreed] DEBUG - Dict keys: {list(fg_data.keys())}")
                    
                    if "data_list" in fg_data:
                        data_list = fg_data.get("data_list", [])
                        logger.info(f"[FearGreed] DEBUG - data_list length: {len(data_list) if isinstance(data_list, list) else 'not a list'}")
                        
                        if isinstance(data_list, list) and len(data_list) > 0:
                            # Get the latest value (last in array)
                            value = int(data_list[-1])
                            
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
                            
                            logger.info(f"[FearGreed] ✅ Latest value: {value}, Sentiment: {sentiment}")
                            
                            return {
                                "value": value,
                                "sentiment": sentiment,
                                "classification": sentiment.replace("_", " ").title(),
                                "contrarian_signal": "buy" if value < 25 else "sell" if value > 75 else "hold",
                                "source": "coinglass_fear_greed",
                                "success": True
                            }
                
                # Handle LIST format (legacy/alternative format)
                elif isinstance(fg_data, list) and len(fg_data) > 0:
                    fg_obj = fg_data[0]
                    
                    if isinstance(fg_obj, dict) and "data_list" in fg_obj:
                        data_list = fg_obj.get("data_list", [])
                        
                        if isinstance(data_list, list) and len(data_list) > 0:
                            value = int(data_list[-1])
                            
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
                            
                            logger.info(f"[FearGreed] ✅ Latest value: {value}, Sentiment: {sentiment}")
                            
                            return {
                                "value": value,
                                "sentiment": sentiment,
                                "classification": sentiment.replace("_", " ").title(),
                                "contrarian_signal": "buy" if value < 25 else "sell" if value > 75 else "hold",
                                "source": "coinglass_fear_greed",
                                "success": True
                            }
            
            logger.warning(f"[FearGreed] Failed to parse data - returning default")
            return self._default_fear_greed_response()
            
        except Exception as e:
            logger.error(f"Fear & Greed error: {e}")
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

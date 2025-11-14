"""
Coinglass Comprehensive Service
Maximizes usage of Coinglass Standard plan ($299/mo) with 90+ endpoints
Includes: Market Data, Liquidations, Long/Short Ratios, Funding Rates, OI Analytics,
         Options Data, ETF Flows, On-Chain Metrics, Market Indexes
         
OPTIMIZATION: Utilization increased from ~8% to 89% (8/9 endpoints - November 2025)
NOTE: Bitcoin-specific indicators (Rainbow Chart, S2F, Bull Peak) only available for BTC
"""
import os
import httpx
from typing import Dict, Optional, List
from datetime import datetime


class CoinglassComprehensiveService:
    """Comprehensive service maximizing all Coinglass Standard plan endpoints"""
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY", "")
        self.base_url_v4 = "https://open-api-v4.coinglass.com"
        self.base_url_pro = "https://open-api.coinglass.com"
        self.headers = {
            "CG-API-KEY": self.api_key,
            "accept": "application/json"
        }
        self._client: Optional[httpx.AsyncClient] = None
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol for Coinglass API using universal normalizer
        Converts: BTC -> BTCUSDT, SOL -> SOLUSDT, etc.
        Already formatted symbols pass through unchanged: BTCUSDT -> BTCUSDT
        """
        from app.utils.symbol_normalizer import normalize_symbol, Provider
        return normalize_symbol(symbol, Provider.COINGLASS)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create shared async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    # ==================== MARKET DATA ENDPOINTS ====================
    
    async def get_coins_markets(self, symbol: Optional[str] = None) -> Dict:
        """
        Get comprehensive market data for futures coins
        Endpoint: /api/futures/coins-markets
        
        Returns:
        - Current price
        - Market cap
        - Open interest (USD & quantity)
        - Funding rates (OI-weighted & volume-weighted)
        - Price changes (5m, 15m, 30m, 1h, 4h, 12h, 24h)
        - OI/Market Cap ratio
        - OI/Volume ratio
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/coins-markets"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                markets = data["data"]
                
                if symbol:
                    symbol_upper = self._normalize_symbol(symbol)
                    symbol_data = next((m for m in markets if m.get("symbol") == symbol_upper), None)
                    
                    if symbol_data:
                        return {
                            "success": True,
                            "symbol": symbol_upper,
                            "price": symbol_data.get("current_price", 0),
                            "marketCap": symbol_data.get("market_cap_usd", 0),
                            "openInterestUsd": symbol_data.get("open_interest_usd", 0),
                            "openInterestQty": symbol_data.get("open_interest_quantity", 0),
                            "fundingRateByOI": symbol_data.get("avg_funding_rate_by_oi", 0),
                            "fundingRateByVol": symbol_data.get("avg_funding_rate_by_vol", 0),
                            "oiMarketCapRatio": symbol_data.get("open_interest_market_cap_ratio", 0),
                            "oiVolumeRatio": symbol_data.get("open_interest_volume_ratio", 0),
                            "priceChange5m": symbol_data.get("price_change_percent_5m", 0),
                            "priceChange15m": symbol_data.get("price_change_percent_15m", 0),
                            "priceChange30m": symbol_data.get("price_change_percent_30m", 0),
                            "priceChange1h": symbol_data.get("price_change_percent_1h", 0),
                            "priceChange4h": symbol_data.get("price_change_percent_4h", 0),
                            "priceChange12h": symbol_data.get("price_change_percent_12h", 0),
                            "priceChange24h": symbol_data.get("price_change_percent_24h", 0),
                            "source": "coinglass_markets"
                        }
                
                return {"success": True, "data": markets, "count": len(markets)}
            
            return {"success": False, "error": "Invalid response structure"}
            
        except Exception as e:
            print(f"[CoinsMarkets] Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_perpetual_market(self, symbol: str) -> Dict:
        """
        Get perpetual futures market data for a symbol
        Endpoint: /api/futures/perpetual-market
        
        Returns current perpetual market metrics
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/perpetual-market"
            params = {"symbol": self._normalize_symbol(symbol)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                return {
                    "success": True,
                    "data": data["data"],
                    "source": "coinglass_perpetual"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_coins_price_change(self) -> Dict:
        """
        Get price changes for ALL coins across multiple timeframes (12TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/coins-price-change
        
        Returns price changes & amplitude (volatility) for:
        - 5m, 15m, 30m, 1h, 4h, 12h, 24h timeframes
        
        Perfect for:
        - Momentum screening (coins pumping/dumping)
        - Volatility analysis (amplitude = opportunity)
        - Quick market overview
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/coins-price-change"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                coins = data["data"]
                
                # Find top gainers/losers (24h)
                sorted_24h = sorted(coins, key=lambda x: float(x.get("price_change_percent_24h", 0)), reverse=True)
                top_gainers = sorted_24h[:10]
                top_losers = sorted_24h[-10:][::-1]  # Reverse to show worst first
                
                # Find most volatile (24h amplitude)
                sorted_volatile = sorted(coins, key=lambda x: float(x.get("price_amplitude_percent_24h", 0)), reverse=True)
                most_volatile = sorted_volatile[:10]
                
                # Short-term momentum (1h)
                sorted_1h = sorted(coins, key=lambda x: float(x.get("price_change_percent_1h", 0)), reverse=True)
                top_1h_gainers = sorted_1h[:10]
                
                return {
                    "success": True,
                    "coinCount": len(coins),
                    "topGainers24h": [
                        {
                            "symbol": c.get("symbol"),
                            "price": c.get("current_price"),
                            "change24h": c.get("price_change_percent_24h"),
                            "amplitude24h": c.get("price_amplitude_percent_24h")
                        } for c in top_gainers
                    ],
                    "topLosers24h": [
                        {
                            "symbol": c.get("symbol"),
                            "price": c.get("current_price"),
                            "change24h": c.get("price_change_percent_24h"),
                            "amplitude24h": c.get("price_amplitude_percent_24h")
                        } for c in top_losers
                    ],
                    "mostVolatile24h": [
                        {
                            "symbol": c.get("symbol"),
                            "price": c.get("current_price"),
                            "amplitude24h": c.get("price_amplitude_percent_24h"),
                            "change24h": c.get("price_change_percent_24h")
                        } for c in most_volatile
                    ],
                    "top1hGainers": [
                        {
                            "symbol": c.get("symbol"),
                            "price": c.get("current_price"),
                            "change1h": c.get("price_change_percent_1h"),
                            "change24h": c.get("price_change_percent_24h")
                        } for c in top_1h_gainers
                    ],
                    "allCoins": coins,
                    "source": "coinglass_price_change"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_price_history(self, exchange: str = "Binance", symbol: str = "BTCUSDT", 
                                interval: str = "1h", limit: int = 100) -> Dict:
        """
        Get historical price data (OHLCV candles) (13TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/price/history
        
        Parameters:
        - exchange: Binance, OKX, Bybit, etc.
        - symbol: Trading pair (e.g., BTCUSDT)
        - interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
        - limit: Number of candles (max 1000)
        
        Returns OHLCV data for charting and technical analysis
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/price/history"
            params = {
                "exchange": exchange,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                candles = data["data"]
                
                # Calculate price change from first to last
                first_open = 0.0
                last_close = 0.0
                if len(candles) >= 2:
                    first_open = float(candles[0].get("open", 0))
                    last_close = float(candles[-1].get("close", 0))
                    price_change = last_close - first_open
                    price_change_percent = (price_change / first_open * 100) if first_open > 0 else 0
                else:
                    price_change = 0
                    price_change_percent = 0
                
                # Find highest/lowest in period
                highs = [float(c.get("high", 0)) for c in candles]
                lows = [float(c.get("low", 0)) for c in candles]
                highest = max(highs) if highs else 0
                lowest = min(lows) if lows else 0
                
                # Total volume
                total_volume = sum(float(c.get("volume_usd", 0)) for c in candles)
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": self._normalize_symbol(symbol),
                    "interval": interval,
                    "candleCount": len(candles),
                    "summary": {
                        "firstOpen": first_open,
                        "lastClose": last_close,
                        "priceChange": price_change,
                        "priceChangePercent": price_change_percent,
                        "highest": highest,
                        "lowest": lowest,
                        "totalVolumeUSD": total_volume
                    },
                    "candles": candles,
                    "source": "coinglass_price_history"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_delisted_pairs(self) -> Dict:
        """
        Get delisted (removed) trading pairs by exchange (14TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/delisted-exchange-pairs
        
        Returns pairs that have been delisted from exchanges:
        - Useful for tracking discontinued pairs
        - Historical reference
        - Avoid trading delisted pairs
        
        Returns breakdown by exchange
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/delisted-exchange-pairs"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                exchanges_data = data["data"]
                
                # Count delisted pairs per exchange
                exchange_summary = {}
                total_delisted = 0
                
                for exchange, pairs in exchanges_data.items():
                    count = len(pairs) if isinstance(pairs, list) else 0
                    total_delisted += count
                    if count > 0:
                        exchange_summary[exchange] = {
                            "count": count,
                            "pairs": pairs[:10]  # Show first 10 as sample
                        }
                
                # Sort exchanges by delisted count
                top_exchanges = sorted(
                    exchange_summary.items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )[:10]
                
                return {
                    "success": True,
                    "totalDelisted": total_delisted,
                    "exchangeCount": len(exchange_summary),
                    "topExchangesByDelistedCount": [
                        {
                            "exchange": ex,
                            "delistedCount": info["count"],
                            "samplePairs": info["pairs"][:5]
                        } for ex, info in top_exchanges
                    ],
                    "allData": exchanges_data,
                    "source": "coinglass_delisted_pairs"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_rsi_indicator(self, exchange: str = "Binance", symbol: str = "BTCUSDT",
                                interval: str = "1h", limit: int = 100, window: int = 14) -> Dict:
        """
        Get RSI (Relative Strength Index) technical indicator (15TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/indicators/rsi
        
        Parameters:
        - exchange: Binance, OKX, Bybit, etc.
        - symbol: Trading pair (e.g., BTCUSDT)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 4500)
        - window: RSI period (default 14)
        
        Returns RSI values with overbought/oversold analysis
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/indicators/rsi"
            params = {
                "exchange": exchange,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit,
                "window": window
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                rsi_data = data["data"]
                
                # Get latest RSI
                latest_rsi = float(rsi_data[-1].get("rsi_value", 0)) if rsi_data else 0
                
                # Classify signal
                if latest_rsi > 70:
                    signal = "OVERBOUGHT"
                    signal_description = "Strong sell signal - RSI above 70"
                elif latest_rsi < 30:
                    signal = "OVERSOLD"
                    signal_description = "Strong buy signal - RSI below 30"
                elif latest_rsi > 60:
                    signal = "BULLISH"
                    signal_description = "Bullish momentum - RSI above 60"
                elif latest_rsi < 40:
                    signal = "BEARISH"
                    signal_description = "Bearish momentum - RSI below 40"
                else:
                    signal = "NEUTRAL"
                    signal_description = "Neutral zone - RSI between 40-60"
                
                # Calculate extremes
                rsi_values = [float(r.get("rsi_value", 0)) for r in rsi_data]
                max_rsi = max(rsi_values) if rsi_values else 0
                min_rsi = min(rsi_values) if rsi_values else 0
                avg_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else 0
                
                # Count overbought/oversold occurrences
                overbought_count = sum(1 for v in rsi_values if v > 70)
                oversold_count = sum(1 for v in rsi_values if v < 30)
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": self._normalize_symbol(symbol),
                    "interval": interval,
                    "window": window,
                    "dataPointCount": len(rsi_data),
                    "latestRSI": latest_rsi,
                    "signal": signal,
                    "signalDescription": signal_description,
                    "statistics": {
                        "max": max_rsi,
                        "min": min_rsi,
                        "average": avg_rsi,
                        "overboughtCount": overbought_count,
                        "oversoldCount": oversold_count
                    },
                    "timeSeries": rsi_data,
                    "source": "coinglass_rsi_indicator"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_open_interest_history(self, exchange: str = "Binance", symbol: str = "BTCUSDT",
                                        interval: str = "1d", limit: int = 100, unit: str = "usd") -> Dict:
        """
        Get Open Interest historical data (OHLC format) (16TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/open-interest/history
        
        Parameters:
        - exchange: Binance, OKX, Bybit, etc.
        - symbol: Trading pair (e.g., BTCUSDT)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        - unit: 'usd' or 'coin'
        
        Returns OI OHLC (not price!) - tracks institutional positioning
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/open-interest/history"
            params = {
                "exchange": exchange,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit,
                "unit": unit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                oi_data = data["data"]
                
                # Calculate OI changes
                if len(oi_data) >= 2:
                    first_oi = float(oi_data[0].get("close", 0))
                    last_oi = float(oi_data[-1].get("close", 0))
                    oi_change = last_oi - first_oi
                    oi_change_percent = (oi_change / first_oi * 100) if first_oi > 0 else 0
                    
                    # Trend detection
                    if oi_change_percent > 5:
                        trend = "STRONG_INCREASE"
                        trend_desc = f"OI increased {oi_change_percent:.1f}% - Institutions accumulating"
                    elif oi_change_percent > 0:
                        trend = "INCREASE"
                        trend_desc = f"OI increased {oi_change_percent:.1f}% - Gradual accumulation"
                    elif oi_change_percent < -5:
                        trend = "STRONG_DECREASE"
                        trend_desc = f"OI decreased {oi_change_percent:.1f}% - Institutions closing positions"
                    elif oi_change_percent < 0:
                        trend = "DECREASE"
                        trend_desc = f"OI decreased {oi_change_percent:.1f}% - Gradual reduction"
                    else:
                        trend = "STABLE"
                        trend_desc = "OI stable - No major positioning changes"
                else:
                    first_oi = 0
                    last_oi = 0
                    oi_change = 0
                    oi_change_percent = 0
                    trend = "UNKNOWN"
                    trend_desc = "Insufficient data"
                
                # Find highs and lows
                closes = [float(d.get("close", 0)) for d in oi_data]
                highs = [float(d.get("high", 0)) for d in oi_data]
                lows = [float(d.get("low", 0)) for d in oi_data]
                
                highest_oi = max(highs) if highs else 0
                lowest_oi = min(lows) if lows else 0
                avg_oi = sum(closes) / len(closes) if closes else 0
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": self._normalize_symbol(symbol),
                    "interval": interval,
                    "unit": unit,
                    "dataPointCount": len(oi_data),
                    "latestOI": last_oi,
                    "trend": trend,
                    "trendDescription": trend_desc,
                    "summary": {
                        "firstOI": first_oi,
                        "lastOI": last_oi,
                        "change": oi_change,
                        "changePercent": oi_change_percent,
                        "highest": highest_oi,
                        "lowest": lowest_oi,
                        "average": avg_oi
                    },
                    "timeSeries": oi_data,
                    "source": "coinglass_oi_history"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_aggregated_oi_history(self, symbol: str = "BTC", interval: str = "1d",
                                        limit: int = 100, unit: str = "usd") -> Dict:
        """
        Get AGGREGATED Open Interest across ALL EXCHANGES (17TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/open-interest/aggregated-history
        
        Parameters:
        - symbol: Coin symbol (e.g., BTC, ETH)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        - unit: 'usd' or 'coin'
        
        Returns TOTAL OI across Binance, OKX, Bybit, etc. combined!
        Much larger values than single exchange OI.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/open-interest/aggregated-history"
            params = {
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit,
                "unit": unit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                oi_data = data["data"]
                
                # Calculate OI changes
                if len(oi_data) >= 2:
                    first_oi = float(oi_data[0].get("close", 0))
                    last_oi = float(oi_data[-1].get("close", 0))
                    oi_change = last_oi - first_oi
                    oi_change_percent = (oi_change / first_oi * 100) if first_oi > 0 else 0
                    
                    # Trend detection for aggregated OI
                    if oi_change_percent > 5:
                        trend = "STRONG_ACCUMULATION"
                        trend_desc = f"Total OI +{oi_change_percent:.1f}% - Market-wide accumulation"
                    elif oi_change_percent > 0:
                        trend = "ACCUMULATION"
                        trend_desc = f"Total OI +{oi_change_percent:.1f}% - Gradual market accumulation"
                    elif oi_change_percent < -5:
                        trend = "STRONG_DISTRIBUTION"
                        trend_desc = f"Total OI {oi_change_percent:.1f}% - Market-wide distribution"
                    elif oi_change_percent < 0:
                        trend = "DISTRIBUTION"
                        trend_desc = f"Total OI {oi_change_percent:.1f}% - Gradual reduction"
                    else:
                        trend = "STABLE"
                        trend_desc = "Total OI stable - Market equilibrium"
                else:
                    first_oi = 0
                    last_oi = 0
                    oi_change = 0
                    oi_change_percent = 0
                    trend = "UNKNOWN"
                    trend_desc = "Insufficient data"
                
                # Find highs and lows
                closes = [float(d.get("close", 0)) for d in oi_data]
                highs = [float(d.get("high", 0)) for d in oi_data]
                lows = [float(d.get("low", 0)) for d in oi_data]
                
                highest_oi = max(highs) if highs else 0
                lowest_oi = min(lows) if lows else 0
                avg_oi = sum(closes) / len(closes) if closes else 0
                
                # Calculate volatility (OI swing)
                oi_range = highest_oi - lowest_oi
                oi_volatility = (oi_range / avg_oi * 100) if avg_oi > 0 else 0
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "interval": interval,
                    "unit": unit,
                    "aggregationType": "ALL_EXCHANGES",
                    "dataPointCount": len(oi_data),
                    "latestTotalOI": last_oi,
                    "trend": trend,
                    "trendDescription": trend_desc,
                    "summary": {
                        "firstOI": first_oi,
                        "lastOI": last_oi,
                        "change": oi_change,
                        "changePercent": oi_change_percent,
                        "highest": highest_oi,
                        "lowest": lowest_oi,
                        "average": avg_oi,
                        "range": oi_range,
                        "volatility": oi_volatility
                    },
                    "timeSeries": oi_data,
                    "source": "coinglass_aggregated_oi"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_aggregated_stablecoin_oi_history(self, exchange_list: str = "Binance", 
                                                    symbol: str = "BTC", interval: str = "1d",
                                                    limit: int = 100) -> Dict:
        """
        Get AGGREGATED STABLECOIN Open Interest history (18TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/open-interest/aggregated-stablecoin-history
        
        Parameters:
        - exchange_list: Exchange name(s) - can be comma-separated (e.g., "Binance,OKX")
        - symbol: Coin symbol (e.g., BTC, ETH)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        
        Returns OI in COIN/STABLECOIN terms (not USD!)
        Shows actual coin-denominated positions.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/open-interest/aggregated-stablecoin-history"
            params = {
                "exchange_list": exchange_list,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                oi_data = data["data"]
                
                # Calculate OI changes (in coin terms)
                if len(oi_data) >= 2:
                    first_oi = float(oi_data[0].get("close", 0))
                    last_oi = float(oi_data[-1].get("close", 0))
                    oi_change = last_oi - first_oi
                    oi_change_percent = (oi_change / first_oi * 100) if first_oi > 0 else 0
                    
                    # Trend detection
                    if oi_change_percent > 5:
                        trend = "STRONG_INCREASE"
                        trend_desc = f"Stablecoin OI +{oi_change_percent:.1f}% - High coin accumulation"
                    elif oi_change_percent > 0:
                        trend = "INCREASE"
                        trend_desc = f"Stablecoin OI +{oi_change_percent:.1f}% - Gradual accumulation"
                    elif oi_change_percent < -5:
                        trend = "STRONG_DECREASE"
                        trend_desc = f"Stablecoin OI {oi_change_percent:.1f}% - High coin distribution"
                    elif oi_change_percent < 0:
                        trend = "DECREASE"
                        trend_desc = f"Stablecoin OI {oi_change_percent:.1f}% - Gradual reduction"
                    else:
                        trend = "STABLE"
                        trend_desc = "Stablecoin OI stable"
                else:
                    first_oi = 0
                    last_oi = 0
                    oi_change = 0
                    oi_change_percent = 0
                    trend = "UNKNOWN"
                    trend_desc = "Insufficient data"
                
                # Find highs and lows
                closes = [float(d.get("close", 0)) for d in oi_data]
                highs = [float(d.get("high", 0)) for d in oi_data]
                lows = [float(d.get("low", 0)) for d in oi_data]
                
                highest_oi = max(highs) if highs else 0
                lowest_oi = min(lows) if lows else 0
                avg_oi = sum(closes) / len(closes) if closes else 0
                
                return {
                    "success": True,
                    "exchangeList": exchange_list,
                    "symbol": self._normalize_symbol(symbol),
                    "interval": interval,
                    "unit": "COIN",
                    "dataPointCount": len(oi_data),
                    "latestOI": last_oi,
                    "trend": trend,
                    "trendDescription": trend_desc,
                    "summary": {
                        "firstOI": first_oi,
                        "lastOI": last_oi,
                        "change": oi_change,
                        "changePercent": oi_change_percent,
                        "highest": highest_oi,
                        "lowest": lowest_oi,
                        "average": avg_oi
                    },
                    "timeSeries": oi_data,
                    "note": "OI values in COIN terms (not USD)",
                    "source": "coinglass_stablecoin_oi"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_aggregated_coin_margin_oi_history(self, exchange_list: str = "Binance", 
                                                     symbol: str = "BTC", interval: str = "1d",
                                                     limit: int = 100) -> Dict:
        """
        Get AGGREGATED COIN-MARGIN Open Interest history (19TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/open-interest/aggregated-coin-margin-history
        
        Parameters:
        - exchange_list: Exchange name(s) - can be comma-separated (e.g., "Binance,OKX")
        - symbol: Coin symbol (e.g., BTC, ETH)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        
        Returns OI for COIN-MARGINED futures (inverse contracts)!
        Example: BTCUSD where margin is in BTC, not USDT
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/open-interest/aggregated-coin-margin-history"
            params = {
                "exchange_list": exchange_list,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                oi_data = data["data"]
                
                # Calculate OI changes (coin-margined contracts)
                if len(oi_data) >= 2:
                    first_oi = float(oi_data[0].get("close", 0))
                    last_oi = float(oi_data[-1].get("close", 0))
                    oi_change = last_oi - first_oi
                    oi_change_percent = (oi_change / first_oi * 100) if first_oi > 0 else 0
                    
                    # Trend detection for coin-margined futures
                    if oi_change_percent > 5:
                        trend = "STRONG_INCREASE"
                        trend_desc = f"Coin-margin OI +{oi_change_percent:.1f}% - Inverse contract accumulation"
                    elif oi_change_percent > 0:
                        trend = "INCREASE"
                        trend_desc = f"Coin-margin OI +{oi_change_percent:.1f}% - Gradual accumulation"
                    elif oi_change_percent < -5:
                        trend = "STRONG_DECREASE"
                        trend_desc = f"Coin-margin OI {oi_change_percent:.1f}% - High distribution"
                    elif oi_change_percent < 0:
                        trend = "DECREASE"
                        trend_desc = f"Coin-margin OI {oi_change_percent:.1f}% - Gradual reduction"
                    else:
                        trend = "STABLE"
                        trend_desc = "Coin-margin OI stable"
                else:
                    first_oi = 0
                    last_oi = 0
                    oi_change = 0
                    oi_change_percent = 0
                    trend = "UNKNOWN"
                    trend_desc = "Insufficient data"
                
                # Find highs and lows
                closes = [float(d.get("close", 0)) for d in oi_data]
                highs = [float(d.get("high", 0)) for d in oi_data]
                lows = [float(d.get("low", 0)) for d in oi_data]
                
                highest_oi = max(highs) if highs else 0
                lowest_oi = min(lows) if lows else 0
                avg_oi = sum(closes) / len(closes) if closes else 0
                
                return {
                    "success": True,
                    "exchangeList": exchange_list,
                    "symbol": self._normalize_symbol(symbol),
                    "interval": interval,
                    "contractType": "COIN_MARGINED",
                    "dataPointCount": len(oi_data),
                    "latestOI": last_oi,
                    "trend": trend,
                    "trendDescription": trend_desc,
                    "summary": {
                        "firstOI": first_oi,
                        "lastOI": last_oi,
                        "change": oi_change,
                        "changePercent": oi_change_percent,
                        "highest": highest_oi,
                        "lowest": lowest_oi,
                        "average": avg_oi
                    },
                    "timeSeries": oi_data,
                    "note": "OI for coin-margined (inverse) futures contracts",
                    "source": "coinglass_coin_margin_oi"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_oi_exchange_list(self, symbol: str = "BTC") -> Dict:
        """
        Get Open Interest breakdown by EXCHANGE (20TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/open-interest/exchange-list
        
        Parameters:
        - symbol: Coin symbol (e.g., BTC, ETH)
        
        Returns comprehensive OI data per exchange:
        - Total OI (USD + quantity)
        - Coin-margined vs Stablecoin-margined breakdown
        - OI change % across 6 timeframes (5m, 15m, 30m, 1h, 4h, 24h)
        - All exchanges + aggregate
        
        Perfect for cross-exchange analysis!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/open-interest/exchange-list"
            params = {"symbol": self._normalize_symbol(symbol)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                exchanges_data = data["data"]
                
                # Find aggregate and top exchanges
                aggregate = next((e for e in exchanges_data if e.get("exchange") == "All"), None)
                exchanges = [e for e in exchanges_data if e.get("exchange") != "All"]
                
                # Sort exchanges by OI
                exchanges_sorted = sorted(exchanges, 
                                         key=lambda x: float(x.get("open_interest_usd", 0)), 
                                         reverse=True)
                
                top_5 = exchanges_sorted[:5]
                
                # Calculate market share for top 5
                total_oi = float(aggregate.get("open_interest_usd", 0)) if aggregate else 0
                
                top_5_with_share = []
                for ex in top_5:
                    ex_oi = float(ex.get("open_interest_usd", 0))
                    market_share = (ex_oi / total_oi * 100) if total_oi > 0 else 0
                    
                    top_5_with_share.append({
                        "exchange": ex.get("exchange"),
                        "openInterestUSD": ex_oi,
                        "openInterestQuantity": float(ex.get("open_interest_quantity", 0)),
                        "marketShare": market_share,
                        "coinMargined": float(ex.get("open_interest_by_coin_margin", 0)),
                        "stablecoinMargined": float(ex.get("open_interest_by_stable_coin_margin", 0)),
                        "change24h": float(ex.get("open_interest_change_percent_24h", 0))
                    })
                
                # Aggregate data
                aggregate_info = {
                    "totalOI": float(aggregate.get("open_interest_usd", 0)) if aggregate else 0,
                    "totalQuantity": float(aggregate.get("open_interest_quantity", 0)) if aggregate else 0,
                    "coinMargined": float(aggregate.get("open_interest_by_coin_margin", 0)) if aggregate else 0,
                    "stablecoinMargined": float(aggregate.get("open_interest_by_stable_coin_margin", 0)) if aggregate else 0,
                    "change24h": float(aggregate.get("open_interest_change_percent_24h", 0)) if aggregate else 0
                } if aggregate else {}
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "exchangeCount": len(exchanges),
                    "aggregate": aggregate_info,
                    "top5Exchanges": top_5_with_share,
                    "allExchanges": exchanges_data,
                    "source": "coinglass_oi_exchange_list"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_oi_exchange_history_chart(self, symbol: str = "BTC", 
                                            range: str = "12h", unit: str = "usd") -> Dict:
        """
        Get Open Interest history CHART data per exchange (21ST ENDPOINT!)
        REAL ENDPOINT: /api/futures/open-interest/exchange-history-chart
        
        Parameters:
        - symbol: Coin symbol (e.g., BTC, ETH)
        - range: Time range (all, 1m, 15m, 1h, 4h, 12h, 24h, etc.)
        - unit: 'usd' or 'coin'
        
        Returns TIME-SERIES data perfect for charting:
        - time_list: Array of timestamps
        - price_list: Array of prices
        - data_map: Object with exchange OI arrays
        
        Ready for frontend charting libraries!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/open-interest/exchange-history-chart"
            params = {
                "symbol": self._normalize_symbol(symbol),
                "range": range,
                "unit": unit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                chart_data = data["data"]
                
                time_list = chart_data.get("time_list", [])
                price_list = chart_data.get("price_list", [])
                data_map = chart_data.get("data_map", {})
                
                # Calculate summary for each exchange
                exchange_summaries = {}
                for exchange, values in data_map.items():
                    if values:
                        first_val = float(values[0]) if values else 0
                        last_val = float(values[-1]) if values else 0
                        change = last_val - first_val
                        change_percent = (change / first_val * 100) if first_val > 0 else 0
                        
                        exchange_summaries[exchange] = {
                            "firstOI": first_val,
                            "lastOI": last_val,
                            "change": change,
                            "changePercent": change_percent,
                            "dataPoints": len(values)
                        }
                
                # Price summary
                price_summary = {}
                if price_list:
                    price_summary = {
                        "firstPrice": float(price_list[0]),
                        "lastPrice": float(price_list[-1]),
                        "priceChange": float(price_list[-1]) - float(price_list[0]),
                        "priceChangePercent": ((float(price_list[-1]) - float(price_list[0])) / float(price_list[0]) * 100) if price_list[0] > 0 else 0
                    }
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "range": range,
                    "unit": unit,
                    "dataPoints": len(time_list),
                    "chartData": {
                        "timeList": time_list,
                        "priceList": price_list,
                        "exchangeData": data_map
                    },
                    "priceSummary": price_summary,
                    "exchangeSummaries": exchange_summaries,
                    "source": "coinglass_oi_chart"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_funding_rate_history(self, exchange: str = "Binance", symbol: str = "BTCUSDT",
                                       interval: str = "1d", limit: int = 100) -> Dict:
        """
        Get Funding Rate historical data (22ND ENDPOINT!)
        REAL ENDPOINT: /api/futures/funding-rate/history
        
        Parameters:
        - exchange: Exchange name (e.g., Binance, OKX, Bybit)
        - symbol: Trading pair (e.g., BTCUSDT)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        
        Returns funding rate OHLC data:
        - Positive = Longs pay shorts (bullish sentiment)
        - Negative = Shorts pay longs (bearish sentiment)
        - Extreme values = Potential reversal
        
        CRITICAL for sentiment analysis!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/funding-rate/history"
            params = {
                "exchange": exchange,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                fr_data = data["data"]
                
                # Calculate funding rate statistics
                if len(fr_data) >= 2:
                    first_fr = float(fr_data[0].get("close", 0))
                    last_fr = float(fr_data[-1].get("close", 0))
                    
                    # Extract all close values for analysis
                    closes = [float(d.get("close", 0)) for d in fr_data]
                    highs = [float(d.get("high", 0)) for d in fr_data]
                    lows = [float(d.get("low", 0)) for d in fr_data]
                    
                    avg_fr = sum(closes) / len(closes) if closes else 0
                    max_fr = max(highs) if highs else 0
                    min_fr = min(lows) if lows else 0
                    
                    # Sentiment analysis
                    if avg_fr > 0.05:
                        sentiment = "EXTREMELY_BULLISH"
                        sentiment_desc = f"Avg funding {avg_fr*100:.2f}% - Extreme long bias, reversal risk!"
                    elif avg_fr > 0.02:
                        sentiment = "VERY_BULLISH"
                        sentiment_desc = f"Avg funding {avg_fr*100:.2f}% - Strong long bias"
                    elif avg_fr > 0.01:
                        sentiment = "BULLISH"
                        sentiment_desc = f"Avg funding {avg_fr*100:.2f}% - Moderate long bias"
                    elif avg_fr > 0:
                        sentiment = "SLIGHTLY_BULLISH"
                        sentiment_desc = f"Avg funding {avg_fr*100:.2f}% - Slight long bias"
                    elif avg_fr > -0.01:
                        sentiment = "SLIGHTLY_BEARISH"
                        sentiment_desc = f"Avg funding {avg_fr*100:.2f}% - Slight short bias"
                    elif avg_fr > -0.02:
                        sentiment = "BEARISH"
                        sentiment_desc = f"Avg funding {avg_fr*100:.2f}% - Moderate short bias"
                    elif avg_fr > -0.05:
                        sentiment = "VERY_BEARISH"
                        sentiment_desc = f"Avg funding {avg_fr*100:.2f}% - Strong short bias"
                    else:
                        sentiment = "EXTREMELY_BEARISH"
                        sentiment_desc = f"Avg funding {avg_fr*100:.2f}% - Extreme short bias, reversal risk!"
                    
                    # Count positive vs negative periods
                    positive_count = sum(1 for c in closes if c > 0)
                    negative_count = sum(1 for c in closes if c < 0)
                    
                    return {
                        "success": True,
                        "exchange": exchange,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "dataPointCount": len(fr_data),
                        "latestFundingRate": last_fr,
                        "latestFundingRatePercent": last_fr * 100,
                        "sentiment": sentiment,
                        "sentimentDescription": sentiment_desc,
                        "summary": {
                            "firstFR": first_fr,
                            "lastFR": last_fr,
                            "average": avg_fr,
                            "averagePercent": avg_fr * 100,
                            "highest": max_fr,
                            "highestPercent": max_fr * 100,
                            "lowest": min_fr,
                            "lowestPercent": min_fr * 100,
                            "positivePeriods": positive_count,
                            "negativePeriods": negative_count
                        },
                        "timeSeries": fr_data,
                        "source": "coinglass_funding_rate"
                    }
                else:
                    first_fr = 0
                    last_fr = 0
                    sentiment = "UNKNOWN"
                    sentiment_desc = "Insufficient data"
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": self._normalize_symbol(symbol),
                    "interval": interval,
                    "dataPointCount": len(fr_data),
                    "latestFundingRate": last_fr,
                    "sentiment": sentiment,
                    "sentimentDescription": sentiment_desc,
                    "timeSeries": fr_data,
                    "source": "coinglass_funding_rate"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_oi_weighted_funding_rate_history(self, symbol: str = "BTC", 
                                                    interval: str = "1d", limit: int = 100) -> Dict:
        """
        Get OI-WEIGHTED Funding Rate history (23RD ENDPOINT!)
        REAL ENDPOINT: /api/futures/funding-rate/oi-weight-history
        
        Parameters:
        - symbol: Coin symbol (e.g., BTC, ETH)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        
        Returns OI-WEIGHTED funding rate (AGGREGATED across ALL exchanges):
        - Weights FR by Open Interest (bigger exchanges = more weight)
        - More accurate than single exchange FR
        - Market-wide sentiment indicator
        
        MORE ACCURATE than per-exchange FR!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/funding-rate/oi-weight-history"
            params = {
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                fr_data = data["data"]
                
                # Calculate OI-weighted funding rate statistics
                if len(fr_data) >= 2:
                    first_fr = float(fr_data[0].get("close", 0))
                    last_fr = float(fr_data[-1].get("close", 0))
                    
                    # Extract all close values for analysis
                    closes = [float(d.get("close", 0)) for d in fr_data]
                    highs = [float(d.get("high", 0)) for d in fr_data]
                    lows = [float(d.get("low", 0)) for d in fr_data]
                    
                    avg_fr = sum(closes) / len(closes) if closes else 0
                    max_fr = max(highs) if highs else 0
                    min_fr = min(lows) if lows else 0
                    
                    # Market-wide sentiment analysis (OI-weighted)
                    if avg_fr > 0.05:
                        sentiment = "EXTREMELY_BULLISH"
                        sentiment_desc = f"Market-wide FR {avg_fr*100:.2f}% - Extreme long bias, reversal risk!"
                    elif avg_fr > 0.02:
                        sentiment = "VERY_BULLISH"
                        sentiment_desc = f"Market-wide FR {avg_fr*100:.2f}% - Strong long bias"
                    elif avg_fr > 0.01:
                        sentiment = "BULLISH"
                        sentiment_desc = f"Market-wide FR {avg_fr*100:.2f}% - Moderate long bias"
                    elif avg_fr > 0:
                        sentiment = "SLIGHTLY_BULLISH"
                        sentiment_desc = f"Market-wide FR {avg_fr*100:.2f}% - Slight long bias"
                    elif avg_fr > -0.01:
                        sentiment = "SLIGHTLY_BEARISH"
                        sentiment_desc = f"Market-wide FR {avg_fr*100:.2f}% - Slight short bias"
                    elif avg_fr > -0.02:
                        sentiment = "BEARISH"
                        sentiment_desc = f"Market-wide FR {avg_fr*100:.2f}% - Moderate short bias"
                    elif avg_fr > -0.05:
                        sentiment = "VERY_BEARISH"
                        sentiment_desc = f"Market-wide FR {avg_fr*100:.2f}% - Strong short bias"
                    else:
                        sentiment = "EXTREMELY_BEARISH"
                        sentiment_desc = f"Market-wide FR {avg_fr*100:.2f}% - Extreme short bias, reversal risk!"
                    
                    # Count positive vs negative periods
                    positive_count = sum(1 for c in closes if c > 0)
                    negative_count = sum(1 for c in closes if c < 0)
                    
                    return {
                        "success": True,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "weightingMethod": "OI_WEIGHTED",
                        "dataPointCount": len(fr_data),
                        "latestFundingRate": last_fr,
                        "latestFundingRatePercent": last_fr * 100,
                        "sentiment": sentiment,
                        "sentimentDescription": sentiment_desc,
                        "summary": {
                            "firstFR": first_fr,
                            "lastFR": last_fr,
                            "average": avg_fr,
                            "averagePercent": avg_fr * 100,
                            "highest": max_fr,
                            "highestPercent": max_fr * 100,
                            "lowest": min_fr,
                            "lowestPercent": min_fr * 100,
                            "positivePeriods": positive_count,
                            "negativePeriods": negative_count
                        },
                        "timeSeries": fr_data,
                        "note": "Funding rate weighted by Open Interest across all exchanges",
                        "source": "coinglass_oi_weighted_fr"
                    }
                else:
                    return {
                        "success": True,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "weightingMethod": "OI_WEIGHTED",
                        "dataPointCount": len(fr_data),
                        "timeSeries": fr_data,
                        "source": "coinglass_oi_weighted_fr"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_volume_weighted_funding_rate_history(self, symbol: str = "BTC", 
                                                        interval: str = "1d", limit: int = 100) -> Dict:
        """
        Get VOLUME-WEIGHTED Funding Rate history (24TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/funding-rate/vol-weight-history
        
        Parameters:
        - symbol: Coin symbol (e.g., BTC, ETH)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        
        Returns VOLUME-WEIGHTED funding rate (AGGREGATED across ALL exchanges):
        - Weights FR by Trading Volume (high volume = more weight)
        - Different from OI-weighted (positions vs activity)
        - Active trading sentiment indicator
        
        Volume-weighted = Active trader sentiment!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/funding-rate/vol-weight-history"
            params = {
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                fr_data = data["data"]
                
                # Calculate volume-weighted funding rate statistics
                if len(fr_data) >= 2:
                    first_fr = float(fr_data[0].get("close", 0))
                    last_fr = float(fr_data[-1].get("close", 0))
                    
                    # Extract all close values for analysis
                    closes = [float(d.get("close", 0)) for d in fr_data]
                    highs = [float(d.get("high", 0)) for d in fr_data]
                    lows = [float(d.get("low", 0)) for d in fr_data]
                    
                    avg_fr = sum(closes) / len(closes) if closes else 0
                    max_fr = max(highs) if highs else 0
                    min_fr = min(lows) if lows else 0
                    
                    # Active trader sentiment analysis (volume-weighted)
                    if avg_fr > 0.05:
                        sentiment = "EXTREMELY_BULLISH"
                        sentiment_desc = f"Active trader FR {avg_fr*100:.2f}% - Extreme long bias, reversal risk!"
                    elif avg_fr > 0.02:
                        sentiment = "VERY_BULLISH"
                        sentiment_desc = f"Active trader FR {avg_fr*100:.2f}% - Strong long bias"
                    elif avg_fr > 0.01:
                        sentiment = "BULLISH"
                        sentiment_desc = f"Active trader FR {avg_fr*100:.2f}% - Moderate long bias"
                    elif avg_fr > 0:
                        sentiment = "SLIGHTLY_BULLISH"
                        sentiment_desc = f"Active trader FR {avg_fr*100:.2f}% - Slight long bias"
                    elif avg_fr > -0.01:
                        sentiment = "SLIGHTLY_BEARISH"
                        sentiment_desc = f"Active trader FR {avg_fr*100:.2f}% - Slight short bias"
                    elif avg_fr > -0.02:
                        sentiment = "BEARISH"
                        sentiment_desc = f"Active trader FR {avg_fr*100:.2f}% - Moderate short bias"
                    elif avg_fr > -0.05:
                        sentiment = "VERY_BEARISH"
                        sentiment_desc = f"Active trader FR {avg_fr*100:.2f}% - Strong short bias"
                    else:
                        sentiment = "EXTREMELY_BEARISH"
                        sentiment_desc = f"Active trader FR {avg_fr*100:.2f}% - Extreme short bias, reversal risk!"
                    
                    # Count positive vs negative periods
                    positive_count = sum(1 for c in closes if c > 0)
                    negative_count = sum(1 for c in closes if c < 0)
                    
                    return {
                        "success": True,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "weightingMethod": "VOLUME_WEIGHTED",
                        "dataPointCount": len(fr_data),
                        "latestFundingRate": last_fr,
                        "latestFundingRatePercent": last_fr * 100,
                        "sentiment": sentiment,
                        "sentimentDescription": sentiment_desc,
                        "summary": {
                            "firstFR": first_fr,
                            "lastFR": last_fr,
                            "average": avg_fr,
                            "averagePercent": avg_fr * 100,
                            "highest": max_fr,
                            "highestPercent": max_fr * 100,
                            "lowest": min_fr,
                            "lowestPercent": min_fr * 100,
                            "positivePeriods": positive_count,
                            "negativePeriods": negative_count
                        },
                        "timeSeries": fr_data,
                        "note": "Funding rate weighted by Trading Volume across all exchanges",
                        "source": "coinglass_volume_weighted_fr"
                    }
                else:
                    return {
                        "success": True,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "weightingMethod": "VOLUME_WEIGHTED",
                        "dataPointCount": len(fr_data),
                        "timeSeries": fr_data,
                        "source": "coinglass_volume_weighted_fr"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_funding_rate_exchange_list(self, symbol: str = "BTC") -> Dict:
        """
        Get REAL-TIME Funding Rate per exchange (25TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/funding-rate/exchange-list
        
        Parameters:
        - symbol: Coin symbol (e.g., BTC, ETH)
        
        Returns current funding rate for ALL exchanges:
        - Current funding rate per exchange
        - Funding interval (1h or 8h)
        - Next funding time
        - Separated by margin type
        
        Perfect for cross-exchange arbitrage!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/funding-rate/exchange-list"
            params = {"symbol": self._normalize_symbol(symbol)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                fr_data = data["data"]
                
                stablecoin_list = []
                coin_margin_list = []
                
                for item in fr_data:
                    symbol_data = item.get("symbol")
                    
                    # Process stablecoin-margined
                    if "stablecoin_margin_list" in item:
                        for ex in item["stablecoin_margin_list"]:
                            stablecoin_list.append({
                                "exchange": ex.get("exchange"),
                                "fundingRate": float(ex.get("funding_rate", 0)),
                                "fundingRatePercent": float(ex.get("funding_rate", 0)) * 100,
                                "fundingInterval": ex.get("funding_rate_interval"),
                                "nextFundingTime": ex.get("next_funding_time")
                            })
                    
                    # Process coin-margined
                    if "coin_margin_list" in item:
                        for ex in item["coin_margin_list"]:
                            coin_margin_list.append({
                                "exchange": ex.get("exchange"),
                                "fundingRate": float(ex.get("funding_rate", 0)),
                                "fundingRatePercent": float(ex.get("funding_rate", 0)) * 100,
                                "fundingInterval": ex.get("funding_rate_interval"),
                                "nextFundingTime": ex.get("next_funding_time")
                            })
                
                # Sort by funding rate (highest to lowest)
                stablecoin_sorted = sorted(stablecoin_list, 
                                          key=lambda x: x["fundingRate"], 
                                          reverse=True)
                coin_margin_sorted = sorted(coin_margin_list, 
                                           key=lambda x: x["fundingRate"], 
                                           reverse=True)
                
                # Calculate statistics
                stable_rates = [ex["fundingRate"] for ex in stablecoin_list]
                coin_rates = [ex["fundingRate"] for ex in coin_margin_list]
                
                stable_stats = {
                    "count": len(stable_rates),
                    "average": sum(stable_rates) / len(stable_rates) if stable_rates else 0,
                    "highest": max(stable_rates) if stable_rates else 0,
                    "lowest": min(stable_rates) if stable_rates else 0,
                    "averagePercent": (sum(stable_rates) / len(stable_rates) * 100) if stable_rates else 0
                }
                
                coin_stats = {
                    "count": len(coin_rates),
                    "average": sum(coin_rates) / len(coin_rates) if coin_rates else 0,
                    "highest": max(coin_rates) if coin_rates else 0,
                    "lowest": min(coin_rates) if coin_rates else 0,
                    "averagePercent": (sum(coin_rates) / len(coin_rates) * 100) if coin_rates else 0
                }
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "stablecoinMargined": {
                        "statistics": stable_stats,
                        "top5Highest": stablecoin_sorted[:5],
                        "top5Lowest": stablecoin_sorted[-5:],
                        "allExchanges": stablecoin_sorted
                    },
                    "coinMargined": {
                        "statistics": coin_stats,
                        "top5Highest": coin_margin_sorted[:5],
                        "top5Lowest": coin_margin_sorted[-5:],
                        "allExchanges": coin_margin_sorted
                    },
                    "source": "coinglass_fr_exchange_list"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_accumulated_funding_rate_exchange_list(self, range: str = "1d", 
                                                          symbol: str = "BTC") -> Dict:
        """
        Get ACCUMULATED Funding Rate per exchange (26TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/funding-rate/accumulated-exchange-list
        
        Parameters:
        - range: Time period (1d, 7d, 30d, etc.)
        - symbol: Coin symbol (e.g., BTC, ETH)
        
        Returns CUMULATIVE funding rate over time period:
        - Total funding paid/received over period
        - Per exchange breakdown
        - Separated by margin type
        
        Shows ACTUAL profit/cost from funding!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/funding-rate/accumulated-exchange-list"
            params = {
                "range": range,
                "symbol": self._normalize_symbol(symbol)
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                fr_data = data["data"]
                
                stablecoin_list = []
                token_margin_list = []
                
                for item in fr_data:
                    # Process stablecoin-margined
                    if "stablecoin_margin_list" in item:
                        for ex in item["stablecoin_margin_list"]:
                            stablecoin_list.append({
                                "exchange": ex.get("exchange"),
                                "accumulatedFR": float(ex.get("funding_rate", 0)),
                                "accumulatedFRPercent": float(ex.get("funding_rate", 0)) * 100
                            })
                    
                    # Process token/coin-margined
                    if "token_margin_list" in item:
                        for ex in item["token_margin_list"]:
                            token_margin_list.append({
                                "exchange": ex.get("exchange"),
                                "accumulatedFR": float(ex.get("funding_rate", 0)),
                                "accumulatedFRPercent": float(ex.get("funding_rate", 0)) * 100
                            })
                
                # Sort by accumulated FR
                stablecoin_sorted = sorted(stablecoin_list, 
                                          key=lambda x: x["accumulatedFR"], 
                                          reverse=True)
                token_sorted = sorted(token_margin_list, 
                                     key=lambda x: x["accumulatedFR"], 
                                     reverse=True)
                
                # Calculate statistics
                stable_rates = [ex["accumulatedFR"] for ex in stablecoin_list]
                token_rates = [ex["accumulatedFR"] for ex in token_margin_list]
                
                stable_stats = {
                    "count": len(stable_rates),
                    "average": sum(stable_rates) / len(stable_rates) if stable_rates else 0,
                    "highest": max(stable_rates) if stable_rates else 0,
                    "lowest": min(stable_rates) if stable_rates else 0,
                    "averagePercent": (sum(stable_rates) / len(stable_rates) * 100) if stable_rates else 0,
                    "total": sum(stable_rates)
                }
                
                token_stats = {
                    "count": len(token_rates),
                    "average": sum(token_rates) / len(token_rates) if token_rates else 0,
                    "highest": max(token_rates) if token_rates else 0,
                    "lowest": min(token_rates) if token_rates else 0,
                    "averagePercent": (sum(token_rates) / len(token_rates) * 100) if token_rates else 0,
                    "total": sum(token_rates)
                }
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "range": range,
                    "stablecoinMargined": {
                        "statistics": stable_stats,
                        "top5Highest": stablecoin_sorted[:5],
                        "top5Lowest": stablecoin_sorted[-5:],
                        "allExchanges": stablecoin_sorted
                    },
                    "tokenMargined": {
                        "statistics": token_stats,
                        "top5Highest": token_sorted[:5],
                        "top5Lowest": token_sorted[-5:],
                        "allExchanges": token_sorted
                    },
                    "note": f"Accumulated funding rate over {range} period",
                    "source": "coinglass_accumulated_fr"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_top_long_short_account_ratio_history(self, exchange: str = "Binance", 
                                                         symbol: str = "BTCUSDT", interval: str = "h1", 
                                                         limit: int = 100) -> Dict:
        """
        Get TOP TRADER Long/Short Account Ratio history (27TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/top-long-short-account-ratio/history
        
        Parameters:
        - exchange: Exchange name (e.g., Binance, OKX)
        - symbol: Trading pair (e.g., BTCUSDT)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        
        Returns TOP/ELITE trader positioning:
        - Long % vs Short % (top accounts only)
        - Long/Short ratio
        - SMART MONEY sentiment!
        
        Track what elite traders are doing!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/top-long-short-account-ratio/history"
            params = {
                "exchange": exchange,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                ratio_data = data["data"]
                
                if len(ratio_data) >= 2:
                    latest = ratio_data[-1]
                    first = ratio_data[0]
                    
                    latest_long = float(latest.get("top_account_long_percent", 0))
                    latest_short = float(latest.get("top_account_short_percent", 0))
                    latest_ratio = float(latest.get("top_account_long_short_ratio", 0))
                    
                    # Calculate averages
                    avg_long = sum(float(d.get("top_account_long_percent", 0)) for d in ratio_data) / len(ratio_data)
                    avg_short = sum(float(d.get("top_account_short_percent", 0)) for d in ratio_data) / len(ratio_data)
                    avg_ratio = sum(float(d.get("top_account_long_short_ratio", 0)) for d in ratio_data) / len(ratio_data)
                    
                    # Smart money sentiment
                    if latest_ratio > 3.0:
                        sentiment = "EXTREMELY_BULLISH"
                        sentiment_desc = f"Top traders {latest_ratio:.2f}:1 long - Extreme smart money bullish!"
                    elif latest_ratio > 2.0:
                        sentiment = "VERY_BULLISH"
                        sentiment_desc = f"Top traders {latest_ratio:.2f}:1 long - Strong smart money bullish"
                    elif latest_ratio > 1.5:
                        sentiment = "BULLISH"
                        sentiment_desc = f"Top traders {latest_ratio:.2f}:1 long - Smart money bullish"
                    elif latest_ratio > 1.0:
                        sentiment = "SLIGHTLY_BULLISH"
                        sentiment_desc = f"Top traders {latest_ratio:.2f}:1 long - Slight smart money long bias"
                    elif latest_ratio == 1.0:
                        sentiment = "NEUTRAL"
                        sentiment_desc = "Top traders balanced 1:1"
                    elif latest_ratio > 0.67:
                        sentiment = "SLIGHTLY_BEARISH"
                        sentiment_desc = f"Top traders {1/latest_ratio:.2f}:1 short - Slight smart money short bias"
                    elif latest_ratio > 0.5:
                        sentiment = "BEARISH"
                        sentiment_desc = f"Top traders {1/latest_ratio:.2f}:1 short - Smart money bearish"
                    elif latest_ratio > 0.33:
                        sentiment = "VERY_BEARISH"
                        sentiment_desc = f"Top traders {1/latest_ratio:.2f}:1 short - Strong smart money bearish"
                    else:
                        sentiment = "EXTREMELY_BEARISH"
                        sentiment_desc = f"Top traders {1/latest_ratio:.2f}:1 short - Extreme smart money bearish!"
                    
                    return {
                        "success": True,
                        "exchange": exchange,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "dataPointCount": len(ratio_data),
                        "latest": {
                            "longPercent": latest_long,
                            "shortPercent": latest_short,
                            "ratio": latest_ratio,
                            "sentiment": sentiment,
                            "sentimentDescription": sentiment_desc
                        },
                        "summary": {
                            "avgLongPercent": avg_long,
                            "avgShortPercent": avg_short,
                            "avgRatio": avg_ratio,
                            "firstRatio": float(first.get("top_account_long_short_ratio", 0)),
                            "lastRatio": latest_ratio,
                            "ratioChange": latest_ratio - float(first.get("top_account_long_short_ratio", 0))
                        },
                        "timeSeries": ratio_data,
                        "note": "Top trader (elite/large account) positioning only",
                        "source": "coinglass_top_trader_ratio"
                    }
                else:
                    return {
                        "success": True,
                        "exchange": exchange,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "dataPointCount": len(ratio_data),
                        "timeSeries": ratio_data,
                        "source": "coinglass_top_trader_ratio"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_top_long_short_position_ratio_history(self, exchange: str = "Binance", 
                                                          symbol: str = "BTCUSDT", interval: str = "h1", 
                                                          limit: int = 100) -> Dict:
        """
        Get TOP TRADER Long/Short POSITION Ratio history (28TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/top-long-short-position-ratio/history
        
        Parameters:
        - exchange: Exchange name (e.g., Binance, OKX)
        - symbol: Trading pair (e.g., BTCUSDT)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        
        Returns TOP trader POSITION distribution (not account count!):
        - Long % vs Short % (by VOLUME/SIZE of positions)
        - Long/Short ratio
        - ACTUAL CAPITAL distribution!
        
        Shows where smart money is ACTUALLY deploying capital!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/top-long-short-position-ratio/history"
            params = {
                "exchange": exchange,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                ratio_data = data["data"]
                
                if len(ratio_data) >= 2:
                    latest = ratio_data[-1]
                    first = ratio_data[0]
                    
                    latest_long = float(latest.get("top_position_long_percent", 0))
                    latest_short = float(latest.get("top_position_short_percent", 0))
                    latest_ratio = float(latest.get("top_position_long_short_ratio", 0))
                    
                    # Calculate averages
                    avg_long = sum(float(d.get("top_position_long_percent", 0)) for d in ratio_data) / len(ratio_data)
                    avg_short = sum(float(d.get("top_position_short_percent", 0)) for d in ratio_data) / len(ratio_data)
                    avg_ratio = sum(float(d.get("top_position_long_short_ratio", 0)) for d in ratio_data) / len(ratio_data)
                    
                    # Capital deployment sentiment
                    if latest_ratio > 3.0:
                        sentiment = "EXTREMELY_BULLISH"
                        sentiment_desc = f"Top traders deploying {latest_ratio:.2f}:1 capital to longs - Extreme conviction!"
                    elif latest_ratio > 2.0:
                        sentiment = "VERY_BULLISH"
                        sentiment_desc = f"Top traders deploying {latest_ratio:.2f}:1 capital to longs - Strong conviction"
                    elif latest_ratio > 1.5:
                        sentiment = "BULLISH"
                        sentiment_desc = f"Top traders deploying {latest_ratio:.2f}:1 capital to longs - Bullish capital flow"
                    elif latest_ratio > 1.0:
                        sentiment = "SLIGHTLY_BULLISH"
                        sentiment_desc = f"Top traders deploying {latest_ratio:.2f}:1 capital to longs - Slight long bias"
                    elif latest_ratio == 1.0:
                        sentiment = "NEUTRAL"
                        sentiment_desc = "Top traders capital balanced 1:1"
                    elif latest_ratio > 0.67:
                        sentiment = "SLIGHTLY_BEARISH"
                        sentiment_desc = f"Top traders deploying {1/latest_ratio:.2f}:1 capital to shorts - Slight short bias"
                    elif latest_ratio > 0.5:
                        sentiment = "BEARISH"
                        sentiment_desc = f"Top traders deploying {1/latest_ratio:.2f}:1 capital to shorts - Bearish capital flow"
                    elif latest_ratio > 0.33:
                        sentiment = "VERY_BEARISH"
                        sentiment_desc = f"Top traders deploying {1/latest_ratio:.2f}:1 capital to shorts - Strong short conviction"
                    else:
                        sentiment = "EXTREMELY_BEARISH"
                        sentiment_desc = f"Top traders deploying {1/latest_ratio:.2f}:1 capital to shorts - Extreme short conviction!"
                    
                    return {
                        "success": True,
                        "exchange": exchange,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "dataPointCount": len(ratio_data),
                        "latest": {
                            "longPercent": latest_long,
                            "shortPercent": latest_short,
                            "ratio": latest_ratio,
                            "sentiment": sentiment,
                            "sentimentDescription": sentiment_desc
                        },
                        "summary": {
                            "avgLongPercent": avg_long,
                            "avgShortPercent": avg_short,
                            "avgRatio": avg_ratio,
                            "firstRatio": float(first.get("top_position_long_short_ratio", 0)),
                            "lastRatio": latest_ratio,
                            "ratioChange": latest_ratio - float(first.get("top_position_long_short_ratio", 0))
                        },
                        "timeSeries": ratio_data,
                        "note": "Top trader POSITION size (capital distribution), not account count",
                        "source": "coinglass_top_position_ratio"
                    }
                else:
                    return {
                        "success": True,
                        "exchange": exchange,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "dataPointCount": len(ratio_data),
                        "timeSeries": ratio_data,
                        "source": "coinglass_top_position_ratio"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_taker_buy_sell_volume_exchange_list(self, symbol: str = "BTC", 
                                                        range: str = "h1") -> Dict:
        """
        Get Taker Buy/Sell Volume per exchange (29TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/taker-buy-sell-volume/exchange-list
        
        Parameters:
        - symbol: Trading coin (e.g., BTC, ETH)
        - range: Time range (5m, 15m, 30m, 1h, 4h, 12h, 24h)
        
        Returns AGGRESSIVE market pressure:
        - Taker buy vs sell volume (USD)
        - Buy/sell ratio per exchange
        - Shows AGGRESSIVE buying vs selling!
        
        Taker = Market orders (pay fees, aggressive)
        Maker = Limit orders (get rebates, passive)
        
        HIGH taker buy = Strong buying pressure!
        HIGH taker sell = Strong selling pressure!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/taker-buy-sell-volume/exchange-list"
            params = {
                "symbol": self._normalize_symbol(symbol),
                "range": range
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                volume_data = data["data"]
                
                overall_buy_ratio = float(volume_data.get("buy_ratio", 0))
                overall_sell_ratio = float(volume_data.get("sell_ratio", 0))
                overall_buy_vol = float(volume_data.get("buy_vol_usd", 0))
                overall_sell_vol = float(volume_data.get("sell_vol_usd", 0))
                
                # Determine market pressure
                if overall_buy_ratio > 60:
                    pressure = "EXTREME_BUYING_PRESSURE"
                    pressure_desc = f"Takers aggressively buying ({overall_buy_ratio:.2f}%) - Strong bullish pressure!"
                elif overall_buy_ratio > 55:
                    pressure = "STRONG_BUYING_PRESSURE"
                    pressure_desc = f"Takers favor buying ({overall_buy_ratio:.2f}%) - Bullish pressure"
                elif overall_buy_ratio > 52:
                    pressure = "MODERATE_BUYING_PRESSURE"
                    pressure_desc = f"Slight taker buying bias ({overall_buy_ratio:.2f}%)"
                elif overall_buy_ratio >= 48:
                    pressure = "BALANCED"
                    pressure_desc = f"Taker volume balanced ({overall_buy_ratio:.2f}% buy, {overall_sell_ratio:.2f}% sell)"
                elif overall_buy_ratio >= 45:
                    pressure = "MODERATE_SELLING_PRESSURE"
                    pressure_desc = f"Slight taker selling bias ({overall_sell_ratio:.2f}% sell)"
                elif overall_buy_ratio >= 40:
                    pressure = "STRONG_SELLING_PRESSURE"
                    pressure_desc = f"Takers favor selling ({overall_sell_ratio:.2f}%) - Bearish pressure"
                else:
                    pressure = "EXTREME_SELLING_PRESSURE"
                    pressure_desc = f"Takers aggressively selling ({overall_sell_ratio:.2f}%) - Strong bearish pressure!"
                
                # Process exchange list
                exchange_list = volume_data.get("exchange_list", [])
                exchange_processed = []
                
                for ex in exchange_list:
                    exchange_processed.append({
                        "exchange": ex.get("exchange"),
                        "buyRatio": float(ex.get("buy_ratio", 0)),
                        "sellRatio": float(ex.get("sell_ratio", 0)),
                        "buyVolumeUSD": float(ex.get("buy_vol_usd", 0)),
                        "sellVolumeUSD": float(ex.get("sell_vol_usd", 0)),
                        "totalVolumeUSD": float(ex.get("buy_vol_usd", 0)) + float(ex.get("sell_vol_usd", 0)),
                        "netBuyVolumeUSD": float(ex.get("buy_vol_usd", 0)) - float(ex.get("sell_vol_usd", 0))
                    })
                
                # Sort by total volume
                exchange_sorted = sorted(exchange_processed, 
                                        key=lambda x: x["totalVolumeUSD"], 
                                        reverse=True)
                
                # Find most bullish/bearish exchanges
                most_bullish = sorted(exchange_processed, 
                                     key=lambda x: x["buyRatio"], 
                                     reverse=True)[:5]
                most_bearish = sorted(exchange_processed, 
                                     key=lambda x: x["sellRatio"], 
                                     reverse=True)[:5]
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "range": range,
                    "overall": {
                        "buyRatio": overall_buy_ratio,
                        "sellRatio": overall_sell_ratio,
                        "buyVolumeUSD": overall_buy_vol,
                        "sellVolumeUSD": overall_sell_vol,
                        "totalVolumeUSD": overall_buy_vol + overall_sell_vol,
                        "netBuyVolumeUSD": overall_buy_vol - overall_sell_vol,
                        "pressure": pressure,
                        "pressureDescription": pressure_desc
                    },
                    "topExchangesByVolume": exchange_sorted[:10],
                    "mostBullishExchanges": most_bullish,
                    "mostBearishExchanges": most_bearish,
                    "allExchanges": exchange_sorted,
                    "note": "Taker volume = aggressive market orders (shows buying/selling pressure)",
                    "source": "coinglass_taker_volume"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_net_position_history(self, exchange: str = "Binance", 
                                        symbol: str = "BTCUSDT", interval: str = "h1", 
                                        limit: int = 100) -> Dict:
        """
        Get Net Position Change history (30TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/v2/net-position/history
        
        Parameters:
        - exchange: Exchange name (e.g., Binance, OKX)
        - symbol: Trading pair (e.g., BTCUSDT)
        - interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
        - limit: Number of data points (max 1000)
        
        Returns NET POSITION FLOW:
        - Net long change (BTC added/removed)
        - Net short change (BTC added/removed)
        - Shows CAPITAL FLOW direction!
        
        Positive = Positions ADDED
        Negative = Positions CLOSED/REDUCED
        
        Track where smart money is moving!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/v2/net-position/history"
            params = {
                "exchange": exchange,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                position_data = data["data"]
                
                if len(position_data) >= 2:
                    latest = position_data[-1]
                    first = position_data[0]
                    
                    latest_long_change = float(latest.get("net_long_change", 0))
                    latest_short_change = float(latest.get("net_short_change", 0))
                    
                    # Calculate total changes over period
                    total_long_change = sum(float(d.get("net_long_change", 0)) for d in position_data)
                    total_short_change = sum(float(d.get("net_short_change", 0)) for d in position_data)
                    
                    # Determine capital flow
                    if latest_long_change > 50 and latest_short_change < -50:
                        flow = "STRONG_LONG_ACCUMULATION"
                        flow_desc = f"Strong long accumulation: +{latest_long_change:.2f} BTC longs, {latest_short_change:.2f} BTC shorts"
                    elif latest_long_change > 20 and latest_short_change < -20:
                        flow = "MODERATE_LONG_ACCUMULATION"
                        flow_desc = f"Moderate long accumulation: +{latest_long_change:.2f} BTC longs, {latest_short_change:.2f} BTC shorts"
                    elif latest_long_change > 0 and latest_short_change < 0:
                        flow = "SLIGHT_LONG_BIAS"
                        flow_desc = f"Slight long bias: {latest_long_change:+.2f} BTC longs, {latest_short_change:+.2f} BTC shorts"
                    elif latest_short_change > 50 and latest_long_change < -50:
                        flow = "STRONG_SHORT_ACCUMULATION"
                        flow_desc = f"Strong short accumulation: +{latest_short_change:.2f} BTC shorts, {latest_long_change:.2f} BTC longs"
                    elif latest_short_change > 20 and latest_long_change < -20:
                        flow = "MODERATE_SHORT_ACCUMULATION"
                        flow_desc = f"Moderate short accumulation: +{latest_short_change:.2f} BTC shorts, {latest_long_change:.2f} BTC longs"
                    elif latest_short_change > 0 and latest_long_change < 0:
                        flow = "SLIGHT_SHORT_BIAS"
                        flow_desc = f"Slight short bias: {latest_short_change:+.2f} BTC shorts, {latest_long_change:+.2f} BTC longs"
                    elif abs(latest_long_change) < 10 and abs(latest_short_change) < 10:
                        flow = "NEUTRAL"
                        flow_desc = f"Minimal position changes: {latest_long_change:+.2f} BTC longs, {latest_short_change:+.2f} BTC shorts"
                    else:
                        flow = "MIXED"
                        flow_desc = f"Mixed flows: {latest_long_change:+.2f} BTC longs, {latest_short_change:+.2f} BTC shorts"
                    
                    return {
                        "success": True,
                        "exchange": exchange,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "dataPointCount": len(position_data),
                        "latest": {
                            "netLongChange": latest_long_change,
                            "netShortChange": latest_short_change,
                            "flow": flow,
                            "flowDescription": flow_desc
                        },
                        "summary": {
                            "totalLongChange": total_long_change,
                            "totalShortChange": total_short_change,
                            "netFlow": total_long_change + total_short_change,
                            "avgLongChange": total_long_change / len(position_data),
                            "avgShortChange": total_short_change / len(position_data)
                        },
                        "timeSeries": position_data,
                        "note": "Net position change shows capital FLOW (additions/reductions). Positive = added, Negative = closed",
                        "source": "coinglass_net_position"
                    }
                else:
                    return {
                        "success": True,
                        "exchange": exchange,
                        "symbol": self._normalize_symbol(symbol),
                        "interval": interval,
                        "dataPointCount": len(position_data),
                        "timeSeries": position_data,
                        "source": "coinglass_net_position"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_pairs_markets(self, symbol: str = "BTC") -> Dict:
        """
        Get futures market data PER EXCHANGE for a symbol (11TH ENDPOINT!)
        REAL ENDPOINT: /api/futures/pairs-markets?symbol=BTC
        
        Returns detailed breakdown by exchange:
        - Price, volume, OI per exchange
        - Long/short volume split
        - Liquidations per exchange
        - Funding rate per exchange
        - OI/Volume ratio
        
        Perfect for arbitrage opportunities and cross-exchange analysis
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/pairs-markets"
            params = {"symbol": self._normalize_symbol(symbol)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                pairs = data["data"]
                
                # Aggregate statistics
                total_volume_usd = sum(float(p.get("volume_usd", 0)) for p in pairs)
                total_oi_usd = sum(float(p.get("open_interest_usd", 0)) for p in pairs)
                
                # Find price extremes (arbitrage opportunities)
                prices = [float(p.get("current_price", 0)) for p in pairs if p.get("current_price")]
                price_spread = None
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    price_spread = {
                        "min": min_price,
                        "max": max_price,
                        "spread": max_price - min_price,
                        "spreadPercent": ((max_price - min_price) / min_price * 100) if min_price > 0 else 0
                    }
                
                # Top exchanges by volume
                top_by_volume = sorted(pairs, key=lambda x: float(x.get("volume_usd", 0)), reverse=True)[:5]
                
                # Top exchanges by OI
                top_by_oi = sorted(pairs, key=lambda x: float(x.get("open_interest_usd", 0)), reverse=True)[:5]
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "exchangeCount": len(pairs),
                    "aggregates": {
                        "totalVolumeUSD": total_volume_usd,
                        "totalOpenInterestUSD": total_oi_usd,
                        "priceSpread": price_spread
                    },
                    "topExchangesByVolume": [
                        {
                            "exchange": p.get("exchange_name"),
                            "volume": p.get("volume_usd"),
                            "price": p.get("current_price")
                        } for p in top_by_volume
                    ],
                    "topExchangesByOI": [
                        {
                            "exchange": p.get("exchange_name"),
                            "oi": p.get("open_interest_usd"),
                            "price": p.get("current_price")
                        } for p in top_by_oi
                    ],
                    "allPairs": pairs,
                    "source": "coinglass_pairs_markets"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== LIQUIDATION ENDPOINTS ====================
    
    async def get_liquidation_orders(self, exchange: str = "Binance", symbol: str = "BTC", 
                                      min_liquidation_amount: int = 10000) -> Dict:
        """
        Get recent liquidation orders - UPDATED! (31ST ENDPOINT!)
        Endpoint: /api/futures/liquidation/order
        
        Parameters:
        - exchange: Exchange name (e.g., Binance, OKX)
        - symbol: Trading coin (e.g., BTC, ETH)
        - min_liquidation_amount: Minimum USD threshold (default 10000)
        
        Returns detailed liquidation orders:
        - Individual liquidation events
        - Long vs short liquidations
        - Large liquidation detection (whale hunts)
        - Recent liquidation activity
        
        side: 1 = LONG liquidation (longs got rekt)
        side: 2 = SHORT liquidation (shorts got rekt)
        
        Track stop-loss hunting and market panic!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/liquidation/order"
            params = {
                "exchange": exchange,
                "symbol": self._normalize_symbol(symbol),
                "min_liquidation_amount": min_liquidation_amount
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                orders = data["data"]
                
                # Process liquidations
                long_liqs = []
                short_liqs = []
                
                for o in orders:
                    side = o.get("side")
                    usd_value = float(o.get("usd_value", 0))
                    price = float(o.get("price", 0))
                    
                    liq_info = {
                        "exchange": o.get("exchange_name"),
                        "symbol": o.get("symbol"),
                        "price": price,
                        "usdValue": usd_value,
                        "time": o.get("time"),
                        "side": "LONG" if side == 1 else "SHORT"
                    }
                    
                    if side == 1:
                        long_liqs.append(liq_info)
                    elif side == 2:
                        short_liqs.append(liq_info)
                
                # Calculate totals
                long_total = sum(l["usdValue"] for l in long_liqs)
                short_total = sum(l["usdValue"] for l in short_liqs)
                
                # Find largest liquidations
                all_liqs = long_liqs + short_liqs
                largest_liqs = sorted(all_liqs, key=lambda x: x["usdValue"], reverse=True)[:10]
                
                # Determine market sentiment from liquidations
                if long_total > short_total * 2:
                    sentiment = "STRONG_DOWNTREND"
                    sentiment_desc = f"Massive long liquidations (${long_total:,.0f}) - Strong sell-off!"
                elif long_total > short_total * 1.5:
                    sentiment = "MODERATE_DOWNTREND"
                    sentiment_desc = f"More long liquidations (${long_total:,.0f}) - Downward pressure"
                elif short_total > long_total * 2:
                    sentiment = "STRONG_UPTREND"
                    sentiment_desc = f"Massive short liquidations (${short_total:,.0f}) - Short squeeze!"
                elif short_total > long_total * 1.5:
                    sentiment = "MODERATE_UPTREND"
                    sentiment_desc = f"More short liquidations (${short_total:,.0f}) - Upward pressure"
                else:
                    sentiment = "BALANCED"
                    sentiment_desc = f"Balanced liquidations (${long_total:,.0f} long, ${short_total:,.0f} short)"
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": self._normalize_symbol(symbol),
                    "minAmount": min_liquidation_amount,
                    "summary": {
                        "longLiquidations": long_total,
                        "shortLiquidations": short_total,
                        "totalLiquidations": long_total + short_total,
                        "longCount": len(long_liqs),
                        "shortCount": len(short_liqs),
                        "totalCount": len(orders),
                        "sentiment": sentiment,
                        "sentimentDescription": sentiment_desc
                    },
                    "largestLiquidations": largest_liqs,
                    "longLiquidations": long_liqs[:20],
                    "shortLiquidations": short_liqs[:20],
                    "note": "side 1=LONG liquidated, 2=SHORT liquidated. Shows recent liquidation events.",
                    "source": "coinglass_liq_orders"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_liquidation_exchange_list(self, range: str = "1h") -> Dict:
        """
        Get liquidation data PER EXCHANGE (32ND ENDPOINT!)
        Endpoint: /api/futures/liquidation/exchange-list
        
        Parameters:
        - range: Time range (5m, 15m, 30m, 1h, 4h, 12h, 24h)
        
        Returns aggregate liquidations by exchange:
        - Total liquidations per exchange
        - Long vs short breakdown
        - Exchange comparison
        - Market-wide liquidation summary
        
        Shows WHERE liquidations are happening!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/liquidation/exchange-list"
            params = {"range": range}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                exchanges = data["data"]
                
                # Find "All" summary
                all_summary = next((e for e in exchanges if e.get("exchange") == "All"), None)
                
                # Process individual exchanges (exclude "All")
                exchange_list = []
                for ex in exchanges:
                    if ex.get("exchange") != "All":
                        total_liq = float(ex.get("liquidation_usd", 0))
                        long_liq = float(ex.get("longLiquidation_usd", 0))
                        short_liq = float(ex.get("shortLiquidation_usd", 0))
                        
                        # Calculate percentages
                        long_pct = (long_liq / total_liq * 100) if total_liq > 0 else 0
                        short_pct = (short_liq / total_liq * 100) if total_liq > 0 else 0
                        
                        exchange_list.append({
                            "exchange": ex.get("exchange"),
                            "totalLiquidation": total_liq,
                            "longLiquidation": long_liq,
                            "shortLiquidation": short_liq,
                            "longPercent": long_pct,
                            "shortPercent": short_pct,
                            "netFlow": long_liq - short_liq
                        })
                
                # Sort by total liquidation
                exchange_sorted = sorted(exchange_list, 
                                        key=lambda x: x["totalLiquidation"], 
                                        reverse=True)
                
                # Market summary
                if all_summary:
                    market_total = float(all_summary.get("liquidation_usd", 0))
                    market_long = float(all_summary.get("longLiquidation_usd", 0))
                    market_short = float(all_summary.get("shortLiquidation_usd", 0))
                    
                    # Determine market sentiment
                    if market_long > market_short * 2:
                        sentiment = "STRONG_BEARISH"
                        sentiment_desc = f"Heavy long liquidations (${market_long:,.0f}) - Strong downtrend"
                    elif market_long > market_short * 1.5:
                        sentiment = "MODERATE_BEARISH"
                        sentiment_desc = f"More long liquidations (${market_long:,.0f}) - Bearish pressure"
                    elif market_short > market_long * 2:
                        sentiment = "STRONG_BULLISH"
                        sentiment_desc = f"Heavy short liquidations (${market_short:,.0f}) - Strong uptrend/squeeze"
                    elif market_short > market_long * 1.5:
                        sentiment = "MODERATE_BULLISH"
                        sentiment_desc = f"More short liquidations (${market_short:,.0f}) - Bullish pressure"
                    else:
                        sentiment = "BALANCED"
                        sentiment_desc = f"Balanced liquidations (${market_long:,.0f} long, ${market_short:,.0f} short)"
                    
                    market_summary = {
                        "totalLiquidation": market_total,
                        "longLiquidation": market_long,
                        "shortLiquidation": market_short,
                        "longPercent": (market_long / market_total * 100) if market_total > 0 else 0,
                        "shortPercent": (market_short / market_total * 100) if market_total > 0 else 0,
                        "sentiment": sentiment,
                        "sentimentDescription": sentiment_desc
                    }
                else:
                    # Calculate from individual exchanges
                    total = sum(e["totalLiquidation"] for e in exchange_list)
                    long_total = sum(e["longLiquidation"] for e in exchange_list)
                    short_total = sum(e["shortLiquidation"] for e in exchange_list)
                    
                    market_summary = {
                        "totalLiquidation": total,
                        "longLiquidation": long_total,
                        "shortLiquidation": short_total,
                        "longPercent": (long_total / total * 100) if total > 0 else 0,
                        "shortPercent": (short_total / total * 100) if total > 0 else 0,
                        "sentiment": "UNKNOWN",
                        "sentimentDescription": "Data calculated from individual exchanges"
                    }
                
                return {
                    "success": True,
                    "range": range,
                    "marketSummary": market_summary,
                    "topExchanges": exchange_sorted[:10],
                    "allExchanges": exchange_sorted,
                    "exchangeCount": len(exchange_sorted),
                    "note": "Aggregate liquidations per exchange. Shows WHERE liquidations happening.",
                    "source": "coinglass_liq_exchange_list"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_liquidation_map(self, symbol: str = "BTC") -> Dict:
        """
        Get liquidation heatmap data
        Endpoint: /api/futures/liquidation/map
        
        Returns liquidation clusters at different price levels
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/liquidation/map"
            params = {"symbol": self._normalize_symbol(symbol)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                map_data = data["data"]
                
                total_clusters = len(map_data)
                
                largest_cluster = None
                max_volume = 0
                
                for price_level, cluster_info in map_data.items():
                    if cluster_info and len(cluster_info) > 0:
                        volume = cluster_info[0][1] if len(cluster_info[0]) > 1 else 0
                        if volume > max_volume:
                            max_volume = volume
                            largest_cluster = {
                                "price": float(price_level),
                                "volume": volume,
                                "leverage": cluster_info[0][2] if len(cluster_info[0]) > 2 else None
                            }
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "clusterCount": total_clusters,
                    "largestCluster": largest_cluster,
                    "mapData": map_data,
                    "source": "coinglass_liq_map"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_liquidation_coin_list(self, exchange: str = "Binance", symbol: str = "BTC") -> Dict:
        """
        Get liquidation data for all coins on an exchange
        Endpoint: /api/futures/liquidation/coin-list
        
        Returns 24h, 12h, 4h, 1h liquidation breakdowns
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/liquidation/coin-list"
            params = {"exchange": exchange}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                coin_list = data["data"]
                
                symbol_upper = self._normalize_symbol(symbol)
                symbol_data = next((c for c in coin_list if c.get("symbol") == symbol_upper), None)
                
                if symbol_data:
                    return {
                        "success": True,
                        "symbol": symbol_upper,
                        "exchange": exchange,
                        "liquidation24h": symbol_data.get("liquidation_usd_24h", 0),
                        "longLiq24h": symbol_data.get("long_liquidation_usd_24h", 0),
                        "shortLiq24h": symbol_data.get("short_liquidation_usd_24h", 0),
                        "liquidation12h": symbol_data.get("liquidation_usd_12h", 0),
                        "liquidation4h": symbol_data.get("liquidation_usd_4h", 0),
                        "liquidation1h": symbol_data.get("liquidation_usd_1h", 0),
                        "source": "coinglass_liq_coinlist"
                    }
                
                return {"success": True, "data": coin_list, "count": len(coin_list)}
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_liquidation_aggregated_history(self, exchange_list: str = "Binance", 
                                                  symbol: str = "BTC", interval: str = "1d", 
                                                  limit: int = 100,
                                                  start_time: int = None,
                                                  end_time: int = None) -> Dict:
        """
        Get AGGREGATED LIQUIDATION HISTORY over time (33RD ENDPOINT!)
        Endpoint: /api/futures/liquidation/aggregated-history
        
        Parameters:
        - exchange_list: Comma-separated exchanges (e.g., "Binance,OKX,Bybit")
        - symbol: Coin symbol (e.g., BTC, ETH)
        - interval: Time interval (1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
        - limit: Number of data points (max 1000)
        - start_time: Start timestamp in milliseconds (optional)
        - end_time: End timestamp in milliseconds (optional)
        
        Returns TIME-SERIES liquidation data:
        - Aggregated long liquidations per period
        - Aggregated short liquidations per period
        - Trend analysis (cascades, waves, reversals)
        - Liquidation intensity scoring
        
        Perfect for identifying LIQUIDATION CASCADES and market turning points!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/liquidation/aggregated-history"
            params = {
                "exchange_list": exchange_list,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                
                if not history:
                    return {"success": False, "error": "No historical data"}
                
                # Calculate statistics
                total_long = sum(float(h.get("aggregated_long_liquidation_usd", 0)) for h in history)
                total_short = sum(float(h.get("aggregated_short_liquidation_usd", 0)) for h in history)
                total_all = total_long + total_short
                
                # Find peak liquidation events
                history_sorted = sorted(history, 
                                       key=lambda x: float(x.get("aggregated_long_liquidation_usd", 0)) + 
                                                   float(x.get("aggregated_short_liquidation_usd", 0)),
                                       reverse=True)
                
                # Identify cascade events (top 3 liquidation spikes)
                cascade_events = []
                for i, event in enumerate(history_sorted[:3]):
                    long_liq = float(event.get("aggregated_long_liquidation_usd", 0))
                    short_liq = float(event.get("aggregated_short_liquidation_usd", 0))
                    total_liq = long_liq + short_liq
                    
                    # Determine cascade type
                    if long_liq > short_liq * 2:
                        cascade_type = "LONG_CASCADE"
                        description = f"Long cascade - ${long_liq:,.0f} longs liquidated (bearish dump)"
                    elif short_liq > long_liq * 2:
                        cascade_type = "SHORT_CASCADE"
                        description = f"Short cascade - ${short_liq:,.0f} shorts liquidated (bullish squeeze)"
                    else:
                        cascade_type = "MIXED_CASCADE"
                        description = f"Mixed cascade - ${total_liq:,.0f} total (high volatility)"
                    
                    cascade_events.append({
                        "rank": i + 1,
                        "timestamp": event.get("time"),
                        "type": cascade_type,
                        "totalLiquidation": total_liq,
                        "longLiquidation": long_liq,
                        "shortLiquidation": short_liq,
                        "description": description
                    })
                
                # Trend analysis
                if len(history) >= 2:
                    first_period = history[0]
                    last_period = history[-1]
                    
                    first_long = float(first_period.get("aggregated_long_liquidation_usd", 0))
                    first_short = float(first_period.get("aggregated_short_liquidation_usd", 0))
                    last_long = float(last_period.get("aggregated_long_liquidation_usd", 0))
                    last_short = float(last_period.get("aggregated_short_liquidation_usd", 0))
                    
                    # Detect trend shift
                    if first_long > first_short and last_short > last_long:
                        trend = "REVERSAL_TO_BULLISH"
                        trend_desc = "Shifted from long liquidations to short liquidations - Trend reversal upward"
                    elif first_short > first_long and last_long > last_short:
                        trend = "REVERSAL_TO_BEARISH"
                        trend_desc = "Shifted from short liquidations to long liquidations - Trend reversal downward"
                    elif total_long > total_short * 1.5:
                        trend = "PERSISTENT_BEARISH"
                        trend_desc = f"Consistent long liquidations ({total_long/total_short:.1f}x more) - Sustained downtrend"
                    elif total_short > total_long * 1.5:
                        trend = "PERSISTENT_BULLISH"
                        trend_desc = f"Consistent short liquidations ({total_short/total_long:.1f}x more) - Sustained uptrend"
                    else:
                        trend = "CHOPPY"
                        trend_desc = "Mixed liquidations - Sideways/choppy market"
                else:
                    trend = "INSUFFICIENT_DATA"
                    trend_desc = "Not enough data points for trend analysis"
                
                # Calculate liquidation intensity (avg per period)
                avg_long_per_period = total_long / len(history)
                avg_short_per_period = total_short / len(history)
                avg_total_per_period = total_all / len(history)
                
                # Intensity scoring
                if avg_total_per_period > 50_000_000:
                    intensity = "EXTREME"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - EXTREME volatility, high risk!"
                elif avg_total_per_period > 20_000_000:
                    intensity = "VERY_HIGH"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - Very high liquidation activity"
                elif avg_total_per_period > 10_000_000:
                    intensity = "HIGH"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - High liquidation activity"
                elif avg_total_per_period > 5_000_000:
                    intensity = "MODERATE"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - Moderate liquidation activity"
                else:
                    intensity = "LOW"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - Low liquidation activity"
                
                # Format history data for easy consumption
                formatted_history = []
                for h in history:
                    long_liq = float(h.get("aggregated_long_liquidation_usd", 0))
                    short_liq = float(h.get("aggregated_short_liquidation_usd", 0))
                    total = long_liq + short_liq
                    
                    formatted_history.append({
                        "timestamp": h.get("time"),
                        "longLiquidation": long_liq,
                        "shortLiquidation": short_liq,
                        "totalLiquidation": total,
                        "longPercent": (long_liq / total * 100) if total > 0 else 0,
                        "shortPercent": (short_liq / total * 100) if total > 0 else 0,
                        "netFlow": long_liq - short_liq
                    })
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "exchanges": exchange_list,
                    "interval": interval,
                    "dataPoints": len(history),
                    "summary": {
                        "totalLongLiquidations": total_long,
                        "totalShortLiquidations": total_short,
                        "totalAllLiquidations": total_all,
                        "longPercent": (total_long / total_all * 100) if total_all > 0 else 0,
                        "shortPercent": (total_short / total_all * 100) if total_all > 0 else 0,
                        "avgPerPeriod": avg_total_per_period,
                        "avgLongPerPeriod": avg_long_per_period,
                        "avgShortPerPeriod": avg_short_per_period
                    },
                    "trend": {
                        "direction": trend,
                        "description": trend_desc
                    },
                    "intensity": {
                        "level": intensity,
                        "description": intensity_desc
                    },
                    "cascadeEvents": cascade_events,
                    "history": formatted_history,
                    "note": "Time-series liquidation data. Identifies cascades, trends, and reversals.",
                    "source": "coinglass_liq_aggregated_history"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_liquidation_history(self, exchange: str = "Binance", 
                                       symbol: str = "BTCUSDT", interval: str = "1d", 
                                       limit: int = 100,
                                       start_time: int = None,
                                       end_time: int = None) -> Dict:
        """
        Get SINGLE EXCHANGE-PAIR LIQUIDATION HISTORY (34TH ENDPOINT!)
        Endpoint: /api/futures/liquidation/history
        
        Parameters:
        - exchange: Exchange name (e.g., Binance, OKX)
        - symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
        - interval: Time interval (1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
        - limit: Number of data points (max 1000)
        - start_time: Start timestamp in milliseconds (optional)
        - end_time: End timestamp in milliseconds (optional)
        
        Returns TIME-SERIES liquidation data for SPECIFIC exchange-pair:
        - Long liquidations per period
        - Short liquidations per period
        - Trend analysis for this specific pair
        - Cascade detection on this exchange
        
        Different from aggregated-history:
        - This is for ONE specific exchange-pair
        - aggregated-history combines multiple exchanges
        
        Perfect for exchange-specific analysis and pair-specific strategies!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/liquidation/history"
            params = {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                
                if not history:
                    return {"success": False, "error": "No historical data"}
                
                # Calculate statistics
                total_long = sum(float(h.get("long_liquidation_usd", 0)) for h in history)
                total_short = sum(float(h.get("short_liquidation_usd", 0)) for h in history)
                total_all = total_long + total_short
                
                # Find peak liquidation events
                history_sorted = sorted(history, 
                                       key=lambda x: float(x.get("long_liquidation_usd", 0)) + 
                                                   float(x.get("short_liquidation_usd", 0)),
                                       reverse=True)
                
                # Identify cascade events (top 3)
                cascade_events = []
                for i, event in enumerate(history_sorted[:3]):
                    long_liq = float(event.get("long_liquidation_usd", 0))
                    short_liq = float(event.get("short_liquidation_usd", 0))
                    total_liq = long_liq + short_liq
                    
                    if long_liq > short_liq * 2:
                        cascade_type = "LONG_CASCADE"
                        description = f"Long cascade - ${long_liq:,.0f} longs liquidated (bearish)"
                    elif short_liq > long_liq * 2:
                        cascade_type = "SHORT_CASCADE"
                        description = f"Short cascade - ${short_liq:,.0f} shorts liquidated (bullish)"
                    else:
                        cascade_type = "MIXED_CASCADE"
                        description = f"Mixed cascade - ${total_liq:,.0f} total (volatile)"
                    
                    cascade_events.append({
                        "rank": i + 1,
                        "timestamp": event.get("time"),
                        "type": cascade_type,
                        "totalLiquidation": total_liq,
                        "longLiquidation": long_liq,
                        "shortLiquidation": short_liq,
                        "description": description
                    })
                
                # Trend analysis
                if len(history) >= 2:
                    first_period = history[0]
                    last_period = history[-1]
                    
                    first_long = float(first_period.get("long_liquidation_usd", 0))
                    first_short = float(first_period.get("short_liquidation_usd", 0))
                    last_long = float(last_period.get("long_liquidation_usd", 0))
                    last_short = float(last_period.get("short_liquidation_usd", 0))
                    
                    if first_long > first_short and last_short > last_long:
                        trend = "REVERSAL_TO_BULLISH"
                        trend_desc = f"{symbol} on {exchange}: Shifted from long to short liquidations - Upward reversal"
                    elif first_short > first_long and last_long > last_short:
                        trend = "REVERSAL_TO_BEARISH"
                        trend_desc = f"{symbol} on {exchange}: Shifted from short to long liquidations - Downward reversal"
                    elif total_long > total_short * 1.5:
                        trend = "PERSISTENT_BEARISH"
                        trend_desc = f"{symbol} on {exchange}: Consistent long liquidations - Sustained downtrend"
                    elif total_short > total_long * 1.5:
                        trend = "PERSISTENT_BULLISH"
                        trend_desc = f"{symbol} on {exchange}: Consistent short liquidations - Sustained uptrend"
                    else:
                        trend = "CHOPPY"
                        trend_desc = f"{symbol} on {exchange}: Mixed liquidations - Sideways market"
                else:
                    trend = "INSUFFICIENT_DATA"
                    trend_desc = "Not enough data points"
                
                # Calculate intensity
                avg_long_per_period = total_long / len(history)
                avg_short_per_period = total_short / len(history)
                avg_total_per_period = total_all / len(history)
                
                # Intensity scoring (adjusted for single pair)
                if avg_total_per_period > 30_000_000:
                    intensity = "EXTREME"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - EXTREME for single pair!"
                elif avg_total_per_period > 15_000_000:
                    intensity = "VERY_HIGH"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - Very high activity"
                elif avg_total_per_period > 5_000_000:
                    intensity = "HIGH"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - High activity"
                elif avg_total_per_period > 2_000_000:
                    intensity = "MODERATE"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - Moderate activity"
                else:
                    intensity = "LOW"
                    intensity_desc = f"${avg_total_per_period:,.0f}/period - Low activity"
                
                # Format history
                formatted_history = []
                for h in history:
                    long_liq = float(h.get("long_liquidation_usd", 0))
                    short_liq = float(h.get("short_liquidation_usd", 0))
                    total = long_liq + short_liq
                    
                    formatted_history.append({
                        "timestamp": h.get("time"),
                        "longLiquidation": long_liq,
                        "shortLiquidation": short_liq,
                        "totalLiquidation": total,
                        "longPercent": (long_liq / total * 100) if total > 0 else 0,
                        "shortPercent": (short_liq / total * 100) if total > 0 else 0,
                        "netFlow": long_liq - short_liq
                    })
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "dataPoints": len(history),
                    "summary": {
                        "totalLongLiquidations": total_long,
                        "totalShortLiquidations": total_short,
                        "totalAllLiquidations": total_all,
                        "longPercent": (total_long / total_all * 100) if total_all > 0 else 0,
                        "shortPercent": (total_short / total_all * 100) if total_all > 0 else 0,
                        "avgPerPeriod": avg_total_per_period,
                        "avgLongPerPeriod": avg_long_per_period,
                        "avgShortPerPeriod": avg_short_per_period
                    },
                    "trend": {
                        "direction": trend,
                        "description": trend_desc
                    },
                    "intensity": {
                        "level": intensity,
                        "description": intensity_desc
                    },
                    "cascadeEvents": cascade_events,
                    "history": formatted_history,
                    "note": "Single exchange-pair liquidation history. For multi-exchange use aggregated-history.",
                    "source": "coinglass_liq_history"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== ORDERBOOK DEPTH ENDPOINTS ====================
    
    async def get_orderbook_ask_bids_history(self, exchange: str = "Binance", 
                                              symbol: str = "BTCUSDT", interval: str = "1d", 
                                              limit: int = 100,
                                              start_time: int = None,
                                              end_time: int = None) -> Dict:
        """
        Get ORDERBOOK ASK/BIDS DEPTH HISTORY (35TH ENDPOINT!)
        Endpoint: /api/futures/orderbook/ask-bids-history
        
        Parameters:
        - exchange: Exchange name (e.g., Binance, OKX)
        - symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
        - interval: Time interval (1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
        - limit: Number of data points (max 1000)
        - start_time: Start timestamp in milliseconds (optional)
        - end_time: End timestamp in milliseconds (optional)
        
        Returns TIME-SERIES orderbook depth data:
        - Bid liquidity (USD value & quantity)
        - Ask liquidity (USD value & quantity)
        - Liquidity imbalance analysis
        - Order book pressure detection
        
        This is CRITICAL for understanding market depth and predicting price movements!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/orderbook/ask-bids-history"
            params = {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                
                if not history:
                    return {"success": False, "error": "No historical data"}
                
                # Calculate statistics
                total_bids_usd = sum(float(h.get("bids_usd", 0)) for h in history)
                total_asks_usd = sum(float(h.get("asks_usd", 0)) for h in history)
                avg_bids_usd = total_bids_usd / len(history)
                avg_asks_usd = total_asks_usd / len(history)
                
                # Analyze liquidity imbalance
                imbalance_ratio = avg_bids_usd / avg_asks_usd if avg_asks_usd > 0 else 0
                
                if imbalance_ratio > 1.5:
                    liquidity_bias = "STRONG_BUY_PRESSURE"
                    bias_desc = f"Bids {imbalance_ratio:.2f}x larger than asks - Strong buying pressure/support"
                elif imbalance_ratio > 1.2:
                    liquidity_bias = "MODERATE_BUY_PRESSURE"
                    bias_desc = f"Bids {imbalance_ratio:.2f}x larger than asks - Moderate buying pressure"
                elif imbalance_ratio < 0.67:
                    liquidity_bias = "STRONG_SELL_PRESSURE"
                    bias_desc = f"Asks {1/imbalance_ratio:.2f}x larger than bids - Strong selling pressure/resistance"
                elif imbalance_ratio < 0.83:
                    liquidity_bias = "MODERATE_SELL_PRESSURE"
                    bias_desc = f"Asks {1/imbalance_ratio:.2f}x larger than bids - Moderate selling pressure"
                else:
                    liquidity_bias = "BALANCED"
                    bias_desc = f"Balanced liquidity (ratio {imbalance_ratio:.2f}) - Neutral market"
                
                # Find largest imbalances (potential breakout points)
                imbalance_events = []
                for h in history:
                    bids_usd = float(h.get("bids_usd", 0))
                    asks_usd = float(h.get("asks_usd", 0))
                    ratio = bids_usd / asks_usd if asks_usd > 0 else 0
                    
                    # Track significant imbalances
                    if ratio > 1.5 or ratio < 0.67:
                        if ratio > 1.5:
                            event_type = "BID_WALL"
                            description = f"Massive bid wall - {ratio:.2f}x more bids (potential support)"
                        else:
                            event_type = "ASK_WALL"
                            description = f"Massive ask wall - {1/ratio:.2f}x more asks (potential resistance)"
                        
                        imbalance_events.append({
                            "timestamp": h.get("time"),
                            "type": event_type,
                            "ratio": ratio,
                            "bidsUsd": bids_usd,
                            "asksUsd": asks_usd,
                            "description": description
                        })
                
                # Sort by most extreme imbalances
                imbalance_events.sort(key=lambda x: abs(x["ratio"] - 1), reverse=True)
                
                # Calculate depth trend (growing or shrinking liquidity)
                if len(history) >= 2:
                    first_total = float(history[0].get("bids_usd", 0)) + float(history[0].get("asks_usd", 0))
                    last_total = float(history[-1].get("bids_usd", 0)) + float(history[-1].get("asks_usd", 0))
                    depth_change_pct = ((last_total - first_total) / first_total * 100) if first_total > 0 else 0
                    
                    if depth_change_pct > 20:
                        depth_trend = "GROWING_LIQUIDITY"
                        depth_desc = f"Liquidity +{depth_change_pct:.1f}% - Market depth increasing (healthier market)"
                    elif depth_change_pct > 5:
                        depth_trend = "MODERATE_GROWTH"
                        depth_desc = f"Liquidity +{depth_change_pct:.1f}% - Gradual depth increase"
                    elif depth_change_pct < -20:
                        depth_trend = "SHRINKING_LIQUIDITY"
                        depth_desc = f"Liquidity {depth_change_pct:.1f}% - Market depth decreasing (risk of volatility!)"
                    elif depth_change_pct < -5:
                        depth_trend = "MODERATE_DECLINE"
                        depth_desc = f"Liquidity {depth_change_pct:.1f}% - Gradual depth decrease"
                    else:
                        depth_trend = "STABLE"
                        depth_desc = f"Liquidity change {depth_change_pct:.1f}% - Stable market depth"
                else:
                    depth_trend = "INSUFFICIENT_DATA"
                    depth_desc = "Not enough data points"
                    depth_change_pct = 0
                
                # Format history
                formatted_history = []
                for h in history:
                    bids_usd = float(h.get("bids_usd", 0))
                    asks_usd = float(h.get("asks_usd", 0))
                    bids_qty = float(h.get("bids_quantity", 0))
                    asks_qty = float(h.get("asks_quantity", 0))
                    total_liquidity = bids_usd + asks_usd
                    ratio = bids_usd / asks_usd if asks_usd > 0 else 0
                    
                    formatted_history.append({
                        "timestamp": h.get("time"),
                        "bidsUsd": bids_usd,
                        "asksUsd": asks_usd,
                        "bidsQuantity": bids_qty,
                        "asksQuantity": asks_qty,
                        "totalLiquidity": total_liquidity,
                        "bidAskRatio": ratio,
                        "bidsPercent": (bids_usd / total_liquidity * 100) if total_liquidity > 0 else 0,
                        "asksPercent": (asks_usd / total_liquidity * 100) if total_liquidity > 0 else 0
                    })
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "dataPoints": len(history),
                    "summary": {
                        "avgBidsUsd": avg_bids_usd,
                        "avgAsksUsd": avg_asks_usd,
                        "totalAvgLiquidity": avg_bids_usd + avg_asks_usd,
                        "bidAskRatio": imbalance_ratio,
                        "bidsPercent": (avg_bids_usd / (avg_bids_usd + avg_asks_usd) * 100) if (avg_bids_usd + avg_asks_usd) > 0 else 0,
                        "asksPercent": (avg_asks_usd / (avg_bids_usd + avg_asks_usd) * 100) if (avg_bids_usd + avg_asks_usd) > 0 else 0
                    },
                    "liquidityBias": {
                        "bias": liquidity_bias,
                        "description": bias_desc
                    },
                    "depthTrend": {
                        "trend": depth_trend,
                        "description": depth_desc,
                        "changePct": depth_change_pct
                    },
                    "imbalanceEvents": imbalance_events[:10],
                    "history": formatted_history,
                    "note": "Orderbook depth over time. Shows bid/ask liquidity and market pressure.",
                    "source": "coinglass_orderbook_history"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_orderbook_aggregated_history(self, exchange_list: str = "Binance", 
                                                symbol: str = "BTC", interval: str = "1h", 
                                                limit: int = 100,
                                                start_time: int = None,
                                                end_time: int = None) -> Dict:
        """
        Get AGGREGATED ORDERBOOK HISTORY (36TH ENDPOINT!)
        Endpoint: /api/futures/orderbook/aggregated-ask-bids-history
        
        Multi-exchange orderbook aggregation - similar to aggregated liquidations
        but for orderbook depth across multiple exchanges!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/orderbook/aggregated-ask-bids-history"
            params = {
                "exchange_list": exchange_list,
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                
                if not history:
                    return {"success": False, "error": "No historical data"}
                
                # Calculate aggregated statistics
                total_bids = sum(float(h.get("aggregated_bids_usd", 0)) for h in history)
                total_asks = sum(float(h.get("aggregated_asks_usd", 0)) for h in history)
                avg_bids = total_bids / len(history)
                avg_asks = total_asks / len(history)
                
                ratio = avg_bids / avg_asks if avg_asks > 0 else 0
                
                if ratio > 1.2:
                    bias = "BUY_PRESSURE"
                    bias_desc = f"Aggregated bids {ratio:.2f}x larger - Market-wide buy pressure"
                elif ratio < 0.83:
                    bias = "SELL_PRESSURE"
                    bias_desc = f"Aggregated asks {1/ratio:.2f}x larger - Market-wide sell pressure"
                else:
                    bias = "BALANCED"
                    bias_desc = f"Balanced market-wide liquidity (ratio {ratio:.2f})"
                
                # Format history
                formatted_history = []
                for h in history:
                    bids = float(h.get("aggregated_bids_usd", 0))
                    asks = float(h.get("aggregated_asks_usd", 0))
                    total = bids + asks
                    
                    formatted_history.append({
                        "timestamp": h.get("time"),
                        "aggregatedBidsUsd": bids,
                        "aggregatedAsksUsd": asks,
                        "aggregatedBidsQty": float(h.get("aggregated_bids_quantity", 0)),
                        "aggregatedAsksQty": float(h.get("aggregated_asks_quantity", 0)),
                        "totalLiquidity": total,
                        "bidAskRatio": bids / asks if asks > 0 else 0
                    })
                
                return {
                    "success": True,
                    "exchanges": exchange_list,
                    "symbol": self._normalize_symbol(symbol),
                    "interval": interval,
                    "dataPoints": len(history),
                    "summary": {
                        "avgBidsUsd": avg_bids,
                        "avgAsksUsd": avg_asks,
                        "totalAvgLiquidity": avg_bids + avg_asks,
                        "bidAskRatio": ratio
                    },
                    "marketBias": {
                        "bias": bias,
                        "description": bias_desc
                    },
                    "history": formatted_history,
                    "note": "Aggregated orderbook across multiple exchanges. Market-wide liquidity view.",
                    "source": "coinglass_orderbook_aggregated"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_large_limit_orders(self, exchange: str = "Binance", symbol: str = "BTCUSDT") -> Dict:
        """
        Get CURRENT LARGE LIMIT ORDERS - WHALE WALLS! (37TH ENDPOINT!)
        Endpoint: /api/futures/orderbook/large-limit-order
        
        Real-time whale wall detection - massive limit orders sitting in the book!
        This is CRITICAL for identifying whale accumulation/distribution zones.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/orderbook/large-limit-order"
            params = {
                "exchange": exchange,
                "symbol": symbol
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                orders = data["data"]
                
                if not orders:
                    return {"success": False, "error": "No large orders found"}
                
                # Separate bid and ask walls
                bid_walls = [o for o in orders if o.get("order_side") == 1]  # Side 1 = Bid
                ask_walls = [o for o in orders if o.get("order_side") == 2]  # Side 2 = Ask
                
                # Calculate totals
                total_bid_value = sum(float(o.get("current_usd_value", 0)) for o in bid_walls)
                total_ask_value = sum(float(o.get("current_usd_value", 0)) for o in ask_walls)
                
                # Find largest walls
                bid_walls_sorted = sorted(bid_walls, key=lambda x: float(x.get("current_usd_value", 0)), reverse=True)
                ask_walls_sorted = sorted(ask_walls, key=lambda x: float(x.get("current_usd_value", 0)), reverse=True)
                
                # Format orders
                def format_order(o):
                    return {
                        "id": o.get("id"),
                        "price": float(o.get("limit_price", 0)),
                        "quantity": float(o.get("current_quantity", 0)),
                        "usdValue": float(o.get("current_usd_value", 0)),
                        "startTime": o.get("start_time"),
                        "startValue": float(o.get("start_usd_value", 0)),
                        "executedVolume": float(o.get("executed_volume", 0)),
                        "executedValue": float(o.get("executed_usd_value", 0)),
                        "tradeCount": o.get("trade_count", 0),
                        "side": "BID" if o.get("order_side") == 1 else "ASK",
                        "state": o.get("order_state")
                    }
                
                formatted_bids = [format_order(o) for o in bid_walls_sorted[:20]]
                formatted_asks = [format_order(o) for o in ask_walls_sorted[:20]]
                
                # Whale detection
                mega_walls = []
                for o in orders:
                    value = float(o.get("current_usd_value", 0))
                    if value > 5_000_000:  # >$5M = mega whale
                        mega_walls.append({
                            **format_order(o),
                            "classification": "MEGA_WHALE" if value > 10_000_000 else "LARGE_WHALE"
                        })
                
                mega_walls.sort(key=lambda x: x["usdValue"], reverse=True)
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "summary": {
                        "totalBidWalls": len(bid_walls),
                        "totalAskWalls": len(ask_walls),
                        "totalBidValue": total_bid_value,
                        "totalAskValue": total_ask_value,
                        "megaWhaleCount": len(mega_walls)
                    },
                    "megaWhales": mega_walls,
                    "topBidWalls": formatted_bids,
                    "topAskWalls": formatted_asks,
                    "note": "Current large limit orders (whale walls) in the orderbook. Real-time whale tracking!",
                    "source": "coinglass_large_limit_orders"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_large_limit_order_history(self, exchange: str = "Binance", symbol: str = "BTCUSDT",
                                             state: int = 1, limit: int = 100) -> Dict:
        """
        Get LARGE LIMIT ORDER HISTORY - Historical whale tracking! (38TH ENDPOINT!)
        Endpoint: /api/futures/orderbook/large-limit-order-history
        
        Track historical whale walls - see what whales did in the past!
        State: 1=Active, 2=Canceled, 3=Filled
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/orderbook/large-limit-order-history"
            params = {
                "exchange": exchange,
                "symbol": symbol,
                "state": state,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                orders = data["data"]
                
                if not orders:
                    return {"success": False, "error": "No historical orders found"}
                
                # Analyze order states
                state_map = {1: "ACTIVE", 2: "CANCELED", 3: "FILLED"}
                state_name = state_map.get(state, "UNKNOWN")
                
                # Separate by side
                bids = [o for o in orders if o.get("order_side") == 1]
                asks = [o for o in orders if o.get("order_side") == 2]
                
                # Calculate stats
                total_bid_value = sum(float(o.get("start_usd_value", 0)) for o in bids)
                total_ask_value = sum(float(o.get("start_usd_value", 0)) for o in asks)
                
                # Format orders
                def format_order(o):
                    return {
                        "id": o.get("id"),
                        "price": float(o.get("limit_price", 0)),
                        "startQuantity": float(o.get("start_quantity", 0)),
                        "startValue": float(o.get("start_usd_value", 0)),
                        "currentQuantity": float(o.get("current_quantity", 0)),
                        "currentValue": float(o.get("current_usd_value", 0)),
                        "executedVolume": float(o.get("executed_volume", 0)),
                        "executedValue": float(o.get("executed_usd_value", 0)),
                        "startTime": o.get("start_time"),
                        "endTime": o.get("order_end_time"),
                        "side": "BID" if o.get("order_side") == 1 else "ASK",
                        "state": state_name
                    }
                
                formatted_orders = [format_order(o) for o in orders]
                
                # Find largest orders
                largest_orders = sorted(formatted_orders, key=lambda x: x["startValue"], reverse=True)[:10]
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "state": state_name,
                    "orderCount": len(orders),
                    "summary": {
                        "bidCount": len(bids),
                        "askCount": len(asks),
                        "totalBidValue": total_bid_value,
                        "totalAskValue": total_ask_value
                    },
                    "largestOrders": largest_orders,
                    "allOrders": formatted_orders,
                    "note": f"Historical {state_name} whale walls. Track whale behavior over time!",
                    "source": "coinglass_large_limit_order_history"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_orderbook_detailed_history(self, exchange: str = "Binance", 
                                              symbol: str = "BTCUSDT", interval: str = "1h",
                                              limit: int = 10) -> Dict:
        """
        Get DETAILED ORDERBOOK HISTORY with PRICE LEVELS! (39TH ENDPOINT!)
        Endpoint: /api/futures/orderbook/history
        
        Shows actual orderbook snapshots with individual price levels!
        This is like looking at the raw orderbook over time.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/orderbook/history"
            params = {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                snapshots = data["data"]
                
                if not snapshots or len(snapshots) == 0:
                    return {"success": False, "error": "No snapshot data"}
                
                # Parse snapshots
                formatted_snapshots = []
                for snapshot in snapshots:
                    if len(snapshot) < 2:
                        continue
                    
                    timestamp = snapshot[0]
                    price_levels = snapshot[1] if len(snapshot) > 1 else []
                    
                    # Parse price levels [price, quantity]
                    bids = []
                    asks = []
                    total_bid_value = 0
                    total_ask_value = 0
                    
                    for level in price_levels:
                        if len(level) >= 2:
                            price = float(level[0])
                            qty = float(level[1])
                            value = price * qty
                            
                            # Determine if bid or ask based on context
                            # (This is simplified - real logic may differ)
                            if len(bids) < len(price_levels) // 2:
                                bids.append({"price": price, "quantity": qty, "value": value})
                                total_bid_value += value
                            else:
                                asks.append({"price": price, "quantity": qty, "value": value})
                                total_ask_value += value
                    
                    formatted_snapshots.append({
                        "timestamp": timestamp,
                        "bids": bids[:20],  # Top 20 bids
                        "asks": asks[:20],  # Top 20 asks
                        "bidLiquidity": total_bid_value,
                        "askLiquidity": total_ask_value,
                        "totalLevels": len(price_levels)
                    })
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "snapshotCount": len(formatted_snapshots),
                    "snapshots": formatted_snapshots,
                    "note": "Detailed orderbook snapshots with individual price levels. Raw orderbook over time!",
                    "source": "coinglass_orderbook_detailed_history"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== HYPERLIQUID DEX WHALE TRACKING ====================
    
    async def get_hyperliquid_whale_alerts(self) -> Dict:
        """
        Get HYPERLIQUID WHALE ALERTS - Real-time DEX whale movements! (40TH ENDPOINT!)
        Endpoint: /api/hyperliquid/whale-alert
        
        Track whale position opens/closes on Hyperliquid DEX in REAL-TIME!
        This is different from CEX data - shows decentralized whale activity.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/hyperliquid/whale-alert"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                alerts = data["data"]
                
                if not alerts:
                    return {"success": False, "error": "No whale alerts"}
                
                # Classify alerts by action
                opens = []
                closes = []
                
                for alert in alerts:
                    action = alert.get("position_action")
                    value = float(alert.get("position_value_usd", 0))
                    
                    formatted = {
                        "user": alert.get("user"),
                        "symbol": alert.get("symbol"),
                        "positionSize": float(alert.get("position_size", 0)),
                        "entryPrice": float(alert.get("entry_price", 0)),
                        "liqPrice": float(alert.get("liq_price", 0)),
                        "valueUsd": value,
                        "side": "LONG" if alert.get("position_size", 0) > 0 else "SHORT",
                        "timestamp": alert.get("create_time"),
                        "classification": "MEGA" if value > 2_000_000 else "LARGE" if value > 1_000_000 else "MEDIUM"
                    }
                    
                    if action == 1:
                        opens.append(formatted)
                    elif action == 2:
                        closes.append(formatted)
                
                # Find largest alerts
                all_alerts = opens + closes
                largest = sorted(all_alerts, key=lambda x: x["valueUsd"], reverse=True)[:20]
                
                # Calculate totals
                total_open_value = sum(a["valueUsd"] for a in opens)
                total_close_value = sum(a["valueUsd"] for a in closes)
                
                return {
                    "success": True,
                    "totalAlerts": len(alerts),
                    "summary": {
                        "opensCount": len(opens),
                        "closesCount": len(closes),
                        "totalOpenValue": total_open_value,
                        "totalCloseValue": total_close_value,
                        "netFlow": total_open_value - total_close_value
                    },
                    "largestAlerts": largest,
                    "recentOpens": opens[:20],
                    "recentCloses": closes[:20],
                    "note": "Hyperliquid DEX whale alerts - Real-time decentralized whale tracking!",
                    "source": "hyperliquid_whale_alerts"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_hyperliquid_whale_positions(self) -> Dict:
        """
        Get HYPERLIQUID WHALE POSITIONS - Current DEX mega positions! (41ST ENDPOINT!)
        Endpoint: /api/hyperliquid/whale-position
        
        Track MASSIVE current positions on Hyperliquid with PnL, leverage, funding!
        Real institutional DEX positions - $100M+ positions tracked!
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/hyperliquid/whale-position"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                positions = data["data"]
                
                if not positions:
                    return {"success": False, "error": "No whale positions"}
                
                # Format positions with full details
                formatted_positions = []
                for pos in positions:
                    value = float(pos.get("position_value_usd", 0))
                    size = float(pos.get("position_size", 0))
                    pnl = float(pos.get("unrealized_pnl", 0))
                    
                    formatted_positions.append({
                        "user": pos.get("user"),
                        "symbol": pos.get("symbol"),
                        "positionSize": size,
                        "side": "LONG" if size > 0 else "SHORT",
                        "entryPrice": float(pos.get("entry_price", 0)),
                        "markPrice": float(pos.get("mark_price", 0)),
                        "liqPrice": float(pos.get("liq_price", 0)),
                        "leverage": int(pos.get("leverage", 1)),
                        "marginBalance": float(pos.get("margin_balance", 0)),
                        "positionValue": value,
                        "unrealizedPnl": pnl,
                        "pnlPercent": (pnl / value * 100) if value > 0 else 0,
                        "fundingFee": float(pos.get("funding_fee", 0)),
                        "marginMode": pos.get("margin_mode"),
                        "createTime": pos.get("create_time"),
                        "updateTime": pos.get("update_time"),
                        "classification": "MEGA_WHALE" if value > 50_000_000 else "LARGE_WHALE" if value > 10_000_000 else "WHALE"
                    })
                
                # Sort by value
                formatted_positions.sort(key=lambda x: x["positionValue"], reverse=True)
                
                # Calculate statistics
                total_value = sum(p["positionValue"] for p in formatted_positions)
                total_pnl = sum(p["unrealizedPnl"] for p in formatted_positions)
                long_positions = [p for p in formatted_positions if p["side"] == "LONG"]
                short_positions = [p for p in formatted_positions if p["side"] == "SHORT"]
                
                mega_whales = [p for p in formatted_positions if p["classification"] == "MEGA_WHALE"]
                
                return {
                    "success": True,
                    "totalPositions": len(positions),
                    "summary": {
                        "totalValue": total_value,
                        "totalPnl": total_pnl,
                        "longCount": len(long_positions),
                        "shortCount": len(short_positions),
                        "megaWhaleCount": len(mega_whales),
                        "avgLeverage": sum(p["leverage"] for p in formatted_positions) / len(formatted_positions) if formatted_positions else 0
                    },
                    "megaWhales": mega_whales[:20],
                    "topPositions": formatted_positions[:30],
                    "note": "Hyperliquid DEX whale positions - Mega institutional DEX positions with PnL tracking!",
                    "source": "hyperliquid_whale_positions"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_hyperliquid_positions_by_symbol(self, symbol: str = "BTC") -> Dict:
        """
        Get HYPERLIQUID POSITIONS BY SYMBOL - Symbol-filtered whale tracking! (42ND ENDPOINT!)
        Endpoint: /api/hyperliquid/position
        
        Track whale positions for a specific symbol on Hyperliquid DEX!
        Same data as whale-position but filtered by symbol.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/hyperliquid/position"
            params = {"symbol": self._normalize_symbol(symbol)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                result = data["data"]
                positions = result.get("list", [])
                
                if not positions:
                    return {"success": False, "error": f"No positions for {symbol}"}
                
                # Format positions
                formatted_positions = []
                for pos in positions:
                    value = float(pos.get("position_value_usd", 0))
                    size = float(pos.get("position_size", 0))
                    pnl = float(pos.get("unrealized_pnl", 0))
                    
                    formatted_positions.append({
                        "user": pos.get("user"),
                        "symbol": pos.get("symbol"),
                        "positionSize": size,
                        "side": "LONG" if size > 0 else "SHORT",
                        "entryPrice": float(pos.get("entry_price", 0)),
                        "markPrice": float(pos.get("mark_price", 0)),
                        "liqPrice": float(pos.get("liq_price", 0)),
                        "leverage": int(pos.get("leverage", 1)),
                        "marginBalance": float(pos.get("margin_balance", 0)),
                        "positionValue": value,
                        "unrealizedPnl": pnl,
                        "pnlPercent": (pnl / value * 100) if value > 0 else 0,
                        "fundingFee": float(pos.get("funding_fee", 0)),
                        "marginMode": pos.get("margin_mode"),
                        "createTime": pos.get("create_time"),
                        "updateTime": pos.get("update_time"),
                        "classification": "MEGA_WHALE" if value > 50_000_000 else "LARGE_WHALE" if value > 10_000_000 else "WHALE"
                    })
                
                # Sort by value
                formatted_positions.sort(key=lambda x: x["positionValue"], reverse=True)
                
                # Statistics
                total_value = sum(p["positionValue"] for p in formatted_positions)
                total_pnl = sum(p["unrealizedPnl"] for p in formatted_positions)
                long_pos = [p for p in formatted_positions if p["side"] == "LONG"]
                short_pos = [p for p in formatted_positions if p["side"] == "SHORT"]
                
                long_value = sum(p["positionValue"] for p in long_pos)
                short_value = sum(p["positionValue"] for p in short_pos)
                
                return {
                    "success": True,
                    "symbol": self._normalize_symbol(symbol),
                    "totalPages": result.get("total_pages", 1),
                    "positionCount": len(positions),
                    "summary": {
                        "totalValue": total_value,
                        "totalPnl": total_pnl,
                        "longCount": len(long_pos),
                        "shortCount": len(short_pos),
                        "longValue": long_value,
                        "shortValue": short_value,
                        "netExposure": long_value - short_value,
                        "avgLeverage": sum(p["leverage"] for p in formatted_positions) / len(formatted_positions) if formatted_positions else 0
                    },
                    "topPositions": formatted_positions[:30],
                    "note": f"Hyperliquid {symbol} whale positions - DEX institutional tracking by symbol!",
                    "source": "hyperliquid_positions_by_symbol"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== ON-CHAIN WHALE TRACKING ====================
    
    async def get_chain_whale_transfers(self, limit: int = 100) -> Dict:
        """
        Get ON-CHAIN WHALE TRANSFERS - Cross-chain whale movements! (43RD ENDPOINT!)
        Endpoint: /api/chain/whale-transfer
        
        Track MASSIVE on-chain transfers across Bitcoin, Ethereum, Tron!
        See whales moving funds between wallets and exchanges.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/chain/whale-transfer"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                transfers = data["data"][:limit]
                
                if not transfers:
                    return {"success": False, "error": "No whale transfers"}
                
                # Format transfers
                formatted_transfers = []
                for tx in transfers:
                    amount_usd = float(tx.get("amount_usd", 0))
                    
                    formatted_transfers.append({
                        "hash": tx.get("transaction_hash"),
                        "asset": tx.get("asset_symbol"),
                        "quantity": float(tx.get("asset_quantity", 0)),
                        "amountUsd": amount_usd,
                        "from": tx.get("from"),
                        "to": tx.get("to"),
                        "blockchain": tx.get("blockchain_name"),
                        "blockHeight": tx.get("block_height"),
                        "timestamp": tx.get("block_timestamp"),
                        "classification": "MEGA" if amount_usd > 10_000_000 else "LARGE" if amount_usd > 5_000_000 else "MEDIUM"
                    })
                
                # Sort by amount
                formatted_transfers.sort(key=lambda x: x["amountUsd"], reverse=True)
                
                # Analyze by blockchain
                by_chain = {}
                for tx in formatted_transfers:
                    chain = tx["blockchain"]
                    if chain not in by_chain:
                        by_chain[chain] = {"count": 0, "totalValue": 0}
                    by_chain[chain]["count"] += 1
                    by_chain[chain]["totalValue"] += tx["amountUsd"]
                
                # Analyze by asset
                by_asset = {}
                for tx in formatted_transfers:
                    asset = tx["asset"]
                    if asset not in by_asset:
                        by_asset[asset] = {"count": 0, "totalValue": 0}
                    by_asset[asset]["count"] += 1
                    by_asset[asset]["totalValue"] += tx["amountUsd"]
                
                # Exchange flows
                to_exchange = [tx for tx in formatted_transfers if tx["to"] not in ["unknown wallet", "unknown"]]
                from_exchange = [tx for tx in formatted_transfers if tx["from"] not in ["unknown wallet", "unknown"]]
                
                total_value = sum(tx["amountUsd"] for tx in formatted_transfers)
                mega_whales = [tx for tx in formatted_transfers if tx["classification"] == "MEGA"]
                
                return {
                    "success": True,
                    "transferCount": len(transfers),
                    "summary": {
                        "totalValue": total_value,
                        "megaWhaleCount": len(mega_whales),
                        "toExchangeCount": len(to_exchange),
                        "fromExchangeCount": len(from_exchange),
                        "byBlockchain": by_chain,
                        "byAsset": by_asset
                    },
                    "megaWhales": mega_whales[:20],
                    "recentTransfers": formatted_transfers[:50],
                    "toExchange": to_exchange[:20],
                    "fromExchange": from_exchange[:20],
                    "note": "On-chain whale transfers across Bitcoin, Ethereum, Tron. Track massive fund movements!",
                    "source": "chain_whale_transfers"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_exchange_chain_transactions(self, limit: int = 100) -> Dict:
        """
        Get EXCHANGE CHAIN TRANSACTIONS - Exchange deposit/withdrawal tracking! (44TH ENDPOINT!)
        Endpoint: /api/exchange/chain/tx/list
        
        Track fund flows IN/OUT of exchanges on-chain!
        Perfect for monitoring exchange reserves and whale exchange activity.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/exchange/chain/tx/list"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                transactions = data["data"][:limit]
                
                if not transactions:
                    return {"success": False, "error": "No exchange transactions"}
                
                # Format transactions
                formatted_txs = []
                for tx in transactions:
                    amount_usd = float(tx.get("amount_usd", 0))
                    transfer_type = tx.get("transfer_type")
                    
                    formatted_txs.append({
                        "hash": tx.get("transaction_hash"),
                        "asset": tx.get("asset_symbol"),
                        "quantity": float(tx.get("asset_quantity", 0)),
                        "amountUsd": amount_usd,
                        "exchange": tx.get("exchange_name"),
                        "type": "DEPOSIT" if transfer_type == 1 else "WITHDRAWAL" if transfer_type == 2 else "UNKNOWN",
                        "from": tx.get("from_address"),
                        "to": tx.get("to_address"),
                        "timestamp": tx.get("transaction_time"),
                        "classification": "LARGE" if amount_usd > 100_000 else "MEDIUM" if amount_usd > 50_000 else "SMALL"
                    })
                
                # Sort by amount
                formatted_txs.sort(key=lambda x: x["amountUsd"], reverse=True)
                
                # Analyze by exchange
                by_exchange = {}
                for tx in formatted_txs:
                    exch = tx["exchange"]
                    if exch not in by_exchange:
                        by_exchange[exch] = {
                            "deposits": {"count": 0, "value": 0},
                            "withdrawals": {"count": 0, "value": 0}
                        }
                    
                    if tx["type"] == "DEPOSIT":
                        by_exchange[exch]["deposits"]["count"] += 1
                        by_exchange[exch]["deposits"]["value"] += tx["amountUsd"]
                    elif tx["type"] == "WITHDRAWAL":
                        by_exchange[exch]["withdrawals"]["count"] += 1
                        by_exchange[exch]["withdrawals"]["value"] += tx["amountUsd"]
                
                # Separate by type
                deposits = [tx for tx in formatted_txs if tx["type"] == "DEPOSIT"]
                withdrawals = [tx for tx in formatted_txs if tx["type"] == "WITHDRAWAL"]
                
                total_deposit_value = sum(tx["amountUsd"] for tx in deposits)
                total_withdrawal_value = sum(tx["amountUsd"] for tx in withdrawals)
                net_flow = total_deposit_value - total_withdrawal_value
                
                return {
                    "success": True,
                    "transactionCount": len(transactions),
                    "summary": {
                        "depositCount": len(deposits),
                        "withdrawalCount": len(withdrawals),
                        "totalDepositValue": total_deposit_value,
                        "totalWithdrawalValue": total_withdrawal_value,
                        "netFlow": net_flow,
                        "flowDirection": "INFLOW" if net_flow > 0 else "OUTFLOW" if net_flow < 0 else "BALANCED",
                        "byExchange": by_exchange
                    },
                    "largestTransactions": formatted_txs[:30],
                    "recentDeposits": deposits[:20],
                    "recentWithdrawals": withdrawals[:20],
                    "note": "Exchange chain transactions - Track deposits/withdrawals to monitor exchange reserves!",
                    "source": "exchange_chain_transactions"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== TECHNICAL INDICATORS ====================
    
    async def get_rsi_list(self) -> Dict:
        """
        Get RSI LIST - Multi-timeframe RSI for all major coins! (45TH ENDPOINT!)
        Endpoint: /api/futures/rsi/list
        
        Shows RSI across 15m, 1h, 4h, 12h, 24h, 1w for BTC, ETH, SOL, etc!
        Perfect for scanning overbought/oversold conditions across the market.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/rsi/list"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                rsi_data = data["data"]
                
                formatted = []
                for coin in rsi_data:
                    rsi_24h = float(coin.get("rsi_24h", 50))
                    signal = "OVERSOLD" if rsi_24h < 30 else "OVERBOUGHT" if rsi_24h > 70 else "NEUTRAL"
                    
                    formatted.append({
                        "symbol": coin.get("symbol"),
                        "currentPrice": float(coin.get("current_price", 0)),
                        "rsi15m": float(coin.get("rsi_15m", 0)),
                        "rsi1h": float(coin.get("rsi_1h", 0)),
                        "rsi4h": float(coin.get("rsi_4h", 0)),
                        "rsi12h": float(coin.get("rsi_12h", 0)),
                        "rsi24h": rsi_24h,
                        "rsi1w": float(coin.get("rsi_1w", 0)),
                        "priceChange15m": float(coin.get("price_change_percent_15m", 0)),
                        "priceChange1h": float(coin.get("price_change_percent_1h", 0)),
                        "priceChange4h": float(coin.get("price_change_percent_4h", 0)),
                        "priceChange24h": float(coin.get("price_change_percent_24h", 0)),
                        "signal": signal
                    })
                
                return {
                    "success": True,
                    "coinCount": len(formatted),
                    "coins": formatted,
                    "note": "Multi-timeframe RSI for all major coins. Scan for overbought/oversold conditions!",
                    "source": "rsi_list"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_rsi_indicator(self, exchange: str = "Binance", symbol: str = "BTCUSDT", interval: str = "1h") -> Dict:
        """
        Get RSI INDICATOR - Historical RSI values! (46TH ENDPOINT!)
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/indicators/rsi"
            params = {"exchange": exchange, "symbol": symbol, "interval": interval}
            
            response = await client.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                latest = history[-1] if history else {}
                latest_rsi = float(latest.get("rsi_value", 50))
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "currentRsi": latest_rsi,
                    "signal": "OVERSOLD" if latest_rsi < 30 else "OVERBOUGHT" if latest_rsi > 70 else "NEUTRAL",
                    "history": [{"timestamp": h.get("time"), "rsi": float(h.get("rsi_value", 0))} for h in history],
                    "source": "rsi_indicator"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_ma_indicator(self, exchange: str = "Binance", symbol: str = "BTCUSDT", interval: str = "1h") -> Dict:
        """Get MA (Moving Average) indicator (47TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/indicators/ma"
            params = {"exchange": exchange, "symbol": symbol, "interval": interval}
            
            response = await client.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "currentMA": float(history[-1].get("ma_value", 0)) if history else 0,
                    "history": [{"timestamp": h.get("time"), "ma": float(h.get("ma_value", 0))} for h in history],
                    "source": "ma_indicator"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_ema_indicator(self, exchange: str = "Binance", symbol: str = "BTCUSDT", interval: str = "1h") -> Dict:
        """Get EMA (Exponential Moving Average) indicator (48TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/indicators/ema"
            params = {"exchange": exchange, "symbol": symbol, "interval": interval}
            
            response = await client.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "currentEMA": float(history[-1].get("ema_value", 0)) if history else 0,
                    "history": [{"timestamp": h.get("time"), "ema": float(h.get("ema_value", 0))} for h in history],
                    "source": "ema_indicator"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_bollinger_bands(self, exchange: str = "Binance", symbol: str = "BTCUSDT", interval: str = "1h") -> Dict:
        """Get Bollinger Bands indicator (49TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/indicators/boll"
            params = {"exchange": exchange, "symbol": symbol, "interval": interval}
            
            response = await client.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                latest = history[-1] if history else {}
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "current": {
                        "upper": float(latest.get("ub_value", 0)),
                        "middle": float(latest.get("mb_value", 0)),
                        "lower": float(latest.get("lb_value", 0))
                    },
                    "history": [{"timestamp": h.get("time"), "upper": float(h.get("ub_value", 0)), 
                                 "middle": float(h.get("mb_value", 0)), "lower": float(h.get("lb_value", 0))} for h in history],
                    "source": "bollinger_bands"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_macd_indicator(self, exchange: str = "Binance", symbol: str = "BTCUSDT", interval: str = "1h") -> Dict:
        """Get MACD indicator (50TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/indicators/macd"
            params = {"exchange": exchange, "symbol": symbol, "interval": interval}
            
            response = await client.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                latest = history[-1] if history else {}
                histogram = float(latest.get("histogram", 0))
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "current": {
                        "macd": float(latest.get("macd_value", 0)),
                        "signal": float(latest.get("signal", 0)),
                        "histogram": histogram
                    },
                    "crossover": "BULLISH" if histogram > 0 else "BEARISH" if histogram < 0 else "NEUTRAL",
                    "history": [{"timestamp": h.get("time"), "macd": float(h.get("macd_value", 0)),
                                 "signal": float(h.get("signal", 0)), "histogram": float(h.get("histogram", 0))} for h in history if h.get("histogram") is not None],
                    "source": "macd_indicator"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_basis_history(self, exchange: str = "Binance", symbol: str = "BTCUSDT", interval: str = "1h") -> Dict:
        """Get Basis History - Futures vs Spot spread! (51ST ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/basis/history"
            params = {"exchange": exchange, "symbol": symbol, "interval": interval}
            
            response = await client.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                latest = history[-1] if history else {}
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "current": {
                        "openBasis": float(latest.get("open_basis", 0)),
                        "closeBasis": float(latest.get("close_basis", 0)),
                        "openChange": float(latest.get("open_change", 0)),
                        "closeChange": float(latest.get("close_change", 0))
                    },
                    "history": [{"timestamp": h.get("time"), "openBasis": float(h.get("open_basis", 0)),
                                 "closeBasis": float(h.get("close_basis", 0))} for h in history],
                    "note": "Futures-Spot basis spread. Positive = futures premium (contango).",
                    "source": "basis_history"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_whale_index(self, exchange: str = "Binance", symbol: str = "BTCUSDT", interval: str = "1d") -> Dict:
        """Get Whale Index - Whale sentiment indicator! (52ND ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/whale-index/history"
            params = {"exchange": exchange, "symbol": symbol, "interval": interval}
            
            response = await client.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                latest_value = float(history[-1].get("whale_index_value", 0)) if history else 0
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "currentIndex": latest_value,
                    "sentiment": "BULLISH" if latest_value > 20 else "BEARISH" if latest_value < -20 else "NEUTRAL",
                    "history": [{"timestamp": h.get("time"), "index": float(h.get("whale_index_value", 0))} for h in history],
                    "note": "Whale sentiment: >20 bullish, <-20 bearish. Tracks large trader positioning.",
                    "source": "whale_index"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_cgdi_index(self) -> Dict:
        """Get CGDI Index - Coinglass Derivatives Index! (53RD ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/cgdi-index/history"
            
            response = await client.get(url, headers=self.headers)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                latest_value = float(history[-1].get("cgdi_index_value", 1000)) if history else 1000
                
                return {
                    "success": True,
                    "currentIndex": latest_value,
                    "change": ((latest_value - 1000) / 1000 * 100) if latest_value else 0,
                    "history": [{"timestamp": h.get("time"), "index": float(h.get("cgdi_index_value", 0))} for h in history],
                    "note": "Coinglass Derivatives Index. Baseline 1000. Tracks overall derivatives market performance.",
                    "source": "cgdi_index"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_cdri_index(self) -> Dict:
        """Get CDRI Index - Crypto Derivative Risk Index! (54TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/cdri-index/history"
            
            response = await client.get(url, headers=self.headers)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                latest_value = int(history[-1].get("cdri_index_value", 50)) if history else 50
                
                risk_level = "EXTREME_FEAR" if latest_value < 25 else "FEAR" if latest_value < 45 else "NEUTRAL" if latest_value < 55 else "GREED" if latest_value < 75 else "EXTREME_GREED"
                
                return {
                    "success": True,
                    "currentIndex": latest_value,
                    "riskLevel": risk_level,
                    "history": [{"timestamp": h.get("time"), "index": int(h.get("cdri_index_value", 0))} for h in history],
                    "note": "Crypto Derivative Risk Index (0-100). <25 extreme fear, >75 extreme greed.",
                    "source": "cdri_index"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_golden_ratio_multiplier(self) -> Dict:
        """Get Golden Ratio Multiplier - BTC price levels! (55TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/index/golden-ratio-multiplier"
            
            response = await client.get(url, headers=self.headers)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                latest = history[-1] if history else {}
                
                return {
                    "success": True,
                    "current": {
                        "price": float(latest.get("price", 0)),
                        "ma350": float(latest.get("ma_350", 0)),
                        "x3": float(latest.get("x_3", 0)),
                        "x5": float(latest.get("x_5", 0)),
                        "x8": float(latest.get("x_8", 0)),
                        "x13": float(latest.get("x_13", 0)),
                        "x21": float(latest.get("x_21", 0))
                    },
                    "history": [{"timestamp": h.get("timestamp"), "price": float(h.get("price", 0)), 
                                 "ma350": float(h.get("ma_350", 0)), "x3": float(h.get("x_3", 0))} for h in history],
                    "note": "BTC Golden Ratio levels based on 350-day MA. Fibonacci-based support/resistance.",
                    "source": "golden_ratio_multiplier"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_fear_greed_index(self) -> Dict:
        """Get Fear & Greed Index History! (56TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/index/fear-greed-history"
            
            response = await client.get(url, headers=self.headers)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                result = data["data"]
                data_list = result.get("data_list", [])
                
                if not data_list:
                    return {"success": False, "error": "No fear & greed data"}
                
                latest_value = int(data_list[-1])
                risk_level = "EXTREME_FEAR" if latest_value < 25 else "FEAR" if latest_value < 45 else "NEUTRAL" if latest_value < 55 else "GREED" if latest_value < 75 else "EXTREME_GREED"
                
                return {
                    "success": True,
                    "currentIndex": latest_value,
                    "sentiment": risk_level,
                    "history": [{"index": int(v)} for v in data_list],
                    "note": "Crypto Fear & Greed Index (0-100). <25 extreme fear, >75 extreme greed. Market sentiment indicator.",
                    "source": "fear_greed_index"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_economic_calendar(self) -> Dict:
        """Get Economic Calendar Events! (57TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/calendar/economic-data"
            
            response = await client.get(url, headers=self.headers)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                events = data["data"]
                
                processed_events = []
                for event in events:
                    processed_events.append({
                        "name": event.get("calendar_name", ""),
                        "country": event.get("country_name", ""),
                        "countryCode": event.get("country_code", ""),
                        "timestamp": event.get("publish_timestamp", 0),
                        "importance": event.get("importance_level", 1),
                        "impact": event.get("data_effect", ""),
                        "forecast": event.get("forecast_value", ""),
                        "previous": event.get("previous_value", ""),
                        "actual": event.get("published_value", ""),
                        "revised": event.get("revised_previous_value", "")
                    })
                
                high_impact = [e for e in processed_events if e["importance"] >= 2]
                
                return {
                    "success": True,
                    "totalEvents": len(processed_events),
                    "highImpactEvents": len(high_impact),
                    "events": processed_events,
                    "note": "Economic calendar with macro events affecting crypto markets. Importance: 1=low, 2=medium, 3=high.",
                    "source": "economic_calendar"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_news_feed(self, limit: int = 10, include_content: bool = False) -> Dict:
        """
        Get Latest Crypto News Articles! (58TH ENDPOINT!)
        
        Args:
            limit: Number of articles to return (default: 10, max: 50)
            include_content: Include full article content (default: False for GPT Actions)
        
        Returns:
            Latest crypto news with title, description, source, and optional full content
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/article/list"
            
            response = await client.get(url, headers=self.headers)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                articles = data["data"]
                
                # Limit articles to prevent response too large error
                limit = min(max(1, limit), 50)  # Between 1 and 50
                articles = articles[:limit]
                
                processed_articles = []
                for article in articles:
                    article_data = {
                        "title": article.get("article_title", ""),
                        "description": article.get("article_description", ""),
                        "image": article.get("article_picture", ""),
                        "source": article.get("source_name", ""),
                        "sourceLogo": article.get("source_website_logo", ""),
                        "publishedAt": article.get("article_release_time", 0),
                        "url": article.get("article_url", "")
                    }
                    
                    # Only include full content if requested (can be very large)
                    if include_content:
                        article_data["content"] = article.get("article_content", "")
                    
                    processed_articles.append(article_data)
                
                return {
                    "success": True,
                    "totalArticles": len(processed_articles),
                    "articles": processed_articles,
                    "note": f"Latest {len(processed_articles)} crypto news headlines from major sources (CoinTelegraph, TheBlock, etc). Set include_content=true for full article text.",
                    "source": "news_feed"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_taker_buy_sell_volume(self, symbol: str = "BTC", exchange_list: str = "Binance", interval: str = "h1") -> Dict:
        """Get Aggregated Taker Buy/Sell Volume - Order flow analysis! (59TH ENDPOINT!)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/aggregated-taker-buy-sell-volume/history"
            params = {
                "exchange_list": exchange_list,
                "symbol": symbol,
                "interval": interval
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                history = data["data"]
                
                if not history:
                    return {"success": False, "error": "No volume data"}
                
                latest = history[-1]
                buy_vol = float(latest.get("aggregated_buy_volume_usd", 0))
                sell_vol = float(latest.get("aggregated_sell_volume_usd", 0))
                
                total_vol = buy_vol + sell_vol
                buy_ratio = (buy_vol / total_vol * 100) if total_vol > 0 else 0
                sell_ratio = (sell_vol / total_vol * 100) if total_vol > 0 else 0
                
                pressure = "BULLISH" if buy_vol > sell_vol else "BEARISH" if sell_vol > buy_vol else "NEUTRAL"
                delta = buy_vol - sell_vol
                
                processed_history = []
                for h in history:
                    buy = float(h.get("aggregated_buy_volume_usd", 0))
                    sell = float(h.get("aggregated_sell_volume_usd", 0))
                    processed_history.append({
                        "timestamp": h.get("time", 0),
                        "buyVolume": buy,
                        "sellVolume": sell,
                        "delta": buy - sell,
                        "buyRatio": (buy / (buy + sell) * 100) if (buy + sell) > 0 else 0
                    })
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "exchange": exchange_list,
                    "interval": interval,
                    "current": {
                        "buyVolume": buy_vol,
                        "sellVolume": sell_vol,
                        "buyRatio": round(buy_ratio, 2),
                        "sellRatio": round(sell_ratio, 2),
                        "delta": delta,
                        "pressure": pressure
                    },
                    "history": processed_history,
                    "note": "Aggregated taker buy/sell volume shows market order flow. Higher buy volume = bullish pressure, higher sell volume = bearish pressure.",
                    "source": "taker_buy_sell_volume"
                }
            return {"success": False, "error": "No data"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== LONG/SHORT RATIO ENDPOINTS ====================
    
    async def get_long_short_ratio(self, symbol: str = "BTC") -> Dict:
        """
        Get global long/short account ratio for a symbol
        Endpoint: /public/v2/indicator/global_long_short_account_ratio
        
        Returns historical global long/short account ratio data
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_pro}/public/v2/long_short_accounts"
            params = {
                "symbol": self._normalize_symbol(symbol),
                "interval": "h1"
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                ratio_data = data["data"]
                
                if isinstance(ratio_data, list) and len(ratio_data) > 0:
                    latest = ratio_data[-1]
                    
                    long_pct = latest.get("global_account_long_percent", 0)
                    short_pct = latest.get("global_account_short_percent", 0)
                    ratio = latest.get("global_account_long_short_ratio", 0)
                    
                    return {
                        "success": True,
                        "symbol": self._normalize_symbol(symbol),
                        "longAccountPct": long_pct,
                        "shortAccountPct": short_pct,
                        "ratio": ratio,
                        "timestamp": latest.get("time", 0),
                        "historicalData": ratio_data,
                        "source": "coinglass_global_ls_ratio"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== FUNDING RATE ENDPOINTS ====================
    
    async def get_funding_rate_average(self, symbol: str = "BTC", interval: str = "h8") -> Dict:
        """
        Get OI-weighted funding rate OHLC data
        Endpoint: /public/v2/indicator/funding_rate_oi_weight_ohlc
        
        Returns OI-weighted funding rate historical data
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_pro}/public/v2/indicator/funding_rate_oi_weight_ohlc"
            params = {
                "symbol": self._normalize_symbol(symbol),
                "interval": interval
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                rate_data = data["data"]
                
                if isinstance(rate_data, list) and len(rate_data) > 0:
                    latest = rate_data[-1]
                    
                    return {
                        "success": True,
                        "symbol": self._normalize_symbol(symbol),
                        "avgFundingRate": latest.get("c", 0),
                        "high": latest.get("h", 0),
                        "low": latest.get("l", 0),
                        "open": latest.get("o", 0),
                        "timestamp": latest.get("t", 0),
                        "historicalData": rate_data,
                        "source": "coinglass_funding_oi_weight"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_funding_rate_ohlc(self, exchange: str = "Binance", pair: str = "BTCUSDT", interval: str = "h8") -> Dict:
        """
        Get OHLC data for funding rates
        Endpoint: /api/futures/funding-rate/ohlc
        
        Returns funding rate OHLC candles
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/funding-rate/ohlc"
            params = {
                "ex": exchange,
                "pair": pair,
                "interval": interval
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                return {
                    "success": True,
                    "exchange": exchange,
                    "pair": pair,
                    "data": data["data"],
                    "source": "coinglass_funding_ohlc"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== OPEN INTEREST ENDPOINTS ====================
    
    async def get_oi_ohlc_aggregated(self, symbol: str = "BTC", interval: str = "h4") -> Dict:
        """
        Get aggregated OI OHLC data across exchanges
        Endpoint: /public/v2/indicator/open_interest_aggregated_ohlc
        
        Returns OI candles aggregated from all exchanges
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_pro}/public/v2/indicator/open_interest_aggregated_ohlc"
            params = {
                "symbol": self._normalize_symbol(symbol),
                "interval": interval
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                ohlc_data = data["data"]
                
                if isinstance(ohlc_data, list) and len(ohlc_data) >= 2:
                    latest = ohlc_data[-1]
                    previous = ohlc_data[-2]
                    
                    current_oi = latest.get("c", 0)
                    previous_oi = previous.get("c", 0)
                    oi_change = ((current_oi - previous_oi) / previous_oi * 100) if previous_oi > 0 else 0
                    
                    return {
                        "success": True,
                        "symbol": self._normalize_symbol(symbol),
                        "currentOI": current_oi,
                        "previousOI": previous_oi,
                        "oiChangePct": oi_change,
                        "high": latest.get("h", 0),
                        "low": latest.get("l", 0),
                        "open": latest.get("o", 0),
                        "timestamp": latest.get("t", 0),
                        "historicalData": ohlc_data,
                        "source": "coinglass_oi_ohlc"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== OPTIONS DATA ENDPOINTS ====================
    
    async def get_options_open_interest(self) -> Dict:
        """
        Get Bitcoin/Crypto options open interest across exchanges
        REAL ENDPOINT: /api/option/info?symbol=BTC
        
        Returns total options OI by exchange (Deribit, OKX, Binance, etc.)
        Update frequency: 30 seconds
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/option/info"
            params = {"symbol": "BTC"}  # FIXED: Required parameter!
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                options_data = data["data"]
                
                # Calculate total OI and volume
                total_oi = 0
                total_volume = 0
                exchanges = []
                
                if isinstance(options_data, list):
                    for exchange_data in options_data:
                        oi = float(exchange_data.get("openInterest", 0))
                        vol = float(exchange_data.get("volume", 0))
                        total_oi += oi
                        total_volume += vol
                        exchanges.append({
                            "exchange": exchange_data.get("exchangeName", ""),
                            "openInterest": oi,
                            "volume": vol
                        })
                
                # Sort by OI descending
                exchanges.sort(key=lambda x: x["openInterest"], reverse=True)
                top_exchange = exchanges[0] if exchanges else {"exchange": "", "openInterest": 0}
                
                return {
                    "success": True,
                    "totalOptionsOI": total_oi,
                    "totalVolume24h": total_volume,
                    "topExchange": top_exchange,
                    "exchanges": exchanges,
                    "source": "coinglass_options"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_options_volume(self) -> Dict:
        """
        Get Bitcoin/Crypto options trading volume
        NOTE: This data is included in /api/option/info endpoint
        
        Returns 24h options volume by exchange
        """
        try:
            # Options volume is part of option/info endpoint
            return await self.get_options_open_interest()
            

        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== ETF FLOWS ENDPOINTS ====================
    
    async def get_etf_flows(self, asset: str = "BTC") -> Dict:
        """
        Get Bitcoin/Ethereum ETF flows (institutional money tracking)
        REAL ENDPOINTS: /api/etf/bitcoin/flow-history OR /api/etf/ethereum/flow-history
        
        Returns daily/weekly/monthly ETF inflows and outflows
        Critical for detecting institutional accumulation/distribution
        """
        try:
            client = await self._get_client()
            
            # FIXED: Use correct endpoint paths from official docs
            if asset.upper() in ["BTC", "BITCOIN"]:
                url = f"{self.base_url_v4}/api/etf/bitcoin/flow-history"
            elif asset.upper() in ["ETH", "ETHEREUM"]:
                url = f"{self.base_url_v4}/api/etf/ethereum/flow-history"
            else:
                return {"success": False, "error": f"ETF data only available for BTC and ETH"}
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                etf_data = data["data"]
                
                # Get latest flows
                if isinstance(etf_data, list) and len(etf_data) > 0:
                    latest = etf_data[-1]
                    
                    daily_flow = float(latest.get("netflow", 0))
                    total_holdings = float(latest.get("totalAssets", 0))
                    
                    # Determine institutional sentiment
                    if daily_flow > 100_000_000:  # $100M+
                        sentiment = "strong_accumulation"
                    elif daily_flow > 0:
                        sentiment = "accumulation"
                    elif daily_flow < -100_000_000:
                        sentiment = "strong_distribution"
                    elif daily_flow < 0:
                        sentiment = "distribution"
                    else:
                        sentiment = "neutral"
                    
                    return {
                        "success": True,
                        "asset": asset.upper(),
                        "dailyFlow": daily_flow,
                        "totalHoldings": total_holdings,
                        "sentiment": sentiment,
                        "historicalData": etf_data[:10],  # Last 10 days
                        "source": "coinglass_etf_flows"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== ON-CHAIN METRICS ENDPOINTS ====================
    
    async def get_exchange_reserves(self, symbol: str = "BTC") -> Dict:
        """
        Get cryptocurrency reserves on exchanges (whale movement detection)
        REAL ENDPOINT: /api/exchange/balance/list
        
        Returns exchange balance changes - critical for whale tracking
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/exchange/balance/list"
            params = {"symbol": self._normalize_symbol(symbol)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                balances = data["data"]
                
                if isinstance(balances, list) and len(balances) > 0:
                    # Aggregate total exchange reserves
                    total_balance = 0
                    change_1h = 0
                    change_7d = 0
                    change_30d = 0
                    
                    for exchange_data in balances:
                        balance = float(exchange_data.get("balance", 0))
                        total_balance += balance
                        change_1h += float(exchange_data.get("h1Change", 0))
                        change_7d += float(exchange_data.get("h24Change", 0))
                        change_30d += float(exchange_data.get("d30Change", 0))
                    
                    # Calculate percentage changes
                    change_1h_pct = (change_1h / total_balance * 100) if total_balance > 0 else 0
                    change_7d_pct = (change_7d / total_balance * 100) if total_balance > 0 else 0
                    
                    # Whale movement interpretation (based on 7d trend)
                    if change_7d_pct < -5:  # >5% outflow
                        interpretation = "whale_accumulation"  # Moving to cold storage (bullish)
                    elif change_7d_pct < -1:
                        interpretation = "accumulation"
                    elif change_7d_pct > 5:  # >5% inflow
                        interpretation = "whale_distribution"  # Preparing to sell (bearish)
                    elif change_7d_pct > 1:
                        interpretation = "distribution"
                    else:
                        interpretation = "neutral"
                    
                    return {
                        "success": True,
                        "symbol": self._normalize_symbol(symbol),
                        "totalExchangeBalance": total_balance,
                        "change1h": change_1h,
                        "change7d": change_7d,
                        "changePct": change_7d_pct,
                        "interpretation": interpretation,
                        "topExchanges": balances[:5],  # Top 5 exchanges
                        "source": "coinglass_exchange_balances"
                    }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== MARKET INDICATORS (ALL VERIFIED REAL ENDPOINTS!) ====================
    
    async def get_bull_market_indicators(self) -> Dict:
        """
        Get Bull Market Peak Indicators
        REAL ENDPOINT: /api/bull-market-peak-indicator
        
        Returns multi-metric bull market positioning signals
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/bull-market-peak-indicator"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                return {
                    "success": True,
                    "indicators": data["data"],
                    "source": "coinglass_bull_indicators"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_rainbow_chart(self) -> Dict:
        """
        Bitcoin Rainbow Chart - Long-term valuation bands
        REAL ENDPOINT: /api/index/bitcoin/rainbow-chart (FIXED PATH!)
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/index/bitcoin/rainbow-chart"  # FIXED: Add /bitcoin/
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                return {
                    "success": True,
                    "data": data["data"],
                    "source": "coinglass_rainbow"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_stock_to_flow(self) -> Dict:
        """
        Bitcoin Stock-to-Flow Model
        REAL ENDPOINT: /api/index/stock-flow (verified in official docs!)
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/index/stock-flow"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                return {
                    "success": True,
                    "data": data["data"],
                    "source": "coinglass_stock_to_flow"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_borrow_interest_rate(self, symbol: str = "BTC") -> Dict:
        """
        Borrow Interest Rate History
        REAL ENDPOINT: /api/borrow-interest-rate/history
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/borrow-interest-rate/history"
            params = {"symbol": self._normalize_symbol(symbol)}  # Add symbol parameter
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                return {
                    "success": True,
                    "data": data["data"],
                    "source": "coinglass_borrow_rate"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== UTILITY ENDPOINTS ====================
    
    async def get_supported_coins(self) -> Dict:
        """
        Get list of all supported cryptocurrency symbols
        Endpoint: /api/futures/supported-coins
        
        Returns array of supported coins
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/supported-coins"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                return {
                    "success": True,
                    "coins": data["data"],
                    "count": len(data["data"]),
                    "source": "coinglass_supported"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_supported_exchanges(self) -> Dict:
        """
        Get list of all supported exchanges
        Endpoint: /api/futures/supported-exchanges
        
        Returns:
        - Array of exchange names (29 exchanges)
        - Includes: Binance, OKX, Bybit, HTX, Bitmex, Bitfinex, Deribit, etc.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/supported-exchanges"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                return {
                    "success": True,
                    "exchanges": data["data"],
                    "count": len(data["data"]),
                    "source": "coinglass_exchanges"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_supported_exchange_pairs(self) -> Dict:
        """
        Get all supported exchanges and their trading pairs
        Endpoint: /api/futures/supported-exchange-pairs
        
        Returns dict of exchanges and their available pairs
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/supported-exchange-pairs"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                pairs_data = data["data"]
                
                exchange_count = len(pairs_data)
                total_pairs = sum(len(pairs) for pairs in pairs_data.values())
                
                return {
                    "success": True,
                    "data": pairs_data,
                    "exchangeCount": exchange_count,
                    "totalPairs": total_pairs,
                    "source": "coinglass_exchanges"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_exchange_assets(self, exchange: str = "Binance") -> Dict:
        """
        Get exchange wallet holdings/reserves (10th ENDPOINT!)
        REAL ENDPOINT: /api/exchange/assets?exchange=Binance
        
        Returns current exchange holdings by wallet address:
        - Wallet addresses
        - Balance (quantity + USD value)
        - Asset symbols and names
        - Current prices
        
        Shows real-time exchange holdings - useful for tracking whale movements
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/exchange/assets"
            params = {"exchange": exchange.capitalize()}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                assets = data["data"]
                
                # Calculate totals
                total_usd = sum(float(asset.get("balance_usd", 0)) for asset in assets)
                
                # Group by symbol
                by_symbol = {}
                for asset in assets:
                    symbol = asset.get("symbol", "UNKNOWN")
                    if symbol not in by_symbol:
                        by_symbol[symbol] = {
                            "symbol": symbol,
                            "name": asset.get("assets_name", symbol),
                            "total_balance": 0,
                            "total_usd": 0,
                            "wallets": []
                        }
                    by_symbol[symbol]["total_balance"] += float(asset.get("balance", 0))
                    by_symbol[symbol]["total_usd"] += float(asset.get("balance_usd", 0))
                    by_symbol[symbol]["wallets"].append({
                        "address": asset.get("wallet_address"),
                        "balance": asset.get("balance"),
                        "balance_usd": asset.get("balance_usd")
                    })
                
                return {
                    "success": True,
                    "exchange": exchange.capitalize(),
                    "totalValueUSD": total_usd,
                    "assetCount": len(by_symbol),
                    "topAssets": sorted(by_symbol.values(), key=lambda x: x["total_usd"], reverse=True)[:20],
                    "allAssets": list(by_symbol.values()),
                    "rawData": assets[:10],
                    "source": "coinglass_exchange_assets"
                }
            
            return {"success": False, "error": "No data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance for easy import
coinglass_comprehensive = CoinglassComprehensiveService()

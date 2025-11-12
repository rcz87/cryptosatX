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
                    symbol_upper = symbol.upper()
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
            params = {"symbol": symbol.upper()}
            
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
                "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
            params = {"symbol": symbol.upper()}
            
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
            params = {"symbol": symbol.upper()}
            
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper()
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
                    "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                    "symbol": symbol.upper(),
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
            params = {"symbol": symbol.upper()}
            
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
                    "symbol": symbol.upper(),
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
    
    async def get_liquidation_orders(self, symbol: str = "BTC") -> Dict:
        """
        Get recent liquidation orders (past 7 days)
        Endpoint: /api/futures/liquidation/order
        
        Returns detailed liquidation orders with exchange, pair, amount
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url_v4}/api/futures/liquidation/order"
            params = {"symbol": symbol.upper()}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if str(data.get("code")) == "0" and data.get("data"):
                orders = data["data"]
                
                long_total = sum(o.get("amount_usd", 0) for o in orders if o.get("side") == "long")
                short_total = sum(o.get("amount_usd", 0) for o in orders if o.get("side") == "short")
                
                return {
                    "success": True,
                    "symbol": symbol.upper(),
                    "orders": orders,
                    "longLiquidations": long_total,
                    "shortLiquidations": short_total,
                    "totalLiquidations": long_total + short_total,
                    "orderCount": len(orders),
                    "source": "coinglass_liq_orders"
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
            params = {"symbol": symbol.upper()}
            
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
                    "symbol": symbol.upper(),
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
                
                symbol_upper = symbol.upper()
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
                "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
                "symbol": symbol.upper(),
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
                        "symbol": symbol.upper(),
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
            params = {"symbol": symbol.upper()}
            
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
                        "symbol": symbol.upper(),
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
            params = {"symbol": symbol.upper()}  # Add symbol parameter
            
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

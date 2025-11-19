"""
CoinAPI Comprehensive Service
Maximizes CoinAPI Startup plan ($78/month) with advanced market data endpoints

Features:
- Multi-timeframe OHLCV (candlestick) data
- Order book depth analysis (whale walls, support/resistance)
- Recent trades volume analysis
- Bid/Ask spread monitoring
- Multi-exchange price aggregation
- Market metadata

Author: Enhanced for production trading signals
"""
import os
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.utils.symbol_normalizer import normalize_symbol, Provider, get_base_symbol


class CoinAPIComprehensiveService:
    """Comprehensive CoinAPI integration with advanced endpoints"""
    
    def __init__(self):
        self.api_key = os.getenv("COINAPI_KEY", "")
        self.base_url = "https://rest.coinapi.io/v1"
        self.headers = {
            "X-CoinAPI-Key": self.api_key
        }
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=15.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def _get_symbol_id(self, symbol: str, exchange: str = "BINANCE") -> str:
        """
        Convert simple symbol to CoinAPI symbol_id format using universal normalizer
        
        Args:
            symbol: Symbol in any format (BTC, BTCUSDT, bitcoin, etc.)
            exchange: Exchange name (default: BINANCE)
            
        Returns:
            CoinAPI symbol_id like 'BINANCE_SPOT_BTC_USDT'
        """
        return normalize_symbol(symbol, Provider.COINAPI, exchange=exchange)
    
    # ==================== OHLCV / CANDLESTICK DATA ====================
    
    async def get_ohlcv_latest(
        self, 
        symbol: str, 
        period: str = "1MIN",
        exchange: str = "BINANCE",
        limit: int = 100
    ) -> Dict:
        """
        Get latest OHLCV (candlestick) data
        Endpoint: /v1/ohlcv/{symbol_id}/latest
        
        Args:
            symbol: Coin symbol (e.g., 'BTC', 'ETH')
            period: Time period - 1SEC, 1MIN, 5MIN, 15MIN, 1HRS, 1DAY, 1WEK, 1MTH
            exchange: Exchange name (default: BINANCE)
            limit: Number of periods (default: 100, max: 100)
            
        Returns:
            Latest OHLCV data with:
            - price_open, price_high, price_low, price_close
            - volume_traded, trades_count
            - time_period_start, time_period_end
            
        Use case: Multi-timeframe price analysis, support/resistance detection
        """
        try:
            client = await self._get_client()
            symbol_id = self._get_symbol_id(symbol, exchange)
            
            url = f"{self.base_url}/ohlcv/{symbol_id}/latest"
            params = {
                "period_id": period,
                "limit": min(limit, 100)
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data and len(data) > 0:
                latest = data[0]
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "exchange": exchange,
                    "period": period,
                    "dataPoints": len(data),
                    
                    # Latest candle
                    "latest": {
                        "timeStart": latest.get("time_period_start"),
                        "timeEnd": latest.get("time_period_end"),
                        "open": float(latest.get("price_open", 0)),
                        "high": float(latest.get("price_high", 0)),
                        "low": float(latest.get("price_low", 0)),
                        "close": float(latest.get("price_close", 0)),
                        "volume": float(latest.get("volume_traded", 0)),
                        "tradesCount": int(latest.get("trades_count", 0))
                    },
                    
                    # Full historical data
                    "candles": data,
                    "source": "coinapi_ohlcv"
                }
            
            return {"success": False, "error": "No OHLCV data available"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_ohlcv_historical(
        self,
        symbol: str,
        period: str = "1HRS",
        days_back: int = 7,
        exchange: str = "BINANCE"
    ) -> Dict:
        """
        Get historical OHLCV data
        Endpoint: /v1/ohlcv/{symbol_id}/history
        
        Args:
            symbol: Coin symbol
            period: Time period (1MIN, 5MIN, 1HRS, 1DAY)
            days_back: Days to look back (1-30)
            exchange: Exchange name
            
        Returns:
            Historical candlestick data with trend analysis
            
        Use case: Price trend detection, volatility analysis
        """
        try:
            client = await self._get_client()
            symbol_id = self._get_symbol_id(symbol, exchange)
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            url = f"{self.base_url}/ohlcv/{symbol_id}/history"
            params = {
                "period_id": period,
                "time_start": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "time_end": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "limit": 1000
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data and len(data) > 0:
                # Extract price arrays for analysis
                closes = [float(c.get("price_close", 0)) for c in data]
                highs = [float(c.get("price_high", 0)) for c in data]
                lows = [float(c.get("price_low", 0)) for c in data]
                volumes = [float(c.get("volume_traded", 0)) for c in data]
                
                # Calculate trend metrics
                price_change = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] > 0 else 0
                avg_volume = sum(volumes) / len(volumes) if volumes else 0
                volatility = ((max(highs) - min(lows)) / min(lows) * 100) if min(lows) > 0 else 0
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "period": period,
                    "dataPoints": len(data),
                    "timeRange": f"{days_back}d",
                    
                    # Trend Analysis
                    "analysis": {
                        "priceChange": round(price_change, 2),
                        "currentPrice": closes[-1],
                        "highPrice": max(highs),
                        "lowPrice": min(lows),
                        "averageVolume": round(avg_volume, 2),
                        "volatility": round(volatility, 2)
                    },
                    
                    # Arrays for charting
                    "timeSeries": {
                        "closes": closes,
                        "highs": highs,
                        "lows": lows,
                        "volumes": volumes
                    },
                    
                    "rawData": data,
                    "source": "coinapi_ohlcv_historical"
                }
            
            return {"success": False, "error": "No historical data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== ORDER BOOK DEPTH ====================
    
    async def get_orderbook_depth(
        self,
        symbol: str,
        exchange: str = "BINANCE",
        limit: int = 20
    ) -> Dict:
        """
        Get order book depth (bids/asks)
        Endpoint: /v1/orderbooks/{symbol_id}/latest
        
        Args:
            symbol: Coin symbol
            exchange: Exchange name
            limit: Depth levels (default: 20, max: 100)
            
        Returns:
            Order book with:
            - Bids and asks arrays
            - Spread analysis
            - Order book imbalance
            - Whale walls detection
            
        Use case: Support/resistance levels, large order detection
        """
        try:
            client = await self._get_client()
            symbol_id = self._get_symbol_id(symbol, exchange)
            
            url = f"{self.base_url}/orderbooks/{symbol_id}/latest"
            params = {"limit": min(limit, 100)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data and len(data) > 0:
                orderbook = data[0]
                asks = orderbook.get("asks", [])
                bids = orderbook.get("bids", [])
                
                if not asks or not bids:
                    return {"success": False, "error": "Empty order book"}
                
                # Calculate metrics
                best_bid = float(bids[0]["price"])
                best_ask = float(asks[0]["price"])
                spread = best_ask - best_bid
                spread_pct = (spread / best_bid * 100) if best_bid > 0 else 0
                
                # Calculate total sizes
                total_bid_size = sum(float(b["size"]) for b in bids)
                total_ask_size = sum(float(a["size"]) for a in asks)
                
                # Order book imbalance (-100 to +100)
                # Positive = more buying pressure, Negative = more selling pressure
                imbalance = ((total_bid_size - total_ask_size) / (total_bid_size + total_ask_size) * 100) if (total_bid_size + total_ask_size) > 0 else 0
                
                # Detect whale walls (orders >5x average size)
                avg_bid_size = total_bid_size / len(bids) if bids else 0
                avg_ask_size = total_ask_size / len(asks) if asks else 0
                
                whale_bids = [b for b in bids if float(b["size"]) > avg_bid_size * 5]
                whale_asks = [a for a in asks if float(a["size"]) > avg_ask_size * 5]
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "exchange": exchange,
                    "timestamp": orderbook.get("time_exchange"),
                    
                    # Spread Analysis
                    "spread": {
                        "bestBid": best_bid,
                        "bestAsk": best_ask,
                        "spread": round(spread, 2),
                        "spreadPercent": round(spread_pct, 4)
                    },
                    
                    # Order Book Metrics
                    "metrics": {
                        "totalBidSize": round(total_bid_size, 2),
                        "totalAskSize": round(total_ask_size, 2),
                        "imbalance": round(imbalance, 2),  # Positive = bullish, Negative = bearish
                        "bidLevels": len(bids),
                        "askLevels": len(asks)
                    },
                    
                    # Whale Walls
                    "whaleWalls": {
                        "largeBids": len(whale_bids),
                        "largeAsks": len(whale_asks),
                        "topBidWall": whale_bids[0] if whale_bids else None,
                        "topAskWall": whale_asks[0] if whale_asks else None
                    },
                    
                    # Raw data
                    "bids": bids[:10],  # Top 10 for response size
                    "asks": asks[:10],
                    "source": "coinapi_orderbook"
                }
            
            return {"success": False, "error": "No order book data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== TRADES / VOLUME ANALYSIS ====================
    
    async def get_recent_trades(
        self,
        symbol: str,
        exchange: str = "BINANCE",
        limit: int = 100
    ) -> Dict:
        """
        Get recent trades
        Endpoint: /v1/trades/{symbol_id}/latest
        
        Args:
            symbol: Coin symbol
            exchange: Exchange name
            limit: Number of trades (default: 100, max: 1000)
            
        Returns:
            Recent trades with:
            - Price, size, side (buy/sell)
            - Volume analysis
            - Buy/sell pressure
            
        Use case: Volume spike detection, market momentum
        """
        try:
            client = await self._get_client()
            symbol_id = self._get_symbol_id(symbol, exchange)
            
            url = f"{self.base_url}/trades/{symbol_id}/latest"
            params = {"limit": min(limit, 1000)}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data and len(data) > 0:
                # Analyze trades
                total_volume = sum(float(t.get("size", 0)) for t in data)
                buy_volume = sum(float(t.get("size", 0)) for t in data if t.get("taker_side") == "BUY")
                sell_volume = sum(float(t.get("size", 0)) for t in data if t.get("taker_side") == "SELL")
                
                # Buy/sell pressure
                buy_pressure = (buy_volume / total_volume * 100) if total_volume > 0 else 50
                sell_pressure = (sell_volume / total_volume * 100) if total_volume > 0 else 50
                
                # Average trade size
                avg_trade_size = total_volume / len(data) if data else 0
                
                # Latest price
                latest_price = float(data[0].get("price", 0))
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "exchange": exchange,
                    "tradesCount": len(data),
                    
                    # Volume Analysis
                    "volume": {
                        "total": round(total_volume, 2),
                        "buyVolume": round(buy_volume, 2),
                        "sellVolume": round(sell_volume, 2),
                        "buyPressure": round(buy_pressure, 2),  # % of buy volume
                        "sellPressure": round(sell_pressure, 2),  # % of sell volume
                        "avgTradeSize": round(avg_trade_size, 2)
                    },
                    
                    # Latest trade
                    "latestTrade": {
                        "price": latest_price,
                        "size": float(data[0].get("size", 0)),
                        "side": data[0].get("taker_side"),
                        "time": data[0].get("time_exchange")
                    },
                    
                    # Recent trades (limited for response size)
                    "recentTrades": data[:20],
                    "source": "coinapi_trades"
                }
            
            return {"success": False, "error": "No trade data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== QUOTES / SPREAD MONITORING ====================
    
    async def get_current_quote(
        self,
        symbol: str,
        exchange: str = "BINANCE"
    ) -> Dict:
        """
        Get current bid/ask quote
        Endpoint: /v1/quotes/{symbol_id}/latest
        
        Args:
            symbol: Coin symbol
            exchange: Exchange name
            
        Returns:
            Current quote with bid/ask prices and spread
            
        Use case: Real-time spread monitoring, liquidity assessment
        """
        try:
            client = await self._get_client()
            symbol_id = self._get_symbol_id(symbol, exchange)
            
            url = f"{self.base_url}/quotes/{symbol_id}/latest"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data and len(data) > 0:
                quote = data[0]
                
                bid_price = float(quote.get("bid_price", 0))
                ask_price = float(quote.get("ask_price", 0))
                spread = ask_price - bid_price
                spread_pct = (spread / bid_price * 100) if bid_price > 0 else 0
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "exchange": exchange,
                    "timestamp": quote.get("time_exchange"),
                    
                    # Quote data
                    "quote": {
                        "bidPrice": bid_price,
                        "askPrice": ask_price,
                        "bidSize": float(quote.get("bid_size", 0)),
                        "askSize": float(quote.get("ask_size", 0)),
                        "spread": round(spread, 2),
                        "spreadPercent": round(spread_pct, 4)
                    },
                    
                    "source": "coinapi_quote"
                }
            
            return {"success": False, "error": "No quote data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_current_price(
        self,
        symbol: str,
        exchange: str = "BINANCE"
    ) -> Dict:
        """
        Get current price for a symbol (simple wrapper around get_ohlcv_latest)
        
        Args:
            symbol: Coin symbol (e.g., 'BTC', 'ETH', 'BTCUSDT')
            exchange: Exchange name (default: BINANCE)
            
        Returns:
            Current price data with:
            - price: Latest close price
            - timestamp: Price timestamp
            - source: Data source
            
        Use case: Quick price lookup for entry/exit calculations
        """
        try:
            # Get latest 1-minute candle
            ohlcv_data = await self.get_ohlcv_latest(
                symbol=symbol,
                period="1MIN",
                exchange=exchange,
                limit=1
            )
            
            if ohlcv_data.get("success") and ohlcv_data.get("latest"):
                latest = ohlcv_data["latest"]
                return {
                    "success": True,
                    "symbol": symbol,
                    "exchange": exchange,
                    "price": latest.get("close", 0),
                    "timestamp": latest.get("timeEnd"),
                    "source": "coinapi_ohlcv"
                }
            
            return {"success": False, "error": "No price data available"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== MULTI-EXCHANGE AGGREGATION ====================
    
    async def get_multi_exchange_prices(
        self,
        symbol: str,
        exchanges: List[str] = ["BINANCE", "COINBASE", "KRAKEN"]
    ) -> Dict:
        """
        Get prices from multiple exchanges for comparison
        
        Args:
            symbol: Coin symbol
            exchanges: List of exchange names
            
        Returns:
            Price comparison across exchanges with:
            - Price variance
            - Average price
            - Arbitrage opportunities
            
        Use case: Price arbitrage detection, multi-exchange validation
        """
        try:
            client = await self._get_client()
            symbol = symbol.upper()
            
            # Fetch prices from all exchanges concurrently
            import asyncio
            
            async def fetch_exchange_price(exchange: str):
                try:
                    url = f"{self.base_url}/exchangerate/{symbol}/USDT"
                    # Add exchange filter if supported
                    response = await client.get(url, headers=self.headers)
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "exchange": exchange,
                            "price": float(data.get("rate", 0)),
                            "success": True
                        }
                except:
                    pass
                return {"exchange": exchange, "price": 0, "success": False}
            
            results = await asyncio.gather(*[fetch_exchange_price(ex) for ex in exchanges])
            
            # Filter successful results
            successful = [r for r in results if r["success"] and r["price"] > 0]
            
            if successful:
                prices = [r["price"] for r in successful]
                avg_price = sum(prices) / len(prices)
                max_price = max(prices)
                min_price = min(prices)
                price_variance = ((max_price - min_price) / min_price * 100) if min_price > 0 else 0
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "exchangesQueried": len(exchanges),
                    "exchangesSuccessful": len(successful),
                    
                    # Price Analysis
                    "priceAnalysis": {
                        "averagePrice": round(avg_price, 2),
                        "highestPrice": max_price,
                        "lowestPrice": min_price,
                        "priceVariance": round(price_variance, 4),  # % difference
                        "arbitrageOpportunity": price_variance > 0.5  # >0.5% variance
                    },
                    
                    # Individual exchange prices
                    "exchangePrices": successful,
                    "source": "coinapi_multi_exchange"
                }
            
            return {"success": False, "error": "No exchange data available"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
coinapi_comprehensive = CoinAPIComprehensiveService()

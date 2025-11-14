"""
Binance Futures Public API Service
Fetch coin list, market data, funding rates from Binance USD-M Futures
NO API KEY REQUIRED - All public endpoints
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from app.utils.symbol_normalizer import normalize_symbol, Provider


class BinanceFuturesService:
    """
    Binance USD-M Futures public API integration
    Provides comprehensive market data without authentication
    """
    
    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self._client: Optional[httpx.AsyncClient] = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=15.0,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    # ==================== EXCHANGE INFO & SYMBOLS ====================
    
    async def get_exchange_info(self) -> Dict:
        """
        Get all trading pairs and their info
        Endpoint: /fapi/v1/exchangeInfo
        
        Returns:
            All symbols with contract type, status, filters, etc.
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/fapi/v1/exchangeInfo")
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            return {
                "success": True,
                "symbols": data.get("symbols", []),
                "totalSymbols": len(data.get("symbols", [])),
                "timezone": data.get("timezone", "UTC"),
                "serverTime": data.get("serverTime", 0)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_all_perpetual_symbols(self) -> List[str]:
        """
        Get list of all PERPETUAL futures symbols (most popular)
        
        Returns:
            List of symbols like ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', ...]
        """
        try:
            info = await self.get_exchange_info()
            
            if not info.get("success"):
                return []
            
            # Filter only PERPETUAL contracts that are TRADING
            perpetual_symbols = [
                symbol["symbol"]
                for symbol in info.get("symbols", [])
                if symbol.get("contractType") == "PERPETUAL"
                and symbol.get("status") == "TRADING"
            ]
            
            return perpetual_symbols
            
        except Exception as e:
            print(f"Error getting perpetual symbols: {e}")
            return []
    
    # ==================== MARKET DATA ====================
    
    async def get_24hr_ticker(self, symbol: Optional[str] = None) -> Dict:
        """
        Get 24hr price change statistics
        Endpoint: /fapi/v1/ticker/24hr
        
        Args:
            symbol: Specific symbol (e.g., 'BTCUSDT') or None for all symbols
            
        Returns:
            24hr stats: price, volume, price changes, high/low, etc.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/fapi/v1/ticker/24hr"
            
            params = {}
            if symbol:
                params["symbol"] = symbol.upper()
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            # If single symbol, wrap in list
            if symbol:
                data = [data]
            
            return {
                "success": True,
                "data": data,
                "count": len(data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_ticker_price(self, symbol: Optional[str] = None) -> Dict:
        """
        Get latest price for symbol(s)
        Endpoint: /fapi/v1/ticker/price
        
        Returns:
            Current price for symbol(s)
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/fapi/v1/ticker/price"
            
            params = {}
            if symbol:
                params["symbol"] = symbol.upper()
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            return {
                "success": True,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== FUNDING RATE & OPEN INTEREST ====================
    
    async def get_funding_rate(self, symbol: Optional[str] = None) -> Dict:
        """
        Get current funding rate and mark price
        Endpoint: /fapi/v1/premiumIndex
        
        Returns:
            Funding rate, mark price, next funding time
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/fapi/v1/premiumIndex"
            
            params = {}
            if symbol:
                params["symbol"] = symbol.upper()
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            # If single symbol, wrap in list
            if symbol:
                data = [data]
            
            return {
                "success": True,
                "data": data,
                "count": len(data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_open_interest(self, symbol: str) -> Dict:
        """
        Get open interest for a symbol
        Endpoint: /fapi/v1/openInterest
        
        Returns:
            Open interest in contracts and USD value
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/fapi/v1/openInterest"
            
            params = {"symbol": symbol.upper()}
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "openInterest": float(data.get("openInterest", 0)),
                "time": data.get("time", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== KLINES / CANDLESTICK DATA ====================
    
    async def get_klines(
        self,
        symbol: str,
        interval: str = "15m",
        limit: int = 100
    ) -> Dict:
        """
        Get candlestick/kline data
        Endpoint: /fapi/v1/klines
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles (max 1500)
            
        Returns:
            OHLCV candlestick data
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/fapi/v1/klines"
            
            params = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": min(limit, 1500)
            }
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            # Parse klines
            # Format: [open_time, open, high, low, close, volume, close_time, ...]
            candles = []
            for kline in data:
                candles.append({
                    "timestamp": int(kline[0]),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "closeTime": int(kline[6])
                })
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "interval": interval,
                "candles": candles,
                "count": len(candles),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== HELPER METHODS ====================
    
    async def get_coin_comprehensive_data(self, symbol: str) -> Dict:
        """
        Get comprehensive data for a single coin
        Combines: 24hr stats, funding rate, open interest, klines
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            
        Returns:
            Complete market data for the coin
        """
        try:
            # Fetch all data concurrently
            ticker, funding, oi, klines = await asyncio.gather(
                self.get_24hr_ticker(symbol),
                self.get_funding_rate(symbol),
                self.get_open_interest(symbol),
                self.get_klines(symbol, "15m", 100)
            )
            
            # Extract data safely
            ticker_data = ticker.get("data", [{}])[0] if ticker.get("success") else {}
            funding_data = funding.get("data", [{}])[0] if funding.get("success") else {}
            oi_data = oi if oi.get("success") else {}
            klines_data = klines if klines.get("success") else {}
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "price": float(ticker_data.get("lastPrice", 0)),
                "priceChange24h": float(ticker_data.get("priceChange", 0)),
                "priceChangePercent24h": float(ticker_data.get("priceChangePercent", 0)),
                "volume24h": float(ticker_data.get("volume", 0)),
                "quoteVolume24h": float(ticker_data.get("quoteVolume", 0)),
                "high24h": float(ticker_data.get("highPrice", 0)),
                "low24h": float(ticker_data.get("lowPrice", 0)),
                "fundingRate": float(funding_data.get("lastFundingRate", 0)),
                "markPrice": float(funding_data.get("markPrice", 0)),
                "nextFundingTime": funding_data.get("nextFundingTime", 0),
                "openInterest": oi_data.get("openInterest", 0),
                "candles": klines_data.get("candles", []),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "binance_futures"
            }
            
        except Exception as e:
            return {
                "success": False,
                "symbol": symbol,
                "error": str(e)
            }
    
    async def filter_coins_by_criteria(
        self,
        min_volume_usdt: float = 1000000,  # Min $1M volume
        min_price_change_percent: Optional[float] = None,
        max_market_cap_rank: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Filter and rank coins by trading criteria
        
        Args:
            min_volume_usdt: Minimum 24h volume in USDT
            min_price_change_percent: Minimum price change % (can be negative)
            max_market_cap_rank: Maximum market cap rank (lower = bigger)
            limit: Max number of results
            
        Returns:
            List of coins matching criteria, sorted by volume
        """
        try:
            # Get all 24hr tickers
            tickers = await self.get_24hr_ticker()
            
            if not tickers.get("success"):
                return []
            
            coins = tickers.get("data", [])
            filtered = []
            
            for coin in coins:
                symbol = coin.get("symbol", "")
                volume = float(coin.get("quoteVolume", 0))
                price_change = float(coin.get("priceChangePercent", 0))
                
                # Apply filters
                if volume < min_volume_usdt:
                    continue
                
                if min_price_change_percent is not None:
                    if price_change < min_price_change_percent:
                        continue
                
                filtered.append({
                    "symbol": symbol,
                    "price": float(coin.get("lastPrice", 0)),
                    "volume24h": volume,
                    "priceChange24h": price_change,
                    "high24h": float(coin.get("highPrice", 0)),
                    "low24h": float(coin.get("lowPrice", 0))
                })
            
            # Sort by volume (descending)
            filtered.sort(key=lambda x: x["volume24h"], reverse=True)
            
            return filtered[:limit]
            
        except Exception as e:
            print(f"Error filtering coins: {e}")
            return []


# Global instance for easy import
binance_futures_service = BinanceFuturesService()

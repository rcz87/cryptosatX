"""
CoinGecko API Service
Coin discovery with filtering by market cap, volume, category
FREE API - 30 calls/min, 10K calls/month (with demo key optional)
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from app.utils.logger import logger
from app.utils.retry_helper import retry_with_backoff, FAST_RETRY


class CoinGeckoService:
    """
    CoinGecko API v3 integration for coin discovery
    Supports 10,000+ coins with comprehensive market data
    """
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self._client: Optional[httpx.AsyncClient] = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
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
    
    # ==================== COIN DISCOVERY ====================
    
    @retry_with_backoff(
        config=FAST_RETRY,
        exceptions=(httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError)
    )
    async def get_coins_markets(
        self,
        vs_currency: str = "usd",
        order: str = "market_cap_desc",
        per_page: int = 100,
        page: int = 1,
        category: Optional[str] = None,
        price_change_percentage: Optional[str] = None
    ) -> Dict:
        """
        Get coin list with market data
        Endpoint: /coins/markets
        
        Args:
            vs_currency: Target currency (usd, eur, btc)
            order: Sort order (market_cap_desc, market_cap_asc, volume_desc, etc)
            per_page: Results per page (1-250)
            page: Page number
            category: Filter by category ID (e.g., 'meme-token', 'layer-1')
            price_change_percentage: Include price change % (1h, 24h, 7d, 14d, 30d, 1y)
            
        Returns:
            List of coins with market data
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/coins/markets"
            
            params = {
                "vs_currency": vs_currency,
                "order": order,
                "per_page": min(per_page, 250),
                "page": page,
                "sparkline": "false"
            }
            
            if category:
                params["category"] = category
            
            if price_change_percentage:
                params["price_change_percentage"] = price_change_percentage
            
            response = await client.get(url, params=params)
            
            # Raise exception for retry logic to work
            if response.status_code != 200:
                logger.warning(f"CoinGecko API error: HTTP {response.status_code}")
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}", 
                    request=response.request, 
                    response=response
                )
            
            data = response.json()
            
            return {
                "success": True,
                "data": data,
                "count": len(data),
                "page": page,
                "per_page": per_page,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError):
            # Re-raise for retry decorator to handle
            raise
        except Exception as e:
            # Unexpected errors - wrap in httpx.HTTPError for consistency
            logger.error(f"CoinGecko unexpected error: {e}")
            raise httpx.HTTPError(str(e))
    
    async def get_coin_by_id(self, coin_id: str) -> Dict:
        """
        Get detailed coin data by CoinGecko ID
        Endpoint: /coins/{id}
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            Detailed coin information
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/coins/{coin_id}"
            
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            }
            
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
    
    # ==================== CATEGORIES ====================
    
    async def get_categories_list(self) -> Dict:
        """
        Get all available categories
        Endpoint: /coins/categories/list
        
        Returns:
            List of all category IDs and names
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/coins/categories/list"
            
            response = await client.get(url)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            return {
                "success": True,
                "categories": data,
                "count": len(data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_categories_with_market_data(self) -> Dict:
        """
        Get categories with market data
        Endpoint: /coins/categories
        
        Returns:
            Categories with market cap, volume, etc.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/coins/categories"
            
            response = await client.get(url)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            return {
                "success": True,
                "data": data,
                "count": len(data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== TRENDING & SEARCH ====================
    
    async def get_trending(self) -> Dict:
        """
        Get trending coins
        Endpoint: /search/trending
        
        Returns:
            Top trending coins in the last 24 hours
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/search/trending"
            
            response = await client.get(url)
            
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
    
    async def search_coins(self, query: str) -> Dict:
        """
        Search for coins by name or symbol
        Endpoint: /search
        
        Args:
            query: Search term (name or symbol)
            
        Returns:
            Search results
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/search"
            
            params = {"query": query}
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            return {
                "success": True,
                "coins": data.get("coins", []),
                "count": len(data.get("coins", [])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== HELPER METHODS ====================
    
    async def discover_small_cap_coins(
        self,
        max_market_cap: float = 100000000,  # $100M
        min_volume: float = 100000,  # $100K
        min_price: float = 0.000001,
        limit: int = 50,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Discover small market cap coins with decent volume
        
        Args:
            max_market_cap: Maximum market cap in USD
            min_volume: Minimum 24h volume in USD
            min_price: Minimum price to filter out trash
            limit: Max number of results
            category: Optional category filter
            
        Returns:
            List of small cap coins sorted by volume
        """
        try:
            # Fetch coins sorted by market cap ascending (smallest first)
            result = await self.get_coins_markets(
                order="market_cap_asc",
                per_page=250,
                page=1,
                category=category,
                price_change_percentage="24h,7d"
            )
            
            if not result.get("success"):
                return []
            
            coins = result.get("data", [])
            filtered = []
            
            for coin in coins:
                market_cap = coin.get("market_cap") or 0
                volume = coin.get("total_volume") or 0
                price = coin.get("current_price") or 0
                
                # Apply filters
                if market_cap > max_market_cap:
                    continue
                
                if volume < min_volume:
                    continue
                
                if price < min_price:
                    continue
                
                filtered.append({
                    "id": coin.get("id"),
                    "symbol": coin.get("symbol", "").upper(),
                    "name": coin.get("name"),
                    "price": price,
                    "marketCap": market_cap,
                    "volume24h": volume,
                    "priceChange24h": coin.get("price_change_percentage_24h", 0),
                    "priceChange7d": coin.get("price_change_percentage_7d_in_currency", 0),
                    "marketCapRank": coin.get("market_cap_rank"),
                    "image": coin.get("image")
                })
            
            # Sort by volume (highest volume = more liquid)
            filtered.sort(key=lambda x: x["volume24h"], reverse=True)
            
            return filtered[:limit]
            
        except Exception as e:
            logger.error(f"Error discovering small cap coins: {e}")
            return []
    
    async def discover_new_listings(
        self,
        min_volume: float = 50000,
        limit: int = 30
    ) -> List[Dict]:
        """
        Discover recently listed coins
        (Coins without market cap rank = likely new)
        
        Args:
            min_volume: Minimum 24h volume
            limit: Max results
            
        Returns:
            List of potential new listings
        """
        try:
            # Get coins with market data
            result = await self.get_coins_markets(
                order="volume_desc",
                per_page=250,
                page=1,
                price_change_percentage="24h"
            )
            
            if not result.get("success"):
                return []
            
            coins = result.get("data", [])
            new_coins = []
            
            for coin in coins:
                volume = coin.get("total_volume") or 0
                market_cap_rank = coin.get("market_cap_rank")
                
                # Filter: no rank = potentially new, but has volume
                if market_cap_rank is not None:
                    continue
                
                if volume < min_volume:
                    continue
                
                new_coins.append({
                    "id": coin.get("id"),
                    "symbol": coin.get("symbol", "").upper(),
                    "name": coin.get("name"),
                    "price": coin.get("current_price", 0),
                    "marketCap": coin.get("market_cap", 0),
                    "volume24h": volume,
                    "priceChange24h": coin.get("price_change_percentage_24h", 0),
                    "image": coin.get("image")
                })
            
            # Sort by volume
            new_coins.sort(key=lambda x: x["volume24h"], reverse=True)
            
            return new_coins[:limit]
            
        except Exception as e:
            logger.error(f"Error discovering new listings: {e}")
            return []
    
    async def get_coins_by_category(
        self,
        category: str,
        limit: int = 50,
        min_volume: float = 0
    ) -> List[Dict]:
        """
        Get coins from specific category

        Args:
            category: Category ID (e.g., 'meme-token', 'layer-1', 'defi')
            limit: Max results
            min_volume: Minimum 24h volume filter

        Returns:
            List of coins in category
        """
        try:
            result = await self.get_coins_markets(
                order="market_cap_desc",
                per_page=min(limit, 250),
                page=1,
                category=category,
                price_change_percentage="24h,7d"
            )

            if not result.get("success"):
                return []

            coins = result.get("data", [])

            # Filter by volume if specified
            if min_volume > 0:
                coins = [c for c in coins if (c.get("total_volume") or 0) >= min_volume]

            # Format response
            formatted = []
            for coin in coins:
                formatted.append({
                    "id": coin.get("id"),
                    "symbol": coin.get("symbol", "").upper(),
                    "name": coin.get("name"),
                    "price": coin.get("current_price", 0),
                    "marketCap": coin.get("market_cap", 0),
                    "volume24h": coin.get("total_volume", 0),
                    "priceChange24h": coin.get("price_change_percentage_24h", 0),
                    "priceChange7d": coin.get("price_change_percentage_7d_in_currency", 0),
                    "marketCapRank": coin.get("market_cap_rank"),
                    "image": coin.get("image")
                })

            return formatted[:limit]

        except Exception as e:
            logger.error(f"Error getting coins by category: {e}")
            return []

    # ==================== ORDERBOOK ESTIMATION ====================

    def _normalize_symbol_for_coingecko(self, symbol: str) -> str:
        """
        Convert symbol to CoinGecko ID

        Args:
            symbol: Symbol like 'BTC', 'BTCUSDT', or 'bitcoin'

        Returns:
            CoinGecko ID like 'bitcoin'
        """
        # Symbol mapping
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "ATOM": "cosmos",
            "LTC": "litecoin",
            "BCH": "bitcoin-cash",
            "NEAR": "near",
            "APT": "aptos",
            "ARB": "arbitrum",
            "OP": "optimism",
            "INJ": "injective-protocol"
        }

        # Remove USDT/PERP suffix if present
        symbol = symbol.upper().replace("USDT", "").replace("PERP", "")

        # Check direct mapping
        if symbol in symbol_map:
            return symbol_map[symbol]

        # Return lowercase for direct use
        return symbol.lower()

    async def get_orderbook_estimate(self, symbol: str) -> Dict:
        """
        Estimate orderbook pressure from market data

        Since CoinGecko doesn't provide full orderbook depth, we estimate
        bid/ask pressure from price action and volume data

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with estimated orderbook pressure:
            {
                "success": True,
                "bids": [[price, volume], ...],  # Estimated
                "asks": [[price, volume], ...],  # Estimated
                "bidPressure": float,
                "askPressure": float
            }
        """
        try:
            coin_id = self._normalize_symbol_for_coingecko(symbol)

            # Get detailed coin data by ID
            client = await self._get_client()
            url = f"{self.base_url}/coins/{coin_id}"

            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false"
            }

            response = await client.get(url, params=params)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code} - Coin {symbol} not found"
                }

            data = response.json()
            market_data = data.get("market_data", {})

            if not market_data:
                return {
                    "success": False,
                    "error": "No market data available"
                }

            # Extract coin data from market_data
            coin_data = {
                "id": coin_id,
                "current_price": market_data.get("current_price", {}).get("usd", 0),
                "price_change_percentage_24h": market_data.get("price_change_percentage_24h", 0),
                "price_change_percentage_1h_in_currency": market_data.get("price_change_percentage_1h_in_currency", {}).get("usd", 0),
                "total_volume": market_data.get("total_volume", {}).get("usd", 0),
                "high_24h": market_data.get("high_24h", {}).get("usd", 0),
                "low_24h": market_data.get("low_24h", {}).get("usd", 0)
            }

            # Extract key metrics
            current_price = coin_data.get("current_price", 0)
            price_change_24h = coin_data.get("price_change_percentage_24h", 0)
            price_change_1h = coin_data.get("price_change_percentage_1h_in_currency", 0)
            volume_24h = coin_data.get("total_volume", 0)
            high_24h = coin_data.get("high_24h", 0)
            low_24h = coin_data.get("low_24h", 0)

            if current_price == 0:
                return {
                    "success": False,
                    "error": "No price data available"
                }

            # Estimate bid/ask pressure from price action
            # Strong uptrend = more buy pressure
            # Strong downtrend = more sell pressure

            if price_change_1h > 3:  # Strong 1h pump
                bid_pressure = 70.0
                ask_pressure = 30.0
            elif price_change_1h > 1:  # Moderate 1h increase
                bid_pressure = 60.0
                ask_pressure = 40.0
            elif price_change_1h < -3:  # Strong 1h dump
                bid_pressure = 30.0
                ask_pressure = 70.0
            elif price_change_1h < -1:  # Moderate 1h decrease
                bid_pressure = 40.0
                ask_pressure = 60.0
            elif price_change_24h > 10:  # Strong 24h uptrend
                bid_pressure = 65.0
                ask_pressure = 35.0
            elif price_change_24h < -10:  # Strong 24h downtrend
                bid_pressure = 35.0
                ask_pressure = 65.0
            else:  # Sideways/balanced
                bid_pressure = 50.0
                ask_pressure = 50.0

            # Estimate spread from volatility (high - low)
            if high_24h > 0 and low_24h > 0:
                volatility = ((high_24h - low_24h) / low_24h) * 100
                spread_pct = min(volatility / 10, 2.0)  # Cap at 2%
            else:
                spread_pct = 0.5  # Default 0.5% spread

            # Create estimated orderbook levels (5 levels)
            spread_amount = current_price * (spread_pct / 100)
            bid_price = current_price - (spread_amount / 2)
            ask_price = current_price + (spread_amount / 2)

            # Estimate volume distribution
            estimated_volume = volume_24h / 1000  # Rough estimate per level

            bids = []
            asks = []

            for i in range(5):
                bid_level_price = bid_price * (1 - (i * 0.001))  # 0.1% increments
                ask_level_price = ask_price * (1 + (i * 0.001))

                # Decreasing volume with depth
                bid_qty = estimated_volume * (bid_pressure / 100) * (0.4 - i * 0.05)
                ask_qty = estimated_volume * (ask_pressure / 100) * (0.4 - i * 0.05)

                bids.append([bid_level_price, max(bid_qty, 0)])
                asks.append([ask_level_price, max(ask_qty, 0)])

            return {
                "success": True,
                "symbol": symbol,
                "bids": bids,
                "asks": asks,
                "lastPrice": current_price,
                "bidPressure": bid_pressure,
                "askPressure": ask_pressure,
                "spread": spread_pct,
                "priceChange1h": price_change_1h,
                "priceChange24h": price_change_24h,
                "volume24h": volume_24h,
                "estimated": True,  # Flag that this is estimated
                "source": "coingecko",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error estimating orderbook for {symbol}: {e}")
            return {
                "success": False,
                "symbol": symbol,
                "error": str(e)
            }


# Global instance for easy import
coingecko_service = CoinGeckoService()

"""
CoinAPI Service - IMPROVED ERROR HANDLING
Provides real-time spot price data for cryptocurrencies
"""

import os

from app.utils.logger import get_logger

# Initialize module logger
logger = get_logger(__name__)
import httpx
from typing import Dict, Optional


class CoinAPIService:
    """Service for interacting with CoinAPI"""

    def __init__(self):
        self.api_key = os.getenv("COINAPI_KEY", "")
        self.base_url = "https://rest.coinapi.io/v1"
        self.headers = {"X-CoinAPI-Key": self.api_key}
        
        # Validate API key on init
        if not self.api_key:
            logger.warning("⚠️ WARNING: CoinAPI key not configured (COINAPI_KEY env variable)")

    async def get_spot_price(self, symbol: str) -> Dict:
        """
        Get spot price for a given cryptocurrency symbol

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with symbol, price, and source
        """
        try:
            # Normalize symbol to uppercase
            symbol = symbol.upper()

            # CoinAPI endpoint for exchange rate
            url = f"{self.base_url}/exchangerate/{symbol}/USDT"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()

                return {
                    "symbol": symbol,
                    "price": float(data.get("rate", 0)),
                    "source": "coinapi",
                    "success": True,
                }

        except httpx.HTTPStatusError as e:
            # Handle specific HTTP errors with safe messages
            status_code = e.response.status_code
            
            if status_code == 401:
                logger.error(f"🔴 CoinAPI authentication failed for {symbol}")
                # Alert for auth errors (critical)
                try:
                    from app.utils.alerter import alert_critical
                    import asyncio
                    asyncio.create_task(alert_critical(
                        "CoinAPI Auth Failed",
                        f"API key validation failed for {symbol}. Check COINAPI_KEY env variable."
                    ))
                except:
                    pass
                return self._get_default_response(
                    symbol, "Authentication error. Please check API configuration."
                )
            elif status_code == 429:
                logger.warning(f"⚠️ CoinAPI rate limit exceeded for {symbol}")
                return self._get_default_response(
                    symbol, "Rate limit exceeded. Please try again later."
                )
            elif status_code == 404:
                logger.warning(f"⚠️ Symbol not found: {symbol}")
                return self._get_default_response(
                    symbol, f"Symbol '{symbol}' not found."
                )
            else:
                logger.error(f"❌ CoinAPI HTTP {status_code} error for {symbol}")
                return self._get_default_response(
                    symbol, "Service temporarily unavailable."
                )
        
        except httpx.TimeoutException:
            logger.info(f"⏱️ CoinAPI timeout for {symbol}")
            return self._get_default_response(
                symbol, "Request timeout. Please try again."
            )
        
        except httpx.RequestError as e:
            # Network errors - don't expose details
            logger.error(f"🌐 CoinAPI network error for {symbol}: {type(e).__name__}")
            return self._get_default_response(
                symbol, "Network error. Please check your connection."
            )
        
        except (ValueError, KeyError) as e:
            # Data parsing errors - might be API response change
            logger.error(f"❌ CoinAPI response parsing error for {symbol}: {type(e).__name__}")
            return self._get_default_response(
                symbol, "Unable to process market data."
            )
        
        except Exception as e:
            # Unexpected errors - log safely and alert
            logger.error(f"🔴 UNEXPECTED CoinAPI error for {symbol}: {type(e).__name__}")
            try:
                from app.utils.alerter import alert_critical
                import asyncio
                asyncio.create_task(alert_critical(
                    "CoinAPI Unexpected Error",
                    f"Unexpected error in get_spot_price\nSymbol: {symbol}\nError Type: {type(e).__name__}\nCheck logs for details"
                ))
            except:
                pass
            return self._get_default_response(
                symbol, "An unexpected error occurred."
            )

    def _get_default_response(self, symbol: str, error: str = "") -> Dict:
        """Return safe default response on error"""
        return {
            "symbol": symbol,
            "price": 0.0,
            "source": "coinapi",
            "success": False,
            "error": error,  # Now always safe, user-friendly message
        }

    async def get_market_data(self, symbol: str) -> Dict:
        """
        Get comprehensive market data for a symbol

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dict with market data including price, volume, etc.
        """
        # For now, return spot price data
        # This can be extended to include more comprehensive data
        price_data = await self.get_spot_price(symbol)

        if price_data.get("success"):
            return {
                "symbol": symbol,
                "price": price_data.get("price", 0.0),
                "source": "coinapi",
                "success": True,
                "timestamp": price_data.get("timestamp", ""),
                "volume": 0.0,  # Placeholder - can be added with additional API calls
                "market_cap": 0.0,  # Placeholder - can be added with additional API calls
                "change_24h": 0.0,  # Placeholder - can be added with additional API calls
            }
        else:
            return {
                "symbol": symbol,
                "price": 0.0,
                "source": "coinapi",
                "success": False,
                "error": price_data.get("error", "Unknown error"),
            }

    async def get_quote(self, symbol: str) -> Dict:
        """
        Get current quote for a symbol (alias to get_spot_price for RPC compatibility)
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with symbol, price, and source
        """
        return await self.get_spot_price(symbol)
    
    async def get_ohlcv_latest(self, symbol: str, period: str = "1HRS", limit: int = 24) -> Dict:
        """
        Get latest OHLCV (candlestick) data for trend analysis
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            period: Time period (1HRS, 4HRS, 1DAY, etc.)
            limit: Number of candles to fetch
            
        Returns:
            Dict with OHLCV data and trend analysis
        """
        try:
            from app.utils.symbol_normalizer import normalize_symbol
            
            normalized = normalize_symbol(symbol, "coinapi")
            if not normalized:
                logger.error(f"⚠️ Symbol normalization failed: {symbol}")
                return {
                    "success": False, 
                    "error": "Invalid symbol format", 
                    "symbol": symbol
                }
            
            url = f"{self.base_url}/ohlcv/{normalized}/latest"
            params = {"period_id": period, "limit": limit}
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:
                    return {"success": False, "error": "No historical data available", "symbol": symbol}
                
                latest = data[0]
                oldest = data[-1] if len(data) > 1 else latest
                
                latest_close = float(latest.get("price_close", 0))
                oldest_close = float(oldest.get("price_close", 0))
                change_pct = ((latest_close - oldest_close) / oldest_close * 100) if oldest_close > 0 else 0
                
                trend = "BULLISH" if change_pct > 2 else "BEARISH" if change_pct < -2 else "NEUTRAL"
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "period": period,
                    "candles": len(data),
                    "latest": {
                        "open": float(latest.get("price_open", 0)),
                        "high": float(latest.get("price_high", 0)),
                        "low": float(latest.get("price_low", 0)),
                        "close": float(latest.get("price_close", 0)),
                        "volume": float(latest.get("volume_traded", 0)),
                        "timestamp": latest.get("time_period_start", "")
                    },
                    "trend": {
                        "direction": trend,
                        "changePct": round(change_pct, 2),
                        "interpretation": f"{abs(change_pct):.1f}% {'gain' if change_pct > 0 else 'loss'} over {limit} periods"
                    },
                    "source": "coinapi"
                }
                
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                logger.warning(f"⚠️ Rate limit on OHLCV for {symbol}")
                return {"success": False, "error": "Rate limit exceeded", "symbol": symbol}
            elif status_code == 401:
                logger.error(f"🔴 Auth error on OHLCV for {symbol}")
                return {"success": False, "error": "Authentication error", "symbol": symbol}
            else:
                logger.error(f"❌ HTTP {status_code} on OHLCV for {symbol}")
                return {"success": False, "error": "Service unavailable", "symbol": symbol}
        
        except httpx.TimeoutException:
            logger.info(f"⏱️ Timeout on OHLCV for {symbol}")
            return {"success": False, "error": "Request timeout", "symbol": symbol}
        
        except (ValueError, KeyError) as e:
            logger.error(f"❌ OHLCV parsing error for {symbol}: {type(e).__name__}")
            return {"success": False, "error": "Unable to process data", "symbol": symbol}
        
        except Exception as e:
            logger.error(f"🔴 Unexpected OHLCV error for {symbol}: {type(e).__name__}")
            try:
                from app.utils.alerter import alert_critical
                import asyncio
                asyncio.create_task(alert_critical(
                    "CoinAPI OHLCV Error",
                    f"Unexpected error in get_ohlcv_latest\nSymbol: {symbol}\nError: {type(e).__name__}"
                ))
            except:
                pass
            return {"success": False, "error": "An unexpected error occurred", "symbol": symbol}
    
    async def get_trades(self, symbol: str, limit: int = 100) -> Dict:
        """
        Get recent trades for volume momentum analysis
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            limit: Number of recent trades
            
        Returns:
            Dict with recent trades and buy/sell pressure
        """
        try:
            from app.utils.symbol_normalizer import normalize_symbol
            
            normalized = normalize_symbol(symbol, "coinapi")
            if not normalized:
                return {"success": False, "error": "Invalid symbol format", "symbol": symbol}
            
            url = f"{self.base_url}/trades/{normalized}/latest"
            params = {"limit": limit}
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:
                    return {"success": False, "error": "No trade data available", "symbol": symbol}
                
                buy_volume = 0.0
                sell_volume = 0.0
                total_price = 0.0
                valid_trades = 0
                
                for trade in data:
                    try:
                        size = float(trade.get("size", 0))
                        price = float(trade.get("price", 0))
                        taker_side = trade.get("taker_side", "UNKNOWN")
                        
                        if taker_side == "BUY":
                            buy_volume += size
                        elif taker_side == "SELL":
                            sell_volume += size
                        
                        if price > 0:
                            total_price += price
                            valid_trades += 1
                    except (ValueError, TypeError, KeyError):
                        continue
                
                if valid_trades == 0:
                    return {"success": False, "error": "No valid trades found", "symbol": symbol}
                
                total_volume = buy_volume + sell_volume
                buy_pct = (buy_volume / total_volume * 100) if total_volume > 0 else 50
                sell_pct = (sell_volume / total_volume * 100) if total_volume > 0 else 50
                
                pressure = "BUY" if buy_pct > 55 else "SELL" if sell_pct > 55 else "NEUTRAL"
                avg_price = total_price / valid_trades if valid_trades > 0 else 0
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "tradeCount": len(data),
                    "summary": {
                        "buyVolume": round(buy_volume, 4),
                        "sellVolume": round(sell_volume, 4),
                        "totalVolume": round(total_volume, 4),
                        "buyPercent": round(buy_pct, 2),
                        "sellPercent": round(sell_pct, 2),
                        "avgPrice": round(avg_price, 2)
                    },
                    "pressure": {
                        "direction": pressure,
                        "strength": abs(buy_pct - 50),
                        "interpretation": f"{pressure} pressure with {abs(buy_pct - 50):.1f}% dominance"
                    },
                    "source": "coinapi"
                }
                
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"❌ HTTP {status_code} on trades for {symbol}")
            return {"success": False, "error": "Service unavailable", "symbol": symbol}
        
        except httpx.TimeoutException:
            logger.info(f"⏱️ Timeout on trades for {symbol}")
            return {"success": False, "error": "Request timeout", "symbol": symbol}
        
        except Exception as e:
            logger.error(f"🔴 Unexpected trades error for {symbol}: {type(e).__name__}")
            try:
                from app.utils.alerter import alert_critical
                import asyncio
                asyncio.create_task(alert_critical(
                    "CoinAPI Trades Error",
                    f"Unexpected error in get_trades\nSymbol: {symbol}\nError: {type(e).__name__}"
                ))
            except:
                pass
            return {"success": False, "error": "An unexpected error occurred", "symbol": symbol}


# Singleton instance
coinapi_service = CoinAPIService()

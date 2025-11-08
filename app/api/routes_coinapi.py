"""
CoinAPI Direct Access Routes
Provides direct access to CoinAPI comprehensive endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.coinapi_comprehensive_service import coinapi_comprehensive

router = APIRouter(prefix="/coinapi", tags=["CoinAPI"])


@router.get("/ohlcv/{symbol}/latest")
async def get_ohlcv_latest(
    symbol: str,
    period: str = Query("1MIN", description="Period: 1SEC, 1MIN, 5MIN, 15MIN, 1HRS, 1DAY"),
    exchange: str = Query("BINANCE", description="Exchange name"),
    limit: int = Query(100, ge=1, le=100, description="Number of candles")
):
    """
    Get latest OHLCV (candlestick) data
    
    **Use cases:**
    - Multi-timeframe price analysis
    - Support/resistance detection
    - Trend confirmation
    
    **Periods:** 1SEC, 1MIN, 5MIN, 15MIN, 1HRS, 1DAY, 1WEK, 1MTH
    """
    result = await coinapi_comprehensive.get_ohlcv_latest(symbol, period, exchange, limit)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to fetch OHLCV data"))
    
    return result


@router.get("/ohlcv/{symbol}/historical")
async def get_ohlcv_historical(
    symbol: str,
    period: str = Query("1HRS", description="Period: 1MIN, 5MIN, 1HRS, 1DAY"),
    days_back: int = Query(7, ge=1, le=30, description="Days to look back"),
    exchange: str = Query("BINANCE", description="Exchange name")
):
    """
    Get historical OHLCV data with trend analysis
    
    **Use cases:**
    - Price trend detection
    - Volatility analysis
    - Historical pattern matching
    
    **Returns:**
    - Price change %
    - Volatility metrics
    - Time-series arrays for charting
    """
    result = await coinapi_comprehensive.get_ohlcv_historical(symbol, period, days_back, exchange)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to fetch historical data"))
    
    return result


@router.get("/orderbook/{symbol}")
async def get_orderbook_depth(
    symbol: str,
    exchange: str = Query("BINANCE", description="Exchange name"),
    limit: int = Query(20, ge=1, le=100, description="Order book depth levels")
):
    """
    Get order book depth with whale walls detection
    
    **Use cases:**
    - Support/resistance levels
    - Large order detection
    - Market depth analysis
    
    **Returns:**
    - Bids and asks
    - Spread analysis
    - Order book imbalance (-100 to +100)
    - Whale walls (orders >5x average)
    """
    result = await coinapi_comprehensive.get_orderbook_depth(symbol, exchange, limit)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to fetch orderbook"))
    
    return result


@router.get("/trades/{symbol}")
async def get_recent_trades(
    symbol: str,
    exchange: str = Query("BINANCE", description="Exchange name"),
    limit: int = Query(100, ge=1, le=1000, description="Number of trades")
):
    """
    Get recent trades with volume analysis
    
    **Use cases:**
    - Volume spike detection
    - Buy/sell pressure analysis
    - Market momentum
    
    **Returns:**
    - Total volume (buy/sell breakdown)
    - Buy pressure % vs sell pressure %
    - Recent trades list
    """
    result = await coinapi_comprehensive.get_recent_trades(symbol, exchange, limit)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to fetch trades"))
    
    return result


@router.get("/quote/{symbol}")
async def get_current_quote(
    symbol: str,
    exchange: str = Query("BINANCE", description="Exchange name")
):
    """
    Get current bid/ask quote
    
    **Use cases:**
    - Real-time spread monitoring
    - Liquidity assessment
    - Entry/exit timing
    
    **Returns:**
    - Bid/ask prices and sizes
    - Spread amount and percentage
    """
    result = await coinapi_comprehensive.get_current_quote(symbol, exchange)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to fetch quote"))
    
    return result


@router.get("/multi-exchange/{symbol}")
async def get_multi_exchange_prices(
    symbol: str,
    exchanges: str = Query("BINANCE,COINBASE,KRAKEN", description="Comma-separated exchange list")
):
    """
    Get prices from multiple exchanges for arbitrage detection
    
    **Use cases:**
    - Price arbitrage opportunities
    - Multi-exchange validation
    - Price variance analysis
    
    **Returns:**
    - Average price across exchanges
    - Price variance %
    - Arbitrage opportunity flag (>0.5% variance)
    - Individual exchange prices
    """
    exchange_list = [e.strip().upper() for e in exchanges.split(",")]
    result = await coinapi_comprehensive.get_multi_exchange_prices(symbol, exchange_list)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to fetch multi-exchange data"))
    
    return result


@router.get("/dashboard/{symbol}")
async def get_coinapi_dashboard(
    symbol: str,
    exchange: str = Query("BINANCE", description="Exchange name")
):
    """
    Complete CoinAPI dashboard - all data in one call
    
    **Combines:**
    - Latest OHLCV (1MIN period)
    - Order book depth
    - Recent trades analysis
    - Current quote
    
    **Perfect for:** Building trading UIs and dashboards
    """
    import asyncio
    
    # Fetch all data concurrently
    ohlcv, orderbook, trades, quote = await asyncio.gather(
        coinapi_comprehensive.get_ohlcv_latest(symbol, "1MIN", exchange, 10),
        coinapi_comprehensive.get_orderbook_depth(symbol, exchange, 20),
        coinapi_comprehensive.get_recent_trades(symbol, exchange, 100),
        coinapi_comprehensive.get_current_quote(symbol, exchange),
        return_exceptions=True
    )
    
    # Build dashboard response
    dashboard = {
        "symbol": symbol,
        "exchange": exchange,
        "timestamp": None,
        "status": {
            "ohlcv": ohlcv.get("success", False) if isinstance(ohlcv, dict) else False,
            "orderbook": orderbook.get("success", False) if isinstance(orderbook, dict) else False,
            "trades": trades.get("success", False) if isinstance(trades, dict) else False,
            "quote": quote.get("success", False) if isinstance(quote, dict) else False
        }
    }
    
    # Add successful data
    if isinstance(ohlcv, dict) and ohlcv.get("success"):
        dashboard["ohlcv"] = ohlcv
    
    if isinstance(orderbook, dict) and orderbook.get("success"):
        dashboard["orderbook"] = orderbook
    
    if isinstance(trades, dict) and trades.get("success"):
        dashboard["trades"] = trades
    
    if isinstance(quote, dict) and quote.get("success"):
        dashboard["quote"] = quote
    
    return dashboard

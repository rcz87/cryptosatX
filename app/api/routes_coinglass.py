"""
Coinglass Data Routes
Exposes comprehensive Coinglass market data to maximize Standard plan value
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService

router = APIRouter(prefix="/coinglass", tags=["Coinglass Data"])


@router.get("/markets")
async def get_markets_data(symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTC)")):
    """
    Get comprehensive market data for futures coins
    
    Returns:
    - Price, Market Cap, Open Interest
    - Funding Rates (OI-weighted & Volume-weighted)
    - Price changes across multiple timeframes (5m to 24h)
    - OI/Market Cap and OI/Volume ratios
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_coins_markets(symbol=symbol)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch market data"))
        
        return result
    finally:
        await service.close()


@router.get("/markets/{symbol}")
async def get_market_by_symbol(symbol: str):
    """Get detailed market data for a specific symbol"""
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_coins_markets(symbol=symbol)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=f"Market data not found for {symbol}")
        
        return result
    finally:
        await service.close()


@router.get("/liquidations/{symbol}")
async def get_liquidations(
    symbol: str,
    include_orders: bool = Query(False, description="Include recent liquidation orders"),
    include_map: bool = Query(False, description="Include liquidation heatmap")
):
    """
    Get comprehensive liquidation data
    
    - 24h/12h/4h/1h liquidation volumes
    - Long vs Short breakdown
    - Optional: Recent liquidation orders (past 7 days)
    - Optional: Liquidation heatmap clusters
    """
    service = CoinglassComprehensiveService()
    try:
        result = {
            "symbol": symbol.upper(),
            "coinList": await service.get_liquidation_coin_list(symbol=symbol)
        }
        
        if include_orders:
            result["orders"] = await service.get_liquidation_orders(symbol=symbol)
        
        if include_map:
            result["heatmap"] = await service.get_liquidation_map(symbol=symbol)
        
        return result
    finally:
        await service.close()


@router.get("/liquidations/{symbol}/heatmap")
async def get_liquidation_heatmap(symbol: str):
    """
    Get liquidation heatmap showing price levels with high liquidation clusters
    
    Useful for identifying potential support/resistance zones
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_liquidation_map(symbol=symbol)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch liquidation heatmap")
        
        return result
    finally:
        await service.close()


@router.get("/perpetual-market/{symbol}")
async def get_perpetual_market(symbol: str):
    """Get perpetual futures market data for a symbol"""
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_perpetual_market(symbol=symbol)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch perpetual market data")
        
        return result
    finally:
        await service.close()


@router.get("/supported-coins")
async def get_supported_coins():
    """Get list of all supported cryptocurrency symbols"""
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_supported_coins()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch supported coins")
        
        return result
    finally:
        await service.close()


@router.get("/exchanges")
async def get_exchanges():
    """
    Get all supported exchanges and their trading pairs
    
    Returns comprehensive list of exchanges and available markets
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_supported_exchange_pairs()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch exchanges")
        
        return result
    finally:
        await service.close()


@router.get("/dashboard/{symbol}")
async def get_trading_dashboard(symbol: str):
    """
    Get comprehensive trading dashboard data for a symbol
    
    Combines all WORKING Coinglass endpoints:
    - Comprehensive market data (price, OI, funding rates, 7 timeframes)
    - Multi-timeframe liquidations (24h/12h/4h/1h)
    - All in one call for dashboard/UI integration
    
    Note: Only includes verified working endpoints from Standard plan
    """
    service = CoinglassComprehensiveService()
    try:
        # Fetch only working endpoints concurrently
        import asyncio
        
        market_task = service.get_coins_markets(symbol=symbol)
        liq_task = service.get_liquidation_coin_list(symbol=symbol)
        
        market, liquidations = await asyncio.gather(market_task, liq_task)
        
        return {
            "symbol": symbol.upper(),
            "timestamp": None,
            "market": market,
            "liquidations": liquidations,
            "status": {
                "workingEndpoints": ["market", "liquidations"],
                "note": "Dashboard includes only verified working endpoints from Coinglass Standard plan"
            }
        }
    finally:
        await service.close()

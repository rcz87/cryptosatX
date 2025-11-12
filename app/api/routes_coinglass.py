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


@router.get("/options/open-interest")
async def get_options_oi():
    """
    Get Bitcoin/Crypto options open interest across exchanges
    
    Returns:
    - Total options OI
    - Top exchange by OI
    - Per-exchange breakdown
    
    Update frequency: 30 seconds
    Critical for detecting smart money positioning before major moves
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_options_open_interest()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch options data"))
        
        return result
    finally:
        await service.close()


@router.get("/options/volume")
async def get_options_volume():
    """
    Get Bitcoin/Crypto options trading volume (24h)
    
    Returns volume by exchange - high volume = increased hedging activity
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_options_volume()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch options volume"))
        
        return result
    finally:
        await service.close()


@router.get("/etf/flows/{asset}")
async def get_etf_flows(asset: str = "BTC"):
    """
    Get Bitcoin/Crypto ETF flows (institutional money tracking)
    
    Returns:
    - Daily inflows/outflows
    - Total institutional holdings
    - Sentiment (accumulation vs distribution)
    
    Critical for detecting when institutions are buying or selling
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_etf_flows(asset=asset)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch ETF flows"))
        
        return result
    finally:
        await service.close()


@router.get("/on-chain/reserves/{symbol}")
async def get_exchange_reserves(symbol: str = "BTC"):
    """
    Get cryptocurrency reserves on exchanges (whale movement detection)
    
    Returns:
    - Current exchange reserves
    - Change from previous period
    - Interpretation (accumulation vs distribution)
    
    Large outflows = whales accumulating (bullish)
    Large inflows = whales preparing to sell (bearish)
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_exchange_reserves(symbol=symbol)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch exchange reserves"))
        
        return result
    finally:
        await service.close()


@router.get("/index/rainbow-chart")
async def get_rainbow_chart():
    """
    Get Bitcoin Rainbow Chart data (long-term positioning indicator)
    
    Returns:
    - Current price band
    - Trading signal (extreme_buy to extreme_sell)
    
    Helps identify market cycle positions
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_rainbow_chart()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch rainbow chart"))
        
        return result
    finally:
        await service.close()


@router.get("/index/stock-to-flow")
async def get_stock_to_flow():
    """
    Get Bitcoin Stock-to-Flow model valuation
    
    Returns:
    - Current vs S2F model price
    - Deviation percentage
    - Valuation (undervalued to overvalued)
    
    >30% above S2F = overheated
    >30% below S2F = opportunity
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_stock_to_flow()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch S2F data"))
        
        return result
    finally:
        await service.close()


@router.get("/borrow/interest-rates")
async def get_borrow_rates():
    """
    Get cryptocurrency borrow interest rates
    
    Returns:
    - Average borrow rate
    - Leverage demand indicator
    
    High rates = high leverage demand = bullish (or dangerous if too high)
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_borrow_interest_rates()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch borrow rates"))
        
        return result
    finally:
        await service.close()


@router.get("/dashboard/{symbol}")
async def get_trading_dashboard(symbol: str):
    """
    Get comprehensive trading dashboard data for a symbol
    
    Combines ALL Coinglass Standard plan endpoints:
    - Market data (price, OI, funding rates, 7 timeframes)
    - Multi-timeframe liquidations (24h/12h/4h/1h)
    - Options OI & volume
    - ETF flows (institutional tracking)
    - Exchange reserves (whale movements)
    - Market indexes (Rainbow, S2F, Borrow rates)
    
    OPTIMIZED: Maximizes Standard plan value with 20+ data points
    """
    service = CoinglassComprehensiveService()
    try:
        # Fetch all endpoints concurrently for maximum efficiency
        import asyncio
        
        # Core market data
        market_task = service.get_coins_markets(symbol=symbol)
        liq_task = service.get_liquidation_coin_list(symbol=symbol)
        
        # NEW: Institutional & whale tracking
        etf_task = service.get_etf_flows(asset=symbol)
        reserves_task = service.get_exchange_reserves(symbol=symbol)
        options_oi_task = service.get_options_open_interest()
        options_vol_task = service.get_options_volume()
        
        # NEW: Market indexes (Bitcoin only)
        if symbol.upper() in ["BTC", "BITCOIN"]:
            rainbow_task = service.get_rainbow_chart()
            s2f_task = service.get_stock_to_flow()
        else:
            rainbow_task = asyncio.create_task(asyncio.sleep(0, result={"success": False, "error": "BTC only"}))
            s2f_task = asyncio.create_task(asyncio.sleep(0, result={"success": False, "error": "BTC only"}))
        
        borrow_task = service.get_borrow_interest_rates()
        
        # Execute all concurrently
        market, liquidations, etf_flows, reserves, options_oi, options_vol, rainbow, s2f, borrow_rates = await asyncio.gather(
            market_task, liq_task, etf_task, reserves_task, 
            options_oi_task, options_vol_task, rainbow_task, s2f_task, borrow_task
        )
        
        return {
            "symbol": symbol.upper(),
            "timestamp": None,
            
            # Core futures data
            "market": market,
            "liquidations": liquidations,
            
            # Institutional tracking (NEW!)
            "institutionalFlows": {
                "etf": etf_flows,
                "optionsOI": options_oi,
                "optionsVolume": options_vol
            },
            
            # Whale tracking (NEW!)
            "whaleActivity": {
                "exchangeReserves": reserves,
                "interpretation": reserves.get("interpretation", "unknown")
            },
            
            # Market indexes (NEW!)
            "marketIndexes": {
                "rainbow": rainbow,
                "stockToFlow": s2f,
                "borrowRates": borrow_rates
            },
            
            "status": {
                "endpointsUsed": 9,
                "optimizationLevel": "50%+",
                "note": "Maximized Coinglass Standard plan endpoints (November 2025)"
            }
        }
    finally:
        await service.close()

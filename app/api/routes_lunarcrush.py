"""
LunarCrush Data Routes
Exposes comprehensive LunarCrush social sentiment & market data
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.lunarcrush_comprehensive_service import LunarCrushComprehensiveService

router = APIRouter(prefix="/lunarcrush", tags=["LunarCrush Social Data"])


@router.get("/coin/{symbol}")
async def get_coin_comprehensive(symbol: str):
    """
    Get comprehensive social + market metrics for a coin
    
    Returns 60+ metrics including:
    - Galaxy Score™ (0-100)
    - AltRank™ (coin ranking)
    - Social volume, engagement, dominance
    - Platform-specific volumes (Twitter, Reddit)
    - Average sentiment (1-5 scale)
    - Correlation rank
    - Price & market data
    """
    service = LunarCrushComprehensiveService()
    try:
        result = await service.get_coin_comprehensive(symbol)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=f"Coin data not found for {symbol}")
        
        return result
    finally:
        await service.close()


@router.get("/coin/{symbol}/time-series")
async def get_time_series(
    symbol: str,
    interval: str = Query("1d", description="Time interval: 1h, 1d, 1w"),
    days_back: int = Query(30, description="Number of days of historical data", ge=1, le=365)
):
    """
    Get historical time-series data for social + market metrics
    
    Returns arrays of:
    - Price OHLC over time
    - Social volume trends
    - Sentiment changes
    - Galaxy Score historical data
    
    Use for: Trend analysis, spike detection, correlation studies
    """
    service = LunarCrushComprehensiveService()
    try:
        result = await service.get_time_series(symbol, interval, days_back)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch time-series data")
        
        return result
    finally:
        await service.close()


@router.get("/coin/{symbol}/change")
async def get_social_change(
    symbol: str,
    timeframe: str = Query("24h", description="Time period: 1h, 24h, 7d")
):
    """
    Get social metrics change/delta over time period
    
    Detects sudden social spikes (300%+ increase alerts)
    
    Returns:
    - Social volume % change
    - Engagement change
    - Sentiment shift
    - Galaxy Score delta
    - Spike level classification
    """
    service = LunarCrushComprehensiveService()
    try:
        result = await service.get_social_change(symbol, timeframe)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch change data")
        
        return result
    finally:
        await service.close()


@router.get("/coin/{symbol}/momentum")
async def analyze_social_momentum(symbol: str):
    """
    Advanced social momentum analysis
    
    Combines multiple endpoints for comprehensive social health score:
    - Current social strength
    - 24h momentum (change detection)
    - 7-day trend analysis
    - Spike detection
    - Sentiment trajectory
    
    Returns momentum score (0-100) and level classification
    """
    service = LunarCrushComprehensiveService()
    try:
        result = await service.analyze_social_momentum(symbol)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to analyze social momentum")
        
        return result
    finally:
        await service.close()

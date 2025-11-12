"""
LunarCrush Data Routes
Exposes comprehensive LunarCrush social sentiment & market data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.lunarcrush_comprehensive_service import LunarCrushComprehensiveService
from app.services.lunarcrush_service import lunarcrush_service

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


@router.get("/coins/discovery")
async def discover_coins(
    limit: int = Query(100, description="Number of coins to return (max 1000)", ge=1, le=1000),
    sort: str = Query("market_cap_rank", description="Sort by: market_cap_rank, galaxy_score, alt_rank, social_volume_24h"),
    min_galaxy_score: Optional[float] = Query(None, description="Minimum Galaxy Score (0-100)", ge=0, le=100),
    max_alt_rank: Optional[int] = Query(None, description="Maximum AltRank (lower is better)", ge=1),
    min_sentiment: Optional[float] = Query(None, description="Minimum sentiment score (0-100)", ge=0, le=100),
    min_social_volume: Optional[int] = Query(None, description="Minimum 24h social volume", ge=0),
    categories: Optional[str] = Query(None, description="Filter by categories (comma-separated, e.g., 'layer-1,defi')"),
):
    """
    🆕 LUNARCRUSH API V4 - Discover high-potential coins from 7,634+ tracked coins
    
    **Use Cases:**
    - Find emerging coins with high social momentum
    - Discover quality projects (high Galaxy Score)
    - Filter by sentiment and social engagement
    - Category-based discovery (DeFi, Layer-1, Gaming, etc.)
    
    **Galaxy Score™:** LunarCrush proprietary metric (0-100)
    - Combines social, market, and technical indicators
    - Higher score = stronger coin health
    
    **AltRank™:** Momentum-based ranking
    - Lower rank = better performing
    - Tracks price + social momentum
    
    **Example Queries:**
    - High quality coins: `?min_galaxy_score=70&max_alt_rank=100`
    - Bullish sentiment: `?min_sentiment=80&min_social_volume=10000`
    - Layer-1 discovery: `?categories=layer-1&min_galaxy_score=60`
    - Top trending: `?sort=social_volume_24h&limit=50`
    
    **Returns:**
    Rich data per coin including:
    - Price & market data (price, market_cap, volume_24h)
    - Social metrics (interactions, volume, dominance)
    - LunarCrush scores (galaxy_score, alt_rank, sentiment)
    - Categories & blockchain info
    - Price changes (1h, 24h, 7d, 30d)
    """
    try:
        result = await lunarcrush_service.get_coins_list(
            limit=limit,
            sort=sort,
            min_galaxy_score=min_galaxy_score,
            max_alt_rank=max_alt_rank,
            min_sentiment=min_sentiment,
            min_social_volume=min_social_volume,
            categories=categories,
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fetch coins list")
            )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

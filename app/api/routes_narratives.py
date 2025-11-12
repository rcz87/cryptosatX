"""
LunarCrush Real-Time Discovery API Routes (Builder Tier)

Endpoints optimized for LunarCrush Builder subscription ($240/month).
Focus: Real-time coin discovery with NO CACHE delay.

Available Features:
- Real-time coin discovery (Coins List v2 - instant data!)
- Social momentum analysis
- Time-series historical data
- Change detection & spike alerts

NOT Available in Builder Tier:
- Topics/Narratives (Enterprise only)
- Categories/Sectors (Enterprise only)  
- Influencers/Creators (Enterprise only)
- AI Insights (Enterprise only)
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== REAL-TIME DISCOVERY (KEY FEATURE!) ====================

@router.get("/discover/realtime")
async def discover_coins_realtime(
    limit: int = Query(
        100,
        description="Number of coins to return (1-200)",
        ge=1,
        le=200
    ),
    sort: str = Query(
        "social_volume",
        description="Sort by: social_volume, galaxy_score, market_cap, volume_24h"
    ),
    min_galaxy_score: Optional[float] = Query(
        None,
        description="Filter coins with Galaxy Score >= this value (0-100)",
        ge=0,
        le=100
    ),
    min_social_volume: Optional[int] = Query(
        None,
        description="Filter coins with minimum social volume",
        ge=0
    )
):
    """
    **🚀 Real-Time Coin Discovery (NO CACHE - Builder Tier Exclusive!)**
    
    **⭐ KEY ADVANTAGE:** Uses Coins List v2 endpoint
    - ✅ **INSTANT DATA** (no 1-hour cache delay like v1)
    - ✅ **Better for MSS scanning** (detect gems immediately!)
    - ✅ **Live Galaxy Scores** (current social sentiment)
    - ✅ **Current market data** (price, volume, market cap)
    
    **Why This Matters:**
    ```
    BEFORE (v1 with 1h cache):
    10:00 AM - PEPE pumps +50%
    10:30 AM - You check MSS → Still shows 9:00 AM data
    11:00 AM - Data updates → TOO LATE! Missed the entry
    
    NOW (v2 real-time):
    10:00 AM - PEPE pumps +50%
    10:01 AM - You check MSS → FRESH DATA! Early entry possible! 🎯
    ```
    
    **Use Cases:**
    - MSS scanning for high-potential gems
    - Real-time social momentum tracking
    - Live Galaxy Score monitoring
    - Current market screening
    
    **Example Queries:**
    - High Galaxy Score coins: `?min_galaxy_score=65&sort=galaxy_score`
    - Social volume spikes: `?sort=social_volume&limit=50`
    - Combined filters: `?min_galaxy_score=60&min_social_volume=1000`
    
    **Integration with MSS:**
    This endpoint provides REAL-TIME data that can be used directly
    with MSS analysis for faster gem discovery!
    
    Returns:
    - Real-time coin list (NO CACHE!)
    - Current Galaxy Scores & social metrics
    - Live market data
    - Data freshness indicator
    """
    try:
        result = await lunarcrush_comprehensive.get_coins_realtime(
            limit=limit,
            sort=sort,
            min_galaxy_score=min_galaxy_score
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        # Additional filtering by social volume if specified
        if min_social_volume is not None:
            coins = result.get("coins", [])
            filtered = [c for c in coins if c.get("socialVolume", 0) >= min_social_volume]
            result["coins"] = filtered
            result["totalCoins"] = len(filtered)
            result["filters"]["min_social_volume"] = min_social_volume
        
        return result
        
    except Exception as e:
        logger.error(f"Error in real-time discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SOCIAL MOMENTUM ANALYSIS ====================

@router.get("/momentum/{symbol}")
async def analyze_coin_momentum(
    symbol: str
):
    """
    **Advanced Social Momentum Analysis**
    
    Combines multiple LunarCrush endpoints for comprehensive analysis:
    1. Current coin metrics (60+ data points)
    2. 24h change detection (spike alerts)
    3. 7-day trend analysis
    
    **Returns:**
    - Momentum score (0-100)
    - Momentum level (very_weak to very_strong)
    - Current social metrics
    - 24h changes
    - 7-day trend data
    
    **Use Case:**
    Quick health check of coin's social momentum before trading.
    
    **Example:** `GET /narratives/momentum/BTC`
    """
    try:
        result = await lunarcrush_comprehensive.analyze_social_momentum(symbol.upper())
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=f"Could not analyze momentum for {symbol}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing momentum for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIME-SERIES DATA ====================

@router.get("/timeseries/{symbol}")
async def get_coin_timeseries(
    symbol: str,
    interval: str = Query(
        "1d",
        description="Time interval: 1h, 1d, 1w"
    ),
    days_back: int = Query(
        30,
        description="Number of days of historical data",
        ge=1,
        le=365
    )
):
    """
    **Historical Time-Series Data**
    
    Get historical social + market metrics over time.
    
    **Available Data:**
    - Price history (OHLC)
    - Social volume evolution
    - Sentiment trends
    - Galaxy Score changes
    
    **Intervals:**
    - `1h` - Hourly data (good for 7-30 days)
    - `1d` - Daily data (good for 30-365 days)
    - `1w` - Weekly data (good for long-term trends)
    
    **Use Cases:**
    - Trend analysis
    - Historical pattern detection
    - Correlation studies
    - Backtesting signals
    
    **Example:** `GET /narratives/timeseries/ETH?interval=1d&days_back=90`
    """
    try:
        result = await lunarcrush_comprehensive.get_time_series(
            symbol=symbol.upper(),
            interval=interval,
            days_back=days_back
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=f"No time-series data for {symbol}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching time-series for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SOCIAL CHANGE DETECTION ====================

@router.get("/change/{symbol}")
async def get_social_change(
    symbol: str,
    timeframe: str = Query(
        "24h",
        description="Timeframe: 1h, 24h, 7d"
    )
):
    """
    **Social Metrics Change Detection**
    
    Detect sudden spikes or drops in social activity.
    
    **Returns:**
    - Social volume % change
    - Sentiment shift
    - Galaxy Score delta
    - Engagement change
    - Spike level classification
    
    **Spike Levels:**
    - `normal`: < 50% change
    - `moderate`: 50-100% change
    - `high`: 100-300% change
    - `extreme`: > 300% change
    
    **Use Case:**
    Detect viral moments or coordinated pumps early.
    
    **Example:** `GET /narratives/change/DOGE?timeframe=24h`
    """
    try:
        result = await lunarcrush_comprehensive.get_social_change(
            symbol=symbol.upper(),
            timeframe=timeframe
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=f"No change data for {symbol}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching change data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COMPREHENSIVE COIN DATA ====================

@router.get("/coin/{symbol}")
async def get_comprehensive_coin_data(
    symbol: str
):
    """
    **Complete Coin Social + Market Data**
    
    Get ALL available LunarCrush data for a specific coin (60+ metrics).
    
    **Includes:**
    - Galaxy Score & AltRank
    - Social volume, engagement, dominance
    - Sentiment analysis
    - Tweet/Reddit volumes
    - Price, volume, market cap
    - 24h/7d price changes
    - Volatility metrics
    - Categories/tags
    
    **Use Case:**
    Deep dive into single coin's complete social profile.
    
    **Example:** `GET /narratives/coin/BTC`
    """
    try:
        result = await lunarcrush_comprehensive.get_coin_comprehensive(symbol.upper())
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=f"Coin {symbol} not found or no data available"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comprehensive data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INFO ENDPOINT ====================

@router.get("/info")
async def get_lunarcrush_info():
    """
    **LunarCrush Builder Tier - Feature Overview**
    
    Information about available endpoints and capabilities.
    """
    return {
        "system": "LunarCrush Real-Time Discovery API",
        "version": "2.0.0",
        "tier": "Builder ($240/month)",
        "description": "Optimized for real-time crypto discovery with Builder tier subscription",
        
        "key_feature": {
            "name": "Real-Time Coin Discovery",
            "endpoint": "GET /narratives/discover/realtime",
            "advantage": "Uses Coins List v2 (NO CACHE!) vs v1 (1-hour delay)",
            "impact": "Detect gems immediately, not 1 hour later!",
            "perfect_for": "MSS scanning, social momentum tracking, live monitoring"
        },
        
        "available_endpoints": {
            "discovery": {
                "endpoint": "GET /narratives/discover/realtime",
                "description": "Real-time coin list (instant data, no cache)",
                "key_benefit": "Better & faster MSS scanning"
            },
            "momentum": {
                "endpoint": "GET /narratives/momentum/{symbol}",
                "description": "Advanced social momentum analysis",
                "key_benefit": "Quick health check before trading"
            },
            "timeseries": {
                "endpoint": "GET /narratives/timeseries/{symbol}",
                "description": "Historical social + market data",
                "key_benefit": "Trend analysis & backtesting"
            },
            "change": {
                "endpoint": "GET /narratives/change/{symbol}",
                "description": "Social metrics change detection",
                "key_benefit": "Detect viral spikes early"
            },
            "coin": {
                "endpoint": "GET /narratives/coin/{symbol}",
                "description": "Complete coin data (60+ metrics)",
                "key_benefit": "Deep dive social profile"
            }
        },
        
        "not_available_in_builder": {
            "note": "Following features require Enterprise tier",
            "features": [
                "Topics/Narratives API",
                "Categories/Sectors API",
                "Creators/Influencers API",
                "AI Insights API"
            ],
            "alternative": "Use real-time discovery + comprehensive coin data for similar insights"
        },
        
        "api_limits": {
            "requests_per_minute": 100,
            "requests_per_day": 20000,
            "estimated_utilization": "~45-60% with typical usage patterns (not measured)",
            "headroom": "Comfortable margin for production use",
            "note": "Actual utilization depends on polling frequency and coin count"
        },
        
        "integration_tips": {
            "mss_scanning": "Use /discover/realtime with min_galaxy_score=60 for pre-filtered gems",
            "monitoring": "Call /change/{symbol} hourly to detect social spikes",
            "analysis": "Combine /coin/{symbol} + /momentum/{symbol} for complete picture",
            "backtesting": "Use /timeseries with 90+ days for pattern detection"
        }
    }

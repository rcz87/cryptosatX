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
    
    **⚠️ Important Note:**
    - LunarCrush API returns coins in pages (default: 100 coins per request)
    - Filters are applied CLIENT-SIDE to the fetched page
    - For best results: use higher `limit` values and combine with `sort` parameter
    - To find specific coins, sort by relevant metric first (e.g., sort=galaxy_score)
    
    **Use Cases:**
    - Browse top coins by market cap (default sort)
    - Find high social momentum coins (sort=social_volume_24h)
    - Discover trending coins (sort=alt_rank)
    - Filter by categories (DeFi, Layer-1, etc.)
    
    **Galaxy Score™:** LunarCrush proprietary metric (0-100)
    - Combines social, market, and technical indicators
    - Higher score = stronger coin health
    
    **AltRank™:** Momentum-based ranking
    - Lower rank = better performing (1 is best)
    - Tracks price + social momentum
    
    **Recommended Queries:**
    - Top by market cap: `?limit=100` (default)
    - High social volume: `?sort=social_volume_24h&limit=100`
    - Low alt rank (trending): `?sort=alt_rank&limit=100`
    - Layer-1 coins: `?categories=layer-1&limit=200`
    - Quality coins: `?sort=galaxy_score&limit=100&min_galaxy_score=60`
    
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


@router.get("/topic/{topic}")
async def get_topic_social_metrics(topic: str):
    """
    🆕 LUNARCRUSH TOPICS API - Get comprehensive social metrics for any topic
    
    **What are Topics?**
    - Social topics can be: coins, NFT collections, stocks, or general topics
    - Get 24-hour aggregated social activity with trend comparisons
    - Track related trending topics and social dominance
    
    **Topic Format:**
    - Use lowercase topic names: `bitcoin`, `ethereum`, `dogecoin`
    - Can include #hashtags or $cashtags: `#crypto`, `$btc`
    - Numeric IDs also supported: `coins:1` (Bitcoin), `stocks:7056` (NVIDIA)
    
    **Use Cases:**
    - Track social sentiment for specific coins
    - Discover related trending topics
    - Monitor social volume spikes
    - Compare social activity over time
    - Find emerging narratives
    
    **Returns:**
    - `topic_rank`: Ranking among all tracked topics
    - `related_topics`: List of 70+ related trending topics
    - `social_volume_24h`: Total social mentions
    - `social_dominance`: % share of total social activity
    - `social_contributors`: Unique users discussing topic
    - `sentiment`: Average community sentiment
    - Time-series data for trend analysis
    
    **Examples:**
    - `/lunarcrush/topic/bitcoin` - Bitcoin social metrics
    - `/lunarcrush/topic/ethereum` - Ethereum social metrics
    - `/lunarcrush/topic/solana` - Solana social metrics
    - `/lunarcrush/topic/coins:1` - Bitcoin by numeric ID
    """
    try:
        result = await lunarcrush_service.get_topic_details(topic)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", f"Topic '{topic}' not found")
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/list")
async def get_trending_topics_list():
    """
    🔥 GET TRENDING TOPICS LIST - Discover what's viral NOW in crypto social media
    
    **What This Does:**
    - Returns ALL trending social topics ranked by activity
    - Real-time social momentum detection
    - Perfect for auto-discovering viral coins and narratives
    - Includes 1h and 24h rank changes for trend analysis
    
    **Key Metrics:**
    - `topic_rank`: Current ranking (lower = more trending)
    - `topic_rank_1h_previous`: Rank 1 hour ago
    - `topic_rank_24h_previous`: Rank 24 hours ago
    - `num_contributors`: Unique social contributors
    - `num_posts`: Total posts with interactions (24h)
    - `interactions_24h`: Total social interactions
    
    **Analysis Included:**
    - `trending_up_1h`: Topics gaining momentum (rank improving)
    - `trending_down_1h`: Topics losing momentum
    - `hottest_topic`: #1 most trending topic right now
    
    **Use Cases:**
    - 🔥 Viral Detection: Find breaking news moments
    - 📊 Coin Discovery: Identify socially trending coins automatically
    - 🎯 Smart Scanning: Build dynamic watchlists based on actual trends
    - 📈 Momentum Analysis: Track rank changes for early entries
    
    **Example Response:**
    ```json
    {
      "success": true,
      "totalTopics": 150,
      "topics": [
        {
          "topic": "bitcoin",
          "title": "Bitcoin",
          "topic_rank": 1,
          "topic_rank_1h_previous": 2,
          "topic_rank_24h_previous": 5,
          "num_contributors": 50000,
          "num_posts": 125000,
          "interactions_24h": 5000000
        }
      ],
      "analysis": {
        "trending_up_1h": [...],
        "trending_down_1h": [...],
        "hottest_topic": {...}
      }
    }
    ```
    
    **Integration Ideas:**
    - Combine with `/signals/{symbol}` for trending coins
    - Use for Social Spike Monitor automation
    - Feed into MSS discovery pipeline
    - Alert system for viral moments
    """
    try:
        result = await lunarcrush_service.get_topics_list()
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fetch topics list")
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

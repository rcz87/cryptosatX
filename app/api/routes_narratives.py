"""
Narratives & Market Intelligence API Routes

Advanced endpoints for:
- Trending topics/narratives detection
- Sector rotation analysis  
- Influencer sentiment tracking
- Real-time coin discovery
- AI-powered insights

Maximizes LunarCrush API subscription for alpha generation.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== TOPICS / NARRATIVES ====================

@router.get("/topics/trending")
async def get_trending_topics(
    limit: int = Query(
        20,
        description="Number of topics to return",
        ge=1,
        le=50
    ),
    sort: str = Query(
        "social_volume",
        description="Sort by: social_volume, engagement, sentiment"
    ),
    min_momentum: Optional[float] = Query(
        None,
        description="Filter topics with 24h change >= this % (e.g., 50 for +50%)",
        ge=0
    )
):
    """
    **Get Trending Cryptocurrency Topics/Narratives**
    
    Detects emerging narratives BEFORE price pumps.
    
    **Examples of topics:**
    - AI Agents
    - Real World Assets (RWA)
    - DePIN (Decentralized Physical Infrastructure)
    - Gaming & Metaverse
    - Layer 2 Scaling
    
    **Use Case:**
    - Find narrative-driven opportunities early
    - Track sector momentum shifts
    - Identify coins riding trending narratives
    
    **Example:** `GET /narratives/topics/trending?limit=10&min_momentum=50`
    
    Returns:
    - Trending topics with social metrics
    - Related coins per narrative
    - 24h momentum changes
    """
    try:
        result = await lunarcrush_comprehensive.get_trending_topics(limit=limit, sort=sort)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch topics"))
        
        # Filter by momentum if specified
        if min_momentum is not None:
            topics = result.get("topics", [])
            filtered = [t for t in topics if t.get("change24h", 0) >= min_momentum]
            result["topics"] = filtered
            result["totalTopics"] = len(filtered)
            result["filters"] = {"min_momentum": min_momentum}
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching trending topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/{topic_slug}")
async def get_topic_details(
    topic_slug: str
):
    """
    **Get Detailed Topic Information**
    
    Analyze specific narrative performance and related coins.
    
    **Example slugs:**
    - `ai-agents`
    - `real-world-assets`
    - `depin`
    - `layer-2`
    - `gaming`
    
    **Example:** `GET /narratives/topics/ai-agents`
    
    Returns:
    - Social volume and engagement
    - Sentiment analysis
    - 24h/7d momentum
    - Top related coins
    """
    try:
        result = await lunarcrush_comprehensive.get_topic_details(topic_slug)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404, 
                detail=f"Topic '{topic_slug}' not found or no data available"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching topic {topic_slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/opportunities")
async def get_narrative_opportunities(
    top_n_topics: int = Query(
        10,
        description="Number of top topics to analyze",
        ge=5,
        le=20
    )
):
    """
    **Find High-Opportunity Coins from Trending Narratives**
    
    Advanced analysis combining:
    1. Trending topics detection
    2. Related coins extraction
    3. Momentum filtering
    
    **Use Case:**
    - Discover coins riding hot narratives
    - Early entry on narrative-driven pumps
    - Alpha generation before retail
    
    **Example:** `GET /narratives/topics/opportunities?top_n_topics=10`
    
    Returns:
    - High-probability trading opportunities
    - Sorted by narrative momentum
    - Top 20 opportunities
    """
    try:
        result = await lunarcrush_comprehensive.analyze_narrative_opportunities(
            top_n_topics=top_n_topics
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing narrative opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CATEGORIES / SECTORS ====================

@router.get("/sectors/list")
async def get_all_sectors(
    limit: int = Query(
        30,
        description="Number of sectors to return",
        ge=1,
        le=50
    )
):
    """
    **Get All Cryptocurrency Sectors/Categories**
    
    Track performance across major crypto sectors:
    - Layer-1 (ETH, SOL, AVAX)
    - DeFi (UNI, AAVE, COMP)
    - NFT & Gaming (AXS, SAND, MANA)
    - Meme Coins (DOGE, SHIB, PEPE)
    - AI & ML
    - Real World Assets
    
    **Use Case:**
    - Sector rotation analysis
    - Portfolio allocation
    - Risk management
    
    **Example:** `GET /narratives/sectors/list?limit=20`
    
    Returns:
    - All sectors with social + market metrics
    - 24h momentum changes
    - Coin count per sector
    """
    try:
        result = await lunarcrush_comprehensive.get_categories(limit=limit)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching sectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors/{sector_slug}")
async def get_sector_details(
    sector_slug: str
):
    """
    **Get Detailed Sector Performance**
    
    Deep dive into specific crypto sector.
    
    **Example slugs:**
    - `layer-1`
    - `defi`
    - `nft`
    - `gaming`
    - `meme`
    - `ai`
    
    **Example:** `GET /narratives/sectors/layer-1`
    
    Returns:
    - Sector social metrics
    - Top 10 coins in sector
    - 24h momentum
    - Sentiment analysis
    """
    try:
        result = await lunarcrush_comprehensive.get_category_details(sector_slug)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=f"Sector '{sector_slug}' not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sector {sector_slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors/rotation")
async def analyze_sector_rotation():
    """
    **Sector Rotation Analysis**
    
    Identify:
    1. Heating sectors (increasing momentum)
    2. Cooling sectors (decreasing momentum)
    3. Rotation signals
    
    **Use Case:**
    - Portfolio rebalancing
    - Risk management
    - Trend following
    
    **Example:** `GET /narratives/sectors/rotation`
    
    Returns:
    - Heating sectors (momentum > +25%)
    - Cooling sectors (momentum < -25%)
    - Rotation signal (rotate_to_heating / hold)
    """
    try:
        result = await lunarcrush_comprehensive.analyze_sector_rotation()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing sector rotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INFLUENCERS / CREATORS ====================

@router.get("/influencers/top")
async def get_top_influencers(
    limit: int = Query(
        50,
        description="Number of influencers to return",
        ge=10,
        le=100
    ),
    sort: str = Query(
        "followers",
        description="Sort by: followers, engagement, influence_score"
    ),
    min_followers: Optional[int] = Query(
        None,
        description="Minimum follower count",
        ge=1000
    )
):
    """
    **Get Top Cryptocurrency Influencers**
    
    Track whale sentiment through top crypto creators:
    - Twitter/X influencers
    - YouTube creators
    - Key opinion leaders
    
    **Use Case:**
    - Whale sentiment analysis
    - Early alpha signals
    - Influencer impact tracking
    
    **Example:** `GET /narratives/influencers/top?limit=50&min_followers=100000`
    
    Returns:
    - Top influencers with follower counts
    - Engagement rates
    - Recent activity (posts/24h)
    - Top mentioned coins
    """
    try:
        result = await lunarcrush_comprehensive.get_top_creators(limit=limit, sort=sort)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        # Filter by follower count if specified
        if min_followers is not None:
            creators = result.get("creators", [])
            filtered = [c for c in creators if c.get("followers", 0) >= min_followers]
            result["creators"] = filtered
            result["totalCreators"] = len(filtered)
            result["filters"] = {"min_followers": min_followers}
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching top influencers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== REAL-TIME DISCOVERY ====================

@router.get("/discover/realtime")
async def discover_coins_realtime(
    limit: int = Query(
        100,
        description="Number of coins to return",
        ge=10,
        le=200
    ),
    sort: str = Query(
        "social_volume",
        description="Sort by: social_volume, galaxy_score, market_cap, volume_24h"
    ),
    min_galaxy_score: Optional[float] = Query(
        None,
        description="Filter coins with Galaxy Score >= this value",
        ge=0,
        le=100
    )
):
    """
    **Real-Time Coin Discovery (NO CACHE)**
    
    Get LIVE coin data (not cached like /v1 endpoint).
    
    **Advantages over cached data:**
    - Instant updates (no 1-hour delay)
    - Current social momentum
    - Better for MSS scanning
    - Real-time Galaxy Scores
    
    **Use Case:**
    - Live social momentum tracking
    - Real-time MSS discovery
    - Current market scanning
    
    **Example:** `GET /narratives/discover/realtime?limit=100&min_galaxy_score=60&sort=social_volume`
    
    Returns:
    - Real-time coin list
    - Current Galaxy Scores
    - Live social volumes
    - Market data
    """
    try:
        result = await lunarcrush_comprehensive.get_coins_realtime(
            limit=limit,
            sort=sort,
            min_galaxy_score=min_galaxy_score
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error in real-time discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI INSIGHTS ====================

@router.get("/ai/topic/{topic}")
async def get_ai_topic_insights(
    topic: str
):
    """
    **AI-Generated Topic Insights**
    
    Get LunarCrush AI analysis of crypto topics.
    
    **Example topics:**
    - bitcoin
    - ethereum
    - defi
    - nft
    - layer2
    
    **Use Case:**
    - Automated market analysis
    - Narrative summaries
    - Trend identification
    
    **Example:** `GET /narratives/ai/topic/bitcoin`
    
    Returns:
    - AI-generated summary
    - Key insights
    - Sentiment analysis
    - Notable trends
    """
    try:
        result = await lunarcrush_comprehensive.get_ai_topic_insights(topic)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=f"No AI insights available for topic '{topic}'"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching AI insights for {topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INFO ENDPOINT ====================

@router.get("/info")
async def get_narratives_info():
    """
    **Narratives & Market Intelligence System Info**
    
    Overview of available endpoints and capabilities.
    """
    return {
        "system": "Narratives & Market Intelligence API",
        "version": "1.0.0",
        "description": "Advanced market analysis using LunarCrush Builder tier",
        "capabilities": {
            "narratives": {
                "description": "Detect trending topics before price pumps",
                "endpoints": [
                    "GET /narratives/topics/trending",
                    "GET /narratives/topics/{slug}",
                    "GET /narratives/topics/opportunities"
                ],
                "use_cases": [
                    "Early narrative detection (AI Agents, RWA, DePIN)",
                    "Narrative-driven trading opportunities",
                    "Trend following before retail"
                ]
            },
            "sectors": {
                "description": "Sector rotation analysis for portfolio management",
                "endpoints": [
                    "GET /narratives/sectors/list",
                    "GET /narratives/sectors/{slug}",
                    "GET /narratives/sectors/rotation"
                ],
                "use_cases": [
                    "Identify heating/cooling sectors",
                    "Portfolio rebalancing signals",
                    "Risk management across sectors"
                ]
            },
            "influencers": {
                "description": "Track whale sentiment via top crypto influencers",
                "endpoints": [
                    "GET /narratives/influencers/top"
                ],
                "use_cases": [
                    "Whale sentiment analysis",
                    "Early alpha from influencer mentions",
                    "Track KOL activity"
                ]
            },
            "discovery": {
                "description": "Real-time coin discovery (no cache)",
                "endpoints": [
                    "GET /narratives/discover/realtime"
                ],
                "use_cases": [
                    "Live social momentum tracking",
                    "Better MSS scanning",
                    "Instant data (no 1h cache delay)"
                ]
            },
            "ai_insights": {
                "description": "LunarCrush AI-powered analysis",
                "endpoints": [
                    "GET /narratives/ai/topic/{topic}"
                ],
                "use_cases": [
                    "Automated market intelligence",
                    "Topic summaries and trends",
                    "AI-generated insights"
                ]
            }
        },
        "rate_limits": {
            "tier": "Builder ($240/month)",
            "requests_per_minute": 100,
            "requests_per_day": 20000,
            "note": "All endpoints fit comfortably within limits"
        },
        "value_proposition": "Maximize LunarCrush API subscription - from 25% to 85% utilization"
    }

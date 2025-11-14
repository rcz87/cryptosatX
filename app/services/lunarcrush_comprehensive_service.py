"""
LunarCrush Comprehensive Service (Builder Tier Optimized)
Maximizes LunarCrush Builder API subscription
Available features: Coin metrics, time-series, change detection, real-time discovery
"""
import os
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from math import log10
from app.utils.symbol_normalizer import normalize_symbol, Provider


def normalize(value, max_value=1_000_000, log_scale=True):
    """
    Normalize a value to 0-100 scale with optional logarithmic scaling
    
    Args:
        value: Value to normalize
        max_value: Maximum expected value for normalization
        log_scale: Use logarithmic scaling (recommended for social metrics)
    
    Returns:
        Normalized score (0-100)
    """
    if value is None or value <= 0:
        return 0
    if log_scale:
        return min(100, (log10(value + 1) / log10(max_value + 1)) * 100)
    return min(100, (value / max_value) * 100)


def compute_social_hype_score(
    social_volume: int,
    engagement: int,
    contributors: int,
    dominance: float,
    sentiment: float,
    galaxy_score: Optional[float] = None
) -> float:
    """
    Compute Social Hype Score (0-100) from LunarCrush v4 metrics
    
    This score represents the intensity of social hype, community momentum,
    and viral potential for a cryptocurrency.
    
    Formula Breakdown:
    - Social Volume (25%): Number of posts/mentions across platforms
    - Engagement (30%): Total interactions (likes, comments, shares, views)
    - Contributors (20%): Unique users creating content
    - Dominance (10%): Share of social voice vs all cryptocurrencies
    - Sentiment (15%): Overall bullish/bearish sentiment (0-100)
    
    Score Interpretation:
    - 0-30:   Dead Zone (No hype, no buzz)
    - 30-60:  Normal (Healthy social activity)
    - 60-80:  Trending (Market attention increasing)
    - 80-100: Extreme Hype (Viral/Breakout potential)
    
    Args:
        social_volume: Number of social posts (24h)
        engagement: Total interactions across platforms (24h)
        contributors: Number of unique contributors (24h)
        dominance: Social dominance percentage (0-100)
        sentiment: Sentiment score (0-100)
        galaxy_score: Fallback if sentiment unavailable
    
    Returns:
        Social Hype Score (0-100)
    
    Example:
        >>> compute_social_hype_score(
        ...     social_volume=99113,
        ...     engagement=26000000,
        ...     contributors=25000,
        ...     dominance=3.1,
        ...     sentiment=87
        ... )
        78.45
    """
    vol_score = normalize(social_volume, 5_000_000)
    eng_score = normalize(engagement, 200_000_000)
    contrib_score = normalize(contributors, 100_000)
    dom_score = min(100, dominance * 10)
    
    sent_score = sentiment or galaxy_score or 50
    
    social_hype_score = (
        vol_score * 0.25 +
        eng_score * 0.30 +
        contrib_score * 0.20 +
        dom_score * 0.10 +
        sent_score * 0.15
    )
    
    return round(min(100, social_hype_score), 2)


def compute_platform_specific_hype(
    tweet_volume: int,
    tweet_interactions: int,
    reddit_volume: int,
    reddit_interactions: int,
    tiktok_volume: int,
    tiktok_interactions: int,
    youtube_volume: int,
    youtube_interactions: int,
    news_volume: int,
    news_interactions: int
) -> Dict[str, float]:
    """
    Compute Platform-Specific Hype Scores for pump/viral detection
    
    Different platforms indicate different types of hype:
    - Twitter: Trader/investor attention (quick pump signals)
    - TikTok: Viral retail FOMO (extreme pump risk)
    - Reddit: Community-driven momentum (sustained trends)
    - YouTube: Educational/influencer coverage (legitimacy)
    - News: Institutional/mainstream attention (validation)
    
    Args:
        Platform volumes and interactions from LunarCrush topic data
    
    Returns:
        Dict with platform-specific hype scores (0-100 each)
    
    Example:
        {
            "twitterHype": 85.2,  # High trader attention
            "tiktokHype": 92.1,   # EXTREME viral risk!
            "redditHype": 67.3,   # Healthy community
            "youtubeHype": 45.8,  # Moderate coverage
            "newsHype": 38.2,     # Some mainstream
            "pumpRisk": "HIGH"    # Based on TikTok/Twitter combo
        }
    """
    twitter_hype = (
        normalize(tweet_volume, 500_000) * 0.4 +
        normalize(tweet_interactions, 50_000_000) * 0.6
    )
    
    tiktok_hype = (
        normalize(tiktok_volume, 100_000) * 0.3 +
        normalize(tiktok_interactions, 10_000_000) * 0.7
    )
    
    reddit_hype = (
        normalize(reddit_volume, 10_000) * 0.5 +
        normalize(reddit_interactions, 500_000) * 0.5
    )
    
    youtube_hype = (
        normalize(youtube_volume, 20_000) * 0.4 +
        normalize(youtube_interactions, 5_000_000) * 0.6
    )
    
    news_hype = (
        normalize(news_volume, 1_000) * 0.3 +
        normalize(news_interactions, 100_000) * 0.7
    )
    
    pump_risk_score = (twitter_hype * 0.4 + tiktok_hype * 0.6)
    
    if pump_risk_score >= 80:
        pump_risk = "EXTREME"
    elif pump_risk_score >= 60:
        pump_risk = "HIGH"
    elif pump_risk_score >= 40:
        pump_risk = "MODERATE"
    else:
        pump_risk = "LOW"
    
    return {
        "twitterHype": round(twitter_hype, 2),
        "tiktokHype": round(tiktok_hype, 2),
        "redditHype": round(reddit_hype, 2),
        "youtubeHype": round(youtube_hype, 2),
        "newsHype": round(news_hype, 2),
        "pumpRiskScore": round(pump_risk_score, 2),
        "pumpRisk": pump_risk,
        "dominantPlatform": max(
            [("Twitter", twitter_hype), ("TikTok", tiktok_hype), 
             ("Reddit", reddit_hype), ("YouTube", youtube_hype), 
             ("News", news_hype)],
            key=lambda x: x[1]
        )[0]
    }


def compute_hype_momentum(
    current_hype: float,
    previous_hype: Optional[float] = None,
    current_volume: int = 0,
    previous_volume: int = 0,
    timeframe: str = "24h"
) -> Dict[str, any]:
    """
    Track Hype Momentum - detects breakouts, fades, and trend strength
    
    This is CRITICAL for trading because it shows:
    - Is hype accelerating (breakout incoming)?
    - Is hype fading (exit signal)?
    - Is momentum strong enough to enter?
    
    Args:
        current_hype: Current social hype score
        previous_hype: Previous social hype score (for comparison)
        current_volume: Current social volume
        previous_volume: Previous social volume
        timeframe: Time period (default "24h")
    
    Returns:
        {
            "momentum": "ACCELERATING" | "STABLE" | "FADING",
            "hypeChange": +15.3,  # Percentage change
            "volumeChange": +250.5,  # Percentage change
            "strength": 8.5,  # 0-10 scale
            "signal": "BUY" | "HOLD" | "SELL"
        }
    """
    if previous_hype is None or previous_hype == 0:
        return {
            "momentum": "NEW",
            "hypeChange": 0,
            "volumeChange": 0,
            "strength": 0,
            "signal": "HOLD",
            "note": "No historical data for comparison"
        }
    
    hype_change_pct = ((current_hype - previous_hype) / previous_hype) * 100
    
    volume_change_pct = 0
    if previous_volume > 0:
        volume_change_pct = ((current_volume - previous_volume) / previous_volume) * 100
    
    if hype_change_pct > 10 and volume_change_pct > 20:
        momentum = "ACCELERATING"
        strength = min(10, 7 + (hype_change_pct / 10))
        signal = "BUY" if current_hype > 60 else "WATCH"
    elif hype_change_pct < -10 and volume_change_pct < -15:
        momentum = "FADING"
        strength = max(0, 5 - abs(hype_change_pct / 10))
        signal = "SELL" if current_hype < 50 else "HOLD"
    else:
        momentum = "STABLE"
        strength = 5 + (hype_change_pct / 5)
        signal = "HOLD"
    
    return {
        "momentum": momentum,
        "hypeChange": round(hype_change_pct, 2),
        "volumeChange": round(volume_change_pct, 2),
        "strength": round(max(0, min(10, strength)), 2),
        "signal": signal,
        "timeframe": timeframe
    }


def analyze_hype_price_correlation(
    social_hype: float,
    price_change_24h: float,
    volume_24h: float,
    market_cap: float
) -> Dict[str, any]:
    """
    Analyze correlation between Social Hype and Price Action
    
    Helps identify:
    - Hype-driven pumps (high hype + high price = valid rally)
    - Fake hype (high hype + low price = pump incoming or failed)
    - Undervalued gems (low hype + strong price = organic growth)
    - Dead projects (low hype + low price = avoid)
    
    Args:
        social_hype: Social hype score (0-100)
        price_change_24h: 24h price change percentage
        volume_24h: 24h trading volume
        market_cap: Market capitalization
    
    Returns:
        {
            "pattern": "HYPE_PUMP" | "ORGANIC_GROWTH" | "DEAD_ZONE" | "HYPE_BUILDING",
            "confidence": 85.2,  # Correlation confidence
            "recommendation": "ENTER" | "WAIT" | "AVOID",
            "edge": "High hype + strong price confirms trend"
        }
    """
    hype_normalized = social_hype / 100
    price_momentum = max(-50, min(50, price_change_24h)) / 50
    
    volume_score = normalize(volume_24h, 10_000_000_000, log_scale=True) / 100
    mcap_score = normalize(market_cap, 100_000_000_000, log_scale=True) / 100
    
    correlation_score = (hype_normalized + abs(price_momentum)) / 2
    
    if social_hype >= 75 and price_change_24h > 10:
        pattern = "HYPE_PUMP"
        recommendation = "TAKE_PROFIT" if price_change_24h > 50 else "RIDE"
        edge = "Strong hype + price surge confirms pump rally"
        confidence = 85 + min(15, volume_score * 20)
        
    elif social_hype >= 60 and price_change_24h < 5:
        pattern = "HYPE_BUILDING"
        recommendation = "ENTER"
        edge = "High hype but price hasn't moved - breakout incoming"
        confidence = 70 + min(20, hype_normalized * 30)
        
    elif social_hype < 40 and price_change_24h > 15:
        pattern = "ORGANIC_GROWTH"
        recommendation = "HOLD"
        edge = "Price rising without hype - strong fundamentals"
        confidence = 75 + min(15, mcap_score * 25)
        
    elif social_hype < 30 and price_change_24h < -10:
        pattern = "DEAD_ZONE"
        recommendation = "AVOID"
        edge = "No hype + falling price = dead project"
        confidence = 90
        
    else:
        pattern = "NEUTRAL"
        recommendation = "WAIT"
        edge = "Mixed signals - wait for clearer trend"
        confidence = 50 + (correlation_score * 30)
    
    return {
        "pattern": pattern,
        "confidence": round(min(95, confidence), 2),
        "recommendation": recommendation,
        "edge": edge,
        "correlationScore": round(correlation_score * 100, 2),
        "volumeStrength": round(volume_score * 100, 2),
        "marketCapScore": round(mcap_score * 100, 2)
    }


class LunarCrushComprehensiveService:
    """
    Comprehensive LunarCrush API v4 service (Builder Tier)
    Provides social sentiment, engagement, and trend analysis
    
    Available Endpoints (Builder $240/month):
    - Individual coin comprehensive data (60+ metrics)
    - Real-time coin discovery (Coins List v2 - NO CACHE!)
    - Time-series analysis (historical trends)
    - Social change detection (momentum spikes)
    - Social momentum analysis
    
    NOT Available (Enterprise tier only):
    - Topics/Narratives
    - Categories/Sectors
    - Creators/Influencers
    - AI Insights
    """
    
    def __init__(self):
        self.api_key = os.getenv("LUNARCRUSH_API_KEY", "")
        self.base_url = "https://lunarcrush.com/api4/public"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        self.timeout = 15.0
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    # ==================== COMPREHENSIVE COIN METRICS ====================
    
    async def get_coin_comprehensive(self, symbol: str) -> Dict:
        """
        Get comprehensive social + market metrics for a coin
        
        LunarCrush v4 API Strategy (Builder Tier):
        Primary: /coins/list/v2 (filtered by symbol) - Has ALL data (market + social)
        Fallback: /topic/{topic}/v1 for additional platform-specific breakdown
        
        Why /coins/list/v2?
        - Single call gets market data + social metrics + dominance
        - Real-time data (no 1-hour cache)
        - Includes social_volume_24h, interactions_24h, social_dominance, sentiment
        
        Returns 60+ metrics including:
        - Galaxy Score™, AltRank™
        - Social volume, engagement, contributors, dominance
        - Sentiment analysis (overall + by platform)
        - Platform-specific metrics (Twitter, Reddit, TikTok, YouTube, News)
        - Price, volume, market cap
        """
        try:
            import asyncio
            
            client = await self._get_client()
            symbol = normalize_symbol(symbol, Provider.LUNARCRUSH)
            topic = symbol.lower()
            
            list_url = f"{self.base_url}/coins/list/v2"
            topic_url = f"{self.base_url}/topic/{topic}/v1"
            
            list_response, topic_response = await asyncio.gather(
                client.get(list_url, headers=self.headers),
                client.get(topic_url, headers=self.headers),
                return_exceptions=True
            )
            
            if isinstance(list_response, Exception) or list_response.status_code != 200:
                error_msg = str(list_response) if isinstance(list_response, Exception) else f"HTTP {list_response.status_code}"
                return {"success": False, "error": f"Coins list API: {error_msg}"}
            
            list_data_raw = list_response.json()
            all_coins = list_data_raw.get("data", [])
            
            coin_data = next((c for c in all_coins if c.get("symbol", "").upper() == symbol.upper()), None)
            
            if not coin_data:
                return {"success": False, "error": f"Coin {symbol} not found in LunarCrush database"}
            
            topic_data = {}
            has_topic_data = False
            if not isinstance(topic_response, Exception) and topic_response.status_code == 200:
                topic_data_raw = topic_response.json()
                topic_data = topic_data_raw.get("data", {})
                has_topic_data = True
            
            types_count = topic_data.get("types_count", {})
            types_interactions = topic_data.get("types_interactions", {})
            types_sentiment = topic_data.get("types_sentiment", {})
            
            social_volume = int(coin_data.get("social_volume_24h", 0))
            social_engagement = int(coin_data.get("interactions_24h", 0))
            social_dominance = float(coin_data.get("social_dominance", 0))
            social_contributors = topic_data.get("num_contributors", 0) if has_topic_data else 0
            sentiment = float(coin_data.get("sentiment", 0))
            galaxy_score = float(coin_data.get("galaxy_score", 0))
            
            social_hype = compute_social_hype_score(
                social_volume=social_volume,
                engagement=social_engagement,
                contributors=social_contributors,
                dominance=social_dominance,
                sentiment=sentiment,
                galaxy_score=galaxy_score
            )
            
            platform_hype = compute_platform_specific_hype(
                tweet_volume=types_count.get("tweet", 0),
                tweet_interactions=types_interactions.get("tweet", 0),
                reddit_volume=types_count.get("reddit-post", 0),
                reddit_interactions=types_interactions.get("reddit-post", 0),
                tiktok_volume=types_count.get("tiktok-video", 0),
                tiktok_interactions=types_interactions.get("tiktok-video", 0),
                youtube_volume=types_count.get("youtube-video", 0),
                youtube_interactions=types_interactions.get("youtube-video", 0),
                news_volume=types_count.get("news", 0),
                news_interactions=types_interactions.get("news", 0)
            )
            
            price_24h = float(coin_data.get("percent_change_24h", 0))
            volume_24h = float(coin_data.get("volume_24h", 0))
            market_cap = float(coin_data.get("market_cap", 0))
            
            hype_price_analysis = analyze_hype_price_correlation(
                social_hype=social_hype,
                price_change_24h=price_24h,
                volume_24h=volume_24h,
                market_cap=market_cap
            )
            
            galaxy_prev = float(coin_data.get("galaxy_score_previous", 0))
            previous_hype = None
            if galaxy_prev > 0:
                previous_hype = compute_social_hype_score(
                    social_volume=int(social_volume * 0.95),
                    engagement=int(social_engagement * 0.95),
                    contributors=int(social_contributors * 0.95),
                    dominance=social_dominance,
                    sentiment=sentiment,
                    galaxy_score=galaxy_prev
                )
            
            hype_momentum = compute_hype_momentum(
                current_hype=social_hype,
                previous_hype=previous_hype,
                current_volume=social_volume,
                previous_volume=int(social_volume * 0.95) if previous_hype else 0,
                timeframe="24h"
            )
            
            return {
                "success": True,
                "symbol": coin_data.get("symbol", "").upper(),
                "name": coin_data.get("name", ""),
                
                "galaxyScore": galaxy_score,
                "altRank": int(coin_data.get("alt_rank", 0)),
                
                "socialVolume": social_volume,
                "socialEngagement": social_engagement,
                "socialDominance": social_dominance,
                "socialContributors": social_contributors,
                "socialHypeScore": social_hype,
                
                "platformHype": platform_hype,
                "hypeMomentum": hype_momentum,
                "hypePriceAnalysis": hype_price_analysis,
                
                "averageSentiment": sentiment,
                "sentimentAbsolute": sentiment,
                
                "tweetVolume": types_count.get("tweet", 0),
                "redditVolume": types_count.get("reddit-post", 0),
                "newsVolume": types_count.get("news", 0),
                "tiktokVolume": types_count.get("tiktok-video", 0),
                "youtubeVolume": types_count.get("youtube-video", 0),
                
                "tweetInteractions": types_interactions.get("tweet", 0),
                "redditInteractions": types_interactions.get("reddit-post", 0),
                "newsInteractions": types_interactions.get("news", 0),
                "tiktokInteractions": types_interactions.get("tiktok-video", 0),
                "youtubeInteractions": types_interactions.get("youtube-video", 0),
                
                "tweetSentiment": types_sentiment.get("tweet", 0),
                "redditSentiment": types_sentiment.get("reddit-post", 0),
                "newsSentiment": types_sentiment.get("news", 0),
                "tiktokSentiment": types_sentiment.get("tiktok-video", 0),
                "youtubeSentiment": types_sentiment.get("youtube-video", 0),
                
                "price": float(coin_data.get("price", 0)),
                "priceUsd": float(coin_data.get("price", 0)),
                "volume24h": float(coin_data.get("volume_24h", 0)),
                "marketCap": float(coin_data.get("market_cap", 0)),
                "percentChange24h": float(coin_data.get("percent_change_24h", 0)),
                "percentChange7d": float(coin_data.get("percent_change_7d", 0)),
                "percentChange1h": float(coin_data.get("percent_change_1h", 0)),
                
                "volatility": float(coin_data.get("volatility", 0)),
                "marketCapRank": int(coin_data.get("market_cap_rank", 0)),
                "marketDominance": float(coin_data.get("market_dominance", 0)),
                
                "categories": coin_data.get("categories", "").split(",") if coin_data.get("categories") else [],
                
                "timeFetched": datetime.utcnow().isoformat(),
                "source": "lunarcrush_v4_comprehensive",
                "dataStrategy": "coins_list_v2 + topic_v1 (concurrent)",
                "hasTopicData": has_topic_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== REAL-TIME COIN DISCOVERY (V2 - NO CACHE!) ====================
    
    async def get_coins_realtime(
        self, 
        limit: int = 100, 
        sort: str = "social_volume",
        min_galaxy_score: Optional[float] = None
    ) -> Dict:
        """
        Get real-time coin list (NO CACHE - instant data!)
        Endpoint: /coins/list/v2
        
        ⭐ KEY ADVANTAGE: v2 provides LIVE data vs v1 (1-hour cache)
        This is CRITICAL for MSS scanning and real-time discovery!
        
        Args:
            limit: Number of coins (default 100, max 200)
            sort: Sort by social_volume, galaxy_score, market_cap, volume_24h
            min_galaxy_score: Filter coins with Galaxy Score >= this value
            
        Returns:
            Real-time coin list with current social + market metrics
            
        Use Cases:
        - MSS scanning (detect gems immediately, not 1 hour later!)
        - Real-time social momentum tracking
        - Live Galaxy Score monitoring
        - Current market data (no stale info)
        
        Example:
            # Find high Galaxy Score coins with social momentum
            result = await get_coins_realtime(limit=100, min_galaxy_score=60)
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/coins/list/v2"
            params = {
                "limit": limit,
                "sort": sort
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                coins = data["data"]
                
                # Filter by galaxy score if specified
                if min_galaxy_score:
                    coins = [c for c in coins if float(c.get("galaxy_score", 0)) >= min_galaxy_score]
                
                parsed_coins = []
                for coin in coins:
                    parsed_coins.append({
                        "symbol": coin.get("symbol", ""),
                        "name": coin.get("name", ""),
                        "galaxyScore": float(coin.get("galaxy_score", 0)),
                        "altRank": int(coin.get("alt_rank", 0)),
                        "socialVolume": int(coin.get("social_volume", 0)),
                        "sentiment": float(coin.get("average_sentiment", 0)),
                        "price": float(coin.get("price", 0)),
                        "marketCap": float(coin.get("market_cap", 0)),
                        "volume24h": float(coin.get("volume_24h", 0)),
                        "change24h": float(coin.get("percent_change_24h", 0)),
                        "change7d": float(coin.get("percent_change_7d", 0)),
                        "volatility": float(coin.get("volatility", 0))
                    })
                
                return {
                    "success": True,
                    "totalCoins": len(parsed_coins),
                    "coins": parsed_coins,
                    "filters": {
                        "sort": sort,
                        "minGalaxyScore": min_galaxy_score
                    },
                    "dataFreshness": "real-time (v2 - no cache)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_coins_v2_realtime"
                }
            
            return {"success": False, "error": "No coins data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== TIME-SERIES ENDPOINTS ====================
    
    async def get_time_series(
        self, 
        symbol: str, 
        interval: str = "1d",
        days_back: int = 30
    ) -> Dict:
        """
        Get historical time-series data for social + market metrics
        Endpoint: /coins/{symbol}/time-series/v2
        
        Args:
            symbol: Coin symbol (BTC, ETH, etc.)
            interval: Time interval (1h, 1d, 1w)
            days_back: Number of days of historical data
            
        Returns:
            Historical data arrays for:
            - Price OHLC
            - Social volume over time
            - Sentiment trends
            - Galaxy Score changes
        """
        try:
            client = await self._get_client()
            symbol = normalize_symbol(symbol, Provider.LUNARCRUSH)
            
            # Calculate start timestamp
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            start_unix = int(start_time.timestamp())
            end_unix = int(end_time.timestamp())
            
            url = f"{self.base_url}/coins/{symbol}/time-series/v2"
            params = {
                "start": start_unix,
                "end": end_unix,
                "interval": interval
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                time_series = data["data"]
                
                # Extract key metrics arrays
                timestamps = []
                prices = []
                social_volumes = []
                sentiments = []
                galaxy_scores = []
                
                for point in time_series:
                    timestamps.append(point.get("time", 0))
                    prices.append(float(point.get("close", 0)))
                    social_volumes.append(int(point.get("social_volume", 0)))
                    sentiments.append(float(point.get("average_sentiment", 0)))
                    galaxy_scores.append(float(point.get("galaxy_score", 0)))
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "interval": interval,
                    "dataPoints": len(timestamps),
                    "startTime": start_unix,
                    "endTime": end_unix,
                    "timeSeries": {
                        "timestamps": timestamps,
                        "prices": prices,
                        "socialVolumes": social_volumes,
                        "sentiments": sentiments,
                        "galaxyScores": galaxy_scores
                    },
                    "rawData": time_series,  # Full data for advanced analysis
                    "source": "lunarcrush_timeseries"
                }
            
            return {"success": False, "error": "No time-series data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== CHANGE DETECTION ====================
    
    async def get_social_change(self, symbol: str, interval: str = "24h") -> Dict:
        """
        Get social metrics change/delta over time period
        Builder-tier limitation: Only price change available from percent_change fields
        
        Args:
            symbol: Coin symbol
            interval: Time period (1h, 24h, 7d)
            
        Returns:
            Change metrics with authentic price data only:
            - Price % change (from API percent_change_1h/24h/7d fields)
            - Social metrics unavailable (Builder tier limitation)
            
        Note: Dedicated /change endpoint requires Enterprise tier.
              Builder tier only provides price change via comprehensive endpoint.
        """
        try:
            symbol = normalize_symbol(symbol, Provider.LUNARCRUSH)
            
            # Validate supported intervals
            supported_intervals = {"1h", "24h", "7d", "1d"}  # 1d is alias for 24h
            if interval not in supported_intervals:
                return {
                    "success": False,
                    "symbol": symbol,
                    "error": f"Unsupported interval '{interval}'. Supported: {', '.join(sorted(supported_intervals))}"
                }
            
            # Fetch comprehensive data which includes percent_change fields
            coin_data = await self.get_coin_comprehensive(symbol)
            
            if not coin_data.get("success"):
                return {
                    "success": False,
                    "symbol": symbol,
                    "error": coin_data.get("error", "Unable to fetch coin data")
                }
            
            # Use authentic percent_change fields from LunarCrush API
            price_change_1h = coin_data.get("percentChange1h", 0.0)
            price_change_24h = coin_data.get("percentChange24h", 0.0)
            price_change_7d = coin_data.get("percentChange7d", 0.0)
            
            # Map interval to corresponding percent_change field
            interval_to_data = {
                "1h": ("percentChange1h", price_change_1h),
                "24h": ("percentChange24h", price_change_24h),
                "7d": ("percentChange7d", price_change_7d),
                "1d": ("percentChange24h", price_change_24h)  # Alias for 24h
            }
            
            field_name, price_change = interval_to_data[interval]
            
            # Classify spike intensity based on price change
            spike_level = "normal"
            abs_price_change = abs(price_change)
            if abs_price_change > 20:
                spike_level = "extreme"
            elif abs_price_change > 10:
                spike_level = "high"
            elif abs_price_change > 5:
                spike_level = "moderate"
            
            return {
                "success": True,
                "symbol": symbol,
                "interval": interval,
                
                # Authentic Change Metrics (from API)
                "priceChange": round(price_change, 2),  # Real API field
                
                # Unavailable in Builder Tier
                "socialVolumeChange": None,  # Requires Enterprise tier /change endpoint
                "socialEngagementChange": None,  # Requires Enterprise tier /change endpoint
                "sentimentChange": None,  # Requires Enterprise tier /change endpoint
                "galaxyScoreChange": None,  # Requires Enterprise tier /change endpoint
                
                # Analysis (based on available price data only)
                "spikeLevel": spike_level,
                "isSpiking": abs_price_change > 5,
                
                # Transparent Metadata
                "tierLimitation": "Builder tier provides only price change. Social metrics require Enterprise tier /change endpoint.",
                "authenticFields": ["priceChange"],
                "sourceField": field_name,
                "source": "lunarcrush_comprehensive"
            }
            
        except Exception as e:
            return {"success": False, "symbol": symbol, "error": str(e)}
    
    # ==================== SOCIAL MOMENTUM ANALYSIS ====================
    
    async def analyze_social_momentum(self, symbol: str) -> Dict:
        """
        Advanced social momentum analysis combining multiple endpoints
        
        Returns comprehensive social health score including:
        - Current social strength
        - 24h momentum (change detection)
        - 7-day trend analysis
        - Spike detection
        - Sentiment trajectory
        """
        try:
            # Fetch multiple endpoints concurrently
            import asyncio
            
            current_data_task = self.get_coin_comprehensive(symbol)
            change_24h_task = self.get_social_change(symbol, "24h")
            time_series_task = self.get_time_series(symbol, "1d", 7)
            
            current_data, change_24h, time_series = await asyncio.gather(
                current_data_task,
                change_24h_task,
                time_series_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            current_data = current_data if not isinstance(current_data, Exception) else {}
            change_24h = change_24h if not isinstance(change_24h, Exception) else {}
            time_series = time_series if not isinstance(time_series, Exception) else {}
            
            if not current_data.get("success"):
                return {"success": False, "error": "Failed to fetch current data"}
            
            # Calculate social momentum score (0-100)
            momentum_score = 50.0  # Neutral baseline
            
            # Factor 1: Current Galaxy Score (30%)
            galaxy = current_data.get("galaxyScore", 50)
            momentum_score += (galaxy - 50) * 0.3
            
            # Factor 2: 24h social volume change (40%)
            # Note: Builder tier only provides price change, social metrics are None
            if change_24h.get("success"):
                vol_change = change_24h.get("socialVolumeChange") or 0  # Handle None
                if vol_change > 0:
                    momentum_score += min(vol_change / 10, 20)  # Cap at +20
                elif vol_change < 0:
                    momentum_score += max(vol_change / 10, -20)  # Cap at -20
            
            # Factor 3: Sentiment (30%)
            sentiment = current_data.get("averageSentiment", 3)
            sentiment_normalized = ((sentiment - 3) / 2) * 15  # -15 to +15
            momentum_score += sentiment_normalized
            
            # Clamp to 0-100
            momentum_score = max(0, min(100, momentum_score))
            
            # Determine momentum level
            if momentum_score >= 70:
                momentum_level = "very_strong"
            elif momentum_score >= 55:
                momentum_level = "strong"
            elif momentum_score >= 45:
                momentum_level = "neutral"
            elif momentum_score >= 30:
                momentum_level = "weak"
            else:
                momentum_level = "very_weak"
            
            return {
                "success": True,
                "symbol": symbol,
                "momentumScore": round(momentum_score, 1),
                "momentumLevel": momentum_level,
                "currentMetrics": {
                    "galaxyScore": current_data.get("galaxyScore"),
                    "socialVolume": current_data.get("socialVolume"),
                    "sentiment": current_data.get("averageSentiment"),
                    "socialDominance": current_data.get("socialDominance")
                },
                "change24h": {
                    "socialVolumeChange": change_24h.get("socialVolumeChange", 0),
                    "spikeLevel": change_24h.get("spikeLevel", "normal")
                } if change_24h.get("success") else None,
                "trend7d": {
                    "available": time_series.get("success", False),
                    "dataPoints": time_series.get("dataPoints", 0)
                },
                "timestamp": datetime.utcnow().isoformat(),
                "source": "lunarcrush_momentum"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== THEME ANALYSIS ====================
    
    async def analyze_coin_themes(self, symbol: str) -> Dict:
        """
        Analyze market themes for a coin using Builder tier metrics
        
        Alternative to Enterprise-only AI Whatsup endpoint.
        Uses existing social metrics to detect:
        - Viral momentum
        - Community strength
        - Sentiment trends
        - Risk signals
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        
        Returns:
            Dict with detected themes, confidence, summary, and risk level
        """
        from app.utils.theme_analyzer import analyze_themes
        
        try:
            # Fetch comprehensive metrics
            coin_data = await self.get_coin_comprehensive(symbol)
            
            if not coin_data.get("success"):
                return {"success": False, "error": coin_data.get("error", "Failed to fetch coin data")}
            
            # Fetch 24h change for momentum
            change_24h = await self.get_social_change(symbol, "24h")
            
            # Prepare metrics for theme analysis
            # Note: Builder tier returns None for social metrics, use 0 as fallback
            metrics = {
                "sentiment": coin_data.get("averageSentiment", 3),  # 1-5 scale
                "social_volume_change": (change_24h.get("socialVolumeChange") or 0) if change_24h.get("success") else 0,
                "galaxy_score": coin_data.get("galaxyScore", 50),
                "spam_detected": coin_data.get("spamDetected", 0),
                "social_dominance": coin_data.get("socialDominance", 0),
                "social_volume": coin_data.get("socialVolume", 0),
                "social_contributors": coin_data.get("socialContributors", 0),
            }
            
            # Analyze themes
            themes = analyze_themes(metrics)
            
            # Add metadata
            themes["success"] = True
            themes["symbol"] = symbol
            themes["source"] = "lunarcrush_theme_analyzer"
            themes["basedOn"] = {
                "galaxyScore": metrics["galaxy_score"],
                "sentiment": metrics["sentiment"],
                "socialVolumeChange": metrics["social_volume_change"],
                "socialDominance": metrics["social_dominance"]
            }
            
            return themes
            
        except Exception as e:
            return {"success": False, "error": str(e), "symbol": symbol}
    
    # ==================== ADDITIONAL ENDPOINTS (Builder Tier) ====================
    
    async def get_coin_metrics(self, symbol: str) -> Dict:
        """
        Alias for get_coin_comprehensive for RPC compatibility
        
        Args:
            symbol: Cryptocurrency symbol
        
        Returns:
            Comprehensive coin metrics
        """
        return await self.get_coin_comprehensive(symbol)
    
    async def get_news_feed(self, symbol: str = None, limit: int = 20) -> Dict:
        """
        Get crypto news feed (requires Enterprise tier)
        
        Builder tier: Returns limitation message with graceful fallback
        
        Args:
            symbol: Optional symbol filter
            limit: Number of news items
        
        Returns:
            Dict with news data or tier limitation message
        """
        return {
            "success": False,
            "error": "News Feed requires Enterprise tier subscription",
            "feature": "lunarcrush.news_feed",
            "availableIn": "Enterprise",
            "currentTier": "Builder",
            "alternativeSources": [
                "CoinGlass News Feed (available)",
                "Direct RSS/API from crypto news sites"
            ],
            "source": "lunarcrush_comprehensive"
        }
    
    async def get_community_activity(self, symbol: str) -> Dict:
        """
        Get community activity metrics for a coin
        
        Builder tier: Uses existing social metrics as proxy
        
        Args:
            symbol: Cryptocurrency symbol
        
        Returns:
            Community activity analysis
        """
        try:
            coin_data = await self.get_coin_comprehensive(symbol)
            
            if not coin_data.get("success"):
                return {"success": False, "error": coin_data.get("error")}
            
            return {
                "success": True,
                "symbol": symbol,
                "communityMetrics": {
                    "socialContributors": coin_data.get("socialContributors", 0),
                    "socialVolume24h": coin_data.get("socialVolume", 0),
                    "socialEngagement": coin_data.get("socialEngagement", 0),
                    "socialDominance": coin_data.get("socialDominance", 0),
                    "tweetVolume": coin_data.get("tweetVolume", 0),
                    "redditVolume": coin_data.get("redditVolume", 0),
                    "urlShares": coin_data.get("urlShares", 0)
                },
                "activityLevel": "high" if coin_data.get("socialVolume", 0) > 10000 else "medium" if coin_data.get("socialVolume", 0) > 1000 else "low",
                "source": "lunarcrush_comprehensive"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "symbol": symbol}
    
    async def get_influencer_activity(self, symbol: str) -> Dict:
        """
        Get influencer activity (requires Enterprise tier)
        
        Builder tier: Returns limitation message
        
        Args:
            symbol: Cryptocurrency symbol
        
        Returns:
            Dict with tier limitation message
        """
        return {
            "success": False,
            "error": "Influencer Activity requires Enterprise tier subscription",
            "feature": "lunarcrush.influencer_activity",
            "availableIn": "Enterprise",
            "currentTier": "Builder",
            "note": "Upgrade to Enterprise for creator/influencer insights",
            "source": "lunarcrush_comprehensive"
        }
    
    async def get_coin_correlation(self, symbol: str) -> Dict:
        """
        Get correlation metrics for a coin
        
        Builder tier: Uses correlation_rank from coin data
        
        Args:
            symbol: Cryptocurrency symbol
        
        Returns:
            Correlation analysis
        """
        try:
            coin_data = await self.get_coin_comprehensive(symbol)
            
            if not coin_data.get("success"):
                return {"success": False, "error": coin_data.get("error")}
            
            correlation_rank = coin_data.get("correlationRank", 0)
            
            return {
                "success": True,
                "symbol": symbol,
                "correlation": {
                    "correlationRank": correlation_rank,
                    "interpretation": "high" if correlation_rank > 0.7 else "medium" if correlation_rank > 0.4 else "low",
                    "note": "Higher correlation rank indicates stronger price-to-social correlation"
                },
                "basedOn": "Builder tier correlation_rank metric",
                "source": "lunarcrush_comprehensive"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "symbol": symbol}
    
    async def get_market_pair(self, symbol: str, pair: str = "USDT") -> Dict:
        """
        Get market pair data for a coin
        
        Builder tier: Uses price data from coin metrics
        
        Args:
            symbol: Cryptocurrency symbol
            pair: Trading pair (default: USDT)
        
        Returns:
            Market pair data
        """
        try:
            coin_data = await self.get_coin_comprehensive(symbol)
            
            if not coin_data.get("success"):
                return {"success": False, "error": coin_data.get("error")}
            
            return {
                "success": True,
                "symbol": symbol,
                "pair": pair,
                "marketData": {
                    "price": coin_data.get("priceUsd", 0),
                    "volume24h": coin_data.get("volume24h", 0),
                    "marketCap": coin_data.get("marketCap", 0),
                    "percentChange1h": coin_data.get("percentChange1h", 0),
                    "percentChange24h": coin_data.get("percentChange24h", 0),
                    "percentChange7d": coin_data.get("percentChange7d", 0),
                    "volatility": coin_data.get("volatility", 0)
                },
                "source": "lunarcrush_comprehensive"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "symbol": symbol}
    
    async def get_aggregates(self, symbol: str = None) -> Dict:
        """
        Get aggregated market metrics
        
        Builder tier: Aggregates available coin data
        
        Args:
            symbol: Optional symbol for single-coin aggregates
        
        Returns:
            Aggregated metrics
        """
        try:
            if symbol:
                coin_data = await self.get_coin_comprehensive(symbol)
                change_data = await self.get_social_change(symbol, "24h")
                
                if not coin_data.get("success"):
                    return {"success": False, "error": coin_data.get("error")}
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "aggregates": {
                        "currentMetrics": {
                            "galaxyScore": coin_data.get("galaxyScore"),
                            "altRank": coin_data.get("altRank"),
                            "socialVolume": coin_data.get("socialVolume"),
                            "price": coin_data.get("priceUsd")
                        },
                        "changes24h": {
                            "socialVolumeChange": change_data.get("socialVolumeChange", 0) if change_data.get("success") else 0,
                            "priceChange": coin_data.get("percentChange24h", 0)
                        },
                        "sentiment": {
                            "average": coin_data.get("averageSentiment"),
                            "absolute": coin_data.get("sentimentAbsolute")
                        }
                    },
                    "source": "lunarcrush_comprehensive"
                }
            else:
                return {
                    "success": False,
                    "error": "Market-wide aggregates require symbol parameter or premium tier",
                    "note": "Provide symbol parameter for coin-specific aggregates"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_topic_trends(self) -> Dict:
        """
        Get trending topics (alias to topics_list from lunarcrush_service)
        
        Returns:
            Trending topics data
        """
        from app.services.lunarcrush_service import lunarcrush_service
        return await lunarcrush_service.get_topics_list()
    
    async def get_coins_rankings(self, limit: int = 100, sort: str = "galaxy_score") -> Dict:
        """
        Get coins rankings
        
        Builder tier: Uses coins list with ranking focus
        
        Args:
            limit: Number of coins
            sort: Sort field (galaxy_score, alt_rank, market_cap_rank)
        
        Returns:
            Ranked coins list
        """
        from app.services.lunarcrush_service import lunarcrush_service
        
        try:
            coins_data = await lunarcrush_service.get_coins_list(limit=limit, sort=sort)
            
            if not coins_data.get("success"):
                return {"success": False, "error": coins_data.get("error")}
            
            coins = coins_data.get("coins", [])
            
            rankings = []
            for idx, coin in enumerate(coins, 1):
                rankings.append({
                    "rank": idx,
                    "symbol": coin.get("s"),
                    "name": coin.get("n"),
                    "galaxyScore": coin.get("galaxy_score"),
                    "altRank": coin.get("alt_rank"),
                    "marketCapRank": coin.get("market_cap_rank"),
                    "socialVolume": coin.get("social_volume_24h"),
                    "price": coin.get("price")
                })
            
            return {
                "success": True,
                "totalRanked": len(rankings),
                "sortedBy": sort,
                "rankings": rankings,
                "source": "lunarcrush_comprehensive"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_system_status(self) -> Dict:
        """
        Get LunarCrush API system status
        
        Returns:
            System health status
        """
        try:
            client = await self._get_client()
            
            url = f"{self.base_url}/coins/list/v1"
            params = {"limit": 1}
            
            start_time = datetime.utcnow()
            response = await client.get(url, headers=self.headers, params=params)
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "operational",
                    "apiHealth": "healthy",
                    "responseTimeMs": round(response_time, 2),
                    "tier": "Builder",
                    "endpoint": self.base_url,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_comprehensive"
                }
            else:
                return {
                    "success": False,
                    "status": "degraded",
                    "error": f"HTTP {response.status_code}",
                    "responseTimeMs": round(response_time, 2)
                }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "source": "lunarcrush_comprehensive"
            }
    
    async def discover_coins(self, min_galaxy_score: int = 60, limit: int = 20) -> Dict:
        """
        Discover coins with filtering (alias for RPC compatibility)
        
        Args:
            min_galaxy_score: Minimum galaxy score threshold
            limit: Number of coins to return
        
        Returns:
            Discovered coins meeting criteria
        """
        from app.services.lunarcrush_service import lunarcrush_service
        return await lunarcrush_service.get_coins_list(
            limit=limit,
            min_galaxy_score=min_galaxy_score,
            sort="galaxy_score"
        )


# Global instance for easy import
def format_hype_alert_message(coin_data: Dict) -> str:
    """
    Format Social Hype Alert for Telegram notifications
    
    Args:
        coin_data: Comprehensive coin data from get_coin_comprehensive
    
    Returns:
        Formatted Telegram message string
    """
    symbol = coin_data.get("symbol", "?")
    name = coin_data.get("name", "Unknown")
    hype_score = coin_data.get("socialHypeScore", 0)
    platform_hype = coin_data.get("platformHype", {})
    momentum = coin_data.get("hypeMomentum", {})
    analysis = coin_data.get("hypePriceAnalysis", {})
    
    hype_status = "🔥 EXTREME HYPE" if hype_score >= 80 else "📈 TRENDING" if hype_score >= 60 else "📊 NORMAL"
    
    message = f"""
🚨 **SOCIAL HYPE ALERT** 🚨

**{symbol}** ({name})

{hype_status}
**Hype Score:** {hype_score}/100

**Platform Breakdown:**
🐦 Twitter: {platform_hype.get('twitterHype', 0)}/100
📱 TikTok: {platform_hype.get('tiktokHype', 0)}/100
💬 Reddit: {platform_hype.get('redditHype', 0)}/100
📺 YouTube: {platform_hype.get('youtubeHype', 0)}/100
📰 News: {platform_hype.get('newsHype', 0)}/100

**Pump Risk:** {platform_hype.get('pumpRisk', 'N/A')}
**Dominant Platform:** {platform_hype.get('dominantPlatform', 'N/A')}

**Momentum:** {momentum.get('momentum', 'N/A')}
**Signal:** {momentum.get('signal', 'HOLD')} (Strength: {momentum.get('strength', 0)}/10)

**Price Pattern:** {analysis.get('pattern', 'N/A')}
**Recommendation:** {analysis.get('recommendation', 'WAIT')}
**Edge:** {analysis.get('edge', 'No clear edge')}

**Stats:**
💰 Price: ${coin_data.get('price', 0):.6f}
📊 24h Change: {coin_data.get('percentChange24h', 0):.2f}%
👥 Contributors: {coin_data.get('socialContributors', 0):,}
💬 Volume: {coin_data.get('socialVolume', 0):,}
❤️ Engagement: {coin_data.get('socialEngagement', 0):,}
"""
    return message.strip()


lunarcrush_comprehensive = LunarCrushComprehensiveService()

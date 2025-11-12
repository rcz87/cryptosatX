"""
LunarCrush Comprehensive Service
Maximizes LunarCrush API subscription with advanced social sentiment metrics
Includes: Full coin metrics, time-series analysis, change detection, influencer data
"""
import os
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta


class LunarCrushComprehensiveService:
    """
    Comprehensive LunarCrush API v4 service
    Provides social sentiment, engagement, and trend analysis
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
        Endpoint: /coins/{symbol}/v1
        
        Note: Individual coin lookups use /v1 (only /list endpoints have /v2)
        With paid API tier, this provides current data.
        
        Returns 60+ metrics including:
        - Galaxy Score™, AltRank™
        - Social volume, engagement, dominance
        - Average sentiment (1-5 scale)
        - Tweet/Reddit volumes
        - URL shares, correlation rank
        - Price, volume, market cap
        """
        try:
            client = await self._get_client()
            symbol = symbol.upper()
            url = f"{self.base_url}/coins/{symbol}/v1"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                coin_data = data["data"]
                
                return {
                    "success": True,
                    "symbol": symbol,
                    
                    # Proprietary Scores
                    "galaxyScore": float(coin_data.get("galaxy_score", 0)),
                    "altRank": int(coin_data.get("alt_rank", 0)),
                    
                    # Social Metrics
                    "socialVolume": int(coin_data.get("social_volume", 0)),
                    "socialEngagement": int(coin_data.get("social_engagement", 0)),
                    "socialDominance": float(coin_data.get("social_dominance", 0)),
                    "socialContributors": int(coin_data.get("social_contributors", 0)),
                    
                    # Sentiment Analysis
                    "averageSentiment": float(coin_data.get("average_sentiment", 0)),
                    "sentimentAbsolute": float(coin_data.get("sentiment_absolute", 0)),
                    
                    # Platform-specific Volumes
                    "tweetVolume": int(coin_data.get("tweets", 0)),
                    "redditVolume": int(coin_data.get("reddit_posts", 0)),
                    "urlShares": int(coin_data.get("url_shares", 0)),
                    
                    # Correlation & Quality
                    "correlationRank": float(coin_data.get("correlation_rank", 0)),
                    "spamDetected": int(coin_data.get("spam", 0)),
                    
                    # Market Data
                    "price": float(coin_data.get("price", 0)),
                    "priceUsd": float(coin_data.get("price_usd", 0)),
                    "volume24h": float(coin_data.get("volume_24h", 0)),
                    "marketCap": float(coin_data.get("market_cap", 0)),
                    "percentChange24h": float(coin_data.get("percent_change_24h", 0)),
                    "percentChange7d": float(coin_data.get("percent_change_7d", 0)),
                    
                    # Volatility
                    "volatility": float(coin_data.get("volatility", 0)),
                    
                    # Categories
                    "categories": coin_data.get("categories", []),
                    
                    # Metadata
                    "name": coin_data.get("name", ""),
                    "timeFetched": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_comprehensive"
                }
            
            return {"success": False, "error": "No data returned from API"}
            
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
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
            symbol = symbol.upper()
            
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
    
    async def get_social_change(self, symbol: str, timeframe: str = "24h") -> Dict:
        """
        Get social metrics change/delta over time period
        Endpoint: /coins/{symbol}/change
        
        Args:
            symbol: Coin symbol
            timeframe: Time period (1h, 24h, 7d)
            
        Returns:
            Change metrics including:
            - Social volume % change
            - Sentiment shift
            - Galaxy Score delta
            - Engagement change
            
        Use case: Detect sudden social spikes (300%+ increase alerts)
        """
        try:
            client = await self._get_client()
            symbol = symbol.upper()
            
            url = f"{self.base_url}/coins/{symbol}/change"
            params = {"interval": timeframe}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                raw_data = data["data"]
                
                # Handle both dict and list responses from API
                if isinstance(raw_data, list):
                    if len(raw_data) == 0:
                        return {"success": False, "error": "Empty data array"}
                    change_data = raw_data[0]  # Take first element if list
                else:
                    change_data = raw_data  # Use directly if dict
                
                social_vol_change = float(change_data.get("social_volume_change", 0))
                engagement_change = float(change_data.get("social_engagement_change", 0))
                sentiment_change = float(change_data.get("sentiment_change", 0))
                
                # Classify spike intensity
                spike_level = "normal"
                if abs(social_vol_change) > 300:
                    spike_level = "extreme"
                elif abs(social_vol_change) > 100:
                    spike_level = "high"
                elif abs(social_vol_change) > 50:
                    spike_level = "moderate"
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    
                    # Change Metrics
                    "socialVolumeChange": social_vol_change,
                    "socialEngagementChange": engagement_change,
                    "sentimentChange": sentiment_change,
                    "galaxyScoreChange": float(change_data.get("galaxy_score_change", 0)),
                    "priceChange": float(change_data.get("price_change", 0)),
                    
                    # Analysis
                    "spikeLevel": spike_level,
                    "isSpiking": abs(social_vol_change) > 50,
                    
                    "rawData": change_data,
                    "source": "lunarcrush_change"
                }
            
            return {"success": False, "error": "No change data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
            if change_24h.get("success"):
                vol_change = change_24h.get("socialVolumeChange", 0)
                if vol_change > 0:
                    momentum_score += min(vol_change / 10, 20)  # Cap at +20
                else:
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
    
    # ==================== TOPICS API (NARRATIVE DETECTION) ====================
    
    async def get_trending_topics(self, limit: int = 20, sort: str = "social_volume") -> Dict:
        """
        Get trending cryptocurrency topics/narratives
        Endpoint: /topics/list/v1
        
        Args:
            limit: Number of topics to return (default 20)
            sort: Sort by social_volume, engagement, or sentiment
            
        Returns:
            List of trending topics with:
            - Topic name and slug
            - Social volume, engagement
            - Sentiment, momentum
            - Related coins
            
        Use case: Detect emerging narratives before price pumps
        Examples: "AI Agents", "RWA", "DePIN", "Gaming", etc.
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/topics/list/v1"
            params = {
                "limit": limit,
                "sort": sort
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                topics = data["data"]
                
                # Extract key metrics
                parsed_topics = []
                for topic in topics:
                    parsed_topics.append({
                        "topic": topic.get("topic", ""),
                        "slug": topic.get("slug", ""),
                        "socialVolume": int(topic.get("social_volume", 0)),
                        "socialEngagement": int(topic.get("social_engagement", 0)),
                        "sentiment": float(topic.get("average_sentiment", 0)),
                        "posts24h": int(topic.get("posts_24h", 0)),
                        "change24h": float(topic.get("social_volume_change_24h", 0)),
                        "relatedCoins": topic.get("related_coins", [])[:5]  # Top 5 coins
                    })
                
                return {
                    "success": True,
                    "totalTopics": len(parsed_topics),
                    "topics": parsed_topics,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_topics"
                }
            
            return {"success": False, "error": "No topics data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_topic_details(self, topic_slug: str) -> Dict:
        """
        Get detailed information about a specific topic
        Endpoint: /topic/{topic}/v1
        
        Args:
            topic_slug: Topic identifier (e.g., "ai-agents", "real-world-assets")
            
        Returns:
            Comprehensive topic data including:
            - Social metrics and trends
            - Top related coins
            - Sentiment analysis
            - Momentum indicators
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/topic/{topic_slug}/v1"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                topic_data = data["data"]
                
                return {
                    "success": True,
                    "topic": topic_data.get("topic", ""),
                    "slug": topic_slug,
                    "socialVolume": int(topic_data.get("social_volume", 0)),
                    "socialEngagement": int(topic_data.get("social_engagement", 0)),
                    "sentiment": float(topic_data.get("average_sentiment", 0)),
                    "change24h": float(topic_data.get("social_volume_change_24h", 0)),
                    "change7d": float(topic_data.get("social_volume_change_7d", 0)),
                    "relatedCoins": topic_data.get("related_coins", []),
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_topic"
                }
            
            return {"success": False, "error": "No topic data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== CATEGORIES API (SECTOR ROTATION) ====================
    
    async def get_categories(self, limit: int = 30) -> Dict:
        """
        Get all cryptocurrency categories/sectors
        Endpoint: /categories/list/v1
        
        Returns:
            List of crypto sectors with performance metrics:
            - Layer-1, DeFi, NFT, Gaming, Meme, etc.
            - Social volume and sentiment per category
            - 24h/7d performance changes
            
        Use case: Sector rotation analysis, portfolio allocation
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/categories/list/v1"
            params = {"limit": limit}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                categories = data["data"]
                
                parsed_categories = []
                for cat in categories:
                    parsed_categories.append({
                        "category": cat.get("category", ""),
                        "slug": cat.get("slug", ""),
                        "coinCount": int(cat.get("num_coins", 0)),
                        "socialVolume": int(cat.get("social_volume", 0)),
                        "sentiment": float(cat.get("average_sentiment", 0)),
                        "change24h": float(cat.get("social_volume_change_24h", 0)),
                        "marketCap": float(cat.get("market_cap", 0))
                    })
                
                return {
                    "success": True,
                    "totalCategories": len(parsed_categories),
                    "categories": parsed_categories,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_categories"
                }
            
            return {"success": False, "error": "No categories data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_category_details(self, category_slug: str) -> Dict:
        """
        Get detailed category/sector performance
        Endpoint: /category/{category}/v1
        
        Args:
            category_slug: Category identifier (e.g., "layer-1", "defi", "meme")
            
        Returns:
            Category performance with top coins in sector
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/category/{category_slug}/v1"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                cat_data = data["data"]
                
                return {
                    "success": True,
                    "category": cat_data.get("category", ""),
                    "slug": category_slug,
                    "coinCount": int(cat_data.get("num_coins", 0)),
                    "socialVolume": int(cat_data.get("social_volume", 0)),
                    "sentiment": float(cat_data.get("average_sentiment", 0)),
                    "change24h": float(cat_data.get("social_volume_change_24h", 0)),
                    "topCoins": cat_data.get("top_coins", [])[:10],
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_category"
                }
            
            return {"success": False, "error": "No category data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== CREATORS/INFLUENCERS API ====================
    
    async def get_top_creators(self, limit: int = 50, sort: str = "followers") -> Dict:
        """
        Get top cryptocurrency influencers/creators
        Endpoint: /creators/list/v1
        
        Args:
            limit: Number of creators (default 50)
            sort: Sort by followers, engagement, or influence_score
            
        Returns:
            List of top crypto influencers with:
            - Creator name and network (twitter, youtube, etc.)
            - Follower count, engagement rate
            - Recent activity, sentiment
            - Top mentioned coins
            
        Use case: Track whale sentiment, early alpha signals
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/creators/list/v1"
            params = {
                "limit": limit,
                "sort": sort
            }
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                creators = data["data"]
                
                parsed_creators = []
                for creator in creators:
                    parsed_creators.append({
                        "name": creator.get("name", ""),
                        "username": creator.get("username", ""),
                        "network": creator.get("network", ""),
                        "followers": int(creator.get("followers", 0)),
                        "engagementRate": float(creator.get("engagement_rate", 0)),
                        "posts24h": int(creator.get("posts_24h", 0)),
                        "influenceScore": float(creator.get("influence_score", 0)),
                        "topMentions": creator.get("top_coins", [])[:5]
                    })
                
                return {
                    "success": True,
                    "totalCreators": len(parsed_creators),
                    "creators": parsed_creators,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_creators"
                }
            
            return {"success": False, "error": "No creators data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== COINS LIST V2 (REAL-TIME DISCOVERY) ====================
    
    async def get_coins_realtime(
        self, 
        limit: int = 100, 
        sort: str = "social_volume",
        min_galaxy_score: Optional[float] = None
    ) -> Dict:
        """
        Get real-time coin list (NO CACHE - instant data)
        Endpoint: /coins/list/v2
        
        Args:
            limit: Number of coins (default 100)
            sort: Sort by social_volume, galaxy_score, market_cap, volume_24h
            min_galaxy_score: Filter coins with Galaxy Score >= this value
            
        Returns:
            Real-time coin list with current social + market metrics
            
        Note: v2 endpoint provides LIVE data vs v1 (1-hour cache)
        Better for MSS scanning and real-time discovery
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
                        "change24h": float(coin.get("percent_change_24h", 0))
                    })
                
                return {
                    "success": True,
                    "totalCoins": len(parsed_coins),
                    "coins": parsed_coins,
                    "filters": {
                        "sort": sort,
                        "minGalaxyScore": min_galaxy_score
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_coins_v2_realtime"
                }
            
            return {"success": False, "error": "No coins data"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== AI INSIGHTS (AUTOMATED ANALYSIS) ====================
    
    async def get_ai_topic_insights(self, topic: str) -> Dict:
        """
        Get AI-generated insights about a topic
        Endpoint: /ai/topic/{topic}
        
        Args:
            topic: Topic to analyze (e.g., "bitcoin", "defi", "nft")
            
        Returns:
            AI-generated analysis including:
            - Topic summary and key trends
            - Sentiment analysis
            - Notable developments
            - Related opportunities
            
        Use case: Automated narrative analysis, market intelligence
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/ai/topic/{topic}"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("data"):
                ai_data = data["data"]
                
                return {
                    "success": True,
                    "topic": topic,
                    "summary": ai_data.get("summary", ""),
                    "insights": ai_data.get("insights", []),
                    "sentiment": ai_data.get("sentiment", ""),
                    "keyTrends": ai_data.get("key_trends", []),
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "lunarcrush_ai"
                }
            
            return {"success": False, "error": "No AI insights available"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== ADVANCED ANALYTICS ====================
    
    async def analyze_narrative_opportunities(self, top_n_topics: int = 10) -> Dict:
        """
        Advanced analysis: Find high-opportunity coins from trending narratives
        
        Combines:
        1. Trending topics detection
        2. Related coins extraction
        3. Galaxy Score filtering
        4. Momentum analysis
        
        Returns:
            High-probability trading opportunities based on narrative momentum
        """
        try:
            # Get trending topics
            topics_result = await self.get_trending_topics(limit=top_n_topics)
            
            if not topics_result.get("success"):
                return {"success": False, "error": "Failed to fetch topics"}
            
            opportunities = []
            
            for topic in topics_result.get("topics", []):
                # Filter for high-momentum topics
                if topic.get("change24h", 0) > 50:  # 50%+ social volume increase
                    related_coins = topic.get("relatedCoins", [])
                    
                    for coin in related_coins[:3]:  # Top 3 coins per topic
                        opportunities.append({
                            "symbol": coin,
                            "narrative": topic.get("topic", ""),
                            "narrativeMomentum": topic.get("change24h", 0),
                            "socialVolume": topic.get("socialVolume", 0),
                            "sentiment": topic.get("sentiment", 0)
                        })
            
            # Sort by narrative momentum
            opportunities.sort(key=lambda x: x.get("narrativeMomentum", 0), reverse=True)
            
            return {
                "success": True,
                "opportunitiesFound": len(opportunities),
                "opportunities": opportunities[:20],  # Top 20
                "timestamp": datetime.utcnow().isoformat(),
                "source": "lunarcrush_narrative_analysis"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def analyze_sector_rotation(self) -> Dict:
        """
        Sector rotation analysis
        
        Identifies:
        1. Heating sectors (increasing social momentum)
        2. Cooling sectors (decreasing momentum)
        3. Recommended sector allocation
        
        Returns:
            Sector rotation signals for portfolio rebalancing
        """
        try:
            categories_result = await self.get_categories(limit=20)
            
            if not categories_result.get("success"):
                return {"success": False, "error": "Failed to fetch categories"}
            
            heating = []
            cooling = []
            
            for cat in categories_result.get("categories", []):
                change_24h = cat.get("change24h", 0)
                
                if change_24h > 25:  # Heating up
                    heating.append({
                        "sector": cat.get("category", ""),
                        "momentum": change_24h,
                        "sentiment": cat.get("sentiment", 0),
                        "socialVolume": cat.get("socialVolume", 0)
                    })
                elif change_24h < -25:  # Cooling down
                    cooling.append({
                        "sector": cat.get("category", ""),
                        "momentum": change_24h,
                        "sentiment": cat.get("sentiment", 0),
                        "socialVolume": cat.get("socialVolume", 0)
                    })
            
            heating.sort(key=lambda x: x.get("momentum", 0), reverse=True)
            cooling.sort(key=lambda x: x.get("momentum", 0))
            
            return {
                "success": True,
                "heatingSectors": heating,
                "coolingSectors": cooling,
                "signal": "rotate_to_heating" if len(heating) > 0 else "hold",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "lunarcrush_sector_rotation"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance for easy import
lunarcrush_comprehensive = LunarCrushComprehensiveService()

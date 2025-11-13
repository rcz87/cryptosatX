"""
LunarCrush Comprehensive Service (Builder Tier Optimized)
Maximizes LunarCrush Builder API subscription
Available features: Coin metrics, time-series, change detection, real-time discovery
"""
import os
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta


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
                    "percentChange1h": float(coin_data.get("percent_change_1h", 0)),
                    
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
            symbol = symbol.upper()
            
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
lunarcrush_comprehensive = LunarCrushComprehensiveService()

"""
Enhanced Signal Engine
Combines data from multiple sources to generate advanced trading signals
Uses premium Coinglass endpoints and weighted scoring system
"""
import asyncio
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict

from app.services.coinapi_service import coinapi_service
from app.services.coinapi_comprehensive_service import coinapi_comprehensive
from app.services.coinglass_service import coinglass_service
from app.services.coinglass_premium_service import coinglass_premium
from app.services.coinglass_comprehensive_service import coinglass_comprehensive
from app.services.lunarcrush_service import lunarcrush_service
from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
from app.services.okx_service import okx_service


@dataclass
class EnhancedSignalContext:
    """Structured container for all market metrics"""
    # Basic metrics
    symbol: str
    price: float
    funding_rate: float
    open_interest: float
    social_score: float
    price_trend: str
    
    # Comprehensive Coinglass metrics
    funding_rate_oi_weighted: float = 0.0
    funding_rate_vol_weighted: float = 0.0
    oi_market_cap_ratio: float = 0.0
    oi_volume_ratio: float = 0.0
    price_change_5m: float = 0.0
    price_change_15m: float = 0.0
    price_change_1h: float = 0.0
    price_change_4h: float = 0.0
    price_change_24h: float = 0.0
    multi_timeframe_trend: str = "neutral"
    
    # Premium metrics
    long_liquidations: float = 0.0
    short_liquidations: float = 0.0
    liquidation_imbalance: str = "unknown"
    
    long_account_pct: float = 50.0
    short_account_pct: float = 50.0
    ls_sentiment: str = "neutral"
    
    oi_change_pct: float = 0.0
    oi_trend: str = "unknown"
    
    top_trader_long_pct: float = 50.0
    smart_money_bias: str = "neutral"
    
    fear_greed_value: int = 50
    fear_greed_sentiment: str = "neutral"
    
    # Comprehensive LunarCrush metrics
    alt_rank: int = 0
    social_volume: int = 0
    social_engagement: int = 0
    social_dominance: float = 0.0
    average_sentiment: float = 3.0
    tweet_volume: int = 0
    reddit_volume: int = 0
    url_shares: int = 0
    correlation_rank: float = 0.0
    social_volume_change_24h: float = 0.0
    social_spike_level: str = "normal"
    social_momentum_score: float = 50.0
    social_momentum_level: str = "neutral"
    
    # CoinAPI Comprehensive metrics
    orderbook_imbalance: float = 0.0  # -100 to +100: negative=sell pressure, positive=buy pressure
    spread_percent: float = 0.0
    whale_bids_count: int = 0
    whale_asks_count: int = 0
    buy_pressure_pct: float = 50.0  # From recent trades
    sell_pressure_pct: float = 50.0
    avg_trade_size: float = 0.0
    volatility_7d: float = 0.0
    
    # Data quality flags
    premium_data_available: bool = False
    comprehensive_data_available: bool = False
    lunarcrush_comprehensive_available: bool = False
    coinapi_comprehensive_available: bool = False
    

class SignalEngine:
    """
    Enhanced trading signal engine with premium data integration
    Features:
    - Concurrent data fetching for speed
    - Weighted scoring system (0-100)
    - Multi-factor analysis
    - Smart money tracking
    """
    
    # Scoring weights (total = 100)
    WEIGHTS = {
        "funding_rate": 15,
        "social_sentiment": 10,
        "price_momentum": 15,
        "liquidations": 20,
        "long_short_ratio": 15,
        "oi_trend": 10,
        "smart_money": 10,
        "fear_greed": 5
    }
    
    async def build_signal(self, symbol: str, debug: bool = False) -> Dict:
        """
        Build enhanced trading signal using all data sources concurrently
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            debug: If True, include all raw metrics in response
            
        Returns:
            Dict with signal, score, and comprehensive analysis
        """
        symbol = symbol.upper()
        
        # PHASE 1: Concurrent data collection
        context = await self._collect_market_data(symbol)
        
        # PHASE 2: Calculate weighted score
        score, breakdown = self._calculate_weighted_score(context)
        
        # PHASE 3: Generate signal and reasoning
        signal = self._determine_signal(score)
        top_reasons = self._generate_top_reasons(breakdown, context)
        
        # Build response
        response = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "signal": signal,
            "score": round(score, 1),  # 0-100
            "confidence": self._calculate_confidence(breakdown),
            "price": context.price,
            "reasons": top_reasons,
            "metrics": {
                "fundingRate": context.funding_rate,
                "openInterest": context.open_interest,
                "socialScore": context.social_score,
                "priceTrend": context.price_trend
            }
        }
        
        # Add comprehensive Coinglass metrics if available
        if context.comprehensive_data_available:
            response["comprehensiveMetrics"] = {
                "multiTimeframeTrend": context.multi_timeframe_trend,
                "priceChanges": {
                    "5m": context.price_change_5m,
                    "15m": context.price_change_15m,
                    "1h": context.price_change_1h,
                    "4h": context.price_change_4h,
                    "24h": context.price_change_24h
                },
                "advancedRatios": {
                    "oiMarketCapRatio": context.oi_market_cap_ratio,
                    "oiVolumeRatio": context.oi_volume_ratio
                },
                "fundingRates": {
                    "oiWeighted": context.funding_rate_oi_weighted,
                    "volumeWeighted": context.funding_rate_vol_weighted
                }
            }
        
        # Add comprehensive LunarCrush metrics if available
        if context.lunarcrush_comprehensive_available:
            response["lunarCrushMetrics"] = {
                "altRank": context.alt_rank,
                "socialMetrics": {
                    "volume": context.social_volume,
                    "engagement": context.social_engagement,
                    "dominance": context.social_dominance,
                    "tweetVolume": context.tweet_volume,
                    "redditVolume": context.reddit_volume,
                    "urlShares": context.url_shares
                },
                "sentiment": {
                    "averageSentiment": context.average_sentiment,
                    "correlationRank": context.correlation_rank
                },
                "momentum": {
                    "momentumScore": context.social_momentum_score,
                    "momentumLevel": context.social_momentum_level,
                    "volumeChange24h": context.social_volume_change_24h,
                    "spikeLevel": context.social_spike_level
                }
            }
        
        # Add CoinAPI comprehensive metrics if available
        if context.coinapi_comprehensive_available:
            response["coinAPIMetrics"] = {
                "orderbook": {
                    "imbalance": context.orderbook_imbalance,  # -100 to +100
                    "spreadPercent": context.spread_percent,
                    "whaleBids": context.whale_bids_count,
                    "whaleAsks": context.whale_asks_count
                },
                "trades": {
                    "buyPressure": context.buy_pressure_pct,
                    "sellPressure": context.sell_pressure_pct,
                    "avgTradeSize": context.avg_trade_size
                },
                "volatility7d": context.volatility_7d
            }
        
        # Add premium metrics if available
        if context.premium_data_available:
            response["premiumMetrics"] = {
                "liquidationImbalance": context.liquidation_imbalance,
                "longShortSentiment": context.ls_sentiment,
                "oiTrend": context.oi_trend,
                "smartMoneyBias": context.smart_money_bias,
                "fearGreedIndex": context.fear_greed_value
            }
        
        # Debug mode: include all raw data
        if debug:
            response["debug"] = {
                "scoreBreakdown": breakdown,
                "allMetrics": asdict(context)
            }
        
        return response
    
    async def _collect_market_data(self, symbol: str) -> EnhancedSignalContext:
        """
        Fetch all market data concurrently using asyncio.gather
        """
        # Fetch all data sources in parallel
        results = await asyncio.gather(
            coinapi_service.get_spot_price(symbol),
            coinglass_service.get_funding_and_oi(symbol),
            coinglass_comprehensive.get_coins_markets(symbol=symbol),  # Comprehensive markets
            lunarcrush_service.get_social_score(symbol),  # Basic social score
            lunarcrush_comprehensive.get_coin_comprehensive(symbol),  # Comprehensive LunarCrush
            lunarcrush_comprehensive.get_social_change(symbol, "24h"),  # 24h change detection
            lunarcrush_comprehensive.analyze_social_momentum(symbol),  # Social momentum analysis
            okx_service.get_candles(symbol, "15m", 20),
            # Premium endpoints
            coinglass_premium.get_liquidation_data(symbol),
            coinglass_premium.get_long_short_ratio(symbol),
            coinglass_premium.get_oi_trend(symbol),
            coinglass_premium.get_top_trader_ratio(symbol),
            coinglass_premium.get_fear_greed_index(),
            # CoinAPI comprehensive endpoints
            coinapi_comprehensive.get_orderbook_depth(symbol, "BINANCE", 20),
            coinapi_comprehensive.get_recent_trades(symbol, "BINANCE", 100),
            coinapi_comprehensive.get_ohlcv_historical(symbol, "1DAY", 7, "BINANCE"),
            return_exceptions=True  # Don't fail if one endpoint fails
        )
        
        # Unpack results
        price_data, cg_data, comp_markets, social_data, lc_comp, lc_change, lc_momentum, candles_data, liq_data, ls_data, oi_trend_data, trader_data, fg_data, ca_orderbook, ca_trades, ca_ohlcv = results
        
        # Handle potential exceptions
        price_data = price_data if not isinstance(price_data, Exception) else {}
        cg_data = cg_data if not isinstance(cg_data, Exception) else {}
        comp_markets = comp_markets if not isinstance(comp_markets, Exception) else {}
        social_data = social_data if not isinstance(social_data, Exception) else {}
        lc_comp = lc_comp if not isinstance(lc_comp, Exception) else {}
        lc_change = lc_change if not isinstance(lc_change, Exception) else {}
        lc_momentum = lc_momentum if not isinstance(lc_momentum, Exception) else {}
        candles_data = candles_data if not isinstance(candles_data, Exception) else {}
        liq_data = liq_data if not isinstance(liq_data, Exception) else {}
        ls_data = ls_data if not isinstance(ls_data, Exception) else {}
        oi_trend_data = oi_trend_data if not isinstance(oi_trend_data, Exception) else {}
        trader_data = trader_data if not isinstance(trader_data, Exception) else {}
        fg_data = fg_data if not isinstance(fg_data, Exception) else {}
        ca_orderbook = ca_orderbook if not isinstance(ca_orderbook, Exception) else {}
        ca_trades = ca_trades if not isinstance(ca_trades, Exception) else {}
        ca_ohlcv = ca_ohlcv if not isinstance(ca_ohlcv, Exception) else {}
        
        # Calculate price trend from OKX candles
        price_trend = self._calculate_price_trend(candles_data.get("candles", []))
        
        # Calculate multi-timeframe trend from comprehensive markets data
        multi_tf_trend = self._calculate_multi_timeframe_trend(comp_markets)
        
        # Build context
        premium_available = (
            liq_data.get("success", False) and
            ls_data.get("success", False) and
            oi_trend_data.get("success", False)
        )
        
        comprehensive_available = comp_markets.get("success", False)
        lunarcrush_comp_available = lc_comp.get("success", False)
        # CoinAPI: Accept if any endpoint succeeds (not requiring all)
        coinapi_comp_available = (
            ca_orderbook.get("success", False) or
            ca_trades.get("success", False) or
            ca_ohlcv.get("success", False)
        )
        
        # Log comprehensive data availability
        if not comprehensive_available:
            error_msg = comp_markets.get("error", "unknown error")
            print(f"⚠️  Comprehensive markets data unavailable for {symbol}: {error_msg}. Falling back to basic Coinglass data.")
        
        if not lunarcrush_comp_available:
            error_msg = lc_comp.get("error", "unknown error")
            print(f"⚠️  Comprehensive LunarCrush data unavailable for {symbol}: {error_msg}. Falling back to basic social score.")
        
        if not coinapi_comp_available:
            print(f"⚠️  CoinAPI comprehensive data unavailable for {symbol}. Order book/trades analysis will use defaults.")
        
        # Prefer comprehensive markets data for funding/OI if available, fallback to basic
        funding = comp_markets.get("fundingRateByOI", cg_data.get("fundingRate", 0.0)) if comprehensive_available else cg_data.get("fundingRate", 0.0)
        oi = comp_markets.get("openInterestUsd", cg_data.get("openInterest", 0.0)) if comprehensive_available else cg_data.get("openInterest", 0.0)
        
        return EnhancedSignalContext(
            symbol=symbol,
            price=comp_markets.get("price", price_data.get("price", 0.0)) if comprehensive_available else price_data.get("price", 0.0),
            funding_rate=funding,
            open_interest=oi,
            social_score=social_data.get("socialScore", 50.0),
            price_trend=price_trend,
            # Comprehensive Coinglass data
            funding_rate_oi_weighted=comp_markets.get("fundingRateByOI", 0.0),
            funding_rate_vol_weighted=comp_markets.get("fundingRateByVol", 0.0),
            oi_market_cap_ratio=comp_markets.get("oiMarketCapRatio", 0.0),
            oi_volume_ratio=comp_markets.get("oiVolumeRatio", 0.0),
            price_change_5m=comp_markets.get("priceChange5m", 0.0),
            price_change_15m=comp_markets.get("priceChange15m", 0.0),
            price_change_1h=comp_markets.get("priceChange1h", 0.0),
            price_change_4h=comp_markets.get("priceChange4h", 0.0),
            price_change_24h=comp_markets.get("priceChange24h", 0.0),
            multi_timeframe_trend=multi_tf_trend,
            # Premium data
            long_liquidations=liq_data.get("longLiquidations", 0.0),
            short_liquidations=liq_data.get("shortLiquidations", 0.0),
            liquidation_imbalance=liq_data.get("imbalance", "unknown"),
            long_account_pct=ls_data.get("longAccountPct", 50.0),
            short_account_pct=ls_data.get("shortAccountPct", 50.0),
            ls_sentiment=ls_data.get("sentiment", "neutral"),
            oi_change_pct=oi_trend_data.get("oiChangePct", 0.0),
            oi_trend=oi_trend_data.get("trend", "unknown"),
            top_trader_long_pct=trader_data.get("topTraderLongPct", 50.0),
            smart_money_bias=trader_data.get("smartMoneyBias", "neutral"),
            fear_greed_value=fg_data.get("value", 50),
            fear_greed_sentiment=fg_data.get("sentiment", "neutral"),
            # Comprehensive LunarCrush data
            alt_rank=lc_comp.get("altRank", 0),
            social_volume=lc_comp.get("socialVolume", 0),
            social_engagement=lc_comp.get("socialEngagement", 0),
            social_dominance=lc_comp.get("socialDominance", 0.0),
            average_sentiment=lc_comp.get("averageSentiment", 3.0),
            tweet_volume=lc_comp.get("tweetVolume", 0),
            reddit_volume=lc_comp.get("redditVolume", 0),
            url_shares=lc_comp.get("urlShares", 0),
            correlation_rank=lc_comp.get("correlationRank", 0.0),
            social_volume_change_24h=lc_change.get("socialVolumeChange", 0.0),
            social_spike_level=lc_change.get("spikeLevel", "normal"),
            social_momentum_score=lc_momentum.get("momentumScore", 50.0),
            social_momentum_level=lc_momentum.get("momentumLevel", "neutral"),
            # CoinAPI Comprehensive data
            orderbook_imbalance=ca_orderbook.get("metrics", {}).get("imbalance", 0.0) if coinapi_comp_available else 0.0,
            spread_percent=ca_orderbook.get("spread", {}).get("spreadPercent", 0.0) if coinapi_comp_available else 0.0,
            whale_bids_count=ca_orderbook.get("whaleWalls", {}).get("largeBids", 0) if coinapi_comp_available else 0,
            whale_asks_count=ca_orderbook.get("whaleWalls", {}).get("largeAsks", 0) if coinapi_comp_available else 0,
            buy_pressure_pct=ca_trades.get("volume", {}).get("buyPressure", 50.0) if coinapi_comp_available else 50.0,
            sell_pressure_pct=ca_trades.get("volume", {}).get("sellPressure", 50.0) if coinapi_comp_available else 50.0,
            avg_trade_size=ca_trades.get("volume", {}).get("avgTradeSize", 0.0) if coinapi_comp_available else 0.0,
            volatility_7d=ca_ohlcv.get("analysis", {}).get("volatility", 0.0) if ca_ohlcv.get("success", False) else 0.0,
            # Data quality flags
            premium_data_available=premium_available,
            comprehensive_data_available=comprehensive_available,
            lunarcrush_comprehensive_available=lunarcrush_comp_available,
            coinapi_comprehensive_available=coinapi_comp_available
        )
    
    def _calculate_price_trend(self, candles: list) -> str:
        """
        Calculate simple price trend from candle data
        
        Args:
            candles: List of OHLCV candle data
            
        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        if not candles or len(candles) < 5:
            return "neutral"
        
        try:
            # Get recent candles (most recent first in OKX)
            recent = candles[:5]
            
            # Compare current price with average of last 5 candles
            current_close = recent[0]["close"]
            avg_close = sum(c["close"] for c in recent) / len(recent)
            
            # Calculate percentage difference
            diff_pct = ((current_close - avg_close) / avg_close) * 100
            
            if diff_pct > 0.5:
                return "bullish"
            elif diff_pct < -0.5:
                return "bearish"
            else:
                return "neutral"
        except Exception as e:
            print(f"Error calculating price trend: {e}")
            return "neutral"
    
    def _calculate_multi_timeframe_trend(self, comp_markets: dict) -> str:
        """
        Calculate overall trend from 7 timeframes (5m to 24h)
        
        Args:
            comp_markets: Comprehensive markets data with price changes
            
        Returns:
            'strongly_bullish', 'bullish', 'neutral', 'bearish', or 'strongly_bearish'
        """
        if not comp_markets.get("success", False):
            return "neutral"
        
        try:
            # Get all timeframe changes
            changes = {
                '5m': comp_markets.get("priceChange5m", 0.0),
                '15m': comp_markets.get("priceChange15m", 0.0),
                '30m': comp_markets.get("priceChange30m", 0.0),
                '1h': comp_markets.get("priceChange1h", 0.0),
                '4h': comp_markets.get("priceChange4h", 0.0),
                '12h': comp_markets.get("priceChange12h", 0.0),
                '24h': comp_markets.get("priceChange24h", 0.0)
            }
            
            # Count bullish vs bearish timeframes
            bullish_count = sum(1 for change in changes.values() if change > 0)
            bearish_count = sum(1 for change in changes.values() if change < 0)
            
            # Weighted score (longer timeframes = more weight)
            weights = {'5m': 1, '15m': 1, '30m': 1, '1h': 2, '4h': 3, '12h': 4, '24h': 5}
            weighted_sum = sum(changes[tf] * weights[tf] for tf in changes)
            total_weight = sum(weights.values())
            avg_weighted_change = weighted_sum / total_weight if total_weight > 0 else 0
            
            # Determine trend strength
            if bullish_count >= 6 and avg_weighted_change > 1.0:
                return "strongly_bullish"
            elif bullish_count >= 5:
                return "bullish"
            elif bearish_count >= 6 and avg_weighted_change < -1.0:
                return "strongly_bearish"
            elif bearish_count >= 5:
                return "bearish"
            else:
                return "neutral"
        except Exception as e:
            print(f"Error calculating multi-timeframe trend: {e}")
            return "neutral"
    
    def _calculate_weighted_score(self, context: EnhancedSignalContext) -> tuple[float, Dict]:
        """
        Calculate weighted score (0-100) from all metrics
        
        Returns:
            Tuple of (total_score, score_breakdown)
        """
        breakdown = {}
        
        # 1. Funding Rate Score (15%)
        funding_score = self._score_funding_rate(context.funding_rate)
        breakdown["funding_rate"] = {
            "score": funding_score,
            "weight": self.WEIGHTS["funding_rate"],
            "weighted": funding_score * self.WEIGHTS["funding_rate"] / 100
        }
        
        # 2. Social Sentiment Score (10%)
        social_score = context.social_score  # Already 0-100
        breakdown["social_sentiment"] = {
            "score": social_score,
            "weight": self.WEIGHTS["social_sentiment"],
            "weighted": social_score * self.WEIGHTS["social_sentiment"] / 100
        }
        
        # 3. Price Momentum Score (15%)
        momentum_score = self._score_price_momentum(context.price_trend)
        breakdown["price_momentum"] = {
            "score": momentum_score,
            "weight": self.WEIGHTS["price_momentum"],
            "weighted": momentum_score * self.WEIGHTS["price_momentum"] / 100
        }
        
        # 4. Liquidation Score (20%)
        liq_score = self._score_liquidations(context)
        breakdown["liquidations"] = {
            "score": liq_score,
            "weight": self.WEIGHTS["liquidations"],
            "weighted": liq_score * self.WEIGHTS["liquidations"] / 100
        }
        
        # 5. Long/Short Ratio Score (15%)
        ls_score = self._score_long_short_ratio(context.long_account_pct)
        breakdown["long_short_ratio"] = {
            "score": ls_score,
            "weight": self.WEIGHTS["long_short_ratio"],
            "weighted": ls_score * self.WEIGHTS["long_short_ratio"] / 100
        }
        
        # 6. OI Trend Score (10%)
        oi_score = self._score_oi_trend(context.oi_change_pct)
        breakdown["oi_trend"] = {
            "score": oi_score,
            "weight": self.WEIGHTS["oi_trend"],
            "weighted": oi_score * self.WEIGHTS["oi_trend"] / 100
        }
        
        # 7. Smart Money Score (10%)
        smart_score = self._score_smart_money(context.top_trader_long_pct)
        breakdown["smart_money"] = {
            "score": smart_score,
            "weight": self.WEIGHTS["smart_money"],
            "weighted": smart_score * self.WEIGHTS["smart_money"] / 100
        }
        
        # 8. Fear & Greed Score (5%)
        fg_score = context.fear_greed_value  # Already 0-100
        breakdown["fear_greed"] = {
            "score": fg_score,
            "weight": self.WEIGHTS["fear_greed"],
            "weighted": fg_score * self.WEIGHTS["fear_greed"] / 100
        }
        
        # Calculate total weighted score
        total_score = sum(item["weighted"] for item in breakdown.values())
        
        return total_score, breakdown
    
    def _score_funding_rate(self, rate: float) -> float:
        """
        Score funding rate on 0-100 scale
        Negative funding = bullish (shorts pay longs) = high score
        Positive funding = bearish (longs pay shorts) = low score
        """
        # Normalize to percentage
        rate_pct = rate * 100
        
        if rate_pct < -0.2:  # Very negative = very bullish
            return 85
        elif rate_pct < -0.05:
            return 70
        elif rate_pct < 0:
            return 60
        elif rate_pct < 0.05:
            return 45
        elif rate_pct < 0.2:
            return 30
        else:  # > 0.2% = very bearish
            return 15
    
    def _score_price_momentum(self, trend: str) -> float:
        """Score price momentum based on trend"""
        if trend == "bullish":
            return 75
        elif trend == "bearish":
            return 25
        else:
            return 50
    
    def _score_liquidations(self, context: EnhancedSignalContext) -> float:
        """
        Score based on liquidation imbalance
        More longs liquidated = bearish pressure cleared = bullish
        """
        if not context.premium_data_available:
            return 50  # Neutral if no data
        
        if context.liquidation_imbalance == "long":
            # Longs getting liquidated = potential reversal up
            return 65
        elif context.liquidation_imbalance == "short":
            # Shorts getting liquidated = potential reversal down
            return 35
        else:
            return 50
    
    def _score_long_short_ratio(self, long_pct: float) -> float:
        """
        Score based on long/short ratio (contrarian indicator)
        Too many longs = bearish, too many shorts = bullish
        """
        if long_pct > 65:  # Overcrowded longs = bearish
            return 25
        elif long_pct > 55:
            return 40
        elif long_pct < 35:  # Overcrowded shorts = bullish
            return 75
        elif long_pct < 45:
            return 60
        else:
            return 50
    
    def _score_oi_trend(self, change_pct: float) -> float:
        """
        Score based on OI change
        Rising OI = confirmation of trend
        """
        if change_pct > 5:  # Strong increase
            return 70
        elif change_pct > 1:
            return 60
        elif change_pct < -5:  # Strong decrease
            return 30
        elif change_pct < -1:
            return 40
        else:
            return 50
    
    def _score_smart_money(self, top_trader_long_pct: float) -> float:
        """
        Score based on what smart money is doing
        Follow the whales
        """
        if top_trader_long_pct > 60:
            return 70
        elif top_trader_long_pct > 52:
            return 60
        elif top_trader_long_pct < 40:
            return 30
        elif top_trader_long_pct < 48:
            return 40
        else:
            return 50
    
    def _determine_signal(self, score: float) -> str:
        """
        Determine LONG/SHORT/NEUTRAL based on score
        
        Score ranges (ADJUSTED FOR HIGHER SENSITIVITY):
        - 0-45: SHORT
        - 45-55: NEUTRAL
        - 55-100: LONG
        """
        if score >= 55:
            return "LONG"
        elif score <= 45:
            return "SHORT"
        else:
            return "NEUTRAL"
    
    def _calculate_confidence(self, breakdown: Dict) -> str:
        """
        Calculate confidence level based on score distribution
        """
        weighted_scores = [item["weighted"] for item in breakdown.values()]
        avg_score = sum(weighted_scores) / len(weighted_scores)
        
        # Check if scores are aligned or divergent
        variance = sum((s - avg_score) ** 2 for s in weighted_scores) / len(weighted_scores)
        
        if variance < 5:
            return "high"
        elif variance < 15:
            return "medium"
        else:
            return "low"
    
    def _generate_top_reasons(self, breakdown: Dict, context: EnhancedSignalContext) -> List[str]:
        """
        Generate top 3 reasons for the signal based on highest weighted contributions
        """
        reasons = []
        
        # Sort by weighted score contribution
        sorted_factors = sorted(
            breakdown.items(),
            key=lambda x: abs(x[1]["weighted"] - 50),  # Distance from neutral
            reverse=True
        )
        
        # Generate human-readable reasons for top 3 factors
        for factor_name, factor_data in sorted_factors[:3]:
            score = factor_data["score"]
            
            if factor_name == "liquidations":
                if context.liquidation_imbalance == "long":
                    reasons.append(f"Heavy long liquidations (${context.long_liquidations/1e6:.1f}M) - bearish pressure clearing")
                elif context.liquidation_imbalance == "short":
                    reasons.append(f"Heavy short liquidations (${context.short_liquidations/1e6:.1f}M) - bullish pressure clearing")
            
            elif factor_name == "long_short_ratio":
                if context.long_account_pct > 60:
                    reasons.append(f"Overcrowded longs ({context.long_account_pct:.1f}%) - contrarian bearish")
                elif context.long_account_pct < 40:
                    reasons.append(f"Overcrowded shorts ({context.short_account_pct:.1f}%) - contrarian bullish")
            
            elif factor_name == "smart_money":
                if context.top_trader_long_pct > 55:
                    reasons.append(f"Smart money long-biased ({context.top_trader_long_pct:.1f}%)")
                elif context.top_trader_long_pct < 45:
                    reasons.append(f"Smart money short-biased ({context.top_trader_long_pct:.1f}%)")
            
            elif factor_name == "oi_trend":
                if context.oi_change_pct > 3:
                    reasons.append(f"OI rising strongly (+{context.oi_change_pct:.1f}%) - trend confirmation")
                elif context.oi_change_pct < -3:
                    reasons.append(f"OI falling ({context.oi_change_pct:.1f}%) - trend weakening")
            
            elif factor_name == "funding_rate":
                rate_pct = context.funding_rate * 100
                if rate_pct > 0.1:
                    reasons.append(f"High funding rate ({rate_pct:.3f}%) - longs overleveraged")
                elif rate_pct < -0.1:
                    reasons.append(f"Negative funding ({rate_pct:.3f}%) - shorts overleveraged")
            
            elif factor_name == "fear_greed":
                if context.fear_greed_value < 25:
                    reasons.append(f"Extreme fear ({context.fear_greed_value}/100) - buy opportunity")
                elif context.fear_greed_value > 75:
                    reasons.append(f"Extreme greed ({context.fear_greed_value}/100) - sell signal")
        
        # If we don't have 3 reasons yet, add basic ones
        if len(reasons) < 3:
            reasons.append(f"Price trend: {context.price_trend}")
            reasons.append(f"Social sentiment: {context.social_score:.0f}/100")
        
        return reasons[:3]  # Return top 3


# Singleton instance
signal_engine = SignalEngine()

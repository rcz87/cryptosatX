"""
Enhanced Signal Engine
Combines data from multiple sources to generate advanced trading signals
Uses premium Coinglass endpoints and weighted scoring system
"""

import os
import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

from app.services.coinapi_service import coinapi_service
from app.services.coinapi_comprehensive_service import coinapi_comprehensive
from app.services.coinglass_service import coinglass_service
from app.services.coinglass_premium_service import coinglass_premium
from app.services.coinglass_comprehensive_service import coinglass_comprehensive
from app.services.lunarcrush_service import lunarcrush_service
from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
from app.services.okx_service import okx_service
from app.services.telegram_notifier import telegram_notifier
from app.services.openai_service_v2 import get_openai_service_v2
from app.services.position_sizer import position_sizer
from app.utils import risk_rules
from app.utils.logger import get_logger

# Initialize module logger
logger = get_logger(__name__)


# ============================================================================
# SERVICE TRACKING & QUALITY MONITORING
# ============================================================================

class ServiceTier(Enum):
    """Service priority tiers for quality calculation"""
    CRITICAL = "critical"    # Must have for valid signal (price, funding, basic social)
    IMPORTANT = "important"  # Should have for good signal (liquidations, LS ratio, candles)
    OPTIONAL = "optional"    # Nice to have for enhanced signal (comprehensive data, whale analytics)


@dataclass
class ServiceCallResult:
    """Track individual service call result"""
    name: str
    tier: ServiceTier
    success: bool
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    data: any = None  # Store actual result


@dataclass
class DataQualityReport:
    """Comprehensive data quality metrics"""
    quality_score: float  # Percentage 0-100
    quality_level: str    # excellent/good/fair/poor
    services_total: int
    services_successful: int
    services_failed: List[Dict]  # List of {name, tier, error}
    critical_success_count: int
    important_success_count: int
    optional_success_count: int
    critical_total: int
    important_total: int
    optional_total: int


class ServiceCallMonitor:
    """
    Reusable service call monitor and quality aggregator
    Wraps asyncio.gather results with detailed tracking
    """
    
    # Service tier registry - defines which services are critical/important/optional
    SERVICE_REGISTRY = {
        # CRITICAL - Must have for valid signal
        "price_data": ServiceTier.CRITICAL,
        "funding_oi_data": ServiceTier.CRITICAL,
        "social_basic": ServiceTier.CRITICAL,
        
        # IMPORTANT - Should have for good signal  
        "liquidations": ServiceTier.IMPORTANT,
        "long_short_ratio": ServiceTier.IMPORTANT,
        "candles_data": ServiceTier.IMPORTANT,
        "fear_greed": ServiceTier.IMPORTANT,
        
        # OPTIONAL - Nice to have for enhanced signal
        "comprehensive_markets": ServiceTier.OPTIONAL,
        "lunarcrush_comprehensive": ServiceTier.OPTIONAL,
        "social_change": ServiceTier.OPTIONAL,
        "social_momentum": ServiceTier.OPTIONAL,
        "oi_trend": ServiceTier.OPTIONAL,
        "top_trader_ratio": ServiceTier.OPTIONAL,
        "coinapi_orderbook": ServiceTier.OPTIONAL,
        "coinapi_trades": ServiceTier.OPTIONAL,
        "coinapi_ohlcv": ServiceTier.OPTIONAL,
    }
    
    def __init__(self):
        self.results: List[ServiceCallResult] = []
    
    def track_result(self, name: str, result: any, execution_time_ms: float = 0.0):
        """Track a single service call result"""
        tier = self.SERVICE_REGISTRY.get(name, ServiceTier.OPTIONAL)
        
        is_exception = isinstance(result, Exception)
        success = not is_exception
        error_msg = None
        data = None
        
        if is_exception:
            # Truncate error message to avoid logging sensitive data or huge payloads
            error_msg = str(result)[:200]
        else:
            data = result
            # Check if result dict indicates failure
            if isinstance(result, dict) and not result.get("success", True):
                success = False
                error_msg = result.get("error", "Unknown error")[:200]
        
        self.results.append(ServiceCallResult(
            name=name,
            tier=tier,
            success=success,
            error_message=error_msg,
            data=data,
            execution_time_ms=execution_time_ms
        ))
    
    def calculate_quality(self) -> DataQualityReport:
        """Calculate comprehensive data quality metrics"""
        critical_total = 0
        critical_success = 0
        important_total = 0
        important_success = 0
        optional_total = 0
        optional_success = 0
        failed_services = []
        
        for result in self.results:
            if result.tier == ServiceTier.CRITICAL:
                critical_total += 1
                if result.success:
                    critical_success += 1
                else:
                    failed_services.append({
                        "name": result.name,
                        "tier": result.tier.value,
                        "error": result.error_message
                    })
            
            elif result.tier == ServiceTier.IMPORTANT:
                important_total += 1
                if result.success:
                    important_success += 1
                else:
                    failed_services.append({
                        "name": result.name,
                        "tier": result.tier.value,
                        "error": result.error_message
                    })
            
            else:  # OPTIONAL
                optional_total += 1
                if result.success:
                    optional_success += 1
                else:
                    failed_services.append({
                        "name": result.name,
                        "tier": result.tier.value,
                        "error": result.error_message
                    })
        
        # Quality calculation: (critical_success + important_success) / (critical_total + important_total)
        # Ignore optional services in quality score
        quality_denominator = critical_total + important_total
        quality_numerator = critical_success + important_success
        
        if quality_denominator == 0:
            quality_score = 0.0
        else:
            quality_score = (quality_numerator / quality_denominator) * 100
        
        # Determine quality level using SignalEngine thresholds
        if quality_score >= SignalEngine.QUALITY_THRESHOLDS["excellent"]:
            quality_level = "excellent"
        elif quality_score >= SignalEngine.QUALITY_THRESHOLDS["good"]:
            quality_level = "good"
        elif quality_score >= SignalEngine.QUALITY_THRESHOLDS["minimum"]:
            quality_level = "fair"
        else:
            quality_level = "poor"
        
        total_success = critical_success + important_success + optional_success
        total_services = critical_total + important_total + optional_total
        
        return DataQualityReport(
            quality_score=round(quality_score, 1),
            quality_level=quality_level,
            services_total=total_services,
            services_successful=total_success,
            services_failed=failed_services,
            critical_success_count=critical_success,
            important_success_count=important_success,
            optional_success_count=optional_success,
            critical_total=critical_total,
            important_total=important_total,
            optional_total=optional_total
        )
    
    def get_result_by_name(self, name: str) -> Optional[ServiceCallResult]:
        """Get tracked result by service name"""
        for result in self.results:
            if result.name == name:
                return result
        return None


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
    orderbook_imbalance: float = (
        0.0  # -100 to +100: negative=sell pressure, positive=buy pressure
    )
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
    - 3-Mode system for different risk profiles
    """

    # Scoring weights (total = 100) - ADJUSTED FOR HIGHER SENSITIVITY
    WEIGHTS = {
        "funding_rate": 18,      # High priority - smart money positioning
        "social_sentiment": 6,   # FIXED: Reduced from 8 - less reliable indicator
        "price_momentum": 20,    # High priority - price action confirmation
        "liquidations": 24,      # FIXED: Reduced from 25 - still very important
        "long_short_ratio": 11,  # FIXED: Reduced from 12 - contrarian indicator
        "oi_trend": 6,           # FIXED: Reduced from 8 - less reliable
        "smart_money": 11,       # FIXED: Reduced from 12 - whale positioning
        "fear_greed": 4,         # FIXED: Reduced from 7 - reduce sentiment weight
    }
    # Total: 100% ✅ (Fixed from 110% bug - see AUDIT_REPORT)
    
    # 3-Mode Threshold System for different risk profiles
    MODE_THRESHOLDS = {
        "conservative": {
            "short_max": 48,      # Score <= 48 = SHORT
            "neutral_min": 48,    # Score > 48 and < 52 = NEUTRAL  
            "neutral_max": 52,
            "long_min": 52,       # Score >= 52 = LONG
            "description": "Conservative Mode - Reliable signals, minimal false positives",
            "risk_level": "Low",
            "best_for": "Beginners, risk-averse traders"
        },
        "aggressive": {
            "short_max": 45,      # Score <= 45 = SHORT
            "neutral_min": 45,    # Score > 45 and < 55 = NEUTRAL
            "neutral_max": 55,
            "long_min": 55,       # Score >= 55 = LONG
            "description": "Aggressive Mode - Balanced risk/reward, catch trends earlier",
            "risk_level": "Medium",
            "best_for": "Experienced traders, trending markets"
        },
        "ultra": {
            "short_max": 49,      # Score <= 49 = SHORT
            "neutral_min": 49,    # Score > 49 and < 51 = NEUTRAL
            "neutral_max": 51,
            "long_min": 51,       # Score >= 51 = LONG
            "description": "Ultra-Aggressive Mode - Maximum signals, high frequency trading",
            "risk_level": "High",
            "best_for": "Pro scalpers, always in position"
        }
    }
    
    # Mode aliases for user convenience
    MODE_ALIASES = {
        "1": "conservative",
        "2": "aggressive", 
        "3": "ultra",
        "safe": "conservative",
        "balanced": "aggressive",
        "extreme": "ultra",
        "scalping": "ultra"
    }
    
    # ============================================================================
    # SCORING THRESHOLDS & CONFIGURATION
    # All magic numbers extracted for easy tuning and A/B testing
    # ============================================================================
    
    # Funding Rate Thresholds (in percentage %)
    # Negative = Shorts pay Longs (Bullish) | Positive = Longs pay Shorts (Bearish)
    FUNDING_RATE_THRESHOLDS = {
        "very_negative": -0.2,   # < -0.2% = Extreme short pressure cleared = Very Bullish (Score: 85)
        "negative": -0.05,       # < -0.05% = Moderate short pressure = Bullish (Score: 70)
        "slightly_negative": 0,  # < 0% = Slight bearish sentiment clearing = Slightly Bullish (Score: 60)
        "slightly_positive": 0.05,  # < 0.05% = Slight bullish pressure = Slightly Bearish (Score: 45)
        "positive": 0.2,         # < 0.2% = Moderate long pressure = Bearish (Score: 30)
        # > 0.2% = Extreme long pressure = Very Bearish (Score: 15)
    }
    FUNDING_RATE_SCORES = {
        "very_bullish": 85,
        "bullish": 70,
        "slightly_bullish": 60,
        "neutral_bearish": 45,
        "bearish": 30,
        "very_bearish": 15
    }
    
    # Price Momentum Scores
    PRICE_MOMENTUM_SCORES = {
        "bullish": 80,   # +5 bias: Strong uptrend confirmed
        "bearish": 20,   # -5 bias: Strong downtrend confirmed
        "neutral": 50    # Sideways/ranging market
    }
    
    # Liquidation Imbalance Scores (Contrarian indicator)
    LIQUIDATION_SCORES = {
        "long": 70,      # +5 bias: Longs liquidated = Bearish pressure cleared = Bullish reversal potential
        "short": 30,     # -5 bias: Shorts liquidated = Bullish pressure cleared = Bearish reversal potential
        "neutral": 50    # Balanced liquidations
    }
    
    # Long/Short Ratio Thresholds (% of accounts long - Contrarian indicator)
    # Too many longs = Overcrowded = Bearish | Too many shorts = Oversold = Bullish
    LONG_SHORT_RATIO_THRESHOLDS = {
        "overcrowded_longs": 65,    # > 65% longs = Extreme overcrowding = Very Bearish (Score: 25)
        "high_longs": 55,            # > 55% longs = Moderate overcrowding = Bearish (Score: 40)
        "oversold_shorts": 35,       # < 35% longs = Extreme short crowding = Very Bullish (Score: 75)
        "low_longs": 45              # < 45% longs = Moderate short crowding = Bullish (Score: 60)
        # 45-55% = Neutral (Score: 50)
    }
    LONG_SHORT_RATIO_SCORES = {
        "very_bearish": 25,   # Overcrowded longs
        "bearish": 40,        # High longs
        "neutral": 50,        # Balanced
        "bullish": 60,        # Low longs (high shorts)
        "very_bullish": 75    # Oversold shorts
    }
    
    # Open Interest Change Thresholds (% change in 24h)
    OI_CHANGE_THRESHOLDS = {
        "strong_increase": 5,    # > 5% = Strong conviction increase (Score: 75)
        "increase": 1,           # > 1% = Moderate increase (Score: 60)
        "strong_decrease": -5,   # < -5% = Strong conviction decrease (Score: 25)
        "decrease": -1           # < -1% = Moderate decrease (Score: 40)
        # -1% to 1% = Stable (Score: 50)
    }
    OI_CHANGE_SCORES = {
        "strong_increase": 75,
        "increase": 60,
        "neutral": 50,
        "decrease": 40,
        "strong_decrease": 25
    }
    
    # Smart Money (Top Trader) Thresholds (% of top traders long)
    SMART_MONEY_THRESHOLDS = {
        "high_long": 60,      # > 60% = Smart money heavily long = Bullish (Score: 70)
        "moderate_long": 52,  # > 52% = Smart money moderately long = Slightly Bullish (Score: 60)
        "low_long": 40,       # < 40% = Smart money heavily short = Bearish (Score: 30)
        "moderate_short": 48  # < 48% = Smart money moderately short = Slightly Bearish (Score: 40)
        # 48-52% = Neutral (Score: 50)
    }
    SMART_MONEY_SCORES = {
        "bullish": 70,
        "slightly_bullish": 60,
        "neutral": 50,
        "slightly_bearish": 40,
        "bearish": 30
    }
    
    # Fear & Greed Index Thresholds (0-100 scale)
    FEAR_GREED_THRESHOLDS = {
        "extreme_fear": 25,   # < 25 = Extreme Fear = Contrarian buy opportunity
        "extreme_greed": 75   # > 75 = Extreme Greed = Potential top/correction
    }
    
    # Multi-Timeframe Price Change Thresholds (% change)
    PRICE_CHANGE_THRESHOLDS = {
        "strong_bullish": 0.5,    # > 0.5% across timeframes = Strong uptrend
        "strong_bearish": -0.5    # < -0.5% across timeframes = Strong downtrend
    }
    
    # Candlestick Pattern Analysis
    CANDLE_ANALYSIS = {
        "min_candles": 5,              # Minimum candles needed for trend analysis
        "bullish_threshold": 6,        # >= 6 bullish candles = Strong uptrend
        "bearish_threshold": 6,        # >= 6 bearish candles = Strong downtrend
        "strong_momentum_threshold": 1.0,  # >= 1.0% weighted change = Strong momentum
        "moderate_threshold": 5        # >= 5 candles same direction = Moderate trend
    }
    
    # Volatility & Risk Metrics
    VOLATILITY_THRESHOLDS = {
        "low_variance": 5,       # < 5% variance = Low volatility = Predictable
        "moderate_variance": 15  # < 15% variance = Moderate volatility
        # > 15% = High volatility = Unpredictable
    }
    VOLATILITY_SCORES = {
        "low": 70,       # Low volatility = More predictable = Higher confidence
        "moderate": 55,  # Moderate volatility = Normal
        "high": 40       # High volatility = Less predictable = Lower confidence
    }
    
    # Data Quality Requirements
    QUALITY_THRESHOLDS = {
        "excellent": 80,     # >= 80% data quality
        "good": 60,          # >= 60% data quality
        "minimum": 50,       # >= 50% data quality (hard minimum)
        "critical_services": 3,   # Maximum critical service failures before abort
        "important_services": 5   # Maximum important service failures before warning
    }
    
    # Layer Check Thresholds (for AI verdict analysis)
    LAYER_CHECK_THRESHOLDS = {
        "long_short_high": 60,        # > 60% = Overcrowded
        "long_short_low": 40,         # < 40% = Oversold
        "smart_money_bullish": 55,    # > 55% = Smart money long bias
        "smart_money_bearish": 45,    # < 45% = Smart money short bias
        "oi_increase": 3,             # > 3% = Strong OI increase
        "oi_decrease": -3,            # < -3% = Strong OI decrease
        "funding_high": 0.1,          # > 0.1% = High funding (bearish)
        "funding_low": -0.1,          # < -0.1% = Low funding (bullish)
        "fear_greed_fear": 25,        # < 25 = Extreme fear
        "fear_greed_greed": 75,       # > 75 = Extreme greed
        "min_layers_confidence": 3    # Need >= 3 confirming layers for high confidence
    }
    
    def __init__(self):
        """Initialize and validate signal engine configuration"""
        # Validate weights sum to exactly 100%
        total_weight = sum(self.WEIGHTS.values())
        if total_weight != 100:
            raise ValueError(
                f"Signal engine weights must sum to 100%, got {total_weight}%. "
                f"Weights: {self.WEIGHTS}"
            )
        logger.info(f"✅ Signal engine initialized - weights validated (sum={total_weight}%)")

    async def build_signal(
        self, 
        symbol: str, 
        debug: bool = False, 
        enforce_quality_threshold: bool = True,
        min_quality_score: float = 50.0,
        mode: str = "aggressive"
    ) -> Dict:
        """
        Build enhanced trading signal using all data sources concurrently

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            debug: If True, include all raw metrics in response
            enforce_quality_threshold: If True, reject signals below min_quality_score (default: True)
            min_quality_score: Minimum data quality percentage required (default: 50.0%)
            mode: Signal mode - conservative/aggressive/ultra (or 1/2/3) [default: aggressive]

        Returns:
            Dict with signal, score, comprehensive analysis, data quality metrics, and mode info
            
        Raises:
            ValueError: If data quality is below threshold (when enforce_quality_threshold=True)
        """
        # Normalize mode
        mode = self._normalize_mode(mode)
        mode_info = self.MODE_THRESHOLDS[mode]
        
        logger.info(f"🔵 BUILD_SIGNAL STARTED for {symbol} - Mode: {mode} ({mode_info['risk_level']} risk) - Quality threshold: {min_quality_score}%")
        symbol = symbol.upper()

        # PHASE 1: Concurrent data collection with quality tracking
        context, quality_report = await self._collect_market_data(symbol)
        
        # PHASE 1.5: Quality validation
        logger.info(f"📊 Data Quality: {quality_report.quality_score}% ({quality_report.quality_level}) - "
              f"{quality_report.services_successful}/{quality_report.services_total} services successful")
        
        # Log failed services if any
        if quality_report.services_failed:
            logger.error(f"⚠️  Failed services ({len(quality_report.services_failed)}):")
            for failed in quality_report.services_failed[:5]:  # Show first 5 failures
                logger.error(f"   - {failed['name']} ({failed['tier']}): {failed['error']}")
            if len(quality_report.services_failed) > 5:
                logger.error(f"   ... and {len(quality_report.services_failed) - 5} more")
        
        # Enforce quality threshold if enabled
        if enforce_quality_threshold and quality_report.quality_score < min_quality_score:
            error_msg = (
                f"Insufficient data quality for {symbol}: {quality_report.quality_score}% "
                f"(minimum required: {min_quality_score}%). "
                f"Only {quality_report.services_successful}/{quality_report.services_total} services succeeded. "
                f"Critical: {quality_report.critical_success_count}/{quality_report.critical_total}, "
                f"Important: {quality_report.important_success_count}/{quality_report.important_total}. "
            )
            
            # Add top failed services to error message
            if quality_report.services_failed:
                failed_names = [f['name'] for f in quality_report.services_failed[:3]]
                error_msg += f"Failed services: {', '.join(failed_names)}"
                if len(quality_report.services_failed) > 3:
                    error_msg += f" (and {len(quality_report.services_failed) - 3} more)"
            
            logger.error(f"❌ QUALITY CHECK FAILED: {error_msg}")
            
            # Return error response instead of raising exception (better for API)
            return {
                "success": False,
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "error": error_msg,
                "data_quality": {
                    "quality_score": quality_report.quality_score,
                    "quality_level": quality_report.quality_level,
                    "services_total": quality_report.services_total,
                    "services_successful": quality_report.services_successful,
                    "services_failed": quality_report.services_failed,
                    "critical_services": {
                        "successful": quality_report.critical_success_count,
                        "total": quality_report.critical_total
                    },
                    "important_services": {
                        "successful": quality_report.important_success_count,
                        "total": quality_report.important_total
                    },
                    "threshold_enforced": True,
                    "min_quality_required": min_quality_score
                }
            }

        # PHASE 2: Calculate weighted score
        score, breakdown = self._calculate_weighted_score(context)

        # PHASE 3: Generate signal and reasoning with mode-specific thresholds
        signal = self._determine_signal(score, mode)
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
            # Mode information - NEW!
            "mode": mode,
            "mode_info": {
                "name": mode,
                "description": mode_info["description"],
                "risk_level": mode_info["risk_level"],
                "best_for": mode_info["best_for"],
                "thresholds": {
                    "short": f"0-{mode_info['short_max']}",
                    "neutral": f"{mode_info['neutral_min']}-{mode_info['neutral_max']}",
                    "long": f"{mode_info['long_min']}-100"
                }
            },
            "metrics": {
                "fundingRate": context.funding_rate,
                "openInterest": context.open_interest,
                "socialScore": context.social_score,
                "priceTrend": context.price_trend,
            },
            "premiumDataAvailable": context.premium_data_available,
            "comprehensiveDataAvailable": context.comprehensive_data_available,
            "lunarcrushDataAvailable": context.lunarcrush_comprehensive_available,
            "coinapiDataAvailable": context.coinapi_comprehensive_available,
            # Data quality metrics - NEW!
            "data_quality": {
                "quality_score": quality_report.quality_score,
                "quality_level": quality_report.quality_level,
                "services_total": quality_report.services_total,
                "services_successful": quality_report.services_successful,
                "services_failed": quality_report.services_failed,
                "critical_services": {
                    "successful": quality_report.critical_success_count,
                    "total": quality_report.critical_total,
                    "success_rate": round((quality_report.critical_success_count / quality_report.critical_total * 100), 1) if quality_report.critical_total > 0 else 0.0
                },
                "important_services": {
                    "successful": quality_report.important_success_count,
                    "total": quality_report.important_total,
                    "success_rate": round((quality_report.important_success_count / quality_report.important_total * 100), 1) if quality_report.important_total > 0 else 0.0
                },
                "optional_services": {
                    "successful": quality_report.optional_success_count,
                    "total": quality_report.optional_total
                },
                "threshold_enforced": enforce_quality_threshold,
                "min_quality_required": min_quality_score if enforce_quality_threshold else None
            },
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
                    "24h": context.price_change_24h,
                },
                "advancedRatios": {
                    "oiMarketCapRatio": context.oi_market_cap_ratio,
                    "oiVolumeRatio": context.oi_volume_ratio,
                },
                "fundingRates": {
                    "oiWeighted": context.funding_rate_oi_weighted,
                    "volumeWeighted": context.funding_rate_vol_weighted,
                },
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
                    "urlShares": context.url_shares,
                },
                "sentiment": {
                    "averageSentiment": context.average_sentiment,
                    "correlationRank": context.correlation_rank,
                },
                "momentum": {
                    "momentumScore": context.social_momentum_score,
                    "momentumLevel": context.social_momentum_level,
                    "volumeChange24h": context.social_volume_change_24h,
                    "spikeLevel": context.social_spike_level,
                },
            }

        # Add CoinAPI comprehensive metrics if available
        if context.coinapi_comprehensive_available:
            response["coinAPIMetrics"] = {
                "orderbook": {
                    "imbalance": context.orderbook_imbalance,  # -100 to +100
                    "spreadPercent": context.spread_percent,
                    "whaleBids": context.whale_bids_count,
                    "whaleAsks": context.whale_asks_count,
                },
                "trades": {
                    "buyPressure": context.buy_pressure_pct,
                    "sellPressure": context.sell_pressure_pct,
                    "avgTradeSize": context.avg_trade_size,
                },
                "volatility7d": context.volatility_7d,
            }

        # Add premium metrics if available
        if context.premium_data_available:
            response["premiumMetrics"] = {
                "liquidationImbalance": context.liquidation_imbalance,
                "longShortSentiment": context.ls_sentiment,
                "oiTrend": context.oi_trend,
                "smartMoneyBias": context.smart_money_bias,
                "fearGreedIndex": context.fear_greed_value,
            }

        # Debug mode: include all raw data
        if debug:
            response["debug"] = {
                "scoreBreakdown": breakdown,
                "allMetrics": asdict(context),
            }

        # Apply AI Verdict Layer (OpenAI V2 with rule-based fallback)
        enable_ai_judge = os.getenv("ENABLE_AI_JUDGE", "true").lower() == "true"
        if enable_ai_judge:
            response = await self._apply_ai_verdict(response)

        # Auto-send Telegram alert for actionable signals (LONG/SHORT only)
        # Respect AI verdict: skip sending if verdict is SKIP and auto_skip is enabled
        auto_skip_avoid = os.getenv("AUTO_SKIP_AVOID_SIGNALS", "true").lower() == "true"
        ai_verdict = response.get("aiVerdictLayer", {}).get("verdict", "CONFIRM")
        
        should_send_telegram = (
            signal in ["LONG", "SHORT"] 
            and telegram_notifier.enabled
            and not (auto_skip_avoid and ai_verdict == "SKIP")
        )
        
        logger.info(f"🟢 Signal={signal}, Verdict={ai_verdict}, Telegram enabled={telegram_notifier.enabled}, Should send={should_send_telegram}")
        
        if should_send_telegram:
            logger.info(f"🟡 Attempting to send Telegram alert for {symbol} {signal}")
            try:
                result = await telegram_notifier.send_signal_alert(response)
                logger.info(f"✅ Telegram alert sent successfully: {result}")
            except Exception as e:
                # Don't fail signal generation if Telegram fails
                logger.error(f"⚠️ Telegram notification failed: {e}")

        return response

    async def _apply_ai_verdict(self, signal_data: Dict) -> Dict:
        """
        Apply AI verdict layer using OpenAI V2 Signal Judge with rule-based fallback
        
        Enhances signal with:
        - verdict: CONFIRM/DOWNSIZE/SKIP/WAIT
        - riskMode: NORMAL/REDUCED/AVOID/AGGRESSIVE
        - riskMultiplier: 0.0-1.5x position size
        - aiSummary: Telegram-ready summary
        - layerChecks: Key agreements and conflicts
        
        Falls back to rule-based assessment if OpenAI fails/times out
        """
        symbol = signal_data.get("symbol", "UNKNOWN")
        ai_timeout = int(os.getenv("AI_JUDGE_TIMEOUT", "15"))
        
        try:
            logger.info(f"🤖 Calling OpenAI V2 Signal Judge for {symbol}...")
            
            openai_v2 = await asyncio.wait_for(
                get_openai_service_v2(),
                timeout=ai_timeout
            )
            
            validation_result = await asyncio.wait_for(
                openai_v2.validate_signal_with_verdict(
                    symbol=symbol,
                    signal_data=signal_data,
                    comprehensive_metrics={
                        "premiumMetrics": signal_data.get("premiumMetrics", {}),
                        "comprehensiveMetrics": signal_data.get("comprehensiveMetrics", {}),
                        "lunarCrushMetrics": signal_data.get("lunarCrushMetrics", {}),
                        "coinAPIMetrics": signal_data.get("coinAPIMetrics", {}),
                    }
                ),
                timeout=ai_timeout
            )
            
            if validation_result.get("success"):
                logger.info(f"✅ OpenAI V2 verdict: {validation_result.get('verdict')} (confidence: {validation_result.get('ai_confidence')}%)")
                
                risk_suggestion = validation_result.get("adjusted_risk_suggestion", {})
                verdict = validation_result.get("verdict", "SKIP")
                risk_mode = risk_suggestion.get("risk_factor", "NORMAL")
                
                signal_data["aiVerdictLayer"] = {
                    "verdict": verdict,
                    "riskMode": risk_mode,
                    "riskMultiplier": risk_suggestion.get("position_size_multiplier", 1.0),
                    "aiConfidence": validation_result.get("ai_confidence", 50),
                    "aiSummary": validation_result.get("telegram_summary", ""),
                    "layerChecks": {
                        "agreements": validation_result.get("key_agreements", []),
                        "conflicts": validation_result.get("key_conflicts", []),
                    },
                    "source": "openai_v2",
                    "model": validation_result.get("model_used", "gpt-4-turbo"),
                }
                
                # Calculate volatility metrics (ATR-based position sizing and stop loss)
                volatility_metrics = await self._calculate_volatility_metrics(
                    symbol=symbol,
                    entry_price=signal_data.get("price", 0),
                    signal_type=signal_data.get("signal", "NEUTRAL"),
                    risk_mode=risk_mode
                )
                
                if volatility_metrics:
                    signal_data["aiVerdictLayer"]["volatilityMetrics"] = volatility_metrics
                    logger.info(f"📊 Volatility metrics added: {volatility_metrics.get('tradePlanSummary', '')}")
                
                return signal_data
            
            else:
                error_msg = validation_result.get("error", "Unknown error")
                logger.error(f"⚠️  OpenAI V2 validation failed: {error_msg}. Falling back to rule-based.")
                raise Exception(f"V2 validation failed: {error_msg}")
        
        except asyncio.TimeoutError:
            logger.info(f"⏱️  OpenAI V2 timeout after {ai_timeout}s. Falling back to rule-based assessment.")
        except Exception as e:
            logger.error(f"⚠️  OpenAI V2 error: {e}. Falling back to rule-based assessment.")
        
        logger.info(f"🔧 Using rule-based risk assessment for {symbol}")
        verdict = risk_rules.rule_based_verdict(signal_data)
        risk_mode = risk_rules.rule_based_risk_mode(signal_data)
        risk_multiplier = risk_rules.rule_based_multiplier(signal_data)
        warnings, agreements = risk_rules.get_risk_warnings(signal_data)
        summary = risk_rules.generate_rule_based_summary(
            signal_data, verdict, risk_mode, warnings, agreements
        )
        
        signal_data["aiVerdictLayer"] = {
            "verdict": verdict,
            "riskMode": risk_mode,
            "riskMultiplier": risk_multiplier,
            "aiConfidence": None,
            "aiSummary": summary,
            "layerChecks": {
                "agreements": agreements[:3],
                "conflicts": warnings[:3],
            },
            "source": "rule_fallback",
            "model": None,
        }
        
        logger.info(f"🔧 Rule-based verdict: {verdict}, Risk mode: {risk_mode}, Multiplier: {risk_multiplier}x")
        
        # Calculate volatility metrics (ATR-based position sizing and stop loss)
        volatility_metrics = await self._calculate_volatility_metrics(
            symbol=symbol,
            entry_price=signal_data.get("price", 0),
            signal_type=signal_data.get("signal", "NEUTRAL"),
            risk_mode=risk_mode
        )
        
        if volatility_metrics:
            signal_data["aiVerdictLayer"]["volatilityMetrics"] = volatility_metrics
            logger.info(f"📊 Volatility metrics added: {volatility_metrics.get('tradePlanSummary', '')}")
        
        return signal_data

    async def _calculate_volatility_metrics(
        self,
        symbol: str,
        entry_price: float,
        signal_type: str,
        risk_mode: str = "NORMAL"
    ) -> Optional[Dict]:
        """
        Calculate volatility-adjusted position sizing and risk parameters
        
        Uses ATR (Average True Range) to determine:
        - Recommended position size (volatility-adjusted)
        - Stop loss price (ATR-based)
        - Take profit price (risk-reward optimized)
        
        Returns None if ATR calculation fails (graceful degradation)
        """
        try:
            logger.info(f"📊 Calculating volatility metrics for {symbol} ({signal_type})...")
            
            trade_plan = await position_sizer.get_complete_trade_plan(
                symbol=symbol,
                entry_price=entry_price,
                signal_type=signal_type,
                risk_mode=risk_mode,
                base_size=1.0,
                timeframe="4h"
            )
            
            if not trade_plan or "error" in trade_plan:
                logger.error(f"⚠️  Failed to calculate volatility metrics: {trade_plan.get('error') if trade_plan else 'unknown error'}")
                return None
            
            position_sizing = trade_plan.get("position_sizing", {}) or {}
            stop_loss = trade_plan.get("stop_loss", {}) or {}
            take_profit = trade_plan.get("take_profit", {}) or {}
            volatility_info = position_sizing.get("volatility_info") if position_sizing else None
            
            # Extract with safe defaults to prevent KeyError
            # IMPORTANT: Distinguish None (missing) from 0 (intentional for SKIP/AVOID)
            multiplier = position_sizing.get("multiplier") if position_sizing else None
            if multiplier is None:
                multiplier = position_sizing.get("recommended_size", 1.0) if position_sizing else 1.0
            
            recommended_size = position_sizing.get("recommended_size") if position_sizing else None
            if recommended_size is None:
                recommended_size = 1.0
            
            sl_price = stop_loss.get("stop_loss_price") if stop_loss else None
            sl_dist = stop_loss.get("distance_pct") if stop_loss else None
            
            tp_price = take_profit.get("take_profit_price") if take_profit else None
            tp_dist = take_profit.get("reward_distance_pct") if take_profit else None
            rr_ratio = take_profit.get("risk_reward_ratio") if take_profit else None
            
            atr_val = volatility_info.get("atr_value") if volatility_info else None
            atr_pct = volatility_info.get("current_atr_pct") if volatility_info else None
            classification = volatility_info.get("classification", "UNKNOWN") if volatility_info else "UNKNOWN"
            
            return {
                "recommendedPositionMultiplier": round(multiplier, 4) if multiplier is not None else 1.0,
                "recommendedPositionSize": round(recommended_size, 4) if recommended_size is not None else 1.0,
                "stopLossPrice": round(sl_price, 8) if sl_price is not None else None,
                "stopLossDistancePct": round(sl_dist, 4) if sl_dist is not None else None,
                "takeProfitPrice": round(tp_price, 8) if tp_price is not None else None,
                "takeProfitDistancePct": round(tp_dist, 4) if tp_dist is not None else None,
                "riskRewardRatio": round(rr_ratio, 2) if rr_ratio is not None else None,
                "atrValue": round(atr_val, 8) if atr_val is not None else None,
                "atrPercentage": round(atr_pct, 4) if atr_pct is not None else None,
                "volatilityClassification": classification,
                "tradePlanSummary": trade_plan.get("trade_plan_summary", "ATR unavailable"),
                "timeframe": "4h"
            }
        
        except Exception as e:
            logger.error(f"[ERROR] _calculate_volatility_metrics failed: {e}")
            return None

    async def _get_funding_and_oi_with_fallback(self, symbol: str, cg_data: Dict, comp_markets: Dict, comprehensive_available: bool) -> Dict:
        """
        Get funding rate and open interest with automatic OKX fallback for reliability.
        
        Implements robust fallback strategy to ensure critical funding/OI data is available:
        1. Primary: Coinglass (comprehensive or basic)
        2. Fallback: OKX if Coinglass fails or returns zeros
        
        Args:
            symbol: Cryptocurrency symbol
            cg_data: Coinglass basic data response
            comp_markets: Coinglass comprehensive markets data
            comprehensive_available: Whether comprehensive data succeeded
            
        Returns:
            Dict containing:
                - fundingRate: Current funding rate (%)
                - openInterest: Total open interest (USD)
                - fundingSource: Data source used ('coinglass' or 'okx')
                - oiSource: Data source used ('coinglass' or 'okx')
                
        Note:
            Funding and OI may use different sources if only one Coinglass metric failed.
            Source tracking enables quality report accuracy.
        """
        # Start with Coinglass data
        funding_source = "coinglass"
        oi_source = "coinglass"
        
        funding = (
            comp_markets.get("fundingRateByOI", cg_data.get("fundingRate", 0.0))
            if comprehensive_available
            else cg_data.get("fundingRate", 0.0)
        )
        oi = (
            comp_markets.get("openInterestUsd", cg_data.get("openInterest", 0.0))
            if comprehensive_available
            else cg_data.get("openInterest", 0.0)
        )
        
        # Check if Coinglass data is valid
        cg_success = cg_data.get("success", False) or comprehensive_available
        
        # If Coinglass failed or returned zero values, try OKX fallback
        if not cg_success or (funding == 0.0 and oi == 0.0):
            logger.warning(f"⚠️  Coinglass funding/OI unavailable for {symbol}, attempting OKX fallback...")
            
            try:
                # Fetch from OKX
                okx_funding_result, okx_oi_result = await asyncio.gather(
                    okx_service.get_funding_rate(symbol),
                    okx_service.get_open_interest(symbol),
                    return_exceptions=True
                )
                
                # Handle potential exceptions
                if not isinstance(okx_funding_result, Exception) and okx_funding_result.get("success"):
                    funding = okx_funding_result.get("fundingRate", 0.0)
                    funding_source = "okx"
                    logger.info(f"✅ OKX funding rate retrieved for {symbol}: {funding}")
                
                if not isinstance(okx_oi_result, Exception) and okx_oi_result.get("success"):
                    oi = okx_oi_result.get("openInterest", 0.0)
                    oi_source = "okx"
                    logger.info(f"✅ OKX open interest retrieved for {symbol}: {oi}")
                    
            except Exception as e:
                logger.error(f"⚠️  OKX fallback failed for {symbol}: {e}")
        
        return {
            "fundingRate": funding,
            "openInterest": oi,
            "fundingSource": funding_source,
            "oiSource": oi_source
        }
    
    async def _collect_market_data(self, symbol: str) -> Tuple[EnhancedSignalContext, DataQualityReport]:
        """
        Fetch all market data concurrently from multiple providers using asyncio.gather.
        
        Orchestrates concurrent data retrieval from multiple sources including:
        - CoinAPI: Spot price, orderbook depth, recent trades, OHLCV historical
        - Coinglass: Funding rates, open interest, comprehensive markets data
        - Coinglass Premium: Liquidations, long/short ratio, OI trend, top trader ratio, Fear & Greed
        - LunarCrush: Social score, comprehensive coin data, social change, momentum analysis
        - OKX: Candlestick data for trend calculation
        
        Implementation:
        - Parallel execution using asyncio.gather with return_exceptions=True
        - Quality tracking with 3-tier service classification (CRITICAL/IMPORTANT/OPTIONAL)
        - OKX fallback attempted if Coinglass funding/OI fails
        - Returns empty context if price data is missing (critical failure)
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'SOL')
            
        Returns:
            Tuple[EnhancedSignalContext, DataQualityReport]: 
                - context: Populated with available market data using safe defaults for failures
                - quality_report: Quality metrics including score, failed services, tier breakdown
        """
        # Initialize service call monitor
        monitor = ServiceCallMonitor()
        start_time = time.time()
        
        # Fetch all data sources in parallel
        results = await asyncio.gather(
            coinapi_service.get_spot_price(symbol),
            coinglass_service.get_funding_and_oi(symbol),
            coinglass_comprehensive.get_coins_markets(
                symbol=symbol
            ),  # Comprehensive markets
            lunarcrush_service.get_social_score(symbol),  # Basic social score
            lunarcrush_comprehensive.get_coin_comprehensive(
                symbol
            ),  # Comprehensive LunarCrush
            lunarcrush_comprehensive.get_social_change(
                symbol, "24h"
            ),  # 24h change detection
            lunarcrush_comprehensive.analyze_social_momentum(
                symbol
            ),  # Social momentum analysis
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
            return_exceptions=True,  # Don't fail if one endpoint fails
        )

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Unpack results
        (
            price_data,
            cg_data,
            comp_markets,
            social_data,
            lc_comp,
            lc_change,
            lc_momentum,
            candles_data,
            liq_data,
            ls_data,
            oi_trend_data,
            trader_data,
            fg_data,
            ca_orderbook,
            ca_trades,
            ca_ohlcv,
        ) = results

        # Track all service results with monitor
        # Execution time is averaged across all parallel calls
        avg_time_per_service = execution_time_ms / len(results)
        
        monitor.track_result("price_data", price_data, avg_time_per_service)
        monitor.track_result("funding_oi_data", cg_data, avg_time_per_service)
        monitor.track_result("comprehensive_markets", comp_markets, avg_time_per_service)
        monitor.track_result("social_basic", social_data, avg_time_per_service)
        monitor.track_result("lunarcrush_comprehensive", lc_comp, avg_time_per_service)
        monitor.track_result("social_change", lc_change, avg_time_per_service)
        monitor.track_result("social_momentum", lc_momentum, avg_time_per_service)
        monitor.track_result("candles_data", candles_data, avg_time_per_service)
        monitor.track_result("liquidations", liq_data, avg_time_per_service)
        monitor.track_result("long_short_ratio", ls_data, avg_time_per_service)
        monitor.track_result("oi_trend", oi_trend_data, avg_time_per_service)
        monitor.track_result("top_trader_ratio", trader_data, avg_time_per_service)
        monitor.track_result("fear_greed", fg_data, avg_time_per_service)
        monitor.track_result("coinapi_orderbook", ca_orderbook, avg_time_per_service)
        monitor.track_result("coinapi_trades", ca_trades, avg_time_per_service)
        monitor.track_result("coinapi_ohlcv", ca_ohlcv, avg_time_per_service)

        # Handle potential exceptions (still needed for fallback logic)
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
        oi_trend_data = (
            oi_trend_data if not isinstance(oi_trend_data, Exception) else {}
        )
        trader_data = trader_data if not isinstance(trader_data, Exception) else {}
        fg_data = fg_data if not isinstance(fg_data, Exception) else {}
        ca_orderbook = ca_orderbook if not isinstance(ca_orderbook, Exception) else {}
        ca_trades = ca_trades if not isinstance(ca_trades, Exception) else {}
        ca_ohlcv = ca_ohlcv if not isinstance(ca_ohlcv, Exception) else {}

        # Calculate price trend from OKX candles
        price_trend = self._calculate_price_trend(candles_data.get("candles", []))

        # Calculate multi-timeframe trend from comprehensive markets data
        multi_tf_trend = self._calculate_multi_timeframe_trend(comp_markets)

        # Build context - FIXED: More flexible premium data check
        # Accept premium data if at least 2 out of 4 endpoints succeed
        # OI Trend endpoint frequently returns 404 for some coins (like SOL)
        premium_success_count = sum([
            liq_data.get("success", False),
            ls_data.get("success", False),
            oi_trend_data.get("success", False),
            trader_data.get("success", False)
        ])
        premium_available = premium_success_count >= 2
        
        # Log which premium endpoints succeeded
        if premium_available:
            successful_endpoints = []
            if liq_data.get("success"): successful_endpoints.append("liquidations")
            if ls_data.get("success"): successful_endpoints.append("long/short ratio")
            if oi_trend_data.get("success"): successful_endpoints.append("OI trend")
            if trader_data.get("success"): successful_endpoints.append("top trader")
            logger.info(f"✅ Premium data available for {symbol}: {', '.join(successful_endpoints)}")

        comprehensive_available = comp_markets.get("success", False)
        lunarcrush_comp_available = lc_comp.get("success", False)
        # CoinAPI: Accept if any endpoint succeeds (not requiring all)
        coinapi_comp_available = (
            ca_orderbook.get("success", False)
            or ca_trades.get("success", False)
            or ca_ohlcv.get("success", False)
        )

        # Log comprehensive data availability
        if not comprehensive_available:
            error_msg = comp_markets.get("error", "unknown error")
            logger.error(f"⚠️  Comprehensive markets data unavailable for {symbol}: {error_msg}. Falling back to basic Coinglass data.")

        if not lunarcrush_comp_available:
            error_msg = lc_comp.get("error", "unknown error")
            logger.error(f"⚠️  Comprehensive LunarCrush data unavailable for {symbol}: {error_msg}. Falling back to basic social score.")

        if not coinapi_comp_available:
            logger.warning(f"⚠️  CoinAPI comprehensive data unavailable for {symbol}. Order book/trades analysis will use defaults.")

        # CRITICAL: Validate price data - hard-fail if missing
        price_value = (
            comp_markets.get("price", price_data.get("price", 0.0))
            if comprehensive_available
            else price_data.get("price", 0.0)
        )
        
        if price_value == 0.0 or not price_data:
            # Price data is CRITICAL - cannot generate signal without it
            error_msg = f"❌ CRITICAL: Price data missing for {symbol}. Cannot generate signal."
            logger.error(error_msg)
            # Mark price as failed and return early with quality report
            monitor.track_result("price_data", Exception(error_msg), 0.0)
            quality_report = monitor.calculate_quality()
            # Return empty context with quality report showing critical failure
            empty_context = EnhancedSignalContext(
                symbol=symbol,
                price=0.0,
                funding_rate=0.0,
                open_interest=0.0,
                social_score=0.0,
                price_trend="unknown"
            )
            return (empty_context, quality_report)
        
        # Get funding/OI with OKX fallback
        funding_oi_data = await self._get_funding_and_oi_with_fallback(
            symbol, cg_data, comp_markets, comprehensive_available
        )
        
        funding = funding_oi_data["fundingRate"]
        oi = funding_oi_data["openInterest"]
        funding_source = funding_oi_data["fundingSource"]
        oi_source = funding_oi_data["oiSource"]
        
        # Update funding/OI tracking to reflect final fallback state
        # If fallback succeeded (source changed to okx), update the tracked result
        if funding_source == "okx" or oi_source == "okx":
            # Overwrite the original failed result with successful fallback
            fallback_success_data = {
                "success": True,
                "fundingRate": funding,
                "openInterest": oi,
                "source": f"fallback_to_{funding_source}"
            }
            monitor.track_result("funding_oi_data", fallback_success_data, 0.0)
            logger.info(f"✅ Funding/OI fallback successful - updated quality tracking")

        # Build context
        context = EnhancedSignalContext(
            symbol=symbol,
            price=(
                comp_markets.get("price", price_data.get("price", 0.0))
                if comprehensive_available
                else price_data.get("price", 0.0)
            ),
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
            orderbook_imbalance=(
                ca_orderbook.get("metrics", {}).get("imbalance", 0.0)
                if coinapi_comp_available
                else 0.0
            ),
            spread_percent=(
                ca_orderbook.get("spread", {}).get("spreadPercent", 0.0)
                if coinapi_comp_available
                else 0.0
            ),
            whale_bids_count=(
                ca_orderbook.get("whaleWalls", {}).get("largeBids", 0)
                if coinapi_comp_available
                else 0
            ),
            whale_asks_count=(
                ca_orderbook.get("whaleWalls", {}).get("largeAsks", 0)
                if coinapi_comp_available
                else 0
            ),
            buy_pressure_pct=(
                ca_trades.get("volume", {}).get("buyPressure", 50.0)
                if coinapi_comp_available
                else 50.0
            ),
            sell_pressure_pct=(
                ca_trades.get("volume", {}).get("sellPressure", 50.0)
                if coinapi_comp_available
                else 50.0
            ),
            avg_trade_size=(
                ca_trades.get("volume", {}).get("avgTradeSize", 0.0)
                if coinapi_comp_available
                else 0.0
            ),
            volatility_7d=(
                ca_ohlcv.get("analysis", {}).get("volatility", 0.0)
                if ca_ohlcv.get("success", False)
                else 0.0
            ),
            # Data quality flags
            premium_data_available=premium_available,
            comprehensive_data_available=comprehensive_available,
            lunarcrush_comprehensive_available=lunarcrush_comp_available,
            coinapi_comprehensive_available=coinapi_comp_available,
        )
        
        # Calculate final quality report
        quality_report = monitor.calculate_quality()
        
        # Return tuple of (context, quality_report)
        return (context, quality_report)

    def _calculate_price_trend(self, candles: list) -> str:
        """
        Calculate simple price trend from candle data

        Args:
            candles: List of OHLCV candle data

        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        if not candles or len(candles) < self.CANDLE_ANALYSIS["min_candles"]:
            return "neutral"

        try:
            # Get recent candles (most recent first in OKX)
            recent = candles[:self.CANDLE_ANALYSIS["min_candles"]]

            # Compare current price with average of last N candles
            current_close = recent[0]["close"]
            avg_close = sum(c["close"] for c in recent) / len(recent)

            # Calculate percentage difference
            diff_pct = ((current_close - avg_close) / avg_close) * 100

            if diff_pct > self.PRICE_CHANGE_THRESHOLDS["strong_bullish"]:
                return "bullish"
            elif diff_pct < self.PRICE_CHANGE_THRESHOLDS["strong_bearish"]:
                return "bearish"
            else:
                return "neutral"
        except Exception as e:
            logger.error(f"Error calculating price trend: {e}")
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
                "5m": comp_markets.get("priceChange5m", 0.0),
                "15m": comp_markets.get("priceChange15m", 0.0),
                "30m": comp_markets.get("priceChange30m", 0.0),
                "1h": comp_markets.get("priceChange1h", 0.0),
                "4h": comp_markets.get("priceChange4h", 0.0),
                "12h": comp_markets.get("priceChange12h", 0.0),
                "24h": comp_markets.get("priceChange24h", 0.0),
            }

            # Count bullish vs bearish timeframes
            bullish_count = sum(1 for change in changes.values() if change > 0)
            bearish_count = sum(1 for change in changes.values() if change < 0)

            # Weighted score (longer timeframes = more weight)
            weights = {
                "5m": 1,
                "15m": 1,
                "30m": 1,
                "1h": 2,
                "4h": 3,
                "12h": 4,
                "24h": 5,
            }
            weighted_sum = sum(changes[tf] * weights[tf] for tf in changes)
            total_weight = sum(weights.values())
            avg_weighted_change = weighted_sum / total_weight if total_weight > 0 else 0

            # Determine trend strength using configured thresholds
            if (bullish_count >= self.CANDLE_ANALYSIS["bullish_threshold"] and 
                avg_weighted_change > self.CANDLE_ANALYSIS["strong_momentum_threshold"]):
                return "strongly_bullish"
            elif bullish_count >= self.CANDLE_ANALYSIS["moderate_threshold"]:
                return "bullish"
            elif (bearish_count >= self.CANDLE_ANALYSIS["bearish_threshold"] and 
                  avg_weighted_change < -self.CANDLE_ANALYSIS["strong_momentum_threshold"]):
                return "strongly_bearish"
            elif bearish_count >= self.CANDLE_ANALYSIS["moderate_threshold"]:
                return "bearish"
            else:
                return "neutral"
        except Exception as e:
            logger.error(f"Error calculating multi-timeframe trend: {e}")
            return "neutral"

    def _calculate_weighted_score(
        self, context: EnhancedSignalContext
    ) -> tuple[float, Dict]:
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
            "weighted": funding_score * self.WEIGHTS["funding_rate"] / 100,
        }

        # 2. Social Sentiment Score (10%)
        social_score = context.social_score  # Already 0-100
        breakdown["social_sentiment"] = {
            "score": social_score,
            "weight": self.WEIGHTS["social_sentiment"],
            "weighted": social_score * self.WEIGHTS["social_sentiment"] / 100,
        }

        # 3. Price Momentum Score (15%)
        momentum_score = self._score_price_momentum(context.price_trend)
        breakdown["price_momentum"] = {
            "score": momentum_score,
            "weight": self.WEIGHTS["price_momentum"],
            "weighted": momentum_score * self.WEIGHTS["price_momentum"] / 100,
        }

        # 4. Liquidation Score (20%)
        liq_score = self._score_liquidations(context)
        breakdown["liquidations"] = {
            "score": liq_score,
            "weight": self.WEIGHTS["liquidations"],
            "weighted": liq_score * self.WEIGHTS["liquidations"] / 100,
        }

        # 5. Long/Short Ratio Score (15%)
        ls_score = self._score_long_short_ratio(context.long_account_pct)
        breakdown["long_short_ratio"] = {
            "score": ls_score,
            "weight": self.WEIGHTS["long_short_ratio"],
            "weighted": ls_score * self.WEIGHTS["long_short_ratio"] / 100,
        }

        # 6. OI Trend Score (10%)
        oi_score = self._score_oi_trend(context.oi_change_pct)
        breakdown["oi_trend"] = {
            "score": oi_score,
            "weight": self.WEIGHTS["oi_trend"],
            "weighted": oi_score * self.WEIGHTS["oi_trend"] / 100,
        }

        # 7. Smart Money Score (10%)
        smart_score = self._score_smart_money(context.top_trader_long_pct)
        breakdown["smart_money"] = {
            "score": smart_score,
            "weight": self.WEIGHTS["smart_money"],
            "weighted": smart_score * self.WEIGHTS["smart_money"] / 100,
        }

        # 8. Fear & Greed Score (5%)
        fg_score = context.fear_greed_value  # Already 0-100
        breakdown["fear_greed"] = {
            "score": fg_score,
            "weight": self.WEIGHTS["fear_greed"],
            "weighted": fg_score * self.WEIGHTS["fear_greed"] / 100,
        }

        # Calculate total weighted score
        total_score = sum(item["weighted"] for item in breakdown.values())

        return total_score, breakdown

    def _score_funding_rate(self, rate: float) -> float:
        """
        Score funding rate on 0-100 scale using configured thresholds
        Negative funding = bullish (shorts pay longs) = high score
        Positive funding = bearish (longs pay shorts) = low score
        """
        # Normalize to percentage
        rate_pct = rate * 100

        if rate_pct < self.FUNDING_RATE_THRESHOLDS["very_negative"]:
            return self.FUNDING_RATE_SCORES["very_bullish"]
        elif rate_pct < self.FUNDING_RATE_THRESHOLDS["negative"]:
            return self.FUNDING_RATE_SCORES["bullish"]
        elif rate_pct < self.FUNDING_RATE_THRESHOLDS["slightly_negative"]:
            return self.FUNDING_RATE_SCORES["slightly_bullish"]
        elif rate_pct < self.FUNDING_RATE_THRESHOLDS["slightly_positive"]:
            return self.FUNDING_RATE_SCORES["neutral_bearish"]
        elif rate_pct < self.FUNDING_RATE_THRESHOLDS["positive"]:
            return self.FUNDING_RATE_SCORES["bearish"]
        else:
            return self.FUNDING_RATE_SCORES["very_bearish"]

    def _score_price_momentum(self, trend: str) -> float:
        """Score price momentum based on trend using configured scores"""
        if trend == "bullish":
            return self.PRICE_MOMENTUM_SCORES["bullish"]
        elif trend == "bearish":
            return self.PRICE_MOMENTUM_SCORES["bearish"]
        else:
            return self.PRICE_MOMENTUM_SCORES["neutral"]

    def _score_liquidations(self, context: EnhancedSignalContext) -> float:
        """
        Score based on liquidation imbalance using configured scores
        More longs liquidated = bearish pressure cleared = bullish
        """
        if not context.premium_data_available:
            return self.LIQUIDATION_SCORES["neutral"]

        if context.liquidation_imbalance == "long":
            return self.LIQUIDATION_SCORES["long"]
        elif context.liquidation_imbalance == "short":
            return self.LIQUIDATION_SCORES["short"]
        else:
            return self.LIQUIDATION_SCORES["neutral"]

    def _score_long_short_ratio(self, long_pct: float) -> float:
        """
        Score based on long/short ratio using configured thresholds (contrarian indicator)
        Too many longs = bearish, too many shorts = bullish
        """
        if long_pct > self.LONG_SHORT_RATIO_THRESHOLDS["overcrowded_longs"]:
            return self.LONG_SHORT_RATIO_SCORES["very_bearish"]
        elif long_pct > self.LONG_SHORT_RATIO_THRESHOLDS["high_longs"]:
            return self.LONG_SHORT_RATIO_SCORES["bearish"]
        elif long_pct < self.LONG_SHORT_RATIO_THRESHOLDS["oversold_shorts"]:
            return self.LONG_SHORT_RATIO_SCORES["very_bullish"]
        elif long_pct < self.LONG_SHORT_RATIO_THRESHOLDS["low_longs"]:
            return self.LONG_SHORT_RATIO_SCORES["bullish"]
        else:
            return self.LONG_SHORT_RATIO_SCORES["neutral"]

    def _score_oi_trend(self, change_pct: float) -> float:
        """
        Score based on OI change using configured thresholds
        Rising OI = confirmation of trend
        """
        if change_pct > self.OI_CHANGE_THRESHOLDS["strong_increase"]:
            return self.OI_CHANGE_SCORES["strong_increase"]
        elif change_pct > self.OI_CHANGE_THRESHOLDS["increase"]:
            return self.OI_CHANGE_SCORES["increase"]
        elif change_pct < self.OI_CHANGE_THRESHOLDS["strong_decrease"]:
            return self.OI_CHANGE_SCORES["strong_decrease"]
        elif change_pct < self.OI_CHANGE_THRESHOLDS["decrease"]:
            return self.OI_CHANGE_SCORES["decrease"]
        else:
            return self.OI_CHANGE_SCORES["neutral"]

    def _score_smart_money(self, top_trader_long_pct: float) -> float:
        """
        Score based on what smart money is doing using configured thresholds
        Follow the whales
        """
        if top_trader_long_pct > self.SMART_MONEY_THRESHOLDS["high_long"]:
            return self.SMART_MONEY_SCORES["bullish"]
        elif top_trader_long_pct > self.SMART_MONEY_THRESHOLDS["moderate_long"]:
            return self.SMART_MONEY_SCORES["slightly_bullish"]
        elif top_trader_long_pct < self.SMART_MONEY_THRESHOLDS["low_long"]:
            return self.SMART_MONEY_SCORES["bearish"]
        elif top_trader_long_pct < self.SMART_MONEY_THRESHOLDS["moderate_short"]:
            return self.SMART_MONEY_SCORES["slightly_bearish"]
        else:
            return self.SMART_MONEY_SCORES["neutral"]

    def _normalize_mode(self, mode: Optional[str]) -> str:
        """
        Normalize mode input to standard mode name
        Supports: conservative/aggressive/ultra, 1/2/3, safe/balanced/extreme, etc.
        """
        if not mode:
            return "aggressive"  # Default mode
        
        mode_lower = str(mode).lower().strip()
        
        # Check aliases first
        if mode_lower in self.MODE_ALIASES:
            return self.MODE_ALIASES[mode_lower]
        
        # Check direct mode names
        if mode_lower in self.MODE_THRESHOLDS:
            return mode_lower
        
        # Default to aggressive if unknown
        logger.warning(f"⚠️  Unknown mode '{mode}', defaulting to 'aggressive'")
        return "aggressive"
    
    def _determine_signal(self, score: float, mode: str = "aggressive") -> str:
        """
        Determine LONG/SHORT/NEUTRAL based on score and mode
        
        Modes:
        - conservative (mode 1): Reliable signals, minimal false positives
          • 0-48: SHORT, 48-52: NEUTRAL, 52-100: LONG
        
        - aggressive (mode 2): Balanced risk/reward, catch trends earlier [DEFAULT]
          • 0-45: SHORT, 45-55: NEUTRAL, 55-100: LONG
        
        - ultra (mode 3): Maximum signals, high frequency trading
          • 0-49: SHORT, 49-51: NEUTRAL, 51-100: LONG
        """
        # Normalize mode input
        mode = self._normalize_mode(mode)
        
        # Get thresholds for this mode
        thresholds = self.MODE_THRESHOLDS.get(mode, self.MODE_THRESHOLDS["aggressive"])
        
        # Apply thresholds
        if score >= thresholds["long_min"]:
            return "LONG"
        elif score <= thresholds["short_max"]:
            return "SHORT"
        else:
            return "NEUTRAL"

    def _calculate_confidence(self, breakdown: Dict) -> str:
        """
        Calculate confidence level based on score distribution
        """
        weighted_scores = [item["weighted"] for item in breakdown.values()]
        avg_score = sum(weighted_scores) / len(weighted_scores)

        # Check if scores are aligned or divergent using configured thresholds
        variance = sum((s - avg_score) ** 2 for s in weighted_scores) / len(
            weighted_scores
        )

        if variance < self.VOLATILITY_THRESHOLDS["low_variance"]:
            return "high"
        elif variance < self.VOLATILITY_THRESHOLDS["moderate_variance"]:
            return "medium"
        else:
            return "low"

    def _generate_top_reasons(
        self, breakdown: Dict, context: EnhancedSignalContext
    ) -> List[str]:
        """
        Generate top 3 reasons for the signal based on highest weighted contributions
        """
        reasons = []

        # Sort by weighted score contribution
        sorted_factors = sorted(
            breakdown.items(),
            key=lambda x: abs(x[1]["weighted"] - 50),  # Distance from neutral
            reverse=True,
        )

        # Generate human-readable reasons for top 3 factors
        for factor_name, factor_data in sorted_factors[:3]:
            score = factor_data["score"]

            if factor_name == "liquidations":
                if context.liquidation_imbalance == "long":
                    reasons.append(
                        f"Heavy long liquidations (${context.long_liquidations/1e6:.1f}M) - bearish pressure clearing"
                    )
                elif context.liquidation_imbalance == "short":
                    reasons.append(
                        f"Heavy short liquidations (${context.short_liquidations/1e6:.1f}M) - bullish pressure clearing"
                    )

            elif factor_name == "long_short_ratio":
                if context.long_account_pct > self.LAYER_CHECK_THRESHOLDS["long_short_high"]:
                    reasons.append(
                        f"Overcrowded longs ({context.long_account_pct:.1f}%) - contrarian bearish"
                    )
                elif context.long_account_pct < self.LAYER_CHECK_THRESHOLDS["long_short_low"]:
                    reasons.append(
                        f"Overcrowded shorts ({context.short_account_pct:.1f}%) - contrarian bullish"
                    )

            elif factor_name == "smart_money":
                if context.top_trader_long_pct > self.LAYER_CHECK_THRESHOLDS["smart_money_bullish"]:
                    reasons.append(
                        f"Smart money long-biased ({context.top_trader_long_pct:.1f}%)"
                    )
                elif context.top_trader_long_pct < self.LAYER_CHECK_THRESHOLDS["smart_money_bearish"]:
                    reasons.append(
                        f"Smart money short-biased ({context.top_trader_long_pct:.1f}%)"
                    )

            elif factor_name == "oi_trend":
                if context.oi_change_pct > self.LAYER_CHECK_THRESHOLDS["oi_increase"]:
                    reasons.append(
                        f"OI rising strongly (+{context.oi_change_pct:.1f}%) - trend confirmation"
                    )
                elif context.oi_change_pct < self.LAYER_CHECK_THRESHOLDS["oi_decrease"]:
                    reasons.append(
                        f"OI falling ({context.oi_change_pct:.1f}%) - trend weakening"
                    )

            elif factor_name == "funding_rate":
                rate_pct = context.funding_rate * 100
                if rate_pct > self.LAYER_CHECK_THRESHOLDS["funding_high"]:
                    reasons.append(
                        f"High funding rate ({rate_pct:.3f}%) - longs overleveraged"
                    )
                elif rate_pct < self.LAYER_CHECK_THRESHOLDS["funding_low"]:
                    reasons.append(
                        f"Negative funding ({rate_pct:.3f}%) - shorts overleveraged"
                    )

            elif factor_name == "fear_greed":
                if context.fear_greed_value < self.LAYER_CHECK_THRESHOLDS["fear_greed_fear"]:
                    reasons.append(
                        f"Extreme fear ({context.fear_greed_value}/100) - buy opportunity"
                    )
                elif context.fear_greed_value > self.LAYER_CHECK_THRESHOLDS["fear_greed_greed"]:
                    reasons.append(
                        f"Extreme greed ({context.fear_greed_value}/100) - sell signal"
                    )

        # If we don't have enough reasons yet, add basic ones
        if len(reasons) < self.LAYER_CHECK_THRESHOLDS["min_layers_confidence"]:
            reasons.append(f"Price trend: {context.price_trend}")
            reasons.append(f"Social sentiment: {context.social_score:.0f}/100")

        return reasons[:3]  # Return top 3


# Singleton instance
signal_engine = SignalEngine()

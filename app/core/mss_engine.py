"""
MSS (Multimodal Signal Score) Engine

Implements 3-phase analysis system for high-potential crypto asset prediction:
- Phase 1: Discovery (Tokenomics filtering)
- Phase 2: Confirmation (Social momentum)
- Phase 3: Validation (Institutional positioning)

Based on research: Multi-Modal Data Fusion for Alpha Generation
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MSSEngine:
    """
    MSS scoring engine that combines tokenomics, social sentiment, and whale activity
    into a single predictive score for identifying high-potential assets before retail adoption.
    """
    
    # Scoring weights from research paper
    WEIGHT_DISCOVERY = 0.35      # 35% - Tokenomics & valuation
    WEIGHT_SOCIAL = 0.30          # 30% - Social momentum & sentiment
    WEIGHT_VALIDATION = 0.35      # 35% - Institutional positioning
    
    # Thresholds for scoring
    MAX_FDV_AGGRESSIVE = 50_000_000    # $50M FDV threshold
    MAX_AGE_HOURS = 72                  # 72 hours for new listings
    MIN_ALTRANK = 100                   # AltRank threshold (lower is better)
    MIN_GALAXY_SCORE = 65               # Galaxy Score threshold
    MIN_OI_INCREASE = 50.0              # Minimum OI increase %
    
    def __init__(self):
        """Initialize MSS Engine"""
        self.version = "1.0.0"
        logger.info(f"MSS Engine v{self.version} initialized")
    
    def calculate_discovery_score(
        self,
        fdv_usd: Optional[float],
        age_hours: Optional[float],
        circulating_supply_pct: Optional[float] = None,
        market_cap_usd: Optional[float] = None
    ) -> Tuple[float, Dict]:
        """
        Phase 1: Discovery Score (0-35 points)
        
        Evaluates tokenomics for early-stage growth potential:
        - FDV (Fully Diluted Valuation) - lower is better
        - Age - newer is better (< 72 hours ideal)
        - Float (circulating supply %) - lower means higher volatility potential
        
        Args:
            fdv_usd: Fully diluted valuation in USD
            age_hours: Hours since listing/pool creation
            circulating_supply_pct: % of total supply in circulation
            market_cap_usd: Current market cap
        
        Returns:
            Tuple of (score, breakdown_dict)
        """
        score = 0.0
        breakdown = {
            "fdv_score": 0.0,
            "age_score": 0.0,
            "float_score": 0.0,
            "status": "FAIL"
        }
        
        # FDV Score (0-15 points) - inverse relationship
        if fdv_usd is not None:
            if fdv_usd <= 5_000_000:
                fdv_score = 15.0  # Ultra low cap
            elif fdv_usd <= 10_000_000:
                fdv_score = 13.0  # Very low cap
            elif fdv_usd <= 25_000_000:
                fdv_score = 10.0  # Low cap
            elif fdv_usd <= 50_000_000:
                fdv_score = 6.0   # Medium-low cap
            else:
                fdv_score = 2.0   # Above threshold
            
            breakdown["fdv_score"] = fdv_score
            breakdown["fdv_usd"] = fdv_usd
            score += fdv_score
        
        # Age Score (0-12 points) - newer is better
        if age_hours is not None:
            if age_hours <= 24:
                age_score = 12.0   # Ultra fresh
            elif age_hours <= 48:
                age_score = 10.0   # Very fresh
            elif age_hours <= 72:
                age_score = 7.0    # Fresh
            elif age_hours <= 168:  # 1 week
                age_score = 4.0    # Recent
            else:
                age_score = 1.0    # Older
            
            breakdown["age_score"] = age_score
            breakdown["age_hours"] = age_hours
            score += age_score
        
        # Float Score (0-8 points) - low float = high volatility potential
        if circulating_supply_pct is not None:
            if circulating_supply_pct <= 20:
                float_score = 8.0   # Very low float (whale-controlled)
            elif circulating_supply_pct <= 40:
                float_score = 6.0   # Low float
            elif circulating_supply_pct <= 60:
                float_score = 4.0   # Medium float
            else:
                float_score = 2.0   # High float
            
            breakdown["float_score"] = float_score
            breakdown["circulating_supply_pct"] = circulating_supply_pct
            score += float_score
        
        # Determine pass/fail
        if score >= 20.0:  # At least 20/35 to pass phase 1
            breakdown["status"] = "PASS"
        
        breakdown["total_score"] = round(score, 2)
        
        logger.info(f"Discovery score: {score:.2f}/35 - Status: {breakdown['status']}")
        return score, breakdown
    
    def calculate_social_score(
        self,
        altrank: Optional[float],
        galaxy_score: Optional[float],
        sentiment_score: Optional[float],
        volume_24h_change_pct: Optional[float],
        social_volume_change_pct: Optional[float] = None
    ) -> Tuple[float, Dict]:
        """
        Phase 2: Social Confirmation Score (0-30 points)
        
        Validates social momentum and market interest:
        - AltRank - lower rank = stronger performance (< 100 ideal)
        - Galaxy Score - overall health metric (> 65 ideal)
        - Sentiment - bullish bias confirmation
        - Volume spike - market validation (> 100% ideal)
        
        Args:
            altrank: LunarCrush AltRank (lower is better)
            galaxy_score: LunarCrush Galaxy Score (0-100)
            sentiment_score: Average sentiment (-1 to 1, or 0-100)
            volume_24h_change_pct: 24h volume change %
            social_volume_change_pct: Social mentions change %
        
        Returns:
            Tuple of (score, breakdown_dict)
        """
        score = 0.0
        breakdown = {
            "altrank_score": 0.0,
            "galaxy_score_points": 0.0,
            "sentiment_score_points": 0.0,
            "volume_score": 0.0,
            "status": "FAIL"
        }
        
        # AltRank Score (0-10 points) - lower rank is better
        if altrank is not None:
            if altrank <= 50:
                altrank_score = 10.0   # Top 50
            elif altrank <= 100:
                altrank_score = 8.0    # Top 100
            elif altrank <= 200:
                altrank_score = 5.0    # Top 200
            elif altrank <= 500:
                altrank_score = 3.0    # Top 500
            else:
                altrank_score = 1.0    # Below 500
            
            breakdown["altrank_score"] = altrank_score
            breakdown["altrank"] = altrank
            score += altrank_score
        
        # Galaxy Score (0-8 points)
        if galaxy_score is not None:
            if galaxy_score >= 75:
                galaxy_points = 8.0    # Excellent
            elif galaxy_score >= 65:
                galaxy_points = 6.0    # Good
            elif galaxy_score >= 50:
                galaxy_points = 4.0    # Average
            else:
                galaxy_points = 1.0    # Below average
            
            breakdown["galaxy_score_points"] = galaxy_points
            breakdown["galaxy_score"] = galaxy_score
            score += galaxy_points
        
        # Sentiment Score (0-6 points)
        if sentiment_score is not None:
            # Normalize sentiment to 0-100 scale if needed
            normalized_sentiment = sentiment_score
            if sentiment_score < 0:  # If -1 to 1 scale
                normalized_sentiment = (sentiment_score + 1) * 50
            
            if normalized_sentiment >= 70:
                sentiment_points = 6.0   # Very bullish
            elif normalized_sentiment >= 60:
                sentiment_points = 4.5   # Bullish
            elif normalized_sentiment >= 50:
                sentiment_points = 3.0   # Neutral-positive
            else:
                sentiment_points = 1.0   # Bearish/neutral
            
            breakdown["sentiment_score_points"] = sentiment_points
            breakdown["sentiment_score"] = sentiment_score
            score += sentiment_points
        
        # Volume Spike Score (0-6 points)
        if volume_24h_change_pct is not None:
            if volume_24h_change_pct >= 200:
                volume_score = 6.0     # Massive spike
            elif volume_24h_change_pct >= 100:
                volume_score = 5.0     # Large spike
            elif volume_24h_change_pct >= 50:
                volume_score = 3.5     # Moderate spike
            elif volume_24h_change_pct >= 25:
                volume_score = 2.0     # Small increase
            else:
                volume_score = 0.5     # Minimal change
            
            breakdown["volume_score"] = volume_score
            breakdown["volume_24h_change_pct"] = volume_24h_change_pct
            score += volume_score
        
        # Determine pass/fail
        if score >= 18.0:  # At least 18/30 to pass phase 2
            breakdown["status"] = "PASS"
        
        breakdown["total_score"] = round(score, 2)
        
        logger.info(f"Social score: {score:.2f}/30 - Status: {breakdown['status']}")
        return score, breakdown
    
    def calculate_validation_score(
        self,
        oi_change_pct: Optional[float],
        funding_rate: Optional[float],
        top_trader_long_ratio: Optional[float],
        whale_accumulation: Optional[bool],
        liquidation_ratio: Optional[float] = None
    ) -> Tuple[float, Dict]:
        """
        Phase 3: Institutional Validation Score (0-35 points)
        
        Confirms whale/smart money positioning:
        - OI (Open Interest) delta - increasing OI = institutional flow
        - Funding rate - positive = leverage bullish bias
        - Top trader ratios - whale positioning
        - Whale accumulation - detected via orderbook/trades
        
        Args:
            oi_change_pct: Open Interest change % (recent timeframe)
            funding_rate: Current funding rate (%)
            top_trader_long_ratio: Long/Short ratio of top traders
            whale_accumulation: Boolean flag from whale detection
            liquidation_ratio: Long/Short liquidation ratio
        
        Returns:
            Tuple of (score, breakdown_dict)
        """
        score = 0.0
        breakdown = {
            "oi_score": 0.0,
            "funding_score": 0.0,
            "whale_positioning_score": 0.0,
            "accumulation_bonus": 0.0,
            "status": "FAIL"
        }
        
        # OI Delta Score (0-12 points)
        if oi_change_pct is not None:
            if oi_change_pct >= 200:
                oi_score = 12.0    # Massive institutional flow
            elif oi_change_pct >= 100:
                oi_score = 10.0    # Strong flow
            elif oi_change_pct >= 50:
                oi_score = 7.0     # Moderate flow
            elif oi_change_pct >= 25:
                oi_score = 4.0     # Some flow
            elif oi_change_pct >= 0:
                oi_score = 1.0     # Minimal/stable
            else:
                oi_score = 0.0     # Decreasing (bearish)
            
            breakdown["oi_score"] = oi_score
            breakdown["oi_change_pct"] = oi_change_pct
            score += oi_score
        
        # Funding Rate Score (0-8 points)
        if funding_rate is not None:
            # Funding rate as percentage (0.01% to 0.05% typical)
            if 0.01 <= funding_rate <= 0.04:
                funding_score = 8.0    # Healthy bullish leverage
            elif funding_rate > 0.04:
                funding_score = 4.0    # Extreme (risk of long squeeze)
            elif funding_rate > 0:
                funding_score = 5.0    # Slightly positive
            else:
                funding_score = 1.0    # Neutral/negative
            
            breakdown["funding_score"] = funding_score
            breakdown["funding_rate"] = funding_rate
            score += funding_score
        
        # Top Trader Positioning Score (0-10 points)
        if top_trader_long_ratio is not None:
            if 1.5 <= top_trader_long_ratio <= 2.5:
                whale_score = 10.0   # Strong conviction, not overcrowded
            elif top_trader_long_ratio > 2.5:
                whale_score = 5.0    # Overcrowded (reversal risk)
            elif top_trader_long_ratio >= 1.2:
                whale_score = 7.0    # Moderate bullish
            elif top_trader_long_ratio >= 1.0:
                whale_score = 4.0    # Neutral
            else:
                whale_score = 1.0    # Bearish positioning
            
            breakdown["whale_positioning_score"] = whale_score
            breakdown["top_trader_long_ratio"] = top_trader_long_ratio
            score += whale_score
        
        # Whale Accumulation Bonus (0-5 points)
        if whale_accumulation:
            accumulation_bonus = 5.0
            breakdown["accumulation_bonus"] = accumulation_bonus
            breakdown["whale_accumulation"] = True
            score += accumulation_bonus
        else:
            breakdown["whale_accumulation"] = False
        
        # Determine pass/fail
        if score >= 20.0:  # At least 20/35 to pass phase 3
            breakdown["status"] = "PASS"
        
        breakdown["total_score"] = round(score, 2)
        
        logger.info(f"Validation score: {score:.2f}/35 - Status: {breakdown['status']}")
        return score, breakdown
    
    def calculate_final_mss(
        self,
        discovery_score: float,
        social_score: float,
        validation_score: float
    ) -> Tuple[float, str, Dict]:
        """
        Calculate final MSS (Multimodal Signal Score) from 3 phases
        
        Formula: MSS = (Discovery × 0.35) + (Social × 0.30) + (Validation × 0.35)
        Scale: 0-100 (normalized from 0-100 component scores)
        
        Args:
            discovery_score: Phase 1 score (0-35)
            social_score: Phase 2 score (0-30)
            validation_score: Phase 3 score (0-35)
        
        Returns:
            Tuple of (mss_score, signal, breakdown)
        """
        # Normalize scores to 0-100 scale for final MSS
        discovery_normalized = (discovery_score / 35.0) * 100
        social_normalized = (social_score / 30.0) * 100
        validation_normalized = (validation_score / 35.0) * 100
        
        # Calculate weighted MSS
        mss = (
            (discovery_normalized * self.WEIGHT_DISCOVERY) +
            (social_normalized * self.WEIGHT_SOCIAL) +
            (validation_normalized * self.WEIGHT_VALIDATION)
        )
        
        # Determine signal
        if mss >= 75:
            signal = "STRONG_LONG"
            confidence = "very_high"
        elif mss >= 65:
            signal = "LONG"
            confidence = "high"
        elif mss >= 50:
            signal = "MODERATE_LONG"
            confidence = "medium"
        elif mss >= 35:
            signal = "WEAK_LONG"
            confidence = "low"
        else:
            signal = "NEUTRAL"
            confidence = "insufficient"
        
        breakdown = {
            "mss_score": round(mss, 2),
            "signal": signal,
            "confidence": confidence,
            "components": {
                "discovery_contribution": round(discovery_normalized * self.WEIGHT_DISCOVERY, 2),
                "social_contribution": round(social_normalized * self.WEIGHT_SOCIAL, 2),
                "validation_contribution": round(validation_normalized * self.WEIGHT_VALIDATION, 2)
            },
            "raw_scores": {
                "discovery": round(discovery_score, 2),
                "social": round(social_score, 2),
                "validation": round(validation_score, 2)
            },
            "normalized_scores": {
                "discovery": round(discovery_normalized, 2),
                "social": round(social_normalized, 2),
                "validation": round(validation_normalized, 2)
            }
        }
        
        logger.info(
            f"Final MSS: {mss:.2f}/100 - Signal: {signal} - "
            f"Confidence: {confidence}"
        )
        
        return mss, signal, breakdown
    
    def get_risk_warnings(
        self,
        age_hours: Optional[float],
        fdv_usd: Optional[float],
        funding_rate: Optional[float],
        top_trader_long_ratio: Optional[float],
        circulating_supply_pct: Optional[float]
    ) -> list:
        """
        Generate risk warnings based on extreme conditions
        
        Args:
            age_hours: Asset age
            fdv_usd: FDV
            funding_rate: Funding rate
            top_trader_long_ratio: Trader ratio
            circulating_supply_pct: Float %
        
        Returns:
            List of warning strings
        """
        warnings = []
        
        if age_hours and age_hours < 48:
            warnings.append("⚠️ Very new asset - extreme volatility expected")
        
        if fdv_usd and fdv_usd < 10_000_000:
            warnings.append("⚠️ Ultra low cap - high manipulation risk")
        
        if circulating_supply_pct and circulating_supply_pct < 30:
            warnings.append("⚠️ Low float - whale-controlled price action")
        
        if funding_rate and funding_rate > 0.05:
            warnings.append("🚨 Extreme funding rate - long squeeze risk HIGH")
        
        if top_trader_long_ratio and top_trader_long_ratio > 3.0:
            warnings.append("🚨 Overcrowded long consensus - reversal imminent")
        
        return warnings

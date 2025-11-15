"""
Unified Scoring System for CryptoSatX

Combines multiple signal sources into a single 0-100 composite score
for easy comparison and decision making.

Scoring Components:
- Smart Money Accumulation (30%)
- MSS Score (25%)
- Technical RSI (15%)
- Social Momentum (15%)
- Whale Activity (10%)
- Volume Spike (5%)

Output: Single unified score with tier classification
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.utils.logger import default_logger


class UnifiedScorer:
    """
    Combine all signals into single composite score (0-100)

    Weights can be customized based on market conditions or user preferences.
    Default weights optimized for balanced signal combination.
    """

    # Weight configuration (must sum to 1.0)
    WEIGHTS = {
        "smart_money_accumulation": 0.30,  # 30% - Whale accumulation/distribution
        "mss_score": 0.25,                  # 25% - Multi-modal signal score
        "technical_rsi": 0.15,              # 15% - RSI oversold/overbought
        "social_momentum": 0.15,            # 15% - LunarCrush social metrics
        "whale_activity": 0.10,             # 10% - Large transaction activity
        "volume_spike": 0.05                # 5% - Volume anomalies
    }

    # Tier thresholds
    TIER_THRESHOLDS = {
        "TIER_1": 85,  # Must buy - Very strong signal
        "TIER_2": 70,  # Strong buy - Good signal
        "TIER_3": 55,  # Watchlist - Moderate signal
        "TIER_4": 0    # Neutral - Weak signal
    }

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.logger = default_logger

        # Validate weights sum to 1.0
        total_weight = sum(self.WEIGHTS.values())
        if abs(total_weight - 1.0) > 0.001:
            self.logger.warning(
                f"Weights sum to {total_weight}, not 1.0. "
                "Scores may be incorrect."
            )

    async def _gather_all_scores(self, symbol: str) -> Dict[str, float]:
        """
        Gather scores from all signal sources

        Returns normalized scores (0-100) for each component
        """
        scores = {}

        # Import services
        try:
            from app.services.smart_money_service import SmartMoneyService
            from app.services.mss_service import MSSService
            from app.services.coinglass_service import CoinglassService
            from app.services.lunarcrush_service import LunarCrushService
        except ImportError as e:
            self.logger.error(f"Failed to import services: {e}")
            return self._get_default_scores()

        # Initialize services
        smart_money = SmartMoneyService()
        mss = MSSService()
        coinglass = CoinglassService()
        lunarcrush = LunarCrushService()

        try:
            # Gather all data in parallel
            tasks = {
                "smart_money": self._get_smart_money_score(smart_money, symbol),
                "mss": self._get_mss_score(mss, symbol),
                "technical": self._get_technical_score(coinglass, symbol),
                "social": self._get_social_score(lunarcrush, symbol),
                "whale": self._get_whale_score(symbol),
                "volume": self._get_volume_score(symbol)
            }

            results = await asyncio.gather(
                *tasks.values(),
                return_exceptions=True
            )

            # Process results
            for idx, (key, result) in enumerate(zip(tasks.keys(), results)):
                if isinstance(result, Exception):
                    self.logger.warning(f"Error getting {key} score: {result}")
                    scores[key] = 50.0  # Default neutral score
                else:
                    scores[key] = result

        except Exception as e:
            self.logger.error(f"Error gathering scores for {symbol}: {e}")
            scores = self._get_default_scores()

        finally:
            # Cleanup
            await smart_money.close()
            await mss.close()

        return scores

    async def _get_smart_money_score(
        self,
        service: Any,
        symbol: str
    ) -> float:
        """
        Get Smart Money accumulation/distribution score

        Returns: 0-100 (normalized from 0-10 scale)
        """
        try:
            result = await service.scan_markets(coins=[symbol])

            # Check accumulation signals
            accumulation = result.get("accumulation", [])
            for signal in accumulation:
                if signal.get("symbol") == symbol:
                    # Normalize 0-10 scale to 0-100
                    raw_score = signal.get("score", 0)
                    return (raw_score / 10.0) * 100

            # Check distribution signals (inverse score for selling)
            distribution = result.get("distribution", [])
            for signal in distribution:
                if signal.get("symbol") == symbol:
                    raw_score = signal.get("score", 0)
                    # High distribution = low unified score
                    return 100 - ((raw_score / 10.0) * 100)

            return 50.0  # Neutral if no signal

        except Exception as e:
            self.logger.error(f"Error getting smart money score: {e}")
            return 50.0

    async def _get_mss_score(self, service: Any, symbol: str) -> float:
        """
        Get MSS (Multi-modal Signal Score)

        Returns: 0-100 (already on 0-100 scale)
        """
        try:
            # Try to analyze single coin
            result = await service.phase1_discovery(limit=100)

            # Find the symbol in results
            for coin in result:
                if coin.get("symbol") == symbol:
                    return float(coin.get("mss_score", 50))

            return 50.0  # Neutral if not found

        except Exception as e:
            self.logger.error(f"Error getting MSS score: {e}")
            return 50.0

    async def _get_technical_score(self, service: Any, symbol: str) -> float:
        """
        Get technical score based on RSI

        Returns: 0-100
        - RSI < 20: Very oversold (high score 90-100)
        - RSI < 30: Oversold (high score 70-90)
        - RSI 30-70: Neutral (score 40-60)
        - RSI > 70: Overbought (low score 10-30)
        - RSI > 80: Very overbought (low score 0-10)
        """
        try:
            # Get RSI data
            rsi_data = await service.get_rsi(symbol)

            if not rsi_data.get("success"):
                return 50.0

            rsi = rsi_data.get("rsi", 50)

            # Convert RSI to score (inverse relationship for buying)
            if rsi < 20:
                score = 95  # Very oversold - excellent buy
            elif rsi < 30:
                score = 80  # Oversold - good buy
            elif rsi < 40:
                score = 65  # Slightly oversold
            elif rsi < 60:
                score = 50  # Neutral
            elif rsi < 70:
                score = 35  # Slightly overbought
            elif rsi < 80:
                score = 20  # Overbought - consider selling
            else:
                score = 5   # Very overbought - strong sell signal

            return float(score)

        except Exception as e:
            self.logger.error(f"Error getting technical score: {e}")
            return 50.0

    async def _get_social_score(self, service: Any, symbol: str) -> float:
        """
        Get social momentum score from LunarCrush

        Returns: 0-100
        """
        try:
            metrics = await service.get_coin_metrics(symbol)

            if not metrics:
                return 50.0

            # Use galaxy score or alt rank
            galaxy_score = metrics.get("galaxy_score")
            if galaxy_score:
                return float(galaxy_score)

            # Alternative: convert alt rank to score
            alt_rank = metrics.get("alt_rank")
            if alt_rank:
                # Lower rank = higher score
                # Rank 1 = 100, Rank 100 = 50, Rank 1000+ = 0
                score = max(0, 100 - (alt_rank / 10))
                return float(score)

            return 50.0

        except Exception as e:
            self.logger.error(f"Error getting social score: {e}")
            return 50.0

    async def _get_whale_score(self, symbol: str) -> float:
        """
        Get whale activity score

        Returns: 0-100
        (Placeholder - would integrate with whale tracking service)
        """
        # TODO: Integrate with actual whale tracking
        # For now, return neutral
        return 50.0

    async def _get_volume_score(self, symbol: str) -> float:
        """
        Get volume spike score

        Returns: 0-100
        (Placeholder - would analyze volume anomalies)
        """
        # TODO: Integrate with volume analysis
        # For now, return neutral
        return 50.0

    def _get_default_scores(self) -> Dict[str, float]:
        """Return default neutral scores"""
        return {
            "smart_money": 50.0,
            "mss": 50.0,
            "technical": 50.0,
            "social": 50.0,
            "whale": 50.0,
            "volume": 50.0
        }

    def _classify_tier(self, score: float) -> str:
        """
        Classify score into tier

        Args:
            score: Unified score (0-100)

        Returns:
            Tier name (TIER_1, TIER_2, TIER_3, TIER_4)
        """
        if score >= self.TIER_THRESHOLDS["TIER_1"]:
            return "TIER_1_MUST_BUY"
        elif score >= self.TIER_THRESHOLDS["TIER_2"]:
            return "TIER_2_STRONG_BUY"
        elif score >= self.TIER_THRESHOLDS["TIER_3"]:
            return "TIER_3_WATCHLIST"
        else:
            return "TIER_4_NEUTRAL"

    def _get_recommendation(self, score: float) -> str:
        """Get buy/sell recommendation based on score"""
        if score >= 85:
            return "STRONG BUY - Immediate action recommended"
        elif score >= 70:
            return "BUY - Good opportunity"
        elif score >= 55:
            return "WATCH - Add to watchlist"
        elif score >= 40:
            return "HOLD - Neutral"
        else:
            return "AVOID - Weak signal"

    def _calculate_confidence(self, scores: Dict[str, float]) -> str:
        """
        Calculate confidence level based on score agreement

        If all scores are similar (low variance), confidence is high
        If scores disagree (high variance), confidence is low
        """
        values = list(scores.values())
        avg = sum(values) / len(values)

        # Calculate variance
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        # Confidence based on standard deviation
        if std_dev < 10:
            return "VERY_HIGH"
        elif std_dev < 20:
            return "HIGH"
        elif std_dev < 30:
            return "MEDIUM"
        else:
            return "LOW"

    async def calculate_unified_score(self, symbol: str) -> Dict:
        """
        Calculate composite unified score from all signal sources

        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")

        Returns:
            {
                "symbol": "BTC",
                "unified_score": 87.5,
                "tier": "TIER_1_MUST_BUY",
                "recommendation": "STRONG BUY - Immediate action recommended",
                "confidence": "HIGH",
                "breakdown": {
                    "smart_money_accumulation": 85.0,
                    "mss_score": 82.0,
                    "technical_rsi": 75.0,
                    "social_momentum": 70.0,
                    "whale_activity": 50.0,
                    "volume_spike": 50.0
                },
                "weighted_contributions": {
                    "smart_money_accumulation": 25.5,  # 85.0 * 0.30
                    "mss_score": 20.5,                  # 82.0 * 0.25
                    "technical_rsi": 11.25,             # 75.0 * 0.15
                    "social_momentum": 10.5,            # 70.0 * 0.15
                    "whale_activity": 5.0,              # 50.0 * 0.10
                    "volume_spike": 2.5                 # 50.0 * 0.05
                },
                "timestamp": "2025-11-15T14:30:00Z"
            }
        """
        self.logger.info(f"Calculating unified score for {symbol}")

        # Gather all scores
        scores = await self._gather_all_scores(symbol)

        # Calculate weighted contributions
        weighted = {}
        unified_score = 0.0

        for component, raw_score in scores.items():
            # Map component names to weight keys
            weight_key = component.replace("smart_money", "smart_money_accumulation")
            weight_key = weight_key.replace("technical", "technical_rsi")
            weight_key = weight_key.replace("social", "social_momentum")
            weight_key = weight_key.replace("whale", "whale_activity")
            weight_key = weight_key.replace("volume", "volume_spike")
            weight_key = weight_key.replace("mss", "mss_score")

            weight = self.WEIGHTS.get(weight_key, 0)
            contribution = raw_score * weight
            weighted[weight_key] = round(contribution, 2)
            unified_score += contribution

        # Classify tier
        tier = self._classify_tier(unified_score)
        recommendation = self._get_recommendation(unified_score)
        confidence = self._calculate_confidence(scores)

        result = {
            "symbol": symbol.upper(),
            "unified_score": round(unified_score, 1),
            "tier": tier,
            "recommendation": recommendation,
            "confidence": confidence,
            "breakdown": {
                "smart_money_accumulation": round(scores.get("smart_money", 50), 1),
                "mss_score": round(scores.get("mss", 50), 1),
                "technical_rsi": round(scores.get("technical", 50), 1),
                "social_momentum": round(scores.get("social", 50), 1),
                "whale_activity": round(scores.get("whale", 50), 1),
                "volume_spike": round(scores.get("volume", 50), 1)
            },
            "weighted_contributions": weighted,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.info(
            f"Unified score for {symbol}: {result['unified_score']} "
            f"({result['tier']}, confidence: {result['confidence']})"
        )

        return result

    async def calculate_bulk_scores(
        self,
        symbols: List[str],
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """
        Calculate unified scores for multiple symbols

        Args:
            symbols: List of symbols to score
            min_score: Optional minimum score filter

        Returns:
            List of score results, sorted by unified_score descending
        """
        self.logger.info(f"Calculating bulk unified scores for {len(symbols)} symbols")

        # Calculate scores in parallel
        tasks = [
            self.calculate_unified_score(symbol)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors and apply min_score filter
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Error in bulk calculation: {result}")
                continue

            if min_score and result["unified_score"] < min_score:
                continue

            valid_results.append(result)

        # Sort by unified_score descending
        valid_results.sort(key=lambda x: x["unified_score"], reverse=True)

        self.logger.info(
            f"Bulk calculation complete: {len(valid_results)}/{len(symbols)} valid"
        )

        return valid_results


# Global instance
unified_scorer = UnifiedScorer()


# Convenience function
async def get_unified_score(symbol: str) -> Dict:
    """Get unified score for a symbol"""
    return await unified_scorer.calculate_unified_score(symbol)


async def get_unified_ranking(
    symbols: List[str],
    min_score: Optional[float] = None
) -> List[Dict]:
    """Get ranked list of symbols by unified score"""
    return await unified_scorer.calculate_bulk_scores(symbols, min_score)

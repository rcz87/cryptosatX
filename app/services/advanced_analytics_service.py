"""
Advanced Analytics Service for CryptoSatX
AI/ML-powered pattern recognition and predictive analytics
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatternSignal:
    """Pattern detection signal"""

    pattern_type: str
    confidence: float
    timeframe: str
    entry_price: float
    targets: List[float]
    stop_loss: float
    description: str


@dataclass
class PredictiveSignal:
    """Predictive analytics signal"""

    prediction_type: str
    probability: float
    time_horizon: str
    expected_move: float
    confidence_interval: Tuple[float, float]
    factors: List[str]


class AdvancedAnalyticsService:
    """Advanced analytics with ML capabilities"""

    def __init__(self):
        self.patterns_cache = {}
        self.predictions_cache = {}
        self.support_resistance_levels = {}

    async def detect_chart_patterns(self, symbol: str, timeframe: str = "1h") -> Dict:
        """Detect technical chart patterns using ML algorithms"""
        try:
            # Get historical data
            historical_data = await self._get_historical_data(symbol, timeframe)

            if len(historical_data) < 50:
                return {"error": "Insufficient data for pattern detection"}

            patterns = []

            # Pattern 1: Head and Shoulders
            hs_pattern = self._detect_head_shoulders(historical_data)
            if hs_pattern:
                patterns.append(hs_pattern)

            # Pattern 2: Double Top/Bottom
            dt_pattern = self._detect_double_top_bottom(historical_data)
            if dt_pattern:
                patterns.append(dt_pattern)

            # Pattern 3: Triangle Patterns
            triangle_pattern = self._detect_triangle_patterns(historical_data)
            if triangle_pattern:
                patterns.append(triangle_pattern)

            # Pattern 4: Flag Patterns
            flag_pattern = self._detect_flag_patterns(historical_data)
            if flag_pattern:
                patterns.append(flag_pattern)

            # Pattern 5: Wedge Patterns
            wedge_pattern = self._detect_wedge_patterns(historical_data)
            if wedge_pattern:
                patterns.append(wedge_pattern)

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "patterns_detected": len(patterns),
                "patterns": [self._pattern_to_dict(p) for p in patterns],
                "analysis_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Pattern detection error for {symbol}: {e}")
            return {"error": str(e)}

    async def predict_price_movement(self, symbol: str, horizon: str = "24h") -> Dict:
        """Predict price movement using ML models"""
        try:
            # Get comprehensive data
            price_data = await self._get_historical_data(symbol, "1h", limit=200)
            volume_data = await self._get_volume_data(symbol)
            sentiment_data = await self._get_sentiment_data(symbol)

            if len(price_data) < 100:
                return {"error": "Insufficient data for prediction"}

            predictions = []

            # Prediction 1: Trend Continuation
            trend_pred = self._predict_trend_continuation(price_data, volume_data)
            predictions.append(trend_pred)

            # Prediction 2: Mean Reversion
            mean_rev_pred = self._predict_mean_reversion(price_data)
            predictions.append(mean_rev_pred)

            # Prediction 3: Volatility Forecast
            vol_pred = self._predict_volatility(price_data)
            predictions.append(vol_pred)

            # Prediction 4: Price Target
            price_target = self._predict_price_target(price_data, sentiment_data)
            predictions.append(price_target)

            # Aggregate predictions
            consensus = self._aggregate_predictions(predictions)

            return {
                "symbol": symbol,
                "prediction_horizon": horizon,
                "consensus_prediction": consensus,
                "individual_predictions": [
                    self._prediction_to_dict(p) for p in predictions
                ],
                "confidence_score": consensus.get("confidence", 0),
                "analysis_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Price prediction error for {symbol}: {e}")
            return {"error": str(e)}

    async def analyze_market_sentiment(self, symbol: str) -> Dict:
        """Analyze market sentiment from multiple sources"""
        try:
            sentiment_sources = []

            # Source 1: Social Media Sentiment
            social_sentiment = await self._get_social_sentiment(symbol)
            sentiment_sources.append(social_sentiment)

            # Source 2: News Sentiment
            news_sentiment = await self._get_news_sentiment(symbol)
            sentiment_sources.append(news_sentiment)

            # Source 3: Order Book Sentiment
            orderbook_sentiment = await self._get_orderbook_sentiment(symbol)
            sentiment_sources.append(orderbook_sentiment)

            # Source 4: Funding Rate Sentiment
            funding_sentiment = await self._get_funding_sentiment(symbol)
            sentiment_sources.append(funding_sentiment)

            # Aggregate sentiment
            aggregated = self._aggregate_sentiment(sentiment_sources)

            return {
                "symbol": symbol,
                "overall_sentiment": aggregated["sentiment"],
                "sentiment_score": aggregated["score"],
                "confidence": aggregated["confidence"],
                "sources": sentiment_sources,
                "analysis_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Sentiment analysis error for {symbol}: {e}")
            return {"error": str(e)}

    async def detect_anomalies(self, symbol: str) -> Dict:
        """Detect unusual market behavior and anomalies"""
        try:
            # Get various data points
            price_data = await self._get_historical_data(symbol, "5m", limit=500)
            volume_data = await self._get_volume_data(symbol)
            orderbook_data = await self._get_orderbook_data(symbol)

            anomalies = []

            # Anomaly 1: Volume Spike
            volume_anomaly = self._detect_volume_anomaly(volume_data)
            if volume_anomaly:
                anomalies.append(volume_anomaly)

            # Anomaly 2: Price Gap
            price_gap = self._detect_price_gap(price_data)
            if price_gap:
                anomalies.append(price_gap)

            # Anomaly 3: Order Book Imbalance
            orderbook_anomaly = self._detect_orderbook_anomaly(orderbook_data)
            if orderbook_anomaly:
                anomalies.append(orderbook_anomaly)

            # Anomaly 4: Volatility Spike
            vol_anomaly = self._detect_volatility_anomaly(price_data)
            if vol_anomaly:
                anomalies.append(vol_anomaly)

            return {
                "symbol": symbol,
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies,
                "risk_level": self._calculate_risk_level(anomalies),
                "analysis_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Anomaly detection error for {symbol}: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _get_historical_data(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> List[Dict]:
        """Get historical price data"""
        # This would integrate with existing price data sources
        # For now, return mock data
        prices = []
        base_price = 50000 if symbol == "BTC" else 3000
        for i in range(limit):
            price = base_price + (np.sin(i / 10) * 1000) + (np.random.randn() * 100)
            prices.append(
                {
                    "timestamp": datetime.utcnow() - timedelta(hours=limit - i),
                    "open": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price,
                    "volume": np.random.randint(100, 1000),
                }
            )
        return prices

    async def _get_volume_data(self, symbol: str) -> List[Dict]:
        """Get volume data"""
        # Mock volume data
        return [
            {
                "timestamp": datetime.utcnow() - timedelta(hours=i),
                "volume": np.random.randint(100, 1000),
            }
            for i in range(100)
        ]

    async def _get_sentiment_data(self, symbol: str) -> Dict:
        """Get sentiment data"""
        # Mock sentiment data
        return {
            "score": np.random.uniform(-1, 1),
            "confidence": np.random.uniform(0.5, 1),
        }

    def _detect_head_shoulders(self, data: List[Dict]) -> Optional[PatternSignal]:
        """Detect head and shoulders pattern"""
        # Simplified pattern detection logic
        prices = [d["close"] for d in data[-50:]]

        # Look for head and shoulders formation
        if len(prices) < 20:
            return None

        # Find peaks and valleys
        peaks = []
        valleys = []

        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i - 1] and prices[i] > prices[i + 1]:
                peaks.append((i, prices[i]))
            elif prices[i] < prices[i - 1] and prices[i] < prices[i + 1]:
                valleys.append((i, prices[i]))

        # Check for head and shoulders pattern
        if len(peaks) >= 3 and len(valleys) >= 2:
            # Simplified logic - in real implementation would be more sophisticated
            return PatternSignal(
                pattern_type="head_and_shoulders",
                confidence=0.75,
                timeframe="4h",
                entry_price=prices[-1],
                targets=[prices[-1] * 0.95, prices[-1] * 0.90],
                stop_loss=prices[-1] * 1.02,
                description="Head and shoulders pattern detected, indicating potential bearish reversal",
            )

        return None

    def _detect_double_top_bottom(self, data: List[Dict]) -> Optional[PatternSignal]:
        """Detect double top or double bottom pattern"""
        prices = [d["close"] for d in data[-50:]]

        # Simplified double top/bottom detection
        if len(prices) < 20:
            return None

        # Find recent peaks
        peaks = []
        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i - 1] and prices[i] > prices[i + 1]:
                peaks.append((i, prices[i]))

        if len(peaks) >= 2:
            # Check if two peaks are at similar levels
            recent_peaks = peaks[-2:]
            price_diff = (
                abs(recent_peaks[0][1] - recent_peaks[1][1]) / recent_peaks[0][1]
            )

            if price_diff < 0.02:  # Within 2% difference
                pattern_type = (
                    "double_top" if recent_peaks[0][1] > prices[-1] else "double_bottom"
                )

                return PatternSignal(
                    pattern_type=pattern_type,
                    confidence=0.70,
                    timeframe="1h",
                    entry_price=prices[-1],
                    targets=(
                        [prices[-1] * 0.95]
                        if pattern_type == "double_top"
                        else [prices[-1] * 1.05]
                    ),
                    stop_loss=(
                        prices[-1] * 1.02
                        if pattern_type == "double_top"
                        else prices[-1] * 0.98
                    ),
                    description=f"{pattern_type.replace('_', ' ').title()} pattern detected",
                )

        return None

    def _detect_triangle_patterns(self, data: List[Dict]) -> Optional[PatternSignal]:
        """Detect triangle patterns (ascending, descending, symmetrical)"""
        # Simplified triangle detection
        prices = [d["close"] for d in data[-50:]]

        if len(prices) < 30:
            return None

        # Calculate trendlines
        highs = [d["high"] for d in data[-30:]]
        lows = [d["low"] for d in data[-30:]]

        # Simple linear regression for trendlines
        x = np.arange(len(highs))
        high_slope = np.polyfit(x, highs, 1)[0]
        low_slope = np.polyfit(x, lows, 1)[0]

        # Determine triangle type
        if abs(high_slope) < 0.1 and abs(low_slope) < 0.1:
            pattern_type = "symmetrical_triangle"
        elif high_slope > 0 and low_slope > 0:
            pattern_type = "ascending_triangle"
        elif high_slope < 0 and low_slope < 0:
            pattern_type = "descending_triangle"
        else:
            return None

        return PatternSignal(
            pattern_type=pattern_type,
            confidence=0.65,
            timeframe="2h",
            entry_price=prices[-1],
            targets=[prices[-1] * 1.03],
            stop_loss=prices[-1] * 0.98,
            description=f"{pattern_type.replace('_', ' ').title()} pattern detected",
        )

    def _detect_flag_patterns(self, data: List[Dict]) -> Optional[PatternSignal]:
        """Detect flag patterns (bullish/bearish flags)"""
        # Simplified flag detection
        prices = [d["close"] for d in data[-50:]]

        if len(prices) < 20:
            return None

        # Look for strong trend followed by consolidation
        recent_prices = prices[-20:]
        earlier_prices = prices[-40:-20]

        recent_volatility = np.std(recent_prices) / np.mean(recent_prices)
        earlier_trend = (earlier_prices[-1] - earlier_prices[0]) / earlier_prices[0]

        if abs(earlier_trend) > 0.05 and recent_volatility < 0.02:
            pattern_type = "bullish_flag" if earlier_trend > 0 else "bearish_flag"

            return PatternSignal(
                pattern_type=pattern_type,
                confidence=0.60,
                timeframe="1h",
                entry_price=prices[-1],
                targets=(
                    [prices[-1] * 1.02]
                    if pattern_type == "bullish_flag"
                    else [prices[-1] * 0.98]
                ),
                stop_loss=(
                    prices[-1] * 0.99
                    if pattern_type == "bullish_flag"
                    else prices[-1] * 1.01
                ),
                description=f"{pattern_type.replace('_', ' ').title()} pattern detected",
            )

        return None

    def _detect_wedge_patterns(self, data: List[Dict]) -> Optional[PatternSignal]:
        """Detect wedge patterns (rising/falling wedges)"""
        # Simplified wedge detection
        prices = [d["close"] for d in data[-50:]]

        if len(prices) < 30:
            return None

        # Calculate converging trendlines
        highs = [d["high"] for d in data[-30:]]
        lows = [d["low"] for d in data[-30:]]

        x = np.arange(len(highs))
        high_slope = np.polyfit(x, highs, 1)[0]
        low_slope = np.polyfit(x, lows, 1)[0]

        # Check for converging lines
        if (high_slope > 0 and low_slope > 0 and high_slope > low_slope) or (
            high_slope < 0 and low_slope < 0 and high_slope < low_slope
        ):
            pattern_type = "rising_wedge" if high_slope > 0 else "falling_wedge"

            return PatternSignal(
                pattern_type=pattern_type,
                confidence=0.55,
                timeframe="4h",
                entry_price=prices[-1],
                targets=(
                    [prices[-1] * 0.95]
                    if pattern_type == "rising_wedge"
                    else [prices[-1] * 1.05]
                ),
                stop_loss=(
                    prices[-1] * 1.02
                    if pattern_type == "rising_wedge"
                    else prices[-1] * 0.98
                ),
                description=f"{pattern_type.replace('_', ' ').title()} pattern detected",
            )

        return None

    def _predict_trend_continuation(
        self, price_data: List[Dict], volume_data: List[Dict]
    ) -> PredictiveSignal:
        """Predict trend continuation"""
        prices = [d["close"] for d in price_data[-50:]]
        volumes = [d["volume"] for d in volume_data[-50:]]

        # Calculate trend strength
        price_change = (prices[-1] - prices[0]) / prices[0]
        volume_trend = np.polyfit(range(len(volumes)), volumes, 1)[0]

        # Simple ML-like prediction
        trend_strength = abs(price_change)
        volume_confirmation = 1 if volume_trend > 0 else -1

        probability = min(
            0.85, trend_strength * 2 + (0.1 if volume_confirmation > 0 else -0.1)
        )

        return PredictiveSignal(
            prediction_type="trend_continuation",
            probability=max(0.5, probability),
            time_horizon="12h",
            expected_move=price_change * 1.5,
            confidence_interval=(price_change * 0.8, price_change * 2.2),
            factors=["price_trend", "volume_confirmation", "momentum"],
        )

    def _predict_mean_reversion(self, price_data: List[Dict]) -> PredictiveSignal:
        """Predict mean reversion"""
        prices = [d["close"] for d in price_data[-100:]]

        # Calculate mean and standard deviation
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        current_price = prices[-1]

        # Calculate z-score
        z_score = (current_price - mean_price) / std_price

        # Predict reversion probability
        if abs(z_score) > 2:  # More than 2 standard deviations
            probability = min(0.80, abs(z_score) * 0.2)
            expected_move = -z_score * std_price * 0.5  # Partial reversion
        else:
            probability = 0.3
            expected_move = 0

        return PredictiveSignal(
            prediction_type="mean_reversion",
            probability=probability,
            time_horizon="6h",
            expected_move=expected_move,
            confidence_interval=(expected_move * 0.7, expected_move * 1.3),
            factors=["z_score", "historical_volatility", "price_deviation"],
        )

    def _predict_volatility(self, price_data: List[Dict]) -> PredictiveSignal:
        """Predict volatility"""
        prices = [d["close"] for d in price_data[-100:]]

        # Calculate historical volatility
        returns = np.diff(np.log(prices))
        current_vol = np.std(returns[-20:]) * np.sqrt(24)  # Daily vol
        historical_vol = np.std(returns) * np.sqrt(24)

        # Predict future volatility
        vol_ratio = current_vol / historical_vol

        if vol_ratio > 1.5:  # High volatility regime
            predicted_vol = current_vol * 0.8  # Mean reversion
        elif vol_ratio < 0.5:  # Low volatility regime
            predicted_vol = current_vol * 1.3  # Volatility expansion
        else:
            predicted_vol = current_vol

        return PredictiveSignal(
            prediction_type="volatility_forecast",
            probability=0.70,
            time_horizon="24h",
            expected_move=predicted_vol,
            confidence_interval=(predicted_vol * 0.8, predicted_vol * 1.2),
            factors=["current_volatility", "volatility_regime", "historical_patterns"],
        )

    def _predict_price_target(
        self, price_data: List[Dict], sentiment_data: Dict
    ) -> PredictiveSignal:
        """Predict price target using multiple factors"""
        prices = [d["close"] for d in price_data[-50:]]
        current_price = prices[-1]

        # Technical factors
        resistance = max(prices[-20:])
        support = min(prices[-20:])

        # Sentiment adjustment
        sentiment_adjustment = sentiment_data.get("score", 0) * 0.1

        # Calculate target
        if current_price > (resistance + support) / 2:
            target = resistance + (resistance - support) * 0.5 + sentiment_adjustment
        else:
            target = support - (resistance - support) * 0.3 + sentiment_adjustment

        expected_move = (target - current_price) / current_price

        return PredictiveSignal(
            prediction_type="price_target",
            probability=0.65,
            time_horizon="48h",
            expected_move=expected_move,
            confidence_interval=(expected_move * 0.7, expected_move * 1.3),
            factors=["support_resistance", "sentiment", "price_position"],
        )

    def _aggregate_predictions(self, predictions: List[PredictiveSignal]) -> Dict:
        """Aggregate multiple predictions into consensus"""
        if not predictions:
            return {"prediction": "neutral", "confidence": 0, "expected_move": 0}

        # Weight predictions by probability
        total_weight = sum(p.probability for p in predictions)
        if total_weight == 0:
            return {"prediction": "neutral", "confidence": 0, "expected_move": 0}

        weighted_move = (
            sum(p.expected_move * p.probability for p in predictions) / total_weight
        )
        avg_confidence = sum(p.probability for p in predictions) / len(predictions)

        # Determine consensus direction
        if weighted_move > 0.02:
            prediction = "bullish"
        elif weighted_move < -0.02:
            prediction = "bearish"
        else:
            prediction = "neutral"

        return {
            "prediction": prediction,
            "confidence": avg_confidence,
            "expected_move": weighted_move,
            "factors_consensus": list(set([f for p in predictions for f in p.factors])),
        }

    async def _get_social_sentiment(self, symbol: str) -> Dict:
        """Get social media sentiment"""
        # Mock social sentiment
        return {
            "source": "social_media",
            "sentiment": np.random.choice(["bullish", "bearish", "neutral"]),
            "score": np.random.uniform(-1, 1),
            "confidence": np.random.uniform(0.6, 0.9),
            "mentions": np.random.randint(100, 1000),
        }

    async def _get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment"""
        # Mock news sentiment
        return {
            "source": "news",
            "sentiment": np.random.choice(["bullish", "bearish", "neutral"]),
            "score": np.random.uniform(-1, 1),
            "confidence": np.random.uniform(0.7, 0.95),
            "articles": np.random.randint(5, 50),
        }

    async def _get_orderbook_sentiment(self, symbol: str) -> Dict:
        """Get orderbook sentiment"""
        # Mock orderbook sentiment
        bid_ask_ratio = np.random.uniform(0.8, 1.2)
        sentiment = (
            "bullish"
            if bid_ask_ratio > 1.1
            else "bearish" if bid_ask_ratio < 0.9 else "neutral"
        )

        return {
            "source": "orderbook",
            "sentiment": sentiment,
            "score": (bid_ask_ratio - 1) * 2,  # Scale to -1 to 1
            "confidence": 0.8,
            "bid_ask_ratio": bid_ask_ratio,
        }

    async def _get_funding_sentiment(self, symbol: str) -> Dict:
        """Get funding rate sentiment"""
        # Mock funding sentiment
        funding_rate = np.random.uniform(-0.01, 0.01)
        sentiment = (
            "bullish"
            if funding_rate < -0.005
            else "bearish" if funding_rate > 0.005 else "neutral"
        )

        return {
            "source": "funding_rate",
            "sentiment": sentiment,
            "score": -funding_rate * 100,  # Inverse: negative funding = bullish
            "confidence": 0.75,
            "funding_rate": funding_rate,
        }

    def _aggregate_sentiment(self, sources: List[Dict]) -> Dict:
        """Aggregate sentiment from multiple sources"""
        if not sources:
            return {"sentiment": "neutral", "score": 0, "confidence": 0}

        # Weight by confidence
        total_weight = sum(s.get("confidence", 0.5) for s in sources)
        if total_weight == 0:
            return {"sentiment": "neutral", "score": 0, "confidence": 0}

        weighted_score = (
            sum(s.get("score", 0) * s.get("confidence", 0.5) for s in sources)
            / total_weight
        )
        avg_confidence = sum(s.get("confidence", 0.5) for s in sources) / len(sources)

        # Determine sentiment
        if weighted_score > 0.2:
            sentiment = "bullish"
        elif weighted_score < -0.2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": weighted_score,
            "confidence": avg_confidence,
            "sources_count": len(sources),
        }

    async def _get_orderbook_data(self, symbol: str) -> Dict:
        """Get orderbook data"""
        # Mock orderbook data
        return {
            "bids": [[50000 - i * 10, i * 100] for i in range(10)],
            "asks": [[50010 + i * 10, i * 100] for i in range(10)],
            "spread": 10,
            "bid_volume": 5500,
            "ask_volume": 5500,
        }

    def _detect_volume_anomaly(self, volume_data: List[Dict]) -> Optional[Dict]:
        """Detect volume spike anomalies"""
        if len(volume_data) < 20:
            return None

        volumes = [d["volume"] for d in volume_data[-20:]]
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[:-1])

        if current_volume > avg_volume * 3:  # 3x volume spike
            return {
                "type": "volume_spike",
                "severity": "high" if current_volume > avg_volume * 5 else "medium",
                "current_volume": current_volume,
                "average_volume": avg_volume,
                "ratio": current_volume / avg_volume,
                "description": f"Unusual volume spike detected: {current_volume/avg_volume:.1f}x normal volume",
            }

        return None

    def _detect_price_gap(self, price_data: List[Dict]) -> Optional[Dict]:
        """Detect price gap anomalies"""
        if len(price_data) < 2:
            return None

        prev_close = price_data[-2]["close"]
        curr_open = price_data[-1]["open"]

        gap_percentage = abs(curr_open - prev_close) / prev_close

        if gap_percentage > 0.02:  # 2% gap
            return {
                "type": "price_gap",
                "severity": "high" if gap_percentage > 0.05 else "medium",
                "gap_size": gap_percentage,
                "direction": "up" if curr_open > prev_close else "down",
                "description": f"Price gap detected: {gap_percentage*100:.1f}% {'up' if curr_open > prev_close else 'down'}",
            }

        return None

    def _detect_orderbook_anomaly(self, orderbook_data: Dict) -> Optional[Dict]:
        """Detect orderbook imbalance anomalies"""
        bid_volume = sum(bid[1] for bid in orderbook_data.get("bids", []))
        ask_volume = sum(ask[1] for ask in orderbook_data.get("asks", []))

        if bid_volume == 0 or ask_volume == 0:
            return None

        imbalance = abs(bid_volume - ask_volume) / (bid_volume + ask_volume)

        if imbalance > 0.7:  # 70% imbalance
            return {
                "type": "orderbook_imbalance",
                "severity": "high" if imbalance > 0.8 else "medium",
                "imbalance_ratio": imbalance,
                "bid_volume": bid_volume,
                "ask_volume": ask_volume,
                "direction": (
                    "bid_dominant" if bid_volume > ask_volume else "ask_dominant"
                ),
                "description": f"Orderbook imbalance: {imbalance*100:.1f}% {'bid' if bid_volume > ask_volume else 'ask'} dominant",
            }

        return None

    def _detect_volatility_anomaly(self, price_data: List[Dict]) -> Optional[Dict]:
        """Detect volatility spike anomalies"""
        if len(price_data) < 50:
            return None

        # Calculate recent vs historical volatility
        recent_prices = [d["close"] for d in price_data[-10:]]
        historical_prices = [d["close"] for d in price_data[-50:-10]]

        recent_vol = np.std(np.diff(np.log(recent_prices)))
        historical_vol = np.std(np.diff(np.log(historical_prices)))

        if historical_vol == 0:
            return None

        vol_ratio = recent_vol / historical_vol

        if vol_ratio > 2:  # 2x volatility spike
            return {
                "type": "volatility_spike",
                "severity": "high" if vol_ratio > 3 else "medium",
                "volatility_ratio": vol_ratio,
                "recent_volatility": recent_vol,
                "historical_volatility": historical_vol,
                "description": f"Volatility spike detected: {vol_ratio:.1f}x normal volatility",
            }

        return None

    def _calculate_risk_level(self, anomalies: List[Dict]) -> str:
        """Calculate overall risk level from anomalies"""
        if not anomalies:
            return "low"

        high_severity = sum(1 for a in anomalies if a.get("severity") == "high")
        medium_severity = sum(1 for a in anomalies if a.get("severity") == "medium")

        if high_severity >= 2 or (high_severity >= 1 and medium_severity >= 2):
            return "high"
        elif high_severity >= 1 or medium_severity >= 3:
            return "medium"
        else:
            return "low"

    def _pattern_to_dict(self, pattern: PatternSignal) -> Dict:
        """Convert PatternSignal to dict"""
        return {
            "pattern_type": pattern.pattern_type,
            "confidence": pattern.confidence,
            "timeframe": pattern.timeframe,
            "entry_price": pattern.entry_price,
            "targets": pattern.targets,
            "stop_loss": pattern.stop_loss,
            "description": pattern.description,
        }

    def _prediction_to_dict(self, prediction: PredictiveSignal) -> Dict:
        """Convert PredictiveSignal to dict"""
        return {
            "prediction_type": prediction.prediction_type,
            "probability": prediction.probability,
            "time_horizon": prediction.time_horizon,
            "expected_move": prediction.expected_move,
            "confidence_interval": prediction.confidence_interval,
            "factors": prediction.factors,
        }


# Global instance
advanced_analytics_service = AdvancedAnalyticsService()

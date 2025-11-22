"""
Reversal Detector Service
Detects technical reversal patterns that indicate potential pump beginnings

Features:
- Double Bottom Pattern Detection
- RSI Bullish Divergence Detection
- MACD Crossover Detection
- Support Level Bounce Detection

Author: CryptoSat Intelligence Pre-Pump Detection Engine
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService
from app.utils.logger import logger


class ReversalDetector:
    """Detects technical reversal patterns indicating potential upward movement"""

    def __init__(self, coinapi_service: Optional[CoinAPIComprehensiveService] = None):
        self.coinapi = coinapi_service or CoinAPIComprehensiveService()

    async def detect_reversal(self, symbol: str) -> Dict:
        """
        Main reversal detection method

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')

        Returns:
            Dict with reversal score, signals, and verdict
        """
        try:
            logger.info(f"[ReversalDetector] Analyzing {symbol} for reversal patterns")

            # Run all detection methods in parallel
            signals = await asyncio.gather(
                self.detect_double_bottom(symbol),
                self.detect_rsi_divergence(symbol),
                self.detect_macd_crossover(symbol),
                self.detect_support_bounce(symbol),
                return_exceptions=True
            )

            # Unpack results
            double_bottom = signals[0] if not isinstance(signals[0], Exception) else {"score": 0, "detected": False}
            rsi_divergence = signals[1] if not isinstance(signals[1], Exception) else {"score": 0, "detected": False}
            macd_crossover = signals[2] if not isinstance(signals[2], Exception) else {"score": 0, "detected": False}
            support_bounce = signals[3] if not isinstance(signals[3], Exception) else {"score": 0, "detected": False}

            # Calculate final reversal score
            result = self.calculate_reversal_score({
                "doubleBottom": double_bottom,
                "rsiDivergence": rsi_divergence,
                "macdCrossover": macd_crossover,
                "supportBounce": support_bounce
            })

            logger.info(f"[ReversalDetector] {symbol} reversal score: {result['score']}/100")
            return result

        except Exception as e:
            logger.error(f"[ReversalDetector] Error analyzing {symbol}: {e}")
            return {
                "score": 0,
                "verdict": "ERROR",
                "details": {},
                "error": str(e)
            }

    async def detect_double_bottom(self, symbol: str) -> Dict:
        """
        Detect double bottom pattern (W-shaped pattern)
        Two similar lows followed by price increase = bullish reversal
        """
        try:
            # Get 4-hour candles for pattern detection
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period="4HRS",
                limit=100
            )

            if not ohlcv_data.get("success"):
                return {"detected": False, "score": 0, "signal": "NO_DATA"}

            candles = ohlcv_data.get("data", [])
            if len(candles) < 20:
                return {"detected": False, "score": 0, "signal": "INSUFFICIENT_DATA"}

            # Find local minima (lows)
            minima = []
            for i in range(2, len(candles) - 2):
                current_low = candles[i].get("price_low", 0)
                prev2_low = candles[i-2].get("price_low", float('inf'))
                prev1_low = candles[i-1].get("price_low", float('inf'))
                next1_low = candles[i+1].get("price_low", float('inf'))
                next2_low = candles[i+2].get("price_low", float('inf'))

                # Local minimum: lower than surrounding candles
                if (current_low > 0 and
                    current_low < prev2_low and
                    current_low < prev1_low and
                    current_low < next1_low and
                    current_low < next2_low):
                    minima.append({"index": i, "price": current_low})

            # Check for double bottom (2 similar lows)
            if len(minima) >= 2:
                last_two = minima[-2:]
                price1 = last_two[0]["price"]
                price2 = last_two[1]["price"]

                # Calculate price difference
                price_diff = abs(price1 - price2) / price1

                # If difference < 3%, it's a double bottom
                if price_diff < 0.03:
                    return {
                        "detected": True,
                        "score": 100,
                        "signal": "DOUBLE_BOTTOM_CONFIRMED",
                        "bottomPrice": round((price1 + price2) / 2, 2),
                        "priceDifference": round(price_diff * 100, 2)
                    }

            return {
                "detected": False,
                "score": 0,
                "signal": "NO_PATTERN",
                "minimaFound": len(minima)
            }

        except Exception as e:
            logger.error(f"[ReversalDetector] Double bottom error for {symbol}: {e}")
            return {"detected": False, "score": 0, "signal": "ERROR"}

    async def detect_rsi_divergence(self, symbol: str) -> Dict:
        """
        Detect RSI bullish divergence
        Price making lower lows, RSI making higher lows = reversal signal
        """
        try:
            # Get 1-hour candles for RSI calculation
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period="1HRS",
                limit=50
            )

            if not ohlcv_data.get("success"):
                return {"detected": False, "score": 0, "signal": "NO_DATA"}

            candles = ohlcv_data.get("data", [])
            if len(candles) < 30:
                return {"detected": False, "score": 0, "signal": "INSUFFICIENT_DATA"}

            # Calculate RSI
            rsi_values = self.calculate_rsi(candles, period=14)
            prices = [c.get("price_close", 0) for c in candles]

            if len(rsi_values) < 20 or len(prices) < 20:
                return {"detected": False, "score": 0, "signal": "INSUFFICIENT_DATA"}

            # Check for bullish divergence in last 20 periods
            price_ll = self.is_lower_lows(prices[-20:])
            rsi_hl = self.is_higher_lows(rsi_values[-20:])

            current_rsi = rsi_values[-1] if rsi_values else 50

            if price_ll and rsi_hl:
                return {
                    "detected": True,
                    "score": 100,
                    "signal": "BULLISH_DIVERGENCE",
                    "currentRSI": round(current_rsi, 2)
                }

            return {
                "detected": False,
                "score": 0,
                "signal": "NO_DIVERGENCE",
                "currentRSI": round(current_rsi, 2)
            }

        except Exception as e:
            logger.error(f"[ReversalDetector] RSI divergence error for {symbol}: {e}")
            return {"detected": False, "score": 0, "signal": "ERROR"}

    def calculate_rsi(self, candles: List[Dict], period: int = 14) -> List[float]:
        """Calculate RSI (Relative Strength Index)"""
        try:
            # Calculate price changes
            changes = []
            for i in range(1, len(candles)):
                close_current = candles[i].get("price_close", 0)
                close_prev = candles[i-1].get("price_close", 0)
                if close_prev != 0:
                    changes.append(close_current - close_prev)

            if len(changes) < period:
                return []

            rsi = []
            for i in range(period, len(changes)):
                gains = []
                losses = []

                for j in range(i - period, i):
                    if changes[j] > 0:
                        gains.append(changes[j])
                    elif changes[j] < 0:
                        losses.append(abs(changes[j]))

                avg_gain = sum(gains) / period if gains else 0
                avg_loss = sum(losses) / period if losses else 0.00001  # Avoid division by zero

                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
                rsi.append(rsi_value)

            return rsi

        except Exception as e:
            logger.error(f"[ReversalDetector] RSI calculation error: {e}")
            return []

    def is_lower_lows(self, data: List[float]) -> bool:
        """Check if data shows lower lows pattern"""
        try:
            minima = self.find_local_minima(data)
            if len(minima) < 2:
                return False
            return minima[-1] < minima[-2]
        except:
            return False

    def is_higher_lows(self, data: List[float]) -> bool:
        """Check if data shows higher lows pattern"""
        try:
            minima = self.find_local_minima(data)
            if len(minima) < 2:
                return False
            return minima[-1] > minima[-2]
        except:
            return False

    def find_local_minima(self, data: List[float]) -> List[float]:
        """Find local minimum points in data"""
        minima = []
        for i in range(1, len(data) - 1):
            if data[i] < data[i-1] and data[i] < data[i+1]:
                minima.append(data[i])
        return minima

    async def detect_macd_crossover(self, symbol: str) -> Dict:
        """
        Detect MACD bullish crossover
        MACD line crossing above signal line = bullish
        """
        try:
            # Get 1-hour candles for MACD calculation
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period="1HRS",
                limit=100
            )

            if not ohlcv_data.get("success"):
                return {"detected": False, "score": 0, "signal": "NO_DATA"}

            candles = ohlcv_data.get("data", [])
            if len(candles) < 50:
                return {"detected": False, "score": 0, "signal": "INSUFFICIENT_DATA"}

            # Extract closing prices
            closes = [c.get("price_close", 0) for c in candles if c.get("price_close", 0) > 0]

            if len(closes) < 50:
                return {"detected": False, "score": 0, "signal": "INSUFFICIENT_DATA"}

            # Calculate MACD
            ema12 = self.calculate_ema(closes, 12)
            ema26 = self.calculate_ema(closes, 26)

            if len(ema12) != len(ema26):
                return {"detected": False, "score": 0, "signal": "CALCULATION_ERROR"}

            macd_line = [ema12[i] - ema26[i] for i in range(len(ema12))]
            signal_line = self.calculate_ema(macd_line, 9)

            if len(signal_line) < 2:
                return {"detected": False, "score": 0, "signal": "INSUFFICIENT_DATA"}

            # Check for bullish crossover (MACD crosses above signal)
            current_diff = macd_line[-1] - signal_line[-1]
            previous_diff = macd_line[-2] - signal_line[-2]

            # Bullish crossover: current > 0 and previous <= 0
            if current_diff > 0 and previous_diff <= 0:
                return {
                    "detected": True,
                    "score": 100,
                    "signal": "MACD_BULLISH_CROSS",
                    "macd": round(macd_line[-1], 6)
                }

            # MACD positive but no crossover
            if current_diff > 0:
                return {
                    "detected": False,
                    "score": 50,
                    "signal": "MACD_POSITIVE",
                    "macd": round(macd_line[-1], 6)
                }

            return {
                "detected": False,
                "score": 0,
                "signal": "MACD_NEGATIVE",
                "macd": round(macd_line[-1], 6)
            }

        except Exception as e:
            logger.error(f"[ReversalDetector] MACD crossover error for {symbol}: {e}")
            return {"detected": False, "score": 0, "signal": "ERROR"}

    def calculate_ema(self, data: List[float], period: int) -> List[float]:
        """Calculate EMA (Exponential Moving Average)"""
        try:
            if len(data) < period:
                return []

            k = 2 / (period + 1)
            ema = [data[0]]

            for i in range(1, len(data)):
                ema.append(data[i] * k + ema[i-1] * (1 - k))

            return ema
        except Exception as e:
            logger.error(f"[ReversalDetector] EMA calculation error: {e}")
            return []

    async def detect_support_bounce(self, symbol: str) -> Dict:
        """
        Detect price bounce from support level
        Price approaching and bouncing from support = reversal
        """
        try:
            # Get 4-hour candles for support level detection
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period="4HRS",
                limit=100
            )

            if not ohlcv_data.get("success"):
                return {"detected": False, "score": 0, "signal": "NO_DATA"}

            candles = ohlcv_data.get("data", [])
            if len(candles) < 30:
                return {"detected": False, "score": 0, "signal": "INSUFFICIENT_DATA"}

            # Extract lows
            lows = [c.get("price_low", 0) for c in candles if c.get("price_low", 0) > 0]
            current_price = candles[-1].get("price_close", 0)

            if not lows or current_price == 0:
                return {"detected": False, "score": 0, "signal": "NO_DATA"}

            # Find support level (most common low price area)
            support = self.find_support_level(lows)

            # Check if price bounced from support
            distance_from_support = (current_price - support) / support

            # Price within 5% above support = bounce signal
            if 0 < distance_from_support < 0.05:
                return {
                    "detected": True,
                    "score": 100,
                    "signal": "SUPPORT_BOUNCE",
                    "supportLevel": round(support, 2),
                    "currentPrice": round(current_price, 2),
                    "distanceFromSupport": round(distance_from_support * 100, 2)
                }

            return {
                "detected": False,
                "score": 0,
                "signal": "NO_BOUNCE",
                "supportLevel": round(support, 2),
                "currentPrice": round(current_price, 2)
            }

        except Exception as e:
            logger.error(f"[ReversalDetector] Support bounce error for {symbol}: {e}")
            return {"detected": False, "score": 0, "signal": "ERROR"}

    def find_support_level(self, lows: List[float]) -> float:
        """
        Find support level by grouping prices into buckets
        and finding the most common price area
        """
        try:
            if not lows:
                return 0

            sorted_lows = sorted(lows)
            min_price = sorted_lows[0]
            max_price = sorted_lows[-1]

            if min_price == max_price:
                return min_price

            bucket_size = (max_price - min_price) / 20

            # Group prices into buckets
            buckets = {}
            for low in lows:
                bucket = int((low - min_price) / bucket_size) if bucket_size > 0 else 0
                buckets[bucket] = buckets.get(bucket, 0) + 1

            # Find bucket with most occurrences
            max_bucket = max(buckets.items(), key=lambda x: x[1])[0]

            # Return mid-point of that bucket
            support = min_price + (max_bucket * bucket_size)
            return support

        except Exception as e:
            logger.error(f"[ReversalDetector] Support level calculation error: {e}")
            return min(lows) if lows else 0

    def calculate_reversal_score(self, signals: Dict) -> Dict:
        """
        Calculate weighted reversal score from all signals

        Args:
            signals: Dict with doubleBottom, rsiDivergence, macdCrossover, supportBounce

        Returns:
            Final reversal score and verdict
        """
        # Weighted scoring
        weights = {
            "doubleBottom": 0.35,
            "rsiDivergence": 0.30,
            "macdCrossover": 0.20,
            "supportBounce": 0.15
        }

        total_score = (
            signals["doubleBottom"]["score"] * weights["doubleBottom"] +
            signals["rsiDivergence"]["score"] * weights["rsiDivergence"] +
            signals["macdCrossover"]["score"] * weights["macdCrossover"] +
            signals["supportBounce"]["score"] * weights["supportBounce"]
        )

        # Determine verdict
        if total_score > 70:
            verdict = "STRONG_REVERSAL"
        elif total_score > 50:
            verdict = "MODERATE_REVERSAL"
        else:
            verdict = "WEAK_REVERSAL"

        return {
            "score": round(total_score),
            "details": signals,
            "verdict": verdict,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def close(self):
        """Close service connections"""
        await self.coinapi.close()

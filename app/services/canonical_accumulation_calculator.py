"""
Canonical Accumulation/Distribution Calculator
===============================================

SINGLE SOURCE OF TRUTH untuk semua accumulation/distribution calculations.
Semua service lain HARUS use calculator ini untuk konsistensi.

Author: CryptoSatX Intelligence Engine
Version: 1.0.0
"""

import asyncio
from typing import Dict, List, Optional, Literal
from datetime import datetime
from dataclasses import dataclass
from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService
from app.utils.logger import logger


@dataclass
class AccumulationResult:
    """Canonical result structure untuk accumulation analysis"""

    # Core scores (0-100 scale)
    accumulation_score: float  # 0-100
    distribution_score: float  # 0-100

    # Verdict
    verdict: Literal[
        "STRONG_ACCUMULATION",
        "MODERATE_ACCUMULATION",
        "WEAK_ACCUMULATION",
        "NEUTRAL",
        "WEAK_DISTRIBUTION",
        "MODERATE_DISTRIBUTION",
        "STRONG_DISTRIBUTION"
    ]

    # Dominant pattern
    dominant_pattern: Literal["accumulation", "distribution", "neutral"]

    # Detailed breakdown
    details: Dict

    # Metadata
    timestamp: str
    symbol: str
    timeframe: str

    # Alternative scales (untuk backward compatibility)
    @property
    def accumulation_score_10(self) -> float:
        """Convert to 0-10 scale untuk SmartMoneyService compatibility"""
        return round(self.accumulation_score / 10, 1)

    @property
    def distribution_score_10(self) -> float:
        """Convert to 0-10 scale untuk SmartMoneyService compatibility"""
        return round(self.distribution_score / 10, 1)


class CanonicalAccumulationCalculator:
    """
    Canonical calculator untuk accumulation/distribution analysis.

    SEMUA service lain harus use calculator ini untuk konsistensi:
    - AccumulationDetector
    - SmartMoneyService
    - PrePumpEngine
    - Signal Engine

    Features:
    - Unified scoring system (0-100 base, convertible to 0-10)
    - Comprehensive 4-pillar analysis
    - Support untuk multiple data sources
    - Consistent verdict thresholds
    - Version tracking
    """

    VERSION = "1.0.0"

    # Scoring weights (total = 1.0)
    WEIGHTS = {
        "volume_profile": 0.30,      # Buy vs sell volume
        "consolidation": 0.25,        # Low volatility (sideways)
        "sell_pressure": 0.25,        # Decreasing sell volume
        "order_book_depth": 0.20      # Bid/ask ratios, buy walls
    }

    # Accumulation verdict thresholds (0-100 scale)
    ACCUMULATION_THRESHOLDS = {
        "strong": 75,      # >= 75 = STRONG_ACCUMULATION
        "moderate": 60,    # >= 60 = MODERATE_ACCUMULATION
        "weak": 40         # >= 40 = WEAK_ACCUMULATION
    }

    # Distribution verdict thresholds (0-100 scale)
    DISTRIBUTION_THRESHOLDS = {
        "strong": 75,      # >= 75 = STRONG_DISTRIBUTION
        "moderate": 60,    # >= 60 = MODERATE_DISTRIBUTION
        "weak": 40         # >= 40 = WEAK_DISTRIBUTION
    }

    def __init__(self, coinapi_service: Optional[CoinAPIComprehensiveService] = None):
        self.coinapi = coinapi_service or CoinAPIComprehensiveService()
        logger.info(f"✅ CanonicalAccumulationCalculator initialized (v{self.VERSION})")

    async def calculate(
        self,
        symbol: str,
        timeframe: str = "1HRS",
        additional_data: Optional[Dict] = None
    ) -> AccumulationResult:
        """
        Main calculation method - CANONICAL ACCUMULATION/DISTRIBUTION ANALYSIS

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            timeframe: Time period (1MIN, 5MIN, 1HRS, 1DAY)
            additional_data: Optional pre-fetched data (untuk optimization)

        Returns:
            AccumulationResult with scores, verdict, and details
        """
        try:
            logger.info(f"[Canonical] Analyzing {symbol} on {timeframe}")

            # Run all 4 pillars in parallel
            pillars = await asyncio.gather(
                self._analyze_volume_profile(symbol, timeframe, additional_data),
                self._analyze_consolidation(symbol, timeframe, additional_data),
                self._analyze_sell_pressure(symbol, timeframe, additional_data),
                self._analyze_order_book(symbol, additional_data),
                return_exceptions=True
            )

            # Unpack with error handling
            volume_profile = pillars[0] if not isinstance(pillars[0], Exception) else self._default_pillar()
            consolidation = pillars[1] if not isinstance(pillars[1], Exception) else self._default_pillar()
            sell_pressure = pillars[2] if not isinstance(pillars[2], Exception) else self._default_pillar()
            order_book = pillars[3] if not isinstance(pillars[3], Exception) else self._default_pillar()

            # Calculate weighted accumulation score
            accumulation_score = (
                volume_profile["accumulation_score"] * self.WEIGHTS["volume_profile"] +
                consolidation["accumulation_score"] * self.WEIGHTS["consolidation"] +
                sell_pressure["accumulation_score"] * self.WEIGHTS["sell_pressure"] +
                order_book["accumulation_score"] * self.WEIGHTS["order_book_depth"]
            )

            # Calculate weighted distribution score
            distribution_score = (
                volume_profile["distribution_score"] * self.WEIGHTS["volume_profile"] +
                consolidation["distribution_score"] * self.WEIGHTS["consolidation"] +
                sell_pressure["distribution_score"] * self.WEIGHTS["sell_pressure"] +
                order_book["distribution_score"] * self.WEIGHTS["order_book_depth"]
            )

            # Determine verdict and dominant pattern
            verdict, dominant_pattern = self._determine_verdict(
                accumulation_score,
                distribution_score
            )

            # Build result
            result = AccumulationResult(
                accumulation_score=round(accumulation_score, 2),
                distribution_score=round(distribution_score, 2),
                verdict=verdict,
                dominant_pattern=dominant_pattern,
                details={
                    "pillars": {
                        "volume_profile": volume_profile,
                        "consolidation": consolidation,
                        "sell_pressure": sell_pressure,
                        "order_book_depth": order_book
                    },
                    "weights": self.WEIGHTS,
                    "version": self.VERSION
                },
                timestamp=datetime.utcnow().isoformat(),
                symbol=symbol,
                timeframe=timeframe
            )

            logger.info(
                f"[Canonical] {symbol}: "
                f"Accum={result.accumulation_score:.1f}, "
                f"Dist={result.distribution_score:.1f}, "
                f"Verdict={verdict}"
            )

            return result

        except Exception as e:
            logger.error(f"[Canonical] Error analyzing {symbol}: {e}")
            return self._error_result(symbol, timeframe, str(e))

    async def _analyze_volume_profile(
        self,
        symbol: str,
        timeframe: str,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Pillar 1: Volume Profile Analysis

        Accumulation: High buy volume (>55% buy pressure)
        Distribution: High sell volume (>55% sell pressure)
        """
        try:
            # Get OHLCV data
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period=timeframe,
                limit=100
            )

            if not ohlcv_data.get("success"):
                return self._default_pillar()

            candles = ohlcv_data.get("data", [])
            if len(candles) < 10:
                return self._default_pillar()

            buy_volume = 0
            sell_volume = 0

            # Calculate buy vs sell volume
            for candle in candles:
                close = candle.get("price_close", 0)
                open_price = candle.get("price_open", 0)
                volume = candle.get("volume_traded", 0)

                if close > open_price:  # Bullish = buy volume
                    buy_volume += volume
                else:  # Bearish = sell volume
                    sell_volume += volume

            total_volume = buy_volume + sell_volume
            if total_volume == 0:
                return self._default_pillar()

            buy_pressure = buy_volume / total_volume
            sell_pressure = sell_volume / total_volume

            # Score accumulation (buy pressure)
            if buy_pressure > 0.55:
                accumulation_score = 100
            else:
                accumulation_score = buy_pressure * 100

            # Score distribution (sell pressure)
            if sell_pressure > 0.55:
                distribution_score = 100
            else:
                distribution_score = sell_pressure * 100

            return {
                "accumulation_score": round(accumulation_score, 2),
                "distribution_score": round(distribution_score, 2),
                "buy_pressure": round(buy_pressure, 3),
                "sell_pressure": round(sell_pressure, 3),
                "buy_volume": round(buy_volume, 2),
                "sell_volume": round(sell_volume, 2),
                "signal": "BULLISH" if buy_pressure > 0.55 else "BEARISH" if sell_pressure > 0.55 else "NEUTRAL"
            }

        except Exception as e:
            logger.error(f"[Canonical] Volume profile error: {e}")
            return self._default_pillar()

    async def _analyze_consolidation(
        self,
        symbol: str,
        timeframe: str,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Pillar 2: Consolidation Detection

        Accumulation: Low volatility (consolidation phase)
        Distribution: High volatility (breakout/breakdown)
        """
        try:
            # Get price data
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period=timeframe,
                limit=72
            )

            if not ohlcv_data.get("success"):
                return self._default_pillar()

            candles = ohlcv_data.get("data", [])
            if len(candles) < 20:
                return self._default_pillar()

            # Extract prices
            prices = [c.get("price_close", 0) for c in candles if c.get("price_close")]

            if len(prices) < 20:
                return self._default_pillar()

            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] != 0:
                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(ret)

            if not returns:
                return self._default_pillar()

            # Calculate volatility
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5

            # Score: Low volatility = accumulation, High volatility = distribution
            is_consolidating = volatility < 0.02  # <2% volatility

            if is_consolidating:
                accumulation_score = 100
                distribution_score = 0
            else:
                # Higher volatility = more distribution
                accumulation_score = max(0, 100 - (volatility * 5000))  # Scale volatility
                distribution_score = min(100, volatility * 5000)

            return {
                "accumulation_score": round(accumulation_score, 2),
                "distribution_score": round(distribution_score, 2),
                "volatility": round(volatility, 4),
                "is_consolidating": is_consolidating,
                "signal": "CONSOLIDATING" if is_consolidating else "VOLATILE"
            }

        except Exception as e:
            logger.error(f"[Canonical] Consolidation error: {e}")
            return self._default_pillar()

    async def _analyze_sell_pressure(
        self,
        symbol: str,
        timeframe: str,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Pillar 3: Sell Pressure Analysis

        Accumulation: Low sell pressure (<45%)
        Distribution: High sell pressure (>55%)
        """
        try:
            # Get OHLCV data
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period=timeframe,
                limit=50
            )

            if not ohlcv_data.get("success"):
                return self._default_pillar()

            candles = ohlcv_data.get("data", [])
            if len(candles) < 10:
                return self._default_pillar()

            sell_candles = 0
            buy_candles = 0
            sell_volume = 0
            buy_volume = 0

            for candle in candles:
                close = candle.get("price_close", 0)
                open_price = candle.get("price_open", 0)
                volume = candle.get("volume_traded", 0)

                if close < open_price:  # Bearish
                    sell_candles += 1
                    sell_volume += volume
                else:  # Bullish
                    buy_candles += 1
                    buy_volume += volume

            total_volume = buy_volume + sell_volume
            if total_volume == 0:
                return self._default_pillar()

            sell_pressure_ratio = sell_volume / total_volume

            # Score: Low sell = accumulation, High sell = distribution
            if sell_pressure_ratio < 0.45:
                accumulation_score = 100
                distribution_score = sell_pressure_ratio * 100
            elif sell_pressure_ratio > 0.55:
                accumulation_score = (1 - sell_pressure_ratio) * 100
                distribution_score = 100
            else:
                accumulation_score = 50
                distribution_score = 50

            return {
                "accumulation_score": round(accumulation_score, 2),
                "distribution_score": round(distribution_score, 2),
                "sell_pressure_ratio": round(sell_pressure_ratio, 3),
                "sell_candles": sell_candles,
                "buy_candles": buy_candles,
                "signal": "DECREASING_SELL" if sell_pressure_ratio < 0.45 else "HIGH_SELL" if sell_pressure_ratio > 0.55 else "NEUTRAL"
            }

        except Exception as e:
            logger.error(f"[Canonical] Sell pressure error: {e}")
            return self._default_pillar()

    async def _analyze_order_book(
        self,
        symbol: str,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Pillar 4: Order Book Depth

        Accumulation: High bid/ask ratio (>1.2) + buy walls
        Distribution: Low bid/ask ratio (<0.8) + sell walls
        """
        try:
            # Get order book data
            orderbook_data = await self.coinapi.get_orderbook_latest(
                symbol=symbol,
                limit=20
            )

            if not orderbook_data.get("success"):
                return self._default_pillar()

            bids = orderbook_data.get("data", {}).get("bids", [])
            asks = orderbook_data.get("data", {}).get("asks", [])

            if not bids or not asks:
                return self._default_pillar()

            # Calculate total bid and ask value
            total_bids = sum(bid.get("price", 0) * bid.get("size", 0) for bid in bids)
            total_asks = sum(ask.get("price", 0) * ask.get("size", 0) for ask in asks)

            if total_asks == 0:
                return self._default_pillar()

            bid_ask_ratio = total_bids / total_asks

            # Detect buy walls
            avg_bid_size = total_bids / len(bids) if bids else 0
            buy_walls = sum(1 for bid in bids
                          if (bid.get("price", 0) * bid.get("size", 0)) > avg_bid_size * 3)

            # Detect sell walls
            avg_ask_size = total_asks / len(asks) if asks else 0
            sell_walls = sum(1 for ask in asks
                           if (ask.get("price", 0) * ask.get("size", 0)) > avg_ask_size * 3)

            # Score accumulation (high bid/ask + buy walls)
            if bid_ask_ratio > 1.2 and buy_walls > 0:
                accumulation_score = 100
            elif bid_ask_ratio > 1.0:
                accumulation_score = 70
            else:
                accumulation_score = 40

            # Score distribution (low bid/ask + sell walls)
            if bid_ask_ratio < 0.8 and sell_walls > 0:
                distribution_score = 100
            elif bid_ask_ratio < 1.0:
                distribution_score = 70
            else:
                distribution_score = 40

            return {
                "accumulation_score": accumulation_score,
                "distribution_score": distribution_score,
                "bid_ask_ratio": round(bid_ask_ratio, 3),
                "buy_walls": buy_walls,
                "sell_walls": sell_walls,
                "total_bids": round(total_bids, 2),
                "total_asks": round(total_asks, 2),
                "signal": "STRONG_BIDS" if bid_ask_ratio > 1.2 else "STRONG_ASKS" if bid_ask_ratio < 0.8 else "NEUTRAL"
            }

        except Exception as e:
            logger.error(f"[Canonical] Order book error: {e}")
            return self._default_pillar()

    def _determine_verdict(
        self,
        accumulation_score: float,
        distribution_score: float
    ) -> tuple[str, str]:
        """
        Determine verdict based on accumulation and distribution scores

        Returns:
            (verdict, dominant_pattern)
        """
        # Determine dominant pattern
        if accumulation_score > distribution_score + 10:
            dominant_pattern = "accumulation"

            # Determine accumulation strength
            if accumulation_score >= self.ACCUMULATION_THRESHOLDS["strong"]:
                verdict = "STRONG_ACCUMULATION"
            elif accumulation_score >= self.ACCUMULATION_THRESHOLDS["moderate"]:
                verdict = "MODERATE_ACCUMULATION"
            elif accumulation_score >= self.ACCUMULATION_THRESHOLDS["weak"]:
                verdict = "WEAK_ACCUMULATION"
            else:
                verdict = "NEUTRAL"
                dominant_pattern = "neutral"

        elif distribution_score > accumulation_score + 10:
            dominant_pattern = "distribution"

            # Determine distribution strength
            if distribution_score >= self.DISTRIBUTION_THRESHOLDS["strong"]:
                verdict = "STRONG_DISTRIBUTION"
            elif distribution_score >= self.DISTRIBUTION_THRESHOLDS["moderate"]:
                verdict = "MODERATE_DISTRIBUTION"
            elif distribution_score >= self.DISTRIBUTION_THRESHOLDS["weak"]:
                verdict = "WEAK_DISTRIBUTION"
            else:
                verdict = "NEUTRAL"
                dominant_pattern = "neutral"

        else:
            # Scores are close - neutral
            verdict = "NEUTRAL"
            dominant_pattern = "neutral"

        return verdict, dominant_pattern

    def _default_pillar(self) -> Dict:
        """Return neutral default pillar scores"""
        return {
            "accumulation_score": 50,
            "distribution_score": 50,
            "signal": "NO_DATA"
        }

    def _error_result(self, symbol: str, timeframe: str, error: str) -> AccumulationResult:
        """Return error result"""
        return AccumulationResult(
            accumulation_score=0,
            distribution_score=0,
            verdict="NEUTRAL",
            dominant_pattern="neutral",
            details={"error": error},
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            timeframe=timeframe
        )

    async def close(self):
        """Close service connections"""
        await self.coinapi.close()


# Global singleton instance
canonical_calculator = CanonicalAccumulationCalculator()

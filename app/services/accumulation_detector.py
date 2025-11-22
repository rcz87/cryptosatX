"""
Accumulation Detector Service
Detects accumulation phases before pump events

Features:
- Volume Profile Analysis (buy vs sell pressure)
- Price Consolidation Detection (low volatility)
- Sell Pressure Analysis (decreasing sells = bullish)
- Order Book Depth Analysis (bid/ask ratios, buy walls)

Author: CryptoSat Intelligence Pre-Pump Detection Engine
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService
from app.utils.logger import logger


class AccumulationDetector:
    """Detects accumulation patterns that indicate potential pumps"""

    def __init__(self, coinapi_service: Optional[CoinAPIComprehensiveService] = None):
        self.coinapi = coinapi_service or CoinAPIComprehensiveService()

    async def detect_accumulation(self, symbol: str, timeframe: str = "1HRS") -> Dict:
        """
        Main accumulation detection method

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')
            timeframe: Time period for analysis (1MIN, 5MIN, 1HRS, 1DAY)

        Returns:
            Dict with accumulation score, signals, and verdict
        """
        try:
            logger.info(f"[AccumulationDetector] Analyzing {symbol} on {timeframe} timeframe")

            # Run all detection methods in parallel
            signals = await asyncio.gather(
                self.analyze_volume_profile(symbol, timeframe),
                self.detect_consolidation(symbol, timeframe),
                self.analyze_sell_pressure(symbol, timeframe),
                self.analyze_order_book(symbol),
                return_exceptions=True
            )

            # Unpack results
            volume_profile = signals[0] if not isinstance(signals[0], Exception) else {"score": 50, "signal": "ERROR"}
            consolidation = signals[1] if not isinstance(signals[1], Exception) else {"score": 50, "signal": "ERROR"}
            sell_pressure = signals[2] if not isinstance(signals[2], Exception) else {"score": 50, "signal": "ERROR"}
            order_book = signals[3] if not isinstance(signals[3], Exception) else {"score": 50, "signal": "ERROR"}

            # Calculate final accumulation score
            result = self.calculate_accumulation_score({
                "volumeProfile": volume_profile,
                "consolidation": consolidation,
                "sellPressure": sell_pressure,
                "orderBookDepth": order_book
            })

            logger.info(f"[AccumulationDetector] {symbol} accumulation score: {result['score']}/100")
            return result

        except Exception as e:
            logger.error(f"[AccumulationDetector] Error analyzing {symbol}: {e}")
            return {
                "score": 0,
                "verdict": "ERROR",
                "details": {},
                "error": str(e)
            }

    async def analyze_volume_profile(self, symbol: str, timeframe: str = "1HRS") -> Dict:
        """
        Analyze buy vs sell volume pressure
        High buy volume = accumulation signal
        """
        try:
            # Get OHLCV data for the last 168 periods (7 days for 1HR)
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period=timeframe,
                limit=100
            )

            if not ohlcv_data.get("success"):
                return {"score": 50, "signal": "NO_DATA", "buyPressure": 0}

            candles = ohlcv_data.get("data", [])
            if len(candles) < 10:
                return {"score": 50, "signal": "INSUFFICIENT_DATA", "buyPressure": 0}

            buy_volume = 0
            sell_volume = 0

            # Calculate buy vs sell volume based on candle direction
            for candle in candles:
                close = candle.get("price_close", 0)
                open_price = candle.get("price_open", 0)
                volume = candle.get("volume_traded", 0)

                if close > open_price:  # Bullish candle
                    buy_volume += volume
                else:  # Bearish candle
                    sell_volume += volume

            total_volume = buy_volume + sell_volume
            if total_volume == 0:
                return {"score": 50, "signal": "NO_VOLUME", "buyPressure": 0}

            buy_pressure = buy_volume / total_volume

            # Score: >55% buy pressure = bullish
            score = 100 if buy_pressure > 0.55 else buy_pressure * 100
            signal = "BULLISH" if buy_pressure > 0.55 else "NEUTRAL"

            return {
                "buyPressure": round(buy_pressure, 3),
                "score": round(score),
                "signal": signal,
                "buyVolume": round(buy_volume, 2),
                "sellVolume": round(sell_volume, 2)
            }

        except Exception as e:
            logger.error(f"[AccumulationDetector] Volume profile error for {symbol}: {e}")
            return {"score": 50, "signal": "ERROR", "buyPressure": 0}

    async def detect_consolidation(self, symbol: str, timeframe: str = "1HRS") -> Dict:
        """
        Detect price consolidation (low volatility)
        Consolidation often precedes breakouts
        """
        try:
            # Get recent price data
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period=timeframe,
                limit=72  # Last 72 periods
            )

            if not ohlcv_data.get("success"):
                return {"score": 50, "signal": "NO_DATA", "volatility": 0}

            candles = ohlcv_data.get("data", [])
            if len(candles) < 20:
                return {"score": 50, "signal": "INSUFFICIENT_DATA", "volatility": 0}

            # Extract closing prices
            prices = [c.get("price_close", 0) for c in candles if c.get("price_close")]

            if len(prices) < 20:
                return {"score": 50, "signal": "INSUFFICIENT_DATA", "volatility": 0}

            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] != 0:
                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(ret)

            if not returns:
                return {"score": 50, "signal": "NO_DATA", "volatility": 0}

            # Calculate volatility (standard deviation of returns)
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5

            # Low volatility (<2%) = consolidation
            is_consolidating = volatility < 0.02
            score = 100 if is_consolidating else 50
            signal = "CONSOLIDATING" if is_consolidating else "VOLATILE"

            return {
                "volatility": round(volatility, 4),
                "isConsolidating": is_consolidating,
                "score": score,
                "signal": signal
            }

        except Exception as e:
            logger.error(f"[AccumulationDetector] Consolidation detection error for {symbol}: {e}")
            return {"score": 50, "signal": "ERROR", "volatility": 0}

    async def analyze_sell_pressure(self, symbol: str, timeframe: str = "1HRS") -> Dict:
        """
        Analyze sell pressure from recent trades
        Decreasing sell pressure = bullish accumulation

        Note: This uses OHLCV as a proxy since direct trade data requires exchange APIs
        """
        try:
            # Get recent OHLCV data
            ohlcv_data = await self.coinapi.get_ohlcv_latest(
                symbol=symbol,
                period=timeframe,
                limit=50
            )

            if not ohlcv_data.get("success"):
                return {"score": 50, "signal": "NO_DATA", "sellPressureRatio": 0.5}

            candles = ohlcv_data.get("data", [])
            if len(candles) < 10:
                return {"score": 50, "signal": "INSUFFICIENT_DATA", "sellPressureRatio": 0.5}

            # Analyze candle wicks and body to estimate sell pressure
            sell_candles = 0
            buy_candles = 0
            sell_volume = 0
            buy_volume = 0

            for candle in candles:
                close = candle.get("price_close", 0)
                open_price = candle.get("price_open", 0)
                volume = candle.get("volume_traded", 0)

                if close < open_price:  # Bearish candle (sell pressure)
                    sell_candles += 1
                    sell_volume += volume
                else:  # Bullish candle
                    buy_candles += 1
                    buy_volume += volume

            total_volume = buy_volume + sell_volume
            if total_volume == 0:
                return {"score": 50, "signal": "NO_VOLUME", "sellPressureRatio": 0.5}

            sell_pressure_ratio = sell_volume / total_volume

            # Low sell pressure (<45%) = bullish
            if sell_pressure_ratio < 0.45:
                score = 100
                signal = "DECREASING_SELL"
            else:
                score = (1 - sell_pressure_ratio) * 100
                signal = "HIGH_SELL" if sell_pressure_ratio > 0.55 else "NEUTRAL"

            return {
                "sellPressureRatio": round(sell_pressure_ratio, 3),
                "score": round(score),
                "signal": signal,
                "sellCandles": sell_candles,
                "buyCandles": buy_candles
            }

        except Exception as e:
            logger.error(f"[AccumulationDetector] Sell pressure error for {symbol}: {e}")
            return {"score": 50, "signal": "ERROR", "sellPressureRatio": 0.5}

    async def analyze_order_book(self, symbol: str) -> Dict:
        """
        Analyze order book depth for bid/ask ratios and buy walls

        Note: Requires order book data from CoinAPI or exchange APIs
        This is a placeholder implementation - will need actual order book data
        """
        try:
            # Get order book data from CoinAPI
            orderbook_data = await self.coinapi.get_orderbook_latest(
                symbol=symbol,
                limit=20
            )

            if not orderbook_data.get("success"):
                # Return neutral score if order book data unavailable
                return {
                    "score": 50,
                    "signal": "NO_DATA",
                    "bidAskRatio": 1.0,
                    "buyWalls": 0
                }

            bids = orderbook_data.get("data", {}).get("bids", [])
            asks = orderbook_data.get("data", {}).get("asks", [])

            if not bids or not asks:
                return {
                    "score": 50,
                    "signal": "INSUFFICIENT_DATA",
                    "bidAskRatio": 1.0,
                    "buyWalls": 0
                }

            # Calculate total bid and ask volume (price * size)
            total_bids = sum(bid.get("price", 0) * bid.get("size", 0) for bid in bids)
            total_asks = sum(ask.get("price", 0) * ask.get("size", 0) for ask in asks)

            if total_asks == 0:
                return {"score": 50, "signal": "ERROR", "bidAskRatio": 1.0, "buyWalls": 0}

            bid_ask_ratio = total_bids / total_asks

            # Detect buy walls (bids significantly larger than average)
            avg_bid_size = total_bids / len(bids) if bids else 0
            buy_walls = sum(1 for bid in bids
                          if (bid.get("price", 0) * bid.get("size", 0)) > avg_bid_size * 3)

            # Score: bid/ask > 1.2 and buy walls present = strong accumulation
            if bid_ask_ratio > 1.2 and buy_walls > 0:
                score = 100
                signal = "STRONG_BIDS"
            elif bid_ask_ratio > 1.0:
                score = 70
                signal = "POSITIVE_BIDS"
            else:
                score = 40
                signal = "NEUTRAL"

            return {
                "bidAskRatio": round(bid_ask_ratio, 3),
                "buyWalls": buy_walls,
                "score": score,
                "signal": signal,
                "totalBids": round(total_bids, 2),
                "totalAsks": round(total_asks, 2)
            }

        except Exception as e:
            logger.error(f"[AccumulationDetector] Order book error for {symbol}: {e}")
            return {
                "score": 50,
                "signal": "ERROR",
                "bidAskRatio": 1.0,
                "buyWalls": 0
            }

    def calculate_accumulation_score(self, signals: Dict) -> Dict:
        """
        Calculate weighted accumulation score from all signals

        Args:
            signals: Dict with volumeProfile, consolidation, sellPressure, orderBookDepth

        Returns:
            Final accumulation score and verdict
        """
        # Weighted scoring
        weights = {
            "volumeProfile": 0.30,
            "consolidation": 0.25,
            "sellPressure": 0.25,
            "orderBookDepth": 0.20
        }

        total_score = (
            signals["volumeProfile"]["score"] * weights["volumeProfile"] +
            signals["consolidation"]["score"] * weights["consolidation"] +
            signals["sellPressure"]["score"] * weights["sellPressure"] +
            signals["orderBookDepth"]["score"] * weights["orderBookDepth"]
        )

        # Determine verdict
        if total_score > 75:
            verdict = "STRONG_ACCUMULATION"
        elif total_score > 60:
            verdict = "MODERATE_ACCUMULATION"
        else:
            verdict = "WEAK_ACCUMULATION"

        return {
            "score": round(total_score),
            "details": signals,
            "verdict": verdict,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def close(self):
        """Close service connections"""
        await self.coinapi.close()

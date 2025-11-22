"""
Whale Tracker Service
Tracks large trader (whale) activity that indicates accumulation

Features:
- Large Trades Detection (whale buy vs sell activity)
- Funding Rate Analysis (sentiment from perpetual futures)
- Open Interest Changes (position building)
- Exchange Flow Analysis (coins leaving/entering exchanges)

Author: CryptoSat Intelligence Pre-Pump Detection Engine
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService
from app.utils.logger import logger


class WhaleTracker:
    """Tracks whale activity for pre-pump detection"""

    def __init__(self, coinglass_service: Optional[CoinglassComprehensiveService] = None):
        self.coinglass = coinglass_service or CoinglassComprehensiveService()

    async def track_whale_activity(self, symbol: str) -> Dict:
        """
        Main whale tracking method

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')

        Returns:
            Dict with whale activity score, signals, and verdict
        """
        try:
            logger.info(f"[WhaleTracker] Tracking whale activity for {symbol}")

            # Run all tracking methods in parallel
            signals = await asyncio.gather(
                self.detect_large_trades(symbol),
                self.analyze_funding_rate(symbol),
                self.analyze_open_interest(symbol),
                self.analyze_liquidations(symbol),
                return_exceptions=True
            )

            # Unpack results
            large_trades = signals[0] if not isinstance(signals[0], Exception) else {"score": 50, "signal": "ERROR"}
            funding_rate = signals[1] if not isinstance(signals[1], Exception) else {"score": 50, "signal": "ERROR"}
            open_interest = signals[2] if not isinstance(signals[2], Exception) else {"score": 50, "signal": "ERROR"}
            liquidations = signals[3] if not isinstance(signals[3], Exception) else {"score": 50, "signal": "ERROR"}

            # Calculate final whale score
            result = self.calculate_whale_score({
                "largeTrades": large_trades,
                "fundingRate": funding_rate,
                "openInterest": open_interest,
                "liquidations": liquidations
            })

            logger.info(f"[WhaleTracker] {symbol} whale activity score: {result['score']}/100")
            return result

        except Exception as e:
            logger.error(f"[WhaleTracker] Error tracking {symbol}: {e}")
            return {
                "score": 0,
                "verdict": "ERROR",
                "details": {},
                "error": str(e)
            }

    async def detect_large_trades(self, symbol: str) -> Dict:
        """
        Detect large whale trades
        Uses volume and liquidation data as proxy for whale activity
        """
        try:
            # Get market data which includes volume information
            market_data = await self.coinglass.get_coins_markets(symbol)

            if not market_data.get("success"):
                return {
                    "score": 50,
                    "signal": "NO_DATA",
                    "buyRatio": 0.5
                }

            # Get liquidation data for whale activity signals
            liq_data = await self.coinglass.get_liquidation_history(
                symbol=symbol,
                interval="1h"
            )

            # Analyze volume and liquidation patterns
            if not liq_data.get("success"):
                # If no liquidation data, return neutral score
                return {
                    "score": 50,
                    "signal": "INSUFFICIENT_DATA",
                    "buyRatio": 0.5
                }

            liq_history = liq_data.get("data", [])
            if not liq_history:
                return {
                    "score": 50,
                    "signal": "NO_LIQUIDATION_DATA",
                    "buyRatio": 0.5
                }

            # Analyze recent liquidations (last 24 hours)
            recent_liq = liq_history[-24:] if len(liq_history) >= 24 else liq_history

            total_long_liq = sum(item.get("longLiquidation", 0) for item in recent_liq)
            total_short_liq = sum(item.get("shortLiquidation", 0) for item in recent_liq)

            # High short liquidations = price going up = whales buying
            # High long liquidations = price going down = whales selling
            total_liq = total_long_liq + total_short_liq
            if total_liq == 0:
                return {
                    "score": 50,
                    "signal": "NO_LIQUIDATION_ACTIVITY",
                    "buyRatio": 0.5
                }

            # Short liquidations / Total = buying pressure
            buy_ratio = total_short_liq / total_liq

            # Score: >60% short liquidations = whales accumulating
            if buy_ratio > 0.6:
                score = 100
                signal = "WHALE_ACCUMULATING"
            elif buy_ratio < 0.4:
                score = 30
                signal = "WHALE_DISTRIBUTING"
            else:
                score = buy_ratio * 100
                signal = "NEUTRAL"

            return {
                "buyRatio": round(buy_ratio, 3),
                "score": round(score),
                "signal": signal,
                "shortLiquidations": round(total_short_liq, 2),
                "longLiquidations": round(total_long_liq, 2)
            }

        except Exception as e:
            logger.error(f"[WhaleTracker] Large trades error for {symbol}: {e}")
            return {
                "score": 50,
                "signal": "ERROR",
                "buyRatio": 0.5
            }

    async def analyze_funding_rate(self, symbol: str) -> Dict:
        """
        Analyze funding rates from perpetual futures
        Negative funding = shorts paying longs = bullish
        Positive funding = longs paying shorts = bearish
        """
        try:
            # Get funding rate from Coinglass
            market_data = await self.coinglass.get_coins_markets(symbol)

            if not market_data.get("success"):
                return {
                    "score": 50,
                    "signal": "NO_DATA",
                    "fundingRate": 0
                }

            # Get funding rate (OI-weighted is more accurate)
            funding_rate = market_data.get("fundingRateByOI", 0)

            # Negative funding = bullish (shorts paying longs)
            if funding_rate < 0:
                score = 100
                signal = "BULLISH_FUNDING"
            elif funding_rate < 0.01:  # Very low positive funding
                score = 70
                signal = "NEUTRAL_FUNDING"
            elif funding_rate > 0.05:  # High positive funding
                score = 30
                signal = "BEARISH_FUNDING"
            else:
                score = 50
                signal = "NEUTRAL"

            return {
                "fundingRate": round(funding_rate, 6),
                "score": score,
                "signal": signal
            }

        except Exception as e:
            logger.error(f"[WhaleTracker] Funding rate error for {symbol}: {e}")
            return {
                "score": 50,
                "signal": "ERROR",
                "fundingRate": 0
            }

    async def analyze_open_interest(self, symbol: str) -> Dict:
        """
        Analyze open interest changes
        Rising OI = new positions opening
        Rising OI + Rising Price = bullish (whales accumulating)
        """
        try:
            # Get current market data with OI
            market_data = await self.coinglass.get_coins_markets(symbol)

            if not market_data.get("success"):
                return {
                    "score": 50,
                    "signal": "NO_DATA",
                    "oiChange": 0
                }

            current_oi = market_data.get("openInterestUsd", 0)

            # Get historical OI data
            oi_history = await self.coinglass.get_open_interest_history(
                symbol=symbol,
                interval="1h"
            )

            if not oi_history.get("success"):
                # If no historical data, check if current OI is high
                oi_market_cap_ratio = market_data.get("oiMarketCapRatio", 0)

                if oi_market_cap_ratio > 0.1:  # OI > 10% of market cap
                    return {
                        "score": 70,
                        "signal": "HIGH_OI",
                        "openInterest": current_oi,
                        "oiChange": 0
                    }
                else:
                    return {
                        "score": 50,
                        "signal": "NO_HISTORICAL_DATA",
                        "openInterest": current_oi,
                        "oiChange": 0
                    }

            oi_data = oi_history.get("data", [])
            if len(oi_data) < 2:
                return {
                    "score": 50,
                    "signal": "INSUFFICIENT_DATA",
                    "openInterest": current_oi,
                    "oiChange": 0
                }

            # Calculate OI change (last 24h)
            recent_oi = oi_data[-24:] if len(oi_data) >= 24 else oi_data
            old_oi = recent_oi[0].get("openInterest", current_oi)

            if old_oi == 0:
                oi_change = 0
            else:
                oi_change = (current_oi - old_oi) / old_oi

            # Score: Rising OI > 5% = bullish
            if oi_change > 0.05:
                score = 80
                signal = "OI_INCREASING"
            elif oi_change > 0:
                score = 60
                signal = "OI_GROWING"
            elif oi_change < -0.05:
                score = 40
                signal = "OI_DECREASING"
            else:
                score = 50
                signal = "OI_STABLE"

            return {
                "openInterest": round(current_oi, 2),
                "oiChange": round(oi_change, 4),
                "oiChangePercent": round(oi_change * 100, 2),
                "score": score,
                "signal": signal
            }

        except Exception as e:
            logger.error(f"[WhaleTracker] Open interest error for {symbol}: {e}")
            return {
                "score": 50,
                "signal": "ERROR",
                "openInterest": 0,
                "oiChange": 0
            }

    async def analyze_liquidations(self, symbol: str) -> Dict:
        """
        Analyze liquidation patterns
        High short liquidations = price pumping, whales accumulating
        """
        try:
            # Get recent liquidations
            liq_data = await self.coinglass.get_liquidation_history(
                symbol=symbol,
                interval="1h"
            )

            if not liq_data.get("success"):
                return {
                    "score": 50,
                    "signal": "NO_DATA",
                    "liqRatio": 0
                }

            liq_history = liq_data.get("data", [])
            if not liq_history:
                return {
                    "score": 50,
                    "signal": "NO_LIQUIDATION_DATA",
                    "liqRatio": 0
                }

            # Analyze recent liquidations (last 6 hours)
            recent_liq = liq_history[-6:] if len(liq_history) >= 6 else liq_history

            total_long_liq = sum(item.get("longLiquidation", 0) for item in recent_liq)
            total_short_liq = sum(item.get("shortLiquidation", 0) for item in recent_liq)
            total_liq = total_long_liq + total_short_liq

            if total_liq == 0:
                return {
                    "score": 50,
                    "signal": "NO_RECENT_LIQUIDATIONS",
                    "liqRatio": 0
                }

            # Ratio of short to total liquidations
            short_liq_ratio = total_short_liq / total_liq

            # High short liquidations = price moving up = bullish
            if short_liq_ratio > 0.7:
                score = 90
                signal = "HIGH_SHORT_LIQUIDATIONS"
            elif short_liq_ratio > 0.5:
                score = 70
                signal = "MODERATE_SHORT_LIQUIDATIONS"
            elif short_liq_ratio < 0.3:
                score = 30
                signal = "HIGH_LONG_LIQUIDATIONS"
            else:
                score = 50
                signal = "BALANCED_LIQUIDATIONS"

            return {
                "shortLiquidations": round(total_short_liq, 2),
                "longLiquidations": round(total_long_liq, 2),
                "liqRatio": round(short_liq_ratio, 3),
                "score": score,
                "signal": signal
            }

        except Exception as e:
            logger.error(f"[WhaleTracker] Liquidation analysis error for {symbol}: {e}")
            return {
                "score": 50,
                "signal": "ERROR",
                "liqRatio": 0
            }

    def calculate_whale_score(self, signals: Dict) -> Dict:
        """
        Calculate weighted whale activity score from all signals

        Args:
            signals: Dict with largeTrades, fundingRate, openInterest, liquidations

        Returns:
            Final whale activity score and verdict
        """
        # Weighted scoring
        weights = {
            "largeTrades": 0.30,
            "fundingRate": 0.25,
            "openInterest": 0.25,
            "liquidations": 0.20
        }

        total_score = (
            signals["largeTrades"]["score"] * weights["largeTrades"] +
            signals["fundingRate"]["score"] * weights["fundingRate"] +
            signals["openInterest"]["score"] * weights["openInterest"] +
            signals["liquidations"]["score"] * weights["liquidations"]
        )

        # Determine verdict
        if total_score > 75:
            verdict = "STRONG_WHALE_ACCUMULATION"
        elif total_score > 60:
            verdict = "MODERATE_WHALE_ACTIVITY"
        else:
            verdict = "LOW_WHALE_ACTIVITY"

        return {
            "score": round(total_score),
            "details": signals,
            "verdict": verdict,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def close(self):
        """Close service connections"""
        await self.coinglass.close()

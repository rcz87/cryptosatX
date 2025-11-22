"""
Pre-Pump Detection Engine
Main engine that combines all detection components to identify pre-pump opportunities

Components:
- Accumulation Detector (volume, consolidation, sell pressure, order book)
- Reversal Detector (double bottom, RSI divergence, MACD, support bounce)
- Whale Tracker (large trades, funding rates, open interest, liquidations)

Outputs:
- Comprehensive pre-pump score (0-100)
- Confidence level based on signal agreement
- Trading recommendation with entry/exit strategy

Author: CryptoSat Intelligence Pre-Pump Detection Engine
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from app.services.accumulation_detector import AccumulationDetector
from app.services.reversal_detector import ReversalDetector
from app.services.whale_tracker import WhaleTracker
from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService
from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService
from app.utils.logger import logger


class PrePumpEngine:
    """Main pre-pump detection engine combining all signal sources"""

    def __init__(
        self,
        coinapi_service: Optional[CoinAPIComprehensiveService] = None,
        coinglass_service: Optional[CoinglassComprehensiveService] = None
    ):
        # Initialize API services
        self.coinapi = coinapi_service or CoinAPIComprehensiveService()
        self.coinglass = coinglass_service or CoinglassComprehensiveService()

        # Initialize detectors
        self.accumulation_detector = AccumulationDetector(self.coinapi)
        self.reversal_detector = ReversalDetector(self.coinapi)
        self.whale_tracker = WhaleTracker(self.coinglass)

    async def analyze_pre_pump(self, symbol: str, timeframe: str = "1HRS") -> Dict:
        """
        Comprehensive pre-pump analysis for a single symbol

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')
            timeframe: Analysis timeframe (1MIN, 5MIN, 1HRS, 4HRS, 1DAY)

        Returns:
            Complete pre-pump analysis with score, confidence, and recommendations
        """
        try:
            logger.info(f"[PrePumpEngine] Starting pre-pump analysis for {symbol}")

            # Run all detectors in parallel for maximum efficiency
            results = await asyncio.gather(
                self.accumulation_detector.detect_accumulation(symbol, timeframe),
                self.reversal_detector.detect_reversal(symbol),
                self.whale_tracker.track_whale_activity(symbol),
                return_exceptions=True
            )

            # Unpack results
            accumulation = results[0] if not isinstance(results[0], Exception) else {
                "score": 0, "verdict": "ERROR", "details": {}
            }
            reversal = results[1] if not isinstance(results[1], Exception) else {
                "score": 0, "verdict": "ERROR", "details": {}
            }
            whale = results[2] if not isinstance(results[2], Exception) else {
                "score": 0, "verdict": "ERROR", "details": {}
            }

            # Calculate final pre-pump score
            final_score = self.calculate_final_score({
                "accumulation": accumulation,
                "reversal": reversal,
                "whale": whale
            })

            # Generate trading recommendation
            recommendation = self.generate_recommendation(final_score)

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat(),
                "score": final_score["score"],
                "confidence": final_score["confidence"],
                "verdict": final_score["verdict"],
                "components": {
                    "accumulation": accumulation,
                    "reversal": reversal,
                    "whale": whale
                },
                "recommendation": recommendation,
                "success": True
            }

            logger.info(
                f"[PrePumpEngine] {symbol} analysis complete: "
                f"Score={result['score']}/100, "
                f"Confidence={result['confidence']}%, "
                f"Verdict={result['verdict']}"
            )

            return result

        except Exception as e:
            logger.error(f"[PrePumpEngine] Error analyzing {symbol}: {e}")
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def calculate_final_score(self, components: Dict) -> Dict:
        """
        Calculate weighted final pre-pump score

        Args:
            components: Dict with accumulation, reversal, whale results

        Returns:
            Final score, confidence, and verdict
        """
        # Weighted scoring (all components equally important)
        weights = {
            "accumulation": 0.35,
            "reversal": 0.35,
            "whale": 0.30
        }

        accumulation_score = components["accumulation"].get("score", 0)
        reversal_score = components["reversal"].get("score", 0)
        whale_score = components["whale"].get("score", 0)

        total_score = (
            accumulation_score * weights["accumulation"] +
            reversal_score * weights["reversal"] +
            whale_score * weights["whale"]
        )

        # Calculate confidence based on signal agreement
        # Low variance between scores = high confidence (signals agree)
        scores = [accumulation_score, reversal_score, whale_score]
        avg_score = sum(scores) / len(scores)

        # Calculate variance
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5

        # Convert std dev to confidence (lower std dev = higher confidence)
        # Max std dev ~50, so we normalize
        confidence = max(0, 100 - (std_dev * 2))

        # Determine verdict based on score and confidence
        if total_score >= 80 and confidence >= 70:
            verdict = "VERY_STRONG_PRE_PUMP"
        elif total_score >= 70 and confidence >= 60:
            verdict = "STRONG_PRE_PUMP"
        elif total_score >= 60:
            verdict = "MODERATE_PRE_PUMP"
        elif total_score >= 50:
            verdict = "WEAK_PRE_PUMP"
        else:
            verdict = "NO_PRE_PUMP_SIGNAL"

        return {
            "score": round(total_score, 1),
            "confidence": round(confidence, 1),
            "verdict": verdict,
            "componentScores": {
                "accumulation": accumulation_score,
                "reversal": reversal_score,
                "whale": whale_score
            }
        }

    def generate_recommendation(self, final_score: Dict) -> Dict:
        """
        Generate trading recommendation based on pre-pump score

        Args:
            final_score: Dict with score, confidence, verdict

        Returns:
            Trading recommendation with action, risk, entry/exit strategy
        """
        score = final_score["score"]
        confidence = final_score["confidence"]
        verdict = final_score["verdict"]

        if verdict == "VERY_STRONG_PRE_PUMP":
            return {
                "action": "STRONG_BUY",
                "risk": "LOW",
                "message": "Very strong pre-pump signals detected! High probability of upward movement.",
                "suggestedEntry": "IMMEDIATE",
                "stopLoss": "5-7% below entry",
                "takeProfit": "15-30% above entry",
                "positionSize": "FULL",
                "timeHorizon": "SHORT_TERM",
                "notes": "Multiple strong signals aligned. Consider entering full position."
            }

        elif verdict == "STRONG_PRE_PUMP":
            return {
                "action": "BUY",
                "risk": "MEDIUM",
                "message": "Strong pre-pump signals. Good entry opportunity.",
                "suggestedEntry": "IMMEDIATE",
                "stopLoss": "7-10% below entry",
                "takeProfit": "10-20% above entry",
                "positionSize": "MODERATE",
                "timeHorizon": "SHORT_TERM",
                "notes": "Strong signals but moderate confidence. Consider 50-70% position size."
            }

        elif verdict == "MODERATE_PRE_PUMP":
            return {
                "action": "WATCH",
                "risk": "MEDIUM",
                "message": "Moderate signals. Monitor closely for confirmation.",
                "suggestedEntry": "WAIT_FOR_CONFIRMATION",
                "stopLoss": "10% below entry",
                "takeProfit": "10-15% above entry",
                "positionSize": "SMALL",
                "timeHorizon": "SHORT_TERM",
                "notes": "Wait for additional confirmation before entering. Consider small position (20-30%)."
            }

        elif verdict == "WEAK_PRE_PUMP":
            return {
                "action": "MONITOR",
                "risk": "HIGH",
                "message": "Weak signals. Not recommended for entry yet.",
                "suggestedEntry": "DO_NOT_ENTER",
                "stopLoss": "N/A",
                "takeProfit": "N/A",
                "positionSize": "NONE",
                "timeHorizon": "N/A",
                "notes": "Signals too weak. Continue monitoring but avoid entry."
            }

        else:  # NO_PRE_PUMP_SIGNAL
            return {
                "action": "AVOID",
                "risk": "N/A",
                "message": "No pre-pump signals detected.",
                "suggestedEntry": "DO_NOT_ENTER",
                "stopLoss": "N/A",
                "takeProfit": "N/A",
                "positionSize": "NONE",
                "timeHorizon": "N/A",
                "notes": "No significant pre-pump indicators. Look for other opportunities."
            }

    async def scan_market(
        self,
        symbols: List[str],
        timeframe: str = "1HRS",
        min_score: float = 50.0
    ) -> Dict:
        """
        Scan multiple symbols for pre-pump opportunities

        Args:
            symbols: List of crypto symbols to scan
            timeframe: Analysis timeframe
            min_score: Minimum score to include in results (default: 50)

        Returns:
            Dict with scan results sorted by score
        """
        try:
            logger.info(f"[PrePumpEngine] Scanning {len(symbols)} symbols for pre-pump signals")

            results = []

            # Analyze each symbol (with rate limiting)
            for i, symbol in enumerate(symbols):
                try:
                    analysis = await self.analyze_pre_pump(symbol, timeframe)

                    if analysis.get("success") and analysis.get("score", 0) >= min_score:
                        results.append(analysis)

                    # Rate limiting: small delay between requests
                    if i < len(symbols) - 1:  # Don't delay after last symbol
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"[PrePumpEngine] Error scanning {symbol}: {e}")
                    continue

            # Sort by score (highest first)
            results.sort(key=lambda x: x.get("score", 0), reverse=True)

            # Categorize results
            very_strong = [r for r in results if r.get("verdict") == "VERY_STRONG_PRE_PUMP"]
            strong = [r for r in results if r.get("verdict") == "STRONG_PRE_PUMP"]
            moderate = [r for r in results if r.get("verdict") == "MODERATE_PRE_PUMP"]

            scan_result = {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "totalScanned": len(symbols),
                "totalFound": len(results),
                "minScore": min_score,
                "summary": {
                    "veryStrong": len(very_strong),
                    "strong": len(strong),
                    "moderate": len(moderate)
                },
                "topOpportunities": results[:10],  # Top 10
                "allResults": results
            }

            logger.info(
                f"[PrePumpEngine] Scan complete: {len(results)} opportunities found "
                f"(Very Strong: {len(very_strong)}, Strong: {len(strong)}, Moderate: {len(moderate)})"
            )

            return scan_result

        except Exception as e:
            logger.error(f"[PrePumpEngine] Market scan error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_top_opportunities(
        self,
        symbols: List[str],
        limit: int = 5,
        timeframe: str = "1HRS"
    ) -> List[Dict]:
        """
        Get top N pre-pump opportunities from a list of symbols

        Args:
            symbols: List of symbols to analyze
            limit: Number of top opportunities to return
            timeframe: Analysis timeframe

        Returns:
            List of top opportunities sorted by score
        """
        scan_result = await self.scan_market(symbols, timeframe, min_score=60.0)

        if not scan_result.get("success"):
            return []

        return scan_result.get("topOpportunities", [])[:limit]

    async def close(self):
        """Close all service connections"""
        await self.accumulation_detector.close()
        await self.reversal_detector.close()
        await self.whale_tracker.close()
        await self.coinapi.close()
        await self.coinglass.close()

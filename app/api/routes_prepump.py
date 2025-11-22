"""
Pre-Pump Detection API Routes
Endpoints for detecting pre-pump signals and opportunities

Features:
- Single symbol analysis
- Multi-symbol market scanning
- Top opportunities ranking
- Component-level analysis (accumulation, reversal, whale)

Author: CryptoSat Intelligence Pre-Pump Detection Engine
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.pre_pump_engine import PrePumpEngine
from app.services.accumulation_detector import AccumulationDetector
from app.services.reversal_detector import ReversalDetector
from app.services.whale_tracker import WhaleTracker
# Scanner imports disabled - auto-scanning consumes too much API quota
# from app.services.pre_pump_scanner import (
#     get_pre_pump_scanner,
#     start_pre_pump_scanner,
#     stop_pre_pump_scanner
# )
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/prepump", tags=["Pre-Pump Detection"])

# Initialize engine (singleton pattern)
_engine: Optional[PrePumpEngine] = None


def get_engine() -> PrePumpEngine:
    """Get or create Pre-Pump Engine instance"""
    global _engine
    if _engine is None:
        _engine = PrePumpEngine()
    return _engine


@router.get("/analyze/{symbol}")
async def analyze_symbol(
    symbol: str,
    timeframe: str = Query("1HRS", description="Analysis timeframe (1MIN, 5MIN, 1HRS, 4HRS, 1DAY)")
):
    """
    Analyze a single symbol for pre-pump signals

    **Example:**
    ```
    GET /api/prepump/analyze/BTC?timeframe=1HRS
    ```

    **Returns:**
    - score: Pre-pump score (0-100)
    - confidence: Signal confidence (0-100)
    - verdict: VERY_STRONG_PRE_PUMP, STRONG_PRE_PUMP, MODERATE_PRE_PUMP, WEAK_PRE_PUMP, NO_PRE_PUMP_SIGNAL
    - components: Detailed breakdown (accumulation, reversal, whale)
    - recommendation: Trading action, risk level, entry/exit strategy
    """
    try:
        logger.info(f"[API] Analyzing {symbol} for pre-pump signals")

        engine = get_engine()
        result = await engine.analyze_pre_pump(symbol, timeframe)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {result.get('error', 'Unknown error')}"
            )

        return result

    except Exception as e:
        logger.error(f"[API] Error analyzing {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
async def scan_market(
    symbols: List[str],
    timeframe: str = Query("1HRS", description="Analysis timeframe"),
    min_score: float = Query(50.0, description="Minimum score to include (0-100)")
):
    """
    Scan multiple symbols for pre-pump opportunities

    **Example:**
    ```
    POST /api/prepump/scan?timeframe=1HRS&min_score=60
    Body: ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
    ```

    **Returns:**
    - totalScanned: Number of symbols scanned
    - totalFound: Number of opportunities found
    - summary: Breakdown by strength (very strong, strong, moderate)
    - topOpportunities: Top 10 ranked opportunities
    - allResults: Complete results for all symbols above min_score
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")

        if len(symbols) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 symbols per scan")

        logger.info(f"[API] Scanning {len(symbols)} symbols for pre-pump signals")

        engine = get_engine()
        result = await engine.scan_market(symbols, timeframe, min_score)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Scan failed: {result.get('error', 'Unknown error')}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error scanning market: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-opportunities")
async def get_top_opportunities(
    symbols: str = Query(..., description="Comma-separated list of symbols (e.g., 'BTC,ETH,SOL')"),
    limit: int = Query(5, description="Number of top opportunities to return", ge=1, le=20),
    timeframe: str = Query("1HRS", description="Analysis timeframe")
):
    """
    Get top N pre-pump opportunities from a list of symbols

    **Example:**
    ```
    GET /api/prepump/top-opportunities?symbols=BTC,ETH,SOL,AVAX,MATIC&limit=3&timeframe=1HRS
    ```

    **Returns:**
    List of top opportunities sorted by score (highest first)
    """
    try:
        # Parse comma-separated symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        if not symbol_list:
            raise HTTPException(status_code=400, detail="No valid symbols provided")

        if len(symbol_list) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed")

        logger.info(f"[API] Getting top {limit} opportunities from {len(symbol_list)} symbols")

        engine = get_engine()
        opportunities = await engine.get_top_opportunities(symbol_list, limit, timeframe)

        return {
            "success": True,
            "totalAnalyzed": len(symbol_list),
            "limit": limit,
            "opportunities": opportunities
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error getting top opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/{symbol}/accumulation")
async def analyze_accumulation(
    symbol: str,
    timeframe: str = Query("1HRS", description="Analysis timeframe")
):
    """
    Analyze accumulation signals only for a symbol

    **Example:**
    ```
    GET /api/prepump/components/BTC/accumulation?timeframe=1HRS
    ```

    **Returns:**
    Detailed accumulation analysis with volume profile, consolidation, sell pressure, order book
    """
    try:
        logger.info(f"[API] Analyzing accumulation for {symbol}")

        detector = AccumulationDetector()
        result = await detector.detect_accumulation(symbol, timeframe)
        await detector.close()

        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "result": result
        }

    except Exception as e:
        logger.error(f"[API] Error analyzing accumulation for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/{symbol}/reversal")
async def analyze_reversal(symbol: str):
    """
    Analyze reversal patterns only for a symbol

    **Example:**
    ```
    GET /api/prepump/components/BTC/reversal
    ```

    **Returns:**
    Detailed reversal analysis with double bottom, RSI divergence, MACD, support bounce
    """
    try:
        logger.info(f"[API] Analyzing reversal patterns for {symbol}")

        detector = ReversalDetector()
        result = await detector.detect_reversal(symbol)
        await detector.close()

        return {
            "success": True,
            "symbol": symbol,
            "result": result
        }

    except Exception as e:
        logger.error(f"[API] Error analyzing reversal for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/{symbol}/whale")
async def analyze_whale_activity(symbol: str):
    """
    Analyze whale activity only for a symbol

    **Example:**
    ```
    GET /api/prepump/components/BTC/whale
    ```

    **Returns:**
    Detailed whale analysis with large trades, funding rates, open interest, liquidations
    """
    try:
        logger.info(f"[API] Analyzing whale activity for {symbol}")

        tracker = WhaleTracker()
        result = await tracker.track_whale_activity(symbol)
        await tracker.close()

        return {
            "success": True,
            "symbol": symbol,
            "result": result
        }

    except Exception as e:
        logger.error(f"[API] Error analyzing whale activity for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick-scan")
async def quick_scan(
    timeframe: str = Query("1HRS", description="Analysis timeframe")
):
    """
    Quick scan of popular coins for pre-pump signals

    **Example:**
    ```
    GET /api/prepump/quick-scan?timeframe=1HRS
    ```

    **Returns:**
    Quick analysis of top 20 cryptocurrencies
    """
    try:
        # Default popular coins to scan
        popular_coins = [
            "BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOT", "AVAX",
            "MATIC", "LINK", "UNI", "ATOM", "LTC", "BCH", "XLM",
            "ALGO", "VET", "FIL", "THETA", "AAVE"
        ]

        logger.info(f"[API] Quick scanning {len(popular_coins)} popular coins")

        engine = get_engine()
        result = await engine.scan_market(popular_coins, timeframe, min_score=60.0)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Quick scan failed: {result.get('error', 'Unknown error')}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error in quick scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(
    limit: int = Query(10, description="Number of top opportunities to return", ge=1, le=50)
):
    """
    Get dashboard data for pre-pump detection UI

    **Example:**
    ```
    GET /api/prepump/dashboard?limit=10
    ```

    **Returns:**
    Formatted data suitable for dashboard display with top opportunities
    """
    try:
        # Scan popular coins
        popular_coins = [
            "BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOT", "AVAX",
            "MATIC", "LINK", "UNI", "ATOM", "LTC", "BCH", "XLM",
            "ALGO", "VET", "FIL", "THETA", "AAVE", "NEAR", "HBAR",
            "FTM", "SAND", "MANA", "AXS", "CRV", "SNX", "COMP"
        ]

        logger.info(f"[API] Generating dashboard data")

        engine = get_engine()
        scan_result = await engine.scan_market(popular_coins, "1HRS", min_score=50.0)

        if not scan_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Dashboard data generation failed: {scan_result.get('error', 'Unknown error')}"
            )

        # Format for dashboard
        top_opportunities = scan_result.get("topOpportunities", [])[:limit]

        dashboard = {
            "success": True,
            "timestamp": scan_result.get("timestamp"),
            "totalScanned": scan_result.get("totalScanned", 0),
            "totalFound": scan_result.get("totalFound", 0),
            "summary": scan_result.get("summary", {}),
            "topOpportunities": [
                {
                    "symbol": opp.get("symbol"),
                    "score": opp.get("score"),
                    "confidence": opp.get("confidence"),
                    "verdict": opp.get("verdict"),
                    "action": opp.get("recommendation", {}).get("action"),
                    "risk": opp.get("recommendation", {}).get("risk"),
                    "message": opp.get("recommendation", {}).get("message"),
                    "signals": {
                        "accumulation": opp.get("components", {}).get("accumulation", {}).get("verdict"),
                        "reversal": opp.get("components", {}).get("reversal", {}).get("verdict"),
                        "whale": opp.get("components", {}).get("whale", {}).get("verdict")
                    }
                }
                for opp in top_opportunities
            ]
        }

        return dashboard

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error generating dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SCANNER CONTROL ENDPOINTS ====================
# AUTO-SCANNER DISABLED: Consumes too much API quota (similar to existing auto_scanner)
#
# Scanner endpoints have been disabled to prevent excessive API usage.
# The auto-scanner would consume ~10 API calls per coin, and with automatic
# scanning every 30 minutes, this quickly adds up to hundreds of calls per hour.
#
# Use manual endpoints instead:
# - GET /api/prepump/analyze/{symbol} - Analyze single coin on-demand
# - POST /api/prepump/scan - Scan specific coins manually
# - GET /api/prepump/quick-scan - Quick scan 15 popular coins
# - POST /api/prepump/gpt/analyze - GPT Actions compatible endpoint
# - POST /api/prepump/gpt/scan - GPT Actions scan endpoint
#
# These manual endpoints provide the same functionality without the
# continuous API consumption of an auto-scanner.

# ==================== GPT ACTIONS COMPATIBLE ENDPOINTS ====================

from pydantic import BaseModel, Field

class GPTPrePumpRequest(BaseModel):
    """Flat structure for GPT Actions compatibility"""
    symbol: str = Field(..., description="Cryptocurrency symbol (BTC, ETH, SOL, etc.)")
    timeframe: Optional[str] = Field("1HRS", description="Analysis timeframe (1MIN, 5MIN, 1HRS, 4HRS, 1DAY)")


class GPTPrePumpScanRequest(BaseModel):
    """Flat structure for multi-symbol scan"""
    symbols: str = Field(..., description="Comma-separated symbols (e.g., 'BTC,ETH,SOL')")
    min_score: Optional[float] = Field(60.0, ge=0, le=100, description="Minimum score threshold")
    timeframe: Optional[str] = Field("1HRS", description="Analysis timeframe")


@router.post("/gpt/analyze", summary="Pre-Pump Analysis (GPT Actions Compatible)")
async def analyze_prepump_gpt(request: GPTPrePumpRequest):
    """
    Get pre-pump analysis for a single symbol - GPT Actions compatible version

    **Usage from GPT:**
    Ask ChatGPT: "Analyze BTC for pre-pump signals"

    **Returns:**
    - score: Pre-pump score (0-100)
    - confidence: Signal confidence (0-100)
    - verdict: VERY_STRONG_PRE_PUMP, STRONG_PRE_PUMP, MODERATE_PRE_PUMP, etc.
    - recommendation: Trading action with entry/exit strategy
    - components: Breakdown of accumulation, reversal, whale signals
    """
    try:
        engine = get_engine()
        result = await engine.analyze_pre_pump(request.symbol, request.timeframe)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))

        return {
            "ok": True,
            "data": result,
            "operation": "prepump.analyze"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GPT] Error analyzing {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gpt/scan", summary="Multi-Symbol Pre-Pump Scan (GPT Actions Compatible)")
async def scan_prepump_gpt(request: GPTPrePumpScanRequest):
    """
    Scan multiple symbols for pre-pump opportunities - GPT Actions compatible

    **Usage from GPT:**
    Ask ChatGPT: "Scan BTC, ETH, SOL, AVAX for pre-pump signals"

    **Returns:**
    - totalScanned: Number of symbols analyzed
    - totalFound: Number of opportunities above min_score
    - summary: Breakdown by signal strength
    - topOpportunities: Top ranked opportunities
    """
    try:
        # Parse comma-separated symbols
        symbol_list = [s.strip().upper() for s in request.symbols.split(",") if s.strip()]

        if not symbol_list:
            raise HTTPException(status_code=400, detail="No valid symbols provided")

        if len(symbol_list) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 symbols per scan (to save API quota)")

        engine = get_engine()
        result = await engine.scan_market(
            symbols=symbol_list,
            timeframe=request.timeframe,
            min_score=request.min_score
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Scan failed"))

        return {
            "ok": True,
            "data": result,
            "operation": "prepump.scan"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GPT] Error scanning symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gpt/quick-scan", summary="Quick Pre-Pump Scan (GPT Actions Compatible)")
async def quick_scan_gpt():
    """
    Quick scan of top 15 popular coins for pre-pump signals - GPT Actions compatible

    **Usage from GPT:**
    Ask ChatGPT: "Show me today's pre-pump opportunities" or "Quick pre-pump scan"

    **Returns:**
    Top opportunities from 15 popular cryptocurrencies
    """
    try:
        # Limit to 15 coins to save API quota
        popular_coins = [
            "BTC", "ETH", "BNB", "SOL", "ADA",
            "XRP", "DOT", "AVAX", "MATIC", "LINK",
            "UNI", "ATOM", "LTC", "NEAR", "FTM"
        ]

        engine = get_engine()
        result = await engine.scan_market(popular_coins, "1HRS", min_score=60.0)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Quick scan failed"))

        return {
            "ok": True,
            "data": result,
            "operation": "prepump.quick_scan"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GPT] Error in quick scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

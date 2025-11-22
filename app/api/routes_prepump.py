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
from app.services.pre_pump_scanner import (
    get_pre_pump_scanner,
    start_pre_pump_scanner,
    stop_pre_pump_scanner
)
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

@router.post("/scanner/start")
async def start_scanner(
    scan_interval_minutes: int = Query(30, description="Minutes between scans", ge=5, le=1440),
    min_score: float = Query(70.0, description="Minimum score to alert", ge=0, le=100),
    min_confidence: float = Query(60.0, description="Minimum confidence to alert", ge=0, le=100),
    enable_alerts: bool = Query(True, description="Enable Telegram notifications")
):
    """
    Start the automated pre-pump scanner

    **Example:**
    ```
    POST /api/prepump/scanner/start?scan_interval_minutes=30&min_score=70&enable_alerts=true
    ```

    **Returns:**
    Scanner status and configuration
    """
    try:
        scanner = get_pre_pump_scanner()

        if scanner and scanner.is_running:
            return {
                "success": False,
                "message": "Scanner already running",
                "status": await scanner.get_status()
            }

        logger.info("[API] Starting pre-pump scanner...")

        scanner = await start_pre_pump_scanner(
            scan_interval_minutes=scan_interval_minutes,
            min_score=min_score,
            min_confidence=min_confidence,
            enable_alerts=enable_alerts
        )

        return {
            "success": True,
            "message": "Pre-pump scanner started successfully",
            "status": await scanner.get_status()
        }

    except Exception as e:
        logger.error(f"[API] Error starting scanner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scanner/stop")
async def stop_scanner():
    """
    Stop the automated pre-pump scanner

    **Example:**
    ```
    POST /api/prepump/scanner/stop
    ```

    **Returns:**
    Success confirmation
    """
    try:
        scanner = get_pre_pump_scanner()

        if not scanner or not scanner.is_running:
            return {
                "success": False,
                "message": "Scanner not running"
            }

        logger.info("[API] Stopping pre-pump scanner...")
        await stop_pre_pump_scanner()

        return {
            "success": True,
            "message": "Pre-pump scanner stopped successfully"
        }

    except Exception as e:
        logger.error(f"[API] Error stopping scanner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scanner/status")
async def get_scanner_status():
    """
    Get scanner status and configuration

    **Example:**
    ```
    GET /api/prepump/scanner/status
    ```

    **Returns:**
    Scanner status, configuration, and statistics
    """
    try:
        scanner = get_pre_pump_scanner()

        if not scanner:
            return {
                "success": True,
                "running": False,
                "message": "Scanner not initialized"
            }

        status = await scanner.get_status()
        return {
            "success": True,
            **status
        }

    except Exception as e:
        logger.error(f"[API] Error getting scanner status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scanner/trigger")
async def trigger_manual_scan():
    """
    Trigger a manual scan immediately (doesn't affect scheduled scans)

    **Example:**
    ```
    POST /api/prepump/scanner/trigger
    ```

    **Returns:**
    Scan completion status
    """
    try:
        scanner = get_pre_pump_scanner()

        if not scanner:
            raise HTTPException(
                status_code=400,
                detail="Scanner not initialized. Start the scanner first."
            )

        logger.info("[API] Triggering manual pre-pump scan...")
        result = await scanner.trigger_manual_scan()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error triggering manual scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scanner/watchlist")
async def update_watchlist(watchlist: List[str]):
    """
    Update the scanner's watchlist

    **Example:**
    ```
    POST /api/prepump/scanner/watchlist
    Body: ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
    ```

    **Returns:**
    Updated watchlist confirmation
    """
    try:
        if not watchlist:
            raise HTTPException(status_code=400, detail="Watchlist cannot be empty")

        if len(watchlist) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 symbols allowed")

        scanner = get_pre_pump_scanner()

        if not scanner:
            raise HTTPException(
                status_code=400,
                detail="Scanner not initialized. Start the scanner first."
            )

        await scanner.update_watchlist(watchlist)

        return {
            "success": True,
            "message": f"Watchlist updated with {len(watchlist)} symbols",
            "watchlist": watchlist
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error updating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

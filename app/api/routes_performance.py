"""
Performance Tracking API Routes

Provides endpoints for signal performance tracking and analytics.

Endpoints:
- GET /performance/stats - Overall performance statistics
- GET /performance/report - Comprehensive performance report
- GET /performance/by-scanner - Performance by scanner type
- GET /performance/by-tier - Performance by tier classification
- GET /performance/by-interval - Performance by time interval
- GET /performance/top-performers - Best and worst signals/symbols
- POST /performance/track-signal - Manually track a signal
- GET /performance/tracker-stats - Performance tracker statistics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.services.performance_tracker import performance_tracker, track_signal
from app.services.win_rate_analyzer import (
    win_rate_analyzer,
    get_performance_report,
    get_win_rates
)
from app.utils.logger import default_logger

router = APIRouter(prefix="/performance", tags=["Performance Tracking"])
logger = default_logger


class TrackSignalRequest(BaseModel):
    """Request model for manually tracking a signal"""
    id: str
    symbol: str
    signal: str  # LONG or SHORT
    price: float
    timestamp: Optional[str] = None
    unified_score: Optional[float] = None
    tier: Optional[str] = None
    scanner_type: Optional[str] = None


@router.get("/stats", summary="Get Overall Performance Statistics")
async def get_overall_performance_stats(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get overall performance statistics for the specified period

    Includes:
    - Total signals tracked
    - Win/loss/neutral counts and rates
    - Average win/loss percentages
    - Total P&L percentage

    Args:
        days: Number of days to analyze (default 30)

    Returns:
        Overall performance statistics

    Example:
    ```
    GET /performance/stats?days=30
    ```
    """
    try:
        logger.info(f"Getting overall performance stats ({days} days)")

        stats = await get_win_rates(days)

        return {
            "ok": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting overall stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance stats: {str(e)}"
        )


@router.get("/report", summary="Get Comprehensive Performance Report")
async def get_comprehensive_performance_report(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get comprehensive performance report with all analytics

    Includes:
    - Overall statistics
    - Performance by scanner type
    - Performance by tier classification
    - Performance by time interval
    - Performance by signal type (LONG/SHORT)
    - Top and bottom performers
    - Actionable recommendations

    Args:
        days: Number of days to analyze (default 30)

    Returns:
        Complete performance report with recommendations

    Example:
    ```
    GET /performance/report?days=7
    ```
    """
    try:
        logger.info(f"Generating comprehensive performance report ({days} days)")

        report = await get_performance_report(days)

        return {
            "ok": True,
            "data": report
        }

    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/by-scanner", summary="Get Performance by Scanner Type")
async def get_performance_by_scanner(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get performance statistics broken down by scanner type

    Scanners analyzed:
    - smart_money: Smart Money accumulation/distribution
    - mss: Multi-modal signal score
    - technical: Technical indicators (RSI, etc.)
    - social: LunarCrush social momentum

    Args:
        days: Number of days to analyze (default 30)

    Returns:
        Performance statistics for each scanner type

    Example:
    ```
    GET /performance/by-scanner?days=30
    ```
    """
    try:
        logger.info(f"Getting performance by scanner ({days} days)")

        stats = await win_rate_analyzer.get_stats_by_scanner(days)

        return {
            "ok": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting scanner stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scanner statistics: {str(e)}"
        )


@router.get("/by-tier", summary="Get Performance by Tier Classification")
async def get_performance_by_tier(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get performance statistics broken down by tier classification

    Tiers analyzed:
    - TIER_1_MUST_BUY: Unified score ≥85
    - TIER_2_STRONG_BUY: Unified score ≥70
    - TIER_3_WATCHLIST: Unified score ≥55
    - TIER_4_NEUTRAL: Unified score <55

    This shows whether higher-tier signals actually perform better,
    validating the unified scoring system.

    Args:
        days: Number of days to analyze (default 30)

    Returns:
        Performance statistics for each tier

    Example:
    ```
    GET /performance/by-tier?days=30
    ```
    """
    try:
        logger.info(f"Getting performance by tier ({days} days)")

        stats = await win_rate_analyzer.get_stats_by_tier(days)

        return {
            "ok": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting tier stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tier statistics: {str(e)}"
        )


@router.get("/by-interval", summary="Get Performance by Time Interval")
async def get_performance_by_interval(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get performance statistics broken down by time interval

    Intervals tracked:
    - 1h: Short-term momentum
    - 4h: Intraday performance
    - 24h: Daily performance
    - 7d: Weekly trend
    - 30d: Monthly outcome

    Shows which timeframes have the best win rates.

    Args:
        days: Number of days to analyze (default 30)

    Returns:
        Performance statistics for each interval

    Example:
    ```
    GET /performance/by-interval?days=30
    ```
    """
    try:
        logger.info(f"Getting performance by interval ({days} days)")

        stats = await win_rate_analyzer.get_stats_by_interval(days)

        return {
            "ok": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting interval stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get interval statistics: {str(e)}"
        )


@router.get("/by-signal-type", summary="Get Performance by Signal Type")
async def get_performance_by_signal_type(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get performance statistics broken down by signal type (LONG vs SHORT)

    Shows whether LONG or SHORT signals perform better.

    Args:
        days: Number of days to analyze (default 30)

    Returns:
        Performance statistics for LONG and SHORT signals

    Example:
    ```
    GET /performance/by-signal-type?days=30
    ```
    """
    try:
        logger.info(f"Getting performance by signal type ({days} days)")

        stats = await win_rate_analyzer.get_stats_by_signal_type(days)

        return {
            "ok": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting signal type stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get signal type statistics: {str(e)}"
        )


@router.get("/top-performers", summary="Get Top and Bottom Performers")
async def get_top_performers(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    limit: int = Query(10, description="Number of results per category", ge=1, le=50)
) -> Dict[str, Any]:
    """
    Get top and bottom performing signals and symbols

    Returns:
    - Best individual signals (highest P&L)
    - Worst individual signals (lowest P&L)
    - Best symbols (highest win rate, min 3 signals)
    - Worst symbols (lowest win rate, min 3 signals)

    Args:
        days: Number of days to analyze (default 30)
        limit: Max results per category (default 10)

    Returns:
        Top and bottom performers

    Example:
    ```
    GET /performance/top-performers?days=7&limit=5
    ```
    """
    try:
        logger.info(f"Getting top performers ({days} days, limit {limit})")

        performers = await win_rate_analyzer.get_top_performers(days, limit)

        return {
            "ok": True,
            "data": performers
        }

    except Exception as e:
        logger.error(f"Error getting top performers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get top performers: {str(e)}"
        )


@router.post("/track-signal", summary="Manually Track a Signal")
async def track_signal_manually(request: TrackSignalRequest) -> Dict[str, Any]:
    """
    Manually start tracking a signal's performance

    Schedules automated outcome checks at:
    - 1 hour
    - 4 hours
    - 24 hours
    - 7 days
    - 30 days

    Args:
        request: Signal details including:
            - id: Signal ID
            - symbol: Cryptocurrency symbol
            - signal: LONG or SHORT
            - price: Entry price
            - timestamp: Entry timestamp (optional, defaults to now)
            - unified_score: Unified score (optional)
            - tier: Tier classification (optional)
            - scanner_type: Scanner that generated signal (optional)

    Returns:
        Confirmation that signal is being tracked

    Example:
    ```json
    {
      "id": "signal_123",
      "symbol": "BTC",
      "signal": "LONG",
      "price": 45000.0,
      "unified_score": 87.5,
      "tier": "TIER_1_MUST_BUY",
      "scanner_type": "smart_money"
    }
    ```
    """
    try:
        logger.info(f"Manually tracking signal {request.id} ({request.symbol})")

        # Convert to dict
        signal_data = {
            "id": request.id,
            "symbol": request.symbol,
            "signal": request.signal,
            "price": request.price,
            "timestamp": request.timestamp,
            "unified_score": request.unified_score,
            "tier": request.tier,
            "scanner_type": request.scanner_type
        }

        # Start tracking
        await track_signal(signal_data)

        return {
            "ok": True,
            "data": {
                "message": f"Signal {request.id} is now being tracked",
                "signal_id": request.id,
                "symbol": request.symbol,
                "intervals_scheduled": ["1h", "4h", "24h", "7d", "30d"]
            }
        }

    except Exception as e:
        logger.error(f"Error tracking signal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track signal: {str(e)}"
        )


@router.get("/tracker-stats", summary="Get Performance Tracker Statistics")
async def get_tracker_statistics() -> Dict[str, Any]:
    """
    Get statistics about the performance tracker itself

    Returns:
    - Total signals tracked
    - Outcomes checked
    - Wins/losses/neutral counts
    - Win rate
    - Scheduled jobs count

    Example:
    ```
    GET /performance/tracker-stats
    ```
    """
    try:
        logger.info("Getting performance tracker stats")

        stats = performance_tracker.get_stats()

        return {
            "ok": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting tracker stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tracker stats: {str(e)}"
        )


@router.post("/tracker/start", summary="Start Performance Tracker")
async def start_performance_tracker() -> Dict[str, Any]:
    """
    Start the performance tracker scheduler

    Example:
    ```
    POST /performance/tracker/start
    ```
    """
    try:
        logger.info("Starting performance tracker")

        await performance_tracker.start()

        return {
            "ok": True,
            "data": {
                "message": "Performance tracker started",
                "status": "running"
            }
        }

    except Exception as e:
        logger.error(f"Error starting tracker: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start tracker: {str(e)}"
        )


@router.post("/tracker/stop", summary="Stop Performance Tracker")
async def stop_performance_tracker() -> Dict[str, Any]:
    """
    Stop the performance tracker scheduler

    Example:
    ```
    POST /performance/tracker/stop
    ```
    """
    try:
        logger.info("Stopping performance tracker")

        await performance_tracker.stop()

        return {
            "ok": True,
            "data": {
                "message": "Performance tracker stopped",
                "status": "stopped"
            }
        }

    except Exception as e:
        logger.error(f"Error stopping tracker: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop tracker: {str(e)}"
        )

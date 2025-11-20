"""
Analytics API Routes
Advanced signal history analytics and insights using PostgreSQL

Updated with GPT-5.1 self-evaluation support via analytics_service
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
from aiocache import Cache
from aiocache.serializers import JsonSerializer

from app.storage.signal_db import signal_db

# ADDED FOR PHASE 2 - Verdict performance analytics
from app.services.verdict_analyzer import verdict_analyzer
from app.services.outcome_tracker import outcome_tracker

# ADDED FOR GPT-5.1 SELF-EVALUATION - Performance analytics service
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Insights"])

# Configure cache (in-memory with 5-minute TTL for analytics)
cache = Cache(Cache.MEMORY, serializer=JsonSerializer(), ttl=300)


@router.get("/summary")
async def get_analytics_summary(
    symbol: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get comprehensive analytics summary (Cached for 5 minutes)
    
    Query Parameters:
    - symbol: Filter by symbol (optional, e.g., BTC, ETH)
    - days: Number of days to analyze (1-365, default: 7)
    
    Returns:
    - Signal distribution (LONG/SHORT/NEUTRAL counts)
    - Score statistics (avg, min, max)
    - Confidence distribution
    - Trading insights
    """
    try:
        # Create cache key from parameters
        cache_key = f"analytics_summary_{symbol or 'all'}_{days}"
        
        # Try to get from cache first
        cached_result = await cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # If not in cache, fetch from database
        summary = await signal_db.get_analytics_summary(symbol=symbol, days=days)
        
        # Store in cache
        await cache.set(cache_key, summary)
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/history/latest")
async def get_latest_signals(
    limit: int = Query(default=50, ge=1, le=1000, description="Number of signals to return")
):
    """
    Get latest signals - most recent first (Cached for 2 minutes)
    
    Query Parameters:
    - limit: Maximum number of signals (1-1000, default: 50)
    """
    try:
        cache_key = f"latest_signals_{limit}"
        
        # Check cache
        cached_result = await cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Fetch from database
        signals = await signal_db.get_latest_signals(limit=limit)
        result = {
            "success": True,
            "count": len(signals),
            "signals": signals
        }
        
        # Cache with shorter TTL (2 minutes) since this changes frequently
        await cache.set(cache_key, result, ttl=120)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")


@router.get("/history/{symbol}")
async def get_symbol_history(
    symbol: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    """
    Get signal history for specific symbol (Cached for 5 minutes)
    
    Path Parameters:
    - symbol: Cryptocurrency symbol (e.g., BTC, ETH, SOL)
    
    Query Parameters:
    - limit: Number of signals per page (1-500, default: 50)
    - offset: Pagination offset (default: 0)
    
    Supports pagination for large datasets
    """
    try:
        cache_key = f"symbol_history_{symbol.upper()}_{limit}_{offset}"
        
        # Check cache
        cached_result = await cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Fetch from database
        signals = await signal_db.get_signals_by_symbol(symbol, limit=limit, offset=offset)
        total = await signal_db.get_signal_count(symbol=symbol)
        
        result = {
            "success": True,
            "symbol": symbol.upper(),
            "total": total,
            "count": len(signals),
            "offset": offset,
            "limit": limit,
            "has_more": (offset + len(signals)) < total,
            "signals": signals
        }
        
        # Cache result
        await cache.set(cache_key, result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get symbol history: {str(e)}")


@router.get("/history/date-range")
async def get_signals_by_date_range(
    start_date: str = Query(..., description="Start date (ISO format: YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (ISO format: YYYY-MM-DD)"),
    symbol: Optional[str] = None
):
    """
    Get signals within specific date range (Cached for 10 minutes)
    
    Query Parameters:
    - start_date: Start date (required, format: YYYY-MM-DD)
    - end_date: End date (required, format: YYYY-MM-DD)
    - symbol: Filter by symbol (optional)
    
    Example: /analytics/history/date-range?start_date=2025-11-01&end_date=2025-11-10
    """
    try:
        cache_key = f"date_range_{start_date}_{end_date}_{symbol or 'all'}"
        
        # Check cache
        cached_result = await cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        if start_dt > end_dt:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        # Get signals
        signals = await signal_db.get_signals_by_date_range(start_dt, end_dt, symbol=symbol)
        
        result = {
            "success": True,
            "start_date": start_date,
            "end_date": end_date,
            "symbol": symbol if symbol else "ALL",
            "count": len(signals),
            "signals": signals
        }
        
        # Cache result (historical data, longer TTL - 10 minutes)
        await cache.set(cache_key, result, ttl=600)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")


@router.get("/performance/{symbol}")
async def get_signal_performance(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=200)
):
    """
    **Comprehensive Signal Performance Analysis (Enhanced for GPT-5.1)**
    
    Analyzes signal performance with:
    - Overall win rate and ROI metrics
    - Recent signal outcomes with verdict tracking
    - Verdict effectiveness breakdown (CONFIRM/DOWNSIZE/SKIP)
    - Risk mode performance (REDUCED/NORMAL/AGGRESSIVE)
    - Interval performance (1h, 4h, 24h, 7d, 30d)
    
    Path Parameters:
    - symbol: Cryptocurrency symbol (e.g., BTC, ETH)
    
    Query Parameters:
    - days: Number of days to analyze (1-365, default: 30)
    - limit: Maximum recent signals to return (1-200, default: 50)
    
    **Use Cases:**
    - GPT-5.1 self-evaluation with historical context
    - Performance tracking and win rate calculation
    - Verdict optimization analysis
    - Risk mode effectiveness comparison
    """
    try:
        # Use new analytics_service for comprehensive performance data
        result = await analytics_service.get_symbol_performance(
            symbol=symbol.upper(),
            days_back=days,
            limit=limit
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze performance: {str(e)}")


@router.get("/stats/overview")
async def get_overall_stats():
    """
    Get overall system statistics
    
    Returns:
    - Total signals across all symbols
    - Most active symbols
    - Global signal distribution
    - Database health metrics
    """
    try:
        # Get total count
        total_count = await signal_db.get_signal_count()
        
        # Get recent signals to analyze symbols
        recent_signals = await signal_db.get_latest_signals(limit=1000)
        
        # Symbol distribution
        symbol_counts = {}
        for signal in recent_signals:
            sym = signal.get("symbol", "UNKNOWN")
            symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
        
        # Sort by count
        top_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get 7-day summary
        week_summary = await signal_db.get_analytics_summary(days=7)
        
        return {
            "success": True,
            "total_signals": total_count,
            "recent_signals_analyzed": len(recent_signals),
            "top_symbols": [{"symbol": sym, "count": count} for sym, count in top_symbols],
            "last_7_days": week_summary,
            "database": "postgresql",
            "status": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


# ============================================================================
# GPT-5.1 SELF-EVALUATION ENDPOINTS
# Optimized for AI historical context and performance tracking
# ============================================================================

@router.get("/performance/summary")
async def get_performance_summary(
    days: int = Query(default=30, ge=1, le=365)
):
    """
    **Overall Performance Summary Across All Symbols (GPT-5.1 Optimized)**
    
    Provides system-wide performance metrics:
    - Total signals and symbols tracked
    - Overall win rate and average ROI
    - Top performing symbols (ranked by win rate)
    - Verdict effectiveness stats (CONFIRM/DOWNSIZE/SKIP)
    - Risk mode effectiveness stats (REDUCED/NORMAL/AGGRESSIVE)
    
    Query Parameters:
    - days: Number of days to analyze (1-365, default: 30)
    
    **Use Cases:**
    - System-wide performance overview
    - Identify best performing symbols
    - Compare verdict types globally
    - Track overall AI Judge effectiveness
    - GPT-5.1 macro-level context
    
    **Example:**
    ```
    GET /analytics/performance/summary?days=30
    ```
    """
    try:
        result = await analytics_service.get_overall_summary(days_back=days)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/history/latest/{symbol}")
async def get_latest_signal_history(
    symbol: str,
    limit: int = Query(default=5, ge=1, le=20)
):
    """
    **Latest Signal History for Symbol (GPT Actions Optimized)**
    
    Optimized for GPT-5.1 self-evaluation during signal generation.
    Returns recent signal outcomes with quick performance metrics.
    
    Path Parameters:
    - symbol: Cryptocurrency symbol (e.g., BTC, ETH)
    
    Query Parameters:
    - limit: Number of recent signals (1-20, default: 5)
    
    Returns:
    - Recent signal count and win rate
    - Average ROI from recent signals
    - Last N signals with outcomes and verdicts
    
    **Use Cases:**
    - GPT-5.1 historical context injection before verdict
    - Quick recent performance check
    - Self-evaluation for AI decision making
    - Learning from past verdict outcomes
    
    **Example:**
    ```
    GET /analytics/history/latest/BTC?limit=5
    ```
    
    **RPC Alternative:**
    ```json
    POST /invoke
    {
      "operation": "analytics.history.latest",
      "symbol": "BTC",
      "limit": 5
    }
    ```
    """
    try:
        result = await analytics_service.get_latest_history(
            symbol=symbol.upper(),
            limit=limit
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


# ============================================================================
# PHASE 2: VERDICT PERFORMANCE ANALYTICS
# Track AI verdict accuracy and effectiveness
# ============================================================================

@router.get("/verdict-performance")
async def get_verdict_performance(
    verdict: Optional[str] = Query(None, description="Filter by verdict: CONFIRM, DOWNSIZE, SKIP, WAIT"),
    interval: str = Query("24h", description="Time interval to analyze: 1h, 4h, 24h"),
    days: int = Query(30, description="Number of days to analyze")
):
    """
    **AI Verdict Performance Metrics**
    
    Answers key questions:
    - Does CONFIRM really lead to profits?
    - Does SKIP avoid losses?
    - Does DOWNSIZE reduce drawdown?
    
    Returns:
    - Win rate per verdict type
    - Average P&L percentage
    - Total signals tracked
    - Min/max P&L
    - Standard deviation
    """
    try:
        if interval not in ["1h", "4h", "24h"]:
            raise HTTPException(status_code=400, detail="Invalid interval. Use: 1h, 4h, or 24h")
        
        if verdict and verdict not in ["CONFIRM", "DOWNSIZE", "SKIP", "WAIT"]:
            raise HTTPException(status_code=400, detail="Invalid verdict type")
        
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        result = await verdict_analyzer.get_verdict_performance(
            verdict=verdict,
            interval=interval,
            days_back=days
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/verdict-comparison")
async def compare_verdicts(
    interval: str = Query("24h", description="Time interval: 1h, 4h, 24h"),
    days: int = Query(30, description="Number of days to analyze")
):
    """
    **Compare All Verdict Types**
    
    Provides comparative analysis showing:
    - Which verdicts perform best
    - Effectiveness of AI risk management
    - Data-driven insights and recommendations
    """
    try:
        if interval not in ["1h", "4h", "24h"]:
            raise HTTPException(status_code=400, detail="Invalid interval")
        
        result = await verdict_analyzer.compare_verdicts(
            interval=interval,
            days_back=days
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@router.get("/outcomes-history")
async def get_outcomes_history(
    symbol: Optional[str] = Query(None, description="Filter by symbol (BTC, ETH, etc)"),
    verdict: Optional[str] = Query(None, description="Filter by verdict type"),
    limit: int = Query(100, description="Number of records to return")
):
    """
    **Detailed Signal Outcomes History**
    
    Useful for:
    - Debugging tracking system
    - Detailed analysis of specific signals
    - Reviewing individual outcomes across all timeframes
    """
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        
        results = await verdict_analyzer.get_signal_outcomes_history(
            symbol=symbol,
            verdict=verdict,
            limit=limit
        )
        
        return {
            "total_returned": len(results),
            "filters": {
                "symbol": symbol,
                "verdict": verdict
            },
            "outcomes": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History error: {str(e)}")


@router.post("/process-pending-outcomes")
async def process_pending_outcomes():
    """
    **Manually Process Pending Outcomes**
    
    Triggers immediate processing of all pending outcome tracking:
    - Finds signals needing 1h/4h/24h price updates
    - Fetches current prices
    - Calculates P&L
    - Updates outcomes in database
    
    Normally runs automatically in background
    """
    try:
        await outcome_tracker.process_pending_outcomes()
        
        return {
            "success": True,
            "message": "Pending outcomes processed successfully",
            "note": "Check logs for detailed results"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/tracking-stats")
async def get_tracking_stats():
    """
    **Outcome Tracking System Statistics**
    
    Shows:
    - Total outcomes tracked
    - Pending tracking jobs per interval
    - Completion rates
    - System health
    """
    try:
        # Get counts for each tracking interval
        pending_1h = await outcome_tracker.get_pending_outcomes("1h")
        pending_4h = await outcome_tracker.get_pending_outcomes("4h")
        pending_24h = await outcome_tracker.get_pending_outcomes("24h")
        
        return {
            "tracking_system": "operational",
            "pending_tracking": {
                "1h": len(pending_1h),
                "4h": len(pending_4h),
                "24h": len(pending_24h)
            },
            "thresholds": {
                "win_threshold": f"{outcome_tracker.win_threshold}%",
                "loss_threshold": f"{outcome_tracker.loss_threshold}%"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

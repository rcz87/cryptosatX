"""
Analytics API Routes
Advanced signal history analytics and insights using PostgreSQL
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from app.storage.signal_db import signal_db

router = APIRouter(prefix="/analytics", tags=["Analytics & Insights"])


@router.get("/summary")
async def get_analytics_summary(
    symbol: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get comprehensive analytics summary
    
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
        summary = await signal_db.get_analytics_summary(symbol=symbol, days=days)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/history/latest")
async def get_latest_signals(
    limit: int = Query(default=50, ge=1, le=1000, description="Number of signals to return")
):
    """
    Get latest signals (most recent first)
    
    Query Parameters:
    - limit: Maximum number of signals (1-1000, default: 50)
    """
    try:
        signals = await signal_db.get_latest_signals(limit=limit)
        return {
            "success": True,
            "count": len(signals),
            "signals": signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")


@router.get("/history/{symbol}")
async def get_symbol_history(
    symbol: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    """
    Get signal history for specific symbol
    
    Path Parameters:
    - symbol: Cryptocurrency symbol (e.g., BTC, ETH, SOL)
    
    Query Parameters:
    - limit: Number of signals per page (1-500, default: 50)
    - offset: Pagination offset (default: 0)
    
    Supports pagination for large datasets
    """
    try:
        signals = await signal_db.get_signals_by_symbol(symbol, limit=limit, offset=offset)
        total = await signal_db.get_signal_count(symbol=symbol)
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "total": total,
            "count": len(signals),
            "offset": offset,
            "limit": limit,
            "has_more": (offset + len(signals)) < total,
            "signals": signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get symbol history: {str(e)}")


@router.get("/history/date-range")
async def get_signals_by_date_range(
    start_date: str = Query(..., description="Start date (ISO format: YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (ISO format: YYYY-MM-DD)"),
    symbol: Optional[str] = None
):
    """
    Get signals within specific date range
    
    Query Parameters:
    - start_date: Start date (required, format: YYYY-MM-DD)
    - end_date: End date (required, format: YYYY-MM-DD)
    - symbol: Filter by symbol (optional)
    
    Example: /analytics/history/date-range?start_date=2025-11-01&end_date=2025-11-10
    """
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        if start_dt > end_dt:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        # Get signals
        signals = await signal_db.get_signals_by_date_range(start_dt, end_dt, symbol=symbol)
        
        return {
            "success": True,
            "start_date": start_date,
            "end_date": end_date,
            "symbol": symbol if symbol else "ALL",
            "count": len(signals),
            "signals": signals
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")


@router.get("/performance/{symbol}")
async def get_signal_performance(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Analyze signal performance for specific symbol
    
    Path Parameters:
    - symbol: Cryptocurrency symbol
    
    Query Parameters:
    - days: Number of days to analyze (1-365, default: 30)
    
    Returns performance metrics, trends, and insights
    """
    try:
        # Get analytics summary
        summary = await signal_db.get_analytics_summary(symbol=symbol, days=days)
        
        # Get recent signals for trend analysis
        recent_signals = await signal_db.get_signals_by_symbol(symbol, limit=100)
        
        # Calculate additional metrics
        if recent_signals:
            # Score trend (last 10 vs previous 10)
            last_10_scores = [s["score"] for s in recent_signals[:10]]
            prev_10_scores = [s["score"] for s in recent_signals[10:20]] if len(recent_signals) >= 20 else []
            
            last_avg = sum(last_10_scores) / len(last_10_scores) if last_10_scores else 0
            prev_avg = sum(prev_10_scores) / len(prev_10_scores) if prev_10_scores else last_avg
            
            score_trend = "improving" if last_avg > prev_avg else "declining" if last_avg < prev_avg else "stable"
        else:
            score_trend = "unknown"
            last_avg = 0
        
        return {
            **summary,
            "recent_performance": {
                "last_10_avg_score": round(last_avg, 2),
                "trend": score_trend,
                "total_recent_signals": len(recent_signals)
            }
        }
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

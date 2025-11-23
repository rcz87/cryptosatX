"""
Analytics Service for CryptoSatX

Provides performance analytics and historical signal data for:
- Self-evaluation by GPT-5.1 AI Judge
- Performance tracking and win rate calculation
- Verdict effectiveness analysis
- Risk mode optimization

Queries data from:
- signals table (signal history)
- signal_outcomes table (verdict accuracy tracking)
- performance_outcomes table (multi-interval P&L tracking)
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncpg
from decimal import Decimal

from app.utils.logger import default_logger, get_wib_datetime


class AnalyticsService:
    """
    Analytics service for querying signal performance data
    
    Provides historical context for GPT-5.1 self-evaluation and
    performance tracking across different symbols, verdicts, and risk modes.
    """
    
    def __init__(self):
        self.logger = default_logger
        self.db_url = os.getenv("DATABASE_URL")
        self.pool: Optional[asyncpg.Pool] = None
        
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create database connection pool"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.db_url, min_size=1, max_size=5)
        return self.pool
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def get_symbol_performance(
        self, 
        symbol: str,
        days_back: int = 30,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance analytics for a specific symbol
        
        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC")
            days_back: How many days of history to analyze
            limit: Maximum number of recent signals to return
            
        Returns:
            Dict with:
            - total_signals: Total number of signals generated
            - win_rate: Overall win percentage
            - avg_roi: Average ROI across all intervals
            - recent_signals: Last N signals with outcomes
            - verdict_performance: Win rates per verdict type
            - risk_mode_performance: Win rates per risk mode
            - interval_performance: Performance breakdown by interval
        """
        try:
            pool = await self._get_pool()
            cutoff_date = get_wib_datetime() - timedelta(days=days_back)
            
            async with pool.acquire() as conn:
                # Get total signals and outcomes
                total_query = """
                    SELECT COUNT(DISTINCT po.signal_id) as total_signals,
                           AVG(CASE WHEN po.outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate,
                           AVG(po.pnl_pct) as avg_roi
                    FROM performance_outcomes po
                    WHERE po.symbol = $1
                      AND po.checked_at >= $2
                      AND po.outcome IS NOT NULL
                """
                total_row = await conn.fetchrow(total_query, symbol, cutoff_date)
                
                # Get recent signals with outcomes
                recent_query = """
                    SELECT DISTINCT ON (po.signal_id)
                           po.signal_id,
                           po.signal_type,
                           po.entry_price,
                           po.pnl_pct,
                           po.outcome,
                           po.unified_score,
                           po.tier,
                           po.scanner_type,
                           po.checked_at as timestamp,
                           so.verdict,
                           so.risk_mode
                    FROM performance_outcomes po
                    LEFT JOIN signal_outcomes so ON so.signal_id::text = po.signal_id
                    WHERE po.symbol = $1
                      AND po.checked_at >= $2
                      AND po.interval = '24h'
                    ORDER BY po.signal_id, po.checked_at DESC
                    LIMIT $3
                """
                recent_rows = await conn.fetch(recent_query, symbol, cutoff_date, limit)
                
                # Get verdict performance breakdown
                verdict_query = """
                    SELECT so.verdict,
                           COUNT(*) as count,
                           AVG(CASE WHEN po.outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate,
                           AVG(po.pnl_pct) as avg_roi
                    FROM signal_outcomes so
                    JOIN performance_outcomes po ON so.signal_id::text = po.signal_id
                    WHERE so.symbol = $1
                      AND so.entry_timestamp >= $2
                      AND po.outcome IS NOT NULL
                      AND po.interval = '24h'
                    GROUP BY so.verdict
                """
                verdict_rows = await conn.fetch(verdict_query, symbol, cutoff_date)
                
                # Get risk mode performance breakdown
                risk_query = """
                    SELECT so.risk_mode,
                           COUNT(*) as count,
                           AVG(CASE WHEN po.outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate,
                           AVG(po.pnl_pct) as avg_roi
                    FROM signal_outcomes so
                    JOIN performance_outcomes po ON so.signal_id::text = po.signal_id
                    WHERE so.symbol = $1
                      AND so.entry_timestamp >= $2
                      AND po.outcome IS NOT NULL
                      AND po.interval = '24h'
                      AND so.risk_mode IS NOT NULL
                    GROUP BY so.risk_mode
                """
                risk_rows = await conn.fetch(risk_query, symbol, cutoff_date)
                
                # Get interval performance breakdown
                interval_query = """
                    SELECT po.interval,
                           COUNT(*) as count,
                           AVG(CASE WHEN po.outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate,
                           AVG(po.pnl_pct) as avg_roi,
                           MAX(po.pnl_pct) as max_roi,
                           MIN(po.pnl_pct) as min_roi
                    FROM performance_outcomes po
                    WHERE po.symbol = $1
                      AND po.checked_at >= $2
                      AND po.outcome IS NOT NULL
                    GROUP BY po.interval
                    ORDER BY 
                        CASE po.interval
                            WHEN '1h' THEN 1
                            WHEN '4h' THEN 2
                            WHEN '24h' THEN 3
                            WHEN '7d' THEN 4
                            WHEN '30d' THEN 5
                        END
                """
                interval_rows = await conn.fetch(interval_query, symbol, cutoff_date)
            
            # Format results
            return {
                "symbol": symbol,
                "days_analyzed": days_back,
                "total_signals": int(total_row["total_signals"] or 0),
                "win_rate": float(total_row["win_rate"] or 0),
                "avg_roi": float(total_row["avg_roi"] or 0),
                "recent_signals": [
                    {
                        "signal_id": row["signal_id"],
                        "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
                        "signal_type": row["signal_type"],
                        "verdict": row["verdict"],
                        "risk_mode": row["risk_mode"],
                        "entry_price": float(row["entry_price"]) if row["entry_price"] else None,
                        "roi_24h": float(row["pnl_pct"]) if row["pnl_pct"] else None,
                        "outcome": row["outcome"],
                        "unified_score": float(row["unified_score"]) if row["unified_score"] else None,
                        "tier": row["tier"],
                        "scanner_type": row["scanner_type"]
                    }
                    for row in recent_rows
                ],
                "verdict_performance": {
                    row["verdict"]: {
                        "count": int(row["count"]),
                        "win_rate": float(row["win_rate"] or 0),
                        "avg_roi": float(row["avg_roi"] or 0)
                    }
                    for row in verdict_rows
                },
                "risk_mode_performance": {
                    row["risk_mode"]: {
                        "count": int(row["count"]),
                        "win_rate": float(row["win_rate"] or 0),
                        "avg_roi": float(row["avg_roi"] or 0)
                    }
                    for row in risk_rows
                },
                "interval_performance": {
                    row["interval"]: {
                        "count": int(row["count"]),
                        "win_rate": float(row["win_rate"] or 0),
                        "avg_roi": float(row["avg_roi"] or 0),
                        "max_roi": float(row["max_roi"] or 0),
                        "min_roi": float(row["min_roi"] or 0)
                    }
                    for row in interval_rows
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting symbol performance for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "total_signals": 0,
                "win_rate": 0,
                "avg_roi": 0,
                "recent_signals": [],
                "verdict_performance": {},
                "risk_mode_performance": {},
                "interval_performance": {}
            }
    
    async def get_overall_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get overall performance summary across all symbols
        
        Args:
            days_back: How many days of history to analyze
            
        Returns:
            Dict with:
            - total_signals: Total signals across all symbols
            - total_symbols: Number of unique symbols tracked
            - overall_win_rate: Win rate across all signals
            - overall_avg_roi: Average ROI across all signals
            - top_performers: Best performing symbols
            - verdict_stats: Verdict effectiveness stats
            - risk_mode_stats: Risk mode effectiveness stats
        """
        try:
            pool = await self._get_pool()
            cutoff_date = get_wib_datetime() - timedelta(days=days_back)
            
            async with pool.acquire() as conn:
                # Overall stats
                overall_query = """
                    SELECT COUNT(DISTINCT po.signal_id) as total_signals,
                           COUNT(DISTINCT po.symbol) as total_symbols,
                           AVG(CASE WHEN po.outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate,
                           AVG(po.pnl_pct) as avg_roi
                    FROM performance_outcomes po
                    WHERE po.checked_at >= $1
                      AND po.outcome IS NOT NULL
                      AND po.interval = '24h'
                """
                overall_row = await conn.fetchrow(overall_query, cutoff_date)
                
                # Top performing symbols
                top_query = """
                    SELECT po.symbol,
                           COUNT(DISTINCT po.signal_id) as signal_count,
                           AVG(CASE WHEN po.outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate,
                           AVG(po.pnl_pct) as avg_roi
                    FROM performance_outcomes po
                    WHERE po.checked_at >= $1
                      AND po.outcome IS NOT NULL
                      AND po.interval = '24h'
                    GROUP BY po.symbol
                    HAVING COUNT(DISTINCT po.signal_id) >= 3
                    ORDER BY win_rate DESC, avg_roi DESC
                    LIMIT 10
                """
                top_rows = await conn.fetch(top_query, cutoff_date)
                
                # Verdict stats (all symbols)
                verdict_query = """
                    SELECT so.verdict,
                           COUNT(*) as count,
                           AVG(CASE WHEN po.outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate,
                           AVG(po.pnl_pct) as avg_roi
                    FROM signal_outcomes so
                    JOIN performance_outcomes po ON so.signal_id::text = po.signal_id
                    WHERE so.entry_timestamp >= $1
                      AND po.outcome IS NOT NULL
                      AND po.interval = '24h'
                    GROUP BY so.verdict
                    ORDER BY count DESC
                """
                verdict_rows = await conn.fetch(verdict_query, cutoff_date)
                
                # Risk mode stats (all symbols)
                risk_query = """
                    SELECT so.risk_mode,
                           COUNT(*) as count,
                           AVG(CASE WHEN po.outcome = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate,
                           AVG(po.pnl_pct) as avg_roi
                    FROM signal_outcomes so
                    JOIN performance_outcomes po ON so.signal_id::text = po.signal_id
                    WHERE so.entry_timestamp >= $1
                      AND po.outcome IS NOT NULL
                      AND po.interval = '24h'
                      AND so.risk_mode IS NOT NULL
                    GROUP BY so.risk_mode
                    ORDER BY count DESC
                """
                risk_rows = await conn.fetch(risk_query, cutoff_date)
            
            return {
                "days_analyzed": days_back,
                "total_signals": int(overall_row["total_signals"] or 0),
                "total_symbols": int(overall_row["total_symbols"] or 0),
                "overall_win_rate": float(overall_row["win_rate"] or 0),
                "overall_avg_roi": float(overall_row["avg_roi"] or 0),
                "top_performers": [
                    {
                        "symbol": row["symbol"],
                        "signal_count": int(row["signal_count"]),
                        "win_rate": float(row["win_rate"] or 0),
                        "avg_roi": float(row["avg_roi"] or 0)
                    }
                    for row in top_rows
                ],
                "verdict_stats": {
                    row["verdict"]: {
                        "count": int(row["count"]),
                        "win_rate": float(row["win_rate"] or 0),
                        "avg_roi": float(row["avg_roi"] or 0)
                    }
                    for row in verdict_rows
                },
                "risk_mode_stats": {
                    row["risk_mode"]: {
                        "count": int(row["count"]),
                        "win_rate": float(row["win_rate"] or 0),
                        "avg_roi": float(row["avg_roi"] or 0)
                    }
                    for row in risk_rows
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting overall summary: {e}")
            return {
                "error": str(e),
                "total_signals": 0,
                "total_symbols": 0,
                "overall_win_rate": 0,
                "overall_avg_roi": 0,
                "top_performers": [],
                "verdict_stats": {},
                "risk_mode_stats": {}
            }
    
    async def get_latest_history(
        self, 
        symbol: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get latest signal history for a symbol (optimized for GPT Actions)
        
        This is the primary method for GPT-5.1 self-evaluation, providing
        recent performance context for decision making.
        
        Args:
            symbol: Cryptocurrency symbol
            limit: Number of recent signals to return
            
        Returns:
            Dict with recent signal outcomes and performance metrics
        """
        try:
            pool = await self._get_pool()
            
            async with pool.acquire() as conn:
                # Get last 5 signals with 24h outcomes
                query = """
                    SELECT DISTINCT ON (po.signal_id)
                           po.signal_id,
                           po.signal_type,
                           po.entry_price,
                           po.pnl_pct as roi_24h,
                           po.outcome,
                           po.unified_score,
                           po.tier,
                           po.checked_at as timestamp,
                           so.verdict,
                           so.risk_mode,
                           so.entry_timestamp
                    FROM performance_outcomes po
                    LEFT JOIN signal_outcomes so ON so.signal_id::text = po.signal_id
                    WHERE po.symbol = $1
                      AND po.interval = '24h'
                      AND po.outcome IS NOT NULL
                    ORDER BY po.signal_id, po.checked_at DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, symbol, limit)
                
                # Calculate quick stats from recent signals
                if rows:
                    wins = sum(1 for r in rows if r["outcome"] == "WIN")
                    win_rate = (wins / len(rows)) * 100
                    avg_roi = sum(float(r["roi_24h"] or 0) for r in rows) / len(rows)
                else:
                    win_rate = 0
                    avg_roi = 0
            
            return {
                "symbol": symbol,
                "recent_count": len(rows),
                "recent_win_rate": round(win_rate, 1),
                "recent_avg_roi": round(avg_roi, 2),
                "recent_signals": [
                    {
                        "timestamp": row["entry_timestamp"].isoformat() if row["entry_timestamp"] else None,
                        "signal": row["signal_type"],
                        "verdict": row["verdict"],
                        "risk_mode": row["risk_mode"],
                        "entry_price": float(row["entry_price"]) if row["entry_price"] else None,
                        "roi_24h": float(row["roi_24h"]) if row["roi_24h"] else None,
                        "outcome": row["outcome"],
                        "unified_score": float(row["unified_score"]) if row["unified_score"] else None
                    }
                    for row in rows
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting latest history for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "recent_count": 0,
                "recent_win_rate": 0,
                "recent_avg_roi": 0,
                "recent_signals": []
            }


# Global analytics service instance
analytics_service = AnalyticsService()

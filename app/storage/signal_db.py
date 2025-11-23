"""
Signal Database Service
Provides async CRUD operations for signal history using PostgreSQL
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.utils.logger import get_wib_datetime
import asyncpg

from app.storage.database import db


class SignalDatabaseService:
    """
    Signal persistence and query service using PostgreSQL
    Provides high-performance async operations for signal history
    """
    
    async def save_signal(self, signal_data: Dict) -> int:
        """
        Save signal to database
        
        Args:
            signal_data: Signal dictionary from /signals endpoint
            
        Returns:
            Signal ID (primary key)
        """
        async with db.acquire() as conn:
            signal_id = await conn.fetchval("""
                INSERT INTO signals (
                    symbol, signal, score, confidence, price, timestamp,
                    reasons, metrics, comprehensive_metrics, lunarcrush_metrics,
                    coinapi_metrics, smc_analysis, ai_validation
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                ) RETURNING id
            """,
                signal_data.get("symbol"),
                signal_data.get("signal"),
                signal_data.get("score"),
                signal_data.get("confidence"),
                signal_data.get("price"),
                datetime.fromisoformat(signal_data.get("timestamp").replace('Z', '+00:00')),
                json.dumps(signal_data.get("reasons", [])),
                json.dumps(signal_data.get("metrics", {})),
                json.dumps(signal_data.get("comprehensiveMetrics", {})),
                json.dumps(signal_data.get("lunarCrushMetrics", {})),
                json.dumps(signal_data.get("coinAPIMetrics", {})),
                json.dumps(signal_data.get("smcAnalysis", {})),
                json.dumps(signal_data.get("ai_validation", {}))
            )
            
            return signal_id
    
    async def get_latest_signals(self, limit: int = 100) -> List[Dict]:
        """
        Get latest signals (most recent first)
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of signal dictionaries
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, symbol, signal, score, confidence, price, timestamp,
                    reasons, metrics, comprehensive_metrics, lunarcrush_metrics,
                    coinapi_metrics, smc_analysis, ai_validation, created_at
                FROM signals
                ORDER BY timestamp DESC
                LIMIT $1
            """, limit)
            
            return [self._row_to_dict(row) for row in rows]
    
    async def get_signals_by_symbol(
        self, 
        symbol: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get signals for specific symbol
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC, ETH)
            limit: Maximum number of signals
            offset: Pagination offset
            
        Returns:
            List of signal dictionaries
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, symbol, signal, score, confidence, price, timestamp,
                    reasons, metrics, comprehensive_metrics, lunarcrush_metrics,
                    coinapi_metrics, smc_analysis, ai_validation, created_at
                FROM signals
                WHERE symbol = $1
                ORDER BY timestamp DESC
                LIMIT $2 OFFSET $3
            """, symbol.upper(), limit, offset)
            
            return [self._row_to_dict(row) for row in rows]
    
    async def get_signals_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: Optional[str] = None
    ) -> List[Dict]:
        """
        Get signals within date range
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            symbol: Optional symbol filter
            
        Returns:
            List of signal dictionaries
        """
        async with db.acquire() as conn:
            if symbol:
                rows = await conn.fetch("""
                    SELECT 
                        id, symbol, signal, score, confidence, price, timestamp,
                        reasons, metrics, comprehensive_metrics, lunarcrush_metrics,
                        coinapi_metrics, smc_analysis, ai_validation, created_at
                    FROM signals
                    WHERE symbol = $1 AND timestamp BETWEEN $2 AND $3
                    ORDER BY timestamp DESC
                """, symbol.upper(), start_date, end_date)
            else:
                rows = await conn.fetch("""
                    SELECT 
                        id, symbol, signal, score, confidence, price, timestamp,
                        reasons, metrics, comprehensive_metrics, lunarcrush_metrics,
                        coinapi_metrics, smc_analysis, ai_validation, created_at
                    FROM signals
                    WHERE timestamp BETWEEN $1 AND $2
                    ORDER BY timestamp DESC
                """, start_date, end_date)
            
            return [self._row_to_dict(row) for row in rows]
    
    async def get_analytics_summary(self, symbol: Optional[str] = None, days: int = 7) -> Dict:
        """
        Get analytics summary for signals
        
        Args:
            symbol: Optional symbol filter
            days: Number of days to analyze
            
        Returns:
            Analytics dictionary with counts, averages, etc.
        """
        async with db.acquire() as conn:
            cutoff_date = get_wib_datetime() - timedelta(days=days)
            
            if symbol:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN signal = 'LONG' THEN 1 END) as long_count,
                        COUNT(CASE WHEN signal = 'SHORT' THEN 1 END) as short_count,
                        COUNT(CASE WHEN signal = 'NEUTRAL' THEN 1 END) as neutral_count,
                        AVG(score) as avg_score,
                        MIN(score) as min_score,
                        MAX(score) as max_score,
                        COUNT(CASE WHEN confidence = 'high' THEN 1 END) as high_confidence_count,
                        COUNT(CASE WHEN confidence = 'medium' THEN 1 END) as medium_confidence_count,
                        COUNT(CASE WHEN confidence = 'low' THEN 1 END) as low_confidence_count
                    FROM signals
                    WHERE symbol = $1 AND timestamp >= $2
                """, symbol.upper(), cutoff_date)
            else:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN signal = 'LONG' THEN 1 END) as long_count,
                        COUNT(CASE WHEN signal = 'SHORT' THEN 1 END) as short_count,
                        COUNT(CASE WHEN signal = 'NEUTRAL' THEN 1 END) as neutral_count,
                        AVG(score) as avg_score,
                        MIN(score) as min_score,
                        MAX(score) as max_score,
                        COUNT(CASE WHEN confidence = 'high' THEN 1 END) as high_confidence_count,
                        COUNT(CASE WHEN confidence = 'medium' THEN 1 END) as medium_confidence_count,
                        COUNT(CASE WHEN confidence = 'low' THEN 1 END) as low_confidence_count
                    FROM signals
                    WHERE timestamp >= $1
                """, cutoff_date)
            
            return {
                "period_days": days,
                "symbol": symbol if symbol else "ALL",
                "total_signals": stats["total_signals"],
                "signal_distribution": {
                    "LONG": stats["long_count"],
                    "SHORT": stats["short_count"],
                    "NEUTRAL": stats["neutral_count"]
                },
                "score_stats": {
                    "average": float(stats["avg_score"]) if stats["avg_score"] else 0,
                    "min": float(stats["min_score"]) if stats["min_score"] else 0,
                    "max": float(stats["max_score"]) if stats["max_score"] else 0
                },
                "confidence_distribution": {
                    "high": stats["high_confidence_count"],
                    "medium": stats["medium_confidence_count"],
                    "low": stats["low_confidence_count"]
                }
            }
    
    async def get_signal_count(self, symbol: Optional[str] = None) -> int:
        """Get total signal count"""
        async with db.acquire() as conn:
            if symbol:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM signals WHERE symbol = $1",
                    symbol.upper()
                )
            else:
                count = await conn.fetchval("SELECT COUNT(*) FROM signals")
            
            return count
    
    def _row_to_dict(self, row: asyncpg.Record) -> Dict:
        """Convert database row to dictionary"""
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "signal": row["signal"],
            "score": float(row["score"]),
            "confidence": row["confidence"],
            "price": float(row["price"]),
            "timestamp": row["timestamp"].isoformat(),
            "reasons": json.loads(row["reasons"]) if row["reasons"] else [],
            "metrics": json.loads(row["metrics"]) if row["metrics"] else {},
            "comprehensiveMetrics": json.loads(row["comprehensive_metrics"]) if row["comprehensive_metrics"] else {},
            "lunarCrushMetrics": json.loads(row["lunarcrush_metrics"]) if row["lunarcrush_metrics"] else {},
            "coinAPIMetrics": json.loads(row["coinapi_metrics"]) if row["coinapi_metrics"] else {},
            "smcAnalysis": json.loads(row["smc_analysis"]) if row["smc_analysis"] else {},
            "ai_validation": json.loads(row["ai_validation"]) if row["ai_validation"] else {},
            "created_at": row["created_at"].isoformat()
        }


# Global instance
signal_db = SignalDatabaseService()

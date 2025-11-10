"""
MSS Signal Database Service
Provides async CRUD operations for MSS (Multi-Modal Signal Score) signal history
Uses existing signals table with MSS-specific data mapping
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncpg

from app.storage.database import db


class MSSSignalDatabaseService:
    """
    MSS signal persistence and query service using PostgreSQL
    Stores MSS discoveries with complete 3-phase breakdown
    """
    
    async def save_mss_signal(self, mss_data: Dict) -> int:
        """
        Save MSS signal to database
        
        Args:
            mss_data: MSS analysis dictionary from /mss/analyze endpoint
            Expected fields:
                - symbol: str
                - mss_score: float (0-100)
                - signal: str (STRONG_LONG, MODERATE_LONG, LONG, etc.)
                - confidence: str (very_high, high, medium, low)
                - phases: dict with phase1_discovery, phase2_confirmation, phase3_validation
                - timestamp: str (ISO format)
                - price: float (optional)
                - market_cap_usd: float (optional)
                - fdv_usd: float (optional)
            
        Returns:
            Signal ID (primary key)
        """
        async with db.acquire() as conn:
            # Extract phase data
            phases = mss_data.get("phases", {})
            phase1 = phases.get("phase1_discovery", {})
            phase2 = phases.get("phase2_confirmation", {})
            phase3 = phases.get("phase3_validation", {})
            
            # Get price from phase1 breakdown if not provided
            price = mss_data.get("price")
            if not price:
                p1_breakdown = phase1.get("breakdown", {})
                price = p1_breakdown.get("current_price", 0.0)
            
            # Build top reasons/factors for MSS
            reasons = []
            if phase1.get("status") == "PASS":
                reasons.append(f"Discovery: {phase1.get('score', 0):.1f}/30 pts")
            if phase2.get("score", 0) >= 17.5:
                reasons.append(f"Social Momentum: {phase2.get('score', 0):.1f}/35 pts")
            if phase3.get("score", 0) >= 20:
                reasons.append(f"Whale Validation: {phase3.get('score', 0):.1f}/35 pts")
            
            # Prepare MSS-specific metrics
            mss_metrics = {
                "signal_type": "MSS",
                "mss_score": mss_data.get("mss_score", 0),
                "phase_scores": {
                    "phase1_discovery": phase1.get("score", 0),
                    "phase2_confirmation": phase2.get("score", 0),
                    "phase3_validation": phase3.get("score", 0)
                },
                "phase_breakdowns": {
                    "phase1": phase1.get("breakdown", {}),
                    "phase2": phase2.get("breakdown", {}),
                    "phase3": phase3.get("breakdown", {})
                },
                "market_data": {
                    "price": price,
                    "market_cap_usd": mss_data.get("market_cap_usd"),
                    "fdv_usd": mss_data.get("fdv_usd")
                }
            }
            
            # Insert into signals table
            signal_id = await conn.fetchval("""
                INSERT INTO signals (
                    symbol, signal, score, confidence, price, timestamp,
                    reasons, metrics, comprehensive_metrics
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9
                ) RETURNING id
            """,
                mss_data.get("symbol", "").upper(),
                f"MSS_{mss_data.get('signal', 'NEUTRAL').upper()}",  # Prefix with MSS_
                float(mss_data.get("mss_score", 0)),
                mss_data.get("confidence", "medium"),
                float(price) if price else 0.0,
                datetime.fromisoformat(mss_data.get("timestamp", datetime.utcnow().isoformat()).replace('Z', '+00:00')),
                json.dumps(reasons),
                json.dumps(mss_metrics),
                json.dumps(phases)  # Store complete phase data
            )
            
            return signal_id
    
    async def get_latest_mss_signals(self, limit: int = 100) -> List[Dict]:
        """
        Get latest MSS signals (most recent first)
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of MSS signal dictionaries
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, symbol, signal, score, confidence, price, timestamp,
                    reasons, metrics, comprehensive_metrics, created_at
                FROM signals
                WHERE signal LIKE 'MSS_%'
                ORDER BY timestamp DESC
                LIMIT $1
            """, limit)
            
            return [self._row_to_mss_dict(row) for row in rows]
    
    async def get_mss_signals_by_symbol(
        self, 
        symbol: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get MSS signals for specific symbol
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC, PEPE)
            limit: Maximum number of signals
            offset: Pagination offset
            
        Returns:
            List of MSS signal dictionaries
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, symbol, signal, score, confidence, price, timestamp,
                    reasons, metrics, comprehensive_metrics, created_at
                FROM signals
                WHERE symbol = $1 AND signal LIKE 'MSS_%'
                ORDER BY timestamp DESC
                LIMIT $2 OFFSET $3
            """, symbol.upper(), limit, offset)
            
            return [self._row_to_mss_dict(row) for row in rows]
    
    async def get_high_score_mss_signals(
        self,
        min_score: float = 75.0,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get high-scoring MSS signals (MSS >= threshold)
        
        Args:
            min_score: Minimum MSS score threshold
            limit: Maximum number of signals
            
        Returns:
            List of high-scoring MSS signal dictionaries
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, symbol, signal, score, confidence, price, timestamp,
                    reasons, metrics, comprehensive_metrics, created_at
                FROM signals
                WHERE signal LIKE 'MSS_%' AND score >= $1
                ORDER BY score DESC, timestamp DESC
                LIMIT $2
            """, min_score, limit)
            
            return [self._row_to_mss_dict(row) for row in rows]
    
    async def get_mss_analytics_summary(
        self,
        symbol: Optional[str] = None,
        days: int = 7
    ) -> Dict:
        """
        Get analytics summary for MSS signals
        
        Args:
            symbol: Optional symbol filter
            days: Number of days to analyze
            
        Returns:
            Analytics dictionary with MSS-specific stats
        """
        async with db.acquire() as conn:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            if symbol:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN signal = 'MSS_STRONG_LONG' THEN 1 END) as strong_long_count,
                        COUNT(CASE WHEN signal = 'MSS_MODERATE_LONG' THEN 1 END) as moderate_long_count,
                        COUNT(CASE WHEN signal = 'MSS_LONG' THEN 1 END) as long_count,
                        COUNT(CASE WHEN signal = 'MSS_WEAK_LONG' THEN 1 END) as weak_long_count,
                        COUNT(CASE WHEN score >= 80 THEN 1 END) as diamond_tier,
                        COUNT(CASE WHEN score >= 65 AND score < 80 THEN 1 END) as gold_tier,
                        COUNT(CASE WHEN score >= 50 AND score < 65 THEN 1 END) as silver_tier,
                        AVG(score) as avg_mss_score,
                        MIN(score) as min_mss_score,
                        MAX(score) as max_mss_score
                    FROM signals
                    WHERE symbol = $1 AND signal LIKE 'MSS_%' AND timestamp >= $2
                """, symbol.upper(), cutoff_date)
            else:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN signal = 'MSS_STRONG_LONG' THEN 1 END) as strong_long_count,
                        COUNT(CASE WHEN signal = 'MSS_MODERATE_LONG' THEN 1 END) as moderate_long_count,
                        COUNT(CASE WHEN signal = 'MSS_LONG' THEN 1 END) as long_count,
                        COUNT(CASE WHEN signal = 'MSS_WEAK_LONG' THEN 1 END) as weak_long_count,
                        COUNT(CASE WHEN score >= 80 THEN 1 END) as diamond_tier,
                        COUNT(CASE WHEN score >= 65 AND score < 80 THEN 1 END) as gold_tier,
                        COUNT(CASE WHEN score >= 50 AND score < 65 THEN 1 END) as silver_tier,
                        AVG(score) as avg_mss_score,
                        MIN(score) as min_mss_score,
                        MAX(score) as max_mss_score
                    FROM signals
                    WHERE signal LIKE 'MSS_%' AND timestamp >= $1
                """, cutoff_date)
            
            return {
                "period_days": days,
                "symbol": symbol if symbol else "ALL",
                "total_mss_signals": stats["total_signals"],
                "signal_distribution": {
                    "STRONG_LONG": stats["strong_long_count"],
                    "MODERATE_LONG": stats["moderate_long_count"],
                    "LONG": stats["long_count"],
                    "WEAK_LONG": stats["weak_long_count"]
                },
                "tier_distribution": {
                    "diamond": stats["diamond_tier"],  # MSS >= 80
                    "gold": stats["gold_tier"],         # MSS 65-79
                    "silver": stats["silver_tier"]      # MSS 50-64
                },
                "mss_score_stats": {
                    "average": float(stats["avg_mss_score"]) if stats["avg_mss_score"] else 0,
                    "min": float(stats["min_mss_score"]) if stats["min_mss_score"] else 0,
                    "max": float(stats["max_mss_score"]) if stats["max_mss_score"] else 0
                }
            }
    
    async def get_mss_signal_count(self, symbol: Optional[str] = None) -> int:
        """Get total MSS signal count"""
        async with db.acquire() as conn:
            if symbol:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM signals WHERE symbol = $1 AND signal LIKE 'MSS_%'",
                    symbol.upper()
                )
            else:
                count = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE signal LIKE 'MSS_%'")
            
            return count
    
    def _row_to_mss_dict(self, row: asyncpg.Record) -> Dict:
        """Convert database row to MSS dictionary"""
        metrics = json.loads(row["metrics"]) if row["metrics"] else {}
        phases = json.loads(row["comprehensive_metrics"]) if row["comprehensive_metrics"] else {}
        
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "signal": row["signal"].replace("MSS_", ""),  # Remove MSS_ prefix for display
            "mss_score": float(row["score"]),
            "confidence": row["confidence"],
            "price": float(row["price"]),
            "timestamp": row["timestamp"].isoformat(),
            "reasons": json.loads(row["reasons"]) if row["reasons"] else [],
            "phase_scores": metrics.get("phase_scores", {}),
            "phase_breakdowns": metrics.get("phase_breakdowns", {}),
            "market_data": metrics.get("market_data", {}),
            "phases": phases,  # Complete phase data
            "created_at": row["created_at"].isoformat()
        }


# Global instance
mss_db = MSSSignalDatabaseService()

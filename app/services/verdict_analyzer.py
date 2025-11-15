"""
Verdict Performance Analyzer
Calculates AI verdict accuracy metrics and win rates
Phase 2: AI Verdict Validation System
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.storage.database import db
from app.utils.logger import logger


class VerdictAnalyzer:
    """
    Analyzes AI verdict performance by calculating:
    - Win rates per verdict type (CONFIRM, DOWNSIZE, SKIP)
    - Average P&L per verdict
    - Accuracy metrics over time
    - Drawdown reduction effectiveness
    """

    async def get_verdict_performance(
        self,
        verdict: Optional[str] = None,
        interval: str = "24h",
        days_back: int = 30
    ) -> Dict:
        """
        Get performance metrics for AI verdicts
        
        Args:
            verdict: Filter by specific verdict (CONFIRM/DOWNSIZE/SKIP/WAIT) or None for all
            interval: Which timeframe to analyze (1h/4h/24h)
            days_back: How many days of history to analyze
            
        Returns:
            Dict with win_rate, avg_pnl, total_signals, etc.
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Build query based on verdict filter
            if verdict:
                verdict_filter = "AND verdict = $2" if db.use_postgres else "AND verdict = ?"
                params = [cutoff_date, verdict] if db.use_postgres else (cutoff_date.isoformat(), verdict)
            else:
                verdict_filter = ""
                params = [cutoff_date] if db.use_postgres else (cutoff_date.isoformat(),)
            
            if db.use_postgres:
                async with db.pool.acquire() as conn:
                    # Get aggregate stats
                    query = f"""
                        SELECT 
                            verdict,
                            COUNT(*) as total_signals,
                            COUNT(CASE WHEN outcome_{interval} = 'WIN' THEN 1 END) as wins,
                            COUNT(CASE WHEN outcome_{interval} = 'LOSS' THEN 1 END) as losses,
                            COUNT(CASE WHEN outcome_{interval} = 'NEUTRAL' THEN 1 END) as neutral,
                            AVG(pnl_{interval}) as avg_pnl,
                            MIN(pnl_{interval}) as min_pnl,
                            MAX(pnl_{interval}) as max_pnl,
                            STDDEV(pnl_{interval}) as pnl_stddev
                        FROM signal_outcomes
                        WHERE entry_timestamp >= $1
                        AND outcome_{interval} IS NOT NULL
                        {verdict_filter}
                        GROUP BY verdict
                        ORDER BY verdict
                    """
                    
                    records = await conn.fetch(query, *params)
                    
                    results = []
                    for r in records:
                        total = r["total_signals"]
                        wins = r["wins"]
                        losses = r["losses"]
                        
                        results.append({
                            "verdict": r["verdict"],
                            "total_signals": total,
                            "wins": wins,
                            "losses": losses,
                            "neutral": r["neutral"],
                            "win_rate": (wins / total * 100) if total > 0 else 0,
                            "loss_rate": (losses / total * 100) if total > 0 else 0,
                            "avg_pnl": float(r["avg_pnl"]) if r["avg_pnl"] else 0,
                            "min_pnl": float(r["min_pnl"]) if r["min_pnl"] else 0,
                            "max_pnl": float(r["max_pnl"]) if r["max_pnl"] else 0,
                            "pnl_stddev": float(r["pnl_stddev"]) if r["pnl_stddev"] else 0
                        })
                    
                    return {
                        "interval": interval,
                        "days_analyzed": days_back,
                        "verdicts": results,
                        "total_tracked": sum(r["total_signals"] for r in results)
                    }
            else:
                # SQLite version
                async with db.sqlite_conn.execute(
                    f"""
                    SELECT 
                        verdict,
                        COUNT(*) as total_signals,
                        SUM(CASE WHEN outcome_{interval} = 'WIN' THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN outcome_{interval} = 'LOSS' THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN outcome_{interval} = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral,
                        AVG(pnl_{interval}) as avg_pnl,
                        MIN(pnl_{interval}) as min_pnl,
                        MAX(pnl_{interval}) as max_pnl
                    FROM signal_outcomes
                    WHERE entry_timestamp >= ?
                    AND outcome_{interval} IS NOT NULL
                    {verdict_filter}
                    GROUP BY verdict
                    ORDER BY verdict
                    """,
                    params
                ) as cursor:
                    rows = await cursor.fetchall()
                    
                    results = []
                    for row in rows:
                        total = row[1]
                        wins = row[2]
                        losses = row[3]
                        
                        results.append({
                            "verdict": row[0],
                            "total_signals": total,
                            "wins": wins,
                            "losses": losses,
                            "neutral": row[4],
                            "win_rate": (wins / total * 100) if total > 0 else 0,
                            "loss_rate": (losses / total * 100) if total > 0 else 0,
                            "avg_pnl": float(row[5]) if row[5] else 0,
                            "min_pnl": float(row[6]) if row[6] else 0,
                            "max_pnl": float(row[7]) if row[7] else 0,
                            "pnl_stddev": 0
                        })
                    
                    return {
                        "interval": interval,
                        "days_analyzed": days_back,
                        "verdicts": results,
                        "total_tracked": sum(r["total_signals"] for r in results)
                    }
        
        except Exception as e:
            logger.error(f" Failed to get verdict performance: {e}")
            return {
                "error": str(e),
                "interval": interval,
                "verdicts": []
            }

    async def compare_verdicts(
        self,
        interval: str = "24h",
        days_back: int = 30
    ) -> Dict:
        """
        Compare performance across all verdict types
        Returns comparative analysis showing which verdicts perform best
        """
        try:
            all_verdicts = await self.get_verdict_performance(
                verdict=None,
                interval=interval,
                days_back=days_back
            )
            
            if "error" in all_verdicts:
                return all_verdicts
            
            verdicts = all_verdicts["verdicts"]
            
            # Calculate comparative metrics
            confirm_stats = next((v for v in verdicts if v["verdict"] == "CONFIRM"), None)
            downsize_stats = next((v for v in verdicts if v["verdict"] == "DOWNSIZE"), None)
            skip_stats = next((v for v in verdicts if v["verdict"] == "SKIP"), None)
            
            comparison = {
                "interval": interval,
                "days_analyzed": days_back,
                "total_signals": all_verdicts["total_tracked"],
                "summary": {
                    "CONFIRM": {
                        "total": confirm_stats["total_signals"] if confirm_stats else 0,
                        "win_rate": confirm_stats["win_rate"] if confirm_stats else 0,
                        "avg_pnl": confirm_stats["avg_pnl"] if confirm_stats else 0,
                        "description": "Signals where AI confirmed the original signal"
                    },
                    "DOWNSIZE": {
                        "total": downsize_stats["total_signals"] if downsize_stats else 0,
                        "win_rate": downsize_stats["win_rate"] if downsize_stats else 0,
                        "avg_pnl": downsize_stats["avg_pnl"] if downsize_stats else 0,
                        "description": "Signals where AI suggested reduced position"
                    },
                    "SKIP": {
                        "total": skip_stats["total_signals"] if skip_stats else 0,
                        "win_rate": skip_stats["win_rate"] if skip_stats else 0,
                        "avg_pnl": skip_stats["avg_pnl"] if skip_stats else 0,
                        "description": "Signals where AI recommended skipping (not tracking these)"
                    }
                },
                "insights": []
            }
            
            # Generate insights
            if confirm_stats and confirm_stats["win_rate"] > 60:
                comparison["insights"].append(
                    f"✅ CONFIRM verdicts have {confirm_stats['win_rate']:.1f}% win rate - AI confirmation is valuable"
                )
            
            if downsize_stats and downsize_stats["avg_pnl"] > 0:
                comparison["insights"].append(
                    f"📊 DOWNSIZE strategy shows {downsize_stats['avg_pnl']:+.2f}% avg P&L - risk reduction working"
                )
            
            if skip_stats and skip_stats["avg_pnl"] < 0:
                comparison["insights"].append(
                    f"⚠️ SKIP verdicts would have resulted in {skip_stats['avg_pnl']:.2f}% avg loss - AI protection effective"
                )
            
            return comparison
            
        except Exception as e:
            logger.error(f" Failed to compare verdicts: {e}")
            return {"error": str(e)}

    async def get_signal_outcomes_history(
        self,
        symbol: Optional[str] = None,
        verdict: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get detailed history of signal outcomes
        Useful for debugging and detailed analysis
        """
        try:
            filters = []
            params = []
            
            if symbol:
                if db.use_postgres:
                    filters.append(f"symbol = ${len(params) + 1}")
                else:
                    filters.append("symbol = ?")
                params.append(symbol)
            
            if verdict:
                if db.use_postgres:
                    filters.append(f"verdict = ${len(params) + 1}")
                else:
                    filters.append("verdict = ?")
                params.append(verdict)
            
            where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
            
            if db.use_postgres:
                async with db.pool.acquire() as conn:
                    query = f"""
                        SELECT 
                            id, symbol, signal_type, verdict, risk_mode,
                            entry_price, entry_timestamp,
                            price_1h, price_4h, price_24h,
                            outcome_1h, outcome_4h, outcome_24h,
                            pnl_1h, pnl_4h, pnl_24h
                        FROM signal_outcomes
                        {where_clause}
                        ORDER BY entry_timestamp DESC
                        LIMIT {limit}
                    """
                    
                    records = await conn.fetch(query, *params)
                    
                    return [
                        {
                            "id": r["id"],
                            "symbol": r["symbol"],
                            "signal_type": r["signal_type"],
                            "verdict": r["verdict"],
                            "risk_mode": r["risk_mode"],
                            "entry_price": float(r["entry_price"]),
                            "entry_timestamp": r["entry_timestamp"].isoformat(),
                            "outcomes": {
                                "1h": {
                                    "price": float(r["price_1h"]) if r["price_1h"] else None,
                                    "outcome": r["outcome_1h"],
                                    "pnl": float(r["pnl_1h"]) if r["pnl_1h"] else None
                                },
                                "4h": {
                                    "price": float(r["price_4h"]) if r["price_4h"] else None,
                                    "outcome": r["outcome_4h"],
                                    "pnl": float(r["pnl_4h"]) if r["pnl_4h"] else None
                                },
                                "24h": {
                                    "price": float(r["price_24h"]) if r["price_24h"] else None,
                                    "outcome": r["outcome_24h"],
                                    "pnl": float(r["pnl_24h"]) if r["pnl_24h"] else None
                                }
                            }
                        }
                        for r in records
                    ]
            
        except Exception as e:
            logger.error(f" Failed to get outcomes history: {e}")
            return []


# Global instance
verdict_analyzer = VerdictAnalyzer()

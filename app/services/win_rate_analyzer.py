"""
Win Rate Analyzer for CryptoSatX

Analyzes signal performance to calculate win rates and optimize system.

Analyzes by:
- Scanner type (Smart Money, MSS, Technical, Social)
- Tier classification (TIER_1, TIER_2, TIER_3, TIER_4)
- Time interval (1h, 4h, 24h, 7d, 30d)
- Signal type (LONG, SHORT)

Metrics calculated:
- Total signals tracked
- Win count & win rate
- Loss count & loss rate
- Average win/loss percentage
- Best performing scanner/tier
- ROI estimation
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.utils.logger import default_logger


class WinRateAnalyzer:
    """
    Performance analytics engine

    Calculates win rates and identifies best performing strategies
    for signal optimization.
    """

    def __init__(self):
        self.logger = default_logger
        self.logger.info("WinRateAnalyzer initialized")

    async def get_overall_stats(self, days: int = 30) -> Dict:
        """
        Get overall performance statistics

        Args:
            days: Number of days to analyze (default 30)

        Returns:
            {
                "total_signals": int,
                "outcomes_checked": int,
                "wins": int,
                "losses": int,
                "neutral": int,
                "win_rate": float,
                "loss_rate": float,
                "neutral_rate": float,
                "avg_win_pct": float,
                "avg_loss_pct": float,
                "total_pnl_pct": float,
                "period_days": int
            }
        """
        try:
            from app.storage.database import db

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get outcome statistics
            result = await db.fetch_one(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN outcome = 'NEUTRAL' THEN 1 END) as neutral,
                    AVG(CASE WHEN outcome = 'WIN' THEN pnl_pct END) as avg_win,
                    AVG(CASE WHEN outcome = 'LOSS' THEN pnl_pct END) as avg_loss,
                    AVG(pnl_pct) as avg_pnl
                FROM performance_outcomes
                WHERE checked_at >= $1
                """,
                cutoff_date.isoformat() + "Z"
            )

            if not result or result["total"] == 0:
                return {
                    "total_signals": 0,
                    "outcomes_checked": 0,
                    "wins": 0,
                    "losses": 0,
                    "neutral": 0,
                    "win_rate": 0.0,
                    "loss_rate": 0.0,
                    "neutral_rate": 0.0,
                    "avg_win_pct": 0.0,
                    "avg_loss_pct": 0.0,
                    "total_pnl_pct": 0.0,
                    "period_days": days
                }

            total = result["total"]
            wins = result["wins"] or 0
            losses = result["losses"] or 0
            neutral = result["neutral"] or 0

            return {
                "total_signals": total,
                "outcomes_checked": total,
                "wins": wins,
                "losses": losses,
                "neutral": neutral,
                "win_rate": round((wins / total * 100) if total > 0 else 0, 2),
                "loss_rate": round((losses / total * 100) if total > 0 else 0, 2),
                "neutral_rate": round((neutral / total * 100) if total > 0 else 0, 2),
                "avg_win_pct": round(result["avg_win"] or 0, 2),
                "avg_loss_pct": round(result["avg_loss"] or 0, 2),
                "total_pnl_pct": round(result["avg_pnl"] or 0, 2),
                "period_days": days
            }

        except Exception as e:
            self.logger.error(f"Error getting overall stats: {e}")
            # Try file fallback
            return await self._get_stats_from_file(days)

    async def get_stats_by_scanner(self, days: int = 30) -> Dict:
        """
        Get performance statistics by scanner type

        Args:
            days: Number of days to analyze

        Returns:
            {
                "smart_money": {...},
                "mss": {...},
                "technical": {...},
                "social": {...}
            }
        """
        try:
            from app.storage.database import db

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            results = await db.fetch_all(
                """
                SELECT
                    scanner_type,
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN outcome = 'NEUTRAL' THEN 1 END) as neutral,
                    AVG(CASE WHEN outcome = 'WIN' THEN pnl_pct END) as avg_win,
                    AVG(CASE WHEN outcome = 'LOSS' THEN pnl_pct END) as avg_loss,
                    AVG(pnl_pct) as avg_pnl
                FROM performance_outcomes
                WHERE checked_at >= $1 AND scanner_type IS NOT NULL
                GROUP BY scanner_type
                """,
                cutoff_date.isoformat() + "Z"
            )

            stats = {}
            for row in results:
                scanner = row["scanner_type"]
                total = row["total"]
                wins = row["wins"] or 0

                stats[scanner] = {
                    "total_signals": total,
                    "wins": wins,
                    "losses": row["losses"] or 0,
                    "neutral": row["neutral"] or 0,
                    "win_rate": round((wins / total * 100) if total > 0 else 0, 2),
                    "avg_win_pct": round(row["avg_win"] or 0, 2),
                    "avg_loss_pct": round(row["avg_loss"] or 0, 2),
                    "avg_pnl_pct": round(row["avg_pnl"] or 0, 2)
                }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting scanner stats: {e}")
            return {}

    async def get_stats_by_tier(self, days: int = 30) -> Dict:
        """
        Get performance statistics by tier classification

        Args:
            days: Number of days to analyze

        Returns:
            {
                "TIER_1_MUST_BUY": {...},
                "TIER_2_STRONG_BUY": {...},
                "TIER_3_WATCHLIST": {...},
                "TIER_4_NEUTRAL": {...}
            }
        """
        try:
            from app.storage.database import db

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            results = await db.fetch_all(
                """
                SELECT
                    tier,
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN outcome = 'NEUTRAL' THEN 1 END) as neutral,
                    AVG(unified_score) as avg_score,
                    AVG(CASE WHEN outcome = 'WIN' THEN pnl_pct END) as avg_win,
                    AVG(CASE WHEN outcome = 'LOSS' THEN pnl_pct END) as avg_loss,
                    AVG(pnl_pct) as avg_pnl
                FROM performance_outcomes
                WHERE checked_at >= $1 AND tier IS NOT NULL
                GROUP BY tier
                ORDER BY avg_score DESC
                """,
                cutoff_date.isoformat() + "Z"
            )

            stats = {}
            for row in results:
                tier = row["tier"]
                total = row["total"]
                wins = row["wins"] or 0

                stats[tier] = {
                    "total_signals": total,
                    "wins": wins,
                    "losses": row["losses"] or 0,
                    "neutral": row["neutral"] or 0,
                    "win_rate": round((wins / total * 100) if total > 0 else 0, 2),
                    "avg_unified_score": round(row["avg_score"] or 0, 2),
                    "avg_win_pct": round(row["avg_win"] or 0, 2),
                    "avg_loss_pct": round(row["avg_loss"] or 0, 2),
                    "avg_pnl_pct": round(row["avg_pnl"] or 0, 2)
                }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting tier stats: {e}")
            return {}

    async def get_stats_by_interval(self, days: int = 30) -> Dict:
        """
        Get performance statistics by time interval

        Args:
            days: Number of days to analyze

        Returns:
            {
                "1h": {...},
                "4h": {...},
                "24h": {...},
                "7d": {...},
                "30d": {...}
            }
        """
        try:
            from app.storage.database import db

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            results = await db.fetch_all(
                """
                SELECT
                    interval,
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN outcome = 'NEUTRAL' THEN 1 END) as neutral,
                    AVG(CASE WHEN outcome = 'WIN' THEN pnl_pct END) as avg_win,
                    AVG(CASE WHEN outcome = 'LOSS' THEN pnl_pct END) as avg_loss,
                    AVG(pnl_pct) as avg_pnl
                FROM performance_outcomes
                WHERE checked_at >= $1
                GROUP BY interval
                ORDER BY
                    CASE interval
                        WHEN '1h' THEN 1
                        WHEN '4h' THEN 2
                        WHEN '24h' THEN 3
                        WHEN '7d' THEN 4
                        WHEN '30d' THEN 5
                    END
                """,
                cutoff_date.isoformat() + "Z"
            )

            stats = {}
            for row in results:
                interval = row["interval"]
                total = row["total"]
                wins = row["wins"] or 0

                stats[interval] = {
                    "total_signals": total,
                    "wins": wins,
                    "losses": row["losses"] or 0,
                    "neutral": row["neutral"] or 0,
                    "win_rate": round((wins / total * 100) if total > 0 else 0, 2),
                    "avg_win_pct": round(row["avg_win"] or 0, 2),
                    "avg_loss_pct": round(row["avg_loss"] or 0, 2),
                    "avg_pnl_pct": round(row["avg_pnl"] or 0, 2)
                }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting interval stats: {e}")
            return {}

    async def get_stats_by_signal_type(self, days: int = 30) -> Dict:
        """
        Get performance statistics by signal type (LONG vs SHORT)

        Args:
            days: Number of days to analyze

        Returns:
            {
                "LONG": {...},
                "SHORT": {...}
            }
        """
        try:
            from app.storage.database import db

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            results = await db.fetch_all(
                """
                SELECT
                    signal_type,
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN outcome = 'NEUTRAL' THEN 1 END) as neutral,
                    AVG(CASE WHEN outcome = 'WIN' THEN pnl_pct END) as avg_win,
                    AVG(CASE WHEN outcome = 'LOSS' THEN pnl_pct END) as avg_loss,
                    AVG(pnl_pct) as avg_pnl
                FROM performance_outcomes
                WHERE checked_at >= $1
                GROUP BY signal_type
                """,
                cutoff_date.isoformat() + "Z"
            )

            stats = {}
            for row in results:
                signal_type = row["signal_type"]
                total = row["total"]
                wins = row["wins"] or 0

                stats[signal_type] = {
                    "total_signals": total,
                    "wins": wins,
                    "losses": row["losses"] or 0,
                    "neutral": row["neutral"] or 0,
                    "win_rate": round((wins / total * 100) if total > 0 else 0, 2),
                    "avg_win_pct": round(row["avg_win"] or 0, 2),
                    "avg_loss_pct": round(row["avg_loss"] or 0, 2),
                    "avg_pnl_pct": round(row["avg_pnl"] or 0, 2)
                }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting signal type stats: {e}")
            return {}

    async def get_top_performers(self, days: int = 30, limit: int = 10) -> Dict:
        """
        Get top performing signals

        Args:
            days: Number of days to analyze
            limit: Max results to return

        Returns:
            {
                "best_signals": [...],
                "worst_signals": [...],
                "best_symbols": [...],
                "worst_symbols": [...]
            }
        """
        try:
            from app.storage.database import db

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Best individual signals
            best_signals = await db.fetch_all(
                """
                SELECT
                    signal_id, symbol, signal_type, interval,
                    entry_price, exit_price, pnl_pct, outcome,
                    tier, unified_score, scanner_type
                FROM performance_outcomes
                WHERE checked_at >= $1 AND outcome = 'WIN'
                ORDER BY pnl_pct DESC
                LIMIT $2
                """,
                cutoff_date.isoformat() + "Z",
                limit
            )

            # Worst individual signals
            worst_signals = await db.fetch_all(
                """
                SELECT
                    signal_id, symbol, signal_type, interval,
                    entry_price, exit_price, pnl_pct, outcome,
                    tier, unified_score, scanner_type
                FROM performance_outcomes
                WHERE checked_at >= $1 AND outcome = 'LOSS'
                ORDER BY pnl_pct ASC
                LIMIT $2
                """,
                cutoff_date.isoformat() + "Z",
                limit
            )

            # Best symbols (by win rate)
            best_symbols = await db.fetch_all(
                """
                SELECT
                    symbol,
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    AVG(pnl_pct) as avg_pnl,
                    AVG(unified_score) as avg_score
                FROM performance_outcomes
                WHERE checked_at >= $1
                GROUP BY symbol
                HAVING COUNT(*) >= 3
                ORDER BY
                    CAST(COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) AS FLOAT) / COUNT(*) DESC,
                    avg_pnl DESC
                LIMIT $2
                """,
                cutoff_date.isoformat() + "Z",
                limit
            )

            # Worst symbols
            worst_symbols = await db.fetch_all(
                """
                SELECT
                    symbol,
                    COUNT(*) as total,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    AVG(pnl_pct) as avg_pnl,
                    AVG(unified_score) as avg_score
                FROM performance_outcomes
                WHERE checked_at >= $1
                GROUP BY symbol
                HAVING COUNT(*) >= 3
                ORDER BY avg_pnl ASC
                LIMIT $2
                """,
                cutoff_date.isoformat() + "Z",
                limit
            )

            return {
                "best_signals": [dict(row) for row in best_signals],
                "worst_signals": [dict(row) for row in worst_signals],
                "best_symbols": [
                    {
                        "symbol": row["symbol"],
                        "total_signals": row["total"],
                        "wins": row["wins"],
                        "win_rate": round((row["wins"] / row["total"] * 100) if row["total"] > 0 else 0, 2),
                        "avg_pnl_pct": round(row["avg_pnl"] or 0, 2),
                        "avg_unified_score": round(row["avg_score"] or 0, 2)
                    }
                    for row in best_symbols
                ],
                "worst_symbols": [
                    {
                        "symbol": row["symbol"],
                        "total_signals": row["total"],
                        "losses": row["losses"],
                        "loss_rate": round((row["losses"] / row["total"] * 100) if row["total"] > 0 else 0, 2),
                        "avg_pnl_pct": round(row["avg_pnl"] or 0, 2),
                        "avg_unified_score": round(row["avg_score"] or 0, 2)
                    }
                    for row in worst_symbols
                ]
            }

        except Exception as e:
            self.logger.error(f"Error getting top performers: {e}")
            return {
                "best_signals": [],
                "worst_signals": [],
                "best_symbols": [],
                "worst_symbols": []
            }

    async def get_comprehensive_report(self, days: int = 30) -> Dict:
        """
        Get comprehensive performance report with all analytics

        Args:
            days: Number of days to analyze

        Returns:
            Complete report with all statistics and recommendations
        """
        self.logger.info(f"Generating comprehensive performance report ({days} days)")

        # Gather all statistics in parallel
        results = await asyncio.gather(
            self.get_overall_stats(days),
            self.get_stats_by_scanner(days),
            self.get_stats_by_tier(days),
            self.get_stats_by_interval(days),
            self.get_stats_by_signal_type(days),
            self.get_top_performers(days),
            return_exceptions=True
        )

        # Unpack results
        overall = results[0] if not isinstance(results[0], Exception) else {}
        by_scanner = results[1] if not isinstance(results[1], Exception) else {}
        by_tier = results[2] if not isinstance(results[2], Exception) else {}
        by_interval = results[3] if not isinstance(results[3], Exception) else {}
        by_signal_type = results[4] if not isinstance(results[4], Exception) else {}
        top_performers = results[5] if not isinstance(results[5], Exception) else {}

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall, by_scanner, by_tier, by_interval
        )

        return {
            "report_generated_at": datetime.utcnow().isoformat() + "Z",
            "period_days": days,
            "overall": overall,
            "by_scanner": by_scanner,
            "by_tier": by_tier,
            "by_interval": by_interval,
            "by_signal_type": by_signal_type,
            "top_performers": top_performers,
            "recommendations": recommendations
        }

    def _generate_recommendations(
        self,
        overall: Dict,
        by_scanner: Dict,
        by_tier: Dict,
        by_interval: Dict
    ) -> List[Dict]:
        """
        Generate actionable recommendations based on performance data

        Returns:
            List of recommendation dicts with priority and action
        """
        recommendations = []

        # Overall performance check
        if overall.get("outcomes_checked", 0) > 0:
            win_rate = overall.get("win_rate", 0)

            if win_rate >= 70:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "overall",
                    "message": f"Excellent performance! Win rate: {win_rate}% - System is performing well",
                    "action": "Continue current strategy"
                })
            elif win_rate >= 55:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "overall",
                    "message": f"Good performance. Win rate: {win_rate}% - Room for improvement",
                    "action": "Consider optimizing underperforming scanners/tiers"
                })
            else:
                recommendations.append({
                    "priority": "URGENT",
                    "category": "overall",
                    "message": f"Low win rate: {win_rate}% - System needs optimization",
                    "action": "Review thresholds and scanner weights immediately"
                })

        # Scanner performance
        if by_scanner:
            best_scanner = max(by_scanner.items(), key=lambda x: x[1].get("win_rate", 0))
            worst_scanner = min(by_scanner.items(), key=lambda x: x[1].get("win_rate", 0))

            recommendations.append({
                "priority": "INFO",
                "category": "scanner",
                "message": f"Best scanner: {best_scanner[0]} ({best_scanner[1].get('win_rate')}% win rate)",
                "action": f"Consider increasing weight for {best_scanner[0]} signals"
            })

            if worst_scanner[1].get("win_rate", 0) < 45:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "scanner",
                    "message": f"Weak scanner: {worst_scanner[0]} ({worst_scanner[1].get('win_rate')}% win rate)",
                    "action": f"Review {worst_scanner[0]} thresholds or decrease weight"
                })

        # Tier performance
        if by_tier:
            tier1 = by_tier.get("TIER_1_MUST_BUY", {})
            tier1_win_rate = tier1.get("win_rate", 0)

            if tier1_win_rate < 60 and tier1.get("total_signals", 0) >= 10:
                recommendations.append({
                    "priority": "URGENT",
                    "category": "tier",
                    "message": f"TIER_1 underperforming: {tier1_win_rate}% win rate",
                    "action": "Increase TIER_1 threshold from 85 to 90 to be more selective"
                })
            elif tier1_win_rate >= 75:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "tier",
                    "message": f"TIER_1 performing well: {tier1_win_rate}% win rate",
                    "action": "Consider lowering TIER_1 threshold to capture more opportunities"
                })

        # Interval performance
        if by_interval:
            for interval, stats in by_interval.items():
                win_rate = stats.get("win_rate", 0)
                if win_rate >= 70 and stats.get("total_signals", 0) >= 20:
                    recommendations.append({
                        "priority": "INFO",
                        "category": "interval",
                        "message": f"{interval} interval performing well: {win_rate}% win rate",
                        "action": f"Focus on {interval} timeframe for best results"
                    })

        return recommendations

    async def _get_stats_from_file(self, days: int = 30) -> Dict:
        """Fallback: Get stats from file storage"""
        try:
            import json
            import os
            from pathlib import Path

            file_path = "performance_data/outcomes.jsonl"

            if not os.path.exists(file_path):
                return {
                    "total_signals": 0,
                    "outcomes_checked": 0,
                    "wins": 0,
                    "losses": 0,
                    "neutral": 0,
                    "win_rate": 0.0,
                    "loss_rate": 0.0,
                    "neutral_rate": 0.0,
                    "avg_win_pct": 0.0,
                    "avg_loss_pct": 0.0,
                    "total_pnl_pct": 0.0,
                    "period_days": days
                }

            cutoff = datetime.utcnow() - timedelta(days=days)

            wins = []
            losses = []
            neutral = 0
            total = 0

            with open(file_path, "r") as f:
                for line in f:
                    outcome = json.loads(line)
                    checked_at = datetime.fromisoformat(outcome["checked_at"].replace("Z", "+00:00"))

                    if checked_at >= cutoff:
                        total += 1
                        if outcome["outcome"] == "WIN":
                            wins.append(outcome["pnl_pct"])
                        elif outcome["outcome"] == "LOSS":
                            losses.append(outcome["pnl_pct"])
                        else:
                            neutral += 1

            win_count = len(wins)
            loss_count = len(losses)

            return {
                "total_signals": total,
                "outcomes_checked": total,
                "wins": win_count,
                "losses": loss_count,
                "neutral": neutral,
                "win_rate": round((win_count / total * 100) if total > 0 else 0, 2),
                "loss_rate": round((loss_count / total * 100) if total > 0 else 0, 2),
                "neutral_rate": round((neutral / total * 100) if total > 0 else 0, 2),
                "avg_win_pct": round(sum(wins) / len(wins) if wins else 0, 2),
                "avg_loss_pct": round(sum(losses) / len(losses) if losses else 0, 2),
                "total_pnl_pct": round((sum(wins) + sum(losses)) / total if total > 0 else 0, 2),
                "period_days": days
            }

        except Exception as e:
            self.logger.error(f"Error reading stats from file: {e}")
            return {}


# Global instance
win_rate_analyzer = WinRateAnalyzer()


# Convenience functions
async def get_performance_report(days: int = 30) -> Dict:
    """Get comprehensive performance report"""
    return await win_rate_analyzer.get_comprehensive_report(days)


async def get_win_rates(days: int = 30) -> Dict:
    """Get overall win rate statistics"""
    return await win_rate_analyzer.get_overall_stats(days)

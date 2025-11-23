"""
Performance Tracker for CryptoSatX

Automatically tracks signal outcomes at multiple intervals to validate
system performance and calculate win rates.

Tracking Intervals:
- 1 hour: Short-term momentum
- 4 hours: Intraday performance
- 24 hours: Daily performance
- 7 days: Weekly trend
- 30 days: Monthly outcome

Win/Loss Criteria:
- LONG signal: WIN if price +5%, LOSS if price -3%
- SHORT signal: WIN if price -5%, LOSS if price +3%
- Otherwise: NEUTRAL
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.utils.logger import get_wib_datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from app.utils.logger import default_logger


class PerformanceTracker:
    """
    Automated signal outcome tracking system

    Tracks every signal at multiple intervals and calculates P&L
    to build performance statistics.
    """

    # Tracking intervals (in seconds)
    INTERVALS = {
        "1h": 3600,
        "4h": 14400,
        "24h": 86400,
        "7d": 604800,
        "30d": 2592000
    }

    # Win/Loss thresholds (percentage)
    WIN_THRESHOLD_LONG = 5.0   # +5% for LONG
    LOSS_THRESHOLD_LONG = -3.0  # -3% for LONG
    WIN_THRESHOLD_SHORT = -5.0  # -5% for SHORT
    LOSS_THRESHOLD_SHORT = 3.0  # +3% for SHORT

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.logger = default_logger

        # Statistics
        self.stats = {
            "total_tracked": 0,
            "outcomes_checked": 0,
            "wins": 0,
            "losses": 0,
            "neutral": 0
        }

        self.logger.info("PerformanceTracker initialized")

    async def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("🎯 Performance Tracker started")

    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self.logger.info("🎯 Performance Tracker stopped")

    async def track_signal(self, signal: Dict):
        """
        Start tracking a signal at all intervals

        Args:
            signal: Signal dict with keys:
                - id: Signal ID
                - symbol: Cryptocurrency symbol
                - signal: LONG or SHORT
                - price: Entry price
                - timestamp: Entry timestamp
                - unified_score: (optional) Unified score
                - tier: (optional) Tier classification
                - scanner_type: (optional) Scanner that generated signal
        """
        try:
            signal_id = signal.get("id")
            symbol = signal.get("symbol")
            signal_type = signal.get("signal", "LONG")
            entry_price = signal.get("price")
            entry_time = signal.get("timestamp")

            if not all([signal_id, symbol, entry_price]):
                self.logger.warning(
                    f"Incomplete signal data for tracking: {signal_id}"
                )
                return

            # Parse entry time
            if isinstance(entry_time, str):
                entry_time = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
            elif entry_time is None:
                entry_time = get_wib_datetime()

            self.logger.info(
                f"📊 Tracking signal {signal_id} ({symbol} {signal_type} @ ${entry_price})"
            )

            # Schedule outcome checks at each interval
            await self._schedule_checks(signal, entry_time)

            # Update stats
            self.stats["total_tracked"] += 1

        except Exception as e:
            self.logger.error(f"Error tracking signal: {e}")

    async def _schedule_checks(self, signal: Dict, entry_time: datetime):
        """Schedule outcome checks at all intervals"""
        signal_id = signal.get("id")

        for interval_name, seconds in self.INTERVALS.items():
            run_time = entry_time + timedelta(seconds=seconds)

            # Only schedule if in the future
            if run_time > get_wib_datetime():
                self.scheduler.add_job(
                    self._check_outcome,
                    trigger=DateTrigger(run_date=run_time),
                    args=[signal, interval_name],
                    id=f"check_{signal_id}_{interval_name}",
                    replace_existing=True
                )

                self.logger.debug(
                    f"Scheduled {interval_name} check for signal {signal_id} at {run_time}"
                )

    async def _check_outcome(self, signal: Dict, interval: str):
        """
        Check signal outcome at a specific interval

        Args:
            signal: Original signal dict
            interval: Interval name (1h, 4h, 24h, etc.)
        """
        try:
            signal_id = signal.get("id")
            symbol = signal.get("symbol")
            signal_type = signal.get("signal", "LONG")
            entry_price = float(signal.get("price"))

            self.logger.info(
                f"🔍 Checking {interval} outcome for signal {signal_id} ({symbol})"
            )

            # Get current price
            current_price = await self._get_current_price(symbol)

            if current_price is None:
                self.logger.warning(
                    f"Could not get current price for {symbol}, skipping outcome check"
                )
                return

            # Calculate P&L
            pnl_pct = ((current_price - entry_price) / entry_price) * 100

            # Determine outcome
            outcome = self._determine_outcome(signal_type, pnl_pct)

            # Save outcome
            await self._save_outcome({
                "signal_id": signal_id,
                "symbol": symbol,
                "signal_type": signal_type,
                "interval": interval,
                "entry_price": entry_price,
                "exit_price": current_price,
                "pnl_pct": round(pnl_pct, 2),
                "outcome": outcome,
                "unified_score": signal.get("unified_score"),
                "tier": signal.get("tier"),
                "scanner_type": signal.get("scanner_type"),
                "checked_at": get_wib_datetime().isoformat()
            })

            # Update stats
            self.stats["outcomes_checked"] += 1
            if outcome == "WIN":
                self.stats["wins"] += 1
            elif outcome == "LOSS":
                self.stats["losses"] += 1
            else:
                self.stats["neutral"] += 1

            self.logger.info(
                f"✅ {interval} outcome for {symbol}: {outcome} "
                f"(P&L: {pnl_pct:+.2f}%, price: ${entry_price} → ${current_price})"
            )

        except Exception as e:
            self.logger.error(f"Error checking outcome: {e}")

    def _determine_outcome(self, signal_type: str, pnl_pct: float) -> str:
        """
        Determine if signal was WIN, LOSS, or NEUTRAL

        Args:
            signal_type: LONG or SHORT
            pnl_pct: Price change percentage

        Returns:
            "WIN", "LOSS", or "NEUTRAL"
        """
        if signal_type.upper() == "LONG":
            if pnl_pct >= self.WIN_THRESHOLD_LONG:
                return "WIN"
            elif pnl_pct <= self.LOSS_THRESHOLD_LONG:
                return "LOSS"
            else:
                return "NEUTRAL"

        elif signal_type.upper() == "SHORT":
            if pnl_pct <= self.WIN_THRESHOLD_SHORT:
                return "WIN"
            elif pnl_pct >= self.LOSS_THRESHOLD_SHORT:
                return "LOSS"
            else:
                return "NEUTRAL"

        else:
            return "NEUTRAL"

    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for symbol

        Uses CoinAPI or fallback to other price sources
        """
        try:
            from app.services.coinapi_service import CoinapiService

            service = CoinapiService()
            price_data = await service.get_current_price(symbol)

            if price_data.get("success"):
                return float(price_data.get("price", 0))

            return None

        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None

    async def _save_outcome(self, outcome: Dict):
        """
        Save outcome to database

        Stores outcome in signal_outcomes table for later analysis
        """
        try:
            from app.storage.database import db

            # Save to database
            await db.execute(
                """
                INSERT INTO performance_outcomes
                (signal_id, symbol, signal_type, interval, entry_price, exit_price,
                 pnl_pct, outcome, unified_score, tier, scanner_type, checked_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (signal_id, interval) DO UPDATE SET
                    exit_price = EXCLUDED.exit_price,
                    pnl_pct = EXCLUDED.pnl_pct,
                    outcome = EXCLUDED.outcome,
                    checked_at = EXCLUDED.checked_at
                """,
                outcome["signal_id"],
                outcome["symbol"],
                outcome["signal_type"],
                outcome["interval"],
                outcome["entry_price"],
                outcome["exit_price"],
                outcome["pnl_pct"],
                outcome["outcome"],
                outcome.get("unified_score"),
                outcome.get("tier"),
                outcome.get("scanner_type"),
                outcome["checked_at"]
            )

            self.logger.debug(f"Saved outcome for signal {outcome['signal_id']}")

        except Exception as e:
            self.logger.error(f"Error saving outcome: {e}")
            # Fallback to file storage if database fails
            await self._save_outcome_to_file(outcome)

    async def _save_outcome_to_file(self, outcome: Dict):
        """Fallback: Save outcome to JSON file"""
        try:
            import json
            import os

            # Ensure directory exists
            os.makedirs("performance_data", exist_ok=True)

            # Append to outcomes file
            file_path = "performance_data/outcomes.jsonl"

            with open(file_path, "a") as f:
                f.write(json.dumps(outcome) + "\n")

            self.logger.debug(f"Saved outcome to file: {file_path}")

        except Exception as e:
            self.logger.error(f"Error saving outcome to file: {e}")

    def get_stats(self) -> Dict:
        """Get tracker statistics"""
        win_rate = (
            (self.stats["wins"] / self.stats["outcomes_checked"] * 100)
            if self.stats["outcomes_checked"] > 0
            else 0
        )

        return {
            **self.stats,
            "win_rate": round(win_rate, 1),
            "scheduled_jobs": len(self.scheduler.get_jobs()) if self.scheduler.running else 0
        }


# Global instance
performance_tracker = PerformanceTracker()


# Convenience function
async def track_signal(signal: Dict):
    """Track a signal's performance"""
    await performance_tracker.track_signal(signal)

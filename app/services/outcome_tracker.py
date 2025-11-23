"""
Signal Outcome Tracker Service
Monitors price movements after signals and calculates accuracy metrics
Phase 2: AI Verdict Validation System
"""

import asyncio
from datetime import datetime, timedelta
from app.utils.logger import get_wib_datetime
from typing import Optional, Dict, Any
import httpx
from app.storage.database import db
from app.utils.logger import logger


class OutcomeTracker:
    """
    Tracks signal outcomes by monitoring price movements
    Validates AI verdict accuracy over time
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Outcome classification thresholds (percentage)
        self.win_threshold = 1.0  # 1% profit = WIN
        self.loss_threshold = -1.0  # -1% loss = LOSS
        # Between these = NEUTRAL
        
        # Prevent race conditions in concurrent updates
        self._update_locks = {}  # outcome_id -> asyncio.Lock
        self._locks_lock = asyncio.Lock()  # Protect _update_locks dict itself

    async def _get_outcome_lock(self, outcome_id: int) -> asyncio.Lock:
        """Get or create a lock for a specific outcome_id (thread-safe)"""
        async with self._locks_lock:
            if outcome_id not in self._update_locks:
                self._update_locks[outcome_id] = asyncio.Lock()
            return self._update_locks[outcome_id]

    async def record_signal_entry(
        self,
        signal_id: int,
        symbol: str,
        signal_type: str,
        verdict: str,
        risk_mode: str,
        entry_price: float,
        entry_timestamp: datetime
    ) -> Optional[int]:
        """
        Record a new signal entry for outcome tracking
        Returns outcome_id if successful
        """
        try:
            if db.use_postgres:
                async with db.pool.acquire() as conn:
                    outcome_id = await conn.fetchval(
                        """
                        INSERT INTO signal_outcomes (
                            signal_id, symbol, signal_type, verdict, risk_mode,
                            entry_price, entry_timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id
                        """,
                        signal_id, symbol, signal_type, verdict, risk_mode,
                        entry_price, entry_timestamp
                    )
                    return outcome_id
            else:
                async with db.sqlite_conn.execute(
                    """
                    INSERT INTO signal_outcomes (
                        signal_id, symbol, signal_type, verdict, risk_mode,
                        entry_price, entry_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (signal_id, symbol, signal_type, verdict, risk_mode,
                     entry_price, entry_timestamp.isoformat())
                ) as cursor:
                    outcome_id = cursor.lastrowid
                    await db.sqlite_conn.commit()
                    return outcome_id
        except Exception as e:
            logger.error(f"Failed to record signal entry: {e}")
            return None

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch current price from Binance Futures
        Fallback to multiple sources if needed
        """
        try:
            # Try Binance Futures first (most reliable for crypto futures)
            url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}USDT"
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return float(data["price"])
            
            # Fallback: Try spot price
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return float(data["price"])

            return None
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            return None

    def calculate_pnl(
        self,
        entry_price: float,
        current_price: float,
        signal_type: str
    ) -> float:
        """
        Calculate P&L percentage based on signal type
        LONG: (current - entry) / entry * 100
        SHORT: (entry - current) / entry * 100
        """
        # Safety guard: prevent division by zero
        if entry_price <= 0 or current_price <= 0:
            logger.error(f"Invalid price for P&L calculation: entry={entry_price}, current={current_price}")
            return 0.0
        
        if signal_type == "LONG":
            return ((current_price - entry_price) / entry_price) * 100
        elif signal_type == "SHORT":
            return ((entry_price - current_price) / entry_price) * 100
        else:
            return 0.0

    def classify_outcome(self, pnl: float) -> str:
        """
        Classify outcome based on P&L percentage
        WIN: pnl >= win_threshold
        LOSS: pnl <= loss_threshold
        NEUTRAL: in between
        """
        if pnl >= self.win_threshold:
            return "WIN"
        elif pnl <= self.loss_threshold:
            return "LOSS"
        else:
            return "NEUTRAL"

    async def update_outcome(
        self,
        outcome_id: int,
        interval: str  # "1h", "4h", "24h"
    ) -> bool:
        """
        Update outcome for a specific time interval
        Fetches current price, calculates P&L, classifies outcome
        
        Uses per-outcome locking to prevent race conditions
        """
        # Acquire lock for this outcome_id to serialize updates
        lock = await self._get_outcome_lock(outcome_id)
        async with lock:
            return await self._update_outcome_locked(outcome_id, interval)
    
    async def _update_outcome_locked(
        self,
        outcome_id: int,
        interval: str
    ) -> bool:
        """
        Internal method: Update outcome (called under lock)
        """
        try:
            # Fetch outcome record
            if db.use_postgres:
                async with db.pool.acquire() as conn:
                    record = await conn.fetchrow(
                        """
                        SELECT symbol, signal_type, entry_price
                        FROM signal_outcomes
                        WHERE id = $1
                        """,
                        outcome_id
                    )
            else:
                async with db.sqlite_conn.execute(
                    """
                    SELECT symbol, signal_type, entry_price
                    FROM signal_outcomes
                    WHERE id = ?
                    """,
                    (outcome_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        record = {
                            "symbol": row[0],
                            "signal_type": row[1],
                            "entry_price": row[2]
                        }
                    else:
                        record = None

            if not record:
                logger.error(f"Outcome record {outcome_id} not found")
                return False

            # Get current price
            current_price = await self.get_current_price(record["symbol"])
            if not current_price:
                logger.error(f"Could not fetch price for {record['symbol']}")
                return False

            # Calculate metrics
            pnl = self.calculate_pnl(
                float(record["entry_price"]),
                current_price,
                record["signal_type"]
            )
            outcome = self.classify_outcome(pnl)
            now = get_wib_datetime()

            # Update database
            if db.use_postgres:
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        UPDATE signal_outcomes
                        SET price_{interval} = $1,
                            outcome_{interval} = $2,
                            pnl_{interval} = $3,
                            tracked_at_{interval} = $4
                        WHERE id = $5
                        """,
                        current_price, outcome, pnl, now, outcome_id
                    )
            else:
                await db.sqlite_conn.execute(
                    f"""
                    UPDATE signal_outcomes
                    SET price_{interval} = ?,
                        outcome_{interval} = ?,
                        pnl_{interval} = ?,
                        tracked_at_{interval} = ?
                    WHERE id = ?
                    """,
                    (current_price, outcome, pnl, now.isoformat(), outcome_id)
                )
                await db.sqlite_conn.commit()

            logger.info(f"Updated outcome {outcome_id} at {interval}: {outcome} ({pnl:+.2f}%)")
            return True

        except Exception as e:
            logger.error(f"Failed to update outcome: {e}")
            return False

    async def schedule_outcome_tracking(
        self,
        outcome_id: int,
        intervals: list = None
    ):
        """
        Schedule outcome tracking at specified intervals
        Default: 1h, 4h, 24h
        """
        if intervals is None:
            intervals = [
                ("1h", 3600),    # 1 hour = 3600 seconds
                ("4h", 14400),   # 4 hours = 14400 seconds
                ("24h", 86400)   # 24 hours = 86400 seconds
            ]

        async def track_at_interval(interval_name: str, delay_seconds: int):
            """Background task to track outcome at specified delay"""
            await asyncio.sleep(delay_seconds)
            await self.update_outcome(outcome_id, interval_name)

        # Schedule background tasks
        for interval_name, delay in intervals:
            asyncio.create_task(
                track_at_interval(interval_name, delay)
            )

    async def get_pending_outcomes(self, interval: str) -> list:
        """
        Get outcomes that need tracking at specified interval
        Returns outcomes where tracked_at_{interval} is NULL
        and entry_timestamp is >= interval ago
        """
        try:
            # Calculate time threshold
            now = get_wib_datetime()
            if interval == "1h":
                threshold = now - timedelta(hours=1)
            elif interval == "4h":
                threshold = now - timedelta(hours=4)
            elif interval == "24h":
                threshold = now - timedelta(hours=24)
            else:
                return []

            if db.use_postgres:
                async with db.pool.acquire() as conn:
                    # Convert to naive datetime for PostgreSQL comparison
                    # (column is timestamp without time zone)
                    threshold_naive = threshold.replace(tzinfo=None)
                    records = await conn.fetch(
                        f"""
                        SELECT id
                        FROM signal_outcomes
                        WHERE tracked_at_{interval} IS NULL
                        AND entry_timestamp <= $1
                        ORDER BY entry_timestamp ASC
                        LIMIT 100
                        """,
                        threshold_naive
                    )
                    return [r["id"] for r in records]
            else:
                async with db.sqlite_conn.execute(
                    f"""
                    SELECT id
                    FROM signal_outcomes
                    WHERE tracked_at_{interval} IS NULL
                    AND entry_timestamp <= ?
                    ORDER BY entry_timestamp ASC
                    LIMIT 100
                    """,
                    (threshold.isoformat(),)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Failed to get pending outcomes: {e}")
            return []

    async def process_pending_outcomes(self):
        """
        Process all pending outcomes across all intervals
        Called periodically by background job or on-demand
        """
        logger.info("Processing pending outcome tracking...")

        for interval in ["1h", "4h", "24h"]:
            pending = await self.get_pending_outcomes(interval)

            if pending:
                logger.info(f"Found {len(pending)} pending outcomes for {interval}")

                for outcome_id in pending:
                    await self.update_outcome(outcome_id, interval)
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
            else:
                logger.info(f"No pending outcomes for {interval}")

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Global instance
outcome_tracker = OutcomeTracker()

"""
Liquidation Spike Detector
Monitors liquidation data and alerts on large liquidation events
Uses both REST API polling and WebSocket streaming for real-time detection
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService
from app.services.telegram_notifier import TelegramNotifier
from app.utils.logger import default_logger as logger


class LiquidationSpikeDetector:
    """
    Real-time liquidation spike detection

    Features:
    - Monitors liquidations via REST API every 60 seconds
    - Detects large liquidation events (>$50M in 5min, >$20M in 1min)
    - Tracks long/short liquidation imbalance
    - Instant Telegram alerts for major liquidation spikes
    - Separate tracking for individual coins and market-wide events
    """

    def __init__(
        self,
        check_interval: int = 60,  # Check every 60 seconds
        extreme_threshold: float = 50_000_000,  # $50M in 5min = EXTREME
        high_threshold: float = 20_000_000,  # $20M in 1min = HIGH
        time_window_minutes: int = 5  # Track 5-minute windows
    ):
        self.check_interval = check_interval
        self.extreme_threshold = extreme_threshold
        self.high_threshold = high_threshold
        self.time_window_minutes = time_window_minutes

        self.coinglass = CoinglassComprehensiveService()
        self.telegram = TelegramNotifier()

        self.is_running = False
        self.last_check_time = None

        # Liquidation history: {symbol: deque[(timestamp, long_liq_usd, short_liq_usd)]}
        self.liquidation_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))

        # Track total market liquidations
        self.market_liquidation_history: deque = deque(maxlen=10)

        # Track alert timestamps
        self.last_alert_times: Dict[str, datetime] = {}

        logger.info(
            f"Liquidation Spike Detector initialized: "
            f"extreme_threshold=${extreme_threshold:,.0f}, "
            f"high_threshold=${high_threshold:,.0f}, "
            f"check_interval={check_interval}s"
        )

    async def start(self):
        """Start liquidation monitoring loop"""
        if self.is_running:
            logger.warning("Liquidation spike detector already running")
            return

        self.is_running = True
        logger.info("🚀 Liquidation Spike Detector STARTED - monitoring for large liquidation events")

        try:
            while self.is_running:
                await self._check_liquidation_spikes()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Liquidation spike detector crashed: {e}")
            self.is_running = False

    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        logger.info("Liquidation Spike Detector STOPPED")

    async def _check_liquidation_spikes(self):
        """Check for liquidation spikes across the market"""
        try:
            current_time = datetime.utcnow()
            self.last_check_time = current_time

            logger.debug("🔍 Checking liquidation data...")

            # Get recent liquidation data (24h aggregated by coin)
            # FIXED: get_liquidation_coin_list doesn't accept time_type parameter
            liq_data = await self.coinglass.get_liquidation_coin_list()

            if not liq_data.get("success") or not liq_data.get("data"):
                logger.warning("No liquidation data available")
                return

            liquidations = liq_data["data"]

            # Calculate total market liquidations in last hour
            total_long_liq = 0
            total_short_liq = 0

            # Track per-coin liquidations
            for coin_data in liquidations[:50]:  # Check top 50 by liquidation volume
                symbol = coin_data.get("symbol", "").replace("USDT", "")

                if not symbol:
                    continue

                # Get 1h liquidation amounts
                long_liq_1h = float(coin_data.get("longLiquidationUsd1h", 0))
                short_liq_1h = float(coin_data.get("shortLiquidationUsd1h", 0))

                total_long_liq += long_liq_1h
                total_short_liq += short_liq_1h

                # Add to history
                self.liquidation_history[symbol].append((current_time, long_liq_1h, short_liq_1h))

                # Check for individual coin spikes
                await self._check_coin_liquidation_spike(symbol, long_liq_1h, short_liq_1h, current_time)

            # Add to market history
            self.market_liquidation_history.append((current_time, total_long_liq, total_short_liq))

            # Check for market-wide liquidation spike
            await self._check_market_liquidation_spike(total_long_liq, total_short_liq, current_time)

            logger.debug(
                f"✅ Liquidation check complete: "
                f"${total_long_liq:,.0f} longs, ${total_short_liq:,.0f} shorts liquidated in last hour"
            )

        except Exception as e:
            logger.error(f"Error in liquidation check cycle: {e}")

    async def _check_coin_liquidation_spike(
        self,
        symbol: str,
        long_liq: float,
        short_liq: float,
        current_time: datetime
    ):
        """Check if a specific coin has large liquidations"""
        try:
            total_liq = long_liq + short_liq

            # Check for extreme liquidations (>$20M in 1 hour for single coin)
            if total_liq > self.high_threshold:
                # Calculate imbalance
                if total_liq > 0:
                    long_ratio = long_liq / total_liq * 100
                    short_ratio = short_liq / total_liq * 100
                else:
                    long_ratio = short_ratio = 0

                # Determine dominant side
                if long_ratio > 70:
                    dominant_side = "LONG"
                    imbalance_emoji = "🔴"
                elif short_ratio > 70:
                    dominant_side = "SHORT"
                    imbalance_emoji = "🟢"
                else:
                    dominant_side = "MIXED"
                    imbalance_emoji = "🟡"

                logger.info(
                    f"🔥 LIQUIDATION SPIKE: {symbol} - "
                    f"${total_liq:,.0f} total ({long_ratio:.0f}% long, {short_ratio:.0f}% short)"
                )

                # Send alert
                await self._send_liquidation_alert(
                    symbol=symbol,
                    total_liq=total_liq,
                    long_liq=long_liq,
                    short_liq=short_liq,
                    long_ratio=long_ratio,
                    short_ratio=short_ratio,
                    dominant_side=dominant_side,
                    imbalance_emoji=imbalance_emoji,
                    is_market_wide=False
                )

                self.last_alert_times[f"coin_{symbol}"] = current_time

        except Exception as e:
            logger.error(f"Error checking coin liquidation spike for {symbol}: {e}")

    async def _check_market_liquidation_spike(
        self,
        total_long_liq: float,
        total_short_liq: float,
        current_time: datetime
    ):
        """Check for market-wide liquidation spike"""
        try:
            total_liq = total_long_liq + total_short_liq

            # Check for extreme market-wide liquidations (>$50M in 1 hour)
            if total_liq > self.extreme_threshold:
                # Calculate imbalance
                if total_liq > 0:
                    long_ratio = total_long_liq / total_liq * 100
                    short_ratio = total_short_liq / total_liq * 100
                else:
                    long_ratio = short_ratio = 0

                # Determine dominant side
                if long_ratio > 70:
                    dominant_side = "LONG"
                    imbalance_emoji = "🔴"
                elif short_ratio > 70:
                    dominant_side = "SHORT"
                    imbalance_emoji = "🟢"
                else:
                    dominant_side = "MIXED"
                    imbalance_emoji = "🟡"

                logger.info(
                    f"🔥🔥🔥 MARKET-WIDE LIQUIDATION SPIKE: "
                    f"${total_liq:,.0f} total ({long_ratio:.0f}% long, {short_ratio:.0f}% short)"
                )

                # Send alert
                await self._send_liquidation_alert(
                    symbol="MARKET",
                    total_liq=total_liq,
                    long_liq=total_long_liq,
                    short_liq=total_short_liq,
                    long_ratio=long_ratio,
                    short_ratio=short_ratio,
                    dominant_side=dominant_side,
                    imbalance_emoji=imbalance_emoji,
                    is_market_wide=True
                )

                self.last_alert_times["market_wide"] = current_time

        except Exception as e:
            logger.error(f"Error checking market liquidation spike: {e}")

    async def _send_liquidation_alert(
        self,
        symbol: str,
        total_liq: float,
        long_liq: float,
        short_liq: float,
        long_ratio: float,
        short_ratio: float,
        dominant_side: str,
        imbalance_emoji: str,
        is_market_wide: bool
    ):
        """Send Telegram alert for liquidation spike"""
        try:
            message = self._format_liquidation_alert(
                symbol=symbol,
                total_liq=total_liq,
                long_liq=long_liq,
                short_liq=short_liq,
                long_ratio=long_ratio,
                short_ratio=short_ratio,
                dominant_side=dominant_side,
                imbalance_emoji=imbalance_emoji,
                is_market_wide=is_market_wide
            )

            if self.telegram.enabled:
                await self.telegram._send_telegram_message(message)
                logger.info(f"✅ Liquidation alert sent for {symbol}")
            else:
                logger.warning(f"Telegram disabled - liquidation alert not sent for {symbol}")

        except Exception as e:
            logger.error(f"Error sending liquidation alert: {e}")

    def _format_liquidation_alert(
        self,
        symbol: str,
        total_liq: float,
        long_liq: float,
        short_liq: float,
        long_ratio: float,
        short_ratio: float,
        dominant_side: str,
        imbalance_emoji: str,
        is_market_wide: bool
    ) -> str:
        """Format liquidation alert message"""

        if is_market_wide:
            title = "🌊🌊🌊 MARKET-WIDE LIQUIDATION CASCADE 🌊🌊🌊"
            scope = "Entire Crypto Market"
        else:
            title = f"💥💥 MASSIVE LIQUIDATION EVENT 💥💥"
            scope = f"${symbol}"

        # Severity
        if total_liq > 100_000_000:
            severity = "CATASTROPHIC"
            severity_emoji = "🔴🔴🔴"
        elif total_liq > 50_000_000:
            severity = "EXTREME"
            severity_emoji = "🔴🔴"
        else:
            severity = "HIGH"
            severity_emoji = "🔴"

        msg = f"""
{title}

🎯 Scope: {scope}
💰 Total Liquidations: ${total_liq:,.0f}

📊 LIQUIDATION BREAKDOWN:
━━━━━━━━━━━━━━━━━━━━━━━
🔴 Long Liquidations: ${long_liq:,.0f} ({long_ratio:.1f}%)
🟢 Short Liquidations: ${short_liq:,.0f} ({short_ratio:.1f}%)

{imbalance_emoji} Dominant Side: {dominant_side}
{severity_emoji} Severity: {severity}

⚡ MARKET IMPLICATIONS:
{self._get_liquidation_implications(dominant_side, long_ratio, short_ratio)}

🎯 TRADING STRATEGY:
{self._get_liquidation_strategy(dominant_side, long_ratio, short_ratio)}

━━━━━━━━━━━━━━━━━━━━━━━
🕐 Detected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
⚙️ Source: Liquidation Monitor (60s interval)
📊 Data: Last 1 hour aggregated

#Liquidation #{symbol} #CryptoSatX #LiquidationSpike
"""
        return msg

    def _get_liquidation_implications(self, dominant_side: str, long_ratio: float, short_ratio: float) -> str:
        """Get market implications of liquidation spike"""
        if dominant_side == "LONG":
            return (
                "⚠️ LONG SQUEEZE in progress! "
                "Massive long position liquidations indicate:\n"
                "• Strong downward price pressure\n"
                "• Overleveraged longs getting rekt\n"
                "• Possible capitulation or bottom formation\n"
                "• Potential for sharp reversal if selling exhausts"
            )
        elif dominant_side == "SHORT":
            return (
                "⚠️ SHORT SQUEEZE in progress! "
                "Massive short position liquidations indicate:\n"
                "• Strong upward price pressure\n"
                "• Overleveraged shorts getting rekt\n"
                "• Parabolic move likely continuing\n"
                "• Forced buying accelerating rally"
            )
        else:
            return (
                "⚠️ MIXED LIQUIDATIONS detected! "
                "Both sides getting liquidated indicates:\n"
                "• Extreme volatility and whipsaw action\n"
                "• Uncertain market direction\n"
                "• High risk environment\n"
                "• Wait for clear direction before entry"
            )

    def _get_liquidation_strategy(self, dominant_side: str, long_ratio: float, short_ratio: float) -> str:
        """Get trading strategy based on liquidations"""
        if dominant_side == "LONG":
            return (
                "🎯 LONG LIQUIDATION CASCADE:\n"
                "1. WAIT for liquidation cascade to complete\n"
                "2. Look for reversal signals (volume spike, wick rejection)\n"
                "3. Can consider LONG at strong support with tight stop\n"
                "4. Target: 5-10% bounce from liquidation low\n"
                "5. ⚠️ HIGH RISK - use small position size"
            )
        elif dominant_side == "SHORT":
            return (
                "🎯 SHORT LIQUIDATION CASCADE:\n"
                "1. DO NOT SHORT into squeeze (likely to get rekt)\n"
                "2. WAIT for parabolic exhaustion signals\n"
                "3. Can ride momentum with trailing stop if already long\n"
                "4. Target: Take profits at psychological resistance\n"
                "5. ⚠️ HIGH RISK - squeeze can continue longer than expected"
            )
        else:
            return (
                "🎯 MIXED LIQUIDATIONS:\n"
                "1. AVOID TRADING - too much volatility\n"
                "2. WAIT for clear directional move\n"
                "3. Set alerts for price stabilization\n"
                "4. Only scalp if very experienced\n"
                "5. ⚠️ EXTREME RISK - both sides getting liquidated"
            )

    async def get_status(self) -> Dict:
        """Get detector status"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "extreme_threshold": self.extreme_threshold,
            "high_threshold": self.high_threshold,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "coins_tracked": len(self.liquidation_history),
            "total_alerts_sent": len(self.last_alert_times)
        }


# Global instance
liquidation_spike_detector = LiquidationSpikeDetector(
    check_interval=60,  # Check every 60 seconds
    extreme_threshold=50_000_000,  # $50M threshold for market-wide
    high_threshold=20_000_000,  # $20M threshold for individual coins
    time_window_minutes=5
)

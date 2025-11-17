"""
Real-Time Price Spike Detector
Monitors top 100 coins for sudden price movements >8% in 5 minutes
Sends instant Telegram alerts for early entry opportunities
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService
from app.services.telegram_notifier import TelegramNotifier
from app.utils.logger import default_logger as logger


class RealtimeSpikeDetector:
    """
    Real-time price spike detection for top 100 coins

    Features:
    - Monitors price changes every 30 seconds
    - Detects >8% moves in 5-minute windows
    - Instant Telegram alerts (no cooldown)
    - Tracks both pumps and dumps
    - Maintains price history for accurate spike detection
    """

    def __init__(
        self,
        check_interval: int = 30,  # Check every 30 seconds
        spike_threshold: float = 8.0,  # 8% threshold
        time_window_minutes: int = 5,  # 5-minute window
        top_coins_count: int = 100  # Monitor top 100 coins
    ):
        self.check_interval = check_interval
        self.spike_threshold = spike_threshold
        self.time_window_minutes = time_window_minutes
        self.top_coins_count = top_coins_count

        self.coinapi = CoinAPIComprehensiveService()
        self.telegram = TelegramNotifier()

        self.is_running = False
        self.last_check_time = None

        # Price history: {symbol: deque[(timestamp, price)]}
        # Keep last 5 minutes of data (10 data points at 30s intervals)
        self.price_history: Dict[str, deque] = {}
        self.max_history_length = 10

        # Track alert timestamps to avoid spam (but still allow per-spike alerts)
        self.last_alert_times: Dict[str, datetime] = {}

        logger.info(
            f"Real-Time Spike Detector initialized: "
            f"threshold={spike_threshold}%, window={time_window_minutes}min, "
            f"check_interval={check_interval}s, monitoring {top_coins_count} coins"
        )

    async def start(self):
        """Start real-time monitoring loop"""
        if self.is_running:
            logger.warning("Real-time spike detector already running")
            return

        self.is_running = True
        logger.info("🚀 Real-Time Spike Detector STARTED - monitoring for >8% moves in 5min")

        try:
            while self.is_running:
                await self._check_price_spikes()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Real-time spike detector crashed: {e}")
            self.is_running = False

    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        logger.info("Real-Time Spike Detector STOPPED")

    async def _check_price_spikes(self):
        """Check all monitored coins for price spikes"""
        try:
            current_time = datetime.utcnow()
            self.last_check_time = current_time

            # Get top coins to monitor
            coins_to_monitor = await self._get_top_coins()

            if not coins_to_monitor:
                logger.warning("No coins to monitor")
                return

            logger.debug(f"🔍 Checking {len(coins_to_monitor)} coins for price spikes")

            # Check each coin for spikes (parallel processing)
            tasks = [
                self._check_coin_price_spike(symbol, current_time)
                for symbol in coins_to_monitor
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count detected spikes
            spikes_detected = sum(1 for r in results if r and not isinstance(r, Exception))

            if spikes_detected > 0:
                logger.info(f"🔥 Detected {spikes_detected} price spikes!")

        except Exception as e:
            logger.error(f"Error in spike check cycle: {e}")

    async def _get_top_coins(self) -> List[str]:
        """
        Get list of top 100 coins to monitor
        Uses CoinAPI market cap data
        """
        try:
            # Hardcoded top 100 coins by market cap (update periodically)
            # This is more reliable than API calls and faster
            top_100_coins = [
                "BTC", "ETH", "USDT", "BNB", "SOL", "USDC", "XRP", "DOGE", "ADA", "TRX",
                "AVAX", "SHIB", "TON", "DOT", "LINK", "MATIC", "BCH", "ICP", "UNI", "LTC",
                "DAI", "ATOM", "ETC", "FIL", "ARB", "OKB", "APT", "LDO", "OP", "INJ",
                "MKR", "HBAR", "VET", "QNT", "NEAR", "GRT", "AAVE", "STX", "RUNE", "ALGO",
                "FTM", "SAND", "MANA", "XTZ", "EGLD", "THETA", "AXS", "SNX", "EOS", "FLOW",
                "XLM", "APE", "CHZ", "KLAY", "MINA", "CRV", "ZEC", "CFX", "FXS", "CAKE",
                "NEO", "BSV", "ZIL", "DASH", "ENJ", "BAT", "LRC", "GMX", "DYDX", "COMP",
                "GALA", "XMR", "1INCH", "KCS", "WAVES", "HNT", "IOTA", "YFI", "CELO", "NEXO",
                "AR", "FET", "KAVA", "BTT", "ROSE", "IMX", "BLUR", "AUDIO", "ONT", "JST",
                "WOO", "SXP", "ANKR", "RVN", "MASK", "OMG", "ZRX", "BAL", "SKL", "PEOPLE"
            ]

            return top_100_coins

        except Exception as e:
            logger.error(f"Error getting top coins: {e}")
            # Return major coins as fallback
            return ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC"]

    async def _check_coin_price_spike(self, symbol: str, current_time: datetime) -> Optional[Dict]:
        """
        Check a single coin for price spike
        Returns spike data if detected, None otherwise
        """
        try:
            # Get current price
            current_price = await self._get_current_price(symbol)

            if not current_price or current_price <= 0:
                return None

            # Initialize price history for this symbol if needed
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=self.max_history_length)

            # Add current price to history
            self.price_history[symbol].append((current_time, current_price))

            # Need at least 2 data points to calculate change
            if len(self.price_history[symbol]) < 2:
                return None

            # Get oldest price within time window (5 minutes ago)
            time_threshold = current_time - timedelta(minutes=self.time_window_minutes)

            # Find oldest price within window
            oldest_price = None
            for timestamp, price in self.price_history[symbol]:
                if timestamp >= time_threshold:
                    oldest_price = price
                    break

            if not oldest_price:
                # Use oldest available price
                oldest_price = self.price_history[symbol][0][1]

            # Calculate percentage change
            price_change_pct = ((current_price - oldest_price) / oldest_price) * 100

            # Check if spike exceeds threshold (both up and down)
            if abs(price_change_pct) >= self.spike_threshold:
                spike_direction = "PUMP" if price_change_pct > 0 else "DUMP"

                logger.info(
                    f"🔥 PRICE SPIKE DETECTED: {symbol} - "
                    f"{price_change_pct:+.2f}% in {self.time_window_minutes}min ({spike_direction})"
                )

                # Send Telegram alert (INSTANT - no cooldown)
                await self._send_spike_alert(symbol, current_price, oldest_price, price_change_pct, spike_direction)

                # Update last alert time (for logging purposes)
                self.last_alert_times[symbol] = current_time

                return {
                    "symbol": symbol,
                    "current_price": current_price,
                    "old_price": oldest_price,
                    "price_change_pct": price_change_pct,
                    "direction": spike_direction,
                    "timestamp": current_time.isoformat()
                }

        except Exception as e:
            logger.error(f"Error checking price spike for {symbol}: {e}")
            return None

    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # Try CoinAPI first
            result = await self.coinapi.get_current_price(symbol)

            if result.get("success") and result.get("price"):
                return float(result["price"])

            return None

        except Exception as e:
            logger.debug(f"Error getting price for {symbol}: {e}")
            return None

    async def _send_spike_alert(
        self,
        symbol: str,
        current_price: float,
        old_price: float,
        change_pct: float,
        direction: str
    ):
        """Send instant Telegram alert for price spike"""
        try:
            # Format alert message
            message = self._format_spike_alert(
                symbol=symbol,
                current_price=current_price,
                old_price=old_price,
                change_pct=change_pct,
                direction=direction
            )

            # Send via Telegram
            if self.telegram.enabled:
                await self.telegram._send_telegram_message(message)
                logger.info(f"✅ Instant spike alert sent for {symbol}")
            else:
                logger.warning(f"Telegram disabled - spike alert not sent for {symbol}")

        except Exception as e:
            logger.error(f"Error sending spike alert for {symbol}: {e}")

    def _format_spike_alert(
        self,
        symbol: str,
        current_price: float,
        old_price: float,
        change_pct: float,
        direction: str
    ) -> str:
        """Format spike alert message for Telegram"""

        # Direction emoji and severity
        if direction == "PUMP":
            direction_emoji = "🚀" * 3 if abs(change_pct) > 15 else "🚀" * 2 if abs(change_pct) > 10 else "🚀"
            severity = "EXTREME PUMP" if abs(change_pct) > 15 else "STRONG PUMP" if abs(change_pct) > 10 else "PUMP"
        else:
            direction_emoji = "📉" * 3 if abs(change_pct) > 15 else "📉" * 2 if abs(change_pct) > 10 else "📉"
            severity = "EXTREME DUMP" if abs(change_pct) > 15 else "STRONG DUMP" if abs(change_pct) > 10 else "DUMP"

        msg = f"""
{direction_emoji} PRICE SPIKE ALERT {direction_emoji}

🪙 Coin: ${symbol}
💰 Current Price: ${current_price:,.8f}
📊 Previous Price: ${old_price:,.8f}

⚡ PRICE CHANGE:
━━━━━━━━━━━━━━━━━━━━━━━
{direction_emoji} Change: {change_pct:+.2f}%
⏱️ Time Window: 5 minutes
🔥 Severity: {severity}

📈 TRADING IMPLICATIONS:
{self._get_trading_implications(change_pct, direction)}

⚠️ ACTION REQUIRED:
{self._get_action_recommendation(change_pct, direction)}

━━━━━━━━━━━━━━━━━━━━━━━
🕐 Detected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
⚙️ Source: Real-Time Price Monitor (30s interval)
💡 Alert Type: INSTANT (no cooldown)

#PriceSpike #{symbol} #CryptoSatX #EarlyEntry
"""
        return msg

    def _get_trading_implications(self, change_pct: float, direction: str) -> str:
        """Get trading implications based on spike"""
        abs_change = abs(change_pct)

        if direction == "PUMP":
            if abs_change > 15:
                return "⚠️ EXTREME pump! Possible parabolic move or news catalyst. High volatility expected. Consider taking profits or waiting for pullback."
            elif abs_change > 10:
                return "📈 STRONG pump! Significant buying pressure. Monitor for continuation or reversal. Consider scaling in on dips."
            else:
                return "📊 Notable pump. Increased buying interest. Watch for momentum continuation or resistance levels."
        else:
            if abs_change > 15:
                return "⚠️ EXTREME dump! Possible panic selling or negative news. High risk of further downside. Avoid catching falling knife."
            elif abs_change > 10:
                return "📉 STRONG dump! Heavy selling pressure. Monitor for support levels or capitulation signals."
            else:
                return "📊 Notable dump. Increased selling pressure. Watch for support levels and potential reversal."

    def _get_action_recommendation(self, change_pct: float, direction: str) -> str:
        """Get action recommendation based on spike"""
        abs_change = abs(change_pct)

        if direction == "PUMP":
            if abs_change > 15:
                return "🎯 WAIT for pullback (20-30% retracement typical). Set alerts for support levels. DO NOT FOMO at top!"
            elif abs_change > 10:
                return "🎯 Monitor closely. If breaking key resistance, can enter with tight stop loss. Target: +5-8% from entry."
            else:
                return "🎯 Early stage pump. Can consider entry if volume confirms. Stop loss: -3% from entry."
        else:
            if abs_change > 15:
                return "🎯 AVOID entry. Wait for stabilization and reversal signals. Set alerts for support bounce."
            elif abs_change > 10:
                return "🎯 Monitor for support bounce. Only enter if clear reversal pattern forms with volume."
            else:
                return "🎯 Watch for support levels. Can consider entry if price stabilizes with decreasing sell volume."

    async def get_status(self) -> Dict:
        """Get current detector status"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "spike_threshold": self.spike_threshold,
            "time_window_minutes": self.time_window_minutes,
            "top_coins_count": self.top_coins_count,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "coins_tracked": len(self.price_history),
            "total_alerts_sent": len(self.last_alert_times),
            "monitoring_coins": list(self.price_history.keys())[:20]  # Show first 20
        }


# Global instance
realtime_spike_detector = RealtimeSpikeDetector(
    check_interval=30,  # Check every 30 seconds
    spike_threshold=8.0,  # 8% threshold
    time_window_minutes=5,  # 5-minute window
    top_coins_count=100  # Monitor top 100 coins
)

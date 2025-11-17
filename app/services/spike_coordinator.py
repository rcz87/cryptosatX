"""
Spike Coordinator - Multi-Signal Correlation System
Aggregates signals from multiple spike detectors and provides unified alerts
Reduces false positives through cross-validation
"""
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from app.services.telegram_notifier import TelegramNotifier
from app.utils.logger import default_logger as logger


class SpikeType(Enum):
    """Types of spikes detected"""
    PRICE_PUMP = "price_pump"
    PRICE_DUMP = "price_dump"
    LIQUIDATION_LONG = "liquidation_long"
    LIQUIDATION_SHORT = "liquidation_short"
    SOCIAL_SPIKE = "social_spike"
    VOLUME_SPIKE = "volume_spike"
    WHALE_ACCUMULATION = "whale_accumulation"
    WHALE_DISTRIBUTION = "whale_distribution"


class ConfidenceLevel(Enum):
    """Confidence levels for spike signals"""
    EXTREME = "extreme"  # 3+ signals aligned
    HIGH = "high"  # 2 signals aligned
    MEDIUM = "medium"  # 1 strong signal
    LOW = "low"  # 1 weak signal


@dataclass
class SpikeSignal:
    """Individual spike signal from a detector"""
    spike_type: SpikeType
    symbol: str
    value: float  # Spike magnitude (%, $, etc.)
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)


@dataclass
class CorrelatedSpike:
    """Correlated spike event combining multiple signals"""
    symbol: str
    primary_signal: SpikeSignal
    supporting_signals: List[SpikeSignal]
    confidence: ConfidenceLevel
    timestamp: datetime
    score: float  # 0-100 correlation score


class SpikeCoordinator:
    """
    Central coordinator for all spike detection systems

    Features:
    - Aggregates signals from all detectors
    - Cross-validates multiple signals
    - Reduces false positives
    - Sends unified high-confidence alerts
    - Tracks signal correlation patterns
    """

    def __init__(
        self,
        correlation_window_seconds: int = 300  # 5-minute correlation window
    ):
        self.correlation_window_seconds = correlation_window_seconds
        self.telegram = TelegramNotifier()

        # Recent signals buffer: {symbol: [SpikeSignal]}
        self.recent_signals: Dict[str, List[SpikeSignal]] = {}

        # Correlated spikes cache
        self.correlated_spikes: List[CorrelatedSpike] = []

        # Alert history to avoid duplicate alerts
        self.alert_history: Set[str] = set()

        logger.info("Spike Coordinator initialized - multi-signal correlation active")

    async def register_spike(
        self,
        spike_type: SpikeType,
        symbol: str,
        value: float,
        metadata: Optional[Dict] = None
    ):
        """
        Register a spike signal from any detector
        Automatically correlates with other recent signals
        """
        try:
            current_time = datetime.utcnow()

            # Create spike signal
            signal = SpikeSignal(
                spike_type=spike_type,
                symbol=symbol,
                value=value,
                timestamp=current_time,
                metadata=metadata or {}
            )

            # Add to recent signals
            if symbol not in self.recent_signals:
                self.recent_signals[symbol] = []

            self.recent_signals[symbol].append(signal)

            # Clean old signals
            await self._clean_old_signals(symbol)

            # Check for correlation
            correlated = await self._check_correlation(symbol)

            if correlated:
                logger.info(
                    f"🔥 CORRELATED SPIKE: {symbol} - "
                    f"{len(correlated.supporting_signals) + 1} signals aligned, "
                    f"confidence: {correlated.confidence.value}"
                )

                # Send unified alert for high-confidence spikes
                if correlated.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.EXTREME]:
                    await self._send_correlated_alert(correlated)

        except Exception as e:
            logger.error(f"Error registering spike: {e}")

    async def _clean_old_signals(self, symbol: str):
        """Remove signals older than correlation window"""
        try:
            if symbol not in self.recent_signals:
                return

            cutoff_time = datetime.utcnow() - timedelta(seconds=self.correlation_window_seconds)

            self.recent_signals[symbol] = [
                s for s in self.recent_signals[symbol]
                if s.timestamp >= cutoff_time
            ]

            # Remove empty entries
            if not self.recent_signals[symbol]:
                del self.recent_signals[symbol]

        except Exception as e:
            logger.error(f"Error cleaning old signals: {e}")

    async def _check_correlation(self, symbol: str) -> Optional[CorrelatedSpike]:
        """
        Check if multiple signals are correlated for this symbol
        Returns CorrelatedSpike if correlation found
        """
        try:
            if symbol not in self.recent_signals:
                return None

            signals = self.recent_signals[symbol]

            if len(signals) < 1:
                return None

            # Get most recent signal as primary
            primary_signal = signals[-1]

            # Get supporting signals (within correlation window)
            supporting = [s for s in signals[:-1]]

            # Calculate confidence and score
            signal_count = len(signals)
            confidence, score = self._calculate_confidence(signals)

            # Create correlated spike
            correlated = CorrelatedSpike(
                symbol=symbol,
                primary_signal=primary_signal,
                supporting_signals=supporting,
                confidence=confidence,
                timestamp=datetime.utcnow(),
                score=score
            )

            # Store in cache
            self.correlated_spikes.append(correlated)

            return correlated

        except Exception as e:
            logger.error(f"Error checking correlation: {e}")
            return None

    def _calculate_confidence(self, signals: List[SpikeSignal]) -> tuple[ConfidenceLevel, float]:
        """
        Calculate confidence level and score based on signal combination

        Scoring rules:
        - 3+ signals = EXTREME (score 90-100)
        - 2 signals = HIGH (score 70-89)
        - 1 signal = MEDIUM (score 50-69)
        """
        signal_count = len(signals)

        # Count signal types
        signal_types = set(s.spike_type for s in signals)

        # Bonus points for complementary signals
        complementary_bonus = 0

        # Price pump + Social spike = strong bullish
        if SpikeType.PRICE_PUMP in signal_types and SpikeType.SOCIAL_SPIKE in signal_types:
            complementary_bonus += 15

        # Price pump + Short liquidation = short squeeze
        if SpikeType.PRICE_PUMP in signal_types and SpikeType.LIQUIDATION_SHORT in signal_types:
            complementary_bonus += 20

        # Price dump + Long liquidation = long squeeze
        if SpikeType.PRICE_DUMP in signal_types and SpikeType.LIQUIDATION_LONG in signal_types:
            complementary_bonus += 20

        # Whale accumulation + Price pump = smart money move
        if SpikeType.WHALE_ACCUMULATION in signal_types and SpikeType.PRICE_PUMP in signal_types:
            complementary_bonus += 25

        # Calculate base score
        if signal_count >= 3:
            base_score = 90
            confidence = ConfidenceLevel.EXTREME
        elif signal_count == 2:
            base_score = 70
            confidence = ConfidenceLevel.HIGH
        else:
            base_score = 50
            confidence = ConfidenceLevel.MEDIUM

        # Final score (capped at 100)
        final_score = min(100, base_score + complementary_bonus)

        return confidence, final_score

    async def _send_correlated_alert(self, correlated: CorrelatedSpike):
        """Send Telegram alert for correlated spike"""
        try:
            # Generate alert key to avoid duplicates
            alert_key = f"{correlated.symbol}_{correlated.timestamp.strftime('%Y%m%d%H%M')}"

            if alert_key in self.alert_history:
                logger.debug(f"Duplicate alert prevented for {correlated.symbol}")
                return

            # Add to history
            self.alert_history.add(alert_key)

            # Format message
            message = self._format_correlated_alert(correlated)

            # Send via Telegram
            if self.telegram.enabled:
                await self.telegram._send_telegram_message(message)
                logger.info(f"✅ Correlated spike alert sent for {correlated.symbol}")
            else:
                logger.warning("Telegram disabled - correlated alert not sent")

        except Exception as e:
            logger.error(f"Error sending correlated alert: {e}")

    def _format_correlated_alert(self, correlated: CorrelatedSpike) -> str:
        """Format correlated spike alert message"""

        # Confidence emoji
        if correlated.confidence == ConfidenceLevel.EXTREME:
            confidence_emoji = "🔥🔥🔥"
        elif correlated.confidence == ConfidenceLevel.HIGH:
            confidence_emoji = "🔥🔥"
        else:
            confidence_emoji = "🔥"

        # Signal summary
        all_signals = [correlated.primary_signal] + correlated.supporting_signals
        signal_types = [s.spike_type.value for s in all_signals]
        signal_count = len(all_signals)

        # Determine overall direction
        bullish_signals = sum(
            1 for s in all_signals
            if s.spike_type in [SpikeType.PRICE_PUMP, SpikeType.LIQUIDATION_SHORT, SpikeType.WHALE_ACCUMULATION]
        )
        bearish_signals = sum(
            1 for s in all_signals
            if s.spike_type in [SpikeType.PRICE_DUMP, SpikeType.LIQUIDATION_LONG, SpikeType.WHALE_DISTRIBUTION]
        )

        if bullish_signals > bearish_signals:
            direction = "BULLISH"
            direction_emoji = "🚀"
        elif bearish_signals > bullish_signals:
            direction = "BEARISH"
            direction_emoji = "📉"
        else:
            direction = "MIXED"
            direction_emoji = "⚠️"

        msg = f"""
{confidence_emoji} MULTI-SIGNAL CORRELATION ALERT {confidence_emoji}

🎯 Asset: ${correlated.symbol}
{direction_emoji} Direction: {direction}
📊 Confidence: {correlated.confidence.value.upper()} ({correlated.score:.0f}/100)

🔍 DETECTED SIGNALS ({signal_count}):
━━━━━━━━━━━━━━━━━━━━━━━
"""

        # Add each signal detail
        for i, signal in enumerate(all_signals, 1):
            signal_emoji = self._get_signal_emoji(signal.spike_type)
            signal_name = signal.spike_type.value.replace("_", " ").title()
            msg += f"{i}. {signal_emoji} {signal_name}: {signal.value:+.2f}\n"

        msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━

💡 CORRELATION INSIGHT:
{self._get_correlation_insight(all_signals)}

🎯 RECOMMENDED ACTION:
{self._get_recommended_action(correlated)}

━━━━━━━━━━━━━━━━━━━━━━━
🕐 Detected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
⚙️ Source: Multi-Signal Correlation Engine
🎯 Signals Aligned: {signal_count} within 5min window

#Correlation #{correlated.symbol} #CryptoSatX #MultiSignal
"""
        return msg

    def _get_signal_emoji(self, spike_type: SpikeType) -> str:
        """Get emoji for signal type"""
        emoji_map = {
            SpikeType.PRICE_PUMP: "📈",
            SpikeType.PRICE_DUMP: "📉",
            SpikeType.LIQUIDATION_LONG: "🔴",
            SpikeType.LIQUIDATION_SHORT: "🟢",
            SpikeType.SOCIAL_SPIKE: "📱",
            SpikeType.VOLUME_SPIKE: "💥",
            SpikeType.WHALE_ACCUMULATION: "🐋",
            SpikeType.WHALE_DISTRIBUTION: "🐳"
        }
        return emoji_map.get(spike_type, "⚡")

    def _get_correlation_insight(self, signals: List[SpikeSignal]) -> str:
        """Get insight based on signal combination"""
        signal_types = set(s.spike_type for s in signals)

        # Short squeeze
        if SpikeType.PRICE_PUMP in signal_types and SpikeType.LIQUIDATION_SHORT in signal_types:
            return (
                "🚀 SHORT SQUEEZE DETECTED!\n"
                "Price pump + short liquidations = forced buying cascade.\n"
                "High probability of continuation as more shorts get liquidated."
            )

        # Long squeeze
        if SpikeType.PRICE_DUMP in signal_types and SpikeType.LIQUIDATION_LONG in signal_types:
            return (
                "📉 LONG SQUEEZE DETECTED!\n"
                "Price dump + long liquidations = forced selling cascade.\n"
                "High probability of further downside as more longs get liquidated."
            )

        # Smart money accumulation
        if SpikeType.WHALE_ACCUMULATION in signal_types and SpikeType.PRICE_PUMP in signal_types:
            return (
                "🐋 SMART MONEY ACCUMULATION!\n"
                "Whale buying + price pump = institutional accumulation phase.\n"
                "Strong bullish signal - smart money positioning for rally."
            )

        # Viral pump
        if SpikeType.SOCIAL_SPIKE in signal_types and SpikeType.PRICE_PUMP in signal_types:
            return (
                "🔥 VIRAL PUMP DETECTED!\n"
                "Social spike + price pump = retail FOMO entering.\n"
                "Momentum play - but watch for exhaustion and reversal."
            )

        # Multiple signals
        if len(signals) >= 3:
            return (
                "⚡ MULTIPLE SIGNALS ALIGNED!\n"
                f"{len(signals)} independent signals confirmed within 5 minutes.\n"
                "Very high confidence - rare confluence of indicators."
            )

        return "Multiple signals detected. Cross-validation confirms elevated probability."

    def _get_recommended_action(self, correlated: CorrelatedSpike) -> str:
        """Get recommended action based on correlation"""
        if correlated.confidence == ConfidenceLevel.EXTREME:
            return (
                "🎯 EXTREME CONFIDENCE - HIGH PROBABILITY TRADE\n"
                "• Entry: IMMEDIATE (within 1-2 minutes)\n"
                "• Position Size: 2-3% of portfolio\n"
                "• Stop Loss: 3% from entry\n"
                "• Target: 8-12% from entry\n"
                "• Time Horizon: 1-4 hours"
            )
        elif correlated.confidence == ConfidenceLevel.HIGH:
            return (
                "🎯 HIGH CONFIDENCE - GOOD PROBABILITY TRADE\n"
                "• Entry: Monitor for 5 minutes, enter on confirmation\n"
                "• Position Size: 1-2% of portfolio\n"
                "• Stop Loss: 3% from entry\n"
                "• Target: 5-8% from entry\n"
                "• Time Horizon: 1-6 hours"
            )
        else:
            return (
                "🎯 MEDIUM CONFIDENCE - WAIT FOR CONFIRMATION\n"
                "• Entry: Wait for additional signals\n"
                "• Position Size: 0.5-1% of portfolio\n"
                "• Stop Loss: 2% from entry\n"
                "• Target: 3-5% from entry\n"
                "• Time Horizon: 1-12 hours"
            )

    async def get_status(self) -> Dict:
        """Get coordinator status"""
        total_signals = sum(len(signals) for signals in self.recent_signals.values())

        return {
            "correlation_window_seconds": self.correlation_window_seconds,
            "active_symbols": len(self.recent_signals),
            "total_recent_signals": total_signals,
            "correlated_spikes_detected": len(self.correlated_spikes),
            "alerts_sent": len(self.alert_history),
            "monitored_symbols": list(self.recent_signals.keys())
        }


# Global instance
spike_coordinator = SpikeCoordinator(
    correlation_window_seconds=300  # 5-minute correlation window
)

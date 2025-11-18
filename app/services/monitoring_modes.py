"""
Monitoring Modes Manager for Smart Money Tracking

Implements 3 specialized monitoring modes:
1. Scalp Monitor (15 min intervals) - For intraday traders
2. Swing Monitor (4 hour intervals) - For position traders
3. Smart Money Pulse (event-driven) - Only whale entry alerts

Each mode has specific filtering logic and alert thresholds.

Author: CryptoSatX Engineering Team
"""

import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from app.utils.logger import default_logger
from app.services.realtime_indicators import realtime_indicators


class MonitoringMode(Enum):
    """Monitoring mode types"""
    SCALP = "scalp"  # 15 min updates - fast intraday
    SWING = "swing"  # 4 hour updates - position holding
    PULSE = "pulse"  # Event-driven - only big whale moves


class MonitoringModes:
    """
    Manages different monitoring modes with specific characteristics

    **Mode Characteristics:**

    SCALP (15 min):
    - Update frequency: Every 15 minutes
    - Best for: Intraday scalpers
    - Alerts on: All signals above threshold
    - Volume threshold: 1.5x average

    SWING (4 hour):
    - Update frequency: Every 4 hours
    - Best for: Position traders (like your SOL trade)
    - Alerts on: Medium-high confidence signals
    - Volume threshold: 1.8x average

    PULSE (Event-driven):
    - Update frequency: Only when whale activity detected
    - Best for: Noise-free, high-impact alerts
    - Alerts on: Only large whale entries ($100K+)
    - Volume threshold: 2.0x average
    """

    def __init__(self):
        self.logger = default_logger

        # Get active mode from environment
        mode_str = os.getenv("MONITORING_MODE", "swing").lower()
        try:
            self.active_mode = MonitoringMode(mode_str)
        except ValueError:
            self.logger.warning(f"Invalid mode '{mode_str}', defaulting to SWING")
            self.active_mode = MonitoringMode.SWING

        # Mode-specific configurations
        self.mode_configs = {
            MonitoringMode.SCALP: {
                "interval_minutes": 15,
                "volume_threshold": 1.5,
                "min_accumulation_score": 5,
                "min_distribution_score": 5,
                "min_whale_size_usd": 50000,  # $50K
                "alert_all_signals": True,
                "description": "Fast intraday monitoring"
            },
            MonitoringMode.SWING: {
                "interval_minutes": 240,  # 4 hours
                "volume_threshold": 1.8,
                "min_accumulation_score": 6,
                "min_distribution_score": 6,
                "min_whale_size_usd": 100000,  # $100K
                "alert_all_signals": False,  # Only medium-high confidence
                "description": "Position trader monitoring"
            },
            MonitoringMode.PULSE: {
                "interval_minutes": None,  # Event-driven
                "volume_threshold": 2.0,
                "min_accumulation_score": 7,
                "min_distribution_score": 7,
                "min_whale_size_usd": 250000,  # $250K minimum
                "alert_all_signals": False,  # Only high-impact events
                "description": "Whale-only precision alerts"
            }
        }

        self.logger.info(f"MonitoringModes initialized - Active mode: {self.active_mode.value}")
        self.logger.info(f"Config: {self.mode_configs[self.active_mode]}")

    def get_active_mode(self) -> MonitoringMode:
        """Get currently active monitoring mode"""
        return self.active_mode

    def set_mode(self, mode: MonitoringMode):
        """Change monitoring mode"""
        old_mode = self.active_mode
        self.active_mode = mode
        self.logger.info(f"Monitoring mode changed: {old_mode.value} → {mode.value}")

    def get_mode_config(self, mode: Optional[MonitoringMode] = None) -> Dict:
        """Get configuration for specified mode (or active mode)"""
        target_mode = mode or self.active_mode
        return self.mode_configs[target_mode]

    async def filter_signals(
        self,
        signals: List[Dict],
        signal_type: str = "accumulation"
    ) -> List[Dict]:
        """
        Filter signals based on active monitoring mode

        Args:
            signals: List of signal dicts from smart money scanner
            signal_type: "accumulation" or "distribution"

        Returns:
            Filtered list of signals that meet mode criteria
        """
        try:
            config = self.get_mode_config()
            filtered_signals = []

            for signal in signals:
                # Get signal score
                score_key = f"{signal_type}Score"
                signal_score = signal.get(score_key, 0)

                # Apply mode-specific threshold
                threshold = config[f"min_{signal_type}_score"]

                if signal_score < threshold:
                    continue  # Below threshold for this mode

                # For PULSE mode - additional strict filtering
                if self.active_mode == MonitoringMode.PULSE:
                    # Only alert on very high scores
                    if signal_score < 7:
                        continue

                    # Check if whale size is significant
                    # (would need actual trade size data from exchange)
                    # For now, rely on high score threshold

                # Add mode context to signal
                signal["monitoringMode"] = self.active_mode.value
                signal["modeConfig"] = config

                filtered_signals.append(signal)

            self.logger.info(
                f"Filtered {len(signals)} signals → {len(filtered_signals)} "
                f"({self.active_mode.value} mode)"
            )

            return filtered_signals

        except Exception as e:
            self.logger.error(f"Error filtering signals: {e}")
            return signals  # Return unfiltered on error

    async def should_alert(
        self,
        signal_data: Dict,
        indicators: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Determine if signal should trigger alert based on mode

        Args:
            signal_data: Signal information
            indicators: Optional realtime indicators data

        Returns:
            Tuple of (should_alert: bool, reason: str)
        """
        try:
            config = self.get_mode_config()

            # SCALP mode - alert on everything above threshold
            if self.active_mode == MonitoringMode.SCALP:
                return True, "Scalp mode - alerting all signals"

            # SWING mode - alert on medium-high confidence
            if self.active_mode == MonitoringMode.SWING:
                score = signal_data.get("accumulationScore") or signal_data.get("distributionScore", 0)

                if score >= 7:
                    return True, f"High confidence signal (score: {score})"
                elif score >= 6:
                    # Check for volume confirmation
                    if indicators and indicators.get("volumeSpike", {}).get("isSpike"):
                        return True, f"Medium confidence with volume spike (score: {score})"
                    else:
                        return False, "Medium confidence but no volume confirmation"
                else:
                    return False, f"Score too low for swing mode (score: {score})"

            # PULSE mode - only high-impact whale moves
            if self.active_mode == MonitoringMode.PULSE:
                score = signal_data.get("accumulationScore") or signal_data.get("distributionScore", 0)

                # Must be very high score
                if score < 7:
                    return False, f"Score below pulse threshold (score: {score})"

                # Must have volume confirmation
                if not indicators or not indicators.get("volumeSpike", {}).get("isSpike"):
                    return False, "No volume spike confirmation"

                volume_sig = indicators.get("volumeSpike", {}).get("significance", "normal")
                if volume_sig not in ["high", "extreme"]:
                    return False, f"Volume spike not significant enough ({volume_sig})"

                # Check for multi-indicator confluence
                confluence_count = 0

                # BOS detection
                if indicators.get("bosValidation", {}).get("isValidBOS"):
                    confluence_count += 1

                # Bid/Ask pressure
                if indicators.get("bidAskPressure", {}).get("isSignificant"):
                    confluence_count += 1

                # Whale walls
                if indicators.get("whaleWalls", {}).get("hasWhaleWalls"):
                    confluence_count += 1

                # OI correlation
                oi_data = indicators.get("oiCorrelation", {})
                if oi_data.get("strength") in ["moderate", "strong"]:
                    confluence_count += 1

                # Need at least 2 confirming indicators for PULSE alert
                if confluence_count < 2:
                    return False, f"Insufficient confluence ({confluence_count}/4 indicators)"

                return True, f"WHALE PULSE: High score + {confluence_count} confirming indicators"

            return False, "Unknown mode"

        except Exception as e:
            self.logger.error(f"Error in should_alert: {e}")
            return False, f"Error: {str(e)}"

    def format_alert_message(
        self,
        signal: Dict,
        indicators: Optional[Dict] = None,
        alert_reason: str = ""
    ) -> str:
        """
        Format alert message based on monitoring mode

        Args:
            signal: Signal data
            indicators: Realtime indicators
            alert_reason: Reason for alert

        Returns:
            Formatted alert message string
        """
        try:
            symbol = signal.get("symbol", "UNKNOWN")
            price = signal.get("price", 0)
            score = signal.get("accumulationScore") or signal.get("distributionScore", 0)
            pattern = signal.get("dominantPattern", "unknown")

            # Mode-specific emoji and header
            mode_emoji = {
                MonitoringMode.SCALP: "⚡",
                MonitoringMode.SWING: "🎯",
                MonitoringMode.PULSE: "🐋"
            }

            emoji = mode_emoji.get(self.active_mode, "📊")

            # Build message
            message = f"{emoji} **{self.active_mode.value.upper()} MODE ALERT**\n\n"
            message += f"**{symbol}** - ${price:,.2f}\n"
            message += f"Pattern: {pattern.upper()} (Score: {score}/10)\n\n"

            # Add reason
            if alert_reason:
                message += f"🎯 {alert_reason}\n\n"

            # Add signal reasons
            reasons = signal.get("reasons", [])
            if reasons:
                message += "**Key Factors:**\n"
                for reason in reasons[:3]:  # Top 3 reasons
                    message += f"• {reason}\n"
                message += "\n"

            # Add indicator confirmations for SWING/PULSE
            if self.active_mode in [MonitoringMode.SWING, MonitoringMode.PULSE] and indicators:
                message += "**Confirmations:**\n"

                # Volume spike
                volume_data = indicators.get("volumeSpike", {})
                if volume_data.get("isSpike"):
                    ratio = volume_data.get("ratio", 0)
                    message += f"✅ Volume Spike: {ratio:.2f}x average\n"

                # BOS validation
                bos_data = indicators.get("bosValidation", {})
                if bos_data.get("isValidBOS"):
                    confidence = bos_data.get("confidence", "unknown")
                    message += f"✅ BOS Validated: {confidence} confidence\n"

                # Bid/Ask pressure
                pressure_data = indicators.get("bidAskPressure", {})
                if pressure_data.get("isSignificant"):
                    side = pressure_data.get("dominantSide", "unknown")
                    pct = pressure_data.get("bidPressure") if side == "bid" else pressure_data.get("askPressure")
                    message += f"✅ {side.upper()} Pressure: {pct:.1f}%\n"

                # OI correlation
                oi_data = indicators.get("oiCorrelation", {})
                if oi_data.get("strength") in ["moderate", "strong"]:
                    pattern_oi = oi_data.get("pattern", "")
                    message += f"✅ OI: {pattern_oi}\n"

                message += "\n"

            # Add recommendation
            message += "**Recommendation:**\n"
            if pattern == "accumulation":
                if score >= 8:
                    message += "🟢 Strong BUY signal - Consider entry\n"
                elif score >= 6:
                    message += "🟡 Moderate BUY - Wait for confirmation\n"
                else:
                    message += "⚪ Watch list - Monitor development\n"
            else:  # distribution
                if score >= 8:
                    message += "🔴 Strong SELL signal - Consider exit/short\n"
                elif score >= 6:
                    message += "🟡 Moderate SELL - Take profits\n"
                else:
                    message += "⚪ Watch - Monitor for weakness\n"

            # Add timestamp
            message += f"\n⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"

            return message

        except Exception as e:
            self.logger.error(f"Error formatting alert message: {e}")
            return f"Alert for {signal.get('symbol', 'UNKNOWN')} - Error formatting message"

    def get_update_interval(self) -> Optional[int]:
        """
        Get update interval in minutes for active mode

        Returns:
            Interval in minutes, or None for event-driven (PULSE)
        """
        config = self.get_mode_config()
        return config.get("interval_minutes")

    def get_mode_description(self) -> str:
        """Get description of active monitoring mode"""
        config = self.get_mode_config()
        return config.get("description", "Unknown mode")

    def get_all_modes_info(self) -> Dict:
        """Get information about all available modes"""
        return {
            "currentMode": self.active_mode.value,
            "modes": {
                "scalp": {
                    "name": "Scalp Monitor",
                    "interval": "15 minutes",
                    "description": "Fast intraday monitoring for scalpers",
                    "alertFrequency": "High - All signals above threshold",
                    "bestFor": "Quick entries/exits, active trading"
                },
                "swing": {
                    "name": "Swing Monitor",
                    "interval": "4 hours",
                    "description": "Position monitoring for swing traders",
                    "alertFrequency": "Medium - High confidence signals only",
                    "bestFor": "Position holding like your SOL trade"
                },
                "pulse": {
                    "name": "Smart Money Pulse",
                    "interval": "Event-driven",
                    "description": "Only major whale activity alerts",
                    "alertFrequency": "Low - Very selective, high-impact only",
                    "bestFor": "Noise-free precision alerts"
                }
            },
            "config": self.mode_configs
        }


# Singleton instance
monitoring_modes = MonitoringModes()

"""
CryptoSatX Professional Alert Formatter
Formats smart entry recommendations into professional Telegram alerts

Creates actionable, comprehensive alerts with:
- Confluence scoring
- Entry zones with SL/TP
- Risk/Reward analysis
- Position sizing recommendations
- Complete reasoning
"""

import logging
from datetime import datetime
from typing import Optional
from app.services.smart_entry_engine import EntryRecommendation, EntryDirection

logger = logging.getLogger(__name__)


class ProAlertFormatter:
    """
    Professional alert formatter for Telegram

    Generates institutional-grade entry alerts with full analysis,
    risk management, and actionable recommendations.
    """

    @staticmethod
    def format_entry_alert(recommendation: EntryRecommendation) -> str:
        """
        Format entry recommendation as professional Telegram alert

        Returns formatted message with:
        - Header with direction and symbol
        - Confluence score and strength
        - Entry zone, SL, TP levels
        - Risk/Reward ratio
        - Position sizing suggestion
        - Complete reasoning
        - Urgency indicator
        """

        # Determine emoji based on direction
        if recommendation.direction == EntryDirection.LONG:
            direction_emoji = "🟢"
            direction_name = "LONG ENTRY SETUP"
        elif recommendation.direction == EntryDirection.SHORT:
            direction_emoji = "🔴"
            direction_name = "SHORT ENTRY SETUP"
        else:
            direction_emoji = "⚪"
            direction_name = "NEUTRAL - NO ENTRY"

        # Confluence strength emoji
        score = recommendation.confluence_score.total_score
        if score >= 80:
            conf_emoji = "🔥"  # Very strong
        elif score >= 70:
            conf_emoji = "💎"  # Strong
        elif score >= 60:
            conf_emoji = "✨"  # Good
        elif score >= 50:
            conf_emoji = "⚡"  # Moderate
        else:
            conf_emoji = "⚠️"  # Weak

        # Risk/Reward emoji
        rr = recommendation.risk_reward_ratio
        if rr >= 3:
            rr_emoji = "🎯"  # Excellent
        elif rr >= 2:
            rr_emoji = "✅"  # Good
        else:
            rr_emoji = "⚠️"  # Poor

        # Urgency emoji
        urgency = recommendation.urgency
        if urgency == "immediate":
            urgency_emoji = "🚨"
            urgency_text = "IMMEDIATE"
        elif urgency == "soon":
            urgency_emoji = "⏰"
            urgency_text = "SOON"
        elif urgency == "wait":
            urgency_emoji = "⏳"
            urgency_text = "WAIT FOR CONFIRMATION"
        else:
            urgency_emoji = "🛑"
            urgency_text = "AVOID - LOW PROBABILITY"

        lines = []

        # ===== HEADER =====
        lines.append(f"{direction_emoji} {recommendation.symbol} - {direction_name}")
        lines.append("")

        # ===== CONFLUENCE SCORE =====
        lines.append(f"{conf_emoji} CONFLUENCE SCORE: {score}/100")
        lines.append(f"├─ Strength: {recommendation.confluence_score.strength.value.upper()}")
        lines.append(f"├─ Signals Analyzed: {recommendation.confluence_score.signals_analyzed}")
        lines.append(f"├─ Bullish: {recommendation.confluence_score.signals_bullish}")
        lines.append(f"├─ Bearish: {recommendation.confluence_score.signals_bearish}")
        lines.append(f"└─ Neutral: {recommendation.confluence_score.signals_neutral}")
        lines.append("")

        # ===== ENTRY MANAGEMENT =====
        lines.append("📍 ENTRY ZONE:")
        lines.append(f"├─ Entry Low: ${recommendation.entry_zone_low:.6f}")
        lines.append(f"└─ Entry High: ${recommendation.entry_zone_high:.6f}")
        lines.append("")

        lines.append("🛑 STOP LOSS:")
        lines.append(f"└─ SL: ${recommendation.stop_loss:.6f}")
        sl_pct = abs((recommendation.stop_loss - recommendation.entry_zone_low) / recommendation.entry_zone_low * 100)
        lines.append(f"   ({sl_pct:.2f}% risk)")
        lines.append("")

        lines.append("🎯 TAKE PROFIT TARGETS:")
        lines.append(f"├─ TP1: ${recommendation.take_profit_1:.6f}")
        tp1_pct = abs((recommendation.take_profit_1 - recommendation.entry_zone_low) / recommendation.entry_zone_low * 100)
        lines.append(f"│  (+{tp1_pct:.2f}%)")

        if recommendation.take_profit_2:
            lines.append(f"├─ TP2: ${recommendation.take_profit_2:.6f}")
            tp2_pct = abs((recommendation.take_profit_2 - recommendation.entry_zone_low) / recommendation.entry_zone_low * 100)
            lines.append(f"│  (+{tp2_pct:.2f}%)")

        if recommendation.take_profit_3:
            lines.append(f"└─ TP3: ${recommendation.take_profit_3:.6f}")
            tp3_pct = abs((recommendation.take_profit_3 - recommendation.entry_zone_low) / recommendation.entry_zone_low * 100)
            lines.append(f"   (+{tp3_pct:.2f}%)")
        lines.append("")

        # ===== RISK MANAGEMENT =====
        lines.append(f"{rr_emoji} RISK/REWARD ANALYSIS:")
        lines.append(f"├─ Risk/Reward Ratio: 1:{rr:.2f}")

        if rr >= 3:
            rr_rating = "EXCELLENT"
        elif rr >= 2.5:
            rr_rating = "VERY GOOD"
        elif rr >= 2:
            rr_rating = "GOOD"
        elif rr >= 1.5:
            rr_rating = "ACCEPTABLE"
        else:
            rr_rating = "POOR"

        lines.append(f"└─ Rating: {rr_rating}")
        lines.append("")

        # ===== POSITION SIZING =====
        lines.append("💰 POSITION SIZING:")
        lines.append(f"└─ Suggested Size: {recommendation.position_size_pct:.1f}% of portfolio")

        if recommendation.position_size_pct >= 10:
            sizing_note = "High conviction trade"
        elif recommendation.position_size_pct >= 7:
            sizing_note = "Strong trade"
        elif recommendation.position_size_pct >= 5:
            sizing_note = "Standard trade"
        else:
            sizing_note = "Conservative trade"

        lines.append(f"   ({sizing_note})")
        lines.append("")

        # ===== CONFLUENCE BREAKDOWN =====
        lines.append("📊 CONFLUENCE BREAKDOWN:")
        breakdown = recommendation.confluence_score.breakdown

        # Sort by contribution (highest first)
        sorted_breakdown = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)

        for metric, contribution in sorted_breakdown:
            metric_display = metric.replace('_', ' ').title()
            lines.append(f"├─ {metric_display}: {contribution}")

        lines.append("")

        # ===== REASONING =====
        lines.append("🔍 KEY SIGNALS:")
        for i, reason in enumerate(recommendation.reasoning, 1):
            if i < len(recommendation.reasoning):
                lines.append(f"├─ {reason}")
            else:
                lines.append(f"└─ {reason}")
        lines.append("")

        # ===== URGENCY =====
        lines.append(f"{urgency_emoji} URGENCY: {urgency_text}")
        lines.append("")

        # ===== TRADING PLAN =====
        if recommendation.direction != EntryDirection.NEUTRAL:
            lines.append("📋 SUGGESTED TRADING PLAN:")

            if recommendation.direction == EntryDirection.LONG:
                lines.append(f"1. Set buy limit orders in entry zone")
                lines.append(f"2. Place stop loss at ${recommendation.stop_loss:.6f}")
                lines.append(f"3. Take 33% profit at TP1 (${recommendation.take_profit_1:.6f})")
                if recommendation.take_profit_2:
                    lines.append(f"4. Take 33% profit at TP2 (${recommendation.take_profit_2:.6f})")
                if recommendation.take_profit_3:
                    lines.append(f"5. Take 34% profit at TP3 (${recommendation.take_profit_3:.6f})")
                lines.append(f"6. Move SL to breakeven after TP1 hit")
            else:  # SHORT
                lines.append(f"1. Set sell limit orders in entry zone")
                lines.append(f"2. Place stop loss at ${recommendation.stop_loss:.6f}")
                lines.append(f"3. Take 33% profit at TP1 (${recommendation.take_profit_1:.6f})")
                if recommendation.take_profit_2:
                    lines.append(f"4. Take 33% profit at TP2 (${recommendation.take_profit_2:.6f})")
                if recommendation.take_profit_3:
                    lines.append(f"5. Take 34% profit at TP3 (${recommendation.take_profit_3:.6f})")
                lines.append(f"6. Move SL to breakeven after TP1 hit")

            lines.append("")

        # ===== FOOTER =====
        lines.append(f"⏰ {recommendation.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("🔗 CryptoSatX PRO - Smart Entry Engine")

        return "\n".join(lines)

    @staticmethod
    def format_short_alert(recommendation: EntryRecommendation) -> str:
        """
        Format compact alert for quick notifications

        Shorter version with essential info only
        """

        if recommendation.direction == EntryDirection.LONG:
            emoji = "🟢"
            direction = "LONG"
        elif recommendation.direction == EntryDirection.SHORT:
            emoji = "🔴"
            direction = "SHORT"
        else:
            emoji = "⚪"
            direction = "NEUTRAL"

        score = recommendation.confluence_score.total_score
        rr = recommendation.risk_reward_ratio

        lines = [
            f"{emoji} {recommendation.symbol} - {direction} SETUP",
            f"",
            f"Confluence: {score}/100",
            f"Entry: ${recommendation.entry_zone_low:.6f} - ${recommendation.entry_zone_high:.6f}",
            f"SL: ${recommendation.stop_loss:.6f}",
            f"TP1: ${recommendation.take_profit_1:.6f}",
            f"R:R = 1:{rr:.2f}",
            f"Size: {recommendation.position_size_pct:.1f}%",
            f"",
            f"🔗 CryptoSatX PRO"
        ]

        return "\n".join(lines)


# Global instance
_pro_alert_formatter = ProAlertFormatter()

def get_pro_alert_formatter() -> ProAlertFormatter:
    """Get global pro alert formatter instance"""
    return _pro_alert_formatter

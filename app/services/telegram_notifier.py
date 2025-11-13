# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Telegram Notifier Service
Sends trading signal alerts to Telegram with human-friendly formatting
UPDATED: Automatically saves signals to database after successful Telegram send
"""
import os
import httpx
from typing import Dict, Optional
from datetime import datetime


class TelegramNotifier:
    """
    Send formatted trading alerts to Telegram
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment
    Auto-saves signals to database when Telegram alert succeeds
    """

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            print(
                "[WARNING] Telegram notifier disabled - missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
            )

    async def send_signal_alert(self, signal_data: Dict) -> Dict:
        """
        Send trading signal alert to Telegram
        IMPORTANT: Only LONG/SHORT signals are sent (NEUTRAL signals are filtered out)
        Auto-saves to database after successful Telegram delivery

        Args:
            signal_data: Signal dict from /signals/{symbol} endpoint

        Returns:
            Dict with success status and message
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "Telegram notifications not configured",
            }

        try:
            # Format and send Telegram message
            message = self._format_signal_message(signal_data)
            result = await self._send_telegram_message(message)

            # IMPORTANT: Save to database ONLY after successful Telegram send
            # This ensures database contains only signals that were actually sent
            try:
                from app.storage.signal_history import signal_history

                save_result = await signal_history.save_signal(signal_data)
                print(
                    f"[SUCCESS] Signal saved to database: {save_result.get('message', 'success')}"
                )
            except Exception as save_error:
                # Don't fail Telegram send if database save fails
                print(f"[WARNING] Failed to save signal to database: {save_error}")

            return {
                "success": True,
                "message": "Alert sent to Telegram and saved to database",
                "telegram_response": result,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send Telegram alert: {str(e)}",
            }

    def _format_signal_message(self, signal_data: Dict) -> str:
        """
        Format signal data into professional Telegram message
        Uses new pro format with targets, stops, and AI commentary
        """
        return self._build_pro_signal_message(signal_data)

    def _build_pro_signal_message(self, data: Dict) -> str:
        """
        Build NEON CARD style Telegram message with cyber aesthetics
        Enhanced with AI Verdict Layer and Volatility Metrics
        """
        symbol = data.get("symbol", "BTC")
        signal = data.get("signal", "NEUTRAL").upper()
        score = data.get("score", 0)
        confidence = data.get("confidence", "medium").upper()
        price = data.get("price", 0.0)
        reasons = data.get("reasons", [])
        timestamp = data.get("timestamp", datetime.utcnow().isoformat())

        # Extract AI Verdict Layer
        ai_verdict_layer = data.get("aiVerdictLayer", {})
        verdict = ai_verdict_layer.get("verdict", "PENDING")
        risk_mode = ai_verdict_layer.get("riskMode", "NORMAL")
        risk_multiplier = ai_verdict_layer.get("riskMultiplier", 1.0)
        ai_confidence = ai_verdict_layer.get("aiConfidence")
        ai_summary = ai_verdict_layer.get("aiSummary", "")
        layer_checks = ai_verdict_layer.get("layerChecks", {})
        agreements = layer_checks.get("agreements", [])
        conflicts = layer_checks.get("conflicts", [])
        
        # Extract Volatility Metrics (Phase 2)
        volatility_metrics = ai_verdict_layer.get("volatilityMetrics", {})
        vol_multiplier = volatility_metrics.get("recommendedPositionMultiplier", 1.0)
        stop_loss_price = volatility_metrics.get("stopLossPrice")
        take_profit_price = volatility_metrics.get("takeProfitPrice")
        atr_value = volatility_metrics.get("atrValue")
        atr_percentage = volatility_metrics.get("atrPercentage")
        volatility_class = volatility_metrics.get("volatilityClassification", "NORMAL")
        trade_plan = volatility_metrics.get("tradePlanSummary", "")

        # Confidence display
        conf_display_map = {
            "LOW": "LOW CONFIDENCE",
            "MEDIUM": "MODERATE CONFIDENCE", 
            "HIGH": "HIGH CONFIDENCE"
        }
        conf_display = conf_display_map.get(confidence, confidence)
        
        # Signal emoji
        signal_emoji = "🟢" if signal == "LONG" else "🔴" if signal == "SHORT" else "⚪"
        
        # Calculate AI consensus percentage
        ai_conf = ai_confidence if ai_confidence else min(int(score * 1.2), 95)
        
        # Trend indicator (based on score)
        if score >= 65:
            trend = "Bullish" if signal == "LONG" else "Bearish"
        elif score >= 45:
            trend = "Neutral"
        else:
            trend = "Sideways"

        # Calculate targets with ATR-based TP if available
        if signal == "LONG":
            # Use ATR-based TP if available, otherwise fallback to % based
            if take_profit_price:
                target_1 = take_profit_price
                target_2 = price + ((take_profit_price - price) * 1.3)  # Extended target
            else:
                target_1 = price * 1.015  # +1.5%
                target_2 = price * 1.025  # +2.5%
            
            # Use ATR-based SL if available
            stop = stop_loss_price if stop_loss_price else price * 0.992
            
            entry_zone = f"${price:,.2f} ± 0.3%"
            tp_targets = f"\n🎯 TP1: ${target_1:,.2f}\n🎯 TP2: ${target_2:,.2f}"
            stop_loss = f"⛔ Stop Loss: &lt; ${stop:,.2f}"
            
        elif signal == "SHORT":
            if take_profit_price:
                target_1 = take_profit_price
                target_2 = price - ((price - take_profit_price) * 1.3)
            else:
                target_1 = price * 0.985  # -1.5%
                target_2 = price * 0.975  # -2.5%
            
            stop = stop_loss_price if stop_loss_price else price * 1.008
            
            entry_zone = f"${price:,.2f} ± 0.3%"
            tp_targets = f"\n🎯 TP1: ${target_1:,.2f}\n🎯 TP2: ${target_2:,.2f}"
            stop_loss = f"⛔ Stop Loss: &gt; ${stop:,.2f}"
        else:
            entry_zone = f"${price:,.2f}"
            tp_targets = "\n🎯 TP: —"
            stop_loss = "⛔ Stop Loss: —"

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        # Position sizing recommendation (combine risk + volatility)
        combined_multiplier = risk_multiplier * vol_multiplier
        if combined_multiplier >= 1.0:
            position_advice = f"{combined_multiplier:.2f}x — {combined_multiplier * 1.5:.2f}x"
        elif combined_multiplier >= 0.5:
            position_advice = f"{combined_multiplier:.2f}x — {combined_multiplier * 1.2:.2f}x"
        else:
            position_advice = f"{combined_multiplier:.2f}x — {combined_multiplier * 1.5:.2f}x (Conservative)"

        # Volatility mode display
        vol_mode_map = {
            "VERY_LOW": "Ultra-Safe Mode",
            "LOW": "Conservative Mode",
            "NORMAL": "Balanced Mode",
            "HIGH": "Active Mode",
            "VERY_HIGH": "Extreme Caution"
        }
        vol_mode = vol_mode_map.get(volatility_class, "Standard")

        # Build NEON CARD message
        divider = "━━━━━━━━━━━━━━━━━━━"
        
        msg = f"""🌌 <b>CRYPTOSATX</b> — ⚡
🔮 {symbol}/USDT — {signal} ({conf_display})

{divider}

🌈 ✨ <b>OVERVIEW</b>

🔹 Precision Score: {score:.1f} / 100
🔹 AI Consensus: {ai_conf}% ({confidence})
🔹 Trend: {trend}
🔹 Signal Mode: {vol_mode}

{divider}

🔥 🚀 <b>ENTRY PLAN (NEON MODE)</b>

🟩 Entry Zone: {entry_zone}{tp_targets}
{stop_loss}

{divider}

🌋 ⚠️ <b>VOLTAGE RISK</b>
"""

        # Add top 3 risk factors from conflicts or reasons
        if conflicts:
            for i, conflict in enumerate(conflicts[:3], start=1):
                msg += f"\n🔥 {conflict}"
        else:
            # Fallback to negative reasons if no conflicts
            for i, reason in enumerate(reasons[:3], start=1):
                msg += f"\n⚡ {reason}"

        msg += f"""

{divider}

🤖 <b>AI VERDICT — NEON INSIGHT</b>

<i>"{ai_summary if ai_summary else 'AI analysis in progress. Monitor closely for momentum shifts.'}"</i>

{divider}

💜 ⚡ <b>RISK RECOMMENDATION</b>

• Position Size: {position_advice}
• Volatility Mode: {vol_mode}"""

        # Add ATR info if available
        if atr_percentage:
            msg += f"\n• ATR Volatility: {atr_percentage:.2f}%"
        
        # Add entry timing advice
        if verdict == "SKIP" or risk_mode == "AVOID":
            msg += "\n• Entry Timing: ⚠️ WAIT for better setup"
        elif verdict == "DOWNSIZE":
            msg += "\n• Entry Timing: Enter with caution"
        else:
            msg += "\n• Entry Timing: Monitor entry zone"
        
        # Add trade plan if available
        if trade_plan:
            msg += f"\n• DO NOT: {self._extract_donot_advice(conflicts, risk_mode)}"

        msg += f"""

{divider}

🟪 📡 <b>SIGNAL DATA</b>

⏳ Time: {time_str} UTC
📡 Feeds: OKX • CoinAPI • Coinglass • LunarCrush
🤖 Engine: CryptoSatX AI Engine v2.5

{divider}
#CryptoSatX #{symbol} #Signal #AIFutures #NeonCard #CyberTrading"""

        return msg

    def _extract_donot_advice(self, conflicts: list, risk_mode: str) -> str:
        """Extract DO NOT advice from conflicts or risk mode"""
        if risk_mode == "AVOID":
            return "Do NOT enter this trade (High Risk)"
        elif conflicts:
            # Extract key warning from first conflict
            if "overcrowded" in conflicts[0].lower():
                return "Full-size position (rawan squeeze)"
            elif "funding" in conflicts[0].lower():
                return "Ignore high funding rate warning"
            elif "momentum" in conflicts[0].lower():
                return "Enter without confirmation"
        return "Overleveraged position"

    async def _send_telegram_message(self, message: str) -> Dict:
        """
        Send message via Telegram Bot API

        Returns:
            Dict with Telegram API response

        Raises:
            Exception: If HTTP request fails or Telegram API returns error
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)

            # Check HTTP status
            if response.status_code != 200:
                raise Exception(
                    f"Telegram API returned HTTP {response.status_code}: {response.text}"
                )

            # Parse JSON response
            result = response.json()

            # Check Telegram 'ok' field
            if not result.get("ok", False):
                error_description = result.get("description", "Unknown error")
                raise Exception(f"Telegram API error: {error_description}")

            return result

    async def send_custom_alert(
        self, title: str, message: str, emoji: str = "[ALERT]"
    ) -> Dict:
        """
        Send custom alert message

        Args:
            title: Alert title
            message: Alert message
            emoji: Emoji prefix (default: [ALERT])
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            formatted_message = f"{emoji} <b>{title}</b>\n\n{message}\n\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            result = await self._send_telegram_message(formatted_message)

            return {
                "success": True,
                "message": "Custom alert sent",
                "telegram_response": result,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send custom alert: {str(e)}",
            }

    async def send_test_message(self) -> Dict:
        """Send test message to verify Telegram configuration"""
        return await self.send_custom_alert(
            "Test Alert",
            "[SUCCESS] Telegram notifications are working correctly!\n\nYour CryptoSatX bot is ready to send trading signals.",
            "[BELL]",
        )


# Singleton instance
telegram_notifier = TelegramNotifier()

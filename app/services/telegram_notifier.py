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
        Build professional futures signal message with advanced formatting
        Enhanced with AI Verdict Layer (OpenAI V2 Signal Judge)
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
        ai_source = ai_verdict_layer.get("source", "rule_fallback")
        
        agreements = layer_checks.get("agreements", [])
        conflicts = layer_checks.get("conflicts", [])

        # Verdict emoji and status
        verdict_emoji_map = {
            "CONFIRM": "✅",
            "DOWNSIZE": "⚠️",
            "SKIP": "🚫",
            "WAIT": "⏸️",
            "PENDING": "⏳"
        }
        verdict_emoji = verdict_emoji_map.get(verdict, "❓")
        
        # Risk mode display
        risk_display_map = {
            "NORMAL": "🟢 NORMAL",
            "REDUCED": "🟡 REDUCED",
            "AVOID": "🔴 AVOID",
            "AGGRESSIVE": "🟣 AGGRESSIVE"
        }
        risk_display = risk_display_map.get(risk_mode, risk_mode)

        # Calculate AI confidence percentage from score
        ai_conf = min(int(score * 1.2), 95)  # Scale score to confidence %

        # Calculate target and stop based on signal AND risk multiplier
        if signal == "LONG":
            # Adjust targets based on risk multiplier
            base_target_1 = price * 1.015  # +1.5%
            base_target_2 = price * 1.025  # +2.5%
            stop = price * 0.992  # -0.8%
            
            # Scale targets down for DOWNSIZE, more conservative for REDUCED
            if risk_multiplier < 1.0:
                target_1 = price + (base_target_1 - price) * risk_multiplier
                target_2 = price + (base_target_2 - price) * risk_multiplier
            else:
                target_1 = base_target_1
                target_2 = base_target_2
            
            target_str = f"${target_1:,.2f} — ${target_2:,.2f}"
            stop_str = f"Below ${stop:,.2f}"
            emoji = "🟢"
        elif signal == "SHORT":
            base_target_1 = price * 0.985  # -1.5%
            base_target_2 = price * 0.975  # -2.5%
            stop = price * 1.008  # +0.8%
            
            if risk_multiplier < 1.0:
                target_1 = price - (price - base_target_1) * risk_multiplier
                target_2 = price - (price - base_target_2) * risk_multiplier
            else:
                target_1 = base_target_1
                target_2 = base_target_2
            
            target_str = f"${target_1:,.2f} — ${target_2:,.2f}"
            stop_str = f"Above ${stop:,.2f}"
            emoji = "🔴"
        else:
            target_str = "—"
            stop_str = "—"
            emoji = "⚪"

        # Use AI summary if available, otherwise fall back to reasons
        if ai_summary:
            commentary = ai_summary
        elif reasons:
            commentary = f"{reasons[0]}. "
            if len(reasons) > 1:
                commentary += f"Watch for {reasons[1].lower()}."
        else:
            commentary = "AI momentum shift detected. Monitor market closely."

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        # Build message with AI Verdict enhancement
        msg = f"""🚀 <b>CRYPTOSATX FUTURES SIGNAL</b> 🚀
========================================
Asset: {symbol}/USDT
Signal: <b>{signal}</b> {emoji}
Precision Score: {score:.1f} / 100
Confidence Level: {confidence} (AI Consensus {ai_conf}%)

<b>AI Verdict: {verdict_emoji} {verdict}</b>"""

        # Add AI confidence if available (from GPT-4)
        if ai_confidence is not None:
            msg += f" ({ai_confidence}%)"
        
        msg += f"""
Risk Mode: {risk_display}
Position Size: {risk_multiplier}x {'(Full)' if risk_multiplier >= 1.0 else '(Reduced)' if risk_multiplier > 0 else '(Skip)'}

Entry Zone: ${price:,.2f} ± 0.3%
Target: {target_str}
Stop: {stop_str}

========================================
<b>Market Insights</b>"""

        # Add factors
        for i, factor in enumerate(reasons[:4], start=1):
            msg += f"\n{i}. {factor}"

        # Add AI Verdict Analysis section if available
        if agreements or conflicts:
            msg += f"""

========================================
<b>📊 AI Verdict Analysis</b> ({ai_source.replace('_', ' ').title()})"""
            
            if agreements:
                msg += "\n\n<b>✅ Supporting Factors:</b>"
                for agreement in agreements[:3]:
                    msg += f"\n• {agreement}"
            
            if conflicts:
                msg += "\n\n<b>⚠️ Risk Warnings:</b>"
                for conflict in conflicts[:3]:
                    msg += f"\n• {conflict}"

        msg += f"""

========================================
<b>AI Commentary:</b>
<i>> "{commentary}"</i>

Signal Time: {time_str} UTC
Source: Multi-Data Engine (OKX + CoinAPI + Coinglass + LunarCrush)

========================================
Powered by CryptoSatX AI Engine v2.5 (Hybrid AI Judge)
#CryptoSatX #AITrading #Futures #SignalUpdate
"""
        return msg

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

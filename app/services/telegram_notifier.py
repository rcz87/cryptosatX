# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Telegram Notifier Service
Sends trading signal alerts to Telegram with human-friendly formatting
"""
import os
import httpx
from typing import Dict, Optional
from datetime import datetime


class TelegramNotifier:
    """
    Send formatted trading alerts to Telegram
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment
    """
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            print("⚠️ Telegram notifier disabled - missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    
    async def send_signal_alert(self, signal_data: Dict) -> Dict:
        """
        Send trading signal alert to Telegram
        
        Args:
            signal_data: Signal dict from /signals/{symbol} endpoint
        
        Returns:
            Dict with success status and message
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "Telegram notifications not configured"
            }
        
        try:
            message = self._format_signal_message(signal_data)
            result = await self._send_telegram_message(message)
            
            return {
                "success": True,
                "message": "Alert sent to Telegram",
                "telegram_response": result
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send Telegram alert: {str(e)}"
            }
    
    def _format_signal_message(self, signal_data: Dict) -> str:
        """
        Format signal data into human-readable Telegram message with emojis
        """
        symbol = signal_data.get("symbol", "UNKNOWN")
        signal = signal_data.get("signal", "NEUTRAL")
        score = signal_data.get("score", 0)
        price = signal_data.get("price", 0)
        confidence = signal_data.get("confidence", "low")
        reasons = signal_data.get("reasons", [])
        
        # Signal emoji
        signal_emoji = {
            "LONG": "🟢",
            "SHORT": "🔴",
            "NEUTRAL": "⚪️"
        }.get(signal, "⚪️")
        
        # Confidence emoji
        confidence_emoji = {
            "high": "⭐⭐⭐",
            "medium": "⭐⭐",
            "low": "⭐"
        }.get(confidence, "⭐")
        
        # Build message
        message_parts = [
            f"{signal_emoji} <b>CryptoSatX Signal Alert</b> {signal_emoji}",
            "",
            f"💰 <b>Symbol:</b> {symbol}",
            f"📊 <b>Signal:</b> {signal}",
            f"🎯 <b>Score:</b> {score}/100",
            f"✨ <b>Confidence:</b> {confidence.upper()} {confidence_emoji}",
            f"💵 <b>Price:</b> ${price:,.2f}",
            "",
            "<b>📌 Key Factors:</b>",
        ]
        
        # Add reasons
        for i, reason in enumerate(reasons[:3], 1):
            message_parts.append(f"  {i}. {reason}")
        
        # Add metrics
        metrics = signal_data.get("metrics", {})
        if metrics:
            message_parts.extend([
                "",
                "<b>📈 Metrics:</b>",
                f"  • Funding Rate: {metrics.get('fundingRate', 0):.4f}%",
                f"  • Open Interest: ${metrics.get('openInterest', 0):,.0f}",
                f"  • Social Score: {metrics.get('socialScore', 0):.1f}/100",
            ])
        
        # Add timestamp
        message_parts.extend([
            "",
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            "⚡ <i>Powered by CryptoSatX AI Engine</i>"
        ])
        
        return "\n".join(message_parts)
    
    async def _send_telegram_message(self, message: str) -> Dict:
        """Send message via Telegram Bot API"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            return response.json()
    
    async def send_custom_alert(self, title: str, message: str, emoji: str = "📢") -> Dict:
        """
        Send custom alert message
        
        Args:
            title: Alert title
            message: Alert message
            emoji: Emoji prefix (default: 📢)
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            formatted_message = f"{emoji} <b>{title}</b>\n\n{message}\n\n🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            result = await self._send_telegram_message(formatted_message)
            
            return {
                "success": True,
                "message": "Custom alert sent",
                "telegram_response": result
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send custom alert: {str(e)}"
            }
    
    async def send_test_message(self) -> Dict:
        """Send test message to verify Telegram configuration"""
        return await self.send_custom_alert(
            "Test Alert",
            "✅ Telegram notifications are working correctly!\n\nYour CryptoSatX bot is ready to send trading signals.",
            "🔔"
        )


# Singleton instance
telegram_notifier = TelegramNotifier()

"""
Telegram MSS Notifier Service
Sends Multi-Modal Signal Score (MSS) alerts to Telegram for high-potential coin discoveries
Specialized formatting for 3-phase analysis breakdown
"""
import os
import httpx
from typing import Dict, Optional
from datetime import datetime
from app.utils.logger import default_logger as logger


class TelegramMSSNotifier:
    """
    Send MSS discovery alerts to Telegram
    Focuses on early-stage coin opportunities with 3-phase validation
    """
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("⚠️ Telegram MSS notifier disabled - missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        else:
            logger.info("✅ Telegram MSS notifier initialized")
    
    async def send_mss_discovery_alert(
        self,
        symbol: str,
        mss_score: float,
        signal: str,
        confidence: str,
        phases: Dict,
        price: Optional[float] = None,
        market_cap: Optional[float] = None,
        fdv: Optional[float] = None
    ) -> Dict:
        """
        Send MSS discovery alert for high-scoring coins
        
        Args:
            symbol: Coin symbol (e.g., 'PEPE', 'ARB')
            mss_score: Overall MSS score (0-100)
            signal: Signal type (STRONG_LONG, MODERATE_LONG, LONG, etc.)
            confidence: Confidence level (very_high, high, medium, low)
            phases: Dict with phase1_discovery, phase2_confirmation, phase3_validation
            price: Current price (optional)
            market_cap: Market cap in USD (optional)
            fdv: Fully diluted valuation in USD (optional)
        
        Returns:
            Dict with success status and message
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "Telegram notifications not configured"
            }
        
        try:
            message = self._format_mss_message(
                symbol=symbol,
                mss_score=mss_score,
                signal=signal,
                confidence=confidence,
                phases=phases,
                price=price,
                market_cap=market_cap,
                fdv=fdv
            )
            
            result = await self._send_telegram_message(message)
            
            logger.info(f"✅ MSS alert sent for {symbol} (MSS: {mss_score:.1f})")
            
            return {
                "success": True,
                "message": f"MSS alert sent for {symbol}",
                "telegram_response": result
            }
        
        except Exception as e:
            logger.error(f"Failed to send MSS alert for {symbol}: {e}")
            return {
                "success": False,
                "message": f"Failed to send MSS alert: {str(e)}"
            }
    
    def _format_mss_message(
        self,
        symbol: str,
        mss_score: float,
        signal: str,
        confidence: str,
        phases: Dict,
        price: Optional[float],
        market_cap: Optional[float],
        fdv: Optional[float]
    ) -> str:
        """
        Format MSS data into professional Telegram message
        Emphasizes early-stage opportunity with 3-phase breakdown
        """
        # Extract phase scores
        phase1 = phases.get("phase1_discovery", {})
        phase2 = phases.get("phase2_confirmation", {})
        phase3 = phases.get("phase3_validation", {})
        
        p1_score = phase1.get("score", 0)
        p2_score = phase2.get("score", 0)
        p3_score = phase3.get("score", 0)
        
        # Signal emoji mapping
        emoji_map = {
            "STRONG_LONG": "🟢🚀",
            "MODERATE_LONG": "🟢",
            "LONG": "🟡",
            "WEAK_LONG": "⚪️",
            "NEUTRAL": "⚪️"
        }
        signal_emoji = emoji_map.get(signal.upper(), "⚪️")
        
        # MSS tier
        if mss_score >= 80:
            tier = "💎 DIAMOND"
            tier_emoji = "💎💎💎"
        elif mss_score >= 65:
            tier = "🥇 GOLD"
            tier_emoji = "🥇🥇"
        elif mss_score >= 50:
            tier = "🥈 SILVER"
            tier_emoji = "🥈"
        else:
            tier = "🥉 BRONZE"
            tier_emoji = "🥉"
        
        # Build message
        msg = f"""🔍 <b>MSS ALPHA DISCOVERY</b> {tier_emoji}
━━━━━━━━━━━━━━━━━━━━━━━
🪙 <b>{symbol}</b>
📊 MSS Score: <b>{mss_score:.1f}/100</b>
🎯 Signal: <b>{signal}</b> {signal_emoji}
⚡ Tier: <b>{tier}</b>
🔒 Confidence: {confidence.upper()}
"""
        
        # Add market data if available
        if price or market_cap or fdv:
            msg += "\n💰 <b>Market Data</b>\n"
            if price:
                msg += f"💵 Price: ${price:,.6f}\n"
            if market_cap:
                msg += f"📈 Market Cap: ${self._format_large_number(market_cap)}\n"
            if fdv:
                msg += f"💎 FDV: ${self._format_large_number(fdv)}\n"
        
        # Phase breakdown
        msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>3-Phase Analysis</b>

<b>Phase 1: Discovery</b> ({p1_score:.1f}/30)
{self._get_phase_bar(p1_score, 30)}
"""
        
        # Phase 1 details
        p1_breakdown = phase1.get("breakdown", {})
        if p1_breakdown:
            details = []
            if "fdv_usd" in p1_breakdown and p1_breakdown.get("fdv_usd"):
                fdv_val = p1_breakdown["fdv_usd"]
                details.append(f"FDV: ${self._format_large_number(fdv_val)}")
            if "age_hours" in p1_breakdown:
                age = p1_breakdown["age_hours"]
                if age < 24:
                    details.append(f"Age: {age:.0f}h (NEW!)")
                elif age < 168:
                    details.append(f"Age: {age/24:.1f}d")
            if "circulating_supply_pct" in p1_breakdown:
                supply = p1_breakdown["circulating_supply_pct"]
                details.append(f"Circ: {supply:.0f}%")
            
            if details:
                msg += f"└ {' • '.join(details)}\n"
        
        msg += f"""
<b>Phase 2: Social Momentum</b> ({p2_score:.1f}/35)
{self._get_phase_bar(p2_score, 35)}
"""
        
        # Phase 2 details
        p2_breakdown = phase2.get("breakdown", {})
        if p2_breakdown:
            details = []
            if "alt_rank" in p2_breakdown and p2_breakdown.get("alt_rank"):
                rank = p2_breakdown["alt_rank"]
                details.append(f"AltRank: {rank:.0f}")
            if "galaxy_score" in p2_breakdown and p2_breakdown.get("galaxy_score"):
                galaxy = p2_breakdown["galaxy_score"]
                details.append(f"Galaxy: {galaxy:.0f}")
            if "volume_24h_change_pct" in p2_breakdown:
                vol_change = p2_breakdown["volume_24h_change_pct"]
                if vol_change > 60:
                    details.append(f"Vol Spike: {vol_change:.0f}% 🔥")
                elif vol_change > 0:
                    details.append(f"Vol: +{vol_change:.0f}%")
            
            if details:
                msg += f"└ {' • '.join(details)}\n"
        
        msg += f"""
<b>Phase 3: Whale Validation</b> ({p3_score:.1f}/35)
{self._get_phase_bar(p3_score, 35)}
"""
        
        # Phase 3 details
        p3_breakdown = phase3.get("breakdown", {})
        if p3_breakdown:
            details = []
            if "whale_accumulation" in p3_breakdown:
                whale = p3_breakdown["whale_accumulation"]
                if whale:
                    details.append("Whale Activity: YES 🐋")
            if "top_trader_long_ratio" in p3_breakdown and p3_breakdown.get("top_trader_long_ratio"):
                ratio = p3_breakdown["top_trader_long_ratio"]
                details.append(f"Trader Ratio: {ratio:.2f}")
            if "oi_trend" in p3_breakdown:
                oi = p3_breakdown["oi_trend"]
                if oi == "increasing":
                    details.append("OI: Increasing ↗️")
                elif oi == "decreasing":
                    details.append("OI: Decreasing ↘️")
            
            if details:
                msg += f"└ {' • '.join(details)}\n"
        
        # Footer
        msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━
🧠 <b>AI Insight:</b>
<i>"{self._generate_insight(mss_score, signal, p1_score, p2_score, p3_score)}"</i>

🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC
⚙️ MSS Alpha System v1.0

#CryptoSatX #MSS #EarlyGems #Discovery
"""
        return msg
    
    def _get_phase_bar(self, score: float, max_score: float) -> str:
        """Generate visual progress bar for phase score"""
        percentage = (score / max_score) * 100
        filled = int(percentage / 10)
        empty = 10 - filled
        
        bar = "█" * filled + "░" * empty
        return f"{bar} {percentage:.0f}%"
    
    def _format_large_number(self, num: float) -> str:
        """Format large numbers with K/M/B suffixes"""
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num/1_000:.2f}K"
        else:
            return f"{num:.2f}"
    
    def _generate_insight(
        self,
        mss_score: float,
        signal: str,
        p1: float,
        p2: float,
        p3: float
    ) -> str:
        """Generate AI-style insight based on scores"""
        if mss_score >= 80:
            return "Exceptional early-stage opportunity detected. All phases show strong alignment with accumulation patterns."
        elif mss_score >= 65:
            if p3 >= 20:
                return "Strong institutional interest confirmed. Consider early position before retail discovery."
            else:
                return "Solid fundamentals with community momentum. Monitor whale activity for entry timing."
        elif mss_score >= 50:
            if p2 >= 20:
                return "Social momentum building. Watch for institutional validation in coming days."
            else:
                return "Meets discovery criteria. Requires additional confirmation before position."
        else:
            return "Early-stage analysis shows mixed signals. Further data needed for high-confidence entry."
    
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
    
    async def send_test_message(self) -> Dict:
        """Send test message to verify Telegram configuration"""
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            test_msg = """🔍 <b>MSS ALERT TEST</b> 💎

━━━━━━━━━━━━━━━━━━━━━━━
✅ Your MSS notification system is working!

The system will automatically alert you when:
• MSS score ≥ 75 (high-potential discoveries)
• Coins pass all 3 validation phases
• Early accumulation signals detected

Stay ahead of the market! 🚀

━━━━━━━━━━━━━━━━━━━━━━━
⚙️ MSS Alpha System
#CryptoSatX #TestAlert
"""
            result = await self._send_telegram_message(test_msg)
            
            return {
                "success": True,
                "message": "Test message sent successfully",
                "telegram_response": result
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send test message: {str(e)}"
            }


# Singleton instance
telegram_mss_notifier = TelegramMSSNotifier()

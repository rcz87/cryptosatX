"""
Telegram Message Formatters
Utility functions for formatting trading signals and alerts for Telegram
"""
from datetime import datetime
from typing import List, Dict


def format_mss_alert(symbol: str, mss_result: dict) -> str:
    """Format MSS analysis alert for Telegram"""
    mss_score = mss_result.get("mss_score", 0)
    signal = mss_result.get("signal", "NEUTRAL")
    confidence = mss_result.get("confidence", "low")
    
    # Determine tier from score
    if mss_score >= 80:
        tier = "DIAMOND"
        tier_emoji = "💎"
    elif mss_score >= 70:
        tier = "GOLD"
        tier_emoji = "🥇"
    elif mss_score >= 60:
        tier = "SILVER"
        tier_emoji = "🥈"
    else:
        tier = "BRONZE"
        tier_emoji = "🥉"
    
    phases = mss_result.get("phases", {})
    phase1 = phases.get("phase1_discovery", {})
    phase2 = phases.get("phase2_confirmation", {})
    phase3 = phases.get("phase3_validation", {})
    
    p1_breakdown = phase1.get("breakdown", {})
    p2_breakdown = phase2.get("breakdown", {})
    p3_breakdown = phase3.get("breakdown", {})
    
    message = f"""🚀 <b>MSS DISCOVERY ALERT</b> 🚀
━━━━━━━━━━━━━━━━━━━━━━━
{tier_emoji} <b>{symbol}/USDT</b>
📊 MSS Score: <b>{mss_score:.1f}/100</b> ({tier} Tier)
📈 Signal: <b>{signal}</b>
⚡ Confidence: {confidence.upper()}

━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>3-Phase Analysis</b>

<b>Phase 1 - Discovery:</b> {phase1.get('score', 0):.1f}/35
• FDV: ${p1_breakdown.get('fdv_usd', 0):,.0f}
• Age: {p1_breakdown.get('age_hours', 0):.1f}h
• Status: {p1_breakdown.get('status', 'N/A')}

<b>Phase 2 - Social Confirmation:</b> {phase2.get('score', 0):.1f}/30
• AltRank: {p2_breakdown.get('altrank', 0):.0f}
• Galaxy Score: {p2_breakdown.get('galaxy_score', 0):.1f}/100
• Status: {p2_breakdown.get('status', 'N/A')}

<b>Phase 3 - Institutional Validation:</b> {phase3.get('score', 0):.1f}/35
• OI Change: {p3_breakdown.get('oi_change_pct', 0):.1f}%
• Funding Rate: {p3_breakdown.get('funding_rate', 0):.4f}%
• Status: {p3_breakdown.get('status', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>Why This Matters:</b>
{tier} tier MSS score indicates {"STRONG hidden gem potential! 💎" if tier == "DIAMOND" else "good opportunity" if tier == "GOLD" else "moderate opportunity" if tier == "SILVER" else "limited opportunity"}

🕐 Alert Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC
⚙️ Source: MSS 3-Phase Analysis Engine

━━━━━━━━━━━━━━━━━━━━━━━
⚡ Powered by CryptoSatX MSS Discovery
#CryptoSatX #MSSDiscovery #HiddenGems
"""
    return message


def format_smart_money_alert(symbol: str, accumulation: List[Dict], distribution: List[Dict]) -> str:
    """Format smart money alert for Telegram"""
    
    message = f"""🐋 <b>SMART MONEY ALERT</b> 🐋
━━━━━━━━━━━━━━━━━━━━━━━
💎 <b>{symbol}/USDT</b>

"""
    
    if accumulation:
        acc = accumulation[0]
        message += f"""🟢 <b>ACCUMULATION DETECTED</b>
📊 Score: {acc.get('accumulationScore', 0):.1f}/10
💰 Price: ${acc.get('price', 0):.6f}
💡 Signal: Whales buying before retail!

<b>Key Reasons:</b>
"""
        for reason in acc.get('reasons', [])[:3]:
            message += f"• {reason}\n"
        
        message += "\n"
    
    if distribution:
        dist = distribution[0]
        message += f"""🔴 <b>DISTRIBUTION DETECTED</b>
📊 Score: {dist.get('distributionScore', 0):.1f}/10
💰 Price: ${dist.get('price', 0):.6f}
⚠️ Signal: Whales selling to retail!

<b>Key Reasons:</b>
"""
        for reason in dist.get('reasons', [])[:3]:
            message += f"• {reason}\n"
        
        message += "\n"
    
    if not accumulation and not distribution:
        message += """⚪ <b>NEUTRAL</b>
No significant whale accumulation or distribution detected.

"""
    
    message += f"""━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>Smart Money Strategy:</b>
{"BUY during accumulation (before retail FOMO)" if accumulation else ""}
{"AVOID/SHORT during distribution (whales exit to retail)" if distribution else ""}
{"Monitor for clearer signals" if not accumulation and not distribution else ""}

🕐 Alert Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC
⚙️ Source: Smart Money Pattern Recognition

━━━━━━━━━━━━━━━━━━━━━━━
⚡ Powered by CryptoSatX Whale Tracker
#CryptoSatX #SmartMoney #WhaleAlert
"""
    
    return message

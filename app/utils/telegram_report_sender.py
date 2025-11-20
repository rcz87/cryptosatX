"""
Telegram Report Sender for GPT→Telegram Hybrid System
Handles large data reports that exceed GPT Actions limits
Automatically splits messages and sends to Telegram with proper formatting
"""
import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.utils.logger import logger


class TelegramReportSender:
    """
    Send comprehensive analysis reports to Telegram
    Handles pagination for large datasets (>4096 chars per message)
    """
    
    MAX_MESSAGE_LENGTH = 4000  # Telegram limit is 4096, use 4000 for safety
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram report sender disabled - missing credentials")
    
    async def send_full_analysis_report(self, symbol: str, signal_data: Dict) -> Dict:
        """
        Send comprehensive signal analysis to Telegram
        Includes all data that doesn't fit in GPT Actions response
        
        Args:
            symbol: Trading symbol (e.g., "AVAX")
            signal_data: Full signal response from signals.get
            
        Returns:
            Dict with success status and message IDs
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            messages = self._format_full_report(symbol, signal_data)
            sent_messages = []
            
            for i, message in enumerate(messages):
                result = await self._send_message(message)
                if result.get("success"):
                    sent_messages.append(result.get("message_id"))
                    logger.info(f"Sent report part {i+1}/{len(messages)} to Telegram")
                else:
                    logger.error(f"Failed to send part {i+1}: {result.get('error')}")
            
            return {
                "success": len(sent_messages) > 0,
                "messages_sent": len(sent_messages),
                "total_parts": len(messages),
                "message_ids": sent_messages
            }
            
        except Exception as e:
            logger.error(f"Error sending Telegram report: {e}")
            return {"success": False, "message": str(e)}
    
    async def send_funding_rate_report(self, symbol: str, funding_data: Dict) -> Dict:
        """
        Send detailed funding rate report to Telegram
        Handles 18K+ exchange data points with pagination
        
        Args:
            symbol: Trading symbol
            funding_data: Full funding rate response from Coinglass
            
        Returns:
            Dict with success status
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            messages = self._format_funding_report(symbol, funding_data)
            sent_messages = []
            
            for message in messages:
                result = await self._send_message(message)
                if result.get("success"):
                    sent_messages.append(result.get("message_id"))
            
            return {
                "success": len(sent_messages) > 0,
                "messages_sent": len(sent_messages),
                "message_ids": sent_messages
            }
            
        except Exception as e:
            logger.error(f"Error sending funding report: {e}")
            return {"success": False, "message": str(e)}
    
    def _format_full_report(self, symbol: str, data: Dict) -> List[str]:
        """Format complete analysis into multiple Telegram messages"""
        messages = []
        
        # Part 1: Executive Summary
        part1 = self._build_executive_summary(symbol, data)
        messages.append(part1)
        
        # Part 2: Technical Analysis Details
        part2 = self._build_technical_details(symbol, data)
        if part2:
            messages.append(part2)
        
        # Part 3: Premium Metrics
        part3 = self._build_premium_metrics(symbol, data)
        if part3:
            messages.append(part3)
        
        # Part 4: AI Verdict Layer
        part4 = self._build_ai_verdict(symbol, data)
        if part4:
            messages.append(part4)
        
        # Part 5: Risk Assessment
        part5 = self._build_risk_assessment(symbol, data)
        if part5:
            messages.append(part5)
        
        return messages
    
    def _build_executive_summary(self, symbol: str, data: Dict) -> str:
        """Build executive summary section"""
        signal = data.get("signal", "NEUTRAL")
        score = data.get("score", 0)
        confidence = data.get("confidence", "medium")
        price = data.get("price", 0)
        timestamp = data.get("timestamp", "")
        
        signal_emoji = "🟢" if signal == "LONG" else "🔴" if signal == "SHORT" else "⚪"
        
        msg = f"""📊 <b>FULL ANALYSIS REPORT: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

{signal_emoji} <b>SIGNAL: {signal}</b>
📈 Score: <b>{score:.1f}/100</b>
⚡ Confidence: {confidence.upper()}
💰 Price: <b>${price:,.4f}</b>

🕐 Analysis Time: {timestamp[:19].replace('T', ' ')} UTC

━━━━━━━━━━━━━━━━━━━━━━━
<b>REASONS FOR SIGNAL:</b>

"""
        reasons = data.get("reasons", [])
        for i, reason in enumerate(reasons[:10], 1):
            msg += f"{i}. {reason}\n"
        
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📱 Part 1/5 - Executive Summary\n"
        msg += "⚡ Powered by CryptoSatX"
        
        return msg
    
    def _build_technical_details(self, symbol: str, data: Dict) -> Optional[str]:
        """Build technical analysis details"""
        metrics = data.get("metrics", {})
        if not metrics:
            return None
        
        msg = f"""📊 <b>TECHNICAL ANALYSIS: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>Market Metrics:</b>
• Funding Rate: {metrics.get('fundingRate', 0):.6f}%
• Open Interest: ${metrics.get('openInterest', 0):,.0f}
• Social Score: {metrics.get('socialScore', 0):.1f}/100
• Price Trend: {metrics.get('priceTrend', 'N/A')}

"""
        
        # Add comprehensive metrics
        comp_metrics = data.get("comprehensiveMetrics", {})
        if comp_metrics:
            msg += f"""<b>Multi-Timeframe Analysis:</b>
• Trend: {comp_metrics.get('multiTimeframeTrend', 'N/A')}

<b>Price Changes:</b>
"""
            price_changes = comp_metrics.get("priceChanges", {})
            for timeframe, change in price_changes.items():
                if change != 0:
                    emoji = "📈" if change > 0 else "📉"
                    msg += f"  {emoji} {timeframe}: {change:+.2f}%\n"
        
        # Add CoinAPI metrics
        coinapi_metrics = data.get("coinAPIMetrics", {})
        if coinapi_metrics:
            orderbook = coinapi_metrics.get("orderbook", {})
            trades = coinapi_metrics.get("trades", {})
            
            msg += f"""
<b>Order Flow Analysis:</b>
• Buy Pressure: {trades.get('buyPressure', 0):.2f}%
• Sell Pressure: {trades.get('sellPressure', 0):.2f}%
• Avg Trade Size: ${trades.get('avgTradeSize', 0):,.2f}
• 7d Volatility: {coinapi_metrics.get('volatility7d', 0):.2f}%
"""
        
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📱 Part 2/5 - Technical Details"
        
        return msg
    
    def _build_premium_metrics(self, symbol: str, data: Dict) -> Optional[str]:
        """Build premium metrics section"""
        premium = data.get("premiumMetrics", {})
        if not premium:
            return None
        
        msg = f"""🔥 <b>PREMIUM METRICS: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>Market Sentiment Indicators:</b>
• Liquidation Imbalance: {premium.get('liquidationImbalance', 'N/A')}
• Long/Short Sentiment: {premium.get('longShortSentiment', 'N/A')}
• OI Trend: {premium.get('oiTrend', 'N/A')}
• Smart Money Bias: {premium.get('smartMoneyBias', 'N/A')}
• Fear & Greed Index: {premium.get('fearGreedIndex', 0)}/100

━━━━━━━━━━━━━━━━━━━━━━━
<b>Data Quality Report:</b>
"""
        
        quality = data.get("data_quality", {})
        if quality:
            msg += f"""• Quality Score: {quality.get('quality_score', 0):.1f}%
• Services Success: {quality.get('services_successful', 0)}/{quality.get('services_total', 0)}
• Quality Level: {quality.get('quality_level', 'unknown').upper()}

"""
        
        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📱 Part 3/5 - Premium Metrics"
        
        return msg
    
    def _build_ai_verdict(self, symbol: str, data: Dict) -> Optional[str]:
        """Build AI verdict section"""
        ai_layer = data.get("aiVerdictLayer", {})
        if not ai_layer:
            return None
        
        verdict = ai_layer.get("verdict", "PENDING")
        risk_mode = ai_layer.get("riskMode", "NORMAL")
        ai_confidence = ai_layer.get("aiConfidence", 0)
        ai_summary = ai_layer.get("aiSummary", "")
        
        verdict_emoji = "✅" if verdict == "CONFIRM" else "⚠️" if verdict == "SKIP" else "❌"
        
        msg = f"""🤖 <b>AI VERDICT LAYER: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

{verdict_emoji} <b>VERDICT: {verdict}</b>
⚠️ Risk Mode: <b>{risk_mode}</b>
🎯 AI Confidence: {ai_confidence}%

<b>AI Analysis Summary:</b>
{ai_summary}

━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add layer checks
        layer_checks = ai_layer.get("layerChecks", {})
        agreements = layer_checks.get("agreements", [])
        conflicts = layer_checks.get("conflicts", [])
        
        if agreements:
            msg += "<b>✅ Agreements:</b>\n"
            for agreement in agreements[:5]:
                msg += f"  • {agreement}\n"
            msg += "\n"
        
        if conflicts:
            msg += "<b>❌ Conflicts:</b>\n"
            for conflict in conflicts[:5]:
                msg += f"  • {conflict}\n"
            msg += "\n"
        
        # Add volatility metrics
        vol_metrics = ai_layer.get("volatilityMetrics", {})
        if vol_metrics:
            stop_loss = vol_metrics.get("stopLossPrice")
            take_profit = vol_metrics.get("takeProfitPrice")
            
            msg += "<b>📊 Trade Plan:</b>\n"
            if stop_loss:
                msg += f"  • Stop Loss: ${stop_loss:,.4f}\n"
            if take_profit:
                msg += f"  • Take Profit: ${take_profit:,.4f}\n"
            msg += f"  • Position Size: {vol_metrics.get('recommendedPositionMultiplier', 1.0):.2f}x\n"
        
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📱 Part 4/5 - AI Verdict Layer"
        
        return msg
    
    def _build_risk_assessment(self, symbol: str, data: Dict) -> str:
        """Build risk assessment section"""
        msg = f"""⚠️ <b>RISK ASSESSMENT: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        ai_layer = data.get("aiVerdictLayer", {})
        risk_mode = ai_layer.get("riskMode", "NORMAL")
        risk_multiplier = ai_layer.get("riskMultiplier", 1.0)
        
        msg += f"<b>Risk Level: {risk_mode}</b>\n"
        msg += f"Position Multiplier: {risk_multiplier}x\n\n"
        
        # Interpretation
        if risk_mode == "AVOID":
            msg += "🚫 <b>RECOMMENDATION: DO NOT TRADE</b>\n"
            msg += "Too many conflicting signals or high risk factors.\n\n"
        elif risk_mode == "REDUCE":
            msg += "⚠️ <b>RECOMMENDATION: REDUCE POSITION</b>\n"
            msg += "Trade with caution and smaller position sizes.\n\n"
        else:
            msg += "✅ <b>RECOMMENDATION: NORMAL SIZING</b>\n"
            msg += "Risk factors within acceptable range.\n\n"
        
        # Data quality impact
        quality = data.get("data_quality", {})
        quality_score = quality.get("quality_score", 100)
        
        if quality_score < 70:
            msg += "⚠️ <b>WARNING:</b> Data quality below optimal\n"
            msg += f"Some critical services failed. Analysis confidence reduced.\n\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "<b>📊 Summary:</b>\n"
        msg += f"This is a comprehensive analysis based on {quality.get('services_successful', 0)} data sources.\n"
        msg += f"Quality Score: {quality_score:.1f}%\n\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📱 Part 5/5 - Risk Assessment\n"
        msg += "⚡ End of Full Report"
        
        return msg
    
    def _format_funding_report(self, symbol: str, data: Dict) -> List[str]:
        """Format funding rate data into paginated messages"""
        messages = []
        
        if not data.get("success"):
            return [f"❌ No funding rate data available for {symbol}"]
        
        stablecoin_data = data.get("stablecoinMargined", {})
        stats = stablecoin_data.get("statistics", {})
        top5_high = stablecoin_data.get("top5Highest", [])
        top5_low = stablecoin_data.get("top5Lowest", [])
        all_exchanges = stablecoin_data.get("allExchanges", [])
        
        # Part 1: Summary
        msg1 = f"""💰 <b>FUNDING RATE REPORT: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Overall Statistics:</b>
• Average: {stats.get('averagePercent', 0):.4f}%
• Highest: {stats.get('highest', 0):.4f}%
• Lowest: {stats.get('lowest', 0):.4f}%
• Total Data Points: {stats.get('count', 0):,}

━━━━━━━━━━━━━━━━━━━━━━━
<b>🟢 TOP 5 BULLISH (Highest Funding):</b>

"""
        for i, ex in enumerate(top5_high, 1):
            rate = ex.get("fundingRatePercent", 0)
            emoji = "😱" if abs(rate) > 100 else "🔥" if abs(rate) > 50 else "📈"
            msg1 += f"{i}. {emoji} <b>{ex.get('exchange')}</b>: {rate:+.2f}%\n"
        
        msg1 += "\n<b>🔴 TOP 5 BEARISH (Lowest Funding):</b>\n\n"
        
        for i, ex in enumerate(top5_low, 1):
            rate = ex.get("fundingRatePercent", 0)
            emoji = "😱" if abs(rate) > 100 else "🔥" if abs(rate) > 50 else "📉"
            msg1 += f"{i}. {emoji} <b>{ex.get('exchange')}</b>: {rate:+.2f}%\n"
        
        msg1 += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg1 += "📱 Part 1/? - Summary"
        
        messages.append(msg1)
        
        # Part 2+: All exchanges (paginated)
        if all_exchanges:
            exchanges_per_msg = 20
            total_exchanges = len(all_exchanges)
            total_pages = (total_exchanges + exchanges_per_msg - 1) // exchanges_per_msg
            
            for page in range(total_pages):
                start_idx = page * exchanges_per_msg
                end_idx = min(start_idx + exchanges_per_msg, total_exchanges)
                page_exchanges = all_exchanges[start_idx:end_idx]
                
                msg = f"""💰 <b>ALL EXCHANGES: {symbol}</b> (Part {page+2}/{total_pages+1})
━━━━━━━━━━━━━━━━━━━━━━━

"""
                for i, ex in enumerate(page_exchanges, start_idx + 1):
                    rate = ex.get("fundingRatePercent", 0)
                    emoji = "🟢" if rate > 0 else "🔴" if rate < 0 else "⚪"
                    msg += f"{i}. {emoji} {ex.get('exchange')}: {rate:+.4f}%\n"
                
                msg += f"\n━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"📱 Showing {start_idx+1}-{end_idx} of {total_exchanges} exchanges"
                
                messages.append(msg)
        
        # Final summary
        avg_rate = stats.get('averagePercent', 0)
        interpretation = "BEARISH" if avg_rate < 0 else "BULLISH" if avg_rate > 0 else "NEUTRAL"
        
        msg_final = f"""💰 <b>FUNDING RATE INTERPRETATION: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>Market Bias: {interpretation}</b>

Average funding rate is <b>{avg_rate:+.4f}%</b>

"""
        if avg_rate < 0:
            msg_final += """📉 <b>NEGATIVE FUNDING = Bearish Market</b>
• Shorts are overcrowded
• Shorts pay longs
• Market expects price decrease

<b>Trading Strategy:</b>
✅ LONG positions get paid (funding income)
❌ SHORT positions pay funding (cost)

<b>Best Exchanges for LONG:</b>
Use exchanges with most negative rates (you get paid most!)
"""
        else:
            msg_final += """📈 <b>POSITIVE FUNDING = Bullish Market</b>
• Longs are overcrowded  
• Longs pay shorts
• Market expects price increase

<b>Trading Strategy:</b>
❌ LONG positions pay funding (cost)
✅ SHORT positions get paid (funding income)

<b>Best Exchanges for SHORT:</b>
Use exchanges with most positive rates (you get paid most!)
"""
        
        msg_final += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg_final += "⚡ End of Funding Rate Report"
        
        messages.append(msg_final)
        
        return messages
    
    async def _send_message(self, text: str) -> Dict:
        """Send single message to Telegram"""
        if not self.enabled:
            return {"success": False, "error": "Not configured"}
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload)
                result = response.json()
                
                if result.get("ok"):
                    return {
                        "success": True,
                        "message_id": result.get("result", {}).get("message_id")
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("description", "Unknown error")
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
telegram_report_sender = TelegramReportSender()

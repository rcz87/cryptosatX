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
    
    async def send_liquidation_report(self, symbol: str, liquidation_data: Dict) -> Dict:
        """
        Send detailed liquidation report to Telegram
        Handles liquidation data with time series analysis
        
        Args:
            symbol: Trading symbol
            liquidation_data: Full liquidation response from Coinglass
            
        Returns:
            Dict with success status
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            messages = self._format_liquidation_report(symbol, liquidation_data)
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
            logger.error(f"Error sending liquidation report: {e}")
            return {"success": False, "message": str(e)}
    
    async def send_social_analytics_report(self, symbol: str, social_data: Dict) -> Dict:
        """
        Send social analytics report to Telegram
        Handles LunarCrush social metrics
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            messages = self._format_social_analytics_report(symbol, social_data)
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
            logger.error(f"Error sending social report: {e}")
            return {"success": False, "message": str(e)}
    
    async def send_whale_activity_report(self, symbol: str, whale_data: Dict) -> Dict:
        """
        Send whale activity report to Telegram
        Handles long/short whale positioning
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            messages = self._format_whale_activity_report(symbol, whale_data)
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
            logger.error(f"Error sending whale report: {e}")
            return {"success": False, "message": str(e)}
    
    async def send_smart_money_report(self, smart_money_data: Dict) -> Dict:
        """
        Send Smart Money Concept analysis report to Telegram
        Handles multiple coins from smart money scan
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            messages = self._format_smart_money_report(smart_money_data)
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
            logger.error(f"Error sending smart money report: {e}")
            return {"success": False, "message": str(e)}
    
    async def send_mss_discovery_report(self, mss_data: Dict) -> Dict:
        """
        Send MSS (Multi-Modal Signal Score) discovery report to Telegram
        Handles emerging cryptocurrency discoveries
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        try:
            messages = self._format_mss_discovery_report(mss_data)
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
            logger.error(f"Error sending MSS report: {e}")
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
    
    def _format_liquidation_report(self, symbol: str, data: Dict) -> List[str]:
        """Format liquidation data into Telegram messages"""
        messages = []
        
        # Extract data
        liquidations = data.get("liquidations", [])
        total_long = data.get("totalLongLiquidations", 0)
        total_short = data.get("totalShortLiquidations", 0)
        total_volume = total_long + total_short
        
        # Part 1: Summary
        msg = f"""💥 <b>LIQUIDATION REPORT: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Total Liquidations:</b>
• Total Volume: <b>${total_volume:,.0f}</b>
• Long Liquidations: ${total_long:,.0f} ({total_long/total_volume*100 if total_volume else 0:.1f}%)
• Short Liquidations: ${total_short:,.0f} ({total_short/total_volume*100 if total_volume else 0:.1f}%)

"""
        
        # Interpretation
        if total_long > total_short * 1.5:
            msg += """🔴 <b>BEARISH SIGNAL</b>
• Longs getting rekt heavily
• Price likely moving down
• Consider SHORT positions

"""
        elif total_short > total_long * 1.5:
            msg += """🟢 <b>BULLISH SIGNAL</b>
• Shorts getting squeezed
• Price likely moving up
• Consider LONG positions

"""
        else:
            msg += """⚪ <b>NEUTRAL</b>
• Balanced liquidations
• No clear directional bias

"""
        
        # Top liquidation events
        if liquidations:
            msg += "<b>📈 Recent Liquidation Events:</b>\n\n"
            for i, liq in enumerate(liquidations[:10], 1):
                side = liq.get("side", "UNKNOWN")
                amount = liq.get("amount", 0)
                price = liq.get("price", 0)
                emoji = "🔴" if side == "LONG" else "🟢"
                msg += f"{i}. {emoji} {side}: ${amount:,.0f} @ ${price:,.2f}\n"
        
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "⚡ Liquidation Analysis Complete"
        
        messages.append(msg)
        return messages
    
    def _format_social_analytics_report(self, symbol: str, data: Dict) -> List[str]:
        """Format LunarCrush social data into Telegram messages"""
        messages = []
        
        # Extract metrics
        social_score = data.get("social_score", 0)
        galaxy_score = data.get("galaxy_score", 0)
        alt_rank = data.get("alt_rank", 999)
        social_volume = data.get("social_volume", 0)
        social_dominance = data.get("social_dominance", 0)
        
        # Sentiment
        sentiment = data.get("sentiment", 0)
        sentiment_text = "BULLISH 🟢" if sentiment > 3 else "BEARISH 🔴" if sentiment < 3 else "NEUTRAL ⚪"
        
        msg = f"""📱 <b>SOCIAL ANALYTICS: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>🌟 Key Scores:</b>
• Social Score: <b>{social_score:.1f}/100</b>
• Galaxy Score: <b>{galaxy_score:.1f}/100</b>
• Alt Rank: <b>#{alt_rank}</b>
• Sentiment: {sentiment_text} ({sentiment:.1f}/5)

<b>📊 Engagement Metrics:</b>
• Social Volume: {social_volume:,} mentions
• Social Dominance: {social_dominance:.3f}%
• Social Contributors: {data.get('social_contributors', 0):,}

"""
        
        # Trending analysis
        trends = data.get("trends", {})
        if trends:
            msg += "<b>📈 Trending Status:</b>\n"
            msg += f"• 24h Change: {trends.get('social_volume_24h_change', 0):+.1f}%\n"
            msg += f"• Trending Score: {trends.get('trending_score', 0):.1f}/100\n\n"
        
        # Platform breakdown
        platforms = data.get("platform_breakdown", {})
        if platforms:
            msg += "<b>🌐 Platform Breakdown:</b>\n"
            for platform, count in list(platforms.items())[:5]:
                msg += f"• {platform.title()}: {count:,} posts\n"
            msg += "\n"
        
        # Hype analysis
        hype_metrics = data.get("hype_metrics", {})
        if hype_metrics:
            hype_level = hype_metrics.get("hype_level", "NORMAL")
            pump_risk = hype_metrics.get("pump_risk_score", 0)
            
            msg += f"<b>⚠️ Hype Analysis:</b>\n"
            msg += f"• Hype Level: <b>{hype_level}</b>\n"
            msg += f"• Pump Risk: {pump_risk:.1f}/100\n\n"
            
            if pump_risk > 70:
                msg += "🚨 <b>HIGH PUMP RISK!</b> Exercise extreme caution.\n\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📱 Social Analytics powered by LunarCrush"
        
        messages.append(msg)
        return messages
    
    def _format_whale_activity_report(self, symbol: str, data: Dict) -> List[str]:
        """Format whale long/short positioning into Telegram messages"""
        messages = []
        
        # Extract data
        long_positions = data.get("longPositions", [])
        short_positions = data.get("shortPositions", [])
        long_ratio = data.get("longRatio", 50)
        short_ratio = data.get("shortRatio", 50)
        
        msg = f"""🐋 <b>WHALE ACTIVITY: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Whale Positioning:</b>
• Long Ratio: <b>{long_ratio:.1f}%</b>
• Short Ratio: <b>{short_ratio:.1f}%</b>

"""
        
        # Interpretation
        if long_ratio > 60:
            msg += """🟢 <b>WHALES ARE BULLISH</b>
• Heavy long positioning
• Smart money expects upside
• Follow the whales → Consider LONG

"""
        elif short_ratio > 60:
            msg += """🔴 <b>WHALES ARE BEARISH</b>
• Heavy short positioning
• Smart money expects downside
• Follow the whales → Consider SHORT

"""
        else:
            msg += """⚪ <b>WHALES ARE NEUTRAL</b>
• Balanced positioning
• No clear directional bias
• Wait for better setup

"""
        
        # Top long whales
        if long_positions:
            msg += "<b>🐳 Top Long Whales:</b>\n\n"
            for i, whale in enumerate(long_positions[:5], 1):
                exchange = whale.get("exchange", "Unknown")
                ratio = whale.get("ratio", 0)
                msg += f"{i}. {exchange}: {ratio:.1f}% long\n"
            msg += "\n"
        
        # Top short whales
        if short_positions:
            msg += "<b>🐋 Top Short Whales:</b>\n\n"
            for i, whale in enumerate(short_positions[:5], 1):
                exchange = whale.get("exchange", "Unknown")
                ratio = whale.get("ratio", 0)
                msg += f"{i}. {exchange}: {ratio:.1f}% short\n"
        
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🐋 Whale intelligence by Coinglass"
        
        messages.append(msg)
        return messages
    
    def _format_smart_money_report(self, data: Dict) -> List[str]:
        """Format Smart Money Concept scan results into Telegram messages"""
        messages = []
        
        # Extract coins
        coins = data.get("coins", [])
        total_scanned = data.get("totalScanned", 0)
        filters_applied = data.get("filtersApplied", {})
        
        # Part 1: Summary
        msg = f"""💰 <b>SMART MONEY CONCEPT SCAN</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Scan Summary:</b>
• Total Coins Scanned: {total_scanned}
• Coins Meeting Criteria: <b>{len(coins)}</b>

<b>🎯 Filters Applied:</b>
• Min Accumulation: {filters_applied.get('min_accumulation', 0)}/10
• Min Distribution: {filters_applied.get('min_distribution', 0)}/10
• Timeframe: {filters_applied.get('timeframe', 'ALL')}

━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if not coins:
            msg += "\n❌ No coins found matching criteria.\n"
            msg += "Try lowering filter thresholds."
        else:
            msg += f"\n<b>🔥 TOP {min(len(coins), 10)} SMART MONEY OPPORTUNITIES:</b>\n\n"
            
            for i, coin in enumerate(coins[:10], 1):
                symbol = coin.get("symbol", "UNKNOWN")
                acc_score = coin.get("accumulationScore", 0)
                dist_score = coin.get("distributionScore", 0)
                pattern = coin.get("pattern", "UNKNOWN")
                
                # Signal interpretation
                if acc_score > 7 and dist_score < 3:
                    signal_emoji = "🟢"
                    signal = "STRONG BUY"
                elif dist_score > 7 and acc_score < 3:
                    signal_emoji = "🔴"
                    signal = "STRONG SELL"
                else:
                    signal_emoji = "⚪"
                    signal = "NEUTRAL"
                
                msg += f"""{i}. {signal_emoji} <b>{symbol}</b>
   • Accumulation: {acc_score}/10
   • Distribution: {dist_score}/10
   • Pattern: {pattern}
   • Signal: <b>{signal}</b>

"""
        
        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "💰 Smart Money Concept Analysis"
        
        messages.append(msg)
        
        # Part 2: Detailed analysis for top 3 coins
        if len(coins) > 0:
            msg2 = "<b>📈 DETAILED ANALYSIS - TOP 3:</b>\n"
            msg2 += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, coin in enumerate(coins[:3], 1):
                symbol = coin.get("symbol", "UNKNOWN")
                timeframe_analysis = coin.get("timeframeAnalysis", {})
                
                msg2 += f"<b>{i}. {symbol}</b>\n"
                msg2 += "Multi-Timeframe View:\n"
                
                for tf, analysis in timeframe_analysis.items():
                    msg2 += f"  • {tf}: {analysis.get('bias', 'N/A')}\n"
                
                msg2 += "\n"
            
            msg2 += "━━━━━━━━━━━━━━━━━━━━━━━"
            messages.append(msg2)
        
        return messages
    
    def _format_mss_discovery_report(self, data: Dict) -> List[str]:
        """Format MSS (Multi-Modal Signal Score) discovery into Telegram messages"""
        messages = []

        # Extract data
        discovered = data.get("discovered", [])
        phase = data.get("phase", "UNKNOWN")
        total_scanned = data.get("totalScanned", 0)
        filters = data.get("filters", {})

        msg = f"""🚀 <b>MSS DISCOVERY REPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>🔍 Discovery Phase: {phase}</b>
• Total Scanned: {total_scanned} coins
• Discoveries: <b>{len(discovered)}</b>

<b>🎯 Discovery Criteria:</b>
• Min MSS Score: {filters.get('min_mss_score', 0)}/100
• Max Results: {filters.get('max_results', 'unlimited')}

━━━━━━━━━━━━━━━━━━━━━━━
"""

        if not discovered:
            msg += "\n❌ No emerging coins discovered.\n"
            msg += "Market conditions may not be favorable for new discoveries."
        else:
            msg += f"\n<b>💎 TOP {min(len(discovered), 10)} EMERGING OPPORTUNITIES:</b>\n\n"

            for i, coin in enumerate(discovered[:10], 1):
                symbol = coin.get("symbol", "UNKNOWN")
                mss_score = coin.get("mssScore", 0)
                market_cap = coin.get("marketCap", 0)
                social_score = coin.get("socialScore", 0)
                momentum = coin.get("momentum", "UNKNOWN")

                # Score interpretation
                if mss_score >= 80:
                    grade = "🔥 EXCELLENT"
                elif mss_score >= 60:
                    grade = "✅ GOOD"
                elif mss_score >= 40:
                    grade = "⚠️ MODERATE"
                else:
                    grade = "❌ WEAK"

                msg += f"""{i}. <b>{symbol}</b> - {grade}
   • MSS Score: <b>{mss_score:.1f}/100</b>
   • Market Cap: ${market_cap:,.0f}
   • Social Score: {social_score:.1f}/100
   • Momentum: {momentum}

"""

        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🚀 Multi-Modal Signal Score Discovery"

        messages.append(msg)

        # Part 2: Detailed breakdown for top 3
        if len(discovered) >= 3:
            msg2 = "<b>📊 DETAILED METRICS - TOP 3:</b>\n"
            msg2 += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

            for i, coin in enumerate(discovered[:3], 1):
                symbol = coin.get("symbol", "UNKNOWN")
                breakdown = coin.get("breakdown", {})

                msg2 += f"<b>{i}. {symbol}</b>\n"
                msg2 += f"Phase 1 - Tokenomics: {breakdown.get('phase1Score', 0)}/100\n"
                msg2 += f"Phase 2 - Community: {breakdown.get('phase2Score', 0)}/100\n"
                msg2 += f"Phase 3 - Institutional: {breakdown.get('phase3Score', 0)}/100\n"

                risks = coin.get("risks", [])
                if risks:
                    msg2 += f"⚠️ Risks: {', '.join(risks[:3])}\n"

                msg2 += "\n"

            msg2 += "━━━━━━━━━━━━━━━━━━━━━━━"
            messages.append(msg2)

        return messages

    # ========================================================================
    # NEW OPERATIONS - 8 Additional Telegram Report Functions
    # ========================================================================

    async def send_market_summary_report(self, market_data: Dict) -> Dict:
        """
        Send market summary report to Telegram
        Handles top coins market overview
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            messages = self._format_market_summary_report(market_data)
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
            logger.error(f"Error sending market summary report: {e}")
            return {"success": False, "message": str(e)}

    async def send_indicators_report(self, indicator_name: str, symbol: str, indicator_data: Dict) -> Dict:
        """
        Send technical indicators report to Telegram
        Supports 12 Coinglass indicators (RSI, MA, EMA, MACD, Bollinger, etc.)
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            messages = self._format_indicators_report(indicator_name, symbol, indicator_data)
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
            logger.error(f"Error sending indicators report: {e}")
            return {"success": False, "message": str(e)}

    async def send_discovery_report(self, discovery_data: Dict) -> Dict:
        """
        Send LunarCrush trending topics/coins discovery report to Telegram
        Handles viral trending analysis
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            messages = self._format_discovery_report(discovery_data)
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
            logger.error(f"Error sending discovery report: {e}")
            return {"success": False, "message": str(e)}

    async def send_accumulation_report(self, accumulation_data: Dict) -> Dict:
        """
        Send smart money accumulation report to Telegram
        Handles whale buying activity analysis
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            messages = self._format_accumulation_report(accumulation_data)
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
            logger.error(f"Error sending accumulation report: {e}")
            return {"success": False, "message": str(e)}

    async def send_mss_analysis_report(self, symbol: str, mss_data: Dict) -> Dict:
        """
        Send MSS analysis report for single coin to Telegram
        Detailed MSS breakdown for specific cryptocurrency
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            messages = self._format_mss_analysis_report(symbol, mss_data)
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
            logger.error(f"Error sending MSS analysis report: {e}")
            return {"success": False, "message": str(e)}

    async def send_monitoring_report(self, monitoring_data: Dict) -> Dict:
        """
        Send automated monitoring status report to Telegram
        Handles monitoring system health and alerts
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            messages = self._format_monitoring_report(monitoring_data)
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
            logger.error(f"Error sending monitoring report: {e}")
            return {"success": False, "message": str(e)}

    async def send_spike_detection_report(self, spike_data: Dict) -> Dict:
        """
        Send spike detection report to Telegram
        Handles real-time price/liquidation/social spikes
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            messages = self._format_spike_detection_report(spike_data)
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
            logger.error(f"Error sending spike detection report: {e}")
            return {"success": False, "message": str(e)}

    async def send_analytics_report(self, analytics_data: Dict) -> Dict:
        """
        Send performance analytics report to Telegram
        Handles signal performance tracking and win rates
        """
        if not self.enabled:
            return {"success": False, "message": "Telegram not configured"}

        try:
            messages = self._format_analytics_report(analytics_data)
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
            logger.error(f"Error sending analytics report: {e}")
            return {"success": False, "message": str(e)}

    # ========================================================================
    # FORMATTING FUNCTIONS - 8 New Report Formatters
    # ========================================================================

    def _format_market_summary_report(self, data: Dict) -> List[str]:
        """Format market summary into Telegram messages"""
        messages = []

        # Extract actual fields from market_summary_service
        market_sentiment = data.get("market_sentiment", "UNKNOWN")
        major_coins = data.get("major_coins", {})  # Dict, not list
        aggregate_metrics = data.get("aggregate_metrics", {})
        explanation = data.get("explanation", "No explanation available")
        recommendations = data.get("recommendations", [])
        data_quality = data.get("data_quality", {})

        # Sentiment emoji
        sentiment_emoji = {
            "BULLISH": "🟢",
            "BEARISH": "🔴",
            "NEUTRAL": "⚪",
            "MIXED": "🟡"
        }.get(market_sentiment, "❓")

        msg = f"""📊 <b>MARKET SUMMARY</b>
━━━━━━━━━━━━━━━━━━━━━━━

{sentiment_emoji} <b>Market Sentiment: {market_sentiment}</b>

<b>📈 Aggregate Metrics:</b>
• Average Score: {aggregate_metrics.get('avg_score', 0):.1f}/100
• Avg Funding Rate: {aggregate_metrics.get('avg_funding_rate', 0):.3f}%
• Market Bias: {aggregate_metrics.get('market_bias', 'N/A')}

<b>📊 Signal Distribution:</b>
• LONG: {aggregate_metrics.get('total_signals', {}).get('LONG', 0)}
• SHORT: {aggregate_metrics.get('total_signals', {}).get('SHORT', 0)}
• NEUTRAL: {aggregate_metrics.get('total_signals', {}).get('NEUTRAL', 0)}

━━━━━━━━━━━━━━━━━━━━━━━
<b>🔥 MAJOR COINS:</b>

"""

        # Iterate through major coins dict
        for i, (symbol, coin_data) in enumerate(major_coins.items(), 1):
            if isinstance(coin_data, dict):
                signal = coin_data.get("signal", "UNKNOWN")
                score = coin_data.get("score", 0)
                price = coin_data.get("price", 0)
                confidence = coin_data.get("confidence", "unknown")

                signal_emoji = "🟢" if signal == "LONG" else "🔴" if signal == "SHORT" else "⚪"

                msg += f"""{i}. <b>{symbol}</b> {signal_emoji} {signal}
   • Score: {score:.1f}/100
   • Price: ${price:,.2f}
   • Confidence: {confidence}

"""

        msg += f"""━━━━━━━━━━━━━━━━━━━━━━━
<b>💡 EXPLANATION:</b>
{explanation}

"""

        if recommendations:
            msg += "<b>🎯 RECOMMENDATIONS:</b>\n"
            for rec in recommendations[:5]:
                msg += f"• {rec}\n"
            msg += "\n"

        msg += f"""━━━━━━━━━━━━━━━━━━━━━━━
<b>📊 Data Quality:</b>
• Coverage: {data_quality.get('coverage_percent', 0):.1f}%
• Successful: {data_quality.get('successful_fetches', 0)}/{data_quality.get('coins_analyzed', 0)}

📊 Market analysis by CryptoSatX"""

        messages.append(msg)
        return messages

    def _format_indicators_report(self, indicator_name: str, symbol: str, data: Dict) -> List[str]:
        """Format technical indicators into Telegram messages"""
        messages = []

        # Map indicator names to emojis
        indicator_emojis = {
            "rsi": "📊",
            "ma": "📈",
            "ema": "📉",
            "macd": "⚡",
            "bollinger": "📏",
            "basis": "🎯",
            "whale_index": "🐋",
            "cgdi": "💎",
            "cdri": "🔥",
            "golden_ratio": "🏆",
            "fear_greed": "😱"
        }

        emoji = indicator_emojis.get(indicator_name.lower(), "📊")

        msg = f"""{emoji} <b>{indicator_name.upper()} INDICATOR: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

"""

        # Different formatting based on indicator type
        if indicator_name.lower() == "rsi":
            value = data.get("value", 0)
            interpretation = "Oversold 🟢" if value < 30 else "Overbought 🔴" if value > 70 else "Neutral ⚪"

            msg += f"""<b>RSI Value: {value:.2f}</b>
• Signal: {interpretation}
• Period: {data.get('period', 14)}

<b>📊 Analysis:</b>
"""
            if value < 30:
                msg += "• Strong oversold condition\n"
                msg += "• Potential reversal upward\n"
                msg += "• Consider LONG entry\n"
            elif value > 70:
                msg += "• Strong overbought condition\n"
                msg += "• Potential reversal downward\n"
                msg += "• Consider SHORT entry\n"
            else:
                msg += "• No extreme condition\n"
                msg += "• Neutral market state\n"
                msg += "• Wait for better setup\n"

        elif indicator_name.lower() in ["ma", "ema"]:
            values = data.get("values", [])
            msg += "<b>Moving Averages:</b>\n"
            for period, value in values:
                msg += f"• {period}-period: ${value:,.2f}\n"
            msg += f"\n<b>Current Price:</b> ${data.get('currentPrice', 0):,.2f}\n"

        elif indicator_name.lower() == "fear_greed":
            value = data.get("value", 50)
            classification = data.get("classification", "Neutral")

            msg += f"""<b>Index Value: {value}/100</b>
• Classification: <b>{classification}</b>

<b>📊 Market Emotion:</b>
"""
            if value < 25:
                msg += "• 😱 Extreme Fear\n• 🟢 Opportunity to BUY\n• Market oversold\n"
            elif value < 50:
                msg += "• 😰 Fear\n• ⚪ Cautious approach\n• Accumulation zone\n"
            elif value < 75:
                msg += "• 😊 Greed\n• ⚠️ Take profits\n• Distribution zone\n"
            else:
                msg += "• 🤑 Extreme Greed\n• 🔴 Danger zone\n• Consider selling\n"

        else:
            # Generic formatting for other indicators
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    msg += f"• {key}: {value:.2f}\n"
                else:
                    msg += f"• {key}: {value}\n"

        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 {indicator_name.upper()} powered by Coinglass"

        messages.append(msg)
        return messages

    def _format_discovery_report(self, data: Dict) -> List[str]:
        """Format LunarCrush trending discovery into Telegram messages"""
        messages = []

        topics = data.get("topics", [])
        trending_coins = data.get("trendingCoins", [])

        msg = f"""🔥 <b>VIRAL DISCOVERY REPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>📈 Trending Topics:</b>
• Total Topics: {len(topics)}
• Trending Coins: {len(trending_coins)}

━━━━━━━━━━━━━━━━━━━━━━━
"""

        if topics:
            msg += "\n<b>🔥 HOT TOPICS:</b>\n\n"
            for i, topic in enumerate(topics[:10], 1):
                name = topic.get("name", "Unknown")
                volume = topic.get("volume", 0)
                change = topic.get("change", 0)

                msg += f"{i}. <b>{name}</b>\n"
                msg += f"   • Volume: {volume:,} mentions\n"
                msg += f"   • 24h Change: {change:+.1f}%\n\n"

        if trending_coins:
            msg += "<b>💎 TRENDING COINS:</b>\n\n"
            for i, coin in enumerate(trending_coins[:10], 1):
                symbol = coin.get("symbol", "UNKNOWN")
                social_volume = coin.get("socialVolume", 0)
                sentiment = coin.get("sentiment", 0)

                sentiment_emoji = "🟢" if sentiment > 3 else "🔴" if sentiment < 3 else "⚪"

                msg += f"{i}. {sentiment_emoji} <b>{symbol}</b>\n"
                msg += f"   • Social Volume: {social_volume:,}\n"
                msg += f"   • Sentiment: {sentiment:.1f}/5\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🔥 Viral trends by LunarCrush"

        messages.append(msg)
        return messages

    def _format_accumulation_report(self, data: Dict) -> List[str]:
        """Format whale accumulation activity into Telegram messages"""
        messages = []

        # Extract actual fields from smart_money_service
        accumulating_coins = data.get("accumulation_coins", data.get("accumulation", []))
        total_scanned = data.get("totalCoins", data.get("coinsScanned", 0))
        summary = data.get("summary", {})

        msg = f"""🐋 <b>WHALE ACCUMULATION REPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Scan Summary:</b>
• Coins Scanned: {total_scanned}
• Accumulation Detected: <b>{len(accumulating_coins)}</b>
• High Confidence: {summary.get('high_confidence', 0)}
• Medium Confidence: {summary.get('medium_confidence', 0)}

━━━━━━━━━━━━━━━━━━━━━━━
"""

        if not accumulating_coins:
            msg += "\n❌ No whale accumulation detected.\n"
            msg += "Whales are not actively buying currently."
        else:
            msg += "\n<b>🟢 WHALES ARE BUYING:</b>\n\n"

            for i, coin in enumerate(accumulating_coins[:10], 1):
                symbol = coin.get("symbol", "UNKNOWN")
                acc_score = coin.get("accumulationScore", 0)
                price = coin.get("price", 0)
                signal_type = coin.get("signalType", "NEUTRAL")
                composite_score = coin.get("compositeScore", 0)
                reasons = coin.get("reasons", [])

                # Strength indicator
                if acc_score >= 8:
                    strength = "🔥 VERY STRONG"
                elif acc_score >= 6:
                    strength = "✅ STRONG"
                elif acc_score >= 4:
                    strength = "⚠️ MODERATE"
                else:
                    strength = "⚪ WEAK"

                msg += f"""{i}. <b>{symbol}</b> - {strength}
   • Accumulation Score: <b>{acc_score}/10</b>
   • Price: ${price:,.4f}
   • Signal: {signal_type}
   • Composite Score: {composite_score:.1f}/100
"""
                if reasons:
                    msg += f"   • Key Reasons: {', '.join(reasons[:2])}\n"
                msg += "\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🐋 Smart Money tracking by CryptoSatX"

        messages.append(msg)
        return messages

    def _format_mss_analysis_report(self, symbol: str, data: Dict) -> List[str]:
        """Format MSS analysis for single coin into Telegram messages"""
        messages = []

        # Extract actual fields from mss_service
        mss_score = data.get("mss_score", data.get("mssScore", 0))
        signal = data.get("signal", "UNKNOWN")
        confidence = data.get("confidence", "unknown")
        phases = data.get("phases", {})
        breakdown = data.get("breakdown", {})
        warnings = data.get("warnings", [])

        # Extract phase scores
        phase1_score = phases.get("phase1_discovery", {}).get("score", 0)
        phase2_score = phases.get("phase2_confirmation", {}).get("score", 0)
        phase3_score = phases.get("phase3_validation", {}).get("score", 0)

        # Score emoji
        if mss_score >= 80:
            grade_emoji = "🔥"
            grade_text = "EXCELLENT"
        elif mss_score >= 60:
            grade_emoji = "✅"
            grade_text = "GOOD"
        elif mss_score >= 40:
            grade_emoji = "⚠️"
            grade_text = "MODERATE"
        else:
            grade_emoji = "❌"
            grade_text = "WEAK"

        signal_emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"

        msg = f"""💎 <b>MSS ANALYSIS: {symbol}</b>
━━━━━━━━━━━━━━━━━━━━━━━

{grade_emoji} <b>MSS Score: {mss_score:.1f}/100</b>
<b>Grade: {grade_text}</b>
{signal_emoji} <b>Signal: {signal}</b>
<b>Confidence: {confidence}</b>

━━━━━━━━━━━━━━━━━━━━━━━
<b>📊 Phase Breakdown:</b>

<b>Phase 1 - Discovery:</b> {phase1_score:.1f}/100
{phases.get('phase1_discovery', {}).get('breakdown', {}).get('status', 'Analysis complete')}

<b>Phase 2 - Social Confirmation:</b> {phase2_score:.1f}/100
• Social Score: {phases.get('phase2_confirmation', {}).get('breakdown', {}).get('social_score', 'N/A')}
• Volume Momentum: {phases.get('phase2_confirmation', {}).get('breakdown', {}).get('volume_score', 'N/A')}

<b>Phase 3 - Institutional Validation:</b> {phase3_score:.1f}/100
• OI Score: {phases.get('phase3_validation', {}).get('breakdown', {}).get('oi_score', 'N/A')}
• Whale Score: {phases.get('phase3_validation', {}).get('breakdown', {}).get('whale_score', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━
<b>📈 Overall Assessment:</b>
• Category: {breakdown.get('category', 'MIXED')}
• Risk Level: {breakdown.get('risk_level', 'MEDIUM')}

"""

        # Recommendation based on signal
        if signal == "BUY" and mss_score >= 70:
            msg += """<b>✅ RECOMMENDATION:</b>
• Strong BUY opportunity
• Consider position entry
• Monitor for optimal entry points

"""
        elif signal == "BUY" and mss_score >= 50:
            msg += """<b>⚠️ RECOMMENDATION:</b>
• Moderate BUY opportunity
• Wait for confirmation
• Small position acceptable

"""
        else:
            msg += """<b>❌ RECOMMENDATION:</b>
• Not a BUY signal currently
• Wait for better setup
• Monitor for improvements

"""

        # Warnings
        if warnings:
            msg += "<b>⚠️ Risk Warnings:</b>\n"
            for warning in warnings[:5]:
                msg += f"• {warning}\n"
            msg += "\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "💎 MSS Analysis by CryptoSatX"

        messages.append(msg)
        return messages

    def _format_monitoring_report(self, data: Dict) -> List[str]:
        """Format monitoring system status into Telegram messages"""
        messages = []

        status = data.get("status", "unknown")
        monitored_symbols = data.get("monitoredSymbols", [])
        alerts = data.get("recentAlerts", [])
        stats = data.get("stats", {})

        status_emoji = "✅" if status == "running" else "⚠️" if status == "paused" else "❌"

        msg = f"""🔍 <b>MONITORING SYSTEM REPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━

{status_emoji} <b>System Status: {status.upper()}</b>

<b>📊 Monitoring Stats:</b>
• Symbols Tracked: {len(monitored_symbols)}
• Active Alerts: {len(alerts)}
• Uptime: {stats.get('uptime', 'N/A')}
• Last Scan: {stats.get('lastScan', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━
"""

        if monitored_symbols:
            msg += "\n<b>🎯 Monitored Symbols:</b>\n"
            msg += ", ".join(monitored_symbols[:20])
            if len(monitored_symbols) > 20:
                msg += f" ...and {len(monitored_symbols) - 20} more"
            msg += "\n\n"

        if alerts:
            msg += "<b>🚨 Recent Alerts:</b>\n\n"
            for i, alert in enumerate(alerts[:5], 1):
                symbol = alert.get("symbol", "UNKNOWN")
                alert_type = alert.get("type", "UNKNOWN")
                message = alert.get("message", "No details")
                timestamp = alert.get("timestamp", "")

                msg += f"{i}. <b>{symbol}</b> - {alert_type}\n"
                msg += f"   {message}\n"
                msg += f"   {timestamp[:19]}\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🔍 Auto-monitoring by CryptoSatX"

        messages.append(msg)
        return messages

    def _format_spike_detection_report(self, data: Dict) -> List[str]:
        """Format spike detection results into Telegram messages"""
        messages = []

        price_spikes = data.get("priceSpikes", [])
        liquidation_spikes = data.get("liquidationSpikes", [])
        social_spikes = data.get("socialSpikes", [])

        total_spikes = len(price_spikes) + len(liquidation_spikes) + len(social_spikes)

        msg = f"""⚡ <b>SPIKE DETECTION REPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>🔥 Total Spikes Detected: {total_spikes}</b>
• Price Spikes: {len(price_spikes)}
• Liquidation Spikes: {len(liquidation_spikes)}
• Social Spikes: {len(social_spikes)}

━━━━━━━━━━━━━━━━━━━━━━━
"""

        if price_spikes:
            msg += "\n<b>📈 PRICE SPIKES:</b>\n\n"
            for i, spike in enumerate(price_spikes[:5], 1):
                symbol = spike.get("symbol", "UNKNOWN")
                change = spike.get("change", 0)
                timeframe = spike.get("timeframe", "Unknown")

                direction = "🟢" if change > 0 else "🔴"

                msg += f"{i}. {direction} <b>{symbol}</b>\n"
                msg += f"   • Change: {change:+.2f}%\n"
                msg += f"   • Timeframe: {timeframe}\n\n"

        if liquidation_spikes:
            msg += "<b>💥 LIQUIDATION SPIKES:</b>\n\n"
            for i, spike in enumerate(liquidation_spikes[:5], 1):
                symbol = spike.get("symbol", "UNKNOWN")
                amount = spike.get("amount", 0)
                side = spike.get("side", "Unknown")

                msg += f"{i}. <b>{symbol}</b>\n"
                msg += f"   • Amount: ${amount:,.0f}\n"
                msg += f"   • Side: {side}\n\n"

        if social_spikes:
            msg += "<b>🔥 SOCIAL SPIKES:</b>\n\n"
            for i, spike in enumerate(social_spikes[:5], 1):
                symbol = spike.get("symbol", "UNKNOWN")
                volume_change = spike.get("volumeChange", 0)

                msg += f"{i}. <b>{symbol}</b>\n"
                msg += f"   • Volume Change: {volume_change:+.1f}%\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "⚡ Real-time spike detection by CryptoSatX"

        messages.append(msg)
        return messages

    def _format_analytics_report(self, data: Dict) -> List[str]:
        """Format performance analytics into Telegram messages"""
        messages = []

        overall = data.get("overall", {})
        by_symbol = data.get("bySymbol", {})
        recent_signals = data.get("recentSignals", [])

        win_rate = overall.get("winRate", 0)
        total_signals = overall.get("totalSignals", 0)
        profitable = overall.get("profitable", 0)

        msg = f"""📊 <b>PERFORMANCE ANALYTICS</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>🎯 Overall Performance:</b>
• Win Rate: <b>{win_rate:.1f}%</b>
• Total Signals: {total_signals}
• Profitable: {profitable}
• Unprofitable: {total_signals - profitable}

<b>💰 Returns:</b>
• Average Return: {overall.get('avgReturn', 0):+.2f}%
• Best Trade: {overall.get('bestTrade', 0):+.2f}%
• Worst Trade: {overall.get('worstTrade', 0):+.2f}%

━━━━━━━━━━━━━━━━━━━━━━━
"""

        if by_symbol:
            msg += "\n<b>📈 Top Performing Symbols:</b>\n\n"
            sorted_symbols = sorted(by_symbol.items(), key=lambda x: x[1].get('winRate', 0), reverse=True)

            for symbol, stats in sorted_symbols[:5]:
                wr = stats.get('winRate', 0)
                count = stats.get('count', 0)
                avg_return = stats.get('avgReturn', 0)

                emoji = "🔥" if wr >= 70 else "✅" if wr >= 60 else "⚠️"

                msg += f"{emoji} <b>{symbol}</b>\n"
                msg += f"   • Win Rate: {wr:.1f}%\n"
                msg += f"   • Signals: {count}\n"
                msg += f"   • Avg Return: {avg_return:+.2f}%\n\n"

        if recent_signals:
            msg += "<b>📋 Recent Signals:</b>\n\n"
            for i, signal in enumerate(recent_signals[:5], 1):
                symbol = signal.get("symbol", "UNKNOWN")
                direction = signal.get("direction", "UNKNOWN")
                result = signal.get("result", "PENDING")
                pnl = signal.get("pnl", 0)

                result_emoji = "✅" if result == "WIN" else "❌" if result == "LOSS" else "⏳"

                msg += f"{i}. {result_emoji} <b>{symbol}</b> {direction}\n"
                msg += f"   • Result: {result}\n"
                msg += f"   • P/L: {pnl:+.2f}%\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📊 Performance tracking by CryptoSatX"

        messages.append(msg)
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

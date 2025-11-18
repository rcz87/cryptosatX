"""
Social Spike Monitor Service
Automated background monitoring for viral moments and social volume spikes
Sends real-time Telegram alerts when significant social activity is detected
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from app.services.lunarcrush_comprehensive_service import LunarCrushComprehensiveService
from app.services.telegram_notifier import TelegramNotifier
from app.utils.logger import default_logger as logger


class SocialSpikeMonitor:
    """
    Background service that monitors social metrics for viral moments
    
    Features:
    - Real-time monitoring of top coins
    - Spike detection (>50%, >100%, >300%)
    - Automated Telegram alerts
    - Configurable monitoring intervals
    """
    
    def __init__(
        self,
        check_interval: int = 300,  # 5 minutes default
        min_spike_threshold: float = 100.0,  # 100% minimum for alerts
        top_coins_count: int = 50  # Monitor top 50 coins
    ):
        self.check_interval = check_interval
        self.min_spike_threshold = min_spike_threshold
        self.top_coins_count = top_coins_count
        
        self.lunarcrush = LunarCrushComprehensiveService()
        self.telegram = TelegramNotifier()
        
        self.is_running = False
        self.last_check_time = None
        self.detected_spikes = {}  # Track recent spikes to avoid duplicates
        
        logger.info(
            f"Social Spike Monitor initialized: "
            f"interval={check_interval}s, threshold={min_spike_threshold}%, "
            f"monitoring {top_coins_count} coins"
        )
    
    async def start(self):
        """Start background monitoring loop"""
        if self.is_running:
            logger.warning("Social spike monitor already running")
            return
        
        self.is_running = True
        logger.info("🚀 Social Spike Monitor STARTED - monitoring for viral moments")
        
        try:
            while self.is_running:
                await self._check_social_spikes()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Social spike monitor crashed: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop background monitoring"""
        self.is_running = False
        logger.info("Social Spike Monitor STOPPED")
    
    async def _check_social_spikes(self):
        """Check all monitored coins for social spikes"""
        try:
            self.last_check_time = datetime.utcnow()
            logger.info(f"🔍 Checking social spikes at {self.last_check_time.isoformat()}")
            
            # Get top coins for monitoring
            coins_to_monitor = await self._get_coins_to_monitor()
            
            if not coins_to_monitor:
                logger.warning("No coins to monitor")
                return
            
            logger.info(f"Monitoring {len(coins_to_monitor)} coins for spikes")
            
            # Check each coin for spikes (parallel processing)
            tasks = [
                self._check_coin_spike(symbol)
                for symbol in coins_to_monitor
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count detected spikes
            spikes_detected = sum(1 for r in results if r and not isinstance(r, Exception))
            
            if spikes_detected > 0:
                logger.info(f"🔥 Detected {spikes_detected} social spikes!")
            else:
                logger.info("No significant spikes detected")
        
        except Exception as e:
            logger.error(f"Error in spike check cycle: {e}")
    
    async def _get_coins_to_monitor(self) -> List[str]:
        """
        Get list of coins to monitor
        Uses LunarCrush discovery to get top coins by market cap
        """
        try:
            # Get top coins from LunarCrush realtime discovery
            result = await self.lunarcrush.get_coins_realtime(
                limit=self.top_coins_count,
                sort="market_cap"
            )
            
            if result.get("success") and result.get("coins"):
                symbols = [coin.get("symbol") for coin in result["coins"]]
                logger.info(f"Monitoring {len(symbols)} top coins: {', '.join(symbols[:10])}...")
                return symbols
            
            # Fallback to default major coins
            logger.warning("Failed to get top coins, using fallback list")
            return [
                "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC",
                "LINK", "UNI", "ATOM", "LTC", "APT", "ARB", "OP", "SUI", "PEPE", "SHIB"
            ]
        
        except Exception as e:
            logger.error(f"Error getting coins to monitor: {e}")
            # Return major coins as fallback
            return ["BTC", "ETH", "SOL", "BNB", "XRP"]
    
    async def _check_coin_spike(self, symbol: str) -> Optional[Dict]:
        """
        Check a single coin for social spike
        Returns spike data if detected, None otherwise
        """
        try:
            # Get 24h social change data
            change_data = await self.lunarcrush.get_social_change(symbol, "24h")
            
            if not change_data.get("success"):
                return None

            # Handle None values from API by using 'or 0'
            social_vol_change = change_data.get("socialVolumeChange") or 0
            spike_level = change_data.get("spikeLevel", "normal")

            # Check if spike exceeds threshold
            if abs(social_vol_change) < self.min_spike_threshold:
                return None
            
            # Check if we already alerted about this spike recently
            spike_key = f"{symbol}_{spike_level}"
            if spike_key in self.detected_spikes:
                # Don't re-alert within 1 hour
                last_alert_time = self.detected_spikes[spike_key]
                time_since_alert = (datetime.utcnow() - last_alert_time).total_seconds()
                if time_since_alert < 3600:  # 1 hour cooldown
                    return None
            
            # New spike detected!
            logger.info(
                f"🔥 SPIKE DETECTED: {symbol} - "
                f"{social_vol_change:+.1f}% social volume change ({spike_level})"
            )
            
            # Record spike
            self.detected_spikes[spike_key] = datetime.utcnow()
            
            # Send Telegram alert
            await self._send_spike_alert(symbol, change_data)
            
            return {
                "symbol": symbol,
                "spike_level": spike_level,
                "social_volume_change": social_vol_change,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error checking spike for {symbol}: {e}")
            return None
    
    async def _send_spike_alert(self, symbol: str, change_data: Dict):
        """Send Telegram alert for detected spike"""
        try:
            # Handle None values from API by using 'or 0'
            social_vol_change = change_data.get("socialVolumeChange") or 0
            engagement_change = change_data.get("socialEngagementChange") or 0
            sentiment_change = change_data.get("sentimentChange") or 0
            spike_level = change_data.get("spikeLevel", "normal")
            
            # Get current price info
            coin_data = await self.lunarcrush.get_coin_comprehensive(symbol)
            price = coin_data.get("price", 0) if coin_data.get("success") else 0
            
            # Format alert message
            message = self._format_spike_alert(
                symbol=symbol,
                price=price,
                social_vol_change=social_vol_change,
                engagement_change=engagement_change,
                sentiment_change=sentiment_change,
                spike_level=spike_level
            )
            
            # Send via Telegram
            if self.telegram.enabled:
                await self.telegram._send_telegram_message(message)
                logger.info(f"✅ Spike alert sent for {symbol}")
            else:
                logger.warning(f"Telegram disabled - spike alert not sent for {symbol}")
        
        except Exception as e:
            logger.error(f"Error sending spike alert for {symbol}: {e}")
    
    def _format_spike_alert(
        self,
        symbol: str,
        price: float,
        social_vol_change: float,
        engagement_change: float,
        sentiment_change: float,
        spike_level: str
    ) -> str:
        """Format spike alert message for Telegram"""
        
        # Spike level emoji
        spike_emoji = {
            "extreme": "🔥🔥🔥",
            "high": "🔥🔥",
            "moderate": "🔥",
            "normal": "📊"
        }.get(spike_level, "📊")
        
        # Direction emoji
        direction_emoji = "🚀" if social_vol_change > 0 else "📉"
        
        # Sentiment emoji
        if sentiment_change > 10:
            sentiment_emoji = "😊 Bullish"
        elif sentiment_change < -10:
            sentiment_emoji = "😟 Bearish"
        else:
            sentiment_emoji = "😐 Neutral"
        
        msg = f"""
{spike_emoji} VIRAL MOMENT DETECTED {spike_emoji}

🪙 Coin: ${symbol}
💰 Price: ${price:,.8f}

📊 SOCIAL METRICS SPIKE:
━━━━━━━━━━━━━━━━━━━━━━━
{direction_emoji} Social Volume: {social_vol_change:+.1f}%
👥 Engagement: {engagement_change:+.1f}%
{sentiment_emoji} Sentiment: {sentiment_change:+.1f}%

🔥 Spike Level: {spike_level.upper()}

⚡ TRADING IMPLICATIONS:
{self._get_spike_interpretation(spike_level, social_vol_change)}

━━━━━━━━━━━━━━━━━━━━━━━
🕐 Detected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
⚙️ Source: LunarCrush Real-Time Monitor

#ViralMoment #SocialSpike #{symbol} #CryptoSatX
"""
        return msg
    
    def _get_spike_interpretation(self, spike_level: str, change_pct: float) -> str:
        """Get trading interpretation for spike"""
        if spike_level == "extreme" and change_pct > 0:
            return "⚠️ EXTREME positive spike! Possible viral trend starting. Monitor for continuation or reversal."
        elif spike_level == "extreme" and change_pct < 0:
            return "⚠️ EXTREME negative spike! Possible FUD or negative news. Exercise caution."
        elif spike_level == "high" and change_pct > 0:
            return "📈 HIGH positive interest! Growing attention - watch for momentum."
        elif spike_level == "high" and change_pct < 0:
            return "📉 HIGH negative sentiment. Potential selling pressure."
        elif spike_level == "moderate" and change_pct > 0:
            return "📊 Moderate increase in social activity. Early stage interest."
        else:
            return "📊 Notable social activity change detected."
    
    async def get_status(self) -> Dict:
        """Get current monitor status"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "min_spike_threshold": self.min_spike_threshold,
            "top_coins_count": self.top_coins_count,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "total_spikes_detected": len(self.detected_spikes),
            "recent_spikes": [
                {"spike": k, "detected_at": v.isoformat()}
                for k, v in list(self.detected_spikes.items())[-10:]
            ]
        }


# Global instance
social_spike_monitor = SocialSpikeMonitor(
    check_interval=300,  # 5 minutes
    min_spike_threshold=100.0,  # 100% minimum
    top_coins_count=50  # Monitor top 50 coins
)

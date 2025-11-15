"""
Social Hype Tracker Service
Stores historical hype data and detects spikes for auto-alerts
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.storage.database import db
from app.utils.logger import logger


class HypeTrackerService:
    """
    Track and analyze social hype over time
    - Store historical hype scores in database
    - Detect hype spikes (>20% increase)
    - Trigger Telegram alerts for significant changes
    """
    
    def __init__(self):
        self.spike_threshold = 20.0
    
    async def save_hype_snapshot(self, coin_data: Dict) -> bool:
        """
        Save current hype metrics to database
        
        Args:
            coin_data: Comprehensive coin data from LunarCrush
        
        Returns:
            True if saved successfully
        """
        try:
            platform_hype = coin_data.get("platformHype", {})
            
            async with db.acquire() as conn:
                if db.use_postgres:
                    await conn.execute(
                        """
                        INSERT INTO hype_history (
                            symbol, social_hype_score, social_volume,
                            social_engagement, social_contributors, social_dominance,
                            sentiment, twitter_hype, tiktok_hype, reddit_hype,
                            youtube_hype, news_hype, pump_risk, pump_risk_score,
                            price, price_change_24h, market_cap, volume_24h
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                            $11, $12, $13, $14, $15, $16, $17, $18
                        )
                        """,
                        coin_data.get("symbol"),
                        float(coin_data.get("socialHypeScore", 0)),
                        coin_data.get("socialVolume", 0),
                        coin_data.get("socialEngagement", 0),
                        coin_data.get("socialContributors", 0),
                        float(coin_data.get("socialDominance", 0)),
                        float(coin_data.get("averageSentiment", 0)),
                        float(platform_hype.get("twitterHype", 0)),
                        float(platform_hype.get("tiktokHype", 0)),
                        float(platform_hype.get("redditHype", 0)),
                        float(platform_hype.get("youtubeHype", 0)),
                        float(platform_hype.get("newsHype", 0)),
                        platform_hype.get("pumpRisk", "UNKNOWN"),
                        float(platform_hype.get("pumpRiskScore", 0)),
                        float(coin_data.get("price", 0)),
                        float(coin_data.get("percentChange24h", 0)),
                        float(coin_data.get("marketCap", 0)),
                        float(coin_data.get("volume24h", 0))
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to save hype snapshot: {e}")
            return False
    
    async def get_hype_history(
        self, 
        symbol: str, 
        hours: int = 24
    ) -> List[Dict]:
        """
        Retrieve historical hype data for a symbol
        
        Args:
            symbol: Coin symbol (e.g., "BTC")
            hours: Lookback period in hours (default 24)
        
        Returns:
            List of historical hype snapshots
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            async with db.acquire() as conn:
                if db.use_postgres:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM hype_history
                        WHERE symbol = $1 AND timestamp >= $2
                        ORDER BY timestamp DESC
                        """,
                        symbol,
                        cutoff
                    )
                    
                    return [dict(row) for row in rows]
                
            return []
            
        except Exception as e:
            logger.error(f"Failed to get hype history: {e}")
            return []
    
    async def detect_hype_spike(
        self,
        symbol: str,
        current_hype: float
    ) -> Optional[Dict]:
        """
        Detect if hype has spiked significantly (>20%)
        
        Args:
            symbol: Coin symbol
            current_hype: Current hype score
        
        Returns:
            Spike details if detected, None otherwise
        """
        try:
            history = await self.get_hype_history(symbol, hours=6)
            
            if not history or len(history) < 2:
                return None
            
            previous_hype = float(history[1].get("social_hype_score", 0))
            
            if previous_hype == 0:
                return None
            
            change_pct = ((current_hype - previous_hype) / previous_hype) * 100
            
            if change_pct >= self.spike_threshold:
                return {
                    "symbol": symbol,
                    "currentHype": current_hype,
                    "previousHype": previous_hype,
                    "changePercent": round(change_pct, 2),
                    "spikeDetected": True,
                    "severity": "EXTREME" if change_pct >= 50 else "HIGH" if change_pct >= 35 else "MODERATE",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to detect hype spike: {e}")
            return None
    
    async def track_and_alert(self, coin_data: Dict) -> Dict:
        """
        Track hype, save to database, and return spike alert if detected
        
        Args:
            coin_data: Comprehensive coin data
        
        Returns:
            {
                "saved": True/False,
                "spike": {...} or None,
                "shouldAlert": True/False
            }
        """
        symbol = coin_data.get("symbol")
        current_hype = coin_data.get("socialHypeScore", 0)
        
        spike = await self.detect_hype_spike(symbol, current_hype)
        
        saved = await self.save_hype_snapshot(coin_data)
        
        return {
            "saved": saved,
            "spike": spike,
            "shouldAlert": spike is not None
        }
    
    async def get_trending_hype_coins(self, limit: int = 10) -> List[Dict]:
        """
        Get coins with highest hype acceleration in last 6 hours
        
        Args:
            limit: Number of coins to return
        
        Returns:
            List of trending coins with hype acceleration
        """
        try:
            async with db.acquire() as conn:
                if db.use_postgres:
                    query = """
                    WITH recent_hype AS (
                        SELECT DISTINCT ON (symbol)
                            symbol,
                            social_hype_score as current_score,
                            timestamp as current_time
                        FROM hype_history
                        WHERE timestamp >= NOW() - INTERVAL '1 hour'
                        ORDER BY symbol, timestamp DESC
                    ),
                    previous_hype AS (
                        SELECT DISTINCT ON (symbol)
                            symbol,
                            social_hype_score as previous_score,
                            timestamp as previous_time
                        FROM hype_history
                        WHERE timestamp >= NOW() - INTERVAL '6 hours'
                          AND timestamp < NOW() - INTERVAL '1 hour'
                        ORDER BY symbol, timestamp DESC
                    )
                    SELECT 
                        r.symbol,
                        r.current_score,
                        p.previous_score,
                        ROUND(((r.current_score - p.previous_score) / p.previous_score * 100)::numeric, 2) as hype_acceleration
                    FROM recent_hype r
                    JOIN previous_hype p ON r.symbol = p.symbol
                    WHERE p.previous_score > 0
                    ORDER BY hype_acceleration DESC
                    LIMIT $1
                    """
                    
                    rows = await conn.fetch(query, limit)
                    return [dict(row) for row in rows]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get trending hype coins: {e}")
            return []


hype_tracker = HypeTrackerService()


async def send_hype_spike_alert(spike_data: Dict, coin_data: Dict) -> Dict:
    """
    Send Telegram alert for hype spike detection
    
    Args:
        spike_data: Spike detection info
        coin_data: Full coin data
    
    Returns:
        Alert status
    """
    try:
        from app.services.telegram_notifier import telegram_notifier
        from app.services.lunarcrush_comprehensive_service import format_hype_alert_message
        
        if not telegram_notifier.enabled:
            return {"success": False, "message": "Telegram not configured"}
        
        symbol = spike_data.get("symbol")
        change_pct = spike_data.get("changePercent", 0)
        severity = spike_data.get("severity", "MODERATE")
        
        severity_emoji = {
            "EXTREME": "🚨🚨🚨",
            "HIGH": "⚠️⚠️",
            "MODERATE": "📈"
        }
        
        header = f"""
{severity_emoji.get(severity, "📈")} **HYPE SPIKE DETECTED** {severity_emoji.get(severity, "📈")}

**{symbol}** - {severity} SURGE
Hype increased by **{change_pct:+.1f}%** in last 6 hours!
"""
        
        main_message = format_hype_alert_message(coin_data)
        
        full_message = header + "\n" + main_message
        
        result = await telegram_notifier._send_telegram_message(full_message)
        
        return {
            "success": True,
            "message": "Hype spike alert sent",
            "telegram_response": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send hype spike alert: {e}")
        return {"success": False, "message": str(e)}

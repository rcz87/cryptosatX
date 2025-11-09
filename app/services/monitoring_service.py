"""
CryptoSatX Monitoring Service
Automated signal monitoring and alerting system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from .telegram_notifier import TelegramNotifier
from .cache_service import CacheService

logger = logging.getLogger(__name__)

class AlertType(Enum):
    SIGNAL_CHANGE = "signal_change"
    STRONG_SIGNAL = "strong_signal"
    THRESHOLD_BREACH = "threshold_breach"
    TIME_BASED = "time_based"

@dataclass
class MonitoringConfig:
    """Configuration for monitoring service"""
    symbols: List[str]
    check_interval_minutes: int = 60
    strong_signal_threshold: float = 80.0
    weak_signal_threshold: float = 20.0
    enable_telegram: bool = True
    enable_cache: bool = True
    max_alerts_per_hour: int = 10

@dataclass
class SignalState:
    """Track signal state for each symbol"""
    symbol: str
    last_signal: str
    last_score: float
    last_check: datetime
    alert_count: int = 0
    last_alert_time: Optional[datetime] = None

class MonitoringService:
    """Automated monitoring and alerting service"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.telegram = TelegramNotifier()
        self.cache = CacheService()
        self.signal_states: Dict[str, SignalState] = {}
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # Initialize signal states
        for symbol in config.symbols:
            self.signal_states[symbol] = SignalState(
                symbol=symbol,
                last_signal="NEUTRAL",
                last_score=50.0,
                last_check=datetime.now() - timedelta(hours=1)  # Force first check
            )
    
    async def start_monitoring(self):
        """Start the monitoring service"""
        if self.running:
            logger.warning("Monitoring service already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started monitoring for {len(self.config.symbols)} symbols")
        logger.info(f"Check interval: {self.config.check_interval_minutes} minutes")
        logger.info(f"Strong signal threshold: {self.config.strong_signal_threshold}")
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._check_all_symbols()
                await asyncio.sleep(self.config.check_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _check_all_symbols(self):
        """Check all monitored symbols"""
        logger.info(f"Checking {len(self.config.symbols)} symbols...")
        
        for symbol in self.config.symbols:
            try:
                await self._check_symbol(symbol)
            except Exception as e:
                logger.error(f"Error checking {symbol}: {e}")
    
    async def _check_symbol(self, symbol: str):
        """Check a single symbol for alerts"""
        from app.main import get_signal_for_symbol  # Import to avoid circular dependency
        
        # Get current signal
        signal_data = await get_signal_for_symbol(symbol)
        if not signal_data:
            logger.warning(f"No signal data for {symbol}")
            return
        
        current_signal = signal_data.get('signal', 'NEUTRAL')
        current_score = signal_data.get('score', 50.0)
        current_time = datetime.now()
        
        # Get previous state
        state = self.signal_states.get(symbol)
        if not state:
            state = SignalState(
                symbol=symbol,
                last_signal="NEUTRAL",
                last_score=50.0,
                last_check=current_time - timedelta(hours=1)
            )
            self.signal_states[symbol] = state
        
        # Check for alerts
        alerts_triggered = []
        
        # 1. Strong signal alert
        if current_score >= self.config.strong_signal_threshold or current_score <= self.config.weak_signal_threshold:
            alerts_triggered.append(AlertType.STRONG_SIGNAL)
        
        # 2. Signal change alert
        if current_signal != state.last_signal:
            alerts_triggered.append(AlertType.SIGNAL_CHANGE)
        
        # 3. Time-based alert (every 6 hours)
        if (current_time - state.last_check).total_seconds() >= 6 * 3600:
            alerts_triggered.append(AlertType.TIME_BASED)
        
        # Send alerts if any triggered
        if alerts_triggered:
            await self._send_alerts(symbol, signal_data, state, alerts_triggered)
        
        # Update state
        state.last_signal = current_signal
        state.last_score = current_score
        state.last_check = current_time
        
        logger.info(f"Checked {symbol}: {current_signal} ({current_score:.1f})")
    
    async def _send_alerts(self, symbol: str, signal_data: Dict, state: SignalState, alert_types: List[AlertType]):
        """Send alerts for triggered conditions"""
        # Check rate limiting
        if not self._should_send_alert(state):
            logger.info(f"Rate limited: {symbol}")
            return
        
        # Format alert message
        message = self._format_alert_message(symbol, signal_data, state, alert_types)
        
        # Send to Telegram
        if self.config.enable_telegram:
            try:
                await self.telegram.send_signal_alert(signal_data, message)
                logger.info(f"Telegram alert sent for {symbol}")
            except Exception as e:
                logger.error(f"Failed to send Telegram alert for {symbol}: {e}")
        
        # Update alert tracking
        state.alert_count += 1
        state.last_alert_time = datetime.now()
        
        # Cache alert
        if self.config.enable_cache:
            await self._cache_alert(symbol, signal_data, alert_types)
    
    def _should_send_alert(self, state: SignalState) -> bool:
        """Check if alert should be sent (rate limiting)"""
        if not state.last_alert_time:
            return True
        
        # Check if more than max_alerts_per_hour have been sent
        time_since_last = datetime.now() - state.last_alert_time
        if time_since_last.total_seconds() < 3600:  # Within last hour
            if state.alert_count >= self.config.max_alerts_per_hour:
                return False
        
        return True
    
    def _format_alert_message(self, symbol: str, signal_data: Dict, state: SignalState, alert_types: List[AlertType]) -> str:
        """Format alert message based on alert types"""
        signal = signal_data.get('signal', 'NEUTRAL')
        score = signal_data.get('score', 50.0)
        confidence = signal_data.get('confidence', 'medium')
        price = signal_data.get('price', 0.0)
        reasons = signal_data.get('reasons', [])
        
        # Determine alert type emoji
        alert_emojis = []
        for alert_type in alert_types:
            if alert_type == AlertType.STRONG_SIGNAL:
                alert_emojis.append("🚨" if score >= self.config.strong_signal_threshold else "⚠️")
            elif alert_type == AlertType.SIGNAL_CHANGE:
                alert_emojis.append("🔄")
            elif alert_type == AlertType.TIME_BASED:
                alert_emojis.append("⏰")
        
        # Signal emoji
        signal_emoji = {
            "STRONG_BUY": "🚀",
            "BUY": "🟢", 
            "NEUTRAL": "🟡",
            "SELL": "🔴",
            "STRONG_SELL": "💥"
        }.get(signal, "📊")
        
        # Format message
        message_parts = [
            f"{' '.join(alert_emojis)} CRYPTOSATX MONITORING ALERT {' '.join(alert_emojis)}",
            "",
            f"📊 Symbol: {symbol}",
            f"{signal_emoji} Signal: {signal}",
            f"📈 Score: {score:.1f}",
            f"🔒 Confidence: {confidence.upper()}",
        ]
        
        if price > 0:
            message_parts.append(f"💰 Price: ${price:,.2f}")
        
        if reasons:
            message_parts.append("")
            message_parts.append("📊 Analysis:")
            for reason in reasons[:3]:  # Limit to top 3 reasons
                message_parts.append(f"• {reason}")
        
        # Add alert context
        if AlertType.SIGNAL_CHANGE in alert_types:
            message_parts.append("")
            message_parts.append(f"🔄 Signal changed from {state.last_signal} to {signal}")
        
        if AlertType.STRONG_SIGNAL in alert_types:
            if score >= self.config.strong_signal_threshold:
                message_parts.append("")
                message_parts.append("🚨 STRONG BUY SIGNAL DETECTED!")
            else:
                message_parts.append("")
                message_parts.append("⚠️ STRONG SELL SIGNAL DETECTED!")
        
        message_parts.extend([
            "",
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "🔗 Powered by CryptoSatX AI"
        ])
        
        return "\n".join(message_parts)
    
    async def _cache_alert(self, symbol: str, signal_data: Dict, alert_types: List[AlertType]):
        """Cache alert for history"""
        try:
            cache_key = f"monitoring_alert:{symbol}:{datetime.now().isoformat()}"
            alert_data = {
                'symbol': symbol,
                'signal_data': signal_data,
                'alert_types': [at.value for at in alert_types],
                'timestamp': datetime.now().isoformat()
            }
            await self.cache.set(cache_key, alert_data, expire=24*3600)  # 24 hours
        except Exception as e:
            logger.error(f"Failed to cache alert for {symbol}: {e}")
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'running': self.running,
            'symbols': self.config.symbols,
            'check_interval_minutes': self.config.check_interval_minutes,
            'strong_signal_threshold': self.config.strong_signal_threshold,
            'weak_signal_threshold': self.config.weak_signal_threshold,
            'signal_states': {
                symbol: {
                    'last_signal': state.last_signal,
                    'last_score': state.last_score,
                    'last_check': state.last_check.isoformat(),
                    'alert_count': state.alert_count,
                    'last_alert_time': state.last_alert_time.isoformat() if state.last_alert_time else None
                }
                for symbol, state in self.signal_states.items()
            }
        }
    
    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts from cache"""
        try:
            # Get all alert keys
            pattern = "monitoring_alert:*"
            keys = await self.cache.get_keys(pattern)
            
            # Get alert data
            alerts = []
            for key in keys[:limit]:
                alert_data = await self.cache.get(key)
                if alert_data:
                    alerts.append(alert_data)
            
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    async def add_symbol(self, symbol: str):
        """Add a new symbol to monitoring"""
        if symbol not in self.config.symbols:
            self.config.symbols.append(symbol)
            self.signal_states[symbol] = SignalState(
                symbol=symbol,
                last_signal="NEUTRAL",
                last_score=50.0,
                last_check=datetime.now() - timedelta(hours=1)
            )
            logger.info(f"Added {symbol} to monitoring")
    
    async def remove_symbol(self, symbol: str):
        """Remove a symbol from monitoring"""
        if symbol in self.config.symbols:
            self.config.symbols.remove(symbol)
            if symbol in self.signal_states:
                del self.signal_states[symbol]
            logger.info(f"Removed {symbol} from monitoring")
    
    async def update_config(self, **kwargs):
        """Update monitoring configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated {key} to {value}")

# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None

async def get_monitoring_service() -> MonitoringService:
    """Get or create monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        # Default configuration - Multiple coins untuk comprehensive monitoring
        config = MonitoringConfig(
            symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT", "MATICUSDT", "DOTUSDT"],
            check_interval_minutes=60,
            strong_signal_threshold=80.0,
            weak_signal_threshold=20.0,
            enable_telegram=True,
            enable_cache=True,
            max_alerts_per_hour=10
        )
        _monitoring_service = MonitoringService(config)
    return _monitoring_service

async def start_monitoring():
    """Start the global monitoring service"""
    service = await get_monitoring_service()
    await service.start_monitoring()

async def stop_monitoring():
    """Stop the global monitoring service"""
    global _monitoring_service
    if _monitoring_service:
        await _monitoring_service.stop_monitoring()

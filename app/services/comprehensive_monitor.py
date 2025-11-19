"""
CryptoSatX Comprehensive Monitoring Service
Multi-coin, multi-timeframe, multi-metric intelligent monitoring system

Features:
- Monitor unlimited coins simultaneously
- Track multiple timeframes (5m, 15m, 1H, 4H)
- Analyze multiple metrics (price, funding, OI, volume, liquidations)
- Smart alert conditions with entry/exit recommendations
- Intelligent Telegram notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json

from app.storage.database import db
from app.services.telegram_notifier import TelegramNotifier
from app.services.coinapi_comprehensive_service import CoinAPIComprehensiveService
from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService
from app.services.binance_futures_service import BinanceFuturesService

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of monitoring alerts"""
    PRICE_BREAKOUT = "price_breakout"
    PRICE_BREAKDOWN = "price_breakdown"
    VOLUME_SPIKE = "volume_spike"
    FUNDING_EXTREME = "funding_extreme"
    OI_SURGE = "oi_surge"
    LIQUIDATION_CASCADE = "liquidation_cascade"
    CONFLUENCE = "confluence"
    ENTRY_SETUP = "entry_setup"
    EXIT_SIGNAL = "exit_signal"


class RuleType(Enum):
    """Types of monitoring rules"""
    PRICE_THRESHOLD = "price_threshold"
    VOLUME_THRESHOLD = "volume_threshold"
    FUNDING_THRESHOLD = "funding_threshold"
    OI_CHANGE = "oi_change"
    TECHNICAL_PATTERN = "technical_pattern"
    CUSTOM = "custom"


@dataclass
class WatchlistCoin:
    """Represents a coin in the watchlist"""
    id: int
    symbol: str
    exchange: str = "binance"
    status: str = "active"
    priority: int = 1
    check_interval_seconds: int = 300  # 5 minutes default
    timeframes: List[str] = field(default_factory=lambda: ["5m", "15m", "1h", "4h"])
    metrics_enabled: Dict[str, bool] = field(default_factory=lambda: {
        "price": True,
        "volume": True,
        "funding": True,
        "open_interest": True,
        "liquidations": True,
        "social": False
    })
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_check_at: Optional[datetime] = None
    last_alert_at: Optional[datetime] = None
    alert_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MonitoringRule:
    """Represents a monitoring rule for a coin"""
    id: int
    watchlist_id: int
    rule_type: str
    rule_name: str
    condition: Dict[str, Any]
    timeframe: Optional[str] = None
    priority: int = 1
    enabled: bool = True
    cooldown_minutes: int = 60
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketMetrics:
    """Market metrics for a coin at a specific timeframe"""
    symbol: str
    timeframe: str
    price: float
    price_change_pct: float = 0.0
    volume: float = 0.0
    volume_change_pct: float = 0.0
    funding_rate: Optional[float] = None
    open_interest: Optional[float] = None
    oi_change_pct: float = 0.0
    liquidations_long: float = 0.0
    liquidations_short: float = 0.0
    social_volume: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertContext:
    """Context for generating intelligent alerts"""
    symbol: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    metrics: MarketMetrics
    analysis: Dict[str, Any]
    recommendations: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComprehensiveMonitor:
    """
    Comprehensive monitoring service for crypto coins

    Monitors multiple coins across multiple timeframes and metrics,
    intelligently detecting entry/exit opportunities and market conditions.
    """

    def __init__(self):
        self.running = False
        self.watchlist: Dict[str, WatchlistCoin] = {}
        self.rules: Dict[int, List[MonitoringRule]] = {}  # watchlist_id -> rules
        self.telegram = TelegramNotifier()
        self.coinapi = CoinAPIComprehensiveService()
        self.coinglass = CoinglassComprehensiveService()
        self.binance = BinanceFuturesService()
        self.monitor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # Cache for recent metrics to calculate changes
        self.metrics_cache: Dict[str, Dict[str, MarketMetrics]] = {}  # symbol -> timeframe -> metrics

        # Alert cooldown tracking
        self.alert_cooldowns: Dict[str, datetime] = {}  # "symbol:rule_id" -> last_alert_time

    async def start(self):
        """Start the comprehensive monitoring service"""
        if self.running:
            logger.warning("Comprehensive monitor already running")
            return

        logger.info("🚀 Starting Comprehensive Monitoring Service...")

        # Load watchlist from database
        await self._load_watchlist()
        await self._load_rules()

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info(f"✅ Monitoring {len(self.watchlist)} coins")

    async def stop(self):
        """Stop the monitoring service"""
        logger.info("🛑 Stopping Comprehensive Monitoring Service...")
        self.running = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("✅ Comprehensive monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Monitor all active coins
                await self._monitor_all_coins()

                # Wait before next check (use minimum interval from watchlist)
                min_interval = min(
                    (coin.check_interval_seconds for coin in self.watchlist.values()),
                    default=60
                )
                await asyncio.sleep(min_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                await asyncio.sleep(30)  # Wait before retry

    async def _monitor_all_coins(self):
        """Monitor all coins in watchlist"""
        tasks = []

        for symbol, coin in self.watchlist.items():
            # Check if it's time to monitor this coin
            if self._should_check_coin(coin):
                tasks.append(self._monitor_coin(coin))

        if tasks:
            # Monitor all coins concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

    def _should_check_coin(self, coin: WatchlistCoin) -> bool:
        """Check if coin should be monitored now"""
        if coin.status != "active":
            return False

        if not coin.last_check_at:
            return True

        elapsed = (datetime.now() - coin.last_check_at).total_seconds()
        return elapsed >= coin.check_interval_seconds

    async def _monitor_coin(self, coin: WatchlistCoin):
        """Monitor a single coin across all timeframes and metrics"""
        try:
            logger.info(f"📊 Monitoring {coin.symbol}...")

            # Collect metrics for all timeframes
            metrics_by_timeframe: Dict[str, MarketMetrics] = {}

            for timeframe in coin.timeframes:
                metrics = await self._collect_metrics(coin, timeframe)
                if metrics:
                    metrics_by_timeframe[timeframe] = metrics

                    # Store in database
                    await self._save_metrics(coin.id, metrics)

            # Update cache
            self.metrics_cache[coin.symbol] = metrics_by_timeframe

            # Evaluate rules and generate alerts
            await self._evaluate_rules(coin, metrics_by_timeframe)

            # Update last check time
            await self._update_last_check(coin.id)

        except Exception as e:
            logger.error(f"Error monitoring {coin.symbol}: {e}", exc_info=True)

    async def _collect_metrics(self, coin: WatchlistCoin, timeframe: str) -> Optional[MarketMetrics]:
        """Collect all metrics for a coin at a specific timeframe"""
        try:
            metrics = MarketMetrics(
                symbol=coin.symbol,
                timeframe=timeframe,
                price=0.0
            )

            # Get current price (always enabled)
            try:
                price_data = await self.coinapi.get_current_price(coin.symbol)
                if price_data:
                    metrics.price = float(price_data.get('price', 0))
            except Exception as e:
                logger.warning(f"Failed to get price for {coin.symbol}: {e}")
                return None

            # Get volume data
            if coin.metrics_enabled.get('volume', True):
                try:
                    volume_data = await self.binance.get_24h_ticker(coin.symbol)
                    if volume_data:
                        metrics.volume = float(volume_data.get('quoteVolume', 0))

                        # Calculate volume change
                        cached = self._get_cached_metrics(coin.symbol, timeframe)
                        if cached and cached.volume > 0:
                            metrics.volume_change_pct = ((metrics.volume - cached.volume) / cached.volume) * 100
                except Exception as e:
                    logger.debug(f"Failed to get volume for {coin.symbol}: {e}")

            # Get funding rate
            if coin.metrics_enabled.get('funding', True):
                try:
                    funding_data = await self.coinglass.get_funding_rate(coin.symbol)
                    if funding_data:
                        metrics.funding_rate = float(funding_data.get('rate', 0))
                except Exception as e:
                    logger.debug(f"Failed to get funding for {coin.symbol}: {e}")

            # Get open interest
            if coin.metrics_enabled.get('open_interest', True):
                try:
                    oi_data = await self.coinglass.get_open_interest(coin.symbol)
                    if oi_data:
                        metrics.open_interest = float(oi_data.get('openInterest', 0))

                        # Calculate OI change
                        cached = self._get_cached_metrics(coin.symbol, timeframe)
                        if cached and cached.open_interest and cached.open_interest > 0:
                            metrics.oi_change_pct = ((metrics.open_interest - cached.open_interest) / cached.open_interest) * 100
                except Exception as e:
                    logger.debug(f"Failed to get OI for {coin.symbol}: {e}")

            # Get liquidations
            if coin.metrics_enabled.get('liquidations', True):
                try:
                    liq_data = await self.coinglass.get_liquidations(coin.symbol, timeframe)
                    if liq_data:
                        metrics.liquidations_long = float(liq_data.get('longLiquidation', 0))
                        metrics.liquidations_short = float(liq_data.get('shortLiquidation', 0))
                except Exception as e:
                    logger.debug(f"Failed to get liquidations for {coin.symbol}: {e}")

            # Calculate price change
            cached = self._get_cached_metrics(coin.symbol, timeframe)
            if cached and cached.price > 0:
                metrics.price_change_pct = ((metrics.price - cached.price) / cached.price) * 100

            metrics.timestamp = datetime.now()
            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics for {coin.symbol} {timeframe}: {e}", exc_info=True)
            return None

    def _get_cached_metrics(self, symbol: str, timeframe: str) -> Optional[MarketMetrics]:
        """Get cached metrics for comparison"""
        return self.metrics_cache.get(symbol, {}).get(timeframe)

    async def _evaluate_rules(self, coin: WatchlistCoin, metrics_by_timeframe: Dict[str, MarketMetrics]):
        """Evaluate monitoring rules and generate alerts"""
        rules = self.rules.get(coin.id, [])

        if not rules:
            # Use default smart detection if no custom rules
            await self._smart_detection(coin, metrics_by_timeframe)
            return

        for rule in rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if not self._check_cooldown(coin.symbol, rule.id, rule.cooldown_minutes):
                continue

            # Evaluate rule
            triggered = await self._evaluate_rule(rule, metrics_by_timeframe)

            if triggered:
                # Generate and send alert
                await self._generate_alert(coin, rule, metrics_by_timeframe, triggered)

                # Update cooldown
                self._set_cooldown(coin.symbol, rule.id)

                # Update rule trigger stats
                await self._update_rule_trigger(rule.id)

    async def _smart_detection(self, coin: WatchlistCoin, metrics_by_timeframe: Dict[str, MarketMetrics]):
        """Smart detection of trading opportunities without explicit rules"""
        alerts_to_send = []

        # Get 1H metrics as primary timeframe
        metrics_1h = metrics_by_timeframe.get("1h")
        if not metrics_1h:
            return

        # Detection 1: Volume Spike
        if metrics_1h.volume_change_pct > 200:
            context = AlertContext(
                symbol=coin.symbol,
                alert_type=AlertType.VOLUME_SPIKE,
                severity=AlertSeverity.HIGH,
                title=f"Volume Spike Detected",
                message=f"Volume increased {metrics_1h.volume_change_pct:.1f}% in last hour",
                metrics=metrics_1h,
                analysis={
                    "volume_change": metrics_1h.volume_change_pct,
                    "signal": "Strong momentum detected"
                },
                recommendations={
                    "action": "Monitor for breakout",
                    "caution": "High volume can indicate reversal"
                }
            )
            alerts_to_send.append(context)

        # Detection 2: Price Breakout (>3% move)
        if abs(metrics_1h.price_change_pct) > 3:
            alert_type = AlertType.PRICE_BREAKOUT if metrics_1h.price_change_pct > 0 else AlertType.PRICE_BREAKDOWN
            severity = AlertSeverity.HIGH if abs(metrics_1h.price_change_pct) > 5 else AlertSeverity.MEDIUM

            context = AlertContext(
                symbol=coin.symbol,
                alert_type=alert_type,
                severity=severity,
                title=f"Price {'Breakout' if metrics_1h.price_change_pct > 0 else 'Breakdown'}",
                message=f"Price moved {metrics_1h.price_change_pct:+.2f}% to ${metrics_1h.price:.6f}",
                metrics=metrics_1h,
                analysis={
                    "price_change": metrics_1h.price_change_pct,
                    "direction": "bullish" if metrics_1h.price_change_pct > 0 else "bearish"
                },
                recommendations={}
            )
            alerts_to_send.append(context)

        # Detection 3: Extreme Funding Rate
        if metrics_1h.funding_rate and abs(metrics_1h.funding_rate) > 0.1:
            context = AlertContext(
                symbol=coin.symbol,
                alert_type=AlertType.FUNDING_EXTREME,
                severity=AlertSeverity.MEDIUM,
                title="Extreme Funding Rate",
                message=f"Funding rate at {metrics_1h.funding_rate:.4f}%",
                metrics=metrics_1h,
                analysis={
                    "funding_rate": metrics_1h.funding_rate,
                    "signal": "High funding = potential short squeeze" if metrics_1h.funding_rate > 0 else "Negative funding = potential long squeeze"
                },
                recommendations={
                    "caution": "Extreme funding can reverse quickly"
                }
            )
            alerts_to_send.append(context)

        # Detection 4: OI Surge
        if metrics_1h.oi_change_pct > 15:
            context = AlertContext(
                symbol=coin.symbol,
                alert_type=AlertType.OI_SURGE,
                severity=AlertSeverity.MEDIUM,
                title="Open Interest Surge",
                message=f"OI increased {metrics_1h.oi_change_pct:.1f}%",
                metrics=metrics_1h,
                analysis={
                    "oi_change": metrics_1h.oi_change_pct,
                    "signal": "Whale accumulation or distribution"
                },
                recommendations={}
            )
            alerts_to_send.append(context)

        # Send all detected alerts
        for context in alerts_to_send:
            # Check cooldown for smart detection
            cooldown_key = f"{coin.symbol}:smart_{context.alert_type.value}"
            if cooldown_key in self.alert_cooldowns:
                last_alert = self.alert_cooldowns[cooldown_key]
                if (datetime.now() - last_alert).total_seconds() < 3600:  # 1 hour cooldown
                    continue

            await self._send_alert(coin, None, context)
            self.alert_cooldowns[cooldown_key] = datetime.now()

    async def _evaluate_rule(self, rule: MonitoringRule, metrics_by_timeframe: Dict[str, MarketMetrics]) -> Optional[Dict[str, Any]]:
        """Evaluate a specific rule"""
        # Get metrics for rule's timeframe
        timeframe = rule.timeframe or "1h"
        metrics = metrics_by_timeframe.get(timeframe)

        if not metrics:
            return None

        condition = rule.condition
        rule_type = rule.rule_type

        try:
            if rule_type == RuleType.PRICE_THRESHOLD.value:
                target_price = float(condition.get('price', 0))
                operator = condition.get('operator', 'above')  # above, below, equal

                if operator == 'above' and metrics.price >= target_price:
                    return {"triggered_price": metrics.price, "target_price": target_price}
                elif operator == 'below' and metrics.price <= target_price:
                    return {"triggered_price": metrics.price, "target_price": target_price}

            elif rule_type == RuleType.VOLUME_THRESHOLD.value:
                threshold = float(condition.get('threshold_pct', 100))
                if metrics.volume_change_pct >= threshold:
                    return {"volume_change": metrics.volume_change_pct, "threshold": threshold}

            elif rule_type == RuleType.FUNDING_THRESHOLD.value:
                threshold = float(condition.get('threshold', 0.1))
                if metrics.funding_rate and abs(metrics.funding_rate) >= threshold:
                    return {"funding_rate": metrics.funding_rate, "threshold": threshold}

            elif rule_type == RuleType.OI_CHANGE.value:
                threshold = float(condition.get('threshold_pct', 10))
                if metrics.oi_change_pct >= threshold:
                    return {"oi_change": metrics.oi_change_pct, "threshold": threshold}

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")

        return None

    def _check_cooldown(self, symbol: str, rule_id: int, cooldown_minutes: int) -> bool:
        """Check if alert is off cooldown"""
        key = f"{symbol}:{rule_id}"
        if key not in self.alert_cooldowns:
            return True

        last_alert = self.alert_cooldowns[key]
        elapsed = (datetime.now() - last_alert).total_seconds() / 60
        return elapsed >= cooldown_minutes

    def _set_cooldown(self, symbol: str, rule_id: int):
        """Set alert cooldown"""
        key = f"{symbol}:{rule_id}"
        self.alert_cooldowns[key] = datetime.now()

    async def _generate_alert(self, coin: WatchlistCoin, rule: MonitoringRule,
                            metrics_by_timeframe: Dict[str, MarketMetrics],
                            trigger_data: Dict[str, Any]):
        """Generate alert from triggered rule"""
        timeframe = rule.timeframe or "1h"
        metrics = metrics_by_timeframe.get(timeframe)

        if not metrics:
            return

        # Create alert context
        context = AlertContext(
            symbol=coin.symbol,
            alert_type=AlertType.ENTRY_SETUP,  # Default, can be customized
            severity=AlertSeverity.MEDIUM,
            title=rule.rule_name,
            message=f"Rule triggered: {rule.rule_name}",
            metrics=metrics,
            analysis=trigger_data,
            recommendations={},
            metadata={"rule_id": rule.id}
        )

        await self._send_alert(coin, rule, context)

    async def _send_alert(self, coin: WatchlistCoin, rule: Optional[MonitoringRule], context: AlertContext):
        """Send alert to Telegram and save to database"""
        try:
            # Format intelligent Telegram message
            message = self._format_telegram_alert(context)

            # Send to Telegram
            telegram_result = None
            if self.telegram.enabled:
                try:
                    signal_data = {
                        "symbol": context.symbol,
                        "signal": "ALERT",
                        "score": 0,
                        "confidence": "high",
                        "price": context.metrics.price,
                        "reasons": [context.message],
                        "timestamp": datetime.now().isoformat()
                    }
                    telegram_result = await self.telegram.send_custom_alert(
                        title=context.title,
                        message=message,
                        emoji="🔔"
                    )
                    logger.info(f"📤 Alert sent to Telegram for {context.symbol}")
                except Exception as e:
                    logger.error(f"Failed to send Telegram alert: {e}")

            # Save to database
            await self._save_alert(coin.id, rule.id if rule else None, context, telegram_result)

        except Exception as e:
            logger.error(f"Error sending alert for {coin.symbol}: {e}", exc_info=True)

    def _format_telegram_alert(self, context: AlertContext) -> str:
        """Format comprehensive Telegram alert message"""
        lines = []

        # Symbol and price
        lines.append(f"📊 {context.symbol}")
        lines.append(f"💵 ${context.metrics.price:.6f}")

        # Price change
        if context.metrics.price_change_pct != 0:
            emoji = "📈" if context.metrics.price_change_pct > 0 else "📉"
            lines.append(f"{emoji} {context.metrics.price_change_pct:+.2f}% ({context.metrics.timeframe})")

        lines.append("")

        # Main message
        lines.append(context.message)

        # Metrics
        if context.metrics.volume > 0:
            lines.append(f"📊 Volume: ${context.metrics.volume:,.0f}")
            if context.metrics.volume_change_pct != 0:
                lines.append(f"   Change: {context.metrics.volume_change_pct:+.1f}%")

        if context.metrics.funding_rate is not None:
            lines.append(f"💰 Funding: {context.metrics.funding_rate:.4f}%")

        if context.metrics.open_interest:
            lines.append(f"📈 OI: ${context.metrics.open_interest:,.0f}")
            if context.metrics.oi_change_pct != 0:
                lines.append(f"   Change: {context.metrics.oi_change_pct:+.1f}%")

        if context.metrics.liquidations_long + context.metrics.liquidations_short > 0:
            lines.append(f"⚡ Liquidations:")
            if context.metrics.liquidations_long > 0:
                lines.append(f"   Longs: ${context.metrics.liquidations_long:,.0f}")
            if context.metrics.liquidations_short > 0:
                lines.append(f"   Shorts: ${context.metrics.liquidations_short:,.0f}")

        # Analysis
        if context.analysis:
            lines.append("")
            lines.append("🔍 Analysis:")
            for key, value in context.analysis.items():
                if isinstance(value, (int, float)):
                    lines.append(f"   {key}: {value:.2f}")
                else:
                    lines.append(f"   {value}")

        # Recommendations
        if context.recommendations:
            lines.append("")
            lines.append("💡 Recommendations:")
            for key, value in context.recommendations.items():
                lines.append(f"   {value}")

        lines.append("")
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)

    # Database operations
    async def _load_watchlist(self):
        """Load watchlist from database"""
        try:
            query = "SELECT * FROM coin_watchlist WHERE status = 'active' ORDER BY priority DESC"
            async with db.acquire() as conn:
                rows = await conn.fetch(query)

            for row in rows:
                coin = WatchlistCoin(
                    id=row['id'],
                    symbol=row['symbol'],
                    exchange=row['exchange'] or 'binance',
                    status=row['status'],
                    priority=row['priority'] or 1,
                    check_interval_seconds=row['check_interval_seconds'],
                    timeframes=row['timeframes'] or ["1h"],
                    metrics_enabled=row['metrics_enabled'] or {},
                    metadata=row['metadata'] or {},
                    last_check_at=row['last_check_at'],
                    last_alert_at=row['last_alert_at'],
                    alert_count=row['alert_count'] or 0,
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                self.watchlist[coin.symbol] = coin

            logger.info(f"📋 Loaded {len(self.watchlist)} coins from watchlist")

        except Exception as e:
            logger.error(f"Error loading watchlist: {e}", exc_info=True)

    async def _load_rules(self):
        """Load monitoring rules from database"""
        try:
            query = "SELECT * FROM monitoring_rules WHERE enabled = true ORDER BY priority DESC"
            async with db.acquire() as conn:
                rows = await conn.fetch(query)

            for row in rows:
                rule = MonitoringRule(
                    id=row['id'],
                    watchlist_id=row['watchlist_id'],
                    rule_type=row['rule_type'],
                    rule_name=row['rule_name'],
                    condition=row['condition'],
                    timeframe=row['timeframe'],
                    priority=row['priority'] or 1,
                    enabled=row['enabled'],
                    cooldown_minutes=row['cooldown_minutes'] or 60,
                    last_triggered_at=row['last_triggered_at'],
                    trigger_count=row['trigger_count'] or 0,
                    metadata=row['metadata'] or {}
                )

                if rule.watchlist_id not in self.rules:
                    self.rules[rule.watchlist_id] = []
                self.rules[rule.watchlist_id].append(rule)

            logger.info(f"📋 Loaded {len(rows)} monitoring rules")

        except Exception as e:
            logger.error(f"Error loading rules: {e}", exc_info=True)

    async def _save_metrics(self, watchlist_id: int, metrics: MarketMetrics):
        """Save metrics to database"""
        try:
            query = """
                INSERT INTO monitoring_metrics
                (watchlist_id, symbol, timeframe, price, volume, funding_rate, open_interest,
                 liquidations_long, liquidations_short, social_volume, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
            """
            async with db.acquire() as conn:
                await conn.execute(
                    query,
                    watchlist_id, metrics.symbol, metrics.timeframe, metrics.price,
                    metrics.volume, metrics.funding_rate, metrics.open_interest,
                    metrics.liquidations_long, metrics.liquidations_short,
                    metrics.social_volume, metrics.timestamp
                )
        except Exception as e:
            logger.debug(f"Error saving metrics: {e}")

    async def _save_alert(self, watchlist_id: int, rule_id: Optional[int],
                         context: AlertContext, telegram_result: Any):
        """Save alert to database"""
        try:
            query = """
                INSERT INTO monitoring_alerts
                (watchlist_id, rule_id, symbol, alert_type, severity, title, message,
                 price, timeframe, metrics, analysis, recommendations, telegram_sent, telegram_sent_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id
            """

            telegram_sent = telegram_result is not None
            telegram_sent_at = datetime.now() if telegram_sent else None

            async with db.acquire() as conn:
                await conn.execute(
                    query,
                    watchlist_id, rule_id, context.symbol, context.alert_type.value,
                    context.severity.value, context.title, context.message,
                    context.metrics.price, context.metrics.timeframe,
                    json.dumps(context.metrics.__dict__, default=str),
                    json.dumps(context.analysis),
                    json.dumps(context.recommendations),
                    telegram_sent, telegram_sent_at
                )

                # Update alert count
                await conn.execute(
                    "UPDATE coin_watchlist SET alert_count = alert_count + 1, last_alert_at = $1 WHERE id = $2",
                    datetime.now(), watchlist_id
                )

        except Exception as e:
            logger.error(f"Error saving alert: {e}", exc_info=True)

    async def _update_last_check(self, watchlist_id: int):
        """Update last check timestamp"""
        try:
            async with db.acquire() as conn:
                await conn.execute(
                    "UPDATE coin_watchlist SET last_check_at = $1 WHERE id = $2",
                    datetime.now(), watchlist_id
                )
        except Exception as e:
            logger.debug(f"Error updating last check: {e}")

    async def _update_rule_trigger(self, rule_id: int):
        """Update rule trigger stats"""
        try:
            async with db.acquire() as conn:
                await conn.execute(
                    "UPDATE monitoring_rules SET trigger_count = trigger_count + 1, last_triggered_at = $1 WHERE id = $2",
                    datetime.now(), rule_id
                )
        except Exception as e:
            logger.debug(f"Error updating rule trigger: {e}")

    # Public API methods
    async def add_coin(self, symbol: str, **kwargs) -> WatchlistCoin:
        """Add a coin to watchlist"""
        async with self._lock:
            # Check if already exists
            async with db.acquire() as conn:
                existing = await conn.fetchrow(
                    "SELECT id FROM coin_watchlist WHERE symbol = $1",
                    symbol
                )

            if existing:
                raise ValueError(f"Coin {symbol} already in watchlist")

            # Insert into database
            query = """
                INSERT INTO coin_watchlist
                (symbol, exchange, status, priority, check_interval_seconds, timeframes, metrics_enabled)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """

            async with db.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    symbol,
                    kwargs.get('exchange', 'binance'),
                    'active',
                    kwargs.get('priority', 1),
                    kwargs.get('check_interval_seconds', 300),
                    kwargs.get('timeframes', ["5m", "15m", "1h", "4h"]),
                    kwargs.get('metrics_enabled', {"price": True, "volume": True, "funding": True, "open_interest": True, "liquidations": True})
                )

            # Create coin object
            coin = WatchlistCoin(
                id=row['id'],
                symbol=row['symbol'],
                exchange=row['exchange'],
                status=row['status'],
                priority=row['priority'],
                check_interval_seconds=row['check_interval_seconds'],
                timeframes=row['timeframes'],
                metrics_enabled=row['metrics_enabled'] or {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

            # Add to watchlist
            self.watchlist[symbol] = coin

            logger.info(f"✅ Added {symbol} to watchlist")
            return coin

    async def remove_coin(self, symbol: str):
        """Remove a coin from watchlist"""
        async with self._lock:
            coin = self.watchlist.get(symbol)
            if not coin:
                raise ValueError(f"Coin {symbol} not in watchlist")

            # Delete from database (cascade will delete rules and alerts)
            async with db.acquire() as conn:
                await conn.execute(
                    "DELETE FROM coin_watchlist WHERE symbol = $1",
                    symbol
                )

            # Remove from watchlist
            del self.watchlist[symbol]
            if coin.id in self.rules:
                del self.rules[coin.id]

            logger.info(f"🗑️ Removed {symbol} from watchlist")

    async def get_status(self) -> Dict[str, Any]:
        """Get monitoring status"""
        return {
            "running": self.running,
            "coins_monitored": len(self.watchlist),
            "total_rules": sum(len(rules) for rules in self.rules.values()),
            "telegram_enabled": self.telegram.enabled,
            "watchlist": [
                {
                    "symbol": coin.symbol,
                    "status": coin.status,
                    "priority": coin.priority,
                    "last_check": coin.last_check_at.isoformat() if coin.last_check_at else None,
                    "last_alert": coin.last_alert_at.isoformat() if coin.last_alert_at else None,
                    "alert_count": coin.alert_count
                }
                for coin in self.watchlist.values()
            ]
        }


# Global instance
_comprehensive_monitor: Optional[ComprehensiveMonitor] = None

def get_comprehensive_monitor() -> ComprehensiveMonitor:
    """Get or create global comprehensive monitor instance"""
    global _comprehensive_monitor
    if _comprehensive_monitor is None:
        _comprehensive_monitor = ComprehensiveMonitor()
    return _comprehensive_monitor

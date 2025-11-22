"""
Pre-Pump Scanner Service
Automated background scanner for detecting pre-pump opportunities

Features:
- Periodic scanning of watchlist coins
- Configurable scan intervals
- Alert generation for strong signals
- Integration with Telegram notifications

Author: CryptoSat Intelligence Pre-Pump Detection Engine
"""
import asyncio
from typing import List, Optional, Dict
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.pre_pump_engine import PrePumpEngine
from app.services.telegram_notifier import TelegramNotifier
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PrePumpScanner:
    """Automated scanner for pre-pump detection with alerting"""

    def __init__(
        self,
        watchlist: Optional[List[str]] = None,
        scan_interval_minutes: int = 30,
        min_score: float = 70.0,
        min_confidence: float = 60.0,
        enable_alerts: bool = True
    ):
        """
        Initialize Pre-Pump Scanner

        Args:
            watchlist: List of symbols to monitor (default: top 30 coins)
            scan_interval_minutes: Minutes between scans (default: 30)
            min_score: Minimum score to trigger alert (default: 70)
            min_confidence: Minimum confidence to trigger alert (default: 60)
            enable_alerts: Enable Telegram notifications (default: True)
        """
        self.watchlist = watchlist or self._get_default_watchlist()
        self.scan_interval = scan_interval_minutes
        self.min_score = min_score
        self.min_confidence = min_confidence
        self.enable_alerts = enable_alerts

        self.engine = PrePumpEngine()
        self.notifier = TelegramNotifier() if enable_alerts else None
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

        # Track sent alerts to avoid spam
        self.alert_cooldown: Dict[str, datetime] = {}
        self.cooldown_hours = 4  # Don't alert same coin twice within 4 hours

    def _get_default_watchlist(self) -> List[str]:
        """Get default watchlist of popular coins"""
        return [
            # Top 10 by market cap
            "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOT", "MATIC", "LINK",
            # DeFi tokens
            "UNI", "AAVE", "CRV", "SNX", "COMP", "MKR", "SUSHI",
            # Layer 1/2
            "ATOM", "NEAR", "FTM", "ALGO", "ONE", "HBAR",
            # Gaming/Metaverse
            "SAND", "MANA", "AXS", "GALA", "ENJ",
            # Others
            "LTC", "BCH", "XLM", "VET"
        ]

    async def start(self):
        """Start the automated scanner"""
        if self.is_running:
            logger.warning("[PrePumpScanner] Scanner already running")
            return

        logger.info("=" * 80)
        logger.info("🚀 PRE-PUMP SCANNER STARTING")
        logger.info("=" * 80)
        logger.info(f"  - Watchlist: {len(self.watchlist)} coins")
        logger.info(f"  - Scan Interval: Every {self.scan_interval} minutes")
        logger.info(f"  - Min Score: {self.min_score}/100")
        logger.info(f"  - Min Confidence: {self.min_confidence}%")
        logger.info(f"  - Alerts: {'ENABLED' if self.enable_alerts else 'DISABLED'}")
        logger.info("=" * 80)

        # Schedule periodic scans
        self.scheduler.add_job(
            self.scan,
            trigger=IntervalTrigger(minutes=self.scan_interval),
            id="pre_pump_scan",
            replace_existing=True,
            max_instances=1
        )

        self.scheduler.start()
        self.is_running = True

        # Run first scan immediately
        logger.info("[PrePumpScanner] Running initial scan...")
        await self.scan()

        logger.info("[PrePumpScanner] Scanner started successfully")

    async def stop(self):
        """Stop the scanner"""
        if not self.is_running:
            return

        logger.info("[PrePumpScanner] Stopping scanner...")
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        await self.engine.close()
        logger.info("[PrePumpScanner] Scanner stopped")

    async def scan(self):
        """Perform a scan of the watchlist"""
        try:
            logger.info(f"[PrePumpScanner] Starting scan of {len(self.watchlist)} coins...")
            scan_start = datetime.utcnow()

            # Scan all watchlist coins
            results = await self.engine.scan_market(
                symbols=self.watchlist,
                timeframe="1HRS",
                min_score=self.min_score
            )

            if not results.get("success"):
                logger.error(f"[PrePumpScanner] Scan failed: {results.get('error')}")
                return

            # Filter for strong signals above confidence threshold
            strong_signals = [
                r for r in results.get("allResults", [])
                if r.get("score", 0) >= self.min_score
                and r.get("confidence", 0) >= self.min_confidence
            ]

            scan_duration = (datetime.utcnow() - scan_start).total_seconds()

            logger.info(
                f"[PrePumpScanner] Scan complete in {scan_duration:.1f}s - "
                f"Found {len(strong_signals)} strong signals"
            )

            # Send alerts for new signals
            if strong_signals and self.enable_alerts:
                await self._send_alerts(strong_signals)

            # Log summary
            self._log_scan_summary(results, strong_signals)

        except Exception as e:
            logger.error(f"[PrePumpScanner] Scan error: {e}", exc_info=True)

    async def _send_alerts(self, signals: List[Dict]):
        """Send Telegram alerts for strong signals"""
        if not self.notifier:
            return

        current_time = datetime.utcnow()

        for signal in signals:
            symbol = signal.get("symbol")

            # Check cooldown
            last_alert = self.alert_cooldown.get(symbol)
            if last_alert:
                hours_since = (current_time - last_alert).total_seconds() / 3600
                if hours_since < self.cooldown_hours:
                    logger.debug(
                        f"[PrePumpScanner] Skipping alert for {symbol} "
                        f"(cooldown: {hours_since:.1f}h / {self.cooldown_hours}h)"
                    )
                    continue

            # Send alert
            await self._send_signal_alert(signal)
            self.alert_cooldown[symbol] = current_time

    async def _send_signal_alert(self, signal: Dict):
        """Format and send a single signal alert"""
        try:
            symbol = signal.get("symbol")
            score = signal.get("score", 0)
            confidence = signal.get("confidence", 0)
            verdict = signal.get("verdict", "UNKNOWN")
            recommendation = signal.get("recommendation", {})

            components = signal.get("components", {})
            accumulation = components.get("accumulation", {})
            reversal = components.get("reversal", {})
            whale = components.get("whale", {})

            # Format alert message
            message = f"""
🚀 **PRE-PUMP ALERT: {symbol}**

**Score:** {score}/100
**Confidence:** {confidence}%
**Verdict:** {verdict}

**Recommendation:**
• Action: {recommendation.get('action', 'N/A')}
• Risk: {recommendation.get('risk', 'N/A')}
• Entry: {recommendation.get('suggestedEntry', 'N/A')}
• Stop Loss: {recommendation.get('stopLoss', 'N/A')}
• Take Profit: {recommendation.get('takeProfit', 'N/A')}

**Signal Breakdown:**
✓ Accumulation: {accumulation.get('verdict', 'N/A')} ({accumulation.get('score', 0)}/100)
✓ Reversal: {reversal.get('verdict', 'N/A')} ({reversal.get('score', 0)}/100)
✓ Whale: {whale.get('verdict', 'N/A')} ({whale.get('score', 0)}/100)

**Message:** {recommendation.get('message', '')}

---
*CryptoSat Pre-Pump Detection Engine*
*{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""

            await self.notifier.send_message(message, parse_mode="Markdown")
            logger.info(f"[PrePumpScanner] Alert sent for {symbol}")

        except Exception as e:
            logger.error(f"[PrePumpScanner] Error sending alert: {e}")

    def _log_scan_summary(self, results: Dict, strong_signals: List[Dict]):
        """Log scan summary"""
        summary = results.get("summary", {})

        logger.info("=" * 80)
        logger.info("📊 PRE-PUMP SCAN SUMMARY")
        logger.info("=" * 80)
        logger.info(f"  Total Scanned: {results.get('totalScanned', 0)} coins")
        logger.info(f"  Total Found: {results.get('totalFound', 0)} opportunities")
        logger.info(f"  Very Strong: {summary.get('veryStrong', 0)}")
        logger.info(f"  Strong: {summary.get('strong', 0)}")
        logger.info(f"  Moderate: {summary.get('moderate', 0)}")
        logger.info(f"  Alerts Sent: {len(strong_signals)} new signals")
        logger.info("=" * 80)

        if strong_signals:
            logger.info("🎯 TOP OPPORTUNITIES:")
            for i, signal in enumerate(strong_signals[:5], 1):
                logger.info(
                    f"  {i}. {signal.get('symbol')} - "
                    f"Score: {signal.get('score')}/100, "
                    f"Confidence: {signal.get('confidence')}%, "
                    f"Action: {signal.get('recommendation', {}).get('action')}"
                )
            logger.info("=" * 80)

    async def get_status(self) -> Dict:
        """Get scanner status"""
        return {
            "running": self.is_running,
            "watchlist": self.watchlist,
            "watchlist_size": len(self.watchlist),
            "scan_interval_minutes": self.scan_interval,
            "min_score": self.min_score,
            "min_confidence": self.min_confidence,
            "alerts_enabled": self.enable_alerts,
            "alert_cooldown_hours": self.cooldown_hours,
            "active_cooldowns": len(self.alert_cooldown)
        }

    async def update_watchlist(self, new_watchlist: List[str]):
        """Update the watchlist"""
        self.watchlist = new_watchlist
        logger.info(f"[PrePumpScanner] Watchlist updated: {len(new_watchlist)} coins")

    async def trigger_manual_scan(self) -> Dict:
        """Trigger a manual scan immediately"""
        logger.info("[PrePumpScanner] Manual scan triggered")
        await self.scan()
        return {"success": True, "message": "Manual scan completed"}


# Global scanner instance (singleton)
pre_pump_scanner: Optional[PrePumpScanner] = None


async def start_pre_pump_scanner(
    watchlist: Optional[List[str]] = None,
    scan_interval_minutes: int = 30,
    min_score: float = 70.0,
    min_confidence: float = 60.0,
    enable_alerts: bool = True
):
    """Start the global pre-pump scanner"""
    global pre_pump_scanner

    if pre_pump_scanner and pre_pump_scanner.is_running:
        logger.warning("[PrePumpScanner] Scanner already running")
        return pre_pump_scanner

    pre_pump_scanner = PrePumpScanner(
        watchlist=watchlist,
        scan_interval_minutes=scan_interval_minutes,
        min_score=min_score,
        min_confidence=min_confidence,
        enable_alerts=enable_alerts
    )

    await pre_pump_scanner.start()
    return pre_pump_scanner


async def stop_pre_pump_scanner():
    """Stop the global pre-pump scanner"""
    global pre_pump_scanner

    if pre_pump_scanner:
        await pre_pump_scanner.stop()
        pre_pump_scanner = None


def get_pre_pump_scanner() -> Optional[PrePumpScanner]:
    """Get the global scanner instance"""
    return pre_pump_scanner

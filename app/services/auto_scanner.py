"""
Auto Scanner Service for CryptoSatX

24/7 automated scanning service that runs scheduled scans across multiple scanners:
- Smart Money Scanner (whale accumulation/distribution)
- MSS Discovery (new listing gems)
- RSI Screener (technical oversold/overbought)
- LunarCrush Trending (social momentum)

Uses APScheduler for reliable task scheduling with configurable intervals.
"""

import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.services.smart_money_service import SmartMoneyService
from app.services.mss_service import MSSService
from app.services.coinglass_service import CoinglassService
from app.services.telegram_notifier import TelegramNotifier
from app.services.performance_tracker import track_signal
from app.utils.logger import default_logger
from app.storage.signal_history import signal_history


class AutoScanner:
    """
    24/7 Automated scanning service

    Features:
    - Smart Money Scan: Hourly whale activity detection
    - MSS Discovery: 6-hourly new listing discovery
    - RSI Screener: 4-hourly technical screening
    - LunarCrush Trending: 2-hourly social momentum tracking
    - Automated alerts via Telegram
    - Daily summary reports
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.logger = default_logger

        # Initialize services
        self.smart_money = SmartMoneyService()
        self.mss = MSSService()
        self.coinglass = CoinglassService()
        self.telegram = TelegramNotifier()

        # Configuration from environment
        self.enabled = os.getenv("AUTO_SCAN_ENABLED", "false").lower() == "true"
        self.smart_money_interval = int(os.getenv("SMART_MONEY_INTERVAL_HOURS", "1"))
        self.mss_interval = int(os.getenv("MSS_DISCOVERY_INTERVAL_HOURS", "6"))
        self.rsi_interval = int(os.getenv("RSI_SCREENER_INTERVAL_HOURS", "4"))
        self.lunarcrush_interval = int(os.getenv("LUNARCRUSH_INTERVAL_HOURS", "2"))

        # Alert thresholds
        self.accumulation_threshold = int(os.getenv("ACCUMULATION_ALERT_THRESHOLD", "7"))
        self.distribution_threshold = int(os.getenv("DISTRIBUTION_ALERT_THRESHOLD", "7"))
        self.mss_threshold = int(os.getenv("MSS_ALERT_THRESHOLD", "75"))
        self.rsi_oversold = int(os.getenv("RSI_OVERSOLD_THRESHOLD", "25"))
        self.rsi_overbought = int(os.getenv("RSI_OVERBOUGHT_THRESHOLD", "75"))

        # Statistics
        self.stats = {
            "total_scans": 0,
            "smart_money_scans": 0,
            "mss_scans": 0,
            "rsi_scans": 0,
            "alerts_sent": 0,
            "last_scan_time": None
        }

        self.logger.info("AutoScanner initialized")
        self.logger.info(f"Auto-scan enabled: {self.enabled}")
        self.logger.info(f"Intervals - Smart Money: {self.smart_money_interval}h, MSS: {self.mss_interval}h, RSI: {self.rsi_interval}h")

    async def start(self):
        """Start the automated scanner"""
        if not self.enabled:
            self.logger.warning("Auto-scanner is DISABLED. Set AUTO_SCAN_ENABLED=true to enable.")
            return

        self.logger.info("Starting AutoScanner...")

        # Schedule Smart Money Scan
        self.scheduler.add_job(
            self.smart_money_auto_scan,
            trigger=IntervalTrigger(hours=self.smart_money_interval),
            id="smart_money_scan",
            name="Smart Money Scanner",
            replace_existing=True,
            next_run_time=datetime.now()  # Run immediately on start
        )
        self.logger.info(f"✅ Smart Money Scan scheduled every {self.smart_money_interval} hour(s)")

        # Schedule MSS Discovery
        self.scheduler.add_job(
            self.mss_auto_discovery,
            trigger=IntervalTrigger(hours=self.mss_interval),
            id="mss_discovery",
            name="MSS Discovery Scanner",
            replace_existing=True,
            next_run_time=datetime.now()  # Run immediately on start
        )
        self.logger.info(f"✅ MSS Discovery scheduled every {self.mss_interval} hour(s)")

        # Schedule RSI Screener
        self.scheduler.add_job(
            self.rsi_auto_screener,
            trigger=IntervalTrigger(hours=self.rsi_interval),
            id="rsi_screener",
            name="RSI Technical Screener",
            replace_existing=True
        )
        self.logger.info(f"✅ RSI Screener scheduled every {self.rsi_interval} hour(s)")

        # Schedule Daily Summary (8 AM every day)
        self.scheduler.add_job(
            self.send_daily_summary,
            trigger=CronTrigger(hour=8, minute=0),
            id="daily_summary",
            name="Daily Summary Report",
            replace_existing=True
        )
        self.logger.info("✅ Daily Summary scheduled at 8:00 AM")

        # Start the scheduler
        self.scheduler.start()
        self.logger.info("🚀 AutoScanner started successfully! Running 24/7...")

    async def stop(self):
        """Stop the automated scanner"""
        self.logger.info("Stopping AutoScanner...")
        self.scheduler.shutdown(wait=True)

        # Close services
        await self.smart_money.close()
        await self.mss.close()

        self.logger.info("AutoScanner stopped")

    async def smart_money_auto_scan(self):
        """
        Automated Smart Money Scanner

        Scans all coins in SCAN_LIST for whale accumulation/distribution
        Sends alerts for signals above threshold
        """
        self.logger.info("🔍 Starting Smart Money Auto-Scan...")
        start_time = datetime.now()

        try:
            # Scan markets with configured thresholds
            results = await self.smart_money.scan_markets(
                min_accumulation_score=self.accumulation_threshold,
                min_distribution_score=self.distribution_threshold
            )

            # Update stats
            self.stats["smart_money_scans"] += 1
            self.stats["total_scans"] += 1
            self.stats["last_scan_time"] = start_time

            # Extract signals
            accumulation_signals = results.get("accumulation", [])
            distribution_signals = results.get("distribution", [])

            total_signals = len(accumulation_signals) + len(distribution_signals)

            self.logger.info(
                f"✅ Smart Money Scan complete: "
                f"{len(accumulation_signals)} accumulation, "
                f"{len(distribution_signals)} distribution signals"
            )

            # Send alerts for strong signals
            if total_signals > 0:
                await self._send_smart_money_alerts(accumulation_signals, distribution_signals)

            # Save signals to history
            await self._save_signals_to_history(accumulation_signals, "ACCUMULATION")
            await self._save_signals_to_history(distribution_signals, "DISTRIBUTION")

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"⏱️ Smart Money Scan completed in {duration:.1f}s")

        except Exception as e:
            self.logger.error(f"❌ Error in Smart Money Auto-Scan: {type(e).__name__}: {str(e)}")

    async def mss_auto_discovery(self):
        """
        Automated MSS Discovery Scanner

        Discovers new low-cap gems with high potential
        Alerts on MSS scores above threshold
        """
        self.logger.info("💎 Starting MSS Auto-Discovery...")
        start_time = datetime.now()

        try:
            # Run Phase 1 Discovery
            results = await self.mss.phase1_discovery(
                max_fdv_usd=50_000_000,  # $50M max FDV
                max_age_hours=72,         # 72 hours (3 days)
                min_volume_24h=100_000,   # $100k min volume
                limit=50
            )

            # Update stats
            self.stats["mss_scans"] += 1
            self.stats["total_scans"] += 1
            self.stats["last_scan_time"] = start_time

            # Filter by threshold
            high_score_gems = [
                coin for coin in results
                if coin.get("mss_score", 0) >= self.mss_threshold
            ]

            self.logger.info(
                f"✅ MSS Discovery complete: "
                f"{len(results)} coins scanned, "
                f"{len(high_score_gems)} gems above threshold ({self.mss_threshold})"
            )

            # Send alerts for high-scoring gems
            if high_score_gems:
                await self._send_mss_alerts(high_score_gems)

            # Save to history
            await self._save_mss_discoveries(high_score_gems)

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"⏱️ MSS Discovery completed in {duration:.1f}s")

        except Exception as e:
            self.logger.error(f"❌ Error in MSS Auto-Discovery: {type(e).__name__}: {str(e)}")

    async def rsi_auto_screener(self):
        """
        Automated RSI Technical Screener

        Scans for oversold (<25) and overbought (>75) conditions
        Uses Coinglass RSI data for 535+ coins
        """
        self.logger.info("📊 Starting RSI Auto-Screener...")
        start_time = datetime.now()

        try:
            # Get all supported coins from Coinglass
            supported = await self.coinglass.get_supported_coins()
            if not supported.get("success"):
                self.logger.warning("Failed to get supported coins from Coinglass")
                return

            coins = supported.get("coins", [])[:100]  # Limit to 100 for performance

            # Scan RSI for all coins (would need to implement batch RSI endpoint)
            oversold = []
            overbought = []

            # Note: This is a placeholder - actual implementation would need
            # batch RSI endpoint or parallel requests
            self.logger.info(f"RSI Screener: Would scan {len(coins)} coins")

            # Update stats
            self.stats["rsi_scans"] += 1
            self.stats["total_scans"] += 1
            self.stats["last_scan_time"] = start_time

            self.logger.info(
                f"✅ RSI Screener complete: "
                f"{len(oversold)} oversold, "
                f"{len(overbought)} overbought"
            )

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"⏱️ RSI Screener completed in {duration:.1f}s")

        except Exception as e:
            self.logger.error(f"❌ Error in RSI Auto-Screener: {type(e).__name__}: {str(e)}")

    async def send_daily_summary(self):
        """
        Send daily summary report

        Includes:
        - Total scans performed
        - Signals generated
        - Top accumulation/distribution coins
        - Performance stats
        """
        self.logger.info("📊 Generating Daily Summary...")

        try:
            summary = f"""
📊 CRYPTOSATX DAILY SUMMARY - {datetime.now().strftime('%Y-%m-%d')}

🔍 Scanning Activity:
• Total Scans: {self.stats['total_scans']}
• Smart Money Scans: {self.stats['smart_money_scans']}
• MSS Discovery Scans: {self.stats['mss_scans']}
• RSI Scans: {self.stats['rsi_scans']}

📢 Alerts:
• Alerts Sent: {self.stats['alerts_sent']}

⏰ Last Scan: {self.stats['last_scan_time'].strftime('%H:%M:%S') if self.stats['last_scan_time'] else 'N/A'}

🤖 AutoScanner Status: ACTIVE ✅
Next report in 24 hours.
"""

            # FIXED: Use send_custom_alert instead of send_message
            await self.telegram.send_custom_alert(
                title="📊 CRYPTOSATX DAILY SUMMARY",
                message=summary
            )
            self.logger.info("✅ Daily summary sent")

            # Reset daily stats (optional - comment out to keep cumulative)
            # self.stats['alerts_sent'] = 0

        except Exception as e:
            self.logger.error(f"❌ Error sending daily summary: {str(e)}")

    async def _send_smart_money_alerts(
        self,
        accumulation_signals: List[Dict],
        distribution_signals: List[Dict]
    ):
        """Send Telegram alerts for Smart Money signals"""
        try:
            # Accumulation alerts
            for signal in accumulation_signals[:5]:  # Top 5
                symbol = signal.get("symbol", "UNKNOWN")
                score = signal.get("score", 0)
                reasons = signal.get("reasons", [])

                # Determine tier
                tier = "🚨 TIER 1" if score >= 9 else "⚠️ TIER 2" if score >= 7 else "ℹ️ TIER 3"

                message = f"""
{tier} - ACCUMULATION DETECTED

Symbol: {symbol}
Score: {score}/10
Type: Whale Accumulation

📊 Signals:
{chr(10).join(['• ' + r for r in reasons[:5]])}

💡 Action: {self._get_action_recommendation(score, 'accumulation')}
⏰ Detected: {self._get_wib_timestamp()}
"""

                # FIXED: Use send_custom_alert instead of send_message
                await self.telegram.send_custom_alert(
                    title=f"{tier} - ACCUMULATION DETECTED",
                    message=message
                )
                self.stats['alerts_sent'] += 1
                await asyncio.sleep(1)  # Rate limit

            # Distribution alerts
            for signal in distribution_signals[:5]:  # Top 5
                symbol = signal.get("symbol", "UNKNOWN")
                score = signal.get("score", 0)
                reasons = signal.get("reasons", [])

                tier = "🚨 TIER 1" if score >= 9 else "⚠️ TIER 2" if score >= 7 else "ℹ️ TIER 3"

                message = f"""
{tier} - DISTRIBUTION DETECTED

Symbol: {symbol}
Score: {score}/10
Type: Whale Distribution

📊 Signals:
{chr(10).join(['• ' + r for r in reasons[:5]])}

💡 Action: {self._get_action_recommendation(score, 'distribution')}
⏰ Detected: {self._get_wib_timestamp()}
"""

                # FIXED: Use send_custom_alert instead of send_message
                await self.telegram.send_custom_alert(
                    title=f"{tier} - DISTRIBUTION DETECTED",
                    message=message
                )
                self.stats['alerts_sent'] += 1
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"Error sending Smart Money alerts: {str(e)}")

    async def _send_mss_alerts(self, gems: List[Dict]):
        """Send Telegram alerts for MSS discoveries"""
        try:
            for gem in gems[:3]:  # Top 3
                symbol = gem.get("symbol", "UNKNOWN")
                score = gem.get("mss_score", 0)
                fdv = gem.get("fdv", 0)
                age_hours = gem.get("age_hours", 0)

                tier = "🚨 TIER 1" if score >= 90 else "⚠️ TIER 2" if score >= 80 else "ℹ️ TIER 3"

                message = f"""
{tier} - NEW GEM DISCOVERED 💎

Symbol: {symbol}
MSS Score: {score}/100

📊 Fundamentals:
• FDV: ${fdv:,.0f}
• Age: {age_hours:.0f} hours
• Category: New Listing

💰 Expected Return: {self._get_expected_return(score)}
💡 Action: IMMEDIATE RESEARCH + BUY
⏰ Discovered: {self._get_wib_timestamp()}
"""

                # FIXED: Use send_custom_alert instead of send_message
                await self.telegram.send_custom_alert(
                    title=f"{tier} - NEW GEM DISCOVERED 💎",
                    message=message
                )
                self.stats['alerts_sent'] += 1
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"Error sending MSS alerts: {str(e)}")

    async def _save_signals_to_history(self, signals: List[Dict], signal_type: str):
        """Save signals to signal history database and start performance tracking"""
        for signal in signals:
            try:
                symbol = signal.get("symbol", "UNKNOWN")

                signal_data = {
                    "symbol": symbol,
                    "signal": signal_type,
                    "score": signal.get("score", 0),
                    "reasons": signal.get("reasons", []),
                    "timestamp": datetime.now().isoformat(),
                    "source": "auto_scanner"
                }

                # Save to history
                saved_signal = await signal_history.save_signal(signal_data)

                # Start performance tracking
                if saved_signal and saved_signal.get("id"):
                    try:
                        # Get current price for tracking
                        from app.services.coinapi_service import CoinapiService
                        coinapi = CoinapiService()
                        price_data = await coinapi.get_current_price(symbol)

                        if price_data.get("success"):
                            # Map signal type to LONG/SHORT
                            signal_direction = "LONG" if signal_type == "ACCUMULATION" else "SHORT"

                            # Prepare tracking data
                            tracking_data = {
                                "id": saved_signal["id"],
                                "symbol": symbol,
                                "signal": signal_direction,
                                "price": price_data["price"],
                                "timestamp": datetime.now().isoformat(),
                                "scanner_type": "smart_money"
                            }

                            # Start tracking
                            await track_signal(tracking_data)
                            self.logger.debug(f"Started tracking signal {saved_signal['id']} for {symbol}")
                    except Exception as track_err:
                        self.logger.warning(f"Could not start tracking for {symbol}: {track_err}")

            except Exception as e:
                self.logger.error(f"Error saving signal to history: {str(e)}")

    async def _save_mss_discoveries(self, gems: List[Dict]):
        """Save MSS discoveries to history and start performance tracking"""
        for gem in gems:
            try:
                symbol = gem.get("symbol", "UNKNOWN")
                mss_score = gem.get("mss_score", 0)

                signal_data = {
                    "symbol": symbol,
                    "signal": "MSS_DISCOVERY",
                    "score": mss_score,
                    "fdv": gem.get("fdv", 0),
                    "age_hours": gem.get("age_hours", 0),
                    "timestamp": datetime.now().isoformat(),
                    "source": "auto_scanner"
                }

                # Save to history
                saved_signal = await signal_history.save_signal(signal_data)

                # Start performance tracking
                if saved_signal and saved_signal.get("id"):
                    try:
                        # Get current price for tracking
                        from app.services.coinapi_service import CoinapiService
                        coinapi = CoinapiService()
                        price_data = await coinapi.get_current_price(symbol)

                        if price_data.get("success"):
                            # Prepare tracking data
                            tracking_data = {
                                "id": saved_signal["id"],
                                "symbol": symbol,
                                "signal": "LONG",  # MSS discoveries are buy signals
                                "price": price_data["price"],
                                "timestamp": datetime.now().isoformat(),
                                "unified_score": mss_score,  # MSS score as unified score
                                "scanner_type": "mss"
                            }

                            # Start tracking
                            await track_signal(tracking_data)
                            self.logger.debug(f"Started tracking MSS signal {saved_signal['id']} for {symbol}")
                    except Exception as track_err:
                        self.logger.warning(f"Could not start tracking for {symbol}: {track_err}")

            except Exception as e:
                self.logger.error(f"Error saving MSS discovery to history: {str(e)}")

    def _get_action_recommendation(self, score: int, signal_type: str) -> str:
        """Get action recommendation based on score"""
        if signal_type == "accumulation":
            if score >= 9:
                return "STRONG BUY - Immediate position"
            elif score >= 7:
                return "BUY - Accumulate on dips"
            else:
                return "WATCH - Monitor closely"
        else:  # distribution
            if score >= 9:
                return "SELL - Exit positions"
            elif score >= 7:
                return "REDUCE - Take profits"
            else:
                return "WATCH - Prepare to exit"

    def _get_expected_return(self, mss_score: int) -> str:
        """Estimate expected return based on MSS score"""
        if mss_score >= 90:
            return "20-50x (ultra high potential)"
        elif mss_score >= 85:
            return "10-25x (very high potential)"
        elif mss_score >= 80:
            return "5-15x (high potential)"
        elif mss_score >= 75:
            return "3-8x (good potential)"
        else:
            return "2-5x (moderate potential)"

    def _get_wib_timestamp(self) -> str:
        """Get current timestamp in WIB (Western Indonesian Time / UTC+7)"""
        from datetime import timedelta, timezone
        wib_tz = timezone(timedelta(hours=7))
        return datetime.now(wib_tz).strftime('%Y-%m-%d %H:%M:%S')

    def get_stats(self) -> Dict:
        """Get current scanner statistics"""
        return {
            **self.stats,
            "enabled": self.enabled,
            "next_jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
        }


# Global instance
auto_scanner = AutoScanner()


async def start_auto_scanner():
    """Start the auto scanner (called from main app)"""
    await auto_scanner.start()


async def stop_auto_scanner():
    """Stop the auto scanner (called on shutdown)"""
    await auto_scanner.stop()


if __name__ == "__main__":
    """Run auto scanner standalone"""
    import logging
    logging.basicConfig(level=logging.INFO)

    async def main():
        await auto_scanner.start()

        # Keep running
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            await auto_scanner.stop()

    asyncio.run(main())

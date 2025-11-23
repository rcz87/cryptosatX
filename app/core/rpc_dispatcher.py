"""
RPC Dispatcher - IMPROVED VERSION with Timeout Protection
Maps operation names to service-layer callables with proper validation and timeout handling
"""
import os
import time
import asyncio
import traceback
from typing import Dict, Any, Callable
from pydantic import ValidationError

from app.utils.operation_catalog import get_operation_metadata
from app.models.rpc_models import RPCResponse, SymbolArgs
from app.utils.logger import logger


class RPCDispatcher:
    """
    Unified RPC dispatcher - maps operations to service functions
    Follows architect guidance: service-layer callables with Pydantic validation
    
    ✅ NEW: Timeout protection for all operations
    ✅ NEW: Detailed error logging with context
    ✅ NEW: Graceful degradation on timeout
    """
    
    # Operation timeout configuration (seconds)
    DEFAULT_TIMEOUT = int(os.getenv("RPC_OPERATION_TIMEOUT", "30"))
    
    # Timeout overrides for specific operation types
    TIMEOUT_OVERRIDES = {
        "signals.get": 45,  # Signal generation needs more time
        "mss.discover": 60,  # MSS discovery scans many coins
        "mss.scan": 60,
        "smart_money.scan": 45,
        "smart_money.scan_tiered": 60,  # Tiered scanning for 1000+ coins
        "backtest.run": 120,  # Backtesting can take longer
        "scalping.analyze": 45,  # Full scalping analysis with smart money
    }
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """Register operation handlers - CORRECTED with proper service imports"""
        
        # Core Signals
        self.handlers["signals.get"] = self._signals_get
        self.handlers["market.get"] = self._market_get
        self.handlers["market.summary"] = self._market_summary
        
        # Coinglass - Key endpoints
        self.handlers["coinglass.markets"] = self._coinglass_markets
        self.handlers["coinglass.liquidations.symbol"] = self._coinglass_liquidations_symbol
        self.handlers["coinglass.funding_rate.history"] = self._coinglass_funding_rate_history
        self.handlers["coinglass.open_interest.history"] = self._coinglass_open_interest_history
        self.handlers["coinglass.indicators.fear_greed"] = self._coinglass_fear_greed
        self.handlers["coinglass.indicators.rsi_list"] = self._coinglass_rsi_list
        self.handlers["coinglass.supported_coins"] = self._coinglass_supported_coins
        
        # Smart Money
        self.handlers["smart_money.scan"] = self._smart_money_scan
        self.handlers["smart_money.scan_accumulation"] = self._smart_money_scan_accumulation
        self.handlers["smart_money.scan_distribution"] = self._smart_money_scan_distribution
        self.handlers["smart_money.analyze"] = self._smart_money_analyze
        self.handlers["smart_money.scan_tiered"] = self._smart_money_scan_tiered
        
        # MSS
        self.handlers["mss.discover"] = self._mss_discover
        self.handlers["mss.analyze"] = self._mss_analyze
        self.handlers["mss.scan"] = self._mss_scan
        
        # LunarCrush
        self.handlers["lunarcrush.coin"] = self._lunarcrush_coin
        self.handlers["lunarcrush.coins_discovery"] = self._lunarcrush_coins_discovery
        
        # CoinAPI
        self.handlers["coinapi.quote"] = self._coinapi_quote
        
        # Health
        self.handlers["health.check"] = self._health_check
        
        # Spike Detection (Phase 5)
        self.handlers["spike.check_system"] = self._spike_check_system
        self.handlers["spike.recent_activity"] = self._spike_recent_activity
        self.handlers["spike.configuration"] = self._spike_configuration
        self.handlers["spike.explain"] = self._spike_explain
        self.handlers["spike.monitor_coin"] = self._spike_monitor_coin
        self.handlers["spike.status"] = self._spike_status
        self.handlers["spike.health"] = self._spike_health
        self.handlers["spike.price_detector_status"] = self._spike_price_detector_status
        self.handlers["spike.liquidation_detector_status"] = self._spike_liquidation_detector_status
        self.handlers["spike.social_monitor_status"] = self._spike_social_monitor_status
        self.handlers["spike.coordinator_status"] = self._spike_coordinator_status
        
        # Analytics (GPT-5.1 Self-Evaluation)
        self.handlers["analytics.history.latest"] = self._analytics_history_latest
        self.handlers["analytics.performance.symbol"] = self._analytics_performance_symbol
        self.handlers["analytics.performance.summary"] = self._analytics_performance_summary

        # Scalping Analysis
        self.handlers["scalping.analyze"] = self._scalping_analyze
        self.handlers["scalping.quick"] = self._scalping_quick
        self.handlers["scalping.info"] = self._scalping_info
    
    async def dispatch(self, operation: str, args: Dict[str, Any]) -> RPCResponse:
        """
        Dispatch operation with validation, timeout protection, and error handling
        
        ✅ NEW: Wraps execution with asyncio.wait_for() for timeout protection
        ✅ NEW: Catches TimeoutError and returns user-friendly error
        ✅ NEW: Logs execution context for debugging
        """
        start_time = time.time()
        
        # Check operation exists
        if operation not in self.handlers:
            available = list(self.handlers.keys())[:10]
            return RPCResponse(
                ok=False,
                operation=operation,
                error=f"Unknown operation. Available (showing 10/{len(self.handlers)}): {available}"
            )
        
        # Get and validate metadata
        try:
            metadata = get_operation_metadata(operation)
        except ValueError:
            return RPCResponse(
                ok=False,
                operation=operation,
                error=f"Operation not in catalog: {operation}"
            )
        
        # Validate required arguments
        validation_error = self._validate_args(metadata, args)
        if validation_error:
            return RPCResponse(
                ok=False,
                operation=operation,
                error=validation_error
            )
        
        # ✅ NEW: Get timeout for this operation
        timeout = self.TIMEOUT_OVERRIDES.get(operation, self.DEFAULT_TIMEOUT)
        
        # Execute handler with timeout protection
        try:
            handler = self.handlers[operation]
            
            # ✅ NEW: Wrap with asyncio.wait_for for timeout protection
            result = await asyncio.wait_for(
                handler(args),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return RPCResponse(
                ok=True,
                operation=operation,
                data=result,
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace,
                    "timeout_limit_s": timeout
                }
            )
            
        except asyncio.TimeoutError:
            # ✅ NEW: Handle timeout gracefully
            execution_time = time.time() - start_time
            
            error_msg = (
                f"Operation timeout after {timeout}s. "
                f"The operation took too long to complete. "
                f"Try reducing the scope or parameters."
            )
            
            # Log timeout for monitoring
            logger.info(f"⏱️  RPC TIMEOUT: {operation} after {timeout}s with args: {args}")
            
            return RPCResponse(
                ok=False,
                operation=operation,
                error=error_msg,
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace,
                    "timeout_limit_s": timeout,
                    "error_type": "TimeoutError",
                    "suggestion": "Reduce scope or increase timeout in environment variables"
                }
            )
            
        except Exception as e:
            # ✅ IMPROVED: Better error logging with context
            execution_time = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Log detailed error for debugging
            logger.info(f"❌ RPC ERROR: {operation}")
            logger.info(f"   Error Type: {error_type}")
            logger.info(f"   Error Message: {error_msg}")
            logger.info(f"   Args: {args}")
            logger.info(f"   Stack Trace:\n{traceback.format_exc()}")
            
            return RPCResponse(
                ok=False,
                operation=operation,
                error=f"{error_type}: {error_msg}",
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace,
                    "error_type": error_type,
                    "timeout_limit_s": timeout
                }
            )
    
    def _validate_args(self, metadata, args: Dict) -> str:
        """Validate required arguments - returns error message or None"""
        if metadata.requires_symbol and not args.get("symbol"):
            return f"Missing required argument 'symbol' for operation '{metadata.name}'. Example: {{\"operation\": \"{metadata.name}\", \"args\": {{\"symbol\": \"BTC\"}}}}"
        if metadata.requires_topic and not args.get("topic"):
            return f"Missing required argument 'topic' for operation '{metadata.name}'. Example: {{\"operation\": \"{metadata.name}\", \"args\": {{\"topic\": \"bitcoin\"}}}}"
        if metadata.requires_asset and not args.get("asset"):
            return f"Missing required argument 'asset' for operation '{metadata.name}'. Example: {{\"operation\": \"{metadata.name}\", \"args\": {{\"asset\": \"BTC\"}}}}"
        if metadata.requires_exchange and not args.get("exchange"):
            return f"Missing required argument 'exchange' for operation '{metadata.name}'. Example: {{\"operation\": \"{metadata.name}\", \"args\": {{\"exchange\": \"Binance\"}}}}"
        return None
    
    # ========================================================================
    # HANDLER IMPLEMENTATIONS - FIXED with proper imports and arg handling
    # ========================================================================
    
    async def _signals_get(self, args: Dict) -> Dict:
        """Get trading signal with mode support"""
        from app.core.signal_engine import signal_engine
        symbol = args["symbol"]
        debug = args.get("debug", False)
        mode = args.get("mode", "aggressive")  # Support mode parameter (conservative/aggressive/ultra or 1/2/3)
        return await signal_engine.build_signal(symbol, debug=debug, mode=mode)
    
    async def _market_get(self, args: Dict) -> Dict:
        """Get market data - uses signal engine's internal aggregation"""
        from app.core.signal_engine import signal_engine
        symbol = args["symbol"]
        # Signal engine internally aggregates market data
        return await signal_engine.build_signal(symbol, debug=True)
    
    async def _market_summary(self, args: Dict) -> Dict:
        """Get overall market summary across major cryptocurrencies"""
        from app.services.market_summary_service import market_summary_service
        return await market_summary_service.get_market_summary()
    
    async def _coinglass_markets(self, args: Dict) -> Dict:
        """Get Coinglass markets"""
        from app.services.coinglass_comprehensive_service import coinglass_comprehensive
        symbol = args.get("symbol")
        return await coinglass_comprehensive.get_coins_markets(symbol=symbol)
    
    async def _coinglass_liquidations_symbol(self, args: Dict) -> Dict:
        """Get liquidations for symbol - FIXED arg passing + response size optimization"""
        from app.services.coinglass_comprehensive_service import coinglass_comprehensive
        symbol = args.get("symbol", "BTC")
        exchange = args.get("exchange", "Binance")
        interval = args.get("interval", "h1")
        # ✅ OPTIMIZATION: Reduce default limit from 100 to 20 to prevent ResponseTooLargeError
        # This is especially important for high-volume coins like SOL, BTC, ETH
        limit = args.get("limit", 20)  # GPT Actions have ~100KB response limit
        return await coinglass_comprehensive.get_liquidation_history(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            limit=limit
        )
    
    async def _coinglass_funding_rate_history(self, args: Dict) -> Dict:
        """Get funding rate history"""
        from app.services.coinglass_comprehensive_service import coinglass_comprehensive
        return await coinglass_comprehensive.get_funding_rate_history(**args)
    
    async def _coinglass_open_interest_history(self, args: Dict) -> Dict:
        """Get open interest history"""
        from app.services.coinglass_comprehensive_service import coinglass_comprehensive
        return await coinglass_comprehensive.get_open_interest_history(**args)
    
    async def _coinglass_fear_greed(self, args: Dict) -> Dict:
        """Get Fear & Greed Index"""
        from app.services.coinglass_comprehensive_service import coinglass_comprehensive
        return await coinglass_comprehensive.get_fear_greed_index()
    
    async def _coinglass_rsi_list(self, args: Dict) -> Dict:
        """Get RSI list with pagination support - FIXED type safety"""
        from app.services.coinglass_comprehensive_service import coinglass_comprehensive
        limit = args.get("limit", 20)
        signal_filter = args.get("signal_filter")
        
        # Validate and default signal_filter for type safety
        if signal_filter and signal_filter.upper() not in ["OVERSOLD", "OVERBOUGHT", "NEUTRAL"]:
            return {
                "success": False,
                "error": f"Invalid signal_filter '{signal_filter}'. Must be one of: OVERSOLD, OVERBOUGHT, NEUTRAL"
            }
        
        # Use default "all" if None to satisfy type checker
        filter_value = signal_filter if signal_filter else "all"
        
        return await coinglass_comprehensive.get_rsi_list(
            limit=limit,
            signal_filter=filter_value
        )
    
    async def _coinglass_supported_coins(self, args: Dict) -> Dict:
        """Get supported coins"""
        from app.services.coinglass_comprehensive_service import coinglass_comprehensive
        return await coinglass_comprehensive.get_supported_coins()
    
    async def _smart_money_scan(self, args: Dict) -> Dict:
        """Scan smart money - FIXED"""
        from app.services.smart_money_service import smart_money_service
        min_acc = args.get("min_accumulation_score", 5)
        min_dist = args.get("min_distribution_score", 5)
        coins_str = args.get("coins")
        coin_list = coins_str.split(",") if coins_str else None
        limit = args.get("limit", 50)  # ✅ Default 50 instead of 20
        return await smart_money_service.scan_markets(
            min_accumulation_score=min_acc,
            min_distribution_score=min_dist,
            coins=coin_list,
            limit=limit  # ✅ Pass limit parameter
        )
    
    async def _smart_money_scan_accumulation(self, args: Dict) -> Dict:
        """Scan accumulation - delegates to main scan"""
        from app.services.smart_money_service import smart_money_service
        min_score = args.get("min_score", 6)
        # Use scan_markets and filter for accumulation
        result = await smart_money_service.scan_markets(
            min_accumulation_score=min_score,
            min_distribution_score=10  # High threshold to filter out distribution
        )
        return {"accumulation_signals": result.get("accumulation", [])}
    
    async def _smart_money_scan_distribution(self, args: Dict) -> Dict:
        """Scan distribution - delegates to main scan"""
        from app.services.smart_money_service import smart_money_service
        min_score = args.get("min_score", 6)
        # Use scan_markets and filter for distribution
        result = await smart_money_service.scan_markets(
            min_accumulation_score=10,  # High threshold to filter out accumulation
            min_distribution_score=min_score
        )
        return {"distribution_signals": result.get("distribution", [])}
    
    async def _smart_money_analyze(self, args: Dict) -> Dict:
        """Analyze smart money - FIXED method name"""
        from app.services.smart_money_service import smart_money_service
        symbol = args["symbol"]
        return await smart_money_service.analyze_any_coin(symbol)

    async def _smart_money_scan_tiered(self, args: Dict) -> Dict:
        """Tiered scan - scan 1000+ coins with 3-tier filtering"""
        from app.services.tiered_scanner import tiered_scanner

        total_coins = args.get("total_coins", 100)
        tier1_enabled = args.get("tier1_enabled", True)
        tier2_enabled = args.get("tier2_enabled", True)
        tier3_enabled = args.get("tier3_enabled", True)
        final_limit = args.get("final_limit", 10)

        result = await tiered_scanner.scan_tiered(
            total_coins=total_coins,
            tier1_enabled=tier1_enabled,
            tier2_enabled=tier2_enabled,
            tier3_enabled=tier3_enabled,
            final_limit=final_limit
        )

        return result

    async def _mss_discover(self, args: Dict) -> Dict:
        """MSS discover - FIXED method name and parameters"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        # Map GPT Action params to actual service params
        limit = args.get("max_results", 10)
        max_fdv = args.get("max_fdv_usd", 50000000)
        max_age = args.get("max_age_hours", 72)
        min_vol = args.get("min_volume_24h", 100000.0)
        # phase1_discovery returns List[Dict], wrap it
        results = await mss.phase1_discovery(
            limit=limit,
            max_fdv_usd=max_fdv,
            max_age_hours=max_age,
            min_volume_24h=min_vol
        )
        return {"discovered_coins": results, "count": len(results)}
    
    async def _mss_analyze(self, args: Dict) -> Dict:
        """MSS analyze - FIXED"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        symbol = args["symbol"]
        # Method calculate_mss_score is the correct method
        return await mss.calculate_mss_score(symbol)
    
    async def _mss_scan(self, args: Dict) -> Dict:
        """MSS scan - FIXED method name and parameters"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        # Map GPT Action params to actual service params
        limit = args.get("max_results", 10)
        max_fdv = args.get("max_fdv_usd", 50000000)
        max_age = args.get("max_age_hours", 72)
        min_score = args.get("min_mss_score", 65.0)
        # scan_and_rank returns List[Dict], wrap it
        results = await mss.scan_and_rank(
            limit=limit,
            max_fdv_usd=max_fdv,
            max_age_hours=max_age,
            min_mss_score=min_score
        )
        return {"ranked_coins": results, "count": len(results)}
    
    async def _lunarcrush_coin(self, args: Dict) -> Dict:
        """Get LunarCrush coin data - FIXED service import"""
        from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
        symbol = args["symbol"]
        return await lunarcrush_comprehensive.get_coin_metrics(symbol)
    
    async def _lunarcrush_coins_discovery(self, args: Dict) -> Dict:
        """LunarCrush coins discovery - FIXED service import"""
        from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
        min_galaxy = args.get("min_galaxy_score", 50)
        limit = args.get("limit", 20)
        return await lunarcrush_comprehensive.discover_coins(
            min_galaxy_score=min_galaxy,
            limit=limit
        )
    
    async def _coinapi_quote(self, args: Dict) -> Dict:
        """Get CoinAPI quote - FIXED"""
        from app.services.coinapi_service import coinapi_service
        symbol = args["symbol"]
        return await coinapi_service.get_quote(symbol)
    
    async def _health_check(self, args: Dict) -> Dict:
        """Health check"""
        return {
            "status": "healthy",
            "service": "CryptoSatX RPC Endpoint",
            "version": "3.0.0",
            "operations_count": len(self.handlers),
            "timeout_protection": "enabled",
            "default_timeout_s": self.DEFAULT_TIMEOUT
        }
    
    # ========================================================================
    # SPIKE DETECTION HANDLERS (PHASE 5)
    # ========================================================================
    
    async def _spike_check_system(self, args: Dict) -> Dict:
        """Check spike detection system status"""
        from app.api.routes_spike_gpt import check_spike_system
        return await check_spike_system()
    
    async def _spike_recent_activity(self, args: Dict) -> Dict:
        """Get recent spike detection activity"""
        from app.api.routes_spike_gpt import get_recent_spike_activity
        return await get_recent_spike_activity()
    
    async def _spike_configuration(self, args: Dict) -> Dict:
        """Get spike detection configuration"""
        from app.services.realtime_spike_detector import realtime_spike_detector
        from app.services.liquidation_spike_detector import liquidation_spike_detector
        from app.services.social_spike_monitor import social_spike_monitor
        
        price_status = await realtime_spike_detector.get_status()
        liq_status = await liquidation_spike_detector.get_status()
        social_status = await social_spike_monitor.get_status()
        
        return {
            "success": True,
            "configuration": {
                "price_spike_detector": {
                    "threshold": f"{price_status.get('spike_threshold', 8.0)}% price change",
                    "time_window": "5 minutes",
                    "check_interval": f"{price_status.get('check_interval', 30)} seconds",
                    "monitoring_scope": "Top 100 coins by market cap"
                },
                "liquidation_spike_detector": {
                    "market_wide_threshold": "$50 Million in 1 hour",
                    "per_coin_threshold": "$20 Million in 1 hour",
                    "check_interval": f"{liq_status.get('check_interval', 60)} seconds"
                },
                "social_spike_detector": {
                    "threshold": "100% social volume increase",
                    "check_interval": f"{social_status.get('check_interval', 300)} seconds"
                }
            },
            "user_message": "✅ System configured for early entry opportunities with multi-signal correlation"
        }
    
    async def _spike_explain(self, args: Dict) -> Dict:
        """Explain spike detection system"""
        return {
            "success": True,
            "what_it_does": "Monitors the crypto market 24/7 to catch sudden price movements BEFORE retail traders react",
            "how_it_works": {
                "step_1": "🔍 Monitors top 100 coins every 30 seconds for >8% price moves",
                "step_2": "💥 Tracks liquidations >$50M market-wide and >$20M per coin",
                "step_3": "📱 Detects viral social moments with >100% volume spike",
                "step_4": "🎯 Correlates multiple signals for high-confidence alerts",
                "step_5": "📲 Sends instant Telegram notifications with entry recommendations"
            },
            "signal_confidence_levels": {
                "EXTREME (3+ signals)": {
                    "description": "Multiple spike types detected simultaneously",
                    "expected_win_rate": "70-80%",
                    "action": "Strong entry signal - consider immediate position"
                },
                "HIGH (2 signals)": {
                    "description": "Two spike types correlate",
                    "expected_win_rate": "60-70%",
                    "action": "Good entry opportunity - monitor closely"
                },
                "MEDIUM (1 signal)": {
                    "description": "Single spike detected",
                    "expected_win_rate": "50-60%",
                    "action": "Watch for confirmation from other signals"
                }
            },
            "user_message": "🎯 You're 30-60 seconds ahead of retail traders with this system!"
        }

    async def _spike_monitor_coin(self, args: Dict) -> Dict:
        """Monitor spike detection for specific coin"""
        from app.api.routes_spike_gpt import monitor_coin_spikes
        symbol = args.get("symbol", "BTC")
        return await monitor_coin_spikes(symbol)

    async def _spike_status(self, args: Dict) -> Dict:
        """Get comprehensive spike detection status"""
        from app.services.realtime_spike_detector import realtime_spike_detector
        from app.services.liquidation_spike_detector import liquidation_spike_detector
        from app.services.social_spike_monitor import social_spike_monitor
        from app.services.spike_coordinator import spike_coordinator
        
        return {
            "success": True,
            "price_detector": await realtime_spike_detector.get_status(),
            "liquidation_detector": await liquidation_spike_detector.get_status(),
            "social_monitor": await social_spike_monitor.get_status(),
            "coordinator": await spike_coordinator.get_status()
        }
    
    async def _spike_health(self, args: Dict) -> Dict:
        """Quick health check for spike detectors"""
        from app.services.realtime_spike_detector import realtime_spike_detector
        from app.services.liquidation_spike_detector import liquidation_spike_detector
        from app.services.social_spike_monitor import social_spike_monitor
        
        all_running = (
            realtime_spike_detector.is_running and
            liquidation_spike_detector.is_running and
            social_spike_monitor.is_running
        )
        
        return {
            "success": True,
            "system_status": "ACTIVE" if all_running else "DEGRADED",
            "detectors_running": {
                "price": realtime_spike_detector.is_running,
                "liquidation": liquidation_spike_detector.is_running,
                "social": social_spike_monitor.is_running
            },
            "message": "✅ All detectors active" if all_running else "⚠️ Some detectors offline"
        }
    
    async def _spike_price_detector_status(self, args: Dict) -> Dict:
        """Get price spike detector detailed status"""
        from app.services.realtime_spike_detector import realtime_spike_detector
        return await realtime_spike_detector.get_status()
    
    async def _spike_liquidation_detector_status(self, args: Dict) -> Dict:
        """Get liquidation spike detector detailed status"""
        from app.services.liquidation_spike_detector import liquidation_spike_detector
        return await liquidation_spike_detector.get_status()
    
    async def _spike_social_monitor_status(self, args: Dict) -> Dict:
        """Get social spike monitor detailed status"""
        from app.services.social_spike_monitor import social_spike_monitor
        return await social_spike_monitor.get_status()
    
    async def _spike_coordinator_status(self, args: Dict) -> Dict:
        """Get spike coordinator detailed status"""
        from app.services.spike_coordinator import spike_coordinator
        return await spike_coordinator.get_status()
    
    # ========================================================================
    # ANALYTICS HANDLERS - GPT-5.1 Self-Evaluation Support
    # ========================================================================
    
    async def _analytics_history_latest(self, args: Dict) -> Dict:
        """
        Get latest signal history for a symbol (GPT-5.1 optimized)
        
        Returns recent signal outcomes with quick performance metrics,
        ideal for GPT-5.1 historical context during signal generation.
        """
        from app.services.analytics_service import analytics_service
        
        symbol = args.get("symbol", "BTC").upper()
        limit = args.get("limit", 5)
        
        result = await analytics_service.get_latest_history(
            symbol=symbol,
            limit=limit
        )
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "symbol": symbol
            }
        
        return {
            "success": True,
            **result
        }
    
    async def _analytics_performance_symbol(self, args: Dict) -> Dict:
        """
        Get comprehensive performance metrics for a specific symbol
        
        Returns:
        - Overall win rate and ROI
        - Recent signal outcomes
        - Verdict effectiveness (CONFIRM/DOWNSIZE/SKIP)
        - Risk mode performance (REDUCED/NORMAL/AGGRESSIVE)
        - Interval performance breakdown (1h, 4h, 24h, 7d, 30d)
        """
        from app.services.analytics_service import analytics_service
        
        symbol = args.get("symbol", "BTC").upper()
        days = args.get("days", 30)
        limit = args.get("limit", 50)
        
        result = await analytics_service.get_symbol_performance(
            symbol=symbol,
            days_back=days,
            limit=limit
        )
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "symbol": symbol
            }
        
        return {
            "success": True,
            **result
        }
    
    async def _analytics_performance_summary(self, args: Dict) -> Dict:
        """
        Get overall performance summary across all symbols
        
        Returns:
        - Total signals and symbols tracked
        - Overall win rate and average ROI
        - Top performing symbols
        - Verdict effectiveness stats across all symbols
        - Risk mode effectiveness stats across all symbols
        """
        from app.services.analytics_service import analytics_service
        
        days = args.get("days", 30)
        
        result = await analytics_service.get_overall_summary(days_back=days)
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"]
            }
        
        return {
            "success": True,
            **result
        }

    # ========================================================================
    # SCALPING HANDLERS - Real-time Scalping Analysis
    # ========================================================================

    async def _scalping_analyze(self, args: Dict) -> Dict:
        """
        Complete scalping analysis with all data layers

        Includes: orderbook, liquidations, funding, volume delta,
        smart money, whale positions, sentiment, and more.
        """
        from app.api.routes_scalping import ScalpingAnalysisRequest, analyze_for_scalping

        # Map RPC args to request model
        symbol = args.get("symbol", "BTC").upper()
        mode = args.get("mode", "aggressive")

        request = ScalpingAnalysisRequest(
            symbol=symbol,
            mode=mode,
            include_smart_money=args.get("include_smart_money", True),
            include_whale_positions=args.get("include_whale_positions", True),
            include_fear_greed=args.get("include_fear_greed", True),
            include_coinapi=args.get("include_coinapi", True),
            include_sentiment=args.get("include_sentiment", True),
            gpt_mode=args.get("gpt_mode", True)  # Default True for GPT Actions
        )

        return await analyze_for_scalping(request)

    async def _scalping_quick(self, args: Dict) -> Dict:
        """
        Quick scalping check - critical layers only, no smart money
        Fast response (~8s) for rapid queries
        """
        from app.api.routes_scalping import quick_scalping_check

        symbol = args.get("symbol", "BTC").upper()
        return await quick_scalping_check(symbol)

    async def _scalping_info(self, args: Dict) -> Dict:
        """
        Get scalping engine information and capabilities
        """
        from app.api.routes_scalping import scalping_info

        return await scalping_info()


# Global dispatcher instance
rpc_dispatcher = RPCDispatcher()

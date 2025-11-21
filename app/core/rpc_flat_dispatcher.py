"""
Flat RPC Dispatcher - GPT Actions Compatible with Timeout Protection
Maps flat parameters to existing service handlers
"""
import os
import json
import time
import asyncio
import traceback
from typing import Dict, Any
from pydantic import BaseModel

from app.models.rpc_flat_models import FlatRPCResponse
from app.utils.operation_catalog import get_operation_metadata, OPERATION_CATALOG
from app.utils.logger import logger
from app.middleware.auto_optimizer import optimize_request
from app.utils.telegram_report_sender import telegram_report_sender


class FlatRPCDispatcher:
    """
    Unified RPC dispatcher with FLAT parameters for GPT Actions compatibility

    Converts flat parameters to the format expected by existing handlers
    
    ✅ NEW: Timeout protection for all operations
    ✅ NEW: Detailed error logging with context
    ✅ NEW: Graceful degradation on timeout
    """
    
    # Operation timeout configuration (seconds)
    DEFAULT_TIMEOUT = int(os.getenv("RPC_OPERATION_TIMEOUT", "30"))
    
    # Timeout overrides for specific operation types
    TIMEOUT_OVERRIDES = {
        # Signal generation (heavy operations)
        "signals.get": 45,
        "signals.debug": 45,
        
        # MSS operations (multi-coin scans with batching optimization)
        "mss.discover": 120,  # Increased: batched processing may take longer but won't timeout
        "mss.scan": 90,
        "mss.analyze": 45,
        
        # Smart Money operations (dynamic discovery + multi-timeframe analysis)
        "smart_money.scan": 180,  # Increased: 40 coins × 4s/coin = ~160s needed
        "smart_money.scan_auto": 180,
        "smart_money.discover": 120,
        
        # Smart Entry operations (confluence analysis)
        "smart_entry.analyze": 45,
        "smart_entry.analyze_batch": 60,
        "smart_entry.test": 30,
        "smart_entry.health": 30,
        
        # Coinglass aggregated endpoints (large datasets)
        "coinglass.liquidation.aggregated_history": 45,
        "coinglass.open_interest.aggregated_history": 45,
        "coinglass.orderbook.aggregated_history": 45,
        
        # CoinAPI dashboard (multiple endpoints)
        "coinapi.dashboard": 45,
        
        # LunarCrush comprehensive operations
        "lunarcrush.coins_rankings": 45,
        "lunarcrush.topic_trends": 45,
        
        # New listings (API-heavy)
        "new_listings.multi_exchange": 60,
        "new_listings.analyze": 60,
        
        # Backtesting (if implemented)
        "backtest.run": 180,
    }

    async def dispatch(self, request: BaseModel) -> FlatRPCResponse:
        """
        Dispatch operation with flat parameters, timeout protection, and error handling
        
        ✅ NEW: Wraps execution with asyncio.wait_for() for timeout protection
        ✅ NEW: Catches TimeoutError and returns user-friendly error
        ✅ NEW: Logs execution context for debugging

        Args:
            request: FlatInvokeRequest with flat parameters

        Returns:
            FlatRPCResponse with result
        """
        start_time = time.time()
        operation = request.operation

        # Check if operation exists
        if operation not in OPERATION_CATALOG:
            available = list(OPERATION_CATALOG.keys())[:20]
            return FlatRPCResponse(
                ok=False,
                operation=operation,
                error=f"Unknown operation '{operation}'. Available (showing 20/{len(OPERATION_CATALOG)}): {available}",
                meta={"total_operations": len(OPERATION_CATALOG)}
            )

        # Get metadata
        try:
            metadata = get_operation_metadata(operation)
        except ValueError as e:
            return FlatRPCResponse(
                ok=False,
                operation=operation,
                error=str(e)
            )

        # Convert flat request to args dict
        args = self._extract_args(request, metadata)
        
        # Extract send_telegram parameter before optimization
        send_telegram = args.pop("send_telegram", False)
        
        # ✅ NEW: Auto-optimize parameters to prevent timeout
        optimized_args, optimization_meta = optimize_request(operation, args, mode="safe")
        
        # Log optimization if applied
        if optimization_meta.get("optimized"):
            logger.info(
                f"🔧 Auto-optimized {operation}: "
                f"risk={optimization_meta.get('timeout_risk')}, "
                f"mode={optimization_meta.get('mode')}"
            )
        
        # Use optimized args
        args = optimized_args

        # Validate required arguments
        validation_error = self._validate_args(metadata, args)
        if validation_error:
            return FlatRPCResponse(
                ok=False,
                operation=operation,
                error=validation_error
            )

        # ✅ NEW: Get timeout for this operation
        timeout = self.TIMEOUT_OVERRIDES.get(operation, self.DEFAULT_TIMEOUT)

        # Execute operation with timeout protection
        try:
            # ✅ NEW: Wrap with asyncio.wait_for for timeout protection
            result = await asyncio.wait_for(
                self._execute_operation(operation, args),
                timeout=timeout
            )

            execution_time = time.time() - start_time

            # Build response meta
            response_meta = {
                "execution_time_ms": round(execution_time * 1000, 2),
                "namespace": metadata.namespace,
                "method": metadata.method,
                "path": metadata.path,
                "timeout_limit_s": timeout
            }
            
            # Add optimization info if parameters were optimized
            if optimization_meta.get("optimized"):
                response_meta["auto_optimized"] = True
                response_meta["optimization_mode"] = optimization_meta.get("mode")
                if optimization_meta.get("timeout_risk"):
                    response_meta["timeout_risk"] = optimization_meta.get("timeout_risk")
            
            # ✅ NEW: Send full report to Telegram if requested (GPT→Telegram Hybrid)
            if send_telegram and result:
                try:
                    symbol = args.get("symbol", "UNKNOWN")
                    
                    # 1. Send full analysis report to Telegram (signals.get)
                    if operation == "signals.get":
                        asyncio.create_task(
                            telegram_report_sender.send_full_analysis_report(symbol, result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "full_analysis"
                        logger.info(f"📱 Sending full analysis report for {symbol} to Telegram")
                    
                    # 2. Send funding rate report to Telegram
                    elif "funding_rate" in operation and "exchange_list" in operation:
                        asyncio.create_task(
                            telegram_report_sender.send_funding_rate_report(symbol, result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "funding_rate"
                        logger.info(f"📱 Sending funding rate report for {symbol} to Telegram")
                    
                    # 3. Send liquidation report to Telegram
                    elif "liquidations" in operation and "symbol" in operation:
                        asyncio.create_task(
                            telegram_report_sender.send_liquidation_report(symbol, result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "liquidations"
                        logger.info(f"📱 Sending liquidation report for {symbol} to Telegram")
                    
                    # 4. Send social analytics report to Telegram (LunarCrush)
                    elif operation in ["lunarcrush.coin", "lunarcrush.coin_comprehensive"]:
                        asyncio.create_task(
                            telegram_report_sender.send_social_analytics_report(symbol, result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "social_analytics"
                        logger.info(f"📱 Sending social analytics report for {symbol} to Telegram")
                    
                    # 5. Send whale activity report to Telegram (Long/Short Ratio)
                    elif "long_short_ratio" in operation:
                        asyncio.create_task(
                            telegram_report_sender.send_whale_activity_report(symbol, result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "whale_activity"
                        logger.info(f"📱 Sending whale activity report for {symbol} to Telegram")
                    
                    # 6. Send Smart Money Concept scan report to Telegram
                    elif operation == "smart_money.scan":
                        asyncio.create_task(
                            telegram_report_sender.send_smart_money_report(result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "smart_money"
                        logger.info(f"📱 Sending Smart Money scan report to Telegram")
                    
                    # 7. Send MSS discovery report to Telegram
                    elif operation == "mss.discover":
                        asyncio.create_task(
                            telegram_report_sender.send_mss_discovery_report(result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "mss_discovery"
                        logger.info(f"📱 Sending MSS discovery report to Telegram")

                    # ========== NEW: 8 Additional Operations ==========

                    # 8. Send market summary report to Telegram
                    elif operation == "market.summary":
                        asyncio.create_task(
                            telegram_report_sender.send_market_summary_report(result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "market_summary"
                        logger.info(f"📱 Sending market summary report to Telegram")

                    # 9. Send technical indicators report to Telegram (12 indicators)
                    elif operation.startswith("coinglass.indicators."):
                        indicator_name = operation.split(".")[-1]  # Extract indicator name (rsi, ma, etc.)
                        asyncio.create_task(
                            telegram_report_sender.send_indicators_report(indicator_name, symbol, result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "indicators"
                        response_meta["indicator"] = indicator_name
                        logger.info(f"📱 Sending {indicator_name.upper()} indicator report for {symbol} to Telegram")

                    # 10. Send LunarCrush trending discovery report to Telegram
                    elif operation in ["lunarcrush.topics_list", "lunarcrush.coins_discovery", "lunarcrush.coins_realtime"]:
                        asyncio.create_task(
                            telegram_report_sender.send_discovery_report(result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "trending_discovery"
                        logger.info(f"📱 Sending trending discovery report to Telegram")

                    # 11. Send smart money accumulation report to Telegram
                    elif operation == "smart_money.scan_accumulation":
                        asyncio.create_task(
                            telegram_report_sender.send_accumulation_report(result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "accumulation"
                        logger.info(f"📱 Sending whale accumulation report to Telegram")

                    # 12. Send MSS single coin analysis report to Telegram
                    elif operation == "mss.analyze":
                        asyncio.create_task(
                            telegram_report_sender.send_mss_analysis_report(symbol, result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "mss_analysis"
                        logger.info(f"📱 Sending MSS analysis for {symbol} to Telegram")

                    # 13. Send monitoring system status report to Telegram
                    elif operation in ["monitoring.status", "monitoring.check", "monitoring.health"]:
                        asyncio.create_task(
                            telegram_report_sender.send_monitoring_report(result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "monitoring"
                        logger.info(f"📱 Sending monitoring system report to Telegram")

                    # 14. Send spike detection report to Telegram
                    elif operation.startswith("spike."):
                        asyncio.create_task(
                            telegram_report_sender.send_spike_detection_report(result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "spike_detection"
                        logger.info(f"📱 Sending spike detection report to Telegram")

                    # 15. Send analytics/performance report to Telegram
                    elif operation.startswith("analytics."):
                        asyncio.create_task(
                            telegram_report_sender.send_analytics_report(result)
                        )
                        response_meta["telegram_sent"] = True
                        response_meta["telegram_report_type"] = "analytics"
                        logger.info(f"📱 Sending analytics report to Telegram")

                    else:
                        # Generic Telegram send for other operations (future support)
                        response_meta["telegram_sent"] = False
                        response_meta["telegram_note"] = "Operation not yet supported for Telegram reporting"
                        
                except Exception as telegram_error:
                    # Don't fail the whole request if Telegram fails
                    logger.warning(f"Failed to send Telegram report: {telegram_error}")
                    response_meta["telegram_sent"] = False
                    response_meta["telegram_error"] = str(telegram_error)

            return FlatRPCResponse(
                ok=True,
                operation=operation,
                data=result,
                meta=response_meta
            )
            
        except asyncio.TimeoutError:
            # ✅ NEW: Handle timeout gracefully
            execution_time = time.time() - start_time
            
            error_msg = (
                f"Operation timeout after {timeout}s. "
                f"The operation took too long to complete. "
            )
            
            # Add specific suggestions based on operation type
            suggestions = []
            if "scan" in operation or "discover" in operation:
                suggestions.append("Try reducing max_results parameter")
                suggestions.append("Use more specific filters to narrow the search")
            elif "history" in operation or "aggregated" in operation:
                suggestions.append("Try reducing the time range (limit parameter)")
                suggestions.append("Use a shorter interval (e.g., 1h instead of 1m)")
            else:
                suggestions.append("Try simplifying the request parameters")
            
            error_msg += f" Suggestions: {'; '.join(suggestions)}"
            
            # Log timeout for monitoring
            logger.info(f"⏱️  FLAT RPC TIMEOUT: {operation} after {timeout}s")
            logger.info(f"   Args: {json.dumps(args, indent=2, default=str)}")
            
            return FlatRPCResponse(
                ok=False,
                operation=operation,
                error=error_msg,
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace,
                    "timeout_limit_s": timeout,
                    "error_type": "TimeoutError",
                    "suggestions": suggestions
                }
            )
            
        except Exception as e:
            # ✅ IMPROVED: Better error logging with context
            execution_time = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Log detailed error for debugging
            logger.info(f"❌ FLAT RPC ERROR: {operation}")
            logger.info(f"   Error Type: {error_type}")
            logger.info(f"   Error Message: {error_msg}")
            logger.info(f"   Args: {json.dumps(args, indent=2, default=str)}")
            
            # Only log full stack trace for unexpected errors
            if error_type not in ["ValueError", "KeyError", "ValidationError"]:
                logger.info(f"   Stack Trace:\n{traceback.format_exc()}")

            return FlatRPCResponse(
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

    def _extract_args(self, request: BaseModel, metadata) -> Dict[str, Any]:
        """Extract arguments from flat request"""
        args = {}

        # System parameters that should only be included if explicitly set to non-default values
        system_params = {'debug', 'include_raw'}
        
        # Parameters only needed for specific operations (not Coinglass/LunarCrush indicators)
        signal_specific_params = {
            'mode',           # Only for signals.get
            'send_telegram',  # Only for smart entry/monitoring operations
            'min_confluence', # Only for smart entry operations
            'symbols',        # Only for batch operations
            'duration_minutes', 'priority', 'check_interval_seconds'  # Only for monitoring
        }

        # Extract all non-None fields except 'operation'
        for field_name in request.model_fields:
            if field_name == 'operation':
                continue

            value = getattr(request, field_name, None)
            
            # Skip system parameters if they are default values (False/None)
            if field_name in system_params:
                if value in (None, False):
                    continue
            
            # Skip signal-specific params for Coinglass/LunarCrush indicator operations
            if field_name in signal_specific_params:
                # ✅ EXCEPTION: Always allow send_telegram if True (GPT→Telegram Hybrid)
                if field_name == 'send_telegram' and value is True:
                    pass  # Don't skip, allow it through
                # Skip for Coinglass and LunarCrush operations (unless they explicitly need them)
                elif metadata.namespace in ['coinglass', 'lunarcrush']:
                    # Skip all signal-specific params for these namespaces (except send_telegram)
                    continue
                    
                # For other operations, only skip if it's a default value
                elif field_name == 'mode' and value == "aggressive":
                    continue
                elif field_name == 'send_telegram' and value is False:
                    continue
            
            # Skip None values
            if value is not None:
                args[field_name] = value

        return args

    def _validate_args(self, metadata, args: Dict) -> str:
        """Validate required arguments - returns error message or None"""
        if metadata.requires_symbol and not args.get("symbol"):
            return f"Missing required parameter 'symbol' for operation '{metadata.name}'. Example: {{\"operation\": \"{metadata.name}\", \"symbol\": \"BTC\"}}"

        if metadata.requires_topic and not args.get("topic"):
            return f"Missing required parameter 'topic' for operation '{metadata.name}'. Example: {{\"operation\": \"{metadata.name}\", \"topic\": \"bitcoin\"}}"

        if metadata.requires_asset and not args.get("asset"):
            return f"Missing required parameter 'asset' for operation '{metadata.name}'. Example: {{\"operation\": \"{metadata.name}\", \"asset\": \"BTC\"}}"

        if metadata.requires_exchange and not args.get("exchange"):
            return f"Missing required parameter 'exchange' for operation '{metadata.name}'. Example: {{\"operation\": \"{metadata.name}\", \"exchange\": \"Binance\"}}"

        return None

    async def _execute_operation(self, operation: str, args: Dict) -> Any:
        """Execute operation by routing to appropriate service"""

        # ===================================================================
        # SIGNALS & MARKET
        # ===================================================================
        if operation == "signals.get":
            from app.core.signal_engine import signal_engine
            symbol = args["symbol"]
            debug = args.get("debug", False)
            mode = args.get("mode", "aggressive")  # Support mode parameter (conservative/aggressive/ultra or 1/2/3)
            return await signal_engine.build_signal(symbol, debug=debug, mode=mode)

        elif operation == "market.get":
            from app.core.signal_engine import signal_engine
            symbol = args["symbol"]
            return await signal_engine.build_signal(symbol, debug=True)
        
        elif operation == "market.summary":
            from app.services.market_summary_service import market_summary_service
            return await market_summary_service.get_market_summary()

        # ===================================================================
        # COINGLASS - LIQUIDATIONS
        # ===================================================================
        elif operation == "coinglass.liquidations.symbol":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            exchange = args.get("exchange", "Binance")
            symbol = args.get("symbol", "BTC")
            # Fixed: Call get_liquidation_coin_list (same as REST endpoint)
            # This function was already fixed to use symbol.upper() instead of _normalize_symbol()
            return await coinglass_comprehensive.get_liquidation_coin_list(
                exchange=exchange,
                symbol=symbol
            )

        elif operation == "coinglass.liquidations.heatmap":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_liquidation_map(symbol=symbol)

        elif operation == "coinglass.liquidation.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # ✅ OPTIMIZATION: Apply default limit if not specified
            if "limit" not in args:
                args["limit"] = 20  # Prevent ResponseTooLargeError
            return await coinglass_comprehensive.get_liquidation_history(**args)

        elif operation == "coinglass.liquidation.order":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_liquidation_orders(**args)

        elif operation == "coinglass.liquidation.exchange_list":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            range_param = args.get("range", "1h")
            return await coinglass_comprehensive.get_liquidation_exchange_list(range=range_param)

        elif operation == "coinglass.liquidation.aggregated_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # ✅ OPTIMIZATION: Apply default limit if not specified
            if "limit" not in args:
                args["limit"] = 20
            return await coinglass_comprehensive.get_liquidation_aggregated_history(**args)

        # ===================================================================
        # COINGLASS - FUNDING RATE
        # ===================================================================
        elif operation == "coinglass.funding_rate.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            exchange = args.get("exchange", "Binance")
            symbol = args.get("symbol", "BTCUSDT")
            interval = args.get("interval", "1d")
            # ✅ OPTIMIZATION: Reduce default limit from 100 to 20
            limit = args.get("limit", 20)
            return await coinglass_comprehensive.get_funding_rate_history(
                exchange=exchange, symbol=symbol, interval=interval, limit=limit
            )

        elif operation == "coinglass.funding_rate.exchange_list":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_funding_rate_exchange_list(symbol)

        elif operation == "coinglass.funding_rate.accumulated_exchange_list":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_accumulated_funding_rate_exchange_list(**args)

        elif operation == "coinglass.funding_rate.oi_weight_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # ✅ OPTIMIZATION: Apply default limit if not specified
            if "limit" not in args:
                args["limit"] = 20
            return await coinglass_comprehensive.get_oi_weighted_funding_rate_history(**args)

        elif operation == "coinglass.funding_rate.vol_weight_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # ✅ OPTIMIZATION: Apply default limit if not specified
            if "limit" not in args:
                args["limit"] = 20
            return await coinglass_comprehensive.get_volume_weighted_funding_rate_history(**args)

        # ===================================================================
        # COINGLASS - OPEN INTEREST
        # ===================================================================
        elif operation == "coinglass.open_interest.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            exchange = args.get("exchange", "Binance")
            symbol = args.get("symbol", "BTCUSDT")
            interval = args.get("interval", "1d")
            # ✅ OPTIMIZATION: Reduce default limit from 100 to 20
            limit = args.get("limit", 20)
            unit = args.get("unit", "usd")
            return await coinglass_comprehensive.get_open_interest_history(
                exchange=exchange, symbol=symbol, interval=interval, limit=limit, unit=unit
            )

        elif operation == "coinglass.open_interest.exchange_list":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_oi_exchange_list(symbol)

        elif operation == "coinglass.open_interest.aggregated_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # ✅ OPTIMIZATION: Apply default limit if not specified
            if "limit" not in args:
                args["limit"] = 20
            return await coinglass_comprehensive.get_aggregated_oi_history(**args)

        elif operation == "coinglass.open_interest.aggregated_stablecoin_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # ✅ OPTIMIZATION: Apply default limit if not specified
            if "limit" not in args:
                args["limit"] = 20
            return await coinglass_comprehensive.get_aggregated_stablecoin_oi_history(**args)

        elif operation == "coinglass.open_interest.aggregated_coin_margin_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # ✅ OPTIMIZATION: Apply default limit if not specified
            if "limit" not in args:
                args["limit"] = 20
            return await coinglass_comprehensive.get_aggregated_coin_margin_oi_history(**args)

        elif operation == "coinglass.open_interest.exchange_history_chart":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # Filter to only accepted parameters
            filtered_args = {k: v for k, v in args.items() if k in ['symbol', 'range', 'unit']}
            return await coinglass_comprehensive.get_oi_exchange_history_chart(**filtered_args)

        # ===================================================================
        # COINGLASS - INDICATORS
        # ===================================================================
        elif operation == "coinglass.indicators.fear_greed":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_fear_greed_index()

        elif operation == "coinglass.indicators.rsi_list":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            limit = args.get("limit", 20)
            signal_filter = args.get("signal_filter")
            
            # Validate signal_filter (Pydantic already validates, but double-check for safety)
            if signal_filter and signal_filter.upper() not in ["OVERSOLD", "OVERBOUGHT", "NEUTRAL"]:
                return {
                    "success": False,
                    "error": f"Invalid signal_filter '{signal_filter}'. Must be one of: OVERSOLD, OVERBOUGHT, NEUTRAL"
                }
            
            return await coinglass_comprehensive.get_rsi_list(
                limit=limit,
                signal_filter=signal_filter
            )

        elif operation == "coinglass.indicators.rsi":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_rsi_indicator(**args)

        elif operation == "coinglass.indicators.ma":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_ma_indicator(**args)

        elif operation == "coinglass.indicators.ema":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_ema_indicator(**args)

        elif operation == "coinglass.indicators.bollinger":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_bollinger_bands(**args)

        elif operation == "coinglass.indicators.macd":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_macd_indicator(**args)

        elif operation == "coinglass.indicators.basis":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_basis_history(**args)

        elif operation == "coinglass.indicators.whale_index":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_whale_index(**args)

        elif operation == "coinglass.indicators.cgdi":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_cgdi_index()

        elif operation == "coinglass.indicators.cdri":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_cdri_index()

        elif operation == "coinglass.indicators.golden_ratio":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_golden_ratio_multiplier()

        # ===================================================================
        # COINGLASS - ORDERBOOK & WHALE
        # ===================================================================
        elif operation == "coinglass.orderbook.whale_walls":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            # Filter to only accepted parameters
            filtered_args = {k: v for k, v in args.items() if k in ['exchange', 'symbol']}
            return await coinglass_comprehensive.get_large_limit_orders(**filtered_args)

        elif operation == "coinglass.orderbook.whale_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_large_limit_order_history(**args)

        elif operation == "coinglass.orderbook.aggregated_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_orderbook_aggregated_history(**args)

        elif operation == "coinglass.orderbook.ask_bids_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_orderbook_ask_bids_history(**args)

        elif operation == "coinglass.orderbook.detailed_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_orderbook_detailed_history(**args)

        elif operation == "coinglass.chain.whale_transfers":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            limit = args.get("limit", 100)
            return await coinglass_comprehensive.get_chain_whale_transfers(limit=limit)

        elif operation == "coinglass.chain.exchange_flows":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            limit = args.get("limit", 100)
            return await coinglass_comprehensive.get_exchange_chain_transactions(limit=limit)

        # ===================================================================
        # COINGLASS - HYPERLIQUID
        # ===================================================================
        elif operation == "coinglass.hyperliquid.whale_alerts":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_hyperliquid_whale_alerts()

        elif operation == "coinglass.hyperliquid.whale_positions":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_hyperliquid_whale_positions()

        elif operation == "coinglass.hyperliquid.positions.symbol":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_hyperliquid_positions_by_symbol(symbol=symbol)

        # ===================================================================
        # COINGLASS - MARKET DATA
        # ===================================================================
        elif operation == "coinglass.markets":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_coins_markets()

        elif operation == "coinglass.markets.symbol":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_coins_markets(symbol=symbol)

        elif operation == "coinglass.dashboard.symbol":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_coins_markets(symbol=symbol)

        elif operation == "coinglass.supported_coins":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_supported_coins()

        elif operation == "coinglass.supported_exchanges":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_supported_exchanges()

        elif operation == "coinglass.exchanges":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_supported_exchange_pairs()

        # Removed: coinglass.perpetual_market.symbol (Deprecated - HTTP 404 from Coinglass API)

        elif operation == "coinglass.pairs_markets.symbol":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_pairs_markets(symbol=symbol)

        elif operation == "coinglass.price_change":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_coins_price_change()

        elif operation == "coinglass.price_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_price_history(**args)

        elif operation == "coinglass.delisted_pairs":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_delisted_pairs()

        # ===================================================================
        # COINGLASS - ADVANCED METRICS
        # ===================================================================
        elif operation == "coinglass.etf.flows":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            asset = args.get("asset", "BTC")
            return await coinglass_comprehensive.get_etf_flows(asset)

        elif operation == "coinglass.onchain.reserves":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_exchange_reserves(symbol)

        elif operation == "coinglass.long_short_ratio.account_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_top_long_short_account_ratio_history(**args)

        elif operation == "coinglass.long_short_ratio.position_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_top_long_short_position_ratio_history(**args)

        elif operation == "coinglass.net_position.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_net_position_history(**args)

        elif operation == "coinglass.options.open_interest":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_options_open_interest()

        elif operation == "coinglass.options.volume":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_options_volume()

        elif operation == "coinglass.volume.taker_buy_sell":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_taker_buy_sell_volume(**args)

        elif operation == "coinglass.taker_buy_sell.exchange_list":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_taker_buy_sell_volume_exchange_list(**args)

        elif operation == "coinglass.news.feed":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            limit = int(args.get("limit", 10))
            # Handle both boolean and string "true"/"false"
            include_content_raw = args.get("include_content", False)
            include_content = include_content_raw if isinstance(include_content_raw, bool) else str(include_content_raw).lower() == "true"
            return await coinglass_comprehensive.get_news_feed(limit=limit, include_content=include_content)

        elif operation == "coinglass.calendar.economic":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_economic_calendar()

        elif operation == "coinglass.index.bull_market_peak":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_bull_market_indicators()

        elif operation == "coinglass.index.rainbow_chart":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_rainbow_chart()

        elif operation == "coinglass.index.stock_to_flow":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_stock_to_flow()

        elif operation == "coinglass.borrow.interest_rate":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_borrow_interest_rate(**args)

        elif operation == "coinglass.exchange.assets":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            exchange = args.get("exchange", "Binance")
            return await coinglass_comprehensive.get_exchange_assets(exchange=exchange)

        # ===================================================================
        # SMART MONEY
        # ===================================================================
        elif operation == "smart_money.scan":
            from app.services.smart_money_service import smart_money_service
            min_acc = args.get("min_accumulation_score", 5)
            min_dist = args.get("min_distribution_score", 5)
            # FIX #3: Reduce default limit from 50 to 20 for faster response
            limit = args.get("limit", 20)  # Default 20 coins (was 50)
            coins_str = args.get("coins")
            coin_list = coins_str.split(",") if coins_str else None
            return await smart_money_service.scan_smart_money(
                min_accumulation_score=min_acc,
                min_distribution_score=min_dist,
                coins=coins_str,
                limit=limit
            )

        elif operation == "smart_money.scan_accumulation":
            from app.services.smart_money_service import smart_money_service
            min_score = args.get("min_accumulation_score", 7)
            return await smart_money_service.scan_smart_money(
                min_accumulation_score=min_score,
                min_distribution_score=10  # High threshold to filter out distribution
            )

        elif operation == "smart_money.analyze":
            from app.services.smart_money_service import smart_money_service
            symbol = args["symbol"]
            return await smart_money_service.analyze_any_coin(symbol)

        # ===================================================================
        # SMART ENTRY ENGINE
        # ===================================================================
        elif operation == "smart_entry.analyze":
            from app.services.smart_entry_engine import get_smart_entry_engine
            engine = get_smart_entry_engine()
            symbol = args["symbol"]
            timeframe = args.get("timeframe", "1h")
            send_telegram = args.get("send_telegram", False)
            
            recommendation = await engine.analyze_entry(symbol.upper(), timeframe)
            
            if not recommendation:
                return {"success": False, "error": f"Could not analyze {symbol}"}
            
            # Send Telegram alert if requested
            if send_telegram:
                try:
                    from app.services.telegram_notifier import TelegramNotifier
                    from app.services.pro_alert_formatter import get_pro_alert_formatter
                    
                    telegram = TelegramNotifier()
                    formatter = get_pro_alert_formatter()
                    alert_message = formatter.format_entry_alert(recommendation)
                    
                    await telegram.send_custom_alert(
                        title=f"{symbol} Smart Entry Analysis",
                        message=alert_message,
                        emoji="🎯"
                    )
                except Exception as e:
                    logger.warning(f"Failed to send Telegram alert: {e}")
            
            # Return formatted response
            return {
                "success": True,
                "data": {
                    "symbol": recommendation.symbol,
                    "direction": recommendation.direction.value,
                    "confluence": {
                        "score": recommendation.confluence_score.total_score,
                        "strength": recommendation.confluence_score.strength.value,
                        "signals_analyzed": recommendation.confluence_score.signals_analyzed,
                        "signals_bullish": recommendation.confluence_score.signals_bullish,
                        "signals_bearish": recommendation.confluence_score.signals_bearish,
                        "breakdown": recommendation.confluence_score.breakdown
                    },
                    "entry": {
                        "entry_zone_low": recommendation.entry_zone_low,
                        "entry_zone_high": recommendation.entry_zone_high,
                        "stop_loss": recommendation.stop_loss,
                        "take_profit_1": recommendation.take_profit_1,
                        "take_profit_2": recommendation.take_profit_2,
                        "take_profit_3": recommendation.take_profit_3
                    },
                    "risk_management": {
                        "risk_reward_ratio": recommendation.risk_reward_ratio,
                        "position_size_pct": recommendation.position_size_pct,
                        "urgency": recommendation.urgency
                    },
                    "reasoning": recommendation.reasoning
                }
            }

        elif operation == "smart_entry.analyze_batch":
            from app.services.smart_entry_engine import get_smart_entry_engine
            import asyncio
            
            engine = get_smart_entry_engine()
            symbols = args.get("symbols", [])
            timeframe = args.get("timeframe", "1h")
            min_confluence = args.get("min_confluence", 60)
            send_telegram = args.get("send_telegram", False)
            
            if not symbols or len(symbols) > 20:
                return {"success": False, "error": "Provide 1-20 symbols in symbols parameter"}
            
            # Analyze all symbols in parallel
            tasks = [engine.analyze_entry(symbol.upper(), timeframe) for symbol in symbols]
            recommendations = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter and sort results
            results = []
            for symbol, rec in zip(symbols, recommendations):
                if isinstance(rec, Exception) or not rec:
                    continue
                
                # Filter by min confluence
                if rec.confluence_score.total_score >= min_confluence:
                    results.append({
                        "symbol": rec.symbol,
                        "direction": rec.direction.value,
                        "confluence_score": rec.confluence_score.total_score,
                        "entry_zone_low": rec.entry_zone_low,
                        "entry_zone_high": rec.entry_zone_high,
                        "stop_loss": rec.stop_loss,
                        "take_profit_1": rec.take_profit_1,
                        "risk_reward_ratio": rec.risk_reward_ratio,
                        "position_size_pct": rec.position_size_pct,
                        "urgency": rec.urgency,
                        "top_reasons": rec.reasoning[:3]
                    })
            
            # Sort by confluence score
            results.sort(key=lambda x: x['confluence_score'], reverse=True)
            
            # Send best opportunity to Telegram if requested
            if send_telegram and results:
                try:
                    from app.services.telegram_notifier import TelegramNotifier
                    from app.services.pro_alert_formatter import get_pro_alert_formatter
                    
                    best = results[0]
                    best_rec = await engine.analyze_entry(best['symbol'], timeframe)
                    
                    if best_rec:
                        telegram = TelegramNotifier()
                        formatter = get_pro_alert_formatter()
                        alert_message = formatter.format_entry_alert(best_rec)
                        
                        await telegram.send_custom_alert(
                            title=f"🏆 Best Entry: {best['symbol']}",
                            message=alert_message,
                            emoji="🎯"
                        )
                except Exception as e:
                    logger.warning(f"Failed to send batch alert: {e}")
            
            return {
                "success": True,
                "data": {
                    "analyzed": len(symbols),
                    "opportunities": len(results),
                    "min_confluence": min_confluence,
                    "results": results
                }
            }

        elif operation == "smart_entry.test":
            from app.services.smart_entry_engine import get_smart_entry_engine
            from app.services.pro_alert_formatter import get_pro_alert_formatter
            
            engine = get_smart_entry_engine()
            symbol = args["symbol"]
            
            recommendation = await engine.analyze_entry(symbol.upper(), "1h")
            
            if not recommendation:
                return {"success": False, "error": f"Could not analyze {symbol}"}
            
            formatter = get_pro_alert_formatter()
            long_alert = formatter.format_entry_alert(recommendation)
            short_alert = formatter.format_short_alert(recommendation)
            
            return {
                "success": True,
                "data": {
                    "symbol": recommendation.symbol,
                    "direction": recommendation.direction.value,
                    "confluence_score": recommendation.confluence_score.total_score,
                    "telegram_preview": {
                        "full": long_alert,
                        "compact": short_alert
                    }
                }
            }

        elif operation == "smart_entry.health":
            from app.services.smart_entry_engine import get_smart_entry_engine
            
            try:
                engine = get_smart_entry_engine()
                test_rec = await engine.analyze_entry("BTCUSDT", "1h")
                
                if test_rec:
                    return {
                        "success": True,
                        "status": "healthy",
                        "message": f"Smart Entry Engine operational (test: BTC confluence {test_rec.confluence_score.total_score}%)"
                    }
                else:
                    return {
                        "success": True,
                        "status": "degraded",
                        "message": "Engine running but test analysis failed"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": str(e)
                }

        # ===================================================================
        # MSS
        # ===================================================================
        elif operation == "mss.discover":
            from app.services.mss_service import MSSService
            mss = MSSService()
            # Map GPT Action params to actual service params
            # ✅ CRITICAL FIX: Use phase1_discovery (fast) not scan_and_rank (slow)
            limit = args.get("max_results", 10)  # Increased back to 10 (Phase 1 is fast!)
            max_fdv = args.get("max_fdv_usd", 50000000)
            max_age = args.get("max_age_hours", 72)
            min_vol = args.get("min_volume_24h", 100000.0)
            
            # ✅ Phase 1 Discovery only (quick coin discovery from CoinGecko/Binance)
            # Does NOT do full MSS analysis - just discovery filters
            results = await mss.phase1_discovery(
                limit=limit,
                max_fdv_usd=max_fdv,
                max_age_hours=max_age,
                min_volume_24h=min_vol
            )
            return {"discovered_coins": results, "count": len(results)}

        elif operation == "mss.analyze":
            from app.services.mss_service import MSSService
            mss = MSSService()
            symbol = args["symbol"]
            # Method calculate_mss_score is the correct method
            return await mss.calculate_mss_score(symbol)

        elif operation == "mss.scan":
            from app.services.mss_service import MSSService
            mss = MSSService()
            # Map GPT Action params to actual service params
            # ✅ OPTIMIZED: Reduced default to 5 for faster response (batched processing)
            limit = args.get("max_results", 5)  # Changed from 10 to 5
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

        # ===================================================================
        # LUNARCRUSH
        # ===================================================================
        elif operation == "lunarcrush.coin":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args["symbol"]
            return await lunarcrush_comprehensive.get_coin_metrics(symbol)

        elif operation == "lunarcrush.coin_momentum":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args["symbol"]
            return await lunarcrush_comprehensive.analyze_social_momentum(symbol)

        elif operation == "lunarcrush.coin_change":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args["symbol"]
            interval = args.get("interval", "1d")
            return await lunarcrush_comprehensive.get_social_change(symbol, interval)

        elif operation == "lunarcrush.coins_discovery":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            min_galaxy = args.get("min_galaxy_score", 60)
            limit = args.get("limit", 20)
            return await lunarcrush_comprehensive.discover_coins(
                min_galaxy_score=min_galaxy,
                limit=limit
            )

        elif operation == "lunarcrush.topics_list":
            from app.services.lunarcrush_service import lunarcrush_service
            return await lunarcrush_service.get_topics_list()
        
        elif operation == "lunarcrush.coin_themes":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args["symbol"]
            return await lunarcrush_comprehensive.analyze_coin_themes(symbol)
        
        elif operation == "lunarcrush.news_feed":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args.get("symbol")
            limit = args.get("limit", 20)
            # Symbol is optional for news feed - can return all news if None
            return await lunarcrush_comprehensive.get_news_feed(symbol=symbol or "BTC", limit=limit)
        
        elif operation == "lunarcrush.community_activity":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args["symbol"]
            return await lunarcrush_comprehensive.get_community_activity(symbol)
        
        elif operation == "lunarcrush.influencer_activity":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args["symbol"]
            return await lunarcrush_comprehensive.get_influencer_activity(symbol)
        
        elif operation == "lunarcrush.coin_correlation":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args["symbol"]
            return await lunarcrush_comprehensive.get_coin_correlation(symbol)
        
        elif operation == "lunarcrush.market_pair":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args["symbol"]
            pair = args.get("pair", "USDT")
            return await lunarcrush_comprehensive.get_market_pair(symbol=symbol, pair=pair)
        
        elif operation == "lunarcrush.aggregates":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args.get("symbol")
            # Symbol is required for aggregates - use BTC as default
            return await lunarcrush_comprehensive.get_aggregates(symbol=symbol or "BTC")
        
        elif operation == "lunarcrush.topic_trends":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            return await lunarcrush_comprehensive.get_topic_trends()
        
        elif operation == "lunarcrush.coins_rankings":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            limit = args.get("limit", 100)
            sort = args.get("sort", "galaxy_score")
            return await lunarcrush_comprehensive.get_coins_rankings(limit=limit, sort=sort)
        
        elif operation == "lunarcrush.system_status":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            return await lunarcrush_comprehensive.get_system_status()
        
        elif operation == "lunarcrush.coin_time_series":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args.get("symbol")
            if not symbol:
                raise ValueError("Parameter 'symbol' is required for lunarcrush.coin_time_series")
            interval = args.get("interval", "1d")
            days_back = args.get("days_back", 30)
            return await lunarcrush_comprehensive.get_time_series(symbol=symbol, interval=interval, days_back=days_back)
        
        elif operation == "lunarcrush.topic":
            from app.services.lunarcrush_service import lunarcrush_service
            topic = args.get("topic")
            if not topic:
                raise ValueError("Parameter 'topic' is required for lunarcrush.topic")
            return await lunarcrush_service.get_topic_details(topic)
        
        elif operation == "lunarcrush.coins_realtime":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            limit = args.get("limit", 100)
            sort = args.get("sort", "social_volume")
            min_galaxy_score = args.get("min_galaxy_score")
            return await lunarcrush_comprehensive.get_coins_realtime(limit=limit, sort=sort, min_galaxy_score=min_galaxy_score)
        
        elif operation == "lunarcrush.coin_comprehensive":
            from app.services.lunarcrush_comprehensive_service import lunarcrush_comprehensive
            symbol = args.get("symbol")
            if not symbol:
                raise ValueError("Parameter 'symbol' is required for lunarcrush.coin_comprehensive")
            return await lunarcrush_comprehensive.get_coin_comprehensive(symbol)

        # ===================================================================
        # COINAPI
        # ===================================================================
        elif operation == "coinapi.quote":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            exchange = args.get("exchange", "BINANCE")
            return await coinapi_comprehensive.get_current_quote(symbol=symbol, exchange=exchange)

        elif operation == "coinapi.ohlcv.latest":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            period = args.get("period", "1HRS")
            exchange = args.get("exchange", "BINANCE")
            limit = args.get("limit", 100)
            return await coinapi_comprehensive.get_ohlcv_latest(symbol=symbol, period=period, exchange=exchange, limit=limit)
        
        elif operation == "coinapi.ohlcv.historical":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            period = args.get("period", "1HRS")
            days_back = args.get("days_back", 7)
            exchange = args.get("exchange", "BINANCE")
            return await coinapi_comprehensive.get_ohlcv_historical(symbol=symbol, period=period, days_back=days_back, exchange=exchange)

        elif operation == "coinapi.orderbook":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            exchange = args.get("exchange", "BINANCE")
            limit = args.get("limit", 20)
            return await coinapi_comprehensive.get_orderbook_depth(symbol=symbol, exchange=exchange, limit=limit)

        elif operation == "coinapi.trades":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            exchange = args.get("exchange", "BINANCE")
            limit = args.get("limit", 100)
            return await coinapi_comprehensive.get_recent_trades(symbol=symbol, exchange=exchange, limit=limit)
        
        elif operation == "coinapi.multi_exchange":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            exchanges = args.get("exchanges", ["BINANCE", "COINBASE", "KRAKEN"])
            return await coinapi_comprehensive.get_multi_exchange_prices(symbol=symbol, exchanges=exchanges)
        
        elif operation == "coinapi.dashboard":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            
            # Dashboard aggregates multiple CoinAPI endpoints with individual error isolation
            import asyncio
            
            results = await asyncio.gather(
                coinapi_comprehensive.get_ohlcv_latest(symbol=symbol, period="1HRS", limit=24),
                coinapi_comprehensive.get_orderbook_depth(symbol=symbol, limit=20),
                coinapi_comprehensive.get_recent_trades(symbol=symbol, limit=100),
                coinapi_comprehensive.get_current_quote(symbol=symbol),
                return_exceptions=True
            )
            
            ohlcv, orderbook, trades, quote = results
            
            # Helper to check if a result is successful
            # Returns True only if result is a dict with success=True or success is missing (default True)
            # Returns False for all Exceptions and dicts with success=False
            def is_successful(result):
                if isinstance(result, Exception):
                    return False
                if isinstance(result, dict):
                    # Explicit check: success must be True or missing
                    # If success=False, this is an API failure, return False
                    return result.get("success", True) is True
                # Non-dict, non-Exception results default to True
                return True
            
            # Helper to format errors with metadata
            def format_result(result, endpoint_name):
                if isinstance(result, Exception):
                    # Transport/network error
                    return {
                        "success": False,
                        "error": str(result),
                        "error_type": type(result).__name__,
                        "failure_mode": "exception",
                        "endpoint": endpoint_name
                    }
                elif isinstance(result, dict) and result.get("success") is False:
                    # API-level error (service returned success=False)
                    return {
                        **result,
                        "failure_mode": "api_error",
                        "endpoint": endpoint_name
                    }
                # Success case - preserve original result
                return result
            
            # Count successful endpoints (both exception and API failures count as failures)
            successful_count = sum(1 for r in results if is_successful(r))
            
            # CRITICAL: If ALL endpoints failed (either via exception OR success=False),
            # raise exception to ensure RPC ok=false
            # This handles both network outages AND API-level failures
            if successful_count == 0:
                error_details = {
                    "ohlcv": format_result(ohlcv, 'ohlcv.latest'),
                    "orderbook": format_result(orderbook, 'orderbook'),
                    "trades": format_result(trades, 'trades'),
                    "quote": format_result(quote, 'quote')
                }
                raise RuntimeError(
                    f"CoinAPI dashboard total failure for {symbol}: "
                    f"All 4 endpoints failed (0/{len(results)} successful). "
                    f"Error details: {json.dumps(error_details, indent=2)}"
                )
            
            # Return aggregated data with success metrics
            return {
                "success": True,
                "symbol": symbol,
                "endpoints_total": 4,
                "endpoints_successful": successful_count,
                "dashboard": {
                    "ohlcv": format_result(ohlcv, "ohlcv.latest"),
                    "orderbook": format_result(orderbook, "orderbook"),
                    "trades": format_result(trades, "trades"),
                    "quote": format_result(quote, "quote")
                },
                "source": "coinapi_dashboard"
            }
        
        elif operation == "coinapi.symbols":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            exchange_id = args.get("exchange_id")
            asset_id = args.get("asset_id")
            symbol_type = args.get("symbol_type")
            return await coinapi_comprehensive.get_symbols(
                exchange_id=exchange_id,
                asset_id=asset_id,
                symbol_type=symbol_type
            )
        
        elif operation == "coinapi.metrics":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            metric_id = args.get("metric_id", "DERIVATIVES_FUNDING_RATE_CURRENT")
            exchange = args.get("exchange", "BINANCEFTSC")
            historical = args.get("historical", False)
            time_start = args.get("time_start")
            time_end = args.get("time_end")
            limit = args.get("limit", 100)
            return await coinapi_comprehensive.get_metrics(
                metric_id=metric_id,
                symbol=symbol,
                exchange=exchange,
                historical=historical,
                time_start=time_start,
                time_end=time_end,
                limit=limit
            )

        # ===================================================================
        # NEW LISTINGS MONITOR
        # ===================================================================
        elif operation == "new_listings.binance":
            from app.services.binance_listings_monitor import BinanceListingsMonitor
            
            hours = args.get("hours", 72)
            include_stats = args.get("include_stats", True)
            
            monitor = BinanceListingsMonitor()
            try:
                if include_stats:
                    result = await monitor.detect_new_listings_with_stats(hours=hours)
                else:
                    result = await monitor.get_new_listings(hours=hours)
                
                return result
            finally:
                await monitor.close()

        # ===================================================================
        # HEALTH
        # ===================================================================
        elif operation == "health.check":
            return {
                "status": "healthy",
                "service": "CryptoSatX Flat RPC",
                "version": "3.0.0-flat",
                "operations_count": len(OPERATION_CATALOG),
                "gpt_actions_compatible": True
            }

        # ===================================================================
        # SPIKE DETECTION (PHASE 5)
        # ===================================================================
        elif operation == "spike.check_system":
            from app.api.routes_spike_gpt import check_spike_system
            return await check_spike_system()
        
        elif operation == "spike.recent_activity":
            from app.api.routes_spike_gpt import get_recent_spike_activity
            return await get_recent_spike_activity()
        
        elif operation == "spike.configuration":
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
        
        elif operation == "spike.explain":
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

        elif operation == "spike.monitor_coin":
            from app.api.routes_spike_gpt import monitor_coin_spikes
            symbol = args.get("symbol", "BTC")
            return await monitor_coin_spikes(symbol)

        elif operation == "spike.status":
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
        
        elif operation == "spike.health":
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
        
        elif operation == "spike.price_detector_status":
            from app.services.realtime_spike_detector import realtime_spike_detector
            return await realtime_spike_detector.get_status()
        
        elif operation == "spike.liquidation_detector_status":
            from app.services.liquidation_spike_detector import liquidation_spike_detector
            return await liquidation_spike_detector.get_status()
        
        elif operation == "spike.social_monitor_status":
            from app.services.social_spike_monitor import social_spike_monitor
            return await social_spike_monitor.get_status()
        
        elif operation == "spike.coordinator_status":
            from app.services.spike_coordinator import spike_coordinator
            return await spike_coordinator.get_status()

        # ===================================================================
        # ANALYTICS (GPT-5.1 Self-Evaluation)
        # ===================================================================
        elif operation == "analytics.history.latest":
            from app.services.analytics_service import analytics_service
            symbol = args.get("symbol", "BTC").upper()
            limit = args.get("limit", 5)
            result = await analytics_service.get_latest_history(symbol=symbol, limit=limit)
            if "error" in result:
                return {"success": False, "error": result["error"], "symbol": symbol}
            return {"success": True, **result}
        
        elif operation == "analytics.performance.symbol":
            from app.services.analytics_service import analytics_service
            symbol = args.get("symbol", "BTC").upper()
            days = args.get("days", 30)
            limit = args.get("limit", 50)
            result = await analytics_service.get_symbol_performance(symbol=symbol, days_back=days, limit=limit)
            if "error" in result:
                return {"success": False, "error": result["error"], "symbol": symbol}
            return {"success": True, **result}
        
        elif operation == "analytics.performance.summary":
            from app.services.analytics_service import analytics_service
            days = args.get("days", 30)
            result = await analytics_service.get_overall_summary(days_back=days)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, **result}

        # ===================================================================
        # FALLBACK - Operation not implemented yet
        # ===================================================================
        else:
            raise NotImplementedError(
                f"Operation '{operation}' is registered in catalog but handler not implemented yet. "
                f"Please add handler in _execute_operation method."
            )


# Global dispatcher instance
flat_rpc_dispatcher = FlatRPCDispatcher()

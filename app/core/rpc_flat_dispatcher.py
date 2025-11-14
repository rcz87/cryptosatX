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
        
        # MSS operations (multi-coin scans)
        "mss.discover": 60,
        "mss.scan": 60,
        "mss.analyze": 45,
        
        # Smart Money operations
        "smart_money.scan": 60,
        "smart_money.scan_auto": 60,
        "smart_money.discover": 60,
        
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

            return FlatRPCResponse(
                ok=True,
                operation=operation,
                data=result,
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace,
                    "method": metadata.method,
                    "path": metadata.path,
                    "timeout_limit_s": timeout
                }
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
            print(f"⏱️  FLAT RPC TIMEOUT: {operation} after {timeout}s")
            print(f"   Args: {json.dumps(args, indent=2, default=str)}")
            
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
            print(f"❌ FLAT RPC ERROR: {operation}")
            print(f"   Error Type: {error_type}")
            print(f"   Error Message: {error_msg}")
            print(f"   Args: {json.dumps(args, indent=2, default=str)}")
            
            # Only log full stack trace for unexpected errors
            if error_type not in ["ValueError", "KeyError", "ValidationError"]:
                print(f"   Stack Trace:\n{traceback.format_exc()}")

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

        # Extract all non-None fields except 'operation'
        for field_name in request.model_fields:
            if field_name == 'operation':
                continue

            value = getattr(request, field_name, None)
            
            # Skip system parameters if they are default values (False/None)
            if field_name in system_params:
                if value in (None, False):
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
            return await signal_engine.build_signal(symbol, debug=debug)

        elif operation == "market.get":
            from app.core.signal_engine import signal_engine
            symbol = args["symbol"]
            return await signal_engine.build_signal(symbol, debug=True)

        # ===================================================================
        # COINGLASS - LIQUIDATIONS
        # ===================================================================
        elif operation == "coinglass.liquidations.symbol":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            exchange = args.get("exchange", "Binance")
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_liquidation_coin_list(exchange=exchange, symbol=symbol)

        elif operation == "coinglass.liquidations.heatmap":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args.get("symbol", "BTC")
            return await coinglass_comprehensive.get_liquidation_map(symbol=symbol)

        elif operation == "coinglass.liquidation.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
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
            return await coinglass_comprehensive.get_liquidation_aggregated_history(**args)

        # ===================================================================
        # COINGLASS - FUNDING RATE
        # ===================================================================
        elif operation == "coinglass.funding_rate.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            exchange = args.get("exchange", "Binance")
            symbol = args.get("symbol", "BTCUSDT")
            interval = args.get("interval", "1d")
            limit = args.get("limit", 100)
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
            return await coinglass_comprehensive.get_oi_weighted_funding_rate_history(**args)

        elif operation == "coinglass.funding_rate.vol_weight_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_volume_weighted_funding_rate_history(**args)

        # ===================================================================
        # COINGLASS - OPEN INTEREST
        # ===================================================================
        elif operation == "coinglass.open_interest.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            exchange = args.get("exchange", "Binance")
            symbol = args.get("symbol", "BTCUSDT")
            interval = args.get("interval", "1d")
            limit = args.get("limit", 100)
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
            return await coinglass_comprehensive.get_aggregated_oi_history(**args)

        elif operation == "coinglass.open_interest.aggregated_stablecoin_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_aggregated_stablecoin_oi_history(**args)

        elif operation == "coinglass.open_interest.aggregated_coin_margin_history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
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
            return await coinglass_comprehensive.get_rsi_list()

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
            coins_str = args.get("coins")
            coin_list = coins_str.split(",") if coins_str else None
            return await smart_money_service.scan_smart_money(
                min_accumulation_score=min_acc,
                min_distribution_score=min_dist,
                coins=coins_str
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
            return await smart_money_service.analyze_coin(symbol)

        # ===================================================================
        # MSS
        # ===================================================================
        elif operation == "mss.discover":
            from app.services.mss_service import MSSService
            mss = MSSService()
            min_score = args.get("min_mss_score", 75)
            max_results = args.get("max_results", 10)
            return await mss.discover_high_potential(
                min_mss_score=min_score,
                max_results=max_results
            )

        elif operation == "mss.analyze":
            from app.services.mss_service import MSSService
            mss = MSSService()
            symbol = args["symbol"]
            include_raw = args.get("include_raw", False)
            return await mss.analyze_coin(symbol, include_raw=include_raw)

        elif operation == "mss.scan":
            from app.services.mss_service import MSSService
            mss = MSSService()
            min_score = args.get("min_mss_score", 60)
            max_results = args.get("max_results", 20)
            return await mss.scan_market(
                min_mss_score=min_score,
                max_results=max_results
            )

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
            return await lunarcrush_comprehensive.get_news_feed(symbol=symbol, limit=limit)
        
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
            return await lunarcrush_comprehensive.get_aggregates(symbol=symbol)
        
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
        # FALLBACK - Operation not implemented yet
        # ===================================================================
        else:
            raise NotImplementedError(
                f"Operation '{operation}' is registered in catalog but handler not implemented yet. "
                f"Please add handler in _execute_operation method."
            )


# Global dispatcher instance
flat_rpc_dispatcher = FlatRPCDispatcher()

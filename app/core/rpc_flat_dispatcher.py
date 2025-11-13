"""
Flat RPC Dispatcher - GPT Actions Compatible
Maps flat parameters to existing service handlers
"""
import time
from typing import Dict, Any
from pydantic import BaseModel

from app.models.rpc_flat_models import FlatRPCResponse
from app.utils.operation_catalog import get_operation_metadata, OPERATION_CATALOG


class FlatRPCDispatcher:
    """
    Unified RPC dispatcher with FLAT parameters for GPT Actions compatibility

    Converts flat parameters to the format expected by existing handlers
    """

    async def dispatch(self, request: BaseModel) -> FlatRPCResponse:
        """
        Dispatch operation with flat parameters

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

        # Execute operation
        try:
            result = await self._execute_operation(operation, args)

            execution_time = time.time() - start_time

            return FlatRPCResponse(
                ok=True,
                operation=operation,
                data=result,
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace,
                    "method": metadata.method,
                    "path": metadata.path
                }
            )
        except Exception as e:
            execution_time = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)

            return FlatRPCResponse(
                ok=False,
                operation=operation,
                error=f"{error_type}: {error_msg}",
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace
                }
            )

    def _extract_args(self, request: BaseModel, metadata) -> Dict[str, Any]:
        """Extract arguments from flat request"""
        args = {}

        # Extract all non-None fields except 'operation'
        for field_name in request.model_fields:
            if field_name == 'operation':
                continue

            value = getattr(request, field_name, None)
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
            from app.services.coinglass_service import coinglass_service
            symbol = args.get("symbol", "BTC")
            time_type = args.get("time_type", "h24")
            return await coinglass_service.get_liquidations(symbol, time_type)

        elif operation == "coinglass.liquidations.heatmap":
            from app.services.coinglass_service import coinglass_service
            symbol = args["symbol"]
            return await coinglass_service.get_liquidation_heatmap(symbol)

        elif operation == "coinglass.liquidation.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_liquidation_history(**args)

        # ===================================================================
        # COINGLASS - FUNDING RATE
        # ===================================================================
        elif operation == "coinglass.funding_rate.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_funding_rate_history(**args)

        elif operation == "coinglass.funding_rate.exchange_list":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args["symbol"]
            return await coinglass_comprehensive.get_funding_rate_exchange_list(symbol)

        # ===================================================================
        # COINGLASS - OPEN INTEREST
        # ===================================================================
        elif operation == "coinglass.open_interest.history":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_open_interest_history(**args)

        elif operation == "coinglass.open_interest.exchange_list":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args["symbol"]
            return await coinglass_comprehensive.get_oi_exchange_list(symbol)

        # ===================================================================
        # COINGLASS - INDICATORS
        # ===================================================================
        elif operation == "coinglass.indicators.fear_greed":
            from app.services.coinglass_service import coinglass_service
            return await coinglass_service.get_fear_greed_index()

        elif operation == "coinglass.indicators.rsi_list":
            from app.services.coinglass_service import coinglass_service
            return await coinglass_service.get_rsi_list()

        elif operation == "coinglass.indicators.whale_index":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_whale_index(**args)

        # ===================================================================
        # COINGLASS - ORDERBOOK & WHALE
        # ===================================================================
        elif operation == "coinglass.orderbook.whale_walls":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_large_limit_orders(**args)

        elif operation == "coinglass.chain.whale_transfers":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_chain_whale_transfers(**args)

        # ===================================================================
        # COINGLASS - MARKET DATA
        # ===================================================================
        elif operation == "coinglass.markets":
            from app.services.coinglass_service import coinglass_service
            symbol = args.get("symbol")
            return await coinglass_service.get_markets(symbol)

        elif operation == "coinglass.supported_coins":
            from app.services.coinglass_service import coinglass_service
            return await coinglass_service.get_supported_coins()

        elif operation == "coinglass.exchanges":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            return await coinglass_comprehensive.get_exchanges()

        elif operation == "coinglass.perpetual_market.symbol":
            from app.services.coinglass_comprehensive_service import coinglass_comprehensive
            symbol = args["symbol"]
            return await coinglass_comprehensive.get_perpetual_market(symbol)

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
            from app.services.lunarcrush_service import lunarcrush_service
            symbol = args["symbol"]
            return await lunarcrush_service.get_coin_metrics(symbol)

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
            from app.services.lunarcrush_service import lunarcrush_service
            min_galaxy = args.get("min_galaxy_score", 60)
            limit = args.get("limit", 20)
            return await lunarcrush_service.discover_coins(
                min_galaxy_score=min_galaxy,
                limit=limit
            )

        elif operation == "lunarcrush.topics_list":
            from app.services.lunarcrush_service import lunarcrush_service
            return await lunarcrush_service.get_topics_list()

        # ===================================================================
        # COINAPI
        # ===================================================================
        elif operation == "coinapi.quote":
            from app.services.coinapi_service import coinapi_service
            symbol = args["symbol"]
            return await coinapi_service.get_quote(symbol)

        elif operation == "coinapi.ohlcv.latest":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            interval = args.get("interval", "1HRS")
            limit = args.get("limit", 100)
            return await coinapi_comprehensive.get_ohlcv_latest(symbol, interval, limit)

        elif operation == "coinapi.orderbook":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            depth = args.get("limit", 20)
            return await coinapi_comprehensive.get_orderbook_depth(symbol, depth)

        elif operation == "coinapi.trades":
            from app.services.coinapi_comprehensive_service import coinapi_comprehensive
            symbol = args["symbol"]
            limit = args.get("limit", 100)
            return await coinapi_comprehensive.get_recent_trades(symbol, limit)

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

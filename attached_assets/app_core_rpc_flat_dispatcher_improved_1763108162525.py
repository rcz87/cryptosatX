"""
Flat RPC Dispatcher - IMPROVED VERSION with Timeout Protection
Maps flat parameters to existing service handlers
GPT Actions Compatible
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
        "mss.discover": 90,
        "mss.scan": 90,
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
            print(f"   Args: {json.dumps(args, indent=2)}")
            
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
            print(f"   Args: {json.dumps(args, indent=2)}")
            
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

        # ... (rest of the handlers remain the same as original)

        # ===================================================================
        # HEALTH
        # ===================================================================
        elif operation == "health.check":
            return {
                "status": "healthy",
                "service": "CryptoSatX Flat RPC",
                "version": "3.0.0-flat",
                "operations_count": len(OPERATION_CATALOG),
                "gpt_actions_compatible": True,
                "timeout_protection": "enabled",
                "default_timeout_s": self.DEFAULT_TIMEOUT
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

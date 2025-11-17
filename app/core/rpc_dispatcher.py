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
        "backtest.run": 120,  # Backtesting can take longer
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
        """Get liquidations for symbol - FIXED arg passing"""
        from app.services.coinglass_comprehensive_service import coinglass_comprehensive
        symbol = args.get("symbol", "BTC")
        exchange = args.get("exchange", "Binance")
        interval = args.get("interval", "h1")
        return await coinglass_comprehensive.get_liquidation_history(
            exchange=exchange,
            symbol=symbol,
            interval=interval
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
        return await smart_money_service.scan_markets(
            min_accumulation_score=min_acc,
            min_distribution_score=min_dist,
            coins=coin_list
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


# Global dispatcher instance
rpc_dispatcher = RPCDispatcher()

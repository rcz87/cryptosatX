"""
RPC Dispatcher - FIXED VERSION
Maps operation names to service-layer callables with proper validation
"""
import time
from typing import Dict, Any, Callable
from pydantic import ValidationError

from app.utils.operation_catalog import get_operation_metadata
from app.models.rpc_models import RPCResponse, SymbolArgs


class RPCDispatcher:
    """
    Unified RPC dispatcher - maps operations to service functions
    Follows architect guidance: service-layer callables with Pydantic validation
    """
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """Register operation handlers - CORRECTED with proper service imports"""
        
        # Core Signals
        self.handlers["signals.get"] = self._signals_get
        self.handlers["market.get"] = self._market_get
        
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
        Dispatch operation with validation and error handling
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
        
        # Execute handler
        try:
            handler = self.handlers[operation]
            result = await handler(args)
            
            execution_time = time.time() - start_time
            
            return RPCResponse(
                ok=True,
                operation=operation,
                data=result,
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace
                }
            )
        except Exception as e:
            execution_time = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)
            
            return RPCResponse(
                ok=False,
                operation=operation,
                error=f"{error_type}: {error_msg}",
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace
                }
            )
    
    def _validate_args(self, metadata, args: Dict) -> str:
        """Validate required arguments - returns error message or None"""
        if metadata.requires_symbol and not args.get("symbol"):
            return "Missing required argument: symbol"
        if metadata.requires_topic and not args.get("topic"):
            return "Missing required argument: topic"
        if metadata.requires_asset and not args.get("asset"):
            return "Missing required argument: asset"
        if metadata.requires_exchange and not args.get("exchange"):
            return "Missing required argument: exchange"
        return None
    
    # ========================================================================
    # HANDLER IMPLEMENTATIONS - FIXED with proper imports and arg handling
    # ========================================================================
    
    async def _signals_get(self, args: Dict) -> Dict:
        """Get trading signal - FIXED"""
        from app.core.signal_engine import signal_engine
        symbol = args["symbol"]
        debug = args.get("debug", False)
        return await signal_engine.build_signal(symbol, debug=debug)
    
    async def _market_get(self, args: Dict) -> Dict:
        """Get market data - uses signal engine's internal aggregation"""
        from app.core.signal_engine import signal_engine
        symbol = args["symbol"]
        # Signal engine internally aggregates market data
        return await signal_engine.build_signal(symbol, debug=True)
    
    async def _coinglass_markets(self, args: Dict) -> Dict:
        """Get Coinglass markets"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        return await coinglass_service.get_markets()
    
    async def _coinglass_liquidations_symbol(self, args: Dict) -> Dict:
        """Get liquidations for symbol - FIXED arg passing"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        symbol = args.pop("symbol")  # Remove from args to avoid duplicate
        return await coinglass_service.get_liquidations_by_symbol(symbol, **args)
    
    async def _coinglass_funding_rate_history(self, args: Dict) -> Dict:
        """Get funding rate history"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        return await coinglass_service.get_funding_rate_history(**args)
    
    async def _coinglass_open_interest_history(self, args: Dict) -> Dict:
        """Get open interest history"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        return await coinglass_service.get_open_interest_history(**args)
    
    async def _coinglass_fear_greed(self, args: Dict) -> Dict:
        """Get Fear & Greed Index"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        return await coinglass_service.get_indicators_fear_greed()
    
    async def _coinglass_rsi_list(self, args: Dict) -> Dict:
        """Get RSI list"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        return await coinglass_service.get_indicators_rsi_list()
    
    async def _coinglass_supported_coins(self, args: Dict) -> Dict:
        """Get supported coins"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        return await coinglass_service.get_supported_coins()
    
    async def _smart_money_scan(self, args: Dict) -> Dict:
        """Scan smart money - FIXED"""
        from app.services.smart_money_service import smart_money_service
        min_acc = args.get("min_accumulation_score", 5)
        min_dist = args.get("min_distribution_score", 5)
        coins_str = args.get("coins")
        return await smart_money_service.scan_all(
            min_accumulation_score=min_acc,
            min_distribution_score=min_dist,
            coins=coins_str
        )
    
    async def _smart_money_scan_accumulation(self, args: Dict) -> Dict:
        """Scan accumulation"""
        from app.services.smart_money_service import smart_money_service
        min_score = args.get("min_score", 6)
        return await smart_money_service.scan_accumulation(min_score=min_score)
    
    async def _smart_money_scan_distribution(self, args: Dict) -> Dict:
        """Scan distribution"""
        from app.services.smart_money_service import smart_money_service
        min_score = args.get("min_score", 6)
        return await smart_money_service.scan_distribution(min_score=min_score)
    
    async def _smart_money_analyze(self, args: Dict) -> Dict:
        """Analyze smart money - FIXED"""
        from app.services.smart_money_service import smart_money_service
        symbol = args["symbol"]
        return await smart_money_service.analyze_coin(symbol)
    
    async def _mss_discover(self, args: Dict) -> Dict:
        """MSS discover"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        min_score = args.get("min_mss_score", 70)
        max_results = args.get("max_results", 10)
        return await mss.discover_high_potential(
            min_mss_score=min_score,
            max_results=max_results
        )
    
    async def _mss_analyze(self, args: Dict) -> Dict:
        """MSS analyze - FIXED"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        symbol = args["symbol"]
        include_raw = args.get("include_raw", False)
        return await mss.analyze_coin(symbol, include_raw=include_raw)
    
    async def _mss_scan(self, args: Dict) -> Dict:
        """MSS scan"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        min_score = args.get("min_mss_score", 60)
        max_results = args.get("max_results", 20)
        return await mss.scan_market(
            min_mss_score=min_score,
            max_results=max_results
        )
    
    async def _lunarcrush_coin(self, args: Dict) -> Dict:
        """Get LunarCrush coin data - FIXED"""
        from app.services.lunarcrush_service import lunarcrush_service
        symbol = args["symbol"]
        return await lunarcrush_service.get_coin_metrics(symbol)
    
    async def _lunarcrush_coins_discovery(self, args: Dict) -> Dict:
        """LunarCrush coins discovery"""
        from app.services.lunarcrush_service import lunarcrush_service
        min_galaxy = args.get("min_galaxy_score", 50)
        limit = args.get("limit", 20)
        return await lunarcrush_service.discover_coins(
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
            "operations_count": len(self.handlers)
        }


# Global dispatcher instance
rpc_dispatcher = RPCDispatcher()

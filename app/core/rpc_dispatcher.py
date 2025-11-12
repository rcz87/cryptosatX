"""
RPC Dispatcher
Maps operation names to service-layer callables
Reuses existing services for dependency resolution
"""
import time
from typing import Dict, Any, Callable, Optional
from fastapi import HTTPException

from app.utils.operation_catalog import get_operation_metadata, get_all_operations
from app.models.rpc_models import RPCResponse


class RPCDispatcher:
    """
    Unified RPC dispatcher that maps operations to service functions
    Follows hybrid approach: explicit service registration with metadata validation
    """
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self._register_all_handlers()
    
    def _register_all_handlers(self):
        """Register all operation handlers to service functions"""
        
        # Signals operations
        self.handlers["signals.get"] = self._handle_signal_get
        self.handlers["signals.debug"] = self._handle_signal_debug
        self.handlers["market.get"] = self._handle_market_get
        
        # Coinglass operations
        self.handlers["coinglass.markets"] = self._handle_coinglass_markets
        self.handlers["coinglass.markets.symbol"] = self._handle_coinglass_markets_symbol
        self.handlers["coinglass.liquidation.order"] = self._handle_coinglass_liquidation_order
        self.handlers["coinglass.liquidation.exchange_list"] = self._handle_coinglass_liquidation_exchange_list
        self.handlers["coinglass.liquidation.aggregated_history"] = self._handle_coinglass_liquidation_aggregated_history
        self.handlers["coinglass.liquidation.history"] = self._handle_coinglass_liquidation_history
        self.handlers["coinglass.liquidations.symbol"] = self._handle_coinglass_liquidations_symbol
        self.handlers["coinglass.liquidations.heatmap"] = self._handle_coinglass_liquidations_heatmap
        self.handlers["coinglass.funding_rate.history"] = self._handle_coinglass_funding_rate_history
        self.handlers["coinglass.funding_rate.exchange_list"] = self._handle_coinglass_funding_rate_exchange_list
        self.handlers["coinglass.open_interest.history"] = self._handle_coinglass_open_interest_history
        self.handlers["coinglass.open_interest.exchange_list"] = self._handle_coinglass_open_interest_exchange_list
        self.handlers["coinglass.indicators.rsi"] = self._handle_coinglass_indicators_rsi
        self.handlers["coinglass.indicators.rsi_list"] = self._handle_coinglass_indicators_rsi_list
        self.handlers["coinglass.indicators.fear_greed"] = self._handle_coinglass_indicators_fear_greed
        self.handlers["coinglass.supported_coins"] = self._handle_coinglass_supported_coins
        self.handlers["coinglass.exchanges"] = self._handle_coinglass_exchanges
        
        # Smart Money operations
        self.handlers["smart_money.scan"] = self._handle_smart_money_scan
        self.handlers["smart_money.scan_accumulation"] = self._handle_smart_money_scan_accumulation
        self.handlers["smart_money.scan_distribution"] = self._handle_smart_money_scan_distribution
        self.handlers["smart_money.analyze"] = self._handle_smart_money_analyze
        self.handlers["smart_money.info"] = self._handle_smart_money_info
        
        # MSS operations
        self.handlers["mss.discover"] = self._handle_mss_discover
        self.handlers["mss.analyze"] = self._handle_mss_analyze
        self.handlers["mss.scan"] = self._handle_mss_scan
        self.handlers["mss.info"] = self._handle_mss_info
        self.handlers["mss.history"] = self._handle_mss_history
        self.handlers["mss.top_scores"] = self._handle_mss_top_scores
        
        # LunarCrush operations
        self.handlers["lunarcrush.coin"] = self._handle_lunarcrush_coin
        self.handlers["lunarcrush.coin_momentum"] = self._handle_lunarcrush_coin_momentum
        self.handlers["lunarcrush.coin_change"] = self._handle_lunarcrush_coin_change
        self.handlers["lunarcrush.coins_discovery"] = self._handle_lunarcrush_coins_discovery
        
        # CoinAPI operations
        self.handlers["coinapi.ohlcv.latest"] = self._handle_coinapi_ohlcv_latest
        self.handlers["coinapi.orderbook"] = self._handle_coinapi_orderbook
        self.handlers["coinapi.quote"] = self._handle_coinapi_quote
        
        # SMC operations
        self.handlers["smc.analyze"] = self._handle_smc_analyze
        self.handlers["smc.info"] = self._handle_smc_info
        
        # Health operations
        self.handlers["health.check"] = self._handle_health_check
        self.handlers["health.root"] = self._handle_health_root
        
        # New Listings operations
        self.handlers["new_listings.binance"] = self._handle_new_listings_binance
        self.handlers["new_listings.analyze"] = self._handle_new_listings_analyze
        
        # Narratives operations
        self.handlers["narratives.discover_realtime"] = self._handle_narratives_discover_realtime
        self.handlers["narratives.coin"] = self._handle_narratives_coin
        
        # History operations
        self.handlers["history.signals"] = self._handle_history_signals
        self.handlers["history.statistics"] = self._handle_history_statistics
    
    async def dispatch(self, operation: str, args: Dict[str, Any]) -> RPCResponse:
        """
        Dispatch operation to appropriate handler
        
        Args:
            operation: Operation name (e.g., 'signals.get')
            args: Operation arguments
        
        Returns:
            RPCResponse with operation result
        """
        start_time = time.time()
        
        # Validate operation exists
        if operation not in self.handlers:
            return RPCResponse(
                ok=False,
                operation=operation,
                error=f"Unknown operation: {operation}. Available operations: {len(self.handlers)}"
            )
        
        # Get operation metadata
        try:
            metadata = get_operation_metadata(operation)
        except ValueError as e:
            return RPCResponse(
                ok=False,
                operation=operation,
                error=str(e)
            )
        
        # Validate required arguments
        if metadata.requires_symbol and "symbol" not in args:
            return RPCResponse(
                ok=False,
                operation=operation,
                error="Missing required argument: symbol"
            )
        if metadata.requires_topic and "topic" not in args:
            return RPCResponse(
                ok=False,
                operation=operation,
                error="Missing required argument: topic"
            )
        if metadata.requires_asset and "asset" not in args:
            return RPCResponse(
                ok=False,
                operation=operation,
                error="Missing required argument: asset"
            )
        if metadata.requires_exchange and "exchange" not in args:
            return RPCResponse(
                ok=False,
                operation=operation,
                error="Missing required argument: exchange"
            )
        
        # Execute handler
        try:
            handler = self.handlers[operation]
            data = await handler(args)
            
            execution_time = time.time() - start_time
            
            return RPCResponse(
                ok=True,
                operation=operation,
                data=data,
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace,
                    "method": metadata.method
                }
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return RPCResponse(
                ok=False,
                operation=operation,
                error=f"{type(e).__name__}: {str(e)}",
                meta={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "namespace": metadata.namespace
                }
            )
    
    # ============================================================================
    # HANDLER IMPLEMENTATIONS - Service Layer Wrappers
    # ============================================================================
    
    async def _handle_signal_get(self, args: Dict) -> Dict:
        """Get trading signal"""
        from app.core.signal_engine import signal_engine
        symbol = args["symbol"]
        debug = args.get("debug", False)
        result = await signal_engine.generate_signal(symbol, debug=debug)
        return result
    
    async def _handle_signal_debug(self, args: Dict) -> Dict:
        """Get debug premium data"""
        from app.core.signal_engine import signal_engine
        symbol = args["symbol"]
        result = await signal_engine.generate_signal(symbol, debug=True)
        return result
    
    async def _handle_market_get(self, args: Dict) -> Dict:
        """Get market data"""
        from app.services.market_aggregator import market_aggregator
        symbol = args["symbol"]
        result = await market_aggregator.get_aggregated_data(symbol)
        return result
    
    async def _handle_coinglass_markets(self, args: Dict) -> Dict:
        """Get all markets from Coinglass"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_markets()
        return result
    
    async def _handle_coinglass_markets_symbol(self, args: Dict) -> Dict:
        """Get market data for symbol from Coinglass"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        symbol = args["symbol"]
        result = await coinglass_service.get_market_by_symbol(symbol)
        return result
    
    async def _handle_coinglass_liquidation_order(self, args: Dict) -> Dict:
        """Get liquidation orders"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_liquidation_order(
            **args
        )
        return result
    
    async def _handle_coinglass_liquidation_exchange_list(self, args: Dict) -> Dict:
        """Get liquidation exchange list"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_liquidation_exchange_list(
            **args
        )
        return result
    
    async def _handle_coinglass_liquidation_aggregated_history(self, args: Dict) -> Dict:
        """Get aggregated liquidation history"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_liquidation_aggregated_history(
            **args
        )
        return result
    
    async def _handle_coinglass_liquidation_history(self, args: Dict) -> Dict:
        """Get liquidation history"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_liquidation_history(
            **args
        )
        return result
    
    async def _handle_coinglass_liquidations_symbol(self, args: Dict) -> Dict:
        """Get liquidations for symbol"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        symbol = args["symbol"]
        result = await coinglass_service.get_liquidations_by_symbol(symbol)
        return result
    
    async def _handle_coinglass_liquidations_heatmap(self, args: Dict) -> Dict:
        """Get liquidation heatmap"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        symbol = args["symbol"]
        result = await coinglass_service.get_liquidation_heatmap(symbol)
        return result
    
    async def _handle_coinglass_funding_rate_history(self, args: Dict) -> Dict:
        """Get funding rate history"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_funding_rate_history(
            **args
        )
        return result
    
    async def _handle_coinglass_funding_rate_exchange_list(self, args: Dict) -> Dict:
        """Get funding rate exchange list"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        symbol = args["symbol"]
        result = await coinglass_service.get_funding_rate_exchange_list(symbol, **args)
        return result
    
    async def _handle_coinglass_open_interest_history(self, args: Dict) -> Dict:
        """Get open interest history"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_open_interest_history(
            **args
        )
        return result
    
    async def _handle_coinglass_open_interest_exchange_list(self, args: Dict) -> Dict:
        """Get open interest exchange list"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        symbol = args["symbol"]
        result = await coinglass_service.get_open_interest_exchange_list(symbol, **args)
        return result
    
    async def _handle_coinglass_indicators_rsi(self, args: Dict) -> Dict:
        """Get RSI indicator"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_indicators_rsi(
            **args
        )
        return result
    
    async def _handle_coinglass_indicators_rsi_list(self, args: Dict) -> Dict:
        """Get RSI list for all coins"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_indicators_rsi_list()
        return result
    
    async def _handle_coinglass_indicators_fear_greed(self, args: Dict) -> Dict:
        """Get Fear & Greed Index"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_indicators_fear_greed()
        return result
    
    async def _handle_coinglass_supported_coins(self, args: Dict) -> Dict:
        """Get supported coins"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_supported_coins()
        return result
    
    async def _handle_coinglass_exchanges(self, args: Dict) -> Dict:
        """Get exchanges"""
        from app.services.coinglass_comprehensive_service import coinglass_service
        result = await coinglass_service.get_exchanges()
        return result
    
    async def _handle_smart_money_scan(self, args: Dict) -> Dict:
        """Scan smart money activity"""
        from app.services.smart_money_service import smart_money_service
        result = await smart_money_service.scan_all(
            min_accumulation_score=args.get("min_accumulation_score", 5),
            min_distribution_score=args.get("min_distribution_score", 5),
            coins=args.get("coins")
        )
        return result
    
    async def _handle_smart_money_scan_accumulation(self, args: Dict) -> Dict:
        """Scan accumulation patterns"""
        from app.services.smart_money_service import smart_money_service
        result = await smart_money_service.scan_accumulation(
            min_score=args.get("min_score", 6)
        )
        return result
    
    async def _handle_smart_money_scan_distribution(self, args: Dict) -> Dict:
        """Scan distribution patterns"""
        from app.services.smart_money_service import smart_money_service
        result = await smart_money_service.scan_distribution(
            min_score=args.get("min_score", 6)
        )
        return result
    
    async def _handle_smart_money_analyze(self, args: Dict) -> Dict:
        """Analyze smart money for symbol"""
        from app.services.smart_money_service import smart_money_service
        symbol = args["symbol"]
        result = await smart_money_service.analyze_coin(symbol)
        return result
    
    async def _handle_smart_money_info(self, args: Dict) -> Dict:
        """Get smart money scanner info"""
        return {
            "service": "Smart Money Scanner",
            "version": "2.0",
            "features": [
                "Whale accumulation detection",
                "Distribution pattern analysis",
                "Multi-factor scoring (0-10)",
                "Supports 50+ major cryptocurrencies"
            ]
        }
    
    async def _handle_mss_discover(self, args: Dict) -> Dict:
        """Discover high-potential cryptocurrencies"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        result = await mss.discover_high_potential(
            min_mss_score=args.get("min_mss_score", 70),
            max_results=args.get("max_results", 10)
        )
        return result
    
    async def _handle_mss_analyze(self, args: Dict) -> Dict:
        """Analyze MSS for symbol"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        symbol = args["symbol"]
        result = await mss.analyze_coin(symbol, include_raw=args.get("include_raw", False))
        return result
    
    async def _handle_mss_scan(self, args: Dict) -> Dict:
        """Scan cryptocurrencies with MSS"""
        from app.services.mss_service import MSSService
        mss = MSSService()
        result = await mss.scan_market(
            min_mss_score=args.get("min_mss_score", 60),
            max_results=args.get("max_results", 20)
        )
        return result
    
    async def _handle_mss_info(self, args: Dict) -> Dict:
        """Get MSS system info"""
        return {
            "service": "Multi-Modal Signal Score (MSS) Alpha System",
            "version": "3.0",
            "description": "3-phase weighted analysis for discovering high-potential cryptocurrencies before retail adoption",
            "phases": {
                "phase1": "Discovery - Tokenomics filtering",
                "phase2": "Social Confirmation - Community momentum analysis",
                "phase3": "Institutional Validation - Whale positioning verification"
            },
            "tiers": {
                "diamond": "MSS ≥ 80 (Exceptional potential)",
                "gold": "MSS 65-79 (Strong potential)",
                "silver": "MSS 50-64 (Moderate potential)"
            }
        }
    
    async def _handle_mss_history(self, args: Dict) -> Dict:
        """Get MSS signal history"""
        from app.storage.database import db
        result = await db.get_mss_history(
            limit=args.get("limit", 50)
        )
        return {"history": result}
    
    async def _handle_mss_top_scores(self, args: Dict) -> Dict:
        """Get top MSS scores"""
        from app.storage.database import db
        result = await db.get_top_mss_scores(
            limit=args.get("limit", 10)
        )
        return {"top_scores": result}
    
    async def _handle_lunarcrush_coin(self, args: Dict) -> Dict:
        """Get LunarCrush coin data"""
        from app.services.lunarcrush_service import lunarcrush_service
        symbol = args["symbol"]
        result = await lunarcrush_service.get_coin_metrics(symbol)
        return result
    
    async def _handle_lunarcrush_coin_momentum(self, args: Dict) -> Dict:
        """Get coin momentum"""
        from app.services.lunarcrush_service import lunarcrush_service
        symbol = args["symbol"]
        result = await lunarcrush_service.get_coin_momentum(symbol)
        return result
    
    async def _handle_lunarcrush_coin_change(self, args: Dict) -> Dict:
        """Get coin change metrics"""
        from app.services.lunarcrush_service import lunarcrush_service
        symbol = args["symbol"]
        result = await lunarcrush_service.get_coin_change(symbol)
        return result
    
    async def _handle_lunarcrush_coins_discovery(self, args: Dict) -> Dict:
        """Discover coins via LunarCrush"""
        from app.services.lunarcrush_service import lunarcrush_service
        result = await lunarcrush_service.discover_coins(
            min_galaxy_score=args.get("min_galaxy_score", 50),
            limit=args.get("limit", 20)
        )
        return result
    
    async def _handle_coinapi_ohlcv_latest(self, args: Dict) -> Dict:
        """Get latest OHLCV data"""
        from app.services.coinapi_service import coinapi_service
        symbol = args["symbol"]
        result = await coinapi_service.get_ohlcv_latest(symbol)
        return result
    
    async def _handle_coinapi_orderbook(self, args: Dict) -> Dict:
        """Get orderbook snapshot"""
        from app.services.coinapi_service import coinapi_service
        symbol = args["symbol"]
        result = await coinapi_service.get_orderbook(symbol)
        return result
    
    async def _handle_coinapi_quote(self, args: Dict) -> Dict:
        """Get current quote"""
        from app.services.coinapi_service import coinapi_service
        symbol = args["symbol"]
        result = await coinapi_service.get_quote(symbol)
        return result
    
    async def _handle_smc_analyze(self, args: Dict) -> Dict:
        """Analyze Smart Money Concept"""
        from app.services.smc_service import smc_service
        symbol = args["symbol"]
        result = await smc_service.analyze(symbol)
        return result
    
    async def _handle_smc_info(self, args: Dict) -> Dict:
        """Get SMC info"""
        return {
            "service": "Smart Money Concept (SMC) Analyzer",
            "version": "2.0",
            "features": [
                "Break of Structure (BOS) detection",
                "Change of Character (CHoCH) identification",
                "Fair Value Gap (FVG) analysis",
                "Swing points detection",
                "Liquidity zones mapping"
            ]
        }
    
    async def _handle_health_check(self, args: Dict) -> Dict:
        """Health check"""
        return {
            "status": "healthy",
            "service": "CryptoSatX Enhanced Crypto Signal API",
            "version": "2.0.0"
        }
    
    async def _handle_health_root(self, args: Dict) -> Dict:
        """Root endpoint"""
        return {
            "message": "CryptoSatX - Enhanced Crypto Signal API",
            "version": "2.0.0",
            "docs": "/docs",
            "rpc_endpoint": "/invoke"
        }
    
    async def _handle_new_listings_binance(self, args: Dict) -> Dict:
        """Get Binance new listings"""
        from app.services.new_listings_service import new_listings_service
        result = await new_listings_service.get_binance_new_listings()
        return result
    
    async def _handle_new_listings_analyze(self, args: Dict) -> Dict:
        """Analyze new listings"""
        from app.services.new_listings_service import new_listings_service
        result = await new_listings_service.analyze_new_listings()
        return result
    
    async def _handle_narratives_discover_realtime(self, args: Dict) -> Dict:
        """Discover realtime narratives"""
        from app.services.narrative_service import narrative_service
        result = await narrative_service.discover_realtime_narratives(
            limit=args.get("limit", 10)
        )
        return result
    
    async def _handle_narratives_coin(self, args: Dict) -> Dict:
        """Get coin narratives"""
        from app.services.narrative_service import narrative_service
        symbol = args["symbol"]
        result = await narrative_service.get_coin_narratives(symbol)
        return result
    
    async def _handle_history_signals(self, args: Dict) -> Dict:
        """Get signal history"""
        from app.storage.database import db
        result = await db.get_signal_history(
            limit=args.get("limit", 50),
            signal_type=args.get("signal_type")
        )
        return {"signals": result}
    
    async def _handle_history_statistics(self, args: Dict) -> Dict:
        """Get signal statistics"""
        from app.storage.database import db
        result = await db.get_signal_statistics()
        return result


# Global dispatcher instance
rpc_dispatcher = RPCDispatcher()

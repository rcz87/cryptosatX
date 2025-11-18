"""
Operation Catalog Generator
Auto-generates operation enum and metadata from FastAPI routes
"""
from enum import Enum
from typing import Dict, List, Tuple, Callable, Any
from dataclasses import dataclass

@dataclass
class OperationMetadata:
    """Metadata for each operation"""
    name: str
    namespace: str
    path: str
    method: str
    description: str
    requires_symbol: bool = False
    requires_topic: bool = False
    requires_asset: bool = False
    requires_exchange: bool = False

OPERATION_CATALOG: Dict[str, OperationMetadata] = {
    "admin.weights.current": OperationMetadata("admin.weights.current", "admin", "/weights/current", "GET", "Get current signal weight configuration"),
    "admin.weights.update": OperationMetadata("admin.weights.update", "admin", "/weights/update", "POST", "Update signal weights"),
    "admin.weights.reset": OperationMetadata("admin.weights.reset", "admin", "/weights/reset", "POST", "Reset weights to default"),
    "admin.weights.history": OperationMetadata("admin.weights.history", "admin", "/weights/history", "GET", "Get weight adjustment history"),
    "admin.weights.performance": OperationMetadata("admin.weights.performance", "admin", "/weights/performance", "GET", "Get weight performance metrics"),
    "admin.weights.importance": OperationMetadata("admin.weights.importance", "admin", "/weights/importance", "GET", "Get feature importance scores"),
    "admin.ab_test.create": OperationMetadata("admin.ab_test.create", "admin", "/ab-test/create", "POST", "Create new A/B test"),
    "admin.ab_test.list": OperationMetadata("admin.ab_test.list", "admin", "/ab-test/list", "GET", "List all A/B tests"),
    "admin.auto_optimization.configure": OperationMetadata("admin.auto_optimization.configure", "admin", "/auto-optimization/configure", "POST", "Configure auto-optimization"),
    "admin.auto_optimization.run": OperationMetadata("admin.auto_optimization.run", "admin", "/auto-optimization/run", "POST", "Run auto-optimization"),
    "admin.dashboard": OperationMetadata("admin.dashboard", "admin", "/dashboard", "GET", "Get admin dashboard data"),
    "admin.system.health": OperationMetadata("admin.system.health", "admin", "/system/health", "GET", "Get system health metrics"),
    
    "analytics.summary": OperationMetadata("analytics.summary", "analytics", "/summary", "GET", "Get analytics summary"),
    "analytics.history.latest": OperationMetadata("analytics.history.latest", "analytics", "/history/latest", "GET", "Get latest signal history"),
    "analytics.history.symbol": OperationMetadata("analytics.history.symbol", "analytics", "/history/{symbol}", "GET", "Get signal history for symbol", requires_symbol=True),
    "analytics.history.date_range": OperationMetadata("analytics.history.date_range", "analytics", "/history/date-range", "GET", "Get history by date range"),
    "analytics.performance.symbol": OperationMetadata("analytics.performance.symbol", "analytics", "/performance/{symbol}", "GET", "Get performance metrics for symbol", requires_symbol=True),
    "analytics.stats.overview": OperationMetadata("analytics.stats.overview", "analytics", "/stats/overview", "GET", "Get statistics overview"),
    
    "coinapi.ohlcv.latest": OperationMetadata("coinapi.ohlcv.latest", "coinapi", "/ohlcv/{symbol}/latest", "GET", "Get latest OHLCV data", requires_symbol=True),
    "coinapi.ohlcv.historical": OperationMetadata("coinapi.ohlcv.historical", "coinapi", "/ohlcv/{symbol}/historical", "GET", "Get historical OHLCV data", requires_symbol=True),
    "coinapi.orderbook": OperationMetadata("coinapi.orderbook", "coinapi", "/orderbook/{symbol}", "GET", "Get orderbook snapshot", requires_symbol=True),
    "coinapi.trades": OperationMetadata("coinapi.trades", "coinapi", "/trades/{symbol}", "GET", "Get recent trades", requires_symbol=True),
    "coinapi.quote": OperationMetadata("coinapi.quote", "coinapi", "/quote/{symbol}", "GET", "Get current quote", requires_symbol=True),
    "coinapi.multi_exchange": OperationMetadata("coinapi.multi_exchange", "coinapi", "/multi-exchange/{symbol}", "GET", "Get multi-exchange aggregated data", requires_symbol=True),
    "coinapi.dashboard": OperationMetadata("coinapi.dashboard", "coinapi", "/dashboard/{symbol}", "GET", "Get CoinAPI dashboard", requires_symbol=True),
    
    "coinglass.markets": OperationMetadata("coinglass.markets", "coinglass", "/markets", "GET", "Get all markets"),
    "coinglass.markets.symbol": OperationMetadata("coinglass.markets.symbol", "coinglass", "/markets/{symbol}", "GET", "Get market data for symbol", requires_symbol=True),
    "coinglass.liquidation.order": OperationMetadata("coinglass.liquidation.order", "coinglass", "/liquidation/order", "GET", "Get liquidation orders"),
    "coinglass.liquidation.exchange_list": OperationMetadata("coinglass.liquidation.exchange_list", "coinglass", "/liquidation/exchange-list", "GET", "Get liquidation exchange list"),
    "coinglass.liquidation.aggregated_history": OperationMetadata("coinglass.liquidation.aggregated_history", "coinglass", "/liquidation/aggregated-history", "GET", "Get aggregated liquidation history"),
    "coinglass.liquidation.history": OperationMetadata("coinglass.liquidation.history", "coinglass", "/liquidation/history", "GET", "Get liquidation history"),
    "coinglass.orderbook.ask_bids_history": OperationMetadata("coinglass.orderbook.ask_bids_history", "coinglass", "/orderbook/ask-bids-history", "GET", "Get ask/bids history"),
    "coinglass.orderbook.aggregated_history": OperationMetadata("coinglass.orderbook.aggregated_history", "coinglass", "/orderbook/aggregated-history", "GET", "Get aggregated orderbook history"),
    "coinglass.orderbook.whale_walls": OperationMetadata("coinglass.orderbook.whale_walls", "coinglass", "/orderbook/whale-walls", "GET", "Get whale walls"),
    "coinglass.orderbook.whale_history": OperationMetadata("coinglass.orderbook.whale_history", "coinglass", "/orderbook/whale-history", "GET", "Get whale orderbook history"),
    "coinglass.orderbook.detailed_history": OperationMetadata("coinglass.orderbook.detailed_history", "coinglass", "/orderbook/detailed-history", "GET", "Get detailed orderbook history"),
    "coinglass.hyperliquid.whale_alerts": OperationMetadata("coinglass.hyperliquid.whale_alerts", "coinglass", "/hyperliquid/whale-alerts", "GET", "Get Hyperliquid whale alerts"),
    "coinglass.hyperliquid.whale_positions": OperationMetadata("coinglass.hyperliquid.whale_positions", "coinglass", "/hyperliquid/whale-positions", "GET", "Get Hyperliquid whale positions"),
    "coinglass.hyperliquid.positions.symbol": OperationMetadata("coinglass.hyperliquid.positions.symbol", "coinglass", "/hyperliquid/positions/{symbol}", "GET", "Get Hyperliquid positions for symbol", requires_symbol=True),
    "coinglass.chain.whale_transfers": OperationMetadata("coinglass.chain.whale_transfers", "coinglass", "/chain/whale-transfers", "GET", "Get on-chain whale transfers"),
    "coinglass.chain.exchange_flows": OperationMetadata("coinglass.chain.exchange_flows", "coinglass", "/chain/exchange-flows", "GET", "Get exchange inflows/outflows"),
    "coinglass.indicators.rsi_list": OperationMetadata("coinglass.indicators.rsi_list", "coinglass", "/indicators/rsi-list", "GET", "Get RSI list for all coins"),
    "coinglass.indicators.rsi": OperationMetadata("coinglass.indicators.rsi", "coinglass", "/indicators/rsi", "GET", "Get RSI indicator"),
    "coinglass.indicators.ma": OperationMetadata("coinglass.indicators.ma", "coinglass", "/indicators/ma", "GET", "Get Moving Average"),
    "coinglass.indicators.ema": OperationMetadata("coinglass.indicators.ema", "coinglass", "/indicators/ema", "GET", "Get Exponential Moving Average"),
    "coinglass.indicators.bollinger": OperationMetadata("coinglass.indicators.bollinger", "coinglass", "/indicators/bollinger", "GET", "Get Bollinger Bands"),
    "coinglass.indicators.macd": OperationMetadata("coinglass.indicators.macd", "coinglass", "/indicators/macd", "GET", "Get MACD indicator"),
    "coinglass.indicators.basis": OperationMetadata("coinglass.indicators.basis", "coinglass", "/indicators/basis", "GET", "Get Basis indicator"),
    "coinglass.indicators.whale_index": OperationMetadata("coinglass.indicators.whale_index", "coinglass", "/indicators/whale-index", "GET", "Get Whale Index"),
    "coinglass.indicators.cgdi": OperationMetadata("coinglass.indicators.cgdi", "coinglass", "/indicators/cgdi", "GET", "Get Coinglass Directional Index"),
    "coinglass.indicators.cdri": OperationMetadata("coinglass.indicators.cdri", "coinglass", "/indicators/cdri", "GET", "Get Coinglass Directional Relative Index"),
    "coinglass.indicators.golden_ratio": OperationMetadata("coinglass.indicators.golden_ratio", "coinglass", "/indicators/golden-ratio", "GET", "Get Golden Ratio"),
    "coinglass.indicators.fear_greed": OperationMetadata("coinglass.indicators.fear_greed", "coinglass", "/indicators/fear-greed", "GET", "Get Fear & Greed Index"),
    "coinglass.calendar.economic": OperationMetadata("coinglass.calendar.economic", "coinglass", "/calendar/economic", "GET", "Get economic calendar events"),
    "coinglass.news.feed": OperationMetadata("coinglass.news.feed", "coinglass", "/news/feed", "GET", "Get news feed"),
    "coinglass.volume.taker_buy_sell": OperationMetadata("coinglass.volume.taker_buy_sell", "coinglass", "/volume/taker-buy-sell", "GET", "Get taker buy/sell volume"),
    "coinglass.liquidations.symbol": OperationMetadata("coinglass.liquidations.symbol", "coinglass", "/liquidations/{symbol}", "GET", "Get liquidations for symbol", requires_symbol=True),
    "coinglass.liquidations.heatmap": OperationMetadata("coinglass.liquidations.heatmap", "coinglass", "/liquidations/{symbol}/heatmap", "GET", "Get liquidation heatmap", requires_symbol=True),
    # Removed: coinglass.perpetual_market.symbol (Deprecated - HTTP 404 from Coinglass API)
    "coinglass.price_change": OperationMetadata("coinglass.price_change", "coinglass", "/price-change", "GET", "Get price changes"),
    "coinglass.price_history": OperationMetadata("coinglass.price_history", "coinglass", "/price-history", "GET", "Get price history"),
    "coinglass.delisted_pairs": OperationMetadata("coinglass.delisted_pairs", "coinglass", "/delisted-pairs", "GET", "Get delisted pairs"),
    "coinglass.open_interest.history": OperationMetadata("coinglass.open_interest.history", "coinglass", "/open-interest/history", "GET", "Get open interest history"),
    "coinglass.open_interest.aggregated_history": OperationMetadata("coinglass.open_interest.aggregated_history", "coinglass", "/open-interest/aggregated-history", "GET", "Get aggregated OI history"),
    "coinglass.open_interest.aggregated_stablecoin_history": OperationMetadata("coinglass.open_interest.aggregated_stablecoin_history", "coinglass", "/open-interest/aggregated-stablecoin-history", "GET", "Get stablecoin OI history"),
    "coinglass.open_interest.aggregated_coin_margin_history": OperationMetadata("coinglass.open_interest.aggregated_coin_margin_history", "coinglass", "/open-interest/aggregated-coin-margin-history", "GET", "Get coin margin OI history"),
    "coinglass.open_interest.exchange_list": OperationMetadata("coinglass.open_interest.exchange_list", "coinglass", "/open-interest/exchange-list/{symbol}", "GET", "Get OI exchange list", requires_symbol=True),
    "coinglass.open_interest.exchange_history_chart": OperationMetadata("coinglass.open_interest.exchange_history_chart", "coinglass", "/open-interest/exchange-history-chart", "GET", "Get OI exchange history chart"),
    "coinglass.funding_rate.history": OperationMetadata("coinglass.funding_rate.history", "coinglass", "/funding-rate/history", "GET", "Get funding rate history"),
    "coinglass.funding_rate.oi_weight_history": OperationMetadata("coinglass.funding_rate.oi_weight_history", "coinglass", "/funding-rate/oi-weight-history", "GET", "Get OI-weighted funding rate"),
    "coinglass.funding_rate.vol_weight_history": OperationMetadata("coinglass.funding_rate.vol_weight_history", "coinglass", "/funding-rate/vol-weight-history", "GET", "Get volume-weighted funding rate"),
    "coinglass.funding_rate.exchange_list": OperationMetadata("coinglass.funding_rate.exchange_list", "coinglass", "/funding-rate/exchange-list/{symbol}", "GET", "Get funding rate exchange list", requires_symbol=True),
    "coinglass.funding_rate.accumulated_exchange_list": OperationMetadata("coinglass.funding_rate.accumulated_exchange_list", "coinglass", "/funding-rate/accumulated-exchange-list", "GET", "Get accumulated funding rate"),
    "coinglass.long_short_ratio.account_history": OperationMetadata("coinglass.long_short_ratio.account_history", "coinglass", "/top-long-short-account-ratio/history", "GET", "Get account ratio history"),
    "coinglass.long_short_ratio.position_history": OperationMetadata("coinglass.long_short_ratio.position_history", "coinglass", "/top-long-short-position-ratio/history", "GET", "Get position ratio history"),
    "coinglass.taker_buy_sell.exchange_list": OperationMetadata("coinglass.taker_buy_sell.exchange_list", "coinglass", "/taker-buy-sell-volume/exchange-list", "GET", "Get taker buy/sell exchange list"),
    "coinglass.net_position.history": OperationMetadata("coinglass.net_position.history", "coinglass", "/net-position/history", "GET", "Get net position history"),
    "coinglass.pairs_markets.symbol": OperationMetadata("coinglass.pairs_markets.symbol", "coinglass", "/pairs-markets/{symbol}", "GET", "Get pairs markets", requires_symbol=True),
    "coinglass.supported_coins": OperationMetadata("coinglass.supported_coins", "coinglass", "/supported-coins", "GET", "Get supported coins"),
    "coinglass.supported_exchanges": OperationMetadata("coinglass.supported_exchanges", "coinglass", "/supported-exchanges", "GET", "Get supported exchanges"),
    "coinglass.exchanges": OperationMetadata("coinglass.exchanges", "coinglass", "/exchanges", "GET", "Get exchanges"),
    "coinglass.options.open_interest": OperationMetadata("coinglass.options.open_interest", "coinglass", "/options/open-interest", "GET", "Get options open interest"),
    "coinglass.options.volume": OperationMetadata("coinglass.options.volume", "coinglass", "/options/volume", "GET", "Get options volume"),
    "coinglass.etf.flows": OperationMetadata("coinglass.etf.flows", "coinglass", "/etf/flows/{asset}", "GET", "Get ETF flows", requires_asset=True),
    "coinglass.onchain.reserves": OperationMetadata("coinglass.onchain.reserves", "coinglass", "/on-chain/reserves/{symbol}", "GET", "Get on-chain reserves", requires_symbol=True),
    "coinglass.index.bull_market_peak": OperationMetadata("coinglass.index.bull_market_peak", "coinglass", "/index/bull-market-peak", "GET", "Get bull market peak index"),
    "coinglass.index.rainbow_chart": OperationMetadata("coinglass.index.rainbow_chart", "coinglass", "/index/rainbow-chart", "GET", "Get rainbow chart"),
    "coinglass.index.stock_to_flow": OperationMetadata("coinglass.index.stock_to_flow", "coinglass", "/index/stock-to-flow", "GET", "Get stock-to-flow model"),
    "coinglass.borrow.interest_rate": OperationMetadata("coinglass.borrow.interest_rate", "coinglass", "/borrow/interest-rate", "GET", "Get borrow interest rates"),
    "coinglass.exchange.assets": OperationMetadata("coinglass.exchange.assets", "coinglass", "/exchange/assets/{exchange}", "GET", "Get exchange assets", requires_exchange=True),
    "coinglass.dashboard.symbol": OperationMetadata("coinglass.dashboard.symbol", "coinglass", "/dashboard/{symbol}", "GET", "Get Coinglass dashboard", requires_symbol=True),
    
    "signals.get": OperationMetadata("signals.get", "signals", "/signals/{symbol}", "GET", "Get trading signal for symbol", requires_symbol=True),
    "signals.debug": OperationMetadata("signals.debug", "signals", "/debug/premium/{symbol}", "GET", "Get debug premium data", requires_symbol=True),
    "market.get": OperationMetadata("market.get", "market", "/market/{symbol}", "GET", "Get market data for symbol", requires_symbol=True),
    "market.summary": OperationMetadata("market.summary", "market", "/market/summary", "GET", "Get overall market summary across major cryptocurrencies (BTC, ETH, SOL, XRP, BNB)"),
    
    "smart_money.scan": OperationMetadata("smart_money.scan", "smart_money", "/scan", "GET", "Scan smart money activity"),
    "smart_money.scan_accumulation": OperationMetadata("smart_money.scan_accumulation", "smart_money", "/scan/accumulation", "GET", "Scan accumulation patterns"),
    "smart_money.scan_distribution": OperationMetadata("smart_money.scan_distribution", "smart_money", "/scan/distribution", "GET", "Scan distribution patterns"),
    "smart_money.info": OperationMetadata("smart_money.info", "smart_money", "/info", "GET", "Get smart money scanner info"),
    "smart_money.analyze": OperationMetadata("smart_money.analyze", "smart_money", "/analyze/{symbol}", "GET", "Analyze smart money for symbol", requires_symbol=True),
    "smart_money.discover": OperationMetadata("smart_money.discover", "smart_money", "/discover", "GET", "Discover smart money opportunities"),
    "smart_money.futures_list": OperationMetadata("smart_money.futures_list", "smart_money", "/futures/list", "GET", "Get futures list"),
    "smart_money.scan_auto": OperationMetadata("smart_money.scan_auto", "smart_money", "/scan/auto", "GET", "Auto scan smart money"),
    
    "mss.discover": OperationMetadata("mss.discover", "mss", "/discover", "GET", "Discover high-potential cryptocurrencies"),
    "mss.analyze": OperationMetadata("mss.analyze", "mss", "/analyze/{symbol}", "GET", "Analyze MSS for symbol", requires_symbol=True),
    "mss.scan": OperationMetadata("mss.scan", "mss", "/scan", "GET", "Scan cryptocurrencies with MSS"),
    "mss.watch": OperationMetadata("mss.watch", "mss", "/watch/{symbol}", "GET", "Watch symbol with MSS", requires_symbol=True),
    "mss.info": OperationMetadata("mss.info", "mss", "/info", "GET", "Get MSS system info"),
    "mss.telegram_test": OperationMetadata("mss.telegram_test", "mss", "/telegram/test", "GET", "Test Telegram MSS notifications"),
    "mss.history": OperationMetadata("mss.history", "mss", "/history", "GET", "Get MSS signal history"),
    "mss.history_symbol": OperationMetadata("mss.history_symbol", "mss", "/history/{symbol}", "GET", "Get MSS history for symbol", requires_symbol=True),
    "mss.top_scores": OperationMetadata("mss.top_scores", "mss", "/top-scores", "GET", "Get top MSS scores"),
    "mss.analytics": OperationMetadata("mss.analytics", "mss", "/analytics", "GET", "Get MSS analytics"),
    
    "lunarcrush.coin": OperationMetadata("lunarcrush.coin", "lunarcrush", "/coin/{symbol}", "GET", "Get LunarCrush coin data", requires_symbol=True),
    "lunarcrush.coin_time_series": OperationMetadata("lunarcrush.coin_time_series", "lunarcrush", "/coin/{symbol}/time-series", "GET", "Get coin time series", requires_symbol=True),
    "lunarcrush.coin_change": OperationMetadata("lunarcrush.coin_change", "lunarcrush", "/coin/{symbol}/change", "GET", "Get coin change metrics", requires_symbol=True),
    "lunarcrush.coin_momentum": OperationMetadata("lunarcrush.coin_momentum", "lunarcrush", "/coin/{symbol}/momentum", "GET", "Get coin momentum", requires_symbol=True),
    "lunarcrush.coins_discovery": OperationMetadata("lunarcrush.coins_discovery", "lunarcrush", "/coins/discovery", "GET", "Discover coins via LunarCrush"),
    "lunarcrush.topics_list": OperationMetadata("lunarcrush.topics_list", "lunarcrush", "/topics/list", "GET", "Get trending topics list - discover viral crypto moments"),
    "lunarcrush.topic": OperationMetadata("lunarcrush.topic", "lunarcrush", "/topic/{topic}", "GET", "Get topic metrics", requires_topic=True),
    "lunarcrush.coin_themes": OperationMetadata("lunarcrush.coin_themes", "lunarcrush", "/coin/{symbol}/themes", "GET", "Analyze coin themes (AI-free) - detect bullish/bearish signals, sentiment, and risk", requires_symbol=True),
    "lunarcrush.news_feed": OperationMetadata("lunarcrush.news_feed", "lunarcrush", "/news/feed", "GET", "Get crypto news feed (Enterprise tier)"),
    "lunarcrush.community_activity": OperationMetadata("lunarcrush.community_activity", "lunarcrush", "/community/{symbol}", "GET", "Get community activity metrics", requires_symbol=True),
    "lunarcrush.influencer_activity": OperationMetadata("lunarcrush.influencer_activity", "lunarcrush", "/influencers/{symbol}", "GET", "Get influencer activity (Enterprise tier)", requires_symbol=True),
    "lunarcrush.coin_correlation": OperationMetadata("lunarcrush.coin_correlation", "lunarcrush", "/correlation/{symbol}", "GET", "Get coin correlation metrics", requires_symbol=True),
    "lunarcrush.market_pair": OperationMetadata("lunarcrush.market_pair", "lunarcrush", "/market-pair/{symbol}", "GET", "Get market pair data", requires_symbol=True),
    "lunarcrush.aggregates": OperationMetadata("lunarcrush.aggregates", "lunarcrush", "/aggregates", "GET", "Get aggregated market metrics"),
    "lunarcrush.topic_trends": OperationMetadata("lunarcrush.topic_trends", "lunarcrush", "/topics/trends", "GET", "Get trending topics"),
    "lunarcrush.coins_rankings": OperationMetadata("lunarcrush.coins_rankings", "lunarcrush", "/coins/rankings", "GET", "Get coins rankings"),
    "lunarcrush.system_status": OperationMetadata("lunarcrush.system_status", "lunarcrush", "/system/status", "GET", "Get API system status"),
    
    "narratives.discover_realtime": OperationMetadata("narratives.discover_realtime", "narratives", "/discover/realtime", "GET", "Discover realtime narratives"),
    "narratives.momentum": OperationMetadata("narratives.momentum", "narratives", "/momentum/{symbol}", "GET", "Get narrative momentum", requires_symbol=True),
    "narratives.timeseries": OperationMetadata("narratives.timeseries", "narratives", "/timeseries/{symbol}", "GET", "Get narrative timeseries", requires_symbol=True),
    "narratives.change": OperationMetadata("narratives.change", "narratives", "/change/{symbol}", "GET", "Get narrative changes", requires_symbol=True),
    "narratives.coin": OperationMetadata("narratives.coin", "narratives", "/coin/{symbol}", "GET", "Get coin narratives", requires_symbol=True),
    "narratives.info": OperationMetadata("narratives.info", "narratives", "/info", "GET", "Get narratives system info"),
    
    "new_listings.binance": OperationMetadata("new_listings.binance", "new_listings", "/new-listings/binance", "GET", "Get Binance new listings"),
    "new_listings.multi_exchange": OperationMetadata("new_listings.multi_exchange", "new_listings", "/new-listings/multi-exchange", "GET", "Get multi-exchange new listings"),
    "new_listings.region_bypass": OperationMetadata("new_listings.region_bypass", "new_listings", "/new-listings/region-bypass", "GET", "Get region-bypass listings"),
    "new_listings.analyze": OperationMetadata("new_listings.analyze", "new_listings", "/new-listings/analyze", "GET", "Analyze new listings"),
    "new_listings.watch": OperationMetadata("new_listings.watch", "new_listings", "/new-listings/watch", "GET", "Watch new listings"),
    
    "smc.analyze": OperationMetadata("smc.analyze", "smc", "/analyze/{symbol}", "GET", "Analyze Smart Money Concept", requires_symbol=True),
    "smc.info": OperationMetadata("smc.info", "smc", "/info", "GET", "Get SMC info"),
    
    "health.check": OperationMetadata("health.check", "health", "/health", "GET", "Health check"),
    "health.root": OperationMetadata("health.root", "health", "/", "GET", "Root endpoint"),
    
    "history.signals": OperationMetadata("history.signals", "history", "/signals", "GET", "Get signal history"),
    "history.statistics": OperationMetadata("history.statistics", "history", "/statistics", "GET", "Get signal statistics"),
    "history.clear": OperationMetadata("history.clear", "history", "/clear", "DELETE", "Clear signal history"),
    "history.info": OperationMetadata("history.info", "history", "/info", "GET", "Get history info"),
    
    "monitoring.start": OperationMetadata("monitoring.start", "monitoring", "/start", "POST", "Start monitoring"),
    "monitoring.stop": OperationMetadata("monitoring.stop", "monitoring", "/stop", "POST", "Stop monitoring"),
    "monitoring.status": OperationMetadata("monitoring.status", "monitoring", "/status", "GET", "Get monitoring status"),
    "monitoring.alerts": OperationMetadata("monitoring.alerts", "monitoring", "/alerts", "GET", "Get monitoring alerts"),
    "monitoring.symbols_add": OperationMetadata("monitoring.symbols_add", "monitoring", "/symbols/add", "POST", "Add symbols to monitor"),
    "monitoring.symbols_remove": OperationMetadata("monitoring.symbols_remove", "monitoring", "/symbols/{symbol}", "DELETE", "Remove symbol from monitoring", requires_symbol=True),
    "monitoring.config_update": OperationMetadata("monitoring.config_update", "monitoring", "/config", "PUT", "Update monitoring config"),
    "monitoring.check": OperationMetadata("monitoring.check", "monitoring", "/check/{symbol}", "POST", "Manual check symbol", requires_symbol=True),
    "monitoring.test_alert": OperationMetadata("monitoring.test_alert", "monitoring", "/test-alert/{symbol}", "POST", "Test alert for symbol", requires_symbol=True),
    "monitoring.health": OperationMetadata("monitoring.health", "monitoring", "/health", "GET", "Get monitoring health"),
    "monitoring.stats": OperationMetadata("monitoring.stats", "monitoring", "/stats", "GET", "Get monitoring statistics"),
    "monitoring.spike_monitor_status": OperationMetadata("monitoring.spike_monitor_status", "monitoring", "/spike-monitor/status", "GET", "Get spike monitor status"),
    "monitoring.spike_monitor_start": OperationMetadata("monitoring.spike_monitor_start", "monitoring", "/spike-monitor/start", "POST", "Start spike monitor"),
    "monitoring.spike_monitor_stop": OperationMetadata("monitoring.spike_monitor_stop", "monitoring", "/spike-monitor/stop", "POST", "Stop spike monitor"),

    # PHASE 5 - Real-Time Spike Detection System (GPT Actions)
    "spike.check_system": OperationMetadata("spike.check_system", "spike", "/gpt/spike-alerts/check-system", "GET", "Check if spike detection system is running - get real-time status of all detectors"),
    "spike.recent_activity": OperationMetadata("spike.recent_activity", "spike", "/gpt/spike-alerts/recent-activity", "GET", "Get recent spike detection activity - see what the system has been catching"),
    "spike.configuration": OperationMetadata("spike.configuration", "spike", "/gpt/spike-alerts/configuration", "GET", "View spike detection configuration - thresholds, intervals, and settings"),
    "spike.explain": OperationMetadata("spike.explain", "spike", "/gpt/spike-alerts/explain", "GET", "Explain spike detection system - get complete explanation of how it works"),
    "spike.monitor_coin": OperationMetadata("spike.monitor_coin", "spike", "/gpt/spike-alerts/monitor-coin/{symbol}", "GET", "Monitor real-time spike detection for specific coin - get current status and recent alerts", requires_symbol=True),

    # PHASE 5 - Detailed Spike Detection Status
    "spike.status": OperationMetadata("spike.status", "spike", "/spike-detection/status", "GET", "Get comprehensive spike detection system status - all detectors and metrics"),
    "spike.health": OperationMetadata("spike.health", "spike", "/spike-detection/health", "GET", "Quick health check - are all spike detectors running?"),
    "spike.price_detector_status": OperationMetadata("spike.price_detector_status", "spike", "/spike-detection/price-detector/status", "GET", "Get price spike detector status - monitoring >8% moves in 5min"),
    "spike.liquidation_detector_status": OperationMetadata("spike.liquidation_detector_status", "spike", "/spike-detection/liquidation-detector/status", "GET", "Get liquidation spike detector status - monitoring >$50M cascades"),
    "spike.social_monitor_status": OperationMetadata("spike.social_monitor_status", "spike", "/spike-detection/social-monitor/status", "GET", "Get social spike monitor status - monitoring viral moments"),
    "spike.coordinator_status": OperationMetadata("spike.coordinator_status", "spike", "/spike-detection/coordinator/status", "GET", "Get spike coordinator status - multi-signal correlation engine"),

    "openai.analyze": OperationMetadata("openai.analyze", "openai", "/analyze/{symbol}", "GET", "OpenAI analysis for symbol", requires_symbol=True),
    "openai.sentiment_market": OperationMetadata("openai.sentiment_market", "openai", "/sentiment/market", "GET", "Get market sentiment via OpenAI"),
    "openai.validate": OperationMetadata("openai.validate", "openai", "/validate/{symbol}", "POST", "Validate signal via OpenAI", requires_symbol=True),
    "openai.config": OperationMetadata("openai.config", "openai", "/config", "GET", "Get OpenAI config"),
    "openai.health": OperationMetadata("openai.health", "openai", "/health", "GET", "Get OpenAI health"),
}


def get_all_operations() -> List[str]:
    """Get list of all operation names"""
    return list(OPERATION_CATALOG.keys())


def get_operation_metadata(operation: str) -> OperationMetadata:
    """Get metadata for an operation"""
    if operation not in OPERATION_CATALOG:
        raise ValueError(f"Unknown operation: {operation}")
    return OPERATION_CATALOG[operation]


def get_operations_by_namespace(namespace: str) -> List[str]:
    """Get all operations in a namespace"""
    return [
        op for op, meta in OPERATION_CATALOG.items()
        if meta.namespace == namespace
    ]

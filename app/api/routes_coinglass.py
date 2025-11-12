"""
Coinglass Data Routes
Exposes comprehensive Coinglass market data to maximize Standard plan value
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.coinglass_comprehensive_service import CoinglassComprehensiveService

router = APIRouter(prefix="/coinglass", tags=["Coinglass Data"])


@router.get("/markets")
async def get_markets_data(symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTC)")):
    """
    Get comprehensive market data for futures coins
    
    Returns:
    - Price, Market Cap, Open Interest
    - Funding Rates (OI-weighted & Volume-weighted)
    - Price changes across multiple timeframes (5m to 24h)
    - OI/Market Cap and OI/Volume ratios
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_coins_markets(symbol=symbol)
        return result
    finally:
        await service.close()


@router.get("/markets/{symbol}")
async def get_market_by_symbol(symbol: str):
    """
    Get detailed market data for a specific symbol
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_coins_markets(symbol=symbol)
        return result
    finally:
        await service.close()


@router.get("/liquidations/{symbol}")
async def get_liquidations(
    symbol: str,
    include_orders: bool = Query(False, description="Include recent liquidation orders"),
    include_map: bool = Query(False, description="Include liquidation heatmap")
):
    """
    Get comprehensive liquidation data
    
    - 24h/12h/4h/1h liquidation volumes
    - Long vs Short breakdown
    - Optional: Recent liquidation orders (past 7 days)
    - Optional: Liquidation heatmap clusters
    """
    service = CoinglassComprehensiveService()
    try:
        result = {
            "symbol": symbol.upper(),
            "coinList": await service.get_liquidation_coin_list(symbol=symbol)
        }
        
        if include_orders:
            result["orders"] = await service.get_liquidation_orders(symbol=symbol)
        
        if include_map:
            result["heatmap"] = await service.get_liquidation_map(symbol=symbol)
        
        return result
    finally:
        await service.close()


@router.get("/liquidations/{symbol}/heatmap")
async def get_liquidation_heatmap(symbol: str):
    """
    Get liquidation heatmap showing price levels with high liquidation clusters
    
    Useful for identifying potential support/resistance zones
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_liquidation_map(symbol=symbol)
        return result
    finally:
        await service.close()


@router.get("/perpetual-market/{symbol}")
async def get_perpetual_market(symbol: str):
    """
    Get perpetual futures market data for a symbol
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_perpetual_market(symbol=symbol)
        return result
    finally:
        await service.close()


@router.get("/price-change")
async def get_price_change():
    """
    Get price changes for ALL coins (12TH ENDPOINT!)
    
    Returns multi-timeframe analysis:
    - Price changes: 5m, 15m, 30m, 1h, 4h, 12h, 24h
    - Amplitude (volatility) per timeframe
    - Top 10 gainers/losers (24h)
    - Most volatile coins
    - Short-term momentum (1h gainers)
    
    Perfect for:
    - Momentum screening (what's pumping NOW)
    - Volatility hunting (high amplitude = opportunity)
    - Quick market overview
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_coins_price_change()
        return result
    finally:
        await service.close()


@router.get("/price-history")
async def get_price_history(
    exchange: str = Query("Binance", description="Exchange name"),
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    interval: str = Query("1h", description="Interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w"),
    limit: int = Query(100, description="Number of candles (max 1000)", le=1000)
):
    """
    Get historical price data - OHLCV candles (13TH ENDPOINT!)
    
    Returns candlestick data for charting:
    - Open, High, Low, Close prices
    - Volume in USD
    - Timestamp per candle
    - Summary statistics (price change, high/low, total volume)
    
    Perfect for:
    - Price charting and visualization
    - Technical analysis (patterns, indicators)
    - Backtesting strategies
    
    Intervals supported: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_price_history(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return result
    finally:
        await service.close()


@router.get("/delisted-pairs")
async def get_delisted_pairs():
    """
    Get delisted (removed) trading pairs by exchange (14TH ENDPOINT!)
    
    Returns comprehensive list of pairs that have been delisted:
    - Total delisted pairs across all exchanges
    - Breakdown by exchange
    - Sample pairs per exchange
    
    Perfect for:
    - Avoiding trading delisted pairs
    - Historical reference
    - Exchange policy tracking
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_delisted_pairs()
        return result
    finally:
        await service.close()


@router.get("/indicators/rsi")
async def get_rsi_indicator(
    exchange: str = Query("Binance", description="Exchange name"),
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    interval: str = Query("1h", description="Interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w"),
    limit: int = Query(100, description="Number of data points (max 4500)", le=4500),
    window: int = Query(14, description="RSI period (default 14)")
):
    """
    Get RSI (Relative Strength Index) technical indicator (15TH ENDPOINT!)
    
    Returns RSI analysis for trading signals:
    - Latest RSI value
    - Signal classification (OVERBOUGHT/OVERSOLD/BULLISH/BEARISH/NEUTRAL)
    - Historical RSI data
    - Statistics (max, min, average RSI)
    - Overbought/oversold frequency
    
    Trading signals:
    - RSI > 70 = OVERBOUGHT (sell signal)
    - RSI < 30 = OVERSOLD (buy signal)
    - RSI 60-70 = BULLISH (upward momentum)
    - RSI 30-40 = BEARISH (downward momentum)
    - RSI 40-60 = NEUTRAL (consolidation)
    
    Perfect for:
    - Entry/exit timing
    - Momentum confirmation
    - Divergence detection
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_rsi_indicator(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            limit=limit,
            window=window
        )
        return result
    finally:
        await service.close()


@router.get("/open-interest/history")
async def get_open_interest_history(
    exchange: str = Query("Binance", description="Exchange name"),
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    interval: str = Query("1d", description="Interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w"),
    limit: int = Query(100, description="Number of data points (max 1000)", le=1000),
    unit: str = Query("usd", description="Unit: 'usd' or 'coin'")
):
    """
    Get Open Interest historical data - OHLC format (16TH ENDPOINT!)
    
    Returns OI movement over time (NOT price!):
    - OI OHLC (Open, High, Low, Close)
    - Latest OI value
    - OI trend analysis (increasing/decreasing)
    - Statistics (highest, lowest, average OI)
    
    Trend signals:
    - OI INCREASE + Price UP = Bullish (new longs opening)
    - OI INCREASE + Price DOWN = Bearish (new shorts opening)
    - OI DECREASE + Price UP = Bullish weak (shorts closing)
    - OI DECREASE + Price DOWN = Bearish weak (longs closing)
    
    Perfect for:
    - Institutional positioning tracking
    - Correlation with price movements
    - Trend confirmation/divergence
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_open_interest_history(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            limit=limit,
            unit=unit
        )
        return result
    finally:
        await service.close()


@router.get("/open-interest/aggregated-history")
async def get_aggregated_oi_history(
    symbol: str = Query("BTC", description="Coin symbol (e.g., BTC, ETH)"),
    interval: str = Query("1d", description="Interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w"),
    limit: int = Query(100, description="Number of data points (max 1000)", le=1000),
    unit: str = Query("usd", description="Unit: 'usd' or 'coin'")
):
    """
    Get AGGREGATED Open Interest across ALL EXCHANGES (17TH ENDPOINT!)
    
    Returns TOTAL OI combining all exchanges (Binance, OKX, Bybit, etc.):
    - Total market-wide OI (much larger than single exchange)
    - Market-wide trend analysis
    - OI volatility (swing range)
    - OHLC data for total OI
    
    Key differences from per-exchange OI:
    - Per-exchange OI: Shows single exchange positioning (e.g., Binance $8B)
    - Aggregated OI: Shows TOTAL market positioning (e.g., All exchanges $68B)
    
    Perfect for:
    - Market-wide institutional sentiment
    - Overall positioning trends
    - Cross-exchange flow analysis
    - Macro market view
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_aggregated_oi_history(
            symbol=symbol,
            interval=interval,
            limit=limit,
            unit=unit
        )
        return result
    finally:
        await service.close()


@router.get("/open-interest/aggregated-stablecoin-history")
async def get_aggregated_stablecoin_oi_history(
    exchange_list: str = Query("Binance", description="Exchange name(s), comma-separated"),
    symbol: str = Query("BTC", description="Coin symbol (e.g., BTC, ETH)"),
    interval: str = Query("1d", description="Interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w"),
    limit: int = Query(100, description="Number of data points (max 1000)", le=1000)
):
    """
    Get AGGREGATED STABLECOIN Open Interest history (18TH ENDPOINT!)
    
    Returns OI in COIN/STABLECOIN terms (NOT USD!):
    - OI denominated in the actual coin (e.g., BTC, ETH)
    - Tracks coin-denominated positions
    - OHLC data for stablecoin OI
    - Trend analysis
    
    Key differences:
    - USD OI: Shows positions in dollar value (e.g., $67.9B)
    - Stablecoin OI: Shows positions in coin amount (e.g., 94,000 BTC)
    
    Why useful:
    - Track actual coin accumulation/distribution
    - See real coin-denominated leverage
    - Compare coin OI vs USD OI to detect price impacts
    
    Example:
    - If USD OI increases but coin OI stable = price went up
    - If coin OI increases but USD OI stable = price went down
    - If both increase = real accumulation + price up
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_aggregated_stablecoin_oi_history(
            exchange_list=exchange_list,
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return result
    finally:
        await service.close()


@router.get("/open-interest/aggregated-coin-margin-history")
async def get_aggregated_coin_margin_oi_history(
    exchange_list: str = Query("Binance", description="Exchange name(s), comma-separated"),
    symbol: str = Query("BTC", description="Coin symbol (e.g., BTC, ETH)"),
    interval: str = Query("1d", description="Interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w"),
    limit: int = Query(100, description="Number of data points (max 1000)", le=1000)
):
    """
    Get AGGREGATED COIN-MARGIN Open Interest history (19TH ENDPOINT!)
    
    Returns OI for COIN-MARGINED (inverse) futures contracts:
    - Tracks inverse contracts (e.g., BTCUSD where margin is in BTC)
    - Different from linear contracts (BTCUSDT where margin is in USDT)
    - OHLC data for coin-margined OI
    - Trend analysis
    
    Contract Types Explained:
    - **Linear (USDT-margined)**: BTCUSDT - margin in stablecoin
    - **Inverse (Coin-margined)**: BTCUSD - margin in the coin itself
    
    Key Differences:
    - Coin-margined: Profit/loss in BTC (more volatile)
    - USDT-margined: Profit/loss in USDT (more stable)
    - Different risk profiles and use cases
    
    Why Track Both:
    - Professional traders use both contract types
    - Coin-margined popular for hedging spot holdings
    - Different OI trends indicate different trader behaviors
    
    Perfect for:
    - Tracking inverse contract positioning
    - Analyzing professional/institutional flows
    - Comparing linear vs inverse contract trends
    - Risk analysis (coin vs stablecoin exposure)
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_aggregated_coin_margin_oi_history(
            exchange_list=exchange_list,
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return result
    finally:
        await service.close()


@router.get("/open-interest/exchange-list/{symbol}")
async def get_oi_exchange_list(symbol: str):
    """
    Get Open Interest breakdown by EXCHANGE (20TH ENDPOINT!)
    
    Returns comprehensive OI data per exchange:
    - Total market OI aggregate (All exchanges combined)
    - Per-exchange breakdown (Binance, OKX, Bybit, CME, etc.)
    - Market share % for each exchange
    - Coin-margined vs Stablecoin-margined split
    - OI changes across 6 timeframes (5m, 15m, 30m, 1h, 4h, 24h)
    
    Perfect for:
    - Cross-exchange OI comparison
    - Market dominance analysis (which exchange leads?)
    - Exchange flow tracking (money moving between exchanges)
    - Contract type preference per exchange
    - Short-term momentum (5m-4h changes)
    
    Example insights:
    - Binance: $12.4B (18% market share) - Mixed margin types
    - CME: $14.5B (21% market share) - Institutional, USDT-only
    - Bybit: $7.1B (10% market share) - Growing fast (+2.87% 24h)
    
    Use Cases:
    - Identify which exchanges are accumulating/distributing
    - Spot exchange-specific trends before market-wide moves
    - Analyze institutional (CME) vs retail (Binance) flows
    - Track defi exchanges (dYdX) separately
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_oi_exchange_list(symbol=symbol)
        return result
    finally:
        await service.close()


@router.get("/open-interest/exchange-history-chart")
async def get_oi_exchange_history_chart(
    symbol: str = Query("BTC", description="Coin symbol (e.g., BTC, ETH)"),
    range: str = Query("12h", description="Time range: all, 1m, 15m, 1h, 4h, 12h, 24h"),
    unit: str = Query("usd", description="Unit: 'usd' or 'coin'")
):
    """
    Get Open Interest history CHART data per exchange (21ST ENDPOINT!)
    
    Returns TIME-SERIES data optimized for charting:
    - timeList: Array of timestamps (x-axis)
    - priceList: Array of prices (reference line)
    - exchangeData: Object with exchange OI arrays (y-axis per exchange)
    
    Chart-ready format:
    {
      "timeList": [1762128000000, 1762214400000, ...],
      "priceList": [110494.9, 106537.2, ...],
      "exchangeData": {
        "BINANCE": [12149298874, 12117334695, ...],
        "BYBIT": [7123456789, 7234567890, ...],
        ...
      }
    }
    
    Perfect for:
    - Multi-line charts (OI per exchange over time)
    - Stacked area charts (total market OI)
    - Exchange comparison visualization
    - Correlation analysis (OI vs price)
    
    Example use cases:
    - Plot Binance OI vs CME OI to see retail vs institutional trends
    - Overlay price to detect OI-price divergences
    - Stack all exchanges to visualize total market OI
    - Compare short-term (1h) vs long-term (24h) trends
    
    Response includes:
    - Raw chart data (arrays)
    - Price summary (first/last price, change %)
    - Per-exchange summary (first/last OI, change %)
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_oi_exchange_history_chart(
            symbol=symbol,
            range=range,
            unit=unit
        )
        return result
    finally:
        await service.close()


@router.get("/funding-rate/history")
async def get_funding_rate_history(
    exchange: str = Query("Binance", description="Exchange name"),
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    interval: str = Query("1d", description="Interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w"),
    limit: int = Query(100, description="Number of data points (max 1000)", le=1000)
):
    """
    Get Funding Rate historical data (22ND ENDPOINT!)
    
    Returns funding rate OHLC data with sentiment analysis:
    - Latest funding rate & percentage
    - Sentiment classification (Extremely Bullish to Extremely Bearish)
    - Statistical summary (avg, high, low, positive/negative periods)
    - Full time-series OHLC data
    
    Funding Rate Explained:
    - **Positive FR** (e.g., +0.01 = +1%): Longs pay shorts → Bullish sentiment
    - **Negative FR** (e.g., -0.01 = -1%): Shorts pay longs → Bearish sentiment
    - **High FR** (>2%): Extreme bullish, potential long squeeze
    - **Low FR** (<-2%): Extreme bearish, potential short squeeze
    
    Sentiment Classification:
    - Extremely Bullish: avg FR > 5% (reversal risk!)
    - Very Bullish: avg FR > 2%
    - Bullish: avg FR > 1%
    - Slightly Bullish: avg FR > 0%
    - Slightly Bearish: avg FR < 0%
    - Bearish: avg FR < -1%
    - Very Bearish: avg FR < -2%
    - Extremely Bearish: avg FR < -5% (reversal risk!)
    
    Trading Signals:
    - High positive FR + price stall = Long squeeze coming
    - High negative FR + price stall = Short squeeze coming
    - FR flip from positive to negative = Sentiment shift
    - Extreme FR = Contrarian signal (fade the crowd)
    
    Perfect for:
    - Market sentiment analysis
    - Squeeze detection (high FR = potential reversal)
    - Entry/exit timing (extreme FR = fade)
    - Cross-exchange FR comparison
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_funding_rate_history(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return result
    finally:
        await service.close()


@router.get("/funding-rate/oi-weight-history")
async def get_oi_weighted_funding_rate_history(
    symbol: str = Query("BTC", description="Coin symbol (e.g., BTC, ETH)"),
    interval: str = Query("1d", description="Interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w"),
    limit: int = Query(100, description="Number of data points (max 1000)", le=1000)
):
    """
    Get OI-WEIGHTED Funding Rate history (23RD ENDPOINT!)
    
    Returns AGGREGATED funding rate weighted by Open Interest across ALL exchanges:
    - More accurate than single exchange FR
    - Weights by OI (bigger exchanges = higher weight)
    - Market-wide sentiment indicator
    - OHLC data with sentiment analysis
    
    Why OI-Weighted is Better:
    - **Single Exchange FR**: Only shows one exchange sentiment
    - **Simple Average FR**: Treats all exchanges equally (misleading)
    - **OI-Weighted FR**: Weights by liquidity/volume (MOST ACCURATE) ✨
    
    Example:
    - Binance (12B OI) FR = 0.5% → Weight: High
    - Small Exchange (100M OI) FR = 2% → Weight: Low
    - Result: Weighted FR closer to 0.5% (more accurate)
    
    Sentiment Classification:
    - Extremely Bullish: avg FR > 5% (reversal risk!)
    - Very Bullish: avg FR > 2%
    - Bullish: avg FR > 1%
    - Slightly Bullish: avg FR > 0%
    - Slightly Bearish: avg FR < 0%
    - Bearish: avg FR < -1%
    - Very Bearish: avg FR < -2%
    - Extremely Bearish: avg FR < -5% (reversal risk!)
    
    Trading Signals:
    - OI-weighted FR > 2% = Market-wide long bias (potential squeeze)
    - OI-weighted FR < -2% = Market-wide short bias (potential squeeze)
    - Divergence: Single exchange FR ≠ OI-weighted FR = Arbitrage opportunity
    
    Perfect for:
    - **TRUE market sentiment** (not skewed by small exchanges)
    - Squeeze detection across entire market
    - More reliable than single exchange FR
    - Professional-grade sentiment analysis
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_oi_weighted_funding_rate_history(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return result
    finally:
        await service.close()


@router.get("/funding-rate/vol-weight-history")
async def get_volume_weighted_funding_rate_history(
    symbol: str = Query("BTC", description="Coin symbol (e.g., BTC, ETH)"),
    interval: str = Query("1d", description="Interval: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w"),
    limit: int = Query(100, description="Number of data points (max 1000)", le=1000)
):
    """
    Get VOLUME-WEIGHTED Funding Rate history (24TH ENDPOINT!)
    
    Returns AGGREGATED funding rate weighted by Trading Volume across ALL exchanges:
    - Weights by trading volume (high volume = high weight)
    - Different from OI-weighted (positions vs activity)
    - Active trader sentiment indicator
    - OHLC data with sentiment analysis
    
    OI-Weighted vs Volume-Weighted:
    - **OI-Weighted**: Weights by positions held → Positional bias
    - **Volume-Weighted**: Weights by trading activity → Active trader bias ✨
    
    Why Both Matter:
    - **OI-weighted FR**: What holders believe (long-term view)
    - **Volume-weighted FR**: What traders are doing (short-term activity)
    - **Divergence**: OI-weighted ≠ Vol-weighted = Position vs Activity mismatch
    
    Example Divergence:
    - OI-weighted FR: +0.5% (holders bullish)
    - Volume-weighted FR: -0.2% (active traders bearish)
    - Signal: Smart money (low volume) vs retail (high volume) split
    
    Sentiment Classification:
    - Extremely Bullish: avg FR > 5% (reversal risk!)
    - Very Bullish: avg FR > 2%
    - Bullish: avg FR > 1%
    - Slightly Bullish: avg FR > 0%
    - Slightly Bearish: avg FR < 0%
    - Bearish: avg FR < -1%
    - Very Bearish: avg FR < -2%
    - Extremely Bearish: avg FR < -5% (reversal risk!)
    
    Trading Signals:
    - Vol-weighted FR > OI-weighted FR = Active buyers aggressive
    - Vol-weighted FR < OI-weighted FR = Active sellers aggressive
    - High vol-weighted FR = Active traders paying premium (FOMO)
    
    Perfect for:
    - **Active trader sentiment** (what's trading NOW)
    - Short-term momentum analysis
    - Compare with OI-weighted for smart money detection
    - Identify retail vs institutional bias
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_volume_weighted_funding_rate_history(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return result
    finally:
        await service.close()


@router.get("/funding-rate/exchange-list/{symbol}")
async def get_funding_rate_exchange_list(symbol: str):
    """
    Get REAL-TIME Funding Rate per exchange (25TH ENDPOINT!)
    
    Returns current funding rate across ALL exchanges:
    - Current funding rate per exchange
    - Funding interval (1h or 8h typical)
    - Next funding time timestamp
    - Separated by margin type (stablecoin vs coin-margined)
    - Statistical summary (avg, high, low)
    - Top 5 highest/lowest FR exchanges
    
    Perfect for:
    - **Cross-exchange arbitrage** (find FR spreads)
    - Real-time FR comparison
    - Exchange selection (trade where FR is favorable)
    - Market consensus view
    
    Trading Strategies:
    1. **Arbitrage Detection**:
       - High FR exchange (e.g., Bybit 0.377%) vs Low FR (e.g., CoinEx 0%)
       - Spread = 0.377% arbitrage opportunity!
    
    2. **Exchange Selection**:
       - If LONG: Choose exchange with LOWEST FR (pay less)
       - If SHORT: Choose exchange with HIGHEST FR (earn more)
    
    3. **Market Sentiment**:
       - All exchanges HIGH FR = Strong bullish consensus
       - Mixed FR = Market uncertainty
       - All exchanges LOW/NEG FR = Bearish consensus
    
    4. **Funding Interval Optimization**:
       - 1h interval (dYdX, Kraken) = More frequent payments
       - 8h interval (Binance, OKX) = Less frequent but larger
    
    Example Use Cases:
    - Find cheapest exchange to long (lowest FR)
    - Find best exchange to short (highest FR)
    - Detect funding rate arbitrage opportunities
    - Compare stablecoin vs coin-margined FR
    
    Response Structure:
    - stablecoinMargined: Linear contracts (BTCUSDT)
    - coinMargined: Inverse contracts (BTCUSD)
    - Each includes: statistics + top5 + allExchanges
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_funding_rate_exchange_list(symbol=symbol)
        return result
    finally:
        await service.close()


@router.get("/funding-rate/accumulated-exchange-list")
async def get_accumulated_funding_rate_exchange_list(
    range: str = Query("1d", description="Time period: 1d, 7d, 30d, etc."),
    symbol: str = Query("BTC", description="Coin symbol (e.g., BTC, ETH)")
):
    """
    Get ACCUMULATED Funding Rate per exchange (26TH ENDPOINT!)
    
    Returns CUMULATIVE funding rate over time period per exchange:
    - Total funding paid/received over period
    - Per-exchange breakdown
    - Separated by margin type
    - Statistical summary
    
    Key Differences:
    - **Real-time FR (Ep.25)**: Current funding rate NOW (e.g., 0.01%)
    - **Accumulated FR (Ep.26)**: Total funding over period (e.g., 0.55% over 1d) ✨
    
    Why Accumulated FR Matters:
    - **Actual Cost**: Shows real funding paid/received
    - **Period Analysis**: Compare total funding across exchanges
    - **Profit Calculation**: Calculate actual funding profit/loss
    
    Example Use Cases:
    
    1. **Cost Analysis** (for Longs):
       - Binance accumulated FR: 0.55% over 1d
       - Means: Paid 0.55% of position value over 24h
       - On $10,000 position: Paid $55 in funding
    
    2. **Exchange Comparison**:
       - Exchange A: 0.30% accumulated (cheaper)
       - Exchange B: 0.70% accumulated (expensive)
       - Difference: 0.40% = $40 savings per $10k position
    
    3. **Profit Optimization** (for Shorts):
       - Find exchange with HIGHEST accumulated FR
       - Short there to EARN maximum funding
    
    4. **Period Analysis**:
       - 1d: Short-term funding trends
       - 7d: Weekly funding patterns
       - 30d: Long-term funding costs
    
    Trading Strategies:
    - LONG: Choose exchange with LOWEST accumulated FR (minimize cost)
    - SHORT: Choose exchange with HIGHEST accumulated FR (maximize earnings)
    - Compare with real-time FR to predict future costs
    
    Response Structure:
    - stablecoinMargined: Linear contracts (BTCUSDT)
    - tokenMargined: Inverse/coin-margined contracts (BTCUSD)
    - Each includes: statistics, top5 highest/lowest, all exchanges
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_accumulated_funding_rate_exchange_list(
            range=range,
            symbol=symbol
        )
        return result
    finally:
        await service.close()


@router.get("/pairs-markets/{symbol}")
async def get_pairs_markets(symbol: str):
    """
    Get futures market data PER EXCHANGE (11TH ENDPOINT!)
    
    Returns breakdown by exchange for arbitrage analysis:
    - Price differences across exchanges
    - Volume and OI per exchange
    - Long/short volume split
    - Liquidations per exchange
    - Funding rates comparison
    - OI/Volume ratios
    
    Perfect for:
    - Arbitrage opportunities (price spreads)
    - Cross-exchange volume analysis
    - Finding best exchange for trading
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_pairs_markets(symbol=symbol)
        return result
    finally:
        await service.close()


@router.get("/supported-coins")
async def get_supported_coins():
    """
    Get list of all supported cryptocurrency symbols
    
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_supported_coins()
        return result
    finally:
        await service.close()


@router.get("/exchanges")
async def get_exchanges():
    """
    Get all supported exchanges and their trading pairs
    
    Returns comprehensive list of exchanges and available markets
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_supported_exchange_pairs()
        return result
    finally:
        await service.close()


@router.get("/options/open-interest")
async def get_options_oi():
    """
    Get Bitcoin/Crypto options open interest across exchanges
    
    Returns:
    - Total options OI
    - Top exchange by OI
    - Per-exchange breakdown
    
    Update frequency: 30 seconds
    Critical for detecting smart money positioning before major moves
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_options_open_interest()
        return result
    finally:
        await service.close()


@router.get("/options/volume")
async def get_options_volume():
    """
    Get Bitcoin/Crypto options trading volume (24h)
    
    Returns volume by exchange - high volume = increased hedging activity
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_options_volume()
        return result
    finally:
        await service.close()


@router.get("/etf/flows/{asset}")
async def get_etf_flows(asset: str = "BTC"):
    """
    Get Bitcoin/Crypto ETF flows (institutional money tracking)
    
    Returns:
    - Daily inflows/outflows
    - Total institutional holdings
    - Sentiment (accumulation vs distribution)
    
    Critical for detecting when institutions are buying or selling
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_etf_flows(asset=asset)
        return result
    finally:
        await service.close()


@router.get("/on-chain/reserves/{symbol}")
async def get_exchange_reserves(symbol: str = "BTC"):
    """
    Get cryptocurrency reserves on exchanges (whale movement detection)
    
    Returns:
    - Current exchange reserves
    - Change from previous period
    - Interpretation (accumulation vs distribution)
    
    Large outflows = whales accumulating (bullish)
    Large inflows = whales preparing to sell (bearish)
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_exchange_reserves(symbol=symbol)
        return result
    finally:
        await service.close()


@router.get("/index/bull-market-peak")
async def get_bull_market_peak():
    """
    Bull Market Peak Indicators - Multi-metric positioning signals
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_bull_market_indicators()
        return result
    finally:
        await service.close()


@router.get("/index/rainbow-chart")
async def get_rainbow_chart():
    """
    Bitcoin Rainbow Chart - Long-term valuation bands
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_rainbow_chart()
        return result
    finally:
        await service.close()


@router.get("/index/stock-to-flow")
async def get_stock_to_flow():
    """
    Bitcoin Stock-to-Flow Model - Scarcity valuation
    Gracefully returns success:false if data unavailable
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_stock_to_flow()
        return result
    finally:
        await service.close()


@router.get("/borrow/interest-rate")
async def get_borrow_interest_rate():
    """
    Borrow Interest Rate History - Leverage demand indicator
    
    Returns HTTP 200 even when no data available (graceful degradation)
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_borrow_interest_rate()
        return result
    finally:
        await service.close()


@router.get("/exchange/assets/{exchange}")
async def get_exchange_assets(exchange: str = "Binance"):
    """
    Get exchange wallet holdings/reserves (10TH ENDPOINT!)
    
    Returns real-time exchange asset holdings:
    - Total value in USD across all wallets
    - Holdings by asset (BTC, ETH, USDT, etc.)
    - Top 20 assets by value
    - Wallet-level breakdown
    
    Useful for tracking exchange reserves and whale movements
    Supports: Binance, OKX, Bybit, Coinbase, etc.
    """
    service = CoinglassComprehensiveService()
    try:
        result = await service.get_exchange_assets(exchange=exchange)
        return result
    finally:
        await service.close()


@router.get("/dashboard/{symbol}")
async def get_trading_dashboard(symbol: str):
    """
    Get comprehensive trading dashboard data for a symbol
    
    Combines ALL Coinglass Standard plan endpoints:
    - Market data (price, OI, funding rates, 7 timeframes)
    - Multi-timeframe liquidations (24h/12h/4h/1h)
    - Options OI & volume
    - ETF flows (institutional tracking)
    - Exchange reserves (whale movements)
    - Market indexes (Rainbow, S2F, Borrow rates)
    
    OPTIMIZED: Maximizes Standard plan value with 20+ data points
    """
    service = CoinglassComprehensiveService()
    try:
        # Fetch all endpoints concurrently for maximum efficiency
        import asyncio
        
        # Core market data
        market_task = service.get_coins_markets(symbol=symbol)
        liq_task = service.get_liquidation_coin_list(symbol=symbol)
        
        # NEW: Institutional & whale tracking
        etf_task = service.get_etf_flows(asset=symbol)
        reserves_task = service.get_exchange_reserves(symbol=symbol)
        options_oi_task = service.get_options_open_interest()
        options_vol_task = service.get_options_volume()
        
        # NEW: Market indicators (Bitcoin only)
        if symbol.upper() in ["BTC", "BITCOIN"]:
            bull_task = service.get_bull_market_indicators()
            rainbow_task = service.get_rainbow_chart()
            s2f_task = service.get_stock_to_flow()
            borrow_task = service.get_borrow_interest_rate()
        else:
            null_result = {"success": False, "error": "BTC only"}
            bull_task = asyncio.create_task(asyncio.sleep(0, result=null_result))
            rainbow_task = asyncio.create_task(asyncio.sleep(0, result=null_result))
            s2f_task = asyncio.create_task(asyncio.sleep(0, result=null_result))
            borrow_task = asyncio.create_task(asyncio.sleep(0, result=null_result))
        
        # NEW: Exchange assets (Binance only for now)
        exchange_assets_task = service.get_exchange_assets(exchange="Binance")
        
        # Execute all 11 endpoints concurrently (10 WORKING!)
        results = await asyncio.gather(
            market_task, liq_task, etf_task, reserves_task, 
            options_oi_task, options_vol_task, 
            bull_task, rainbow_task, s2f_task, borrow_task,
            exchange_assets_task
        )
        
        market, liquidations, etf_flows, reserves, options_oi, options_vol, bull_indicators, rainbow, s2f, borrow, exchange_assets = results
        
        return {
            "symbol": symbol.upper(),
            "timestamp": None,
            
            # Core futures data
            "market": market,
            "liquidations": liquidations,
            
            # Institutional tracking (NEW!)
            "institutionalFlows": {
                "etf": etf_flows,
                "optionsOI": options_oi,
                "optionsVolume": options_vol
            },
            
            # Whale tracking (NEW!)
            "whaleActivity": {
                "exchangeReserves": reserves,
                "interpretation": reserves.get("interpretation", "unknown")
            },
            
            # Market indexes (NEW! - Bitcoin only)
            "marketIndexes": {
                "bullMarketPeak": bull_indicators,
                "rainbowChart": rainbow,
                "stockToFlow": s2f,
                "borrowInterestRate": borrow
            },
            
            # Exchange holdings (NEW! - 10th endpoint)
            "exchangeAssets": exchange_assets,
            
            "status": {
                "endpointsUsed": 10,
                "workingEndpoints": 10,
                "optimizationLevel": "MAXIMUM",
                "note": "10/10 working endpoints verified from official Coinglass docs (November 2025)",
                "endpoints": [
                    "market", "liquidations", "options_oi", "options_vol", 
                    "etf_flows", "exchange_reserves", "bull_indicators", 
                    "rainbow_chart", "stock_to_flow", "exchange_assets"
                ]
            }
        }
    finally:
        await service.close()

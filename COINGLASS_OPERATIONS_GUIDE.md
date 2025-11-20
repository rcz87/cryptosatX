# Coinglass Operations Guide for GPT Actions

## ⚠️ CRITICAL: Flat Parameter Format Required

**All Coinglass operations use FLAT parameter structure** - do NOT nest parameters under `args`:

✅ **CORRECT:**
```json
{
  "operation": "coinglass.markets.symbol",
  "symbol": "BTC"
}
```

❌ **WRONG:**
```json
{
  "operation": "coinglass.markets.symbol",
  "args": {"symbol": "BTC"}
}
```

This matches the flat parameter contract documented in GPT_ACTIONS_INSTRUCTIONS.txt.

---

## Overview
CryptoSatX provides access to **64 premium Coinglass API endpoints** via GPT Actions. All operations use the `/invoke` RPC endpoint with operation names in `coinglass.category.operation` format.

## Quick Reference by Category

### 📊 Markets & Price Data (5 operations)
- `coinglass.markets` - Get all markets overview
- `coinglass.markets.symbol` - Get market data for specific symbol
- `coinglass.price_change` - Get price changes across coins
- `coinglass.price_history` - Get historical price data
- `coinglass.delisted_pairs` - Get delisted trading pairs

### 💀 Liquidations (6 operations)
- `coinglass.liquidation.order` - Get real-time liquidation orders
- `coinglass.liquidation.exchange_list` - Get exchange-specific liquidation list
- `coinglass.liquidation.aggregated_history` - Get aggregated liquidation history
- `coinglass.liquidation.history` - Get detailed liquidation history
- `coinglass.liquidations.symbol` - Get liquidations for specific symbol
- `coinglass.liquidations.heatmap` - Get liquidation heatmap (price cluster analysis)

### 📖 Orderbook & Whale Tracking (5 operations)
- `coinglass.orderbook.ask_bids_history` - Get historical ask/bid data
- `coinglass.orderbook.aggregated_history` - Get aggregated orderbook history
- `coinglass.orderbook.whale_walls` - Get whale walls (large buy/sell walls)
- `coinglass.orderbook.whale_history` - Get whale orderbook activity history
- `coinglass.orderbook.detailed_history` - Get detailed orderbook snapshots

### 🐋 Hyperliquid (3 operations)
- `coinglass.hyperliquid.whale_alerts` - Get real-time whale alerts on Hyperliquid
- `coinglass.hyperliquid.whale_positions` - Get whale positions on Hyperliquid
- `coinglass.hyperliquid.positions.symbol` - Get Hyperliquid positions for symbol

### ⛓️ On-Chain Data (3 operations)
- `coinglass.chain.whale_transfers` - Get on-chain whale transfers
- `coinglass.chain.exchange_flows` - Get exchange inflows/outflows
- `coinglass.onchain.reserves` - Get on-chain reserves for symbol

### 📈 Technical Indicators (11 operations)
- `coinglass.indicators.rsi_list` - Get RSI list for all coins
- `coinglass.indicators.rsi` - Get RSI indicator for symbol
- `coinglass.indicators.ma` - Get Moving Average
- `coinglass.indicators.ema` - Get Exponential Moving Average
- `coinglass.indicators.bollinger` - Get Bollinger Bands
- `coinglass.indicators.macd` - Get MACD indicator
- `coinglass.indicators.basis` - Get futures basis (premium/discount)
- `coinglass.indicators.whale_index` - Get Whale Index
- `coinglass.indicators.cgdi` - Get Coinglass Directional Index
- `coinglass.indicators.cdri` - Get Coinglass Directional Relative Index
- `coinglass.indicators.golden_ratio` - Get Golden Ratio indicator
- `coinglass.indicators.fear_greed` - Get Fear & Greed Index

### 📅 Calendar & News (2 operations)
- `coinglass.calendar.economic` - Get economic calendar events
- `coinglass.news.feed` - Get crypto news feed

### 📊 Volume & Taker Data (2 operations)
- `coinglass.volume.taker_buy_sell` - Get taker buy/sell volume ratio
- `coinglass.taker_buy_sell.exchange_list` - Get taker volume by exchange

### 💰 Open Interest (6 operations)
- `coinglass.open_interest.history` - Get open interest history
- `coinglass.open_interest.aggregated_history` - Get aggregated OI across exchanges
- `coinglass.open_interest.aggregated_stablecoin_history` - Get stablecoin-settled OI
- `coinglass.open_interest.aggregated_coin_margin_history` - Get coin-margined OI
- `coinglass.open_interest.exchange_list` - Get OI breakdown by exchange
- `coinglass.open_interest.exchange_history_chart` - Get OI chart data

### 💸 Funding Rate (5 operations)
- `coinglass.funding_rate.history` - Get funding rate history
- `coinglass.funding_rate.oi_weight_history` - Get OI-weighted funding rate
- `coinglass.funding_rate.vol_weight_history` - Get volume-weighted funding rate
- `coinglass.funding_rate.exchange_list` - Get funding rates by exchange
- `coinglass.funding_rate.accumulated_exchange_list` - Get accumulated funding rates

### 📊 Long/Short Ratio (2 operations)
- `coinglass.long_short_ratio.account_history` - Get account-based long/short ratio
- `coinglass.long_short_ratio.position_history` - Get position-based long/short ratio

### 📍 Net Position (1 operation)
- `coinglass.net_position.history` - Get net position history

### 🎲 Options Data (2 operations)
- `coinglass.options.open_interest` - Get options open interest
- `coinglass.options.volume` - Get options trading volume

### 🏦 ETF & Exchange Data (2 operations)
- `coinglass.etf.flows` - Get Bitcoin/Ethereum ETF flows
- `coinglass.exchange.assets` - Get exchange asset holdings

### 📊 Market Indices (4 operations)
- `coinglass.index.bull_market_peak` - Get bull market peak indicator
- `coinglass.index.rainbow_chart` - Get Bitcoin rainbow chart data
- `coinglass.index.stock_to_flow` - Get stock-to-flow model data

### 💳 Borrowing (1 operation)
- `coinglass.borrow.interest_rate` - Get borrow interest rates

### 🔍 System Info (4 operations)
- `coinglass.pairs_markets.symbol` - Get all trading pairs for symbol
- `coinglass.supported_coins` - Get list of supported coins
- `coinglass.supported_exchanges` - Get list of supported exchanges
- `coinglass.exchanges` - Get exchange information

### 📱 Dashboard (1 operation)
- `coinglass.dashboard.symbol` - Get comprehensive dashboard for symbol

---

## Detailed Operation Reference

### Markets & Price Data

#### `coinglass.markets`
Get overview of all markets.

**Parameters:** None

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.markets"
}
```

**Use Cases:**
- Get snapshot of entire crypto futures market
- Compare multiple coins at once
- Market screening

---

#### `coinglass.markets.symbol`
Get detailed market data for specific symbol.

**Parameters:**
- `symbol` (required): Trading symbol (e.g., "BTC", "ETH")

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.markets.symbol",
  "symbol": "BTC"
}
```

**Use Cases:**
- Get current price, 24h change, volume for BTC
- Quick market snapshot before trading

---

#### `coinglass.price_change`
Get price changes across multiple timeframes.

**Parameters:** 
- `symbol` (optional): Filter by symbol
- `interval` (optional): Time interval (e.g., "1h", "24h", "7d")

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.price_change",
  "interval": "24h"
}
```

**Use Cases:**
- Find biggest movers in last 24h
- Identify trending coins

---

### Liquidations

#### `coinglass.liquidation.order`
Get real-time liquidation orders (live feed).

**Parameters:**
- `symbol` (optional): Filter by symbol
- `exchange` (optional): Filter by exchange

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.liquidation.order",
  "symbol": "BTC"
}
```

**Use Cases:**
- Track live liquidations as they happen
- Detect cascading liquidations
- Market stress indicator

---

#### `coinglass.liquidations.symbol`
Get liquidation data for specific symbol.

**Parameters:**
- `symbol` (required): Trading symbol

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.liquidations.symbol",
  "symbol": "ETH"
}
```

**Use Cases:**
- Analyze ETH liquidation patterns
- Correlation with price movements

---

#### `coinglass.liquidations.heatmap`
Get liquidation heatmap showing price clusters where liquidations will occur.

**Parameters:**
- `symbol` (required): Trading symbol

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.liquidations.heatmap",
  "symbol": "BTC"
}
```

**Use Cases:**
- Identify key liquidation zones
- Predict support/resistance levels
- Estimate cascade risk

---

### Orderbook & Whale Tracking

#### `coinglass.orderbook.whale_walls`
Get whale walls (large buy/sell orders that create price barriers).

**Parameters:**
- `symbol` (optional): Trading symbol
- `exchange` (optional): Exchange filter

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.orderbook.whale_walls",
  "symbol": "BTC"
}
```

**Use Cases:**
- Detect manipulation attempts
- Find strong support/resistance
- Whale activity tracking

---

#### `coinglass.orderbook.whale_history`
Get historical whale orderbook activity.

**Parameters:**
- `symbol` (optional): Symbol filter
- `days_back` (optional): Days of history

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.orderbook.whale_history",
  "symbol": "BTC",
  "days_back": 7
}
```

**Use Cases:**
- Analyze whale accumulation/distribution patterns
- Track large position changes

---

### Hyperliquid

#### `coinglass.hyperliquid.whale_alerts`
Get real-time whale alerts on Hyperliquid DEX.

**Parameters:** None (or optional filters)

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.hyperliquid.whale_alerts"
}
```

**Use Cases:**
- Track large Hyperliquid trades
- DEX whale activity monitoring

---

#### `coinglass.hyperliquid.positions.symbol`
Get Hyperliquid positions for specific symbol.

**Parameters:**
- `symbol` (required): Trading symbol

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.hyperliquid.positions.symbol",
  "symbol": "ETH"
}
```

**Use Cases:**
- Track ETH positions on Hyperliquid
- DEX positioning analysis

---

### On-Chain Data

#### `coinglass.chain.whale_transfers`
Get on-chain whale transfers (large wallet movements).

**Parameters:**
- `symbol` (optional): Coin filter
- `min_value_usd` (optional): Minimum transfer value

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.chain.whale_transfers",
  "symbol": "BTC",
  "min_value_usd": 1000000
}
```

**Use Cases:**
- Detect whale accumulation
- Exchange deposit/withdrawal tracking
- Smart money movement analysis

---

#### `coinglass.chain.exchange_flows`
Get exchange inflows and outflows.

**Parameters:**
- `symbol` (optional): Coin filter
- `interval` (optional): Time interval

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.chain.exchange_flows",
  "symbol": "ETH"
}
```

**Use Cases:**
- Detect sell pressure (inflows)
- Accumulation signal (outflows)
- Exchange balance changes

---

#### `coinglass.onchain.reserves`
Get on-chain reserves for symbol.

**Parameters:**
- `symbol` (required): Trading symbol

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.onchain.reserves",
  "symbol": "BTC"
}
```

**Use Cases:**
- Track exchange reserve changes
- Supply on exchanges vs cold storage

---

### Technical Indicators

#### `coinglass.indicators.rsi`
Get RSI (Relative Strength Index) indicator.

**Parameters:**
- `symbol` (required): Trading symbol
- `interval` (optional): Timeframe (default: "1h")
- `exchange` (optional): Exchange filter

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.indicators.rsi",
  "symbol": "BTC",
  "interval": "4h"
}
```

**Use Cases:**
- Identify overbought/oversold conditions
- RSI divergence analysis
- Mean reversion signals

---

#### `coinglass.indicators.rsi_list`
Get RSI values for all supported coins at once.

**Parameters:**
- `interval` (optional): Timeframe

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.indicators.rsi_list",
  "interval": "1h"
}
```

**Use Cases:**
- Screen all coins for oversold conditions
- Multi-coin RSI comparison
- Market-wide sentiment

---

#### `coinglass.indicators.fear_greed`
Get Crypto Fear & Greed Index.

**Parameters:** None

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.indicators.fear_greed"
}
```

**Use Cases:**
- Market sentiment gauge
- Contrarian signals (extreme fear/greed)
- Timing market entries/exits

---

#### `coinglass.indicators.whale_index`
Get Whale Index (measures whale activity intensity).

**Parameters:**
- `symbol` (optional): Symbol filter

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.indicators.whale_index",
  "symbol": "BTC"
}
```

**Use Cases:**
- Detect whale accumulation phases
- Smart money activity tracking

---

### Open Interest

#### `coinglass.open_interest.history`
Get open interest history for symbol.

**Parameters:**
- `symbol` (required): Trading symbol
- `interval` (optional): Time interval
- `exchange` (optional): Exchange filter

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.open_interest.history",
  "symbol": "BTC",
  "interval": "1h"
}
```

**Use Cases:**
- Track leverage buildup
- Identify potential squeeze zones
- Correlation with price movements

---

#### `coinglass.open_interest.aggregated_history`
Get aggregated OI across all exchanges.

**Parameters:**
- `symbol` (required): Trading symbol

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.open_interest.aggregated_history",
  "symbol": "ETH"
}
```

**Use Cases:**
- Total market leverage analysis
- Cross-exchange comparison

---

### Funding Rate

#### `coinglass.funding_rate.history`
Get funding rate history.

**Parameters:**
- `symbol` (required): Trading symbol
- `exchange` (optional): Exchange filter

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.funding_rate.history",
  "symbol": "BTC"
}
```

**Use Cases:**
- Detect overleveraged longs/shorts
- Funding rate arbitrage opportunities
- Sentiment analysis

---

#### `coinglass.funding_rate.oi_weight_history`
Get OI-weighted funding rate (weighted by open interest across exchanges).

**Parameters:**
- `symbol` (required): Trading symbol

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.funding_rate.oi_weight_history",
  "symbol": "BTC"
}
```

**Use Cases:**
- More accurate funding rate (accounts for exchange size)
- Better representation of true market cost

---

### Long/Short Ratio

#### `coinglass.long_short_ratio.account_history`
Get long/short ratio by account count.

**Parameters:**
- `symbol` (required): Trading symbol
- `exchange` (optional): Exchange filter

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.long_short_ratio.account_history",
  "symbol": "BTC"
}
```

**Use Cases:**
- Retail sentiment gauge
- Contrarian signals (fade the crowd)

---

#### `coinglass.long_short_ratio.position_history`
Get long/short ratio by position size.

**Parameters:**
- `symbol` (required): Trading symbol

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.long_short_ratio.position_history",
  "symbol": "ETH"
}
```

**Use Cases:**
- Whale positioning analysis
- Smart money vs retail comparison

---

### ETF Data

#### `coinglass.etf.flows`
Get Bitcoin/Ethereum ETF flows.

**Parameters:**
- `asset` (required): "BTC" or "ETH"

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.etf.flows",
  "asset": "BTC"
}
```

**Use Cases:**
- Track institutional inflows/outflows
- Bitcoin ETF adoption trends
- Macro demand signals

---

### Market Indices

#### `coinglass.index.bull_market_peak`
Get bull market peak indicator (detects cycle tops).

**Parameters:** None

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.index.bull_market_peak"
}
```

**Use Cases:**
- Cycle top detection
- Risk management (reduce exposure near peak)

---

#### `coinglass.index.rainbow_chart`
Get Bitcoin rainbow chart data (long-term valuation bands).

**Parameters:** None

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.index.rainbow_chart"
}
```

**Use Cases:**
- Long-term BTC valuation
- Buying/selling zones
- Macro cycle positioning

---

#### `coinglass.index.stock_to_flow`
Get stock-to-flow model data.

**Parameters:** None

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.index.stock_to_flow"
}
```

**Use Cases:**
- Bitcoin scarcity model
- Long-term price prediction
- Halving cycle analysis

---

### Dashboard

#### `coinglass.dashboard.symbol`
Get comprehensive dashboard with multiple data points.

**Parameters:**
- `symbol` (required): Trading symbol

**Example Request (FLAT format):**
```json
{
  "operation": "coinglass.dashboard.symbol",
  "symbol": "BTC"
}
```

**Use Cases:**
- Complete market overview for symbol
- Aggregated data from multiple endpoints

---

## Common GPT Action Patterns

### Pattern 1: Quick Market Check
**User asks:** "What's happening with BTC right now?"

**GPT should call (FLAT format):**
```json
{
  "operation": "coinglass.markets.symbol",
  "symbol": "BTC"
}
```

### Pattern 2: Liquidation Analysis
**User asks:** "Show me BTC liquidation heatmap"

**GPT should call (FLAT format):**
```json
{
  "operation": "coinglass.liquidations.heatmap",
  "symbol": "BTC"
}
```

### Pattern 3: Whale Tracking
**User asks:** "Are whales buying ETH?"

**GPT should call (FLAT format):**
```json
{
  "operation": "coinglass.chain.whale_transfers",
  "symbol": "ETH"
}
```

### Pattern 4: Sentiment Analysis
**User asks:** "What's the market sentiment?"

**GPT should call (FLAT format):**
```json
{
  "operation": "coinglass.indicators.fear_greed"
}
```

### Pattern 5: Multi-Indicator Analysis
**User asks:** "Give me full analysis for SOL"

**GPT should call multiple operations (all FLAT format):**
```json
{
  "operation": "coinglass.markets.symbol",
  "symbol": "SOL"
}
```
```json
{
  "operation": "coinglass.indicators.rsi",
  "symbol": "SOL"
}
```
```json
{
  "operation": "coinglass.funding_rate.history",
  "symbol": "SOL"
}
```
```json
{
  "operation": "coinglass.liquidations.heatmap",
  "symbol": "SOL"
}
```

---

## Important Notes

1. **All operations use FLAT parameters** - Never nest under `args`
2. **Symbol format**: Use base asset only (e.g., "BTC", not "BTCUSDT")
3. **Optional parameters**: Most operations have sensible defaults
4. **Rate limits**: Premium tier allows high request volume
5. **Error handling**: Operations return `ok: true/false` with error details

## API Endpoint
All operations are called via:
```
POST https://cryptosatx.replit.app/invoke
```

Request body format (FLAT parameters):
```json
{
  "operation": "coinglass.category.operation_name",
  "symbol": "BTC",
  "other_param": "value"
}
```

---

**Total Coinglass Operations Available:** 64 endpoints across 14 categories
**Parameter Format:** FLAT (never nested under `args`)

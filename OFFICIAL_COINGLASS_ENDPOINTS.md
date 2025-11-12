# Official Coinglass v4 API Endpoints (from docs.coinglass.com)

## 📊 COMPLETE ENDPOINT LIST (100+)

### **1. MARKET DATA (5 endpoints)**
- `/futures/supported-coins` - Get supported futures coins
- `/futures/supported-exchange-pairs` - Get supported exchanges and pairs
- `/api/futures/pairs-markets` - Futures pair markets
- `/api/futures/coins-markets` - Futures coin markets ⭐
- `/futures/price-change-list` - Price change list
- `/api/price/ohlc-history` - Price OHLC history

### **2. OPEN INTEREST (6 endpoints)**
- `/api/futures/openInterest/ohlc-history` - OI OHLC history
- `/api/futures/openInterest/ohlc-aggregated-history` - Aggregated OI OHLC ⭐
- `/api/futures/openInterest/ohlc-aggregated-stablecoin` - Stablecoin OI
- `/api/futures/openInterest/ohlc-aggregated-coin-margin-history` - Coin margin OI
- `/api/futures/openInterest/exchange-list` - OI by exchange
- `/api/futures/openInterest/exchange-history-chart` - OI chart by exchange

### **3. FUNDING RATE (6 endpoints)**
- `/api/futures/fundingRate/ohlc-history` - Funding rate OHLC ⭐
- `/api/futures/fundingRate/oi-weight-ohlc-history` - OI-weighted funding
- `/api/futures/fundingRate/vol-weight-ohlc-history` - Volume-weighted funding
- `/api/futures/fundingRate/exchange-list` - Funding by exchange
- `/api/futures/fundingRate/accumulated-exchange-list` - Cumulative funding
- `/api/futures/fundingRate/arbitrage` - Funding arbitrage

### **4. LONG/SHORT RATIO (4 endpoints)**
- `/api/futures/global-long-short-account-ratio/history` - Global ratio ✅ USING
- `/api/futures/top-long-short-account-ratio/history` - Top trader account ratio
- `/api/futures/top-long-short-position-ratio/history` - Top trader position ✅ USING
- `/api/futures/taker-buy-sell-volume/exchange-list` - Taker Buy/Sell ratio

### **5. LIQUIDATION (13 endpoints)** 
- `/api/futures/liquidation/history` - Pair liquidation history ✅ USING
- `/api/futures/liquidation/aggregated-history` - Coin liquidation history
- `/api/futures/liquidation/coin-list` - Liquidation coin list ✅ USING
- `/api/futures/liquidation/exchange-list` - Liquidation exchange list
- `/api/futures/liquidation/order` - Liquidation orders
- `/api/futures/liquidation/heatmap/model1` - Heatmap model 1
- `/api/futures/liquidation/heatmap/model2` - Heatmap model 2
- `/api/futures/liquidation/heatmap/model3` - Heatmap model 3
- `/api/futures/liquidation/aggregated-heatmap/model1` - Aggregated heatmap 1
- `/api/futures/liquidation/aggregated-heatmap/model2` - Aggregated heatmap 2
- `/api/futures/liquidation/aggregated-heatmap/model3` - Aggregated heatmap 3
- `/api/futures/liquidation/map` - Pair liquidation map
- `/api/futures/liquidation/aggregated-map` - Coin liquidation map

### **6. ORDERBOOK (5 endpoints)**
- `/api/futures/orderbook/ask-bids-history` - Pair orderbook bid/ask
- `/api/futures/orderbook/aggregated-ask-bids-history` - Coin orderbook
- `/api/futures/orderbook/history` - Orderbook heatmap
- `/api/futures/orderbook/large-limit-order` - Large orders
- `/api/futures/orderbook/large-limit-order-history` - Large orders history

### **7. WHALE POSITIONS (2 endpoints)**
- `/api/hyperliquid/whale-alert` - Hyperliquid whale alerts
- `/api/hyperliquid/whale-position` - Hyperliquid whale positions

### **8. TAKER BUY/SELL (2 endpoints)**
- `/api/futures/taker-buy-sell-volume/history` - Pair taker history
- `/api/futures/aggregated-taker-buy-sell-volume/history` - Coin taker history

### **9. SPOT MARKETS (5 endpoints)**
- `/api/spot/supported-coins` - Supported spot coins
- `/api/spot/supported-exchange-pairs` - Spot pairs
- `/api/spot/coins-markets` - Spot coin markets
- `/api/spot/pairs-markets` - Spot pair markets
- `/api/spot/price/history` - Spot price history

### **10. SPOT ORDERBOOK (5 endpoints)**
- `/api/spot/orderbook/ask-bids-history` - Spot orderbook
- `/api/spot/orderbook/aggregated-ask-bids-history` - Aggregated spot orderbook
- `/api/spot/orderbook/history` - Spot orderbook heatmap
- `/api/spot/orderbook/large-limit-order` - Large spot orders
- `/api/spot/orderbook/large-limit-order-history` - Large spot history

### **11. SPOT TAKER (2 endpoints)**
- `/api/spot/taker-buy-sell-volume/history` - Spot taker history
- `/api/spot/aggregated-taker-buy-sell-volume/history` - Aggregated spot taker

### **12. OPTIONS (4 endpoints)**
- `/api/option/max-pain` - Option max pain
- `/api/option/info` - Options info
- `/api/option/exchange-oi-history` - Exchange OI history
- `/api/option/exchange-vol-history` - Exchange volume history

### **13. ON-CHAIN (4 endpoints)**
- `/api/exchange/assets` - Exchange assets ⭐
- `/api/exchange/balance/list` - Exchange balance list
- `/api/exchange/balance/chart` - Exchange balance chart
- `/api/exchange/chain/tx/list` - On-chain transfers (ERC-20)

### **14. ETF (10 endpoints)**
- `/api/etf/bitcoin/list` - Bitcoin ETF list
- `/api/hk-etf/bitcoin/flow-history` - HK ETF flows
- `/api/etf/bitcoin/net-assets/history` - ETF net assets
- `/api/etf/bitcoin/flow-history` - ETF flows
- `/api/etf/bitcoin/premium-discount/history` - ETF premium/discount
- `/api/etf/bitcoin/history` - ETF history
- `/api/etf/bitcoin/price/history` - ETF price
- `/api/etf/bitcoin/detail` - ETF details
- `/api/etf/ethereum/net-assets-history` - ETH ETF net assets
- `/api/etf/ethereum/list` - ETH ETF list
- `/api/etf/ethereum/flow-history` - ETH ETF flows
- `/api/grayscale/holdings-list` - Grayscale holdings
- `/api/grayscale/premium-history` - Grayscale premium

### **15. INDICATORS (20+ endpoints)**
- `/api/futures/rsi/list` - RSI list ⭐
- `/api/futures/basis/history` - Futures basis
- `/api/coinbase-premium-index` - Coinbase premium
- `/api/bitfinex-margin-long-short` - Bitfinex margin
- `/api/index/ahr999` - AHR999
- `/api/index/puell-multiple` - Puell Multiple
- `/api/index/stock-flow` - Stock-to-Flow
- `/api/index/pi-cycle-indicator` - Pi Cycle Top
- `/api/index/golden-ratio-multiplier` - Golden Ratio
- `/api/index/bitcoin/profitable-days` - Bitcoin profitable days
- `/api/index/bitcoin/rainbow-chart` - Rainbow Chart
- `/api/index/fear-greed-history` - Fear & Greed ✅ USING
- `/api/index/stableCoin-marketCap-history` - Stablecoin market cap
- `/api/index/bitcoin/bubble-index` - Bitcoin Bubble Index
- `/api/bull-market-peak-indicator` - Bull market peak
- `/api/index/2-year-ma-multiplier` - 2-year MA multiplier
- `/api/index/200-week-moving-average-heatmap` - 200-week MA heatmap
- `/api/borrow-interest-rate/history` - Borrow interest rate

---

## ⭐ RECOMMENDED HIGH-VALUE ENDPOINTS TO ADD

Based on signal generation value:

### Priority 1 (Critical for Trading Signals):
1. `/api/futures/coins-markets` - Comprehensive market data for all coins
2. `/api/futures/fundingRate/ohlc-history` - Funding rate analysis
3. `/api/futures/openInterest/ohlc-aggregated-history` - OI trend (currently using OKX fallback)
4. `/api/futures/rsi/list` - RSI for 535+ coins

### Priority 2 (Whale & Smart Money):
5. `/api/exchange/assets` - Exchange wallet holdings (whale tracking)
6. `/api/futures/orderbook/aggregated-ask-bids-history` - Orderbook depth
7. `/api/hyperliquid/whale-alert` - Hyperliquid whale movements
8. `/api/futures/orderbook/large-limit-order` - Large limit orders

### Priority 3 (Enhanced Analysis):
9. `/api/futures/liquidation/aggregated-heatmap/model1` - Liquidation heatmap
10. `/api/index/bitcoin/bubble-index` - Bubble detection

---

## 📝 NOTES

**Legend:**
- ✅ USING = Currently implemented in production
- ⭐ = High priority to add (recommended)

**Total Official Endpoints:** 100+  
**Currently Using:** 5 endpoints  
**Verified Working:** 9 endpoints  
**High Priority to Test:** 10 endpoints

**Next Steps:**
1. Test high-priority endpoints with correct paths
2. Implement top 3-5 most valuable endpoints
3. Update documentation with accurate endpoint counts

# MSS Alpha System - Multi-Modal Signal Score

## 🎯 Overview

The Multi-Modal Signal Score (MSS) Alpha System is a **3-phase analytical framework** designed to identify high-potential cryptocurrency opportunities before retail adoption. Unlike traditional signal systems that analyze established coins, MSS focuses on **discovering emerging assets** with strong fundamentals and institutional accumulation.

## 📊 System Architecture

### Core Philosophy

MSS uses a **phased filtering approach** rather than analyzing all coins equally:

1. **Phase 1: Discovery (30 points max)** - Tokenomics filtering to find fundamentally sound new coins
2. **Phase 2: Social Confirmation (35 points max)** - Social momentum validation to confirm community interest
3. **Phase 3: Institutional Validation (35 points max)** - Whale/institutional positioning to detect smart money flow

**Total MSS Score**: 0-100 scale, weighted composite of all 3 phases

---

## 🔧 Technical Implementation

### Files Structure

```
app/
├── core/
│   └── mss_engine.py          # Scoring logic & weighted calculations
├── services/
│   └── mss_service.py         # Service orchestrator (reuses existing APIs)
└── api/
    └── routes_mss.py          # 5 MSS REST endpoints
```

### Dependencies & Data Sources

MSS **reuses all existing services** from the main signal system:

| Service | Purpose | Current Status |
|---------|---------|----------------|
| **CoinGeckoService** | Coin discovery, FDV, market cap, volume | ✅ **Phase 1 - ACTIVE** |
| **BinanceFuturesService** | 24hr stats, futures availability | ✅ **Phase 1 - ACTIVE** |
| **LunarCrushService** | Social metrics (AltRank, Galaxy Score, sentiment) | ✅ **Phase 2 - ACTIVE** |
| **CoinAPIComprehensiveService** | Trade volume, buy/sell pressure | 🔧 **Phase 2 - PLANNED** |
| **CoinglassPremiumService** | OI trends, funding, top trader positioning | 🔧 **Phase 3 - PLANNED** |

_**Current Limitation:** Phase 2/3 are using placeholder Binance 24hr ticker data instead of proper CoinAPI/Coinglass Premium integrations. This causes volume spike and whale detection to always return 0/false. See Known Limitations section for details._

---

## 🚀 API Endpoints

### 1. **GET /mss/info**
System information and configuration.

**Response:**
```json
{
  "system": "Multi-Modal Signal Score (MSS) Alpha",
  "version": "1.0.0",
  "description": "3-phase crypto discovery system...",
  "phases": {
    "phase1": "Discovery (tokenomics)",
    "phase2": "Social Confirmation",
    "phase3": "Institutional Validation"
  },
  "max_score": 100,
  "endpoints": [...]
}
```

### 2. **GET /mss/discover**
Discover new coins meeting discovery criteria.

**Parameters:**
- `max_fdv` (int, default=50000000): Maximum fully diluted valuation in USD
- `max_age_hours` (int, default=72): Maximum age in hours since listing
- `min_volume` (int, default=100000): Minimum 24h volume in USD
- `limit` (int, default=50): Max coins to return

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-11-10T15:30:00Z",
  "filters": {
    "max_fdv_usd": 50000000,
    "max_age_hours": 72,
    "min_volume_24h_usd": 100000
  },
  "total_discovered": 12,
  "coins": [
    {
      "symbol": "NEWCOIN",
      "name": "New Coin",
      "fdv_usd": 25000000,
      "market_cap_usd": 15000000,
      "volume_24h_usd": 250000,
      "age_hours": 48,
      "discovery_score": 20.0,
      "discovery_breakdown": {
        "status": "PASS",
        "fdv_score": 15.0,
        "age_score": 5.0,
        "supply_score": 0,
        "total": 20.0
      },
      "source": "coingecko",
      "note": "Discovery score matches breakdown total"
    }
  ]
}
```

### 3. **GET /mss/analyze/{symbol}**
Full 3-phase MSS analysis for any coin.

**Parameters:**
- `symbol` (path): Coin symbol (e.g., BTC, ETH)
- `include_raw` (bool, default=false): Include raw metrics from all phases

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-11-10T15:35:00Z",
  "symbol": "BTC",
  "mss_score": 30.75,
  "signal": "NEUTRAL",
  "confidence": "insufficient",
  "breakdown": {
    "phase1_discovery": {
      "score": 0,
      "status": "SKIP",
      "reason": "Not a new coin (Phase 1 skipped for established assets)"
    },
    "phase2_social": {
      "score": 23.75,
      "status": "PASS",
      "altrank_score": 10.0,
      "galaxy_score": 8.75,
      "sentiment_score": 5.0,
      "volume_spike_score": 0.0
    },
    "phase3_validation": {
      "score": 7.0,
      "status": "PARTIAL",
      "oi_trend_score": 3.5,
      "funding_score": 3.5,
      "whale_accumulation": false
    }
  },
  "warnings": [],
  "note": "Sum: 0 + 23.75 + 7.0 = 30.75"
}
```

### 4. **GET /mss/scan**
Auto-scan for high-potential coins.

**Parameters:**
- `max_fdv` (int, default=50000000): Max FDV filter
- `max_age_hours` (int, default=72): Max age filter
- `min_mss_score` (float, default=60.0): Minimum MSS score threshold
- `limit` (int, default=20): Max results

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-11-10T15:40:00Z",
  "scan_parameters": {
    "max_fdv_usd": 50000000,
    "max_age_hours": 72,
    "min_mss_score": 60.0
  },
  "total_high_potential": 3,
  "coins": [
    {
      "symbol": "NEWCOIN",
      "mss_score": 62.5,
      "signal": "LONG",
      "confidence": "medium",
      "fdv_usd": 30000000,
      "age_hours": 36,
      "note": "Current max MSS ~70 due to Phase 2/3 limitations"
    }
  ],
  "summary": {
    "avg_mss_score": 58.33,
    "strong_signals": 0,
    "long_signals": 2,
    "note": "Scores lower than designed due to Phase 2/3 data limitations"
  }
}
```

### 5. **GET /mss/watch**
Watchlist management (Coming Soon).

Currently returns placeholder response. Future enhancement will track discovered coins over time.

---

## 📈 Scoring System Details

### Phase 1: Discovery (0-30 points)

**Target Criteria:**
- FDV: < $50M (smaller = higher score)
- Age: < 72 hours (newer = higher score)
- Circulating Supply: < 30% (lower = higher score)
- Market Cap: Bonus for < $10M

**Scoring Breakdown:**
- FDV Score: 0-20 points
- Age Score: 0-10 points
- Supply Score: 0-10 points (bonus)
- Market Cap Bonus: 0-5 points (bonus)

**Pass Threshold:** ≥ 15 points to proceed to Phase 2

### Phase 2: Social Confirmation (0-35 points)

**Data Sources (Current):**
- ✅ LunarCrush: AltRank, Galaxy Score, sentiment
- 🔧 Trade Volume: **Currently unavailable** (always 0 - see Known Limitations)

**Data Sources (Planned):**
- CoinAPI Comprehensive: Buy/sell pressure, volume spike detection

**Scoring Breakdown:**
- AltRank: 0-10 points (lower AltRank = higher score)
- Galaxy Score: 0-10 points (65+ = 10pts, 50-65 = 5pts)
- Sentiment: 0-10 points (positive bias)
- Volume Spike: 0-5 points (**currently always 0** - requires CoinAPI integration)

**Current Max Score:** 30 points (instead of 35 due to volume spike limitation)
**Pass Threshold:** ≥ 17.5 points to proceed to Phase 3

### Phase 3: Institutional Validation (0-35 points)

**Data Sources (Current):**
- 🔧 Coinglass Basic: Generic market data (**incomplete** - see Known Limitations)
- 🔧 Binance 24hr Ticker: Placeholder for volume (**inaccurate** - see Known Limitations)

**Data Sources (Planned):**
- Coinglass Premium: OI trends, funding rates, top trader positioning
- CoinAPI: Whale detection via orderbook/trades

**Scoring Breakdown:**
- OI Trend: 0-15 points (**currently unreliable** - lacks historical data)
- Funding Rate: 0-10 points (**currently basic** - lacks exchange comparison)
- Whale Accumulation: 0-10 points (**currently always false** - missing trader ratios)

**Whale Detection Criteria (Designed but not yet functional):**
- OI change > 50%
- Top trader long ratio: 1.5-2.5 (sweet spot)
- Volume increasing > 30%

**Current Max Score:** ~10 points (instead of 35 due to data mapping issues)
**Impact:** Phase 3 validation currently unreliable - requires Coinglass Premium integration

---

## 🎯 Signal Classification

| MSS Score | Signal | Confidence | Interpretation | Current Achievability |
|-----------|--------|------------|----------------|----------------------|
| 80-100 | STRONG_LONG | very_high | Exceptional opportunity, all phases aligned | 🔴 **Not reachable** (Phase 2/3 limits) |
| 65-79 | MODERATE_LONG | high | Strong fundamentals, good entry | 🟡 **Rarely reachable** (needs perfect Phase 1+2) |
| 50-64 | LONG | medium | Passing all phases, monitor closely | 🟢 **Achievable** (realistic range) |
| 35-49 | NEUTRAL | insufficient | Mixed signals, wait for clarity | 🟢 **Common** (typical for established coins) |
| 0-34 | NEUTRAL | insufficient | Weak or incomplete data | 🟢 **Common** (missing data or poor fit) |

**Note:** With current Phase 2/3 limitations, max realistic MSS score is ~70 points. Full 0-100 scale will be available after data mapping fixes.

---

## ✅ Current Status

### **Working Features:**
- ✅ All 5 MSS endpoints operational (returning responses)
- ✅ 3-phase scoring engine with weighted calculations (logic complete)
- ✅ Phase 1: CoinGecko + Binance Futures coin discovery **FULLY FUNCTIONAL**
- ✅ Phase 2: LunarCrush social metrics integration **PARTIALLY FUNCTIONAL** (missing volume spike)
- ✅ Real-time timestamps and error handling
- ✅ 100% backward compatible (no breaking changes to existing endpoints)

### **Functional Limitations:**
- 🟡 Phase 2: Social scoring works but limited to ~30/35 max points (no volume spike detection)
- 🔴 Phase 3: Validation scoring degraded to ~10/35 max points (placeholder data only)
- 🔴 Overall MSS scores are **lower than designed** due to Phase 2/3 limitations
- 🟡 System is **operational but not production-ready** until data mappings fixed

### **Known Limitations:**

#### 1. **Phase 2: Volume Analysis** 🔧
**Current Behavior:** Volume change calculation attempts to use Binance 24hr ticker `prevVolume` field which doesn't exist in response. Falls back to 0% change.

**Impact:** Volume spike detection **always returns 0%**, missing real volume surges. Phase 2 max score reduced from 35 to 30 points.

**Root Cause:** Incorrect service mapping - using generic Binance ticker instead of trade history.

**Solution Required:** Replace with `CoinAPIComprehensiveService.get_recent_trades()` which provides actual buy/sell volume pressure over time.

**Code Location:** `app/services/mss_service.py` lines 219-226

#### 2. **Phase 3: Top Trader Ratio** 🔧
**Current Behavior:** Attempting to extract `longShortRatio` from general Coinglass market data which doesn't contain trader positioning. Falls back to None, causing whale detection to always return false.

**Impact:** Whale accumulation detection **always fails**, never detecting institutional flow. Phase 3 max score reduced from 35 to ~10 points.

**Root Cause:** Incorrect service mapping - using basic Coinglass endpoint instead of Premium trader ratios endpoint.

**Solution Required:** Replace with `CoinglassPremiumService.get_top_trader_ratio()` which returns proper `topTraderLongPct` field (already used in main signal engine).

**Code Location:** `app/services/mss_service.py` lines 301-309

#### 3. **OI Change Calculation** 🔧
**Current Behavior:** Attempting to calculate OI change from single data point without historical reference. Falls back to 0% or neutral.

**Impact:** OI trend scoring unreliable - cannot detect increasing/decreasing OI properly.

**Root Cause:** No historical data or previous value comparison.

**Solution Required:** Either (a) store previous OI values in database for delta calc, or (b) use Coinglass historical OI endpoint with multiple timepoints.

**Code Location:** `app/services/mss_service.py` lines 283-291

---

## 🔮 Future Enhancements

### Short-term (Next Sprint):
1. **Fix Data Mappings** - Correct Phase 2/3 service calls (see Known Limitations)
2. **Add Integration Tests** - Verify all 3 phases with real API responses
3. **GPT Actions Schema** - Add MSS endpoints to `/gpt/action-schema`
4. **Logging Improvements** - Add detailed phase-by-phase logging

### Medium-term:
1. **Telegram Integration** - Send MSS alerts for high-scoring discoveries
2. **Database Storage** - Save MSS signals to `signals` table with phase breakdowns
3. **Watchlist Feature** - Track discovered coins over time (implement `/mss/watch`)
4. **Historical Analysis** - Store and analyze MSS score evolution

### Long-term:
1. **Machine Learning** - Train model on successful MSS predictions
2. **Multi-Exchange Support** - Expand beyond Binance for more coverage
3. **Custom Criteria** - User-configurable thresholds per phase
4. **Backtesting** - Historical MSS performance analysis

---

## 💡 Usage Examples

### Example 1: Discover New Small Caps
```bash
# Find coins under $30M FDV, listed within 48 hours, min $50K volume
curl "http://localhost:8000/mss/discover?max_fdv=30000000&max_age_hours=48&min_volume=50000"
```

### Example 2: Analyze Specific Coin
```bash
# Full 3-phase analysis of PEPE
curl "http://localhost:8000/mss/analyze/PEPE?include_raw=true"
```

### Example 3: Scan for High-Potential Opportunities
```bash
# Find coins with MSS > 65, under $50M FDV
curl "http://localhost:8000/mss/scan?min_mss_score=65&max_fdv=50000000"
```

### Example 4: GPT Integration (Future)
```
User: "Find me new small cap gems under $20M with strong social momentum"
GPT → /mss/discover?max_fdv=20000000&max_age_hours=72
GPT → /mss/analyze/{top_results}
GPT → Presents top 3 with detailed MSS breakdown
```

---

## 🏗️ Integration with Existing System

### Workflow Comparison:

**Traditional Signal Flow:**
```
User/GPT → /signals/{symbol} → Signal Engine → Telegram → Database
```

**MSS Signal Flow (Planned):**
```
User/GPT → /mss/scan → MSS Engine → Telegram (future) → Database (future)
```

### Service Reuse:
MSS is **100% additive** - it reuses existing service infrastructure without breaking changes:

**Currently Active:**
- ✅ CoinGeckoService - Fully integrated (Phase 1)
- ✅ BinanceFuturesService - Fully integrated (Phase 1)
- ✅ LunarCrushService - Fully integrated (Phase 2)

**Planned Integrations:**
- 🔧 CoinglassPremiumService - Not yet integrated (Phase 3 needs fixing)
- 🔧 CoinAPIComprehensiveService - Not yet integrated (Phase 2 needs fixing)

**Compatibility:**
- ✅ No existing endpoints were changed or broken
- ✅ All existing services remain unchanged
- ✅ MSS is fully isolated in new module

---

## 📝 Development Notes

### Design Decisions:

1. **Why 3 Phases?** - Filters out noise early. Only ~5-10% of coins pass Phase 1, ~30% of those pass Phase 2, ensuring focused analysis on true opportunities.

2. **Why Weighted Scoring?** - Not all signals equal. Whale accumulation (10pts) more significant than sentiment (5pts).

3. **Why Separate from Traditional Signals?** - Different use case. Traditional signals optimize entries for established coins. MSS finds new opportunities before they're established.

4. **Why Reuse Services?** - DRY principle + maintainability. One source of truth for API integrations.

### Code Quality:
- Type hints throughout
- Comprehensive error handling with safe defaults
- Async/await for performance
- Logging at all critical points
- Docstrings for all public methods

---

## 🐛 Debugging

### Common Issues:

**1. Empty discovery results**
- **Cause:** Very strict filters (small FDV + new age + volume)
- **Solution:** Relax filters or check CoinGecko has data for new listings

**2. Phase scores always 0**
- **Cause:** API rate limits or invalid symbols
- **Solution:** Check logs for API errors, verify symbol format

**3. Whale accumulation always false**
- **Cause:** Known limitation (see Phase 3 issue above)
- **Solution:** Requires data mapping fix

### Logs to Check:
```bash
# Check API logs
tail -f /tmp/logs/api-server_*.log | grep MSS

# Check specific phase
curl "http://localhost:8000/mss/analyze/BTC?include_raw=true" | jq '.raw_metrics'
```

---

## 📚 References

- **CoinGecko API**: Coin discovery and tokenomics
- **LunarCrush API**: Social sentiment and engagement
- **Coinglass API**: Derivatives data and positioning
- **CoinAPI**: Trade and orderbook data

---

## 🎓 Contributing

When enhancing MSS system:

1. **Maintain backward compatibility** - Never break existing endpoints
2. **Follow existing patterns** - Match code style in other services
3. **Add tests** - Integration tests for each phase
4. **Document changes** - Update this guide and replit.md
5. **Architect review** - All major changes reviewed before merge

---

**System Status:** 🟡 **Functional with Known Limitations**

**Next Priority:** Fix Phase 2/3 data mappings for production readiness

**Version:** 1.0.0 (November 10, 2025)

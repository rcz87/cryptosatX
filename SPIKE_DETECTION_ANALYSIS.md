# CryptoSatX Spike Detection & Real-Time Monitoring Analysis

## Executive Summary

The codebase has **SUBSTANTIAL spike detection and alert infrastructure**, but lacks **real-time continuous monitoring** for sudden market changes. Most detection is **interval-based and scheduled** rather than event-driven.

---

## EXISTING CAPABILITIES

### 1. SPIKE DETECTION SYSTEMS

#### A. Social Spike Monitor
**File:** `/home/user/cryptosatX/app/services/social_spike_monitor.py`

- **What it detects:**
  - Social volume spikes (>100% minimum threshold)
  - 24h social changes detection
  - Spike levels: normal, moderate, high, extreme
  - Cooldown: 1-hour minimum between alerts for same spike
  - Monitors top 50 coins by market cap
  
- **Implementation:**
  - Background loop every 5 minutes (configurable)
  - Parallel processing via asyncio
  - Telegram alert integration
  - Detects changes: socialVolumeChange, socialEngagementChange, sentimentChange
  
- **Current Status:** IMPLEMENTED but NOT STARTED by default

#### B. Whale Activity Detection (Smart Money Service)
**File:** `/home/user/cryptosatX/app/services/smart_money_service.py`

- **What it detects:**
  - Whale accumulation (0-10 score)
  - Whale distribution (0-10 score)
  
- **Metrics used:**
  - Buy/Sell pressure (from CoinAPI trades)
  - Funding rates (whale crowding indicator)
  - Social activity (retail awareness)
  - Price action (sideways vs pumped)
  - Open interest changes
  
- **Detection logic:**
  - Accumulation: High buy pressure + low funding + low social + sideways price
  - Distribution: High sell pressure + high funding + high social + recent pump

#### C. Volume Spike Detection (MSS Service)
**File:** `/home/user/cryptosatX/app/services/mss_service.py`

- **What it detects:**
  - Volume spike from buy/sell pressure ratio
  - New listing volume surges
  - 24h volume analysis
  
- **Formula:** 
  - Volume spike = (buy_pressure - 50) * 2
  - Ranges from -100% to +100%
  - Detects divergence between buy and sell pressure

#### D. Price Change Detection (Comprehensive Services)
**File:** `/home/user/cryptosatX/app/services/coinglass_comprehensive_service.py`

- **What it provides:**
  - 5m, 15m, 30m, 1h, 4h, 12h, 24h price changes
  - OI/Volume ratio changes
  - Long/Short position ratio changes
  - Funding rate changes (OI-weighted and volume-weighted)
  
- **Not actively monitoring** but data is available

#### E. Hype Score Spike Detection
**File:** `/home/user/cryptosatX/app/services/hype_tracker.py`

- **What it detects:**
  - Social hype spikes (>20% increase threshold)
  - Historical hype snapshots stored in database
  - Severity classification:
    - EXTREME: >50% change
    - HIGH: >35% change
    - MODERATE: >20% change
  
- **Current Status:** PARTIAL - detection logic exists but not integrated into background monitoring

#### F. New Listings Detection with Stats
**Files:** 
- `/home/user/cryptosatX/app/services/binance_listings_monitor.py`
- `/home/user/cryptosatX/app/services/multi_exchange_listings_monitor.py`

- **What it detects:**
  - New perpetual futures listings (Binance, OKX, CoinAPI)
  - 24h volume and price changes for new listings
  - Trade count and activity metrics
  - Useful for identifying volume spikes on new listings
  
- **Current Status:** IMPLEMENTED but not background monitored

---

### 2. ALERT/NOTIFICATION SYSTEMS

#### A. Alert Service (Core Framework)
**File:** `/home/user/cryptosatX/app/services/alert_service.py`

- **Features:**
  - Multiple channels: Slack, Telegram, Email, Webhook
  - Customizable alert rules with Python expressions
  - Severity levels: LOW, MEDIUM, HIGH, CRITICAL
  - Cooldown/rate limiting (configurable per rule)
  - Default rules for:
    - High error rates (>5%)
    - Slow response times (>2s)
    - Low signal accuracy (<40%)
    - High memory usage (>85%)
    - API rate limiting
    - External API failures
    - Database connection pool issues
    - Low cache hit ratio (<70%)

#### B. Telegram Notifier (Signal Delivery)
**File:** `/home/user/cryptosatX/app/services/telegram_notifier.py`

- **Sends:** Formatted signal alerts with:
  - AI Verdict Layer
  - Volatility metrics
  - Stop loss / Take profit targets
  - Position sizing recommendations
  - Risk mode indicators
  - ATR-based targets
  - HTML-formatted "NEON CARD" style messages

#### C. Telegram MSS Notifier
**File:** `/home/user/cryptosatX/app/services/telegram_mss_notifier.py`

- **Sends:** MSS (Multimodal Signal Score) specific alerts

#### D. Monitoring Service
**File:** `/home/user/cryptosatX/app/services/monitoring_service.py`

- **Features:**
  - Monitors N symbols for signal changes
  - Alert types:
    - Strong signal alerts (>80 or <20 score)
    - Signal change alerts
    - Time-based alerts (every 6 hours)
  - Rate limiting: Max 10 alerts per hour per symbol
  - Configurable check intervals
  - Alert history caching

---

### 3. REAL-TIME CAPABILITIES

#### A. WebSocket Integration
**File:** `/home/user/cryptosatX/app/services/coinglass_websocket_service.py`

- **Provides:**
  - Live liquidation data streaming
  - WebSocket connection management
  - Auto-reconnect with 5-second interval
  - Ping/pong keepalive every 20 seconds
  - Supports real-time liquidation orders channel
  
- **Current Status:** IMPLEMENTED but NOT INTEGRATED INTO MAIN APP
- **Not started:** No automatic startup in lifespan

#### B. Liquidation Monitoring
**File:** `/home/user/cryptosatX/app/services/coinglass_comprehensive_service.py` (5200+ lines)

- **Real-time liquidation endpoints:**
  - `get_liquidation_orders()` - Current liquidations
  - `get_liquidation_exchange_list()` - By exchange over time
  - `get_liquidation_map()` - Aggregated liquidation map
  - `get_liquidation_coin_list()` - By coin
  - `get_liquidation_aggregated_history()` - Historical data
  - `get_liquidation_history()` - Detailed history
  
- **Whale position monitoring:**
  - `get_hyperliquid_whale_alerts()`
  - `get_hyperliquid_whale_positions()`
  - `get_hyperliquid_positions_by_symbol()`
  - `get_chain_whale_transfers()`
  - `get_whale_index()`

#### C. Funding Rate Monitoring
**Available in coinglass_comprehensive_service.py:**
- OI-weighted funding rate history
- Volume-weighted funding rate history
- Funding rate by exchange
- Accumulated funding rate (hourly/daily)
- Funding rate averages

---

### 4. SCANNER & SCHEDULER SYSTEMS

#### A. Auto Scanner (24/7 Monitoring)
**File:** `/home/user/cryptosatX/app/services/auto_scanner.py`

- **Scheduled scans:**
  - Smart Money: Every 1 hour
  - MSS Discovery: Every 6 hours
  - RSI Screener: Every 4 hours
  - Daily Summary: 8:00 AM
  
- **Uses APScheduler** for interval/cron-based scheduling
- **Sends Telegram alerts** for top signals
- **Tracks performance** automatically
- **Current Status:** STARTS AT APP STARTUP (if AUTO_SCAN_ENABLED=true)

#### B. Performance Tracker (Automated Outcome Tracking)
**File:** `/home/user/cryptosatX/app/services/performance_tracker.py`

- **Tracks signal outcomes at:**
  - 1 hour
  - 4 hours
  - 24 hours
  - 7 days
  - 30 days
  
- **Win/Loss criteria:**
  - LONG: WIN if +5%, LOSS if -3%
  - SHORT: WIN if -5%, LOSS if +3%
  - Uses APScheduler to schedule checks
  
- **Current Status:** STARTS AT APP STARTUP

#### C. Parallel Scanner (High-Performance)
**File:** `/home/user/cryptosatX/app/services/parallel_scanner.py`

- **Features:**
  - Scans 100+ coins in parallel
  - Dynamic rate limiting based on API response patterns
  - Connection pooling (reuses HTTP connections)
  - Batch processing with configurable batch size (50 default)
  - Retry logic with exponential backoff
  - Performance tracking: coins/second metrics
  
- **Supports:**
  - Smart Money scanning
  - MSS scanning
  - Signal scanning
  - Price scanning

---

## WHAT'S MISSING / GAPS

### 1. NO CONTINUOUS REAL-TIME MONITORING
- **Gap:** All systems are **interval-based** (hourly, every 6 hours, etc.)
- **Missing:** True real-time spike detection that triggers IMMEDIATELY when:
  - Price moves >10% in 5 minutes
  - Volume spikes >200% from baseline
  - Liquidations surge (>$10M in 1 minute)
  - Funding rates spike suddenly
  - Social volume jumps >300%
  
- **Why:** Would require:
  - Constant stream of market data (WebSocket)
  - Real-time change detection logic
  - Sub-second latency alerting

### 2. WEBSOCKET NOT INTEGRATED
- **Gap:** WebSocket service exists but is NOT started in app lifespan
- **Missing:** No background task to listen to Coinglass liquidation stream
- **Impact:** Missing real-time liquidation alerts

### 3. NO LIQUIDATION SPIKE DETECTION
- **Gap:** Liquidation data is available but:
  - NOT being fetched continuously
  - NO spike detection logic
  - NO alerts for large liquidations
  - NO long/short liquidation imbalance tracking

- **Example missing:** Alert when:
  - Long liquidations > $100M in 10 minutes
  - Short liquidations > $100M in 10 minutes
  - Liquidation/volume ratio suddenly changes

### 4. NO PRICE VELOCITY DETECTION
- **Gap:** Price changes are available (5m, 15m, 30m, etc.) but:
  - NOT being monitored continuously
  - NO alerts for sudden price moves
  - NO momentum spike detection
  
- **Missing logic:** Detect when:
  - Price moves >8% in 15 minutes
  - Price acceleration increases (rate of change of change)
  - Volatility spikes (ATR sudden increase)

### 5. PARTIALLY IMPLEMENTED SYSTEMS NOT ACTIVATED
- **Social Spike Monitor:** Built but needs to be started
- **Hype Tracker Spikes:** Detection logic exists but not integrated into monitoring loop
- **WebSocket Liquidation Streaming:** Built but not started
- **New Listings Monitor:** Detects listings but doesn't monitor for volume spikes on them

### 6. NO ORDERBOOK-BASED SPIKE DETECTION
- **Missing:** Monitoring for:
  - Sudden orderbook imbalance
  - Large buy/sell walls appearing
  - Orderbook depth changes
  - Bid/ask spread anomalies
  
- **Would need:** Orderbook WebSocket stream

### 7. NO FUNDING RATE SPIKE ALERTS
- **Gap:** Funding rate data available but:
  - Not being monitored for sudden changes
  - Not triggering alerts for extreme funding
  - Not detecting funding rate reversals
  
- **Missing:** Alert when:
  - Funding rate spikes >0.5% (hourly)
  - Funding rate suddenly reverses sign
  - Volume-weighted funding diverges from OI-weighted

### 8. NO WHALE ACTIVITY REAL-TIME ALERTS
- **Gap:** Whale detection exists but:
  - Only runs via manual scan or scheduled scanner
  - Not triggered by actual whale transaction events
  - No monitoring of chain-level whale transfers
  
- **Missing:** Real-time chain monitoring for:
  - Large wallet movements
  - Exchange deposit/withdrawal surges
  - Wallet consolidation patterns

### 9. NO CROSS-INDICATOR SPIKE CORRELATION
- **Missing:** Logic that combines multiple spikes:
  - Price spike + volume spike + liquidation spike = STRONG alert
  - Social spike + funding rate spike + whale activity = MEDIUM alert
  - Can reduce false positives

### 10. NO MARKET MICROSTRUCTURE MONITORING
- **Missing:**
  - Trade count acceleration
  - Trade size distribution changes
  - Imbalance ratio (buy count vs sell count)
  - Execution pressure indicators

---

## CURRENT ARCHITECTURE

### What IS Running
```
App Startup (lifespan)
  ├── Auto Scanner (24/7 scheduled scans)
  ├── Performance Tracker (outcome tracking at intervals)
  └── Cache cleanup task
```

### What's NOT Running
```
Social Spike Monitor (needs manual startup)
WebSocket Liquidation Stream (never started)
Hype Tracker spike detection (never integrated)
```

### Alert Flow
```
Detection Event (manual API call or scheduled scan)
  ├── Signal generated
  ├── Async alert service checks rules
  └── Telegram/Email/Slack/Webhook notifications sent
```

---

## RECOMMENDATIONS TO FILL GAPS

### Priority 1: Activate Existing Systems
1. Start Social Spike Monitor in app lifespan
2. Start WebSocket liquidation listener in app lifespan
3. Integrate Hype Tracker spike detection into monitoring loop
4. Create background task to monitor funding rate changes

### Priority 2: Add Real-Time Detection
1. Create WebSocket listener for price changes (5m candle updates)
2. Implement liquidation spike detector (>$50M in 5 min = alert)
3. Add funding rate spike detector (>0.1% change = alert)
4. Create volume spike detector (>300% of baseline)

### Priority 3: Advanced Correlation
1. Multi-indicator spike confirmation
2. False positive filtering
3. Risk-weighted alerting
4. Machine learning-based spike pattern recognition

---

## FILE REFERENCE SUMMARY

### Core Detection Services
- `/home/user/cryptosatX/app/services/social_spike_monitor.py` (308 lines)
- `/home/user/cryptosatX/app/services/smart_money_service.py` (765 lines)
- `/home/user/cryptosatX/app/services/hype_tracker.py` (partial)
- `/home/user/cryptosatX/app/services/mss_service.py` (668 lines)

### Alert Systems
- `/home/user/cryptosatX/app/services/alert_service.py` (535 lines)
- `/home/user/cryptosatX/app/services/telegram_notifier.py` (378 lines)
- `/home/user/cryptosatX/app/services/monitoring_service.py` (~350 lines)

### Real-Time & Data
- `/home/user/cryptosatX/app/services/coinglass_websocket_service.py` (191 lines)
- `/home/user/cryptosatX/app/services/coinglass_comprehensive_service.py` (5233 lines)
- `/home/user/cryptosatX/app/services/binance_listings_monitor.py` (341 lines)

### Scheduling & Background Tasks
- `/home/user/cryptosatX/app/services/auto_scanner.py` (597 lines)
- `/home/user/cryptosatX/app/services/performance_tracker.py` (200+ lines)
- `/home/user/cryptosatX/app/services/parallel_scanner.py` (~423 lines)

### Integration Point
- `/home/user/cryptosatX/app/main.py` (FastAPI lifespan manager)


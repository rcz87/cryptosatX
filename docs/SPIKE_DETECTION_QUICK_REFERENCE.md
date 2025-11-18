# Spike Detection Quick Reference Guide

## WHAT EXISTS (Can Be Used Today)

### 1. Social Volume Spikes
**Threshold:** >100% change  
**File:** `/home/user/cryptosatX/app/services/social_spike_monitor.py` (308 lines)  
**Status:** Implemented, not auto-started  
**How to start:** 
```python
from app.services.social_spike_monitor import social_spike_monitor
await social_spike_monitor.start()
```

### 2. Whale Activity Detection
**Thresholds:**
- Accumulation score >7 = alert
- Distribution score >7 = alert  
**File:** `/home/user/cryptosatX/app/services/smart_money_service.py` (765 lines)  
**Status:** Auto-scanned hourly (if AUTO_SCAN_ENABLED=true)  
**Metrics used:**
- Buy pressure >80% (whale buying)
- Sell pressure >80% (whale selling)
- Funding rate <0% (quiet market)
- Funding rate >0.5% (crowded)

### 3. Volume Spikes (Buy/Sell Pressure)
**Formula:** Volume_spike = (buy_pressure - 50) * 2  
**File:** `/home/user/cryptosatX/app/services/mss_service.py` (668 lines)  
**Range:** -100% to +100%  
**Status:** Auto-scanned every 6 hours

### 4. Hype Spikes
**Threshold:** >20% increase  
**Severity levels:**
- EXTREME: >50% change
- HIGH: >35% change
- MODERATE: >20% change  
**File:** `/home/user/cryptosatX/app/services/hype_tracker.py`  
**Status:** Logic exists, not integrated into monitoring

### 5. New Listing Volume Spikes
**Detects:** 
- New perpetual futures within 24h
- 24h volume statistics
- Price changes
- Trade count activity  
**Files:** 
- `/home/user/cryptosatX/app/services/binance_listings_monitor.py` (341 lines)
- `/home/user/cryptosatX/app/services/multi_exchange_listings_monitor.py` (357 lines)  
**Status:** Implemented, can be called manually

### 6. Price Changes at Multiple Timeframes
**Available from:** `/home/user/cryptosatX/app/services/coinglass_comprehensive_service.py`  
**Timeframes:** 5m, 15m, 30m, 1h, 4h, 12h, 24h  
**Status:** Data available, not auto-monitored for spikes

---

## WHAT EXISTS BUT NOT ACTIVATED

### 1. WebSocket Real-Time Liquidation Stream
**File:** `/home/user/cryptosatX/app/services/coinglass_websocket_service.py` (191 lines)  
**Provides:** Live liquidation orders as they happen  
**Current status:** NOT STARTED in app  
**To activate:**
```python
from app.services.coinglass_websocket_service import CoinglassWebSocketService
ws_service = CoinglassWebSocketService()
await ws_service.stream_liquidations(message_handler)
```

### 2. Alert Service Framework
**File:** `/home/user/cryptosatX/app/services/alert_service.py` (535 lines)  
**Channels:** Slack, Telegram, Email, Webhook  
**Features:** 
- Custom rule expressions
- Severity levels: LOW, MEDIUM, HIGH, CRITICAL
- Cooldown/rate limiting
- Alert history tracking

**Status:** Implemented, not used for spike detection yet

---

## WHAT'S MISSING

### Critical Gaps (Real-Time Focused)
1. **No continuous liquidation monitoring** - WebSocket built but not running
2. **No funding rate spike alerts** - Data available but no monitoring
3. **No real-time price velocity** - Only 5m+ candle data monitored
4. **No orderbook monitoring** - Would need exchange WebSocket
5. **No cross-indicator correlation** - Price + volume + liquidation not combined

### Major Gaps (Feature Complete)
1. **Liquidation spike detection** - (>$100M in 10 min not flagged)
2. **Funding rate anomalies** - (Reversals not detected)
3. **Whale transfer tracking** - (On-chain movements not monitored)
4. **Trade execution pressure** - (Trade acceleration not detected)
5. **Volatility spike alerts** - (ATR changes not monitored)

---

## DETECTION CAPABILITIES MATRIX

| Feature | Status | Frequency | Method |
|---------|--------|-----------|--------|
| Social volume spikes | Implemented | Every 5 min | Loop |
| Whale accumulation | Implemented | Every 1 hour | Scan |
| Whale distribution | Implemented | Every 1 hour | Scan |
| Volume spikes | Implemented | Every 6 hours | Scan |
| Hype spikes | Partial | Not active | Manual |
| Price changes | Available | Real-time | API |
| Liquidations | Available | Real-time | WebSocket (not started) |
| Funding rates | Available | Real-time | API |
| New listings | Implemented | Manual | API |
| Orderbook depth | Not available | N/A | N/A |
| Trade imbalance | Partial | Every 1 hour | Scan |
| Position ratio | Available | Real-time | API |

---

## ALERT CHANNELS AVAILABLE

All detection systems can send to:
- Telegram (main channel)
- Email (SMTP)
- Slack (webhook)
- Custom webhooks
- Database history

Telegram is most integrated.

---

## KEY CODE LOCATIONS

**Spike Detection:**
- Social: `/home/user/cryptosatX/app/services/social_spike_monitor.py:70-182`
- Whale: `/home/user/cryptosatX/app/services/smart_money_service.py:97-260`
- Hype: `/home/user/cryptosatX/app/services/hype_tracker.py:115-150`
- Volume: `/home/user/cryptosatX/app/services/mss_service.py:200-300`

**Alert Delivery:**
- Telegram: `/home/user/cryptosatX/app/services/telegram_notifier.py:31-335`
- Framework: `/home/user/cryptosatX/app/services/alert_service.py:179-412`

**Real-Time:**
- WebSocket: `/home/user/cryptosatX/app/services/coinglass_websocket_service.py:93-146`
- Liquidations: `/home/user/cryptosatX/app/services/coinglass_comprehensive_service.py:2235-2770`

**Background Jobs:**
- Auto Scanner: `/home/user/cryptosatX/app/services/auto_scanner.py:81-133`
- Performance Tracker: `/home/user/cryptosatX/app/services/performance_tracker.py:67-172`

**App Integration:**
- Startup: `/home/user/cryptosatX/app/main.py:68-107`

---

## RECOMMENDED NEXT STEPS

### Immediate (Enable existing systems)
1. Start Social Spike Monitor in lifespan
2. Enable WebSocket liquidation listener
3. Integrate hype tracker into monitoring

### Short-term (Connect real-time data)
1. Create liquidation spike detector
2. Create funding rate change monitor
3. Create price velocity detector

### Medium-term (Add correlation)
1. Multi-indicator confirmation
2. False positive filtering
3. Risk-weighted alerting

---

## TESTING DETECTION SYSTEMS

### Test Social Spike Monitor
```bash
curl http://localhost:8000/social-spike-monitor/status
```

### Test Whale Detection
```bash
curl http://localhost:8000/smart-money/analyze/BTC
```

### Test Liquidations
```bash
curl http://localhost:8000/coinglass/liquidations/history/Binance/BTCUSDT
```

### Test Hype Tracking
```bash
curl http://localhost:8000/lunarcrush/coin/BTC
```


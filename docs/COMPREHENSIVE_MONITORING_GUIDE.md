# 🎯 Comprehensive Coin Monitoring System - Complete Guide

## 📋 Daftar Isi
1. [Overview](#overview)
2. [Features](#features)
3. [Setup](#setup)
4. [Cara Pakai dari GPT](#cara-pakai-dari-gpt)
5. [API Endpoints](#api-endpoints)
6. [Examples](#examples)
7. [Alert Types](#alert-types)
8. [Monitoring Rules](#monitoring-rules)

---

## 🎯 Overview

Sistem monitoring komprehensif untuk crypto yang bisa:
- **Pantau unlimited coins** secara bersamaan
- **Multi-timeframe** (5m, 15m, 1H, 4H)
- **Multi-metric** (price, volume, funding, OI, liquidations)
- **Smart detection** entry/exit opportunities
- **Telegram alerts** dengan analisa lengkap
- **Auto-stop** setelah target tercapai

---

## ✨ Features

### 1. Multi-Coin Monitoring
Pantau sebanyak-banyaknya coin sekaligus. Contoh:
- Hasil scan dapat 4 coin (FIL, ARB, OP, IMX) → tambah semua ke watchlist
- Sistem akan monitor semua coin secara parallel

### 2. Multi-Timeframe Tracking
Setiap coin dipantau di berbagai timeframe:
- **5m**: Scalping & quick moves
- **15m**: Short-term momentum
- **1H**: Primary signals
- **4H**: Trend confirmation

### 3. Multi-Metric Analysis
Untuk setiap coin, sistem track:
- 📊 **Price action** - Breakout, breakdown, support/resistance
- 📈 **Volume** - Spike detection, anomaly
- 💰 **Funding rate** - Long/short sentiment, squeeze risk
- 📊 **Open Interest** - Whale accumulation/distribution
- ⚡ **Liquidations** - Cascade events
- 🐦 **Social volume** (optional) - Viral moments

### 4. Smart Alert Conditions

#### A. Auto-Detection (tanpa atur rule)
Sistem otomatis detect:
- **Volume Spike** (>200% increase)
- **Price Breakout** (>3% move)
- **Extreme Funding** (>0.1%)
- **OI Surge** (>15% increase)

#### B. Custom Rules
Buat rule sendiri untuk kondisi spesifik:
```json
{
  "rule_type": "price_threshold",
  "condition": {
    "price": 1.980,
    "operator": "above"
  },
  "timeframe": "1h",
  "cooldown_minutes": 60
}
```

### 5. Intelligent Telegram Alerts
Alert format comprehensive:
```
🟢 FIL/USDT - LONG ENTRY SETUP DETECTED

📊 FILUSDT
💵 $1.985
📈 +2.5% (1h)

Volume spike detected +240% in last hour

📊 Volume: $128,000,000
   Change: +240.0%
💰 Funding: 0.0500%
📈 OI: $45,000,000
   Change: +8.0%

🔍 Analysis:
   volume_change: 240.00
   Strong momentum detected

💡 Recommendations:
   Monitor for breakout

⏰ 2025-11-19 12:30:45
```

---

## 🚀 Setup

### 1. Run Database Migration
```bash
alembic upgrade head
```

Creates tables:
- `coin_watchlist` - Daftar coin yang dipantau
- `monitoring_rules` - Custom alert rules
- `monitoring_alerts` - Alert history
- `monitoring_metrics` - Historical metrics

### 2. Start Monitoring Service
```bash
POST /comprehensive-monitoring/start
```

### 3. Stop Monitoring
```bash
POST /comprehensive-monitoring/stop
```

---

## 💬 Cara Pakai dari GPT

### Scenario 1: Scan & Monitor Multiple Coins

**User di GPT:**
```
Tolong scan top movers dan pantau 4 coin teratas
```

**Response GPT:**
```
Scan selesai! Top 4 coins:
1. FILUSDT (+15.2%)
2. ARBUSDT (+12.8%)
3. OPUSDT (+9.5%)
4. IMXUSDT (+8.3%)

Menambahkan ke monitoring...
```

**Call API:**
```bash
POST /comprehensive-monitoring/watchlist/bulk-add
{
  "symbols": ["FILUSDT", "ARBUSDT", "OPUSDT", "IMXUSDT"],
  "priority": 2,
  "check_interval_seconds": 300,
  "timeframes": ["5m", "15m", "1h", "4h"],
  "metrics_enabled": {
    "price": true,
    "volume": true,
    "funding": true,
    "open_interest": true,
    "liquidations": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Added 4 coins to watchlist",
  "data": {
    "added": ["FILUSDT", "ARBUSDT", "OPUSDT", "IMXUSDT"],
    "failed": [],
    "total_added": 4
  }
}
```

**Start monitoring:**
```bash
POST /comprehensive-monitoring/start
```

✅ **Sistem sekarang auto-monitor 4 coin!**

### Scenario 2: Set Custom Alert Rule

**User di GPT:**
```
Set alert untuk FIL kalau tembus $1.980, kasih tau untuk LONG entry
```

**Call API:**
```bash
POST /comprehensive-monitoring/rules/add
{
  "symbol": "FILUSDT",
  "rule_type": "price_threshold",
  "rule_name": "FIL Breakout $1.980 - LONG Entry",
  "condition": {
    "price": 1.980,
    "operator": "above"
  },
  "timeframe": "1h",
  "priority": 2,
  "cooldown_minutes": 60
}
```

**Nanti kalau FIL tembus $1.980:**
Telegram alert otomatis dikirim dengan full analysis!

### Scenario 3: Monitor Until Target Reached

**User di GPT:**
```
Pantau FIL sampai break $1.980 atau drop ke $1.920, lalu stop monitoring
```

**Setup:**
1. Add FIL to watchlist
2. Add 2 rules:
   - Rule 1: Break $1.980 (bullish)
   - Rule 2: Drop $1.920 (bearish)
3. Set rule to disable coin after trigger

**Alternative: Manual Stop**
Setelah dapat alert → stop monitoring:
```bash
DELETE /comprehensive-monitoring/watchlist/FILUSDT
```

---

## 📡 API Endpoints

### Watchlist Management

#### Add Single Coin
```http
POST /comprehensive-monitoring/watchlist/add
Content-Type: application/json

{
  "symbol": "FILUSDT",
  "priority": 2,
  "check_interval_seconds": 300,
  "timeframes": ["5m", "1h", "4h"],
  "metrics_enabled": {
    "price": true,
    "volume": true,
    "funding": true,
    "open_interest": true,
    "liquidations": true
  }
}
```

#### Add Multiple Coins (Bulk)
```http
POST /comprehensive-monitoring/watchlist/bulk-add
Content-Type: application/json

{
  "symbols": ["FILUSDT", "ARBUSDT", "OPUSDT", "IMXUSDT"],
  "priority": 2,
  "check_interval_seconds": 300,
  "timeframes": ["5m", "15m", "1h", "4h"]
}
```

#### Get Watchlist
```http
GET /comprehensive-monitoring/watchlist?status=active&limit=100
```

#### Get Coin Details
```http
GET /comprehensive-monitoring/watchlist/FILUSDT
```

#### Remove Coin
```http
DELETE /comprehensive-monitoring/watchlist/FILUSDT
```

### Rules Management

#### Add Rule
```http
POST /comprehensive-monitoring/rules/add
Content-Type: application/json

{
  "symbol": "FILUSDT",
  "rule_type": "price_threshold",
  "rule_name": "FIL Long Entry",
  "condition": {
    "price": 1.980,
    "operator": "above"
  },
  "timeframe": "1h",
  "cooldown_minutes": 60
}
```

**Rule Types:**
- `price_threshold` - Price above/below target
- `volume_threshold` - Volume spike % threshold
- `funding_threshold` - Funding rate extreme
- `oi_change` - Open interest change %

#### Delete Rule
```http
DELETE /comprehensive-monitoring/rules/{rule_id}
```

### Alerts & History

#### Get Alerts
```http
GET /comprehensive-monitoring/alerts?symbol=FILUSDT&hours=24&limit=50
```

#### Get Alert Details
```http
GET /comprehensive-monitoring/alerts/{alert_id}
```

### Service Control

#### Start Monitoring
```http
POST /comprehensive-monitoring/start
```

#### Stop Monitoring
```http
POST /comprehensive-monitoring/stop
```

#### Get Status
```http
GET /comprehensive-monitoring/status
```

#### Get Statistics
```http
GET /comprehensive-monitoring/stats
```

#### Health Check
```http
GET /comprehensive-monitoring/health
```

---

## 📊 Examples

### Example 1: Volume Spike Alert
```json
{
  "symbol": "FILUSDT",
  "rule_type": "volume_threshold",
  "rule_name": "FIL Volume Spike",
  "condition": {
    "threshold_pct": 200
  },
  "timeframe": "1h",
  "priority": 2
}
```

Alert ketika volume naik >200% dalam 1 jam.

### Example 2: Funding Rate Alert
```json
{
  "symbol": "ARBUSDT",
  "rule_type": "funding_threshold",
  "rule_name": "ARB Funding Extreme",
  "condition": {
    "threshold": 0.15
  },
  "timeframe": "1h",
  "priority": 1
}
```

Alert ketika funding rate >0.15% (risk short squeeze).

### Example 3: OI Surge Alert
```json
{
  "symbol": "OPUSDT",
  "rule_type": "oi_change",
  "rule_name": "OP Whale Activity",
  "condition": {
    "threshold_pct": 15
  },
  "timeframe": "1h",
  "priority": 2
}
```

Alert ketika OI naik >15% (whale accumulation).

### Example 4: Breakout Entry Setup
```json
{
  "symbol": "FILUSDT",
  "rule_type": "price_threshold",
  "rule_name": "FIL Bullish Breakout",
  "condition": {
    "price": 1.980,
    "operator": "above"
  },
  "timeframe": "1h",
  "priority": 3,
  "cooldown_minutes": 120
}
```

Alert ketika FIL break resistance $1.980.

### Example 5: Breakdown Short Setup
```json
{
  "symbol": "FILUSDT",
  "rule_type": "price_threshold",
  "rule_name": "FIL Bearish Breakdown",
  "condition": {
    "price": 1.950,
    "operator": "below"
  },
  "timeframe": "1h",
  "priority": 3,
  "cooldown_minutes": 120
}
```

Alert ketika FIL break support $1.950.

---

## 🚨 Alert Types

### 1. `price_breakout`
- Harga break resistance
- Bullish momentum
- Entry signal untuk LONG

### 2. `price_breakdown`
- Harga break support
- Bearish momentum
- Entry signal untuk SHORT

### 3. `volume_spike`
- Volume naik signifikan
- Momentum confirmation
- Watch for breakout/breakdown

### 4. `funding_extreme`
- Funding rate ekstrem (>0.1% atau <-0.1%)
- Risk short/long squeeze
- Contrarian signal

### 5. `oi_surge`
- Open Interest naik >15%
- Whale activity
- Position building

### 6. `liquidation_cascade`
- Large liquidations detected
- Market volatility
- Reversal potential

### 7. `confluence`
- Multiple signals align
- High probability setup
- Strong entry/exit signal

### 8. `entry_setup`
- Entry opportunity detected
- Multiple confirmations
- Clear entry zone

### 9. `exit_signal`
- Exit opportunity detected
- Take profit signal
- Risk management

---

## 🎛️ Monitoring Configuration

### Priority Levels (1-10)
- **10**: Highest priority (check most frequently)
- **5**: Medium priority
- **1**: Lowest priority (check less frequently)

### Check Intervals
- **60s**: Ultra-fast (scalping)
- **300s** (5min): Fast (default)
- **900s** (15min): Medium
- **3600s** (1H): Slow

### Timeframes
- **5m**: Scalping, quick moves
- **15m**: Short-term
- **1h**: Primary signals (recommended)
- **4h**: Trend confirmation

### Metrics Enabled
```json
{
  "price": true,           // Always enabled
  "volume": true,          // Volume tracking
  "funding": true,         // Funding rate
  "open_interest": true,   // OI tracking
  "liquidations": true,    // Liquidation events
  "social": false          // Social volume (optional, slower)
}
```

### Cooldown Minutes
- **15**: Very aggressive (spam alerts)
- **60**: Default (1 hour cooldown)
- **120**: Conservative (2 hour cooldown)
- **1440**: Very conservative (24 hour)

---

## 🎓 Best Practices

### 1. Start Small
```
Begin with 2-3 coins, test the alerts, then scale up
```

### 2. Use Smart Defaults
```
Priority: 2
Check interval: 300s (5 min)
Timeframes: ["1h", "4h"]
Cooldown: 60 minutes
```

### 3. Combine Rules
```
For each coin, set:
- 1 breakout rule (upside)
- 1 breakdown rule (downside)
- 1 volume spike rule
- Let smart detection handle the rest
```

### 4. Monitor High-Conviction Coins
```
Only add coins from:
- Your scan results (top signals)
- High volume movers
- Coins with clear support/resistance
```

### 5. Review Alerts Regularly
```
GET /comprehensive-monitoring/alerts?hours=24

Check which alerts were profitable
Adjust rules based on performance
```

---

## 🔧 Troubleshooting

### Monitoring Not Starting
```bash
# Check status
GET /comprehensive-monitoring/health

# Check database connection
GET /comprehensive-monitoring/status

# Check Telegram config
# Ensure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set
```

### No Alerts Received
```bash
# Check alert cooldowns
GET /comprehensive-monitoring/watchlist/FILUSDT

# Check if rules are enabled
GET /comprehensive-monitoring/watchlist/FILUSDT

# Check Telegram connection
POST /monitoring/test-alert/FILUSDT
```

### Too Many Alerts
```
Solutions:
1. Increase cooldown_minutes (from 60 to 120+)
2. Increase priority threshold
3. Reduce check_interval_seconds (from 300 to 900+)
4. Use fewer timeframes (only 1h and 4h)
```

### API Errors
```
Common issues:
- Coin not in watchlist → Add it first
- Invalid rule condition → Check JSON format
- Database connection → Restart service
```

---

## 📈 Workflow Examples

### Workflow 1: Daily Scanner → Monitor
```
1. Run scan di GPT (get top movers)
2. Add top 5 coins to watchlist (bulk-add)
3. Set breakout/breakdown rules for each
4. Start monitoring
5. Receive alerts via Telegram
6. Execute trades based on alerts
7. End of day: Remove coins, analyze performance
```

### Workflow 2: Specific Coin Setup
```
1. Identify coin (FIL/USDT)
2. Analyze key levels:
   - Resistance: $1.980
   - Support: $1.950
3. Add to watchlist
4. Add 2 rules:
   - Breakout $1.980 → LONG
   - Breakdown $1.950 → SHORT
5. Monitor until triggered
6. Remove after entry executed
```

### Workflow 3: Portfolio Monitoring
```
1. Add all portfolio coins to watchlist
2. Set exit rules (take profit, stop loss)
3. Monitor 24/7
4. Get alerted when exit conditions met
5. Update rules as positions change
```

---

## 🎉 Summary

**Sistem ini BISA:**
✅ Monitor unlimited coins
✅ Track multi-timeframe & multi-metric
✅ Smart auto-detection
✅ Custom alert rules
✅ Telegram notifications
✅ Auto-stop when done
✅ Scalable & efficient

**Yang TIDAK bisa:**
❌ Execute trades automatically (manual execution)
❌ Predict market (analysis only)
❌ Guarantee profits (tool for alerts)

**Perfect untuk:**
- Monitoring scan results
- Setting entry/exit alerts
- Portfolio management
- Whale activity tracking
- Multi-coin strategies

---

## 📞 Support

Questions? Issues?
1. Check `/comprehensive-monitoring/health`
2. Review `/comprehensive-monitoring/stats`
3. Check logs for errors
4. Verify Telegram config

**API Documentation:**
```
http://localhost:8000/docs#/comprehensive-monitoring
```

---

**Happy Monitoring! 🚀📊**

# Panduan URL RPC - CryptoSatX

**Base URL**: `https://guardiansofthetoken.org`
**Tanggal**: 2025-11-20

---

## 🌐 URL RPC UTAMA

### **1. Unified RPC Endpoint** (RECOMMENDED)
```
POST https://guardiansofthetoken.org/invoke
```

**Fungsi**: Single endpoint untuk 192+ operasi crypto data

**Format Request (Flat Parameters - GPT Actions Compatible):**
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "signals.get",
    "symbol": "BTC"
  }'
```

**Format Request (Nested Args - Legacy):**
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "signals.get",
    "args": {
      "symbol": "BTC"
    }
  }'
```

**Response Format:**
```json
{
  "ok": true,
  "operation": "signals.get",
  "data": {
    "signal": "LONG",
    "confidence": 85.5,
    "price": 101044.10,
    "indicators": {...}
  },
  "meta": {
    "execution_time_ms": 245.67,
    "namespace": "signals",
    "timestamp": "2025-11-20T15:30:00Z"
  }
}
```

---

### **2. List Available Operations**
```
GET https://guardiansofthetoken.org/invoke/operations
```

**Fungsi**: Mendapatkan daftar semua operasi RPC yang tersedia

**Example:**
```bash
curl https://guardiansofthetoken.org/invoke/operations
```

**Response:**
```json
{
  "total_operations": 192,
  "namespaces": [
    "signals",
    "coinglass",
    "lunarcrush",
    "coinapi",
    "smart_money",
    "mss",
    "market",
    "health"
  ],
  "operations_by_namespace": {
    "signals": ["signals.get"],
    "coinglass": [
      "coinglass.markets",
      "coinglass.liquidations.symbol",
      "coinglass.funding_rate.history",
      ...
    ],
    "lunarcrush": [
      "lunarcrush.coin",
      "lunarcrush.coins_discovery",
      ...
    ]
  }
}
```

---

### **3. GPT Actions Schema**
```
GET https://guardiansofthetoken.org/invoke/schema
```

**Fungsi**: OpenAPI 3.1 schema untuk integrasi GPT Actions

**Example:**
```bash
curl https://guardiansofthetoken.org/invoke/schema
```

**Response**: OpenAPI schema (JSON) untuk import ke ChatGPT/Claude

**Cara Pakai di ChatGPT:**
1. Buka ChatGPT → Create GPT
2. Configure → Actions → Import from URL
3. Paste: `https://guardiansofthetoken.org/invoke/schema`
4. Done! GPT bisa akses 192+ operasi

---

## 📊 OPERASI RPC YANG TERSEDIA

### **Core Signals & Market**

#### Get Trading Signal
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "signals.get",
  "symbol": "BTC"
}
```

#### Get Market Data
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "market.get",
  "symbol": "BTC"
}
```

#### Health Check
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "health.check"
}
```

---

### **Coinglass Data (64 operations)**

#### Get All Markets
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.markets"
}
```

#### Get Liquidations
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.liquidations.symbol",
  "symbol": "BTC",
  "time_type": "h24"
}
```

#### Funding Rate History
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.funding_rate.history",
  "exchange": "Binance",
  "symbol": "BTCUSDT",
  "interval": "1d"
}
```

#### Open Interest History
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.open_interest.history",
  "exchange": "Binance",
  "symbol": "BTCUSDT",
  "interval": "1d"
}
```

#### Fear & Greed Index
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.indicators.fear_greed"
}
```

#### RSI List (536 coins)
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.indicators.rsi_list"
}
```

#### Whale Transfers
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.chain.whale_transfers"
}
```

#### Whale Walls (Order Book)
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.orderbook.whale_walls",
  "exchange": "Binance",
  "symbol": "BTCUSDT"
}
```

#### Supported Coins
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.supported_coins"
}
```

---

### **LunarCrush Social Data (17 operations)**

#### Get Coin Social Metrics
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "lunarcrush.coin",
  "symbol": "BTC"
}
```

#### Discover Trending Coins
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "lunarcrush.coins_discovery",
  "limit": 10
}
```

#### Get Coin Momentum
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "lunarcrush.coin_momentum",
  "symbol": "BTC"
}
```

#### Trending Topics
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "lunarcrush.topics_list"
}
```

#### Coin Correlation
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "lunarcrush.coin_correlation",
  "symbol": "BTC"
}
```

---

### **CoinAPI Market Data (7 operations)**

#### Current Quote
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinapi.quote",
  "symbol": "BTC"
}
```

#### Latest OHLCV
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinapi.ohlcv.latest",
  "symbol": "BTC",
  "period": "1HRS"
}
```

#### Recent Trades
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinapi.trades",
  "symbol": "BTC"
}
```

#### Order Book
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinapi.orderbook",
  "symbol": "BTC"
}
```

---

### **Smart Money Scanner**

#### Scan Whale Accumulation/Distribution
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "smart_money.scan",
  "min_accumulation_score": 7,
  "min_distribution_score": 7
}
```

#### Scan Accumulation Only
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "smart_money.scan_accumulation",
  "min_score": 7
}
```

#### Analyze Smart Money for Symbol
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "smart_money.analyze",
  "symbol": "BTC"
}
```

---

### **MSS (Multi-Modal Signal Score)**

#### Discover High-Potential Coins
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "mss.discover",
  "min_mss_score": 75,
  "max_results": 10
}
```

#### Analyze MSS for Symbol
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "mss.analyze",
  "symbol": "BTC"
}
```

#### Scan Market with MSS
```bash
POST https://guardiansofthetoken.org/invoke
{
  "operation": "mss.scan"
}
```

---

## 🔐 AUTHENTICATION (Optional)

### Tanpa API Key (Public Mode)
```bash
# Jika API_KEYS kosong di .env, semua endpoint public
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "signals.get", "symbol": "BTC"}'
```

### Dengan API Key (Protected Mode)
```bash
# Jika API_KEYS di-set di .env, tambahkan header X-API-Key
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"operation": "signals.get", "symbol": "BTC"}'
```

---

## 📝 PARAMETER UMUM

### Common Parameters untuk Semua Operasi:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `operation` | string | **REQUIRED** - Nama operasi RPC | `"signals.get"` |
| `symbol` | string | Cryptocurrency symbol | `"BTC"`, `"ETH"` |
| `interval` | string | Time interval | `"1m"`, `"5m"`, `"1h"`, `"1d"` |
| `timeframe` | string | Timeframe (uppercase) | `"1MIN"`, `"1HRS"`, `"1DAY"` |
| `exchange` | string | Exchange name | `"Binance"`, `"OKX"` |
| `limit` | integer | Result limit | `10`, `50`, `100` |
| `debug` | boolean | Enable debug mode | `true`, `false` |
| `time_type` | string | Time type for Coinglass | `"h1"`, `"h4"`, `"h24"` |

---

## 🌐 ALTERNATIVE ENDPOINTS (Direct)

Selain unified RPC `/invoke`, ada juga endpoint direct:

### Health
```
GET https://guardiansofthetoken.org/health
```

### Signals
```
GET https://guardiansofthetoken.org/signals/{symbol}
GET https://guardiansofthetoken.org/signals/BTC
```

### GPT Actions (User-Friendly)
```
POST https://guardiansofthetoken.org/gpt/signal
{
  "symbol": "BTC"
}
```

### Coinglass Direct
```
GET https://guardiansofthetoken.org/coinglass/markets
GET https://guardiansofthetoken.org/coinglass/liquidations/{symbol}
```

### LunarCrush Direct
```
GET https://guardiansofthetoken.org/lunarcrush/coin/{symbol}
```

**CATATAN**: Direct endpoints mungkin terblokir. **Gunakan `/invoke` untuk best compatibility**.

---

## 🚀 CONTOH PENGGUNAAN

### Example 1: Get BTC Signal
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "signals.get",
    "symbol": "BTC"
  }'
```

**Response:**
```json
{
  "ok": true,
  "operation": "signals.get",
  "data": {
    "signal": "LONG",
    "confidence": 85.5,
    "entry_price": 101044.10,
    "stop_loss": 99500.00,
    "take_profit_1": 102500.00,
    "indicators": {
      "rsi": 55.2,
      "macd": "bullish",
      "volume": "high"
    }
  },
  "meta": {
    "execution_time_ms": 245.67,
    "namespace": "signals"
  }
}
```

---

### Example 2: Get Fear & Greed Index
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "coinglass.indicators.fear_greed"
  }'
```

**Response:**
```json
{
  "ok": true,
  "operation": "coinglass.indicators.fear_greed",
  "data": {
    "currentIndex": 14,
    "sentiment": "EXTREME_FEAR",
    "history": [
      {"index": 30},
      {"index": 25},
      {"index": 14}
    ]
  },
  "meta": {
    "execution_time_ms": 180.45,
    "namespace": "coinglass"
  }
}
```

---

### Example 3: Scan Smart Money
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "smart_money.scan",
    "min_accumulation_score": 7,
    "min_distribution_score": 7
  }'
```

**Response:**
```json
{
  "ok": true,
  "operation": "smart_money.scan",
  "data": {
    "accumulation": [
      {
        "symbol": "BTC",
        "score": 8.5,
        "confidence": "high"
      },
      {
        "symbol": "ETH",
        "score": 7.8,
        "confidence": "medium"
      }
    ],
    "distribution": [
      {
        "symbol": "SOL",
        "score": 8.2,
        "confidence": "high"
      }
    ]
  },
  "meta": {
    "execution_time_ms": 1250.30,
    "namespace": "smart_money"
  }
}
```

---

### Example 4: Discover High MSS Coins
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "mss.discover",
    "min_mss_score": 75,
    "max_results": 5
  }'
```

**Response:**
```json
{
  "ok": true,
  "operation": "mss.discover",
  "data": {
    "coins": [
      {
        "symbol": "BTC",
        "mss_score": 92.5,
        "signals": ["smart_money", "social", "technical"]
      },
      {
        "symbol": "ETH",
        "mss_score": 88.3,
        "signals": ["social", "technical"]
      }
    ],
    "total_found": 5
  },
  "meta": {
    "execution_time_ms": 890.12,
    "namespace": "mss"
  }
}
```

---

## 🔧 ERROR HANDLING

### Success Response:
```json
{
  "ok": true,
  "operation": "signals.get",
  "data": {...}
}
```

### Error Response:
```json
{
  "ok": false,
  "operation": "signals.get",
  "error": "Missing required argument: symbol",
  "meta": {
    "execution_time_ms": 5.23,
    "namespace": "signals"
  }
}
```

### HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (missing parameters)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (firewall/proxy blocking)
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

---

## 📊 RESPONSE HEADERS

Setiap response include headers:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Window: 60
X-GPT-Actions-Compatible: true
```

---

## 🎯 TESTING URLs

### Quick Test:
```bash
# Test 1: Health check
curl https://guardiansofthetoken.org/health

# Test 2: RPC health via invoke
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "health.check"}'

# Test 3: List operations
curl https://guardiansofthetoken.org/invoke/operations

# Test 4: Get BTC signal
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "signals.get", "symbol": "BTC"}'
```

---

## 📝 NOTES

### Current Status:
⚠️ **Semua endpoint mengembalikan HTTP 403 "Access denied"**
- Root cause: Proxy/firewall blocking (Replit/Cloudflare)
- Perlu fix di deployment settings
- Setelah fix, semua URL akan accessible

### After Fix:
✅ All URLs will be accessible
✅ 192+ operations via `/invoke`
✅ Rate limit: 30-100 req/min
✅ GPT Actions compatible

---

## ✅ SUMMARY

**Main RPC URL**: `https://guardiansofthetoken.org/invoke`

**Available Operations**: 192+
- 64 Coinglass
- 17 LunarCrush
- 7 CoinAPI
- Smart Money
- MSS
- Signals

**Format**: JSON POST dengan flat parameters
**Auth**: Optional (X-API-Key header)
**Rate Limit**: 30-100 requests/min

---

**Generated by**: Claude AI
**Date**: 2025-11-20
**Branch**: claude/check-rpc-accessibility-01FLrLP7a1TRQwpYv4UyKCDA

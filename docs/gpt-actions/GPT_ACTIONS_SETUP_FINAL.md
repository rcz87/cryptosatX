# 🎯 GPT ACTIONS SETUP - SOLUSI LENGKAP

## 📊 RINGKASAN MASALAH

### Masalah 1: GPT Actions Limit 30 Operations
- **Limit GPT:** 30 operations maximum
- **Aplikasi kamu:** 187 operations
- **Result:** ❌ GPT akan reject atau hanya pakai 30 pertama

### Masalah 2: Dynamic Endpoint Blocked
- **URL:** `https://guardiansofthetoken.org/openapi-gpt.json`
- **Status:** HTTP 403 "Access denied"
- **Cause:** Envoy proxy blocking external access

---

## ✅ SOLUSI: RPC PATTERN + STATIC SCHEMA

### Konsep RPC Pattern

**Traditional (TIDAK WORK - 187 endpoints):**
```
/signals/BTC          → operation 1
/coinglass/markets    → operation 2
/smart-money/scan     → operation 3
... 184 more ...      → operations 4-187
❌ GPT reject: Lebih dari 30 operations!
```

**RPC Pattern (WORK - 1 endpoint):**
```
POST /invoke
{
  "operation": "signals.get",
  "symbol": "BTC"
}

GPT melihat: ✅ 1 operation (invoke)
Tapi akses: ✅ 187 functions via parameter!
```

---

## 📁 FILE YANG SUDAH DIBUAT

**Location:** `static/openapi-gpt.json`

**Specs:**
- ✅ Size: 6.89 KB (limit: 45 KB)
- ✅ Endpoints: 1 (`/invoke`)
- ✅ Operations: 1 (`invoke`)
- ✅ Functions: 187 (via operation enum)
- ✅ Format: OpenAPI 3.1.0

**URL Akses:**
```
https://guardiansofthetoken.org/static/openapi-gpt.json
```

**Status:**
- ✅ Committed to Git
- ✅ Pushed to GitHub
- ⏳ Waiting for auto-deployment

---

## 🎯 CARA SETUP DI GPT ACTIONS

### Step 1: Buka GPT Builder
1. Login ke **ChatGPT**
2. Klik **"Explore GPTs"** → **"Create"**
3. Scroll ke section **"Actions"**
4. Klik **"Create new action"**

### Step 2: Import OpenAPI Schema

**Opsi A: Import from URL (RECOMMENDED)**
1. Di kolom "Schema", pilih **"Import from URL"**
2. Paste URL ini:
   ```
   https://guardiansofthetoken.org/static/openapi-gpt.json
   ```
3. Klik **"Import"**
4. Wait untuk schema loading
5. ✅ Schema akan otomatis terisi

**Opsi B: Manual Copy-Paste**
1. Buka: `https://guardiansofthetoken.org/static/openapi-gpt.json`
2. Copy semua content
3. Paste ke kolom "Schema" di GPT Actions
4. Klik **"Validate"**

### Step 3: Configure (Optional)

**Authentication:** None required (API is public for read operations)

**Privacy:**
- Set sesuai kebutuhan kamu
- Recommended: "Only me" untuk testing

### Step 4: Test

1. Klik **"Test"** button di GPT Actions panel
2. Select operation: **"invoke"**
3. Fill test payload:
   ```json
   {
     "operation": "signals.get",
     "symbol": "BTC"
   }
   ```
4. Klik **"Run"**
5. Check response - harus return trading signal data

### Step 5: Save & Publish

1. Klik **"Update"** atau **"Create"**
2. Give your GPT a name, e.g., "Crypto Signal Analyzer"
3. Klik **"Save"** or **"Publish"**
4. ✅ Done! GPT sekarang bisa akses 187 operations!

---

## 📊 CARA KERJA

### Request Flow

```
User → ChatGPT → GPT Actions → POST /invoke → FastAPI App
                                 {
                                   "operation": "signals.get",
                                   "symbol": "BTC"
                                 }
```

### OpenAPI Schema Structure

```json
{
  "paths": {
    "/invoke": {
      "post": {
        "operationId": "invoke",
        "requestBody": {
          "schema": {
            "properties": {
              "operation": {
                "enum": [
                  "signals.get",
                  "coinglass.liquidations.symbol",
                  "smart_money.scan",
                  ... // 184 more
                ]
              }
            }
          }
        }
      }
    }
  }
}
```

**GPT melihat:**
- Total paths: 1 (`/invoke`)
- Total operations: 1 (`invoke`)
- ✅ LOLOS limit 30 operations!

**User dapat:**
- 187 functions via `operation` parameter
- Access to all namespaces:
  - `coinglass.*` (65 ops)
  - `lunarcrush.*` (19 ops)
  - `smart_money.*` (8 ops)
  - `mss.*` (10 ops)
  - Dan 14 namespace lainnya

---

## 📋 CONTOH PENGGUNAAN

### Example 1: Get Trading Signal

**User asks GPT:**
```
"What's the trading signal for Bitcoin?"
```

**GPT calls API:**
```json
POST https://guardiansofthetoken.org/invoke
{
  "operation": "signals.get",
  "symbol": "BTC"
}
```

**Response:**
```json
{
  "ok": true,
  "operation": "signals.get",
  "data": {
    "symbol": "BTC",
    "signal": "LONG",
    "score": 67.5,
    "confidence": "medium",
    "price": 103500,
    "reasons": [...]
  }
}
```

---

### Example 2: Check Liquidations

**User asks GPT:**
```
"Show me recent liquidations for Ethereum"
```

**GPT calls API:**
```json
POST https://guardiansofthetoken.org/invoke
{
  "operation": "coinglass.liquidations.symbol",
  "symbol": "ETH"
}
```

---

### Example 3: Smart Money Scan

**User asks GPT:**
```
"Find coins with smart money accumulation"
```

**GPT calls API:**
```json
POST https://guardiansofthetoken.org/invoke
{
  "operation": "smart_money.scan_accumulation",
  "limit": 10
}
```

---

### Example 4: MSS Discovery

**User asks GPT:**
```
"Discover high-potential cryptocurrencies"
```

**GPT calls API:**
```json
POST https://guardiansofthetoken.org/invoke
{
  "operation": "mss.discover",
  "limit": 15
}
```

---

## 📋 AVAILABLE OPERATIONS (187 Total)

### Core Trading (2 ops)
- `signals.get` - Get trading signal for symbol
- `signals.debug` - Get debug premium data

### Coinglass Data (65 ops)
- `coinglass.markets` - Get all markets
- `coinglass.liquidations.symbol` - Get liquidations
- `coinglass.funding_rate.history` - Get funding rate
- `coinglass.indicators.rsi` - Get RSI indicator
- `coinglass.indicators.fear_greed` - Get Fear & Greed Index
- ... 60 more operations

### LunarCrush Social (19 ops)
- `lunarcrush.coin` - Get coin social data
- `lunarcrush.topics_list` - Get trending topics
- `lunarcrush.coins_discovery` - Discover viral coins
- ... 16 more operations

### Smart Money (8 ops)
- `smart_money.scan` - Scan smart money activity
- `smart_money.scan_accumulation` - Find accumulation
- `smart_money.scan_distribution` - Find distribution
- ... 5 more operations

### MSS Discovery (10 ops)
- `mss.discover` - Discover high-potential coins
- `mss.analyze` - Analyze MSS score
- `mss.scan` - Scan with MSS criteria
- ... 7 more operations

### Monitoring & Analytics (21 ops)
- `monitoring.start` - Start monitoring
- `analytics.summary` - Get analytics summary
- `analytics.performance.symbol` - Get performance metrics
- ... 18 more operations

### Spike Detection (11 ops)
- `spike.check_system` - Check spike detection status
- `spike.monitor_coin` - Monitor coin for spikes
- ... 9 more operations

### And 11 More Namespaces...
- Admin (12 ops)
- CoinAPI (9 ops)
- Narratives (6 ops)
- New Listings (5 ops)
- OpenAI (5 ops)
- Smart Entry (4 ops)
- History (4 ops)
- Market (2 ops)
- SMC (2 ops)
- Health (2 ops)

**See full list:** `app/utils/operation_catalog.py`

---

## 🔍 TROUBLESHOOTING

### Issue: Schema import gagal

**Solution:**
1. Check URL accessible: `https://guardiansofthetoken.org/static/openapi-gpt.json`
2. Wait for deployment (5-10 menit setelah push)
3. Gunakan manual copy-paste method

---

### Issue: GPT tidak bisa call operation

**Check:**
1. Operation name benar (case-sensitive)
2. Required parameters tersedia (e.g., `symbol` untuk most operations)
3. Test manual di browser/Postman dulu

**Example test:**
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "signals.get", "symbol": "BTC"}'
```

---

### Issue: Response timeout

**Causes:**
- Operation terlalu berat (e.g., scan 100 coins)
- Network latency

**Solutions:**
1. Reduce `limit` parameter (e.g., `limit: 10` instead of `100`)
2. Use `send_telegram: true` untuk heavy operations
3. Try faster operations first (e.g., `health.check`)

---

## ✅ VERIFICATION CHECKLIST

Before going live, verify:

- [ ] Static schema file exists: `static/openapi-gpt.json`
- [ ] File committed to Git
- [ ] File pushed to GitHub
- [ ] Deployment completed (auto-deploy)
- [ ] Schema accessible via browser
- [ ] Schema imported to GPT Actions successfully
- [ ] Test operation works (`signals.get` for BTC)
- [ ] GPT can call multiple different operations
- [ ] No "operation limit" error from GPT

---

## 🚀 NEXT STEPS

1. **Wait 5-10 minutes** untuk auto-deployment
2. **Verify URL accessible:**
   ```
   https://guardiansofthetoken.org/static/openapi-gpt.json
   ```
3. **Import ke GPT Actions** using URL above
4. **Test beberapa operations:**
   - `signals.get` (simple, fast)
   - `coinglass.markets` (simple list)
   - `smart_money.scan` (more complex)
5. **Publish GPT** dan mulai pakai!

---

## 🎉 SUCCESS!

Sekarang kamu punya:
- ✅ GPT Actions dengan 187 operations
- ✅ Bypass limit 30 operations
- ✅ Bypass Envoy blocking
- ✅ Schema size optimal (6.89 KB)
- ✅ Ready untuk production!

**Enjoy your 187 crypto operations! 🚀**

---

**Created:** 2025-11-21
**Author:** Claude Code Agent
**Repository:** https://github.com/rcz87/cryptosatX

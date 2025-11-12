# GPT Actions Troubleshooting Guide

## ❌ Error: "sistem tidak mengenali argumen symbol"

### 🔍 Penyebab
Error ini terjadi ketika GPT Actions **tidak mengirim parameter `args` dengan benar** atau mengirim `args` kosong.

### ✅ Format yang BENAR
```json
{
  "operation": "signals.get",
  "args": {
    "symbol": "SOL"
  }
}
```

### ❌ Format yang SALAH
```json
// SALAH 1: args kosong
{
  "operation": "signals.get",
  "args": {}
}

// SALAH 2: tanpa args
{
  "operation": "signals.get"
}

// SALAH 3: symbol di level top (bukan di dalam args)
{
  "operation": "signals.get",
  "symbol": "SOL"
}
```

---

## 🎯 Solusi untuk GPT Actions

### Step 1: Verifikasi Schema Import
1. Buka GPT Editor → Actions
2. Pastikan schema URL: `https://guardiansofthetoken.org/invoke/schema`
3. Re-import jika perlu (hapus action lama, import ulang)

### Step 2: Cek Examples di Schema
Schema sudah include 5 contoh dengan format yang benar:

**Example 1: BTC Signal**
```json
{
  "operation": "signals.get",
  "args": {"symbol": "BTC"}
}
```

**Example 2: SOL Signal**
```json
{
  "operation": "signals.get",
  "args": {"symbol": "SOL"}
}
```

**Example 3: ETH Signal**
```json
{
  "operation": "signals.get",
  "args": {"symbol": "ETH"}
}
```

### Step 3: Instruksi untuk GPT
Tambahkan di GPT instructions:
```
When calling the invoke action:
- ALWAYS include "args" as an object
- For signals.get, ALWAYS put symbol inside args object
- Example: {"operation": "signals.get", "args": {"symbol": "BTC"}}
- DO NOT put symbol at the top level
```

### Step 4: Test Manual
Test di GPT dengan prompt yang sangat specific:
```
Call the invoke action with this exact JSON:
{
  "operation": "signals.get",
  "args": {
    "symbol": "SOL"
  }
}
```

---

## 🧪 Test Endpoint Langsung

### Via cURL
```bash
# Test SOL
curl -X POST "https://guardiansofthetoken.org/invoke" \
  -H "Content-Type: application/json" \
  -d '{"operation": "signals.get", "args": {"symbol": "SOL"}}'

# Test BTC
curl -X POST "https://guardiansofthetoken.org/invoke" \
  -H "Content-Type: application/json" \
  -d '{"operation": "signals.get", "args": {"symbol": "BTC"}}'
```

### Expected Response
```json
{
  "ok": true,
  "operation": "signals.get",
  "data": {
    "symbol": "SOL",
    "signal": "LONG",
    "score": 59.5,
    "confidence": "low",
    "price": 156.08,
    "reasons": [...],
    "metrics": {...}
  },
  "meta": {
    "execution_time_ms": 2976.15,
    "namespace": "signals"
  }
}
```

### Error Response (jika args kosong)
```json
{
  "ok": false,
  "operation": "signals.get",
  "error": "Missing required argument 'symbol' for operation 'signals.get'. Example: {\"operation\": \"signals.get\", \"args\": {\"symbol\": \"BTC\"}}"
}
```

---

## 📋 Operasi yang Membutuhkan Symbol

Semua operasi ini **WAJIB** memiliki `symbol` di dalam `args`:

**Trading Signals:**
- `signals.get` - Trading signal
- `signals.debug` - Debug premium data
- `market.get` - Market data

**Analytics:**
- `analytics.history.symbol` - Signal history
- `analytics.performance.symbol` - Performance metrics

**CoinAPI:**
- `coinapi.ohlcv.latest` - OHLCV data
- `coinapi.orderbook` - Orderbook snapshot
- `coinapi.trades` - Recent trades
- `coinapi.quote` - Current quote

**LunarCrush:**
- `lunarcrush.coin` - Social metrics
- `lunarcrush.topic` - Topic data

**Smart Money:**
- `smart_money.analyze` - Analyze smart money for symbol

---

## 🔧 Debug di GPT Actions

### 1. Cek Request yang Dikirim
Di GPT Actions debug panel, lihat exact request yang dikirim:
- Apakah ada field `args`?
- Apakah `args` adalah object `{}`?
- Apakah `symbol` berada di dalam `args`?

### 2. Cek Response Error
Error message sekarang sangat informatif:
```
Missing required argument 'symbol' for operation 'signals.get'. 
Example: {"operation": "signals.get", "args": {"symbol": "BTC"}}
```

### 3. Re-import Schema
Jika masih error, hapus action dan re-import:
1. Delete action di GPT editor
2. Re-import dari `https://guardiansofthetoken.org/invoke/schema`
3. Save dan test ulang

---

## 🎯 Alternative Endpoints

Jika RPC endpoint masih bermasalah, gunakan REST endpoint langsung:

### REST API (Direct)
```
GET https://guardiansofthetoken.org/signals/SOL
GET https://guardiansofthetoken.org/signals/BTC
GET https://guardiansofthetoken.org/signals/ETH
```

### Keuntungan RPC vs REST
- **RPC**: 1 endpoint untuk 155 operasi (bypass 30-op limit)
- **REST**: Direct access, lebih simple tapi terbatas 30 endpoints

---

## ✅ Checklist Troubleshooting

- [ ] Schema URL benar: `https://guardiansofthetoken.org/invoke/schema`
- [ ] Examples terlihat di schema (5 examples)
- [ ] GPT instructions include format yang benar
- [ ] Test manual via cURL berhasil
- [ ] Re-import schema jika perlu
- [ ] Cek debug panel untuk lihat request yang dikirim
- [ ] Pastikan `args` adalah object, bukan null
- [ ] Pastikan `symbol` di dalam `args`, bukan top level

---

## 🆘 Masih Bermasalah?

Jika setelah semua langkah di atas masih error:

1. **Copy exact error message** dari GPT Actions
2. **Screenshot request** yang dikirim GPT (dari debug panel)
3. **Test langsung via cURL** untuk confirm API working
4. **Share error detail** untuk diagnosis lebih lanjut

---

## 📞 Contact & Support

- API Docs: `https://guardiansofthetoken.org/docs`
- Schema: `https://guardiansofthetoken.org/invoke/schema`
- Operations List: `https://guardiansofthetoken.org/invoke/operations`

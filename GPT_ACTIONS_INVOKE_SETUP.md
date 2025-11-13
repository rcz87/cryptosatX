# GPT Actions Setup dengan Unified RPC Endpoint `/invoke`

## Overview

Kamu menggunakan **Unified RPC endpoint** untuk bypass GPT Actions 30-operation limit. Ini **strategi yang benar**! 👍

**Setup kamu:**
- ✅ 155+ operations tersedia
- ✅ Single endpoint `/invoke` (POST)
- ✅ Schema endpoint `/invoke/schema` (GET)
- ✅ OpenAPI 3.1 compliant
- ✅ Proper operation enum dan validation

## Current Problem

**Cloudflare memblokir semua endpoints termasuk `/invoke/schema`:**

```bash
curl https://guardiansofthetoken.org/invoke/schema
→ HTTP 403: Access denied
```

GPT Actions tidak bisa fetch schema karena Cloudflare WAF blocking.

## Solution - Fix Cloudflare (CRITICAL!)

### Step 1: Cloudflare WAF Configuration

**Login ke Cloudflare Dashboard:**

1. Pilih domain: `guardiansofthetoken.org`
2. Go to: **Security** → **WAF** → **Custom rules**
3. Klik **Create rule**

**Rule Configuration:**

```
Rule name: Allow OpenAI GPT Actions
Expression builder:
  Field: User Agent
  Operator: contains
  Value: ChatGPT-User

Action: Skip
  - All remaining custom rules
  - All managed rules
  - All rate limiting rules
```

**Alternative - Advanced Expression:**

```
Rule name: Allow OpenAI and Public API Access
Custom expression:
(http.user_agent contains "ChatGPT-User") or
(http.user_agent contains "GPTBot") or
(http.request.uri.path eq "/invoke/schema") or
(http.request.uri.path eq "/invoke") or
(http.request.uri.path eq "/health")

Action: Skip → All rules
```

### Step 2: Verify Cloudflare Fix

**Test Schema Endpoint:**
```bash
# Should return OpenAPI schema JSON
curl https://guardiansofthetoken.org/invoke/schema | jq .info.title
→ "CryptoSatX Unified RPC API"

# Should show operations
curl https://guardiansofthetoken.org/invoke/schema | jq '.paths["/invoke"].post.requestBody.content["application/json"].schema.properties.operation.enum[0:5]'
→ ["signals.get", "smart_money.scan", "mss.discover", ...]
```

**Test Invoke Endpoint:**
```bash
# Test signals.get operation
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "signals.get",
    "args": {"symbol": "SOL"}
  }' | jq .

# Expected response:
{
  "ok": true,
  "operation": "signals.get",
  "data": {
    "symbol": "SOL",
    "signal": "LONG" | "SHORT" | "NEUTRAL",
    "score": 75.5,
    "confidence": "high",
    ...
  },
  "meta": {
    "execution_time_ms": 245.67,
    "namespace": "signals"
  }
}
```

**Test Health Check:**
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "health.check",
    "args": {}
  }' | jq .

# Expected:
{
  "ok": true,
  "operation": "health.check",
  "data": {
    "status": "healthy",
    "service": "CryptoSatX RPC Endpoint",
    "version": "3.0.0",
    "operations_count": 155
  }
}
```

## GPT Actions Configuration

### Step 3: Import Schema ke GPT Actions

**Setelah Cloudflare fix:**

1. **Open ChatGPT:**
   - Go to Settings → Actions
   - Create new action

2. **Import Schema:**
   ```
   Schema URL: https://guardiansofthetoken.org/invoke/schema
   ```

3. **Authentication:** None (public API)
   - Atau set API Key jika kamu enforce authentication

4. **Test in Preview:**
   ```json
   {
     "operation": "signals.get",
     "args": {"symbol": "BTC"}
   }
   ```

### Step 4: GPT Instructions (Custom Instructions)

**Tambahkan di GPT instructions untuk optimal usage:**

```markdown
# CryptoSatX Trading Signal Assistant

You have access to CryptoSatX API dengan 155+ operations via unified RPC endpoint.

## Available Operations (Top Used):

### Core Signals:
- signals.get - Get trading signal for symbol
  Example: {"operation": "signals.get", "args": {"symbol": "BTC"}}

- market.get - Get comprehensive market data
  Example: {"operation": "market.get", "args": {"symbol": "ETH"}}

### Smart Money Analysis:
- smart_money.scan - Scan whale accumulation/distribution
  Example: {"operation": "smart_money.scan", "args": {"min_accumulation_score": 7}}

- smart_money.analyze - Analyze smart money for specific coin
  Example: {"operation": "smart_money.analyze", "args": {"symbol": "SOL"}}

### MSS Discovery:
- mss.discover - Discover high-potential cryptocurrencies
  Example: {"operation": "mss.discover", "args": {"min_mss_score": 75, "max_results": 10}}

- mss.analyze - Analyze MSS for symbol
  Example: {"operation": "mss.analyze", "args": {"symbol": "AVAX"}}

### LunarCrush Social Data:
- lunarcrush.coin - Get social metrics (60+ data points)
  Example: {"operation": "lunarcrush.coin", "args": {"symbol": "DOGE"}}

- lunarcrush.coins_discovery - Discover trending coins
  Example: {"operation": "lunarcrush.coins_discovery", "args": {"min_galaxy_score": 60}}

### Coinglass Data:
- coinglass.liquidations.symbol - Get liquidation data
  Example: {"operation": "coinglass.liquidations.symbol", "args": {"symbol": "BTC"}}

- coinglass.funding_rate.history - Get funding rate history
  Example: {"operation": "coinglass.funding_rate.history", "args": {"symbol": "ETH", "interval": "h1"}}

- coinglass.indicators.fear_greed - Get Fear & Greed Index
  Example: {"operation": "coinglass.indicators.fear_greed", "args": {}}

## Response Format:
All operations return:
{
  "ok": true/false,
  "operation": "operation.name",
  "data": { ... },  // Operation result
  "meta": {
    "execution_time_ms": 123.45,
    "namespace": "namespace"
  },
  "error": "error message if ok=false"
}

## Usage Guidelines:
1. Always provide required args (especially "symbol" for coin-specific operations)
2. Check "ok" field to verify success
3. Use appropriate operations based on user request
4. Combine multiple operations for comprehensive analysis
5. Handle errors gracefully

## Example User Requests:

User: "Berikan signal untuk SOL"
→ Use: {"operation": "signals.get", "args": {"symbol": "SOL"}}

User: "Cari coin yang lagi accumulation whale"
→ Use: {"operation": "smart_money.scan", "args": {"min_accumulation_score": 8}}

User: "Discover gem coin dengan MSS tinggi"
→ Use: {"operation": "mss.discover", "args": {"min_mss_score": 80, "max_results": 5}}

User: "Analisa BTC lengkap"
→ Use multiple operations:
  1. {"operation": "signals.get", "args": {"symbol": "BTC"}}
  2. {"operation": "smart_money.analyze", "args": {"symbol": "BTC"}}
  3. {"operation": "lunarcrush.coin", "args": {"symbol": "BTC"}}
```

## Testing GPT Actions

### Test Case 1: Get Signal
**User asks:** "Berikan signal untuk SOL"

**GPT should call:**
```json
{
  "operation": "signals.get",
  "args": {"symbol": "SOL"}
}
```

**Expected response:**
```json
{
  "ok": true,
  "operation": "signals.get",
  "data": {
    "symbol": "SOL",
    "signal": "LONG",
    "score": 78.5,
    "confidence": "high",
    "reasons": [
      "Strong funding rate divergence",
      "Whale accumulation detected",
      "Positive social sentiment"
    ],
    "timestamp": "2025-11-13T..."
  },
  "meta": {
    "execution_time_ms": 245.67,
    "namespace": "signals"
  }
}
```

**GPT should respond to user:**
```
📊 Signal untuk SOL:

🟢 **LONG** (Confidence: HIGH)
Score: 78.5/100

**Alasan utama:**
1. Strong funding rate divergence
2. Whale accumulation detected
3. Positive social sentiment

💡 Recommendation: Consider LONG position dengan proper risk management.
```

### Test Case 2: Smart Money Scan
**User asks:** "Coin mana yang lagi di-accumulate whale?"

**GPT should call:**
```json
{
  "operation": "smart_money.scan",
  "args": {
    "min_accumulation_score": 7
  }
}
```

### Test Case 3: MSS Discovery
**User asks:** "Cari 5 gem coin terbaik"

**GPT should call:**
```json
{
  "operation": "mss.discover",
  "args": {
    "min_mss_score": 75,
    "max_results": 5
  }
}
```

### Test Case 4: Health Check
**User asks:** "Cek status API"

**GPT should call:**
```json
{
  "operation": "health.check",
  "args": {}
}
```

## Available Operations List (155+)

Your RPC endpoint supports operations dalam namespace berikut:

### Core (2 ops):
- signals.get
- market.get

### Smart Money (8 ops):
- smart_money.scan
- smart_money.scan_accumulation
- smart_money.scan_distribution
- smart_money.analyze
- smart_money.discover
- smart_money.futures_list
- smart_money.scan_auto
- smart_money.info

### MSS - Multi-Modal Signal Score (9 ops):
- mss.discover
- mss.analyze
- mss.scan
- mss.watch
- mss.info
- mss.telegram_test
- mss.history
- mss.history_symbol
- mss.top_scores

### Coinglass (65+ ops):
- Markets, liquidations, funding rates
- Open interest, orderbook data
- Indicators (RSI, MA, EMA, Bollinger, MACD, etc)
- Whale tracking, on-chain data
- Fear & Greed Index
- And 60+ more endpoints...

### LunarCrush (5 ops):
- lunarcrush.coin
- lunarcrush.coin_time_series
- lunarcrush.coin_change
- lunarcrush.coin_momentum
- lunarcrush.coins_discovery

### CoinAPI (7 ops):
- coinapi.quote
- coinapi.ohlcv.latest
- coinapi.ohlcv.historical
- coinapi.orderbook
- coinapi.trades
- coinapi.multi_exchange
- coinapi.dashboard

### Narratives (6 ops):
- narratives.discover_realtime
- narratives.momentum
- narratives.timeseries
- narratives.change
- narratives.coin
- narratives.info

### SMC - Smart Money Concept (2 ops):
- smc.analyze
- smc.info

### Health & Monitoring (2 ops):
- health.check
- health.root

**Total: 155+ operations via single `/invoke` endpoint!**

## Troubleshooting

### Issue: "Kesalahan saat berbicara dengan connector"

**Cause:** Cloudflare blocking request

**Fix:**
1. ✅ Configure Cloudflare WAF (see Step 1 above)
2. ✅ Test with curl to verify
3. ✅ Re-import schema in GPT Actions

### Issue: "Missing required argument 'symbol'"

**Cause:** GPT calling without required args

**Fix:** Update GPT instructions to always include required args:
```json
// ❌ Wrong:
{"operation": "signals.get"}

// ✅ Correct:
{"operation": "signals.get", "args": {"symbol": "BTC"}}
```

### Issue: "Unknown operation"

**Cause:** Operation name typo or not registered in RPC dispatcher

**Fix:**
- Check operation name spelling
- Use exact names from operation catalog
- Call `health.check` to verify RPC is working

### Issue: Schema import fails in GPT Actions

**Cause:** `/invoke/schema` endpoint blocked by Cloudflare

**Fix:**
1. Fix Cloudflare WAF first
2. Verify: `curl https://guardiansofthetoken.org/invoke/schema`
3. Should return valid OpenAPI JSON
4. Then import in GPT Actions

## Performance Optimization

### Recommended Operations for Different Use Cases:

**Quick Signal (fast response):**
```json
{"operation": "signals.get", "args": {"symbol": "BTC"}}
```

**Deep Analysis (comprehensive):**
```json
// Call multiple operations:
1. signals.get
2. smart_money.analyze
3. mss.analyze
4. lunarcrush.coin
```

**Market Scan (find opportunities):**
```json
{"operation": "smart_money.scan", "args": {"min_accumulation_score": 7}}
{"operation": "mss.discover", "args": {"min_mss_score": 75}}
```

## Security Notes

### Rate Limiting
- Cloudflare rate limiting tetap aktif
- Recommended: 100 requests per 10 seconds per IP
- GPT Actions automatically handles retries

### Authentication (Optional)
Jika kamu mau enforce API key:

1. Update OpenAPI schema dengan security scheme
2. Add X-API-Key header requirement
3. Configure in GPT Actions authentication

## Summary Checklist

- [x] RPC dispatcher implemented correctly (155+ operations)
- [x] `/invoke` endpoint working in code
- [x] `/invoke/schema` endpoint returning proper OpenAPI schema
- [ ] **Cloudflare WAF configured to allow OpenAI** ← CRITICAL!
- [ ] Schema accessible via curl (test after Cloudflare fix)
- [ ] Schema imported in GPT Actions
- [ ] GPT instructions configured
- [ ] Test cases passing
- [ ] No more "Access denied" errors
- [ ] GPT dapat fetch signal untuk SOL successfully

## Next Steps

1. **FIX CLOUDFLARE** (5 minutes) - See Step 1
2. **Verify dengan curl** - See Step 2
3. **Import schema ke GPT Actions** - See Step 3
4. **Add GPT instructions** - See Step 4
5. **Test dengan user request** - See Testing section
6. **Monitor performance** - Check response times

Setelah Cloudflare fix, semua 155+ operations akan accessible via GPT Actions! 🚀

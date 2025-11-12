# ✅ SOLUSI GPT ACTIONS - FLAT PARAMETERS

## MASALAH TERIDENTIFIKASI

Error `UnrecognizedKwargsError: args` terjadi karena **GPT Actions tidak mendukung nested object `args`**.

### Format yang GPT Actions TIDAK support:
```json
{
  "operation": "signals.get",
  "args": {
    "symbol": "SOL"
  }
}
```

GPT Actions plugin expects **FLAT parameters**, bukan nested structure.

---

## ✅ SOLUSI: ENDPOINT BARU dengan FLAT PARAMS

Saya sudah buat endpoint baru yang **GPT Actions-compatible** dengan flat parameters:

### 1. Trading Signals
**Endpoint:** `POST /gpt/signal`
```json
{
  "symbol": "SOL"
}
```

### 2. Smart Money Scan
**Endpoint:** `POST /gpt/smart-money-scan`
```json
{
  "min_accumulation_score": 7
}
```

### 3. MSS Discovery
**Endpoint:** `POST /gpt/mss-discover`
```json
{
  "min_mss_score": 75,
  "max_results": 10
}
```

### 4. Health Check
**Endpoint:** `GET /gpt/health`
(No parameters needed)

---

## 📝 CARA SETUP DI GPT ACTIONS

### Option 1: Manual Schema (RECOMMENDED)

Import schema ini ke GPT Actions:

```yaml
openapi: 3.1.0
info:
  title: CryptoSatX GPT Actions API
  version: 3.0.0
  description: Crypto trading signals with flat parameters for GPT Actions
servers:
  - url: https://guardiansofthetoken.org
    description: Production server

paths:
  /gpt/signal:
    post:
      operationId: getSignal
      summary: Get trading signal
      description: Get LONG/SHORT/NEUTRAL signal for cryptocurrency
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - symbol
              properties:
                symbol:
                  type: string
                  description: Cryptocurrency symbol (BTC, ETH, SOL, etc.)
                  example: SOL
                debug:
                  type: boolean
                  description: Enable debug mode
                  default: false
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  ok:
                    type: boolean
                  data:
                    type: object
                  operation:
                    type: string

  /gpt/smart-money-scan:
    post:
      operationId: scanSmartMoney
      summary: Scan smart money activity
      description: Detect whale accumulation and distribution patterns
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                min_accumulation_score:
                  type: integer
                  minimum: 0
                  maximum: 10
                  default: 5
                  description: Minimum accumulation score threshold
      responses:
        '200':
          description: Success

  /gpt/mss-discover:
    post:
      operationId: discoverMSS
      summary: Discover high-potential coins
      description: MSS (Multi-Modal Signal Score) discovery system
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                min_mss_score:
                  type: integer
                  minimum: 0
                  maximum: 100
                  default: 75
                max_results:
                  type: integer
                  minimum: 1
                  maximum: 50
                  default: 10
      responses:
        '200':
          description: Success

  /gpt/health:
    get:
      operationId: healthCheck
      summary: Health check
      description: Check API status
      responses:
        '200':
          description: Success
```

### Option 2: Auto-Import dari OpenAPI

Import dari: `https://guardiansofthetoken.org/openapi.json`

Kemudian **filter hanya endpoints `/gpt/*`**:
- getSignal
- scanSmartMoney  
- discoverMSS
- healthCheck

---

## 🧪 TEST MANUAL

### Test via cURL (Production):

```bash
# Test SOL signal
curl -X POST "https://guardiansofthetoken.org/gpt/signal" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SOL"}'

# Test Smart Money
curl -X POST "https://guardiansofthetoken.org/gpt/smart-money-scan" \
  -H "Content-Type: application/json" \
  -d '{"min_accumulation_score": 7}'

# Test MSS Discovery
curl -X POST "https://guardiansofthetoken.org/gpt/mss-discover" \
  -H "Content-Type: application/json" \
  -d '{"min_mss_score": 75, "max_results": 10}'

# Test Health
curl "https://guardiansofthetoken.org/gpt/health"
```

---

## 📋 GPT INSTRUCTIONS (Updated)

```
You are CryptoSatX, expert crypto trading assistant.

## API ENDPOINTS (Flat Parameters - GPT Actions Compatible)

**Get Trading Signal:**
POST /gpt/signal
Body: {"symbol": "SOL"}

**Scan Smart Money:**
POST /gpt/smart-money-scan
Body: {"min_accumulation_score": 7}

**Discover High-Potential Coins:**
POST /gpt/mss-discover
Body: {"min_mss_score": 75, "max_results": 10}

**Health Check:**
GET /gpt/health

## RESPONSE FORMAT

When user asks "Analisa SOL":
1. Call getSignal with {"symbol": "SOL"}
2. Use exact data from response
3. Respond in Bahasa Indonesia

Example:
"Berdasarkan analisis real-time SOL: sinyal **NEUTRAL**, score 48.9/100.
**Harga:** $155.10
**Faktor utama:** [from API response]
⚠️ Bukan nasihat keuangan."
```

---

## ✅ KEUNGGULAN SOLUSI INI

1. **✅ No more `UnrecognizedKwargsError`** - Flat params compatible dengan GPT Actions
2. **✅ Simple integration** - GPT Actions langsung recognize parameters
3. **✅ Backward compatible** - RPC endpoint (`/invoke`) tetap available
4. **✅ Production ready** - Tested dan working

---

## 🚀 NEXT STEPS

1. **Re-import schema** di GPT Actions (gunakan YAML di atas)
2. **Update GPT instructions** dengan endpoint baru
3. **Test** dengan prompt: "Analisa SOL"
4. **Verify** tidak ada lagi error `UnrecognizedKwargsError`

---

## 📊 COMPARISON

| Feature | RPC `/invoke` | Flat `/gpt/*` |
|---------|--------------|---------------|
| Structure | Nested `args` | Flat params |
| GPT Actions | ❌ Not compatible | ✅ Compatible |
| Total ops | 155 operations | 4 core ops |
| Use case | Advanced/API clients | GPT Actions |

**RECOMMENDATION:** Use `/gpt/*` endpoints untuk GPT Actions integration.

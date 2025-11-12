# ⚡ Quick Start - GPT Actions Setup (5 Menit)

## ✅ CURRENT STATUS
- Production endpoints: **WORKING**
- Test results: BTC LONG (53.1), SOL LONG (52.3)
- Issue fixed: No more `UnrecognizedKwargsError`

---

## 🚀 SETUP IN 3 STEPS

### STEP 1: Import Schema (2 menit)

1. Buka GPT Builder
2. Klik tab **"Actions"**
3. Klik **"Import from file"** atau paste YAML ini:

```yaml
openapi: 3.1.0
info:
  title: CryptoSatX
  version: 3.0.0
servers:
  - url: https://guardiansofthetoken.org

paths:
  /gpt/signal:
    post:
      operationId: getTradingSignal
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [symbol]
              properties:
                symbol:
                  type: string
                  example: BTC
                debug:
                  type: boolean
                  default: false

  /gpt/health:
    get:
      operationId: checkHealth
```

4. Click **"Save"**

---

### STEP 2: Update Instructions (1 menit)

Tambahkan ke GPT Instructions:

```
When user asks to analyze crypto (e.g., "Analisa BTC"):
1. Call getTradingSignal with {"symbol": "BTC"}
2. Use REAL data from response
3. Respond in Bahasa Indonesia
4. Include disclaimer

Example response:
"Berdasarkan analisis real-time BTC:
Sinyal: LONG 📈 (score: 53/100)
Harga: $101,530
⚠️ Bukan nasihat keuangan."
```

---

### STEP 3: Test (2 menit)

**Test Prompt 1:** "Analisa BTC"

**Expected:**
- GPT calls getTradingSignal
- Returns: LONG/SHORT/NEUTRAL
- Shows real price ($101k+)
- Response in Indonesian

**Test Prompt 2:** "Check API health"

**Expected:**
- GPT calls checkHealth
- Returns: "healthy - operational"

---

## ✅ SUCCESS CRITERIA

Anda berhasil jika:
1. ✅ GPT calls `getTradingSignal` (terlihat di Actions log)
2. ✅ Response shows REAL price (bukan mock)
3. ✅ No error `UnrecognizedKwargsError`
4. ✅ Response dalam Bahasa Indonesia

---

## 🐛 TROUBLESHOOTING

**Issue:** Still get "UnrecognizedKwargsError"
**Fix:** Delete old action, re-import schema above

**Issue:** GPT doesn't call action
**Fix:** Add to instructions: "Always use getTradingSignal for crypto analysis"

**Issue:** Returns mock data
**Fix:** Verify schema URL is correct: `https://guardiansofthetoken.org`

---

## 📞 NEXT STEPS

Setelah test berhasil:
1. ✅ Share test results dengan saya
2. ✅ Kita bisa tambah crypto_adapter untuk reliability (optional)
3. ✅ Or finalize dan deploy to users

**Test sekarang dan kabari hasilnya!** 🚀

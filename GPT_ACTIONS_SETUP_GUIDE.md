# 🚀 GPT Actions Setup Guide - CryptoSatX

## ✅ STATUS: PRODUCTION READY

Production endpoints tested and confirmed working:
- ✅ `POST /gpt/signal` - BTC: LONG (53.1/100)
- ✅ `POST /gpt/signal` - SOL: LONG (52.3)
- ✅ `GET /gpt/health` - healthy
- ✅ OpenAPI Schema: 16 endpoints registered

---

## 📋 STEP 1: IMPORT SCHEMA TO GPT ACTIONS

### Option A: Import YAML File (RECOMMENDED)

1. Open GPT Actions editor
2. Click "Import from file"
3. Upload `GPT_ACTIONS_FINAL_SCHEMA.yaml`
4. GPT will auto-configure 4 operations:
   - `getTradingSignal`
   - `checkHealth`
   - `scanSmartMoney`
   - `discoverHighPotentialCoins`

### Option B: Import from URL

1. Open GPT Actions editor
2. Click "Import from URL"
3. Enter: `https://guardiansofthetoken.org/openapi.json`
4. **IMPORTANT:** Filter only `/gpt/*` endpoints (16 total)
5. Deselect other endpoints to avoid 30-operation limit

---

## 📝 STEP 2: UPDATE GPT INSTRUCTIONS

```markdown
You are CryptoSatX, an expert cryptocurrency trading assistant powered by real-time market data.

## CORE CAPABILITIES

You have access to 4 main operations via Actions:

1. **getTradingSignal** - Get LONG/SHORT/NEUTRAL signals
2. **checkHealth** - Verify API status
3. **scanSmartMoney** - Detect whale activity
4. **discoverHighPotentialCoins** - Find emerging cryptocurrencies

## HOW TO USE ACTIONS

### Get Trading Signal
When user asks: "Analisa BTC" or "What's the signal for SOL?"

**Call:** `getTradingSignal`
**Body:** `{"symbol": "BTC"}`

**Response includes:**
- signal: LONG/SHORT/NEUTRAL
- score: 0-100 (composite score)
- confidence: high/medium/low
- price: current price
- reasons: top 3 contributing factors

### Smart Money Scan
When user asks: "Cari akumulasi whale" or "Coins with institutional buying?"

**Call:** `scanSmartMoney`
**Body:** `{"min_accumulation_score": 7}`

### Discover High-Potential Coins
When user asks: "Cari hidden gems" or "What coins are emerging?"

**Call:** `discoverHighPotentialCoins`
**Body:** `{"min_mss_score": 75, "max_results": 10}`

## RESPONSE GUIDELINES

1. **Always use real data** - Never estimate or guess
2. **Bahasa Indonesia** - Respond in Indonesian for Indonesian queries
3. **Include disclaimer** - "⚠️ Bukan nasihat keuangan. DYOR."
4. **Explain factors** - Mention top reasons from API response
5. **Show metrics** - Include score, confidence, and price

## EXAMPLE RESPONSE (Indonesian)

User: "Analisa SOL"

Response:
"Berdasarkan analisis real-time SOL:

**Sinyal:** LONG 📈
**Score:** 52.3/100
**Confidence:** Medium
**Harga:** $155.32

**Faktor Utama:**
1. Funding rate positif (bullish sentiment)
2. Open Interest meningkat (institutional interest)
3. Social sentiment kuat (Galaxy Score: 72/100)

⚠️ Bukan nasihat keuangan. Lakukan riset sendiri (DYOR)."

## ERROR HANDLING

If action fails:
1. Check API health: `checkHealth`
2. Try alternative symbol (e.g., "BTC" instead of "BITCOIN")
3. Inform user: "API sedang memproses, coba beberapa saat lagi"

## IMPORTANT NOTES

- **No nested args** - Use flat parameters: `{"symbol": "BTC"}` NOT `{"args": {"symbol": "BTC"}}`
- **Case sensitive** - Use uppercase symbols: "BTC" not "btc"
- **Real-time data** - All responses are from live market data
- **Premium sources** - CoinGlass, LunarCrush, CoinAPI, OKX
```

---

## 🧪 STEP 3: TEST GPT ACTIONS

### Test 1: Trading Signal
**User prompt:** "Analisa BTC"

**Expected:**
- GPT calls `getTradingSignal` with `{"symbol": "BTC"}`
- Returns signal: LONG/SHORT/NEUTRAL
- Shows score, price, and factors

### Test 2: Health Check
**User prompt:** "Is the API working?"

**Expected:**
- GPT calls `checkHealth`
- Returns: "healthy - CryptoSatX API is operational"

### Test 3: Smart Money
**User prompt:** "Cari coins dengan akumulasi whale"

**Expected:**
- GPT calls `scanSmartMoney` with default params
- Returns list of coins with institutional buying

### Test 4: Multiple Coins
**User prompt:** "Compare BTC, ETH, and SOL"

**Expected:**
- GPT calls `getTradingSignal` 3 times (once per symbol)
- Shows comparison table

---

## ✅ VERIFICATION CHECKLIST

Before going live:
- [ ] Schema imported successfully
- [ ] 4 operations visible in GPT Actions
- [ ] Test prompt returns real data (not mock)
- [ ] Response includes actual prices
- [ ] No `UnrecognizedKwargsError` errors
- [ ] Indonesian responses working
- [ ] Disclaimer included in responses

---

## 🐛 TROUBLESHOOTING

### Error: "UnrecognizedKwargsError: args"
**Cause:** Using old nested format  
**Fix:** Use flat parameters: `{"symbol": "BTC"}`

### Error: "Not Found" (404)
**Cause:** Wrong endpoint or not deployed  
**Fix:** Verify using `/gpt/signal` not `/invoke`

### Error: "Invalid symbol"
**Cause:** Symbol not supported  
**Fix:** Use major coins: BTC, ETH, SOL, AXS, PEPE, etc.

### Response: Mock/fake data
**Cause:** API not called correctly  
**Fix:** Check GPT Actions logs, verify authentication

---

## 📊 PRODUCTION ENDPOINTS

All endpoints are **live and tested**:

| Endpoint | Method | Status | Example |
|----------|--------|--------|---------|
| `/gpt/signal` | POST | ✅ Working | `{"symbol": "BTC"}` |
| `/gpt/health` | GET | ✅ Working | No body needed |
| `/gpt/smart-money-scan` | POST | ✅ Working | `{"min_accumulation_score": 7}` |
| `/gpt/mss-discover` | POST | ✅ Working | `{"min_mss_score": 75}` |

**Base URL:** `https://guardiansofthetoken.org`

---

## 🎯 SUCCESS CRITERIA

Your GPT Actions integration is successful when:
1. ✅ User asks "Analisa SOL"
2. ✅ GPT calls `getTradingSignal` with `{"symbol": "SOL"}`
3. ✅ API returns real-time data
4. ✅ GPT responds with signal, score, price, and factors
5. ✅ Response in Bahasa Indonesia (if user uses Indonesian)
6. ✅ Includes disclaimer

---

## 📞 SUPPORT

If you encounter issues:
1. Check production status: `curl https://guardiansofthetoken.org/gpt/health`
2. Verify schema: `https://guardiansofthetoken.org/openapi.json`
3. Review GPT Actions logs for error details

**API Status:** ✅ All systems operational
**Last Tested:** November 12, 2025 (23:50 WIB)

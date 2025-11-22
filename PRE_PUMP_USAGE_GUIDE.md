# Pre-Pump Detection Engine - Panduan Penggunaan

## ⚠️ PENTING: Auto-Scan DISABLED

Auto-scanner **SENGAJA DIMATIKAN** untuk menghemat kuota API (seperti auto_scanner dan spike_detector yang sudah ada).

**Alasan:**
- Auto scanner boros API (bisa ratusan calls/jam)
- Sistem ini dirancang untuk **MANUAL ON-DEMAND** saja
- Dipanggil lewat GPT Actions atau Dashboard sesuai kebutuhan

---

## ✅ Cara Pakai (Manual Only)

### 1. **Via GPT Actions (ChatGPT)**

Kamu bisa langsung tanya ke ChatGPT:

#### Analisis 1 Coin:
```
"Analyze BTC for pre-pump signals"
"Check if ETH shows pre-pump patterns"
"Is SOL accumulating?"
```

**API yang dipanggil:**
```bash
POST /api/prepump/gpt/analyze
Body: { "symbol": "BTC", "timeframe": "1HRS" }
```

#### Scan Multiple Coins:
```
"Scan BTC, ETH, SOL, AVAX for pre-pump signals"
"Which coins show strong pre-pump patterns: BTC, ETH, BNB, SOL?"
```

**API yang dipanggil:**
```bash
POST /api/prepump/gpt/scan
Body: { "symbols": "BTC,ETH,SOL,AVAX", "min_score": 60.0 }
```

#### Quick Scan:
```
"Show me today's pre-pump opportunities"
"What are the best pre-pump coins right now?"
```

**API yang dipanggil:**
```bash
GET /api/prepump/gpt/quick-scan
```

---

### 2. **Via Dashboard/Direct API**

#### Analisis Single Coin:
```bash
GET http://localhost:8001/api/prepump/analyze/BTC?timeframe=1HRS
```

**Response:**
```json
{
  "symbol": "BTC",
  "score": 78,
  "confidence": 85,
  "verdict": "STRONG_PRE_PUMP",
  "recommendation": {
    "action": "BUY",
    "risk": "MEDIUM",
    "suggestedEntry": "IMMEDIATE",
    "stopLoss": "7-10% below entry",
    "takeProfit": "10-20% above entry"
  },
  "components": {
    "accumulation": { "score": 75, "verdict": "STRONG_ACCUMULATION" },
    "reversal": { "score": 82, "verdict": "STRONG_REVERSAL" },
    "whale": { "score": 77, "verdict": "STRONG_WHALE_ACCUMULATION" }
  }
}
```

#### Scan Multiple Coins:
```bash
curl -X POST "http://localhost:8001/api/prepump/scan?min_score=60" \
  -H "Content-Type: application/json" \
  -d '["BTC", "ETH", "SOL", "AVAX", "MATIC"]'
```

#### Top Opportunities:
```bash
GET http://localhost:8001/api/prepump/top-opportunities?symbols=BTC,ETH,SOL,AVAX&limit=3
```

#### Quick Scan (Popular Coins):
```bash
GET http://localhost:8001/api/prepump/quick-scan
```

#### Dashboard Data:
```bash
GET http://localhost:8001/api/prepump/dashboard?limit=10
```

---

### 3. **Component Analysis (Detail)**

Lihat breakdown per komponen:

```bash
# Accumulation saja
GET /api/prepump/components/BTC/accumulation

# Reversal patterns saja
GET /api/prepump/components/BTC/reversal

# Whale activity saja
GET /api/prepump/components/BTC/whale
```

---

## 📊 Interpretasi Hasil

### Score Ranges:
- **80-100**: 🚀 VERY_STRONG_PRE_PUMP → Action: STRONG_BUY
- **70-79**: ✅ STRONG_PRE_PUMP → Action: BUY
- **60-69**: 👀 MODERATE_PRE_PUMP → Action: WATCH
- **50-59**: ⚠️ WEAK_PRE_PUMP → Action: MONITOR
- **0-49**: ❌ NO_PRE_PUMP_SIGNAL → Action: AVOID

### Confidence:
- **70-100%**: High confidence (semua sinyal sejalan)
- **60-69%**: Moderate confidence
- **0-59%**: Low confidence (sinyal tidak sejalan)

### Trading Recommendations:

**VERY_STRONG_PRE_PUMP (Score 80+, Confidence 70+):**
- Entry: IMMEDIATE
- Position Size: FULL
- Stop Loss: 5-7% below entry
- Take Profit: 15-30% above entry
- Risk: LOW

**STRONG_PRE_PUMP (Score 70-79, Confidence 60+):**
- Entry: IMMEDIATE
- Position Size: MODERATE (50-70%)
- Stop Loss: 7-10% below entry
- Take Profit: 10-20% above entry
- Risk: MEDIUM

**MODERATE_PRE_PUMP (Score 60-69):**
- Entry: WAIT_FOR_CONFIRMATION
- Position Size: SMALL (20-30%)
- Stop Loss: 10% below entry
- Take Profit: 10-15% above entry
- Risk: MEDIUM

---

## 💡 Best Practices

### 1. **Hemat API Quota**
- ✅ Pakai quick-scan (15 coins) bukan scan semua
- ✅ Analisis 1 coin saat ada lead spesifik
- ❌ Jangan scan puluhan coin sekaligus berulang-ulang

### 2. **Timing yang Tepat**
- Gunakan 1-2x sehari untuk screening
- Analisis detail hanya untuk coins yang menarik
- Combine dengan analisis lain (Smart Money, MSS, dll)

### 3. **Risk Management**
- Selalu pakai stop loss sesuai rekomendasi
- Jangan all-in bahkan di VERY_STRONG signal
- Diversifikasi posisi

### 4. **Validation**
- Cross-check dengan komponen individual
- Lihat detail signals (volumeProfile, RSI, whale activity)
- Perhatikan confidence level

---

## 🚫 Yang TIDAK Boleh Dilakukan

### 1. **JANGAN Aktifkan Auto-Scanner**
```bash
# ❌ DISABLED - Endpoint ini di-comment out
# POST /api/prepump/scanner/start

# ✅ Pakai manual endpoint
GET /api/prepump/quick-scan
```

Auto-scanner bisa menghabiskan ratusan API calls per jam!

### 2. **JANGAN Scan Terlalu Banyak Coin**
```bash
# ❌ BAD - Scan 50 coins sekaligus
POST /api/prepump/scan
Body: ["BTC", "ETH", ... 50 coins]

# ✅ GOOD - Scan 5-10 coins yang relevan
POST /api/prepump/scan
Body: ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
```

Limit: Max 20 coins per scan untuk GPT endpoint

### 3. **JANGAN Scan Berulang-ulang**
```bash
# ❌ BAD - Scan tiap 5 menit
while true; do
  curl /api/prepump/quick-scan
  sleep 300
done

# ✅ GOOD - Scan 1-2x per hari sesuai kebutuhan
curl /api/prepump/quick-scan
```

---

## 🔗 API Quota Estimate

### Per Request Cost (Estimasi):

**Single Coin Analysis:**
```bash
GET /api/prepump/analyze/BTC
```
- CoinAPI: ~5-8 calls (OHLCV multiple timeframes, order book)
- CoinGlass: ~3-5 calls (funding rate, OI, liquidations)
- **Total: ~10 API calls per coin**

**Quick Scan (15 coins):**
```bash
GET /api/prepump/gpt/quick-scan
```
- **Total: ~150 API calls** (15 coins × 10 calls)

**Multi-Symbol Scan (5 coins):**
```bash
POST /api/prepump/scan
Body: ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
```
- **Total: ~50 API calls** (5 coins × 10 calls)

### Rekomendasi Usage:
- **Quick scan**: 1-2x per hari = ~300 calls/hari
- **Targeted analysis**: 5-10 coins per hari = ~100 calls/hari
- **Total harian**: ~400 calls (jauh lebih hemat dari auto-scanner yang 200-300 calls/JAM)

---

## 🤖 GPT Actions Setup

Untuk integrasi dengan ChatGPT, tambahkan ke GPT Actions:

### Action 1: Analyze Pre-Pump
```yaml
operationId: analyzePrepump
endpoint: POST /api/prepump/gpt/analyze
description: Analyze a single cryptocurrency for pre-pump signals
parameters:
  - symbol: required (BTC, ETH, SOL, etc.)
  - timeframe: optional (default: 1HRS)
```

### Action 2: Scan Pre-Pump
```yaml
operationId: scanPrepump
endpoint: POST /api/prepump/gpt/scan
description: Scan multiple cryptocurrencies for pre-pump opportunities
parameters:
  - symbols: required (comma-separated, e.g., "BTC,ETH,SOL")
  - min_score: optional (default: 60.0)
  - timeframe: optional (default: 1HRS)
```

### Action 3: Quick Scan
```yaml
operationId: quickScanPrepump
endpoint: GET /api/prepump/gpt/quick-scan
description: Quick scan of top 15 popular coins for pre-pump signals
parameters: none
```

---

## 📈 Use Case Examples

### Use Case 1: Daily Morning Screening
```
1. Wake up
2. Ask ChatGPT: "Show me today's pre-pump opportunities"
3. Review top 3-5 results
4. Analyze details: "Analyze SOL for pre-pump signals"
5. Make trading decision
```

### Use Case 2: Targeted Research
```
1. Dengar rumor tentang SOL di Twitter
2. Ask ChatGPT: "Is SOL accumulating? Check pre-pump signals"
3. Review accumulation/whale/reversal breakdown
4. Decide to enter or not
```

### Use Case 3: Portfolio Monitoring
```
1. Punya watchlist: BTC, ETH, AVAX, MATIC, LINK
2. Ask ChatGPT: "Scan BTC, ETH, AVAX, MATIC, LINK for pre-pump signals"
3. Review which ones show strong signals
4. Adjust position sizing
```

---

## ⚡ Quick Reference

### Endpoints Aktif:
```bash
✅ GET  /api/prepump/analyze/{symbol}
✅ POST /api/prepump/scan
✅ GET  /api/prepump/top-opportunities
✅ GET  /api/prepump/quick-scan
✅ GET  /api/prepump/dashboard
✅ GET  /api/prepump/components/{symbol}/accumulation
✅ GET  /api/prepump/components/{symbol}/reversal
✅ GET  /api/prepump/components/{symbol}/whale
✅ POST /api/prepump/gpt/analyze (GPT Actions)
✅ POST /api/prepump/gpt/scan (GPT Actions)
✅ GET  /api/prepump/gpt/quick-scan (GPT Actions)
```

### Endpoints Disabled:
```bash
❌ POST /api/prepump/scanner/start
❌ POST /api/prepump/scanner/stop
❌ POST /api/prepump/scanner/trigger
❌ POST /api/prepump/scanner/watchlist
```

---

## 📞 Support

Untuk pertanyaan atau masalah:
- Cek dokumentasi lengkap: `PRE_PUMP_DETECTION_ENGINE.md`
- API docs: `http://localhost:8001/docs`
- Logs: Cek error di console untuk debugging

**Remember:** Sistem ini MANUAL ONLY untuk menghemat API quota! 🚀

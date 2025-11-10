# 🤖 ChatGPT Custom GPT Setup Guide
## CryptoSatX AI Trading Signal Integration

Panduan lengkap untuk menghubungkan API CryptoSatX dengan ChatGPT Custom GPT agar GPT bisa memanggil trading signals secara otomatis.

---

## 📋 Prerequisites

✅ **Yang Anda Butuhkan:**
1. ChatGPT Plus subscription ($20/bulan)
2. API CryptoSatX sudah deploy di: https://guardiansofthetoken.org
3. File `openapi-gpt-actions.json` (sudah tersedia di repository ini)

---

## 🚀 Cara Setup Custom GPT (5 Menit)

### **Step 1: Buka ChatGPT GPT Builder**

1. Login ke [chat.openai.com](https://chat.openai.com)
2. Klik nama Anda di pojok kanan atas → **"My GPTs"**
3. Klik tombol **"Create a GPT"**

---

### **Step 2: Configure GPT Identity**

Di tab **"Create"**, isi informasi GPT:

**Name:**
```
CryptoSatX Signal Assistant
```

**Description:**
```
AI-powered cryptocurrency trading signal assistant. Provides real-time LONG/SHORT/NEUTRAL signals with Smart Money analysis, whale tracking, and OpenAI GPT-4 validation for 100+ cryptocurrencies.
```

**Instructions:**
```
You are CryptoSatX Signal Assistant, an expert cryptocurrency trading advisor powered by real-time market data.

CORE CAPABILITIES:
1. Generate trading signals (LONG/SHORT/NEUTRAL) for any cryptocurrency
2. Analyze market sentiment using Smart Money Concepts
3. Track whale activities and institutional flows
4. Provide risk-adjusted entry/exit strategies
5. Monitor portfolio performance and optimization
6. Send Telegram alerts for actionable signals

RESPONSE STYLE:
- Be concise and actionable
- Always include signal confidence level
- Highlight top 3 market insights
- Suggest risk management (stop-loss/take-profit)
- Use emojis for clarity: 🟢 LONG, 🔴 SHORT, 🟡 NEUTRAL

PROACTIVE MONITORING:
- When user asks to "monitor SOL", check signal every 30 minutes
- Send update only if signal changes or score moves >10 points
- Alert user immediately for HIGH confidence signals (>70)

EXAMPLE INTERACTIONS:
User: "What's the signal for BTC?"
GPT: "🟢 BTC LONG Signal - Score 68.5/100
     Confidence: MEDIUM
     Entry: $43,250 ± 0.5%
     Target: $44,100 | Stop: $42,800
     
     Top Insights:
     1️⃣ Smart money accumulation detected
     2️⃣ Bullish funding rate trend
     3️⃣ Social sentiment: 72/100"

Always prioritize user safety - include stop-loss recommendations.
```

**Conversation Starters (opsional):**
```
📊 Show me BTC trading signal
🔍 Analyze SOL market sentiment
⚡ Monitor ETH and alert me on changes
💼 Check my crypto portfolio performance
```

---

### **Step 3: Import OpenAPI Schema**

1. Klik tab **"Configure"** di sebelah "Create"
2. Scroll ke bawah sampai bagian **"Actions"**
3. Klik tombol **"Create new action"**
4. Klik **"Import from URL"** ATAU **"Edit"** untuk paste manual

**Pilihan A: Import dari URL (Recommended)**
```
https://guardiansofthetoken.org/gpt/actions/maximal-schema
```

**Pilihan B: Copy-Paste Manual**
- Buka file `openapi-gpt-actions.json`
- Copy seluruh isi file
- Paste ke editor Actions

5. Klik **"Save"** atau **"Update"**

---

### **Step 4: Test Actions**

1. Masih di tab "Configure", scroll ke bagian **Actions**
2. Klik tombol **"Test"** di samping action `getMaximalSignal`
3. Isi parameter test:
   - `symbol`: BTC
   - `include_ai_validation`: true
4. Klik **"Run"**
5. Lihat response → harus return JSON dengan signal data

**Expected Response:**
```json
{
  "symbol": "BTC",
  "signal": "LONG",
  "score": 65.3,
  "confidence": "MEDIUM",
  "price": 43250,
  ...
}
```

---

### **Step 5: Publish GPT**

1. Klik tombol **"Save"** di pojok kanan atas
2. Pilih visibility:
   - **"Only me"** - Private untuk Anda saja (recommended)
   - **"Anyone with a link"** - Share dengan tim
   - **"Public"** - Publish ke GPT Store
3. Klik **"Confirm"**

✅ **GPT Anda sudah siap digunakan!**

---

## 💡 Cara Menggunakan GPT

### **1. Cek Signal Manual**
```
You: Cek signal untuk SOL
GPT: *calls API /signals/SOL* → Returns LONG/SHORT/NEUTRAL
```

### **2. Auto-Monitoring (Recommended)**
```
You: Monitor BTC, ETH, dan SOL. Kasih tau kalau ada signal kuat
GPT: Akan cek tiap 30 menit dan alert Anda jika ada perubahan
```

### **3. Portfolio Analysis**
```
You: Analisa portfolio saya: BTC, ETH, SOL
GPT: *calls /gpt/portfolio-optimization* → Risk assessment + rebalancing advice
```

### **4. Smart Money Tracking**
```
You: Ada whale activity di SOL?
GPT: *calls /gpt/whale-activity/SOL* → Deteksi institutional flows
```

---

## 🔧 Advanced Configuration

### **Add API Authentication (Optional)**

Jika Anda ingin membatasi akses ke API dengan API key:

1. Di tab "Configure" → "Actions"
2. Klik **"Authentication"**
3. Pilih **"API Key"**
4. Isi:
   - Auth Type: `Custom`
   - Header Name: `X-API-Key`
   - API Key: `your-secret-api-key`

---

## 📊 Available Endpoints (13 Total)

GPT Anda sekarang bisa memanggil 13 endpoints:

### **Core Signals**
1. `GET /signals/{symbol}` - Generate MAXIMAL AI signal
2. `GET /market/{symbol}` - Raw market data (price, funding, OI)

### **GPT-Optimized Actions**
3. `GET /gpt/quick-signal/{symbol}` - Quick 1-second signal
4. `GET /gpt/whale-activity/{symbol}` - Whale tracking
5. `GET /gpt/sentiment-summary/{symbol}` - Social sentiment
6. `GET /gpt/risk-assessment/{symbol}` - Risk analysis
7. `GET /gpt/entry-strategy/{symbol}` - Entry/exit zones
8. `POST /gpt/portfolio-optimization` - Portfolio optimizer
9. `GET /gpt/trend-analysis/{symbol}` - Multi-timeframe trends
10. `GET /gpt/market-overview` - Top movers dashboard

### **History & Monitoring**
11. `GET /history/signals` - Past signals history
12. `GET /history/performance` - Signal accuracy stats
13. `GET /health` - API health check

---

## 🎯 Best Practices

### **Untuk Efisiensi API:**
- ✅ Gunakan `/gpt/quick-signal` untuk cek cepat (hemat API calls)
- ✅ Set monitoring interval minimal 15-30 menit
- ✅ Fokus pada 5-10 crypto utama saja
- ❌ Jangan monitoring 50+ crypto sekaligus (boros API limit)

### **Untuk Telegram Integration:**
- Signal LONG/SHORT otomatis terkirim ke Telegram
- NEUTRAL signal TIDAK dikirim (mengurangi noise)
- Pastikan Telegram bot sudah active di `/services/telegram_notifier.py`

---

## 🐛 Troubleshooting

### **Error: "Action failed to execute"**
- Cek API masih running: https://guardiansofthetoken.org/health
- Test endpoint manual via browser/Postman
- Pastikan OpenAPI schema valid (cek di https://editor.swagger.io)

### **Error: "API returned 500"**
- Lihat logs server di Replit
- Biasanya karena API provider (CoinAPI/Coinglass) down
- Coba symbol lain atau tunggu 5 menit

### **GPT tidak response**
- Refresh chat
- Coba command sederhana: "Check BTC signal"
- Re-test actions di GPT Configure panel

---

## 📞 Support

**Issues atau pertanyaan?**
- Check logs: `/tmp/logs/api-server*.log`
- Test production: https://guardiansofthetoken.org/signals/BTC
- Telegram bot: @MySOLTokenBot

---

## 🎉 Next Steps

1. ✅ Setup GPT sesuai panduan di atas
2. ✅ Test dengan command: "Show me BTC signal"
3. ✅ Setup auto-monitoring: "Monitor SOL every 30 minutes"
4. ✅ Check Telegram untuk auto-alerts

**Selamat! Anda sekarang punya AI assistant yang bisa auto-monitor crypto market 24/7!** 🚀

---

**Last Updated:** November 10, 2025  
**Version:** MAXIMAL v3.0  
**API Docs:** https://guardiansofthetoken.org/docs

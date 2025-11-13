# 🤖 GPT Actions Setup Guide

## ✅ Persiapan Sudah Lengkap!

API Anda **sudah fully ready** untuk integrasi dengan GPT Actions. Berikut detailnya:

---

## 📦 Apa yang Sudah Disiapkan

### 1. ✅ OpenAPI Schema
- **Endpoint**: `/gpt/action-schema`
- **Format**: OpenAPI 3.0 compatible
- **Total Operations**: 6 endpoints siap pakai
- **Status**: Production-ready

### 2. ✅ Endpoints yang Tersedia untuk GPT

| Endpoint | Fungsi | GPT Use Case |
|----------|--------|--------------|
| `/signals/{symbol}` | Get trading signal | "What's the signal for BTC?" |
| `/market/{symbol}` | Get raw market data | "Show me ETH market data" |
| `/smart-money/scan` | Scan whale activity | "Find coins whales are accumulating" |
| `/smart-money/scan/accumulation` | Find buy opportunities | "Which coins should I buy before retail?" |
| `/smart-money/scan/distribution` | Find short opportunities | "Which coins are being dumped by whales?" |
| `/health` | API health check | "Is the API working?" |

---

## 🚀 Dua Opsi Setup

### **Option 1: Gunakan Development URL (Sekarang)**
✅ **Bisa langsung dipakai tanpa deploy**  
⚠️ URL akan berubah setiap Replit restart

**Development URL:**
```
https://87abdc51-8802-483e-a3d7-f8d33853cc46-00-21r8ujyrrmcdu.riker.replit.dev
```

**Schema URL untuk GPT:**
```
https://87abdc51-8802-483e-a3d7-f8d33853cc46-00-21r8ujyrrmcdu.riker.replit.dev/gpt/action-schema
```

**Kapan Gunakan:**
- Testing dan development
- Proof of concept
- Demonstrasi fitur

---

### **Option 2: Deploy ke Production (Recommended)**
✅ **URL stabil dan tidak berubah**  
✅ **Lebih reliable untuk production GPT**  
✅ **Custom domain support**

**Setelah deploy, URL akan jadi:**
```
https://your-repl-name.repl.co
```

**Schema URL production:**
```
https://your-repl-name.repl.co/gpt/action-schema
```

**Kapan Gunakan:**
- Production GPT yang akan dipakai user
- Custom GPT yang di-share ke public
- Aplikasi jangka panjang

---

## 📝 Cara Setup GPT Actions

### Step 1: Buka GPT Builder
1. Go to: https://chat.openai.com/gpts/editor
2. Klik "Create a GPT"
3. Masuk ke tab **"Configure"**

### Step 2: Scroll ke Actions
1. Klik **"Create new action"**
2. Di bagian **"Schema"**, pilih **"Import from URL"**

### Step 3: Paste Schema URL

**Untuk Development (Testing):**
```
https://87abdc51-8802-483e-a3d7-f8d33853cc46-00-21r8ujyrrmcdu.riker.replit.dev/gpt/action-schema
```

**Untuk Production (Setelah Deploy):**
```
https://your-repl-name.repl.co/gpt/action-schema
```

### Step 4: Authentication
- **Select**: "None" (API sudah public, tidak perlu auth)
- Jika mau secure nanti, bisa tambahkan API key authentication

### Step 5: Test Actions
GPT akan auto-detect 6 operations:
- ✅ getSignal
- ✅ getMarketData
- ✅ scanSmartMoney
- ✅ scanAccumulation
- ✅ scanDistribution
- ✅ healthCheck

### Step 6: Configure GPT Instructions

**Contoh Instructions:**
```
You are a crypto trading assistant with access to real-time market data and smart money analysis.

You can:
1. Get trading signals (LONG/SHORT/NEUTRAL) for any cryptocurrency
2. Scan for coins being accumulated by whales (buy-before-retail opportunities)
3. Find coins being distributed by whales (short-before-dump signals)
4. Provide comprehensive market data analysis

When users ask about crypto signals:
- Use getSignal to get recommendations with reasons
- Use scanSmartMoney to find whale accumulation/distribution patterns
- Use scanAccumulation for buy opportunities
- Use scanDistribution for short opportunities

Always explain the reasoning behind signals and warn about market risks.
```

---

## 🎯 Contoh Penggunaan GPT

Setelah setup, user bisa tanya:

**Signal Queries:**
- "What's the trading signal for BTC?"
- "Should I buy ETH right now?"
- "Give me signals for SOL, AVAX, and NEAR"

**Smart Money Queries:**
- "Which coins are whales accumulating?"
- "Find me buy opportunities before retail discovers them"
- "Which coins are being dumped by smart money?"
- "Scan for accumulation signals with score > 7"

**Market Analysis:**
- "Show me comprehensive data for BTC"
- "What's the funding rate and open interest for ETH?"

---

## ⚡ Quick Start (5 Menit)

### Pakai Development URL Sekarang:

1. **Copy schema URL:**
   ```
   https://87abdc51-8802-483e-a3d7-f8d33853cc46-00-21r8ujyrrmcdu.riker.replit.dev/gpt/action-schema
   ```

2. **Go to GPT Builder:**
   https://chat.openai.com/gpts/editor

3. **Import schema** dari URL di atas

4. **Test dengan prompt:**
   "What's the trading signal for BTC?"

5. **Done!** GPT sekarang bisa akses API Anda ✅

---

## 🚀 Production Deployment (Recommended)

### Untuk URL Stabil:

1. **Deploy di Replit:**
   - Click "Deploy" button
   - Pilih "Autoscale" (sudah configured)
   - Wait deployment selesai

2. **Get Production URL:**
   - URL akan jadi: `https://your-repl-name.repl.co`
   - Schema: `https://your-repl-name.repl.co/gpt/action-schema`

3. **Update GPT Actions:**
   - Edit GPT Actions schema URL ke production URL
   - Test endpoints
   - Publish GPT ✅

---

## 🔐 Security Considerations

### Current Setup (Public API):
✅ No authentication required  
✅ Cocok untuk testing dan demo  
⚠️ Siapapun bisa akses API

### Future Enhancements:
- **API Key Authentication**: Tambahkan header `X-API-Key`
- **Rate Limiting**: Batasi requests per IP/user
- **Usage Tracking**: Monitor GPT usage
- **Webhook Logging**: Track GPT interactions

---

## 📊 API Rate Limits

**Current External API Limits:**
- **LunarCrush**: ~100 requests/minute (rate limiting aktif)
- **Coinglass**: Standard plan limits
- **CoinAPI**: Startup plan limits

**Recommendation untuk GPT:**
- Jangan spam smart money scanner (scan 38 coins)
- Use specific coins: `?coins=BTC,ETH,SOL`
- Cache results di GPT conversation

---

## 🎨 Contoh Custom GPT Names

- **"Crypto Whale Tracker"** - Focus on smart money signals
- **"AI Trading Analyst"** - General signals + analysis
- **"DeFi Signal Bot"** - DeFi-specific alerts
- **"Futures Trading Assistant"** - Futures-focused

---

## ✅ Checklist Setup

- [x] ✅ OpenAPI schema ready (`/gpt/action-schema`)
- [x] ✅ 6 endpoints documented
- [x] ✅ Development URL available
- [ ] 🔲 Deploy to production (optional but recommended)
- [ ] 🔲 Create custom GPT
- [ ] 🔲 Import schema to GPT Actions
- [ ] 🔲 Test GPT queries
- [ ] 🔲 Publish GPT (if sharing publicly)

---

## 🆘 Troubleshooting

**Q: GPT says "Failed to fetch schema"**  
A: Make sure API server running. Check URL accessible di browser.

**Q: GPT tidak bisa call endpoints**  
A: Verify CORS configured (already done). Check firewall settings.

**Q: Rate limiting errors (429)**  
A: Normal untuk concurrent scans. Reduce coin count atau use caching.

**Q: Development URL berubah**  
A: Deploy ke production untuk URL stabil.

---

## 📞 Support

Jika ada masalah dengan GPT Actions setup:
1. Test schema URL di browser: `/gpt/action-schema`
2. Verify endpoints work: `/docs`
3. Check API health: `/health`

---

**🎉 Ready to go! API Anda sudah fully compatible dengan GPT Actions!**

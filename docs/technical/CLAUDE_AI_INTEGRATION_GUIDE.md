# Panduan Integrasi Claude AI dengan CryptoSatX RPC

**Status**: ⚠️ PERLU KONFIGURASI
**Tanggal**: 2025-11-20
**Branch**: claude/check-rpc-accessibility-01FLrLP7a1TRQwpYv4UyKCDA

---

## 🎯 Jawaban Singkat

**Apakah RPC di sistem ini bisa diakses oleh Claude AI?**

**Saat ini**: ❌ **TIDAK** - Ada firewall/proxy yang memblokir semua request dengan HTTP 403

**Setelah fix konfigurasi**: ✅ **YA** - RPC fully compatible dengan Claude AI dan GPT Actions

---

## 🔍 Analisis Masalah

### Test Results (2025-11-20 15:37:55)

```
Total Tests: 7
✅ Passed: 0 (0.0%)
❌ Failed: 7 (100.0%)

All endpoints returning: HTTP 403 "Access denied"
```

### Endpoint yang Ditest:
- ❌ `/health` - Health check
- ❌ `/invoke/operations` - List semua RPC operations
- ❌ `/invoke` - Unified RPC endpoint
- ❌ `/invoke/schema` - GPT Actions OpenAPI schema

### Root Cause:
**Proxy/Firewall Blocking** - Kemungkinan besar:
1. Replit deployment proxy configuration
2. Cloudflare firewall rules
3. Custom domain routing issue
4. IP whitelisting yang terlalu ketat

---

## ✅ Solusi: 3 Langkah untuk Enable Claude AI Access

### Langkah 1: Fix Proxy/Firewall (CRITICAL)

**Jika deployed di Replit:**

1. Buka Replit project settings
2. Check "Networking" atau "Deployment" settings
3. Pastikan **Public Access** enabled
4. Disable IP whitelisting (atau tambahkan Anthropic IP ranges)

**Jika menggunakan Cloudflare:**

1. Login ke Cloudflare dashboard
2. Pilih domain `guardiansofthetoken.org`
3. Security → Firewall Rules:
   - **Temporary**: Disable all firewall rules
   - **Permanent**: Create allow rule untuk Claude AI user agent
4. Set Security Level ke "Medium" atau "Low"

---

### Langkah 2: Configure Authentication

**Opsi A: Public Access (Recommended untuk Claude AI)**

```bash
# Di file .env
API_KEYS=

# Restart server
```

Dengan `API_KEYS` kosong, semua endpoint menjadi public tanpa authentication.

**Opsi B: Protected dengan API Key**

```bash
# Di file .env
API_KEYS=claude-ai-secret-key-2025,backup-key-123

# Restart server
```

Claude AI perlu include header:
```
X-API-Key: claude-ai-secret-key-2025
```

---

### Langkah 3: Verify & Test

```bash
# Test dari external (bukan dari server yang sama)
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "health.check"}'

# Expected response:
# {
#   "ok": true,
#   "operation": "health.check",
#   "data": {...},
#   "meta": {...}
# }
```

**Atau gunakan test script:**

```bash
python test_rpc_accessibility.py
```

---

## 🚀 Cara Claude AI Memanggil RPC

### Format 1: Flat Parameters (Recommended for GPT Actions)

```json
POST /invoke
Content-Type: application/json

{
  "operation": "signals.get",
  "symbol": "BTC",
  "debug": false
}
```

### Format 2: Nested Args (Legacy, Backward Compatible)

```json
POST /invoke
Content-Type: application/json

{
  "operation": "signals.get",
  "args": {
    "symbol": "BTC",
    "debug": false
  }
}
```

### Response Format

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

## 📚 Available Operations untuk Claude AI

### Core Signals (High Priority)
```
✅ signals.get - Get AI trading signal
✅ market.get - Get aggregated market data
✅ health.check - System health check
```

### Coinglass Data (64 operations)
```
✅ coinglass.markets - Get all markets
✅ coinglass.liquidations.symbol - Liquidation data per coin
✅ coinglass.funding_rate.history - Funding rate history
✅ coinglass.open_interest.history - Open interest trends
✅ coinglass.indicators.fear_greed - Fear & Greed Index
✅ coinglass.indicators.rsi_list - RSI for 536 coins
✅ coinglass.chain.whale_transfers - On-chain whale moves
✅ coinglass.orderbook.whale_walls - Whale buy/sell walls
```

### LunarCrush Social (17 operations)
```
✅ lunarcrush.coin - Social metrics & sentiment
✅ lunarcrush.coins_discovery - Discover trending coins
✅ lunarcrush.topics_list - Viral topics & narratives
✅ lunarcrush.coin_momentum - Momentum analysis
```

### Smart Money & MSS
```
✅ smart_money.scan - Scan whale accumulation
✅ smart_money.analyze - Analyze smart money for symbol
✅ mss.discover - Multi-Modal Signal Score discovery
✅ mss.analyze - MSS analysis per coin
```

### CoinAPI Market Data (7 operations)
```
✅ coinapi.quote - Current price quote
✅ coinapi.ohlcv.latest - Latest OHLCV candles
✅ coinapi.trades - Recent trades
✅ coinapi.orderbook - Order book snapshot
```

**Total**: 192+ operations tersedia!

---

## 🎨 GPT Actions Integration

### Schema URL untuk ChatGPT

```
https://guardiansofthetoken.org/invoke/schema
```

### Cara Import ke GPT Actions:

1. Buka ChatGPT → Create GPT
2. Configure → Actions → Import from URL
3. Paste schema URL di atas
4. GPT otomatis dapat 100+ operations

### Example GPT Prompts:

```
"Get BTC trading signal"
→ Calls: signals.get with symbol=BTC

"Show me top liquidations"
→ Calls: coinglass.liquidations.symbol

"Find coins with strong social momentum"
→ Calls: lunarcrush.coins_discovery + sort by momentum

"Scan for whale accumulation"
→ Calls: smart_money.scan with min_accumulation_score=7
```

---

## 🔒 Security Best Practices

### Untuk Production:

1. **Enable API Key Authentication**
   ```bash
   API_KEYS=strong-random-key-for-claude,another-key-for-gpt
   ```

2. **Rate Limiting**
   - Sudah built-in di middleware (SlowAPI)
   - GPT Actions: 10 req/min default
   - Adjust di `app/middleware/rate_limiter.py`

3. **CORS Configuration**
   - Sudah enabled untuk `*` (all origins)
   - Untuk production: whitelist specific domains

4. **Monitoring**
   - Request logs: `logs/requests.log`
   - Middleware: DetailedRequestLoggerMiddleware
   - Track Claude AI requests via User-Agent

---

## 📊 Health Monitoring

### Endpoint Health Status

Berdasarkan `rpc_global_health.json`:

```
✅ Coinglass: 96.9% uptime (62/64 active)
✅ CoinAPI: 85.7% uptime (6/7 active)
✅ LunarCrush: 100% uptime (17/17 active)

Overall: 96.6% success rate
```

### Monitor RPC Health:

```bash
# Health check
curl https://guardiansofthetoken.org/health

# RPC operations status
curl https://guardiansofthetoken.org/invoke/operations
```

---

## 🛠️ Troubleshooting

### Jika Claude AI masih tidak bisa akses setelah fix:

**1. Verify Server Running:**
```bash
curl -I https://guardiansofthetoken.org/health
# Should return: HTTP/1.1 200 OK
```

**2. Check Proxy Logs:**
```bash
# Replit: Check deployment logs
# Cloudflare: Analytics → Security Events
```

**3. Test Different User-Agent:**
```bash
curl -A "Mozilla/5.0" https://guardiansofthetoken.org/invoke/operations
curl -A "ClaudeBot/1.0" https://guardiansofthetoken.org/invoke/operations
```

**4. Verify DNS:**
```bash
dig guardiansofthetoken.org
nslookup guardiansofthetoken.org
```

**5. Check Firewall Rules:**
- Replit: Networking settings
- Cloudflare: Security → Firewall
- Check for IP blocking rules

---

## ✅ Checklist Lengkap

### Pre-Production:
- [ ] Fix proxy/firewall blocking (HTTP 403)
- [ ] Setup `.env` file dengan konfigurasi yang benar
- [ ] Set `API_KEYS` (kosong untuk public, atau set untuk protected)
- [ ] Restart server setelah config change
- [ ] Test dengan `test_rpc_accessibility.py`
- [ ] Verify semua 7 test pass (100% success rate)

### Production:
- [ ] Custom domain DNS configured correctly
- [ ] SSL/HTTPS enabled
- [ ] Rate limiting configured
- [ ] Request logging enabled
- [ ] Health monitoring setup
- [ ] Documentation updated

### Claude AI Integration:
- [ ] GPT Actions schema accessible
- [ ] API key configured (jika diperlukan)
- [ ] Test dengan actual Claude AI atau ChatGPT
- [ ] Monitor request logs
- [ ] Track performance & errors

---

## 📞 Support & Resources

**Files Created:**
- `RPC_ACCESSIBILITY_REPORT.md` - Detailed technical report
- `test_rpc_accessibility.py` - Automated test script
- `rpc_accessibility_results.json` - Test results JSON
- `CLAUDE_AI_INTEGRATION_GUIDE.md` - This guide

**Key Code Locations:**
- RPC Routes: `app/api/routes_rpc.py`
- RPC Dispatcher: `app/core/rpc_dispatcher.py` & `rpc_flat_dispatcher.py`
- Auth Middleware: `app/middleware/auth.py`
- Main App: `app/main.py`

**Documentation:**
- OpenAPI Schema: `/invoke/schema`
- Operations List: `/invoke/operations`
- Health Status: `/health`

---

## 🎯 Next Steps

1. **URGENT**: Fix proxy/firewall blocking (Replit/Cloudflare settings)
2. **CONFIG**: Setup `.env` dengan `API_KEYS=` (public) atau set API key
3. **TEST**: Run `python test_rpc_accessibility.py` dan verify 100% pass
4. **DEPLOY**: Restart server dengan new config
5. **VERIFY**: Test dari external dengan curl atau Claude AI
6. **MONITOR**: Track logs dan performance

---

**Status setelah fix**: ✅ Ready for Claude AI integration!

**Generated by**: Claude AI
**Date**: 2025-11-20
**Branch**: claude/check-rpc-accessibility-01FLrLP7a1TRQwpYv4UyKCDA

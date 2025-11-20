# Berapa Coin yang Di-Scan?

## 📊 Limit Scan untuk Setiap Operasi

### 1. **Smart Money Scan** (`smart_money.scan`)

**Default: 30-40 coins**
- ✅ Dynamic discovery dari CoinGecko (top by 24h volume)
- ✅ Auto-update setiap 5 menit
- ✅ User bisa set custom limit (max 50)

**Cara Pakai:**
```json
{"operation": "smart_money.scan", "limit": 20}
{"operation": "smart_money.scan", "limit": 50}  // Max 50
```

**Coins yang di-scan:**
- Top 30-50 coins berdasarkan 24h trading volume
- Diambil dari CoinGecko (real-time)
- Cached 5 menit untuk efisiensi

**Contoh coins yang biasanya masuk:**
BTC, ETH, SOL, BNB, XRP, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, ATOM, LTC, ETC, NEAR, APT, ARB, OP, FTM, ALGO, SAND, MANA, GALA, AXS, CHZ, ENJ, dst.

---

### 2. **Spike Detection** (`spike.monitor_coin`)

**On-Demand Check:**
- ✅ Check 1 coin per call (yang user request)
- ✅ Real-time analysis (tidak perlu monitoring background)

**Background Monitoring (DISABLED):**
- Price Spike Detector: 100 coins (DISABLED to save quota)
- Social Monitor: 50 coins (DISABLED to save quota)
- Liquidation Detector: Market-wide (DISABLED to save quota)

**Cara Pakai:**
```json
{"operation": "spike.monitor_coin", "symbol": "SOL"}
{"operation": "spike.monitor_coin", "symbol": "BTC"}
```

---

### 3. **MSS Discovery** (`mss.discover`)

**Default: 10 hasil**
- ✅ Scan emerging coins (low market cap, high potential)
- ✅ User bisa set custom limit

**Cara Pakai:**
```json
{"operation": "mss.discover", "min_mss_score": 75, "limit": 10}
{"operation": "mss.discover", "min_mss_score": 70, "limit": 20}
```

**Filter Criteria:**
- Max FDV: $50M (default)
- Max Age: 72 hours (default)
- Min Volume: $100K (default)
- Min MSS Score: 65 (default)

---

### 4. **Coinglass Operations**

**Tidak ada limit scan** - Query per coin atau market-wide:

**Per Coin:**
```json
{"operation": "coinglass.liquidations.symbol", "symbol": "BTC"}
{"operation": "coinglass.funding_rate.history", "symbol": "ETH"}
```

**Market-Wide:**
```json
{"operation": "coinglass.liquidation.exchange_list"}  // All exchanges
{"operation": "coinglass.fear_greed"}  // Market sentiment
```

---

### 5. **LunarCrush Operations**

**Per Coin:**
```json
{"operation": "lunarcrush.coin_comprehensive", "symbol": "PEPE"}
```

**Discovery (Multi-Coin):**
```json
{"operation": "lunarcrush.trending"}  // Top trending coins
{"operation": "lunarcrush.top_gainers"}  // Top social gainers
{"operation": "lunarcrush.coins_realtime"}  // Real-time trending
```

---

## 🎯 Summary Table

| Operation | Default Coins | Max Limit | Source |
|-----------|--------------|-----------|---------|
| **smart_money.scan** | 30-40 | 50 | CoinGecko (top by volume) |
| **spike.monitor_coin** | 1 per call | - | On-demand only |
| **mss.discover** | 10 results | Custom | Binance + CoinGecko |
| **Coinglass ops** | 1 per call | - | Per coin or market-wide |
| **LunarCrush ops** | 1 per call | - | Per coin or trending list |

---

## 💡 Rekomendasi Penggunaan

### Untuk Scan Banyak Coins:
```json
// Scan top 30 coins untuk whale patterns
{"operation": "smart_money.scan", "limit": 30}

// Scan top 20 coins (lebih cepat)
{"operation": "smart_money.scan", "limit": 20}

// Max scan 50 coins (paling lambat, paling lengkap)
{"operation": "smart_money.scan", "limit": 50}
```

**Response Time:**
- 20 coins: ~15-20 detik
- 30 coins: ~25-30 detik
- 50 coins: ~40-50 detik

### Untuk Check Specific Coin:
```json
// Lebih cepat - langsung check 1 coin
{"operation": "smart_money.analyze", "symbol": "BTC"}
{"operation": "signals.get", "symbol": "SOL"}
```

**Response Time:**
- 1 coin: ~2-5 detik

---

## 🔧 Konfigurasi Environment Variables

```bash
# Smart Money Scan
MAX_SMART_MONEY_COINS=40  # Default 40 coins
SMART_MONEY_DYNAMIC_DISCOVERY=true  # Enable dynamic discovery

# Spike Detection (Background - Currently DISABLED)
# SPIKE_PRICE_TOP_COINS=100
# SPIKE_SOCIAL_TOP_COINS=50
```

---

## ✅ Best Practices

**1. Untuk Quick Check (1-5 coins):**
```json
{"operation": "smart_money.analyze", "symbol": "BTC"}
{"operation": "signals.get", "symbol": "ETH"}
```
- Lebih cepat
- Fokus per coin
- Response 2-5 detik

**2. Untuk Market Scan (20-30 coins):**
```json
{"operation": "smart_money.scan", "limit": 30}
```
- Dapat overview market
- Temukan whale accumulation/distribution
- Response 25-30 detik

**3. Untuk Deep Market Analysis (50 coins):**
```json
{"operation": "smart_money.scan", "limit": 50}
```
- Paling comprehensive
- Semua top coins covered
- Response 40-50 detik

**4. Untuk Discover New Gems:**
```json
{"operation": "mss.discover", "min_mss_score": 75, "limit": 10}
```
- Find emerging coins
- Low cap, high potential
- Response 10-15 detik

---

## 🚀 Tips Optimasi

1. **Pakai limit sesuai kebutuhan** - Jangan selalu max 50 kalau cuma butuh top 20
2. **Cache-aware** - Smart money scan cached 5 menit, jadi re-scan dalam 5 menit dapat hasil sama
3. **Parallel calls** - GPT bisa call multiple operations parallel untuk efficiency
4. **Focus on what matters** - Check specific coin lebih cepat daripada scan semua

---

**Kesimpulan:** Default scan **30-40 coins**, max **50 coins** untuk smart money scan. Operations lain biasanya per-coin atau market-wide aggregation.

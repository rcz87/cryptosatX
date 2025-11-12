# GPT Prompt Templates - CryptoSatX API Integration

## 🤖 **Prompt Templates untuk Menggunakan Semua API CryptoSatX**

### **📋 Template 1: Comprehensive Market Analysis**

```
Analisis komprehensif cryptocurrency [SYMBOL] menggunakan semua data yang tersedia:

1. **Signal AI Terkini** - Dapatkan sinyal trading dengan AI analysis
2. **Smart Money Concepts (SMC)** - Analisis struktur pasar institusional
3. **Data Historis** - Performa sinyal sebelumnya
4. **Market Data** - Data real-time dari Coinglass
5. **Social Sentiment** - Analisis sentimen dari LunarCrush
6. **Order Book Analysis** - Data depth dari CoinAPI

Gunakan endpoint berikut:
- GET /gpt/actions/signal-with-context/[SYMBOL]?include_smc=true&include_history=true
- GET /coinglass/markets?symbol=[SYMBOL]
- GET /smart-money/scan?symbol=[SYMBOL]

Berikan analisis lengkap dengan rekomendasi trading berdasarkan semua data.
```

### **📋 Template 2: Smart Money Pattern Analysis**

```
Lakukan analisis Smart Money Concepts untuk [SYMBOL] dengan timeframe [TIMEFRAME]:

1. **Break of Structure (BOS)** - Identifikasi breakout harga
2. **Change of Character (CHoCH)** - Deteksi perubahan tren
3. **Fair Value Gap (FVG)** - Temukan area ketidakseimbangan
4. **Market Structure** - Analisis struktur pasar keseluruhan

Gunakan endpoint:
- GET /smc/analyze/[SYMBOL]?timeframe=[TIMEFRAME]
- GET /smc/info
- GET /smart-money/scan

Kombinasikan dengan data dari:
- Coinglass untuk funding rate dan liquidation
- LunarCrush untuk social sentiment
- CoinAPI untuk order book depth

Berikan entry/exit suggestion berdasarkan pola SMC yang teridentifikasi.
```

### **📋 Template 3: Multi-Source Signal Validation**

```
Validasi sinyal trading untuk [SYMBOL] menggunakan multiple data sources:

**Primary Analysis:**
- AI Signal dari /signals/[SYMBOL]
- SMC Analysis dari /smc/analyze/[SYMBOL]

**Cross-Validation:**
- Coinglass data: /coinglass/markets
- LunarCrush sentiment: [integrated in signal]
- CoinAPI order book: [integrated in signal]

**Historical Context:**
- Signal history: /history/signals?symbol=[SYMBOL]&limit=10
- Performance stats: /history/statistics?symbol=[SYMBOL]

**Final Validation:**
- Smart money scan: /smart-money/scan
- Combined context: /gpt/actions/signal-with-context/[SYMBOL]

Buat kesimpulan trading dengan confidence level berdasarkan konfirmasi dari semua sources.
```

### **📋 Template 4: Institutional Flow Analysis**

```
Analisis aliran institusional untuk [SYMBOL] menggunakan data Coinglass:

1. **Funding Rate Analysis** - Biaya pinjaman dan sentimen market
2. **Open Interest Trends** - Minat trader institusional
3. **Liquidation Data** - Area stop loss besar
4. **Long/Short Ratio** - Sentimen trader besar
5. **Top Trader Positions** - Aktivitas trader profesional

Gunakan endpoint:
- GET /coinglass/markets?symbol=[SYMBOL]
- GET /smart-money/scan

Kombinasikan dengan:
- SMC analysis untuk struktur harga
- AI signal untuk konfirmasi timing
- Historical data untuk pattern recognition

Berikan insight tentang kemungkinan pergerakan harga berdasarkan aktivitas institusional.
```

### **📋 Template 5: Social Sentiment Integration**

```
Analisis sentimen sosial untuk [SYMBOL] menggunakan LunarCrush data:

1. **Social Volume** - Volume pembicaraan di media sosial
2. **Sentiment Score** - Positif/Negatif/Netral ratio
3. **Influence Score** - Dampak influencer crypto
4. **Reddit/Discord Activity** - Komunitas engagement
5. **Twitter Mentions** - Buzz di platform besar

Integrasikan dengan:
- AI signal untuk konfirmasi teknikal
- SMC analysis untuk struktur pasar
- Coinglass data untuk money flow
- Historical performance untuk pattern validation

Gunakan endpoint /signals/[SYMBOL] (includes LunarCrush data) dan berikan analisis sentimen vs teknikal.
```

### **📋 Template 6: Real-Time Market Monitoring**

```
Monitor real-time market untuk [SYMBOL] dengan semua API aktif:

**Data Collection:**
1. GET /signals/[SYMBOL] - AI signal terkini
2. GET /smc/analyze/[SYMBOL] - SMC pattern analysis
3. GET /coinglass/markets - Market data real-time
4. GET /smart-money/scan - Whale activity detection

**Alert System:**
- POST /gpt/actions/send-alert/[SYMBOL] - Kirim alert ke Telegram

**Historical Tracking:**
- GET /history/signals?symbol=[SYMBOL] - Track performance
- GET /history/statistics - Overall system stats

**System Health:**
- GET /health - System status
- GET /metrics - Performance metrics

Berikan real-time analysis dengan rekomendasi action untuk trading sekarang.
```

### **📋 Template 7: Portfolio Risk Assessment**

```
Lakukan risk assessment untuk portfolio crypto menggunakan semua data sources:

**For Each Symbol in Portfolio:**
1. **Signal Analysis** - GET /signals/[SYMBOL]
2. **SMC Analysis** - GET /smc/analyze/[SYMBOL]
3. **Market Data** - GET /coinglass/markets
4. **Historical Performance** - GET /history/statistics?symbol=[SYMBOL]

**Portfolio-Level Analysis:**
- Correlation analysis antar assets
- Risk distribution berdasarkan signals
- Exposure ke market conditions
- Liquidity assessment dari Coinglass data

**Risk Management:**
- Stop loss suggestions berdasarkan SMC
- Position sizing berdasarkan confidence scores
- Hedge opportunities dari market data

Berikan comprehensive risk report dengan actionable recommendations.
```

### **📋 Template 8: Arbitrage Opportunity Detection**

```
Deteksi arbitrage opportunities menggunakan multiple data sources:

**Data Sources:**
1. **CoinAPI** - Order book depth dan price feeds
2. **Coinglass** - Funding rate differences
3. **LunarCrush** - Sentiment-based price movements
4. **SMC Analysis** - Technical arbitrage patterns

**Analysis Framework:**
- Price differences antar exchanges (CoinAPI)
- Funding rate arbitrage opportunities (Coinglass)
- Sentiment-driven price inefficiencies (LunarCrush)
- Technical pattern arbitrage (SMC)

**Execution Strategy:**
- Entry/exit timing dengan AI signals
- Risk management dengan historical data
- Profit optimization dengan market data

Gunakan semua endpoints untuk identify dan validate arbitrage opportunities.
```

### **📋 Template 9: Market Regime Detection**

```
Identifikasi market regime (bull/bear/sideways) menggunakan comprehensive data:

**Technical Analysis:**
- SMC patterns dari /smc/analyze/[SYMBOL]
- AI signals dari /signals/[SYMBOL]
- Historical patterns dari /history/signals

**Market Structure:**
- Funding rate trends dari Coinglass
- Open interest changes dari Coinglass
- Liquidation patterns dari Coinglass

**Social Sentiment:**
- Social volume dari LunarCrush
- Sentiment shifts dari LunarCrush
- Influencer impact dari LunarCrush

**Institutional Activity:**
- Smart money flows dari /smart-money/scan
- Top trader positions dari Coinglass
- Whale accumulation/distribution patterns

Kombinasikan semua data untuk identify current market regime dan predict regime changes.
```

### **📋 Template 10: Advanced Backtesting Strategy**

```
Lakukan backtesting strategy menggunakan semua available data:

**Historical Data Collection:**
- GET /history/signals?symbol=[SYMBOL]&limit=1000
- GET /history/statistics?symbol=[SYMBOL]
- Simulate Coinglass historical data
- Simulate LunarCrush sentiment history

**Strategy Testing:**
1. **AI Signal Strategy** - Berdasarkan /signals/[SYMBOL]
2. **SMC Pattern Strategy** - Berdasarkan /smc/analyze/[SYMBOL]
3. **Combined Strategy** - AI + SMC + Market Data
4. **Sentiment Strategy** - Social sentiment integration

**Performance Metrics:**
- Win rate, profit factor, Sharpe ratio
- Maximum drawdown analysis
- Risk-adjusted returns
- Market condition performance

**Optimization:**
- Parameter tuning dengan historical data
- Market regime adaptation
- Risk management optimization

Gunakan /backtesting/strategy endpoint untuk comprehensive strategy testing.
```

---

## 🎯 **How to Use These Templates**

### **Step 1: Choose Template**
Pilih template yang sesuai dengan kebutuhan analisis Anda.

### **Step 2: Replace Placeholders**
- `[SYMBOL]` - Ganti dengan crypto symbol (BTC, ETH, SOL, dll)
- `[TIMEFRAME]` - Pilih timeframe (1MIN, 5MIN, 1HRS, 1DAY)

### **Step 3: Execute API Calls**
Gunakan curl, Postman, atau aplikasi HTTP client untuk memanggil endpoints.

### **Step 4: Analyze Results**
Kombinasikan data dari semua sources untuk comprehensive analysis.

---

## 📊 **Example Usage**

### **Complete Analysis Example:**
```
Analisis BTC dengan semua data sources:

1. GET /gpt/actions/signal-with-context/BTC?include_smc=true&include_history=true
2. GET /coinglass/markets?symbol=BTC
3. GET /smart-money/scan?symbol=BTC
4. GET /smc/analyze/BTC?timeframe=1HRS

Hasil: Comprehensive analysis dengan AI signal, SMC patterns, market data, dan historical context.
```

### **Quick Signal Check:**
```
Cek signal terkini untuk ETH:

GET /signals/ETH

Hasil: AI signal dengan confidence score dan rekomendasi.
```

---

## 🚀 **Advanced Features**

### **Real-Time Monitoring:**
- Gunakan WebSocket untuk real-time updates
- Setup alert system dengan /gpt/actions/send-alert/[SYMBOL]
- Monitor system health dengan /health dan /metrics

### **Batch Processing:**
- Process multiple symbols simultaneously
- Use parallel API calls untuk efficiency
- Cache results dengan Redis untuk performance

### **Custom Integration:**
- Combine dengan external data sources
- Build custom analytics dashboard
- Integrate dengan trading bots

**Templates ini memastikan Anda menggunakan semua kemampuan CryptoSatX secara maksimal!** 🎯

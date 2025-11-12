# GPT Prompt Templates - CryptoSatX API Integration (UPDATED 2025)

## 🤖 **Prompt Templates untuk GPT dengan 15 API Actions**

---

## 📋 **Template 1: Comprehensive Crypto Analysis**

```
Analisis lengkap cryptocurrency [SYMBOL] menggunakan semua data yang tersedia:

1. **Trading Signal (8-Factor)** - Sinyal LONG/SHORT/NEUTRAL
2. **LunarCrush Intelligence** - 60+ social metrics (Galaxy Score, AltRank, sentiment)
3. **MSS Discovery** - Multi-Modal Signal Score untuk hidden gems
4. **Smart Money** - Whale accumulation/distribution patterns
5. **Viral Detection** - Social spike analysis (>100% = viral!)

Gunakan actions:
- getSignal → Trading signal dengan 8-factor scoring
- getLunarCrushCoin → 60+ metrics (Galaxy Score, AltRank, social volume)
- getLunarCrushMomentum → Social momentum score 0-100
- getLunarCrushChange → Detect viral spikes (>300% = extreme!)

Berikan analisis dengan:
- Signal recommendation (LONG/SHORT/NEUTRAL)
- Confidence level (very_high/high/medium/low)
- Galaxy Score interpretation
- AltRank momentum analysis
- Spike detection results
- Risk warnings
```

---

## 📋 **Template 2: Hidden Gems Discovery (MSS System)**

```
Cari hidden gems dengan MSS (Multi-Modal Signal Score) system:

**3-Phase Analysis:**
1. **Discovery Phase** - Tokenomics filtering (market cap, FDV, volume)
2. **Social Confirmation** - LunarCrush metrics (Galaxy Score, social volume)
3. **Institutional Validation** - Whale positioning (funding, OI, liquidations)

Gunakan actions:
- scanMSS → Auto-scan emerging cryptocurrencies
- analyzeMSS → 3-phase analysis untuk specific coin
- getLunarCrushCoin → Social metrics validation

**MSS Tiers:**
- Diamond (≥80): Hidden gem dengan whale backing!
- Gold (65-79): Strong opportunity
- Silver (50-64): Moderate opportunity
- Bronze (<50): Weak signals

Filter by:
- max_fdv_usd: Maximum Fully Diluted Valuation (default 50M)
- max_age_days: Coin age (default 180 days)
- min_galaxy_score: Galaxy Score threshold (default 60)

Berikan hasil dengan:
- MSS score & tier classification
- 3-phase breakdown
- Signal strength (STRONG_LONG/MODERATE_LONG/LONG)
- Confidence level
- Risk warnings
```

---

## 📋 **Template 3: Real-Time Viral Moment Detection**

```
Detect viral moments dan trending cryptocurrencies secara real-time:

**Spike Detection:**
- Moderate (100-200%): Coin getting attention
- High (200-300%): Viral on social media
- Extreme (>300%): Massive FOMO incoming!

Gunakan actions:
- getLunarCrushChange → Detect social spikes untuk specific coin
- discoverRealtimeGems → Real-time discovery (NO CACHE - fresh data every minute!)
- getLunarCrushMomentum → Momentum score 0-100

Filter discovery:
- limit: Number of coins (max 100)
- min_galaxy_score: Quality threshold (60-100)
- sort: social_volume/market_cap/galaxy_score/alt_rank

Berikan hasil dengan:
- Spike level classification
- Social volume change (% increase)
- Sentiment score (0-100)
- Galaxy Score untuk quality check
- Price movement correlation
- FOMO alert level
```

---

## 📋 **Template 4: Smart Money Flow Analysis**

```
Analisis whale accumulation/distribution patterns:

**Accumulation Signals (Buy-before-retail):**
- High buy pressure + negative funding
- Low social activity + sideways price
- Whale accumulation detected
- Score: 7-10/10 = Strong accumulation

**Distribution Signals (Short-before-dump):**
- High sell pressure + overcrowded longs
- Social FOMO + recent pump
- Whale distribution detected
- Score: 7-10/10 = Strong distribution

Gunakan actions:
- scanSmartMoney → Scan both accumulation & distribution
- scanAccumulation → Find buy-before-retail signals (min_score default 6)
- scanDistribution → Find short-before-dump signals (min_score default 6)

Parameters:
- min_accumulation_score: 0-10 (default 5)
- min_distribution_score: 0-10 (default 5)
- coins: Comma-separated list (e.g., "BTC,ETH,SOL")

Berikan hasil dengan:
- Accumulation opportunities ranked by score
- Distribution warnings ranked by score
- Whale pattern explanation
- Entry/exit timing suggestions
```

---

## 📋 **Template 5: Social Intelligence Deep Dive**

```
Analisis mendalam social metrics menggunakan LunarCrush (7,635+ coins tracked):

**60+ Metrics Analysis:**
1. **Galaxy Score™** - 0-100 proprietary quality metric
2. **AltRank™** - Momentum ranking (lower = better, e.g., #10 > #500)
3. **Social Volume** - Total mentions (Twitter, Reddit, news)
4. **Sentiment** - 0-100 average sentiment score
5. **Social Engagement** - Likes, shares, comments
6. **Tweet/Reddit Volume** - Platform breakdown
7. **Correlation Rank** - Price-social correlation

Gunakan actions:
- getLunarCrushCoin → Comprehensive 60+ metrics
- getLunarCrushMomentum → Momentum score with trend data
- getLunarCrushTimeSeries → Historical social & market trends
- getLunarCrushTopic → Topic analysis (e.g., "bitcoin", "defi", "ai")

Time-series parameters:
- interval: 1h/1d/1w (default 1d)
- days_back: 1-365 (default 30)

Berikan insight:
- Galaxy Score interpretation (quality metric)
- AltRank momentum analysis (lower rank = better)
- Social volume trends (growing/declining)
- Sentiment trajectory (improving/deteriorating)
- Engagement strength
- Correlation patterns
```

---

## 📋 **Template 6: Multi-Source Signal Validation**

```
Validasi signal trading menggunakan multiple data sources:

**Primary Analysis:**
- getSignal → 8-factor trading signal (LONG/SHORT/NEUTRAL)
- getLunarCrushCoin → Social metrics validation

**MSS Validation:**
- analyzeMSS → 3-phase MSS analysis
  - Discovery: Tokenomics check
  - Social Confirmation: Galaxy Score, social volume
  - Institutional Validation: Whale positioning

**Smart Money Confirmation:**
- scanSmartMoney → Whale accumulation/distribution check
- getLunarCrushChange → Viral spike detection

**Momentum Analysis:**
- getLunarCrushMomentum → Social momentum 0-100
- getLunarCrushTimeSeries → Historical trend confirmation

Cross-validation checklist:
✅ Trading signal aligned with MSS score?
✅ Social metrics supporting price action?
✅ Whale activity confirming signal?
✅ No extreme spike (>300%) causing FOMO?
✅ Galaxy Score quality check (≥60)?
✅ AltRank momentum favorable?

Berikan final verdict:
- Signal: LONG/SHORT/NEUTRAL
- Confidence: very_high/high/medium/low
- Risk level: low/medium/high
- Entry timing: optimal/wait/avoid
```

---

## 📋 **Template 7: Portfolio Discovery & Screening**

```
Discover dan screen cryptocurrencies untuk portfolio:

**Discovery Process:**

1. **Real-Time Discovery** (NO CACHE!):
   - discoverRealtimeGems → Fresh data every minute
   - Filter by: min_galaxy_score (60-100)
   - Sort by: social_volume/market_cap/galaxy_score

2. **Advanced Filtering**:
   - discoverLunarCrushCoins → 7,635+ coins
   - Filter by: categories (layer-1, defi, meme, ai)
   - Filter by: min_galaxy_score, max_alt_rank

3. **MSS Screening**:
   - scanMSS → Find Diamond tier (≥80) opportunities
   - Filter by: max_fdv_usd (early-stage focus)
   - Filter by: max_age_days (new coins only)

**Quality Checks for Each Coin:**
- Galaxy Score ≥ 70? (quality threshold)
- AltRank < 200? (good momentum)
- MSS Score ≥ 65? (Gold tier minimum)
- Social Volume growing? (positive trend)
- No distribution signals? (whale check)

**Risk Assessment:**
- High FDV warning? (overvalued risk)
- Negative funding? (shorts pressure)
- Social spike >300%? (FOMO risk)

Berikan portfolio recommendations:
- Top 5 Diamond tier (MSS ≥80)
- Top 5 High momentum (AltRank <100)
- Top 5 Viral trending (social volume spike)
- Risk diversification strategy
```

---

## 📋 **Template 8: Topic & Narrative Analysis**

```
Analisis topics dan narratives yang sedang trending:

**Topic Research:**
- getLunarCrushTopic → Topic analysis (e.g., "ethereum", "defi", "ai")
- Topics to analyze: bitcoin, ethereum, defi, ai, meme, layer-1, gaming

**Narrative Discovery:**
- discoverRealtimeGems → Sort by social_volume untuk trending narratives
- discoverLunarCrushCoins → Filter by categories

**Cross-Topic Analysis:**
Compare metrics across topics:
- Social volume trends
- Sentiment comparison
- Related topics mapping
- Narrative shift detection

**Coin-to-Topic Mapping:**
For each trending topic:
1. Find top coins in category (discoverLunarCrushCoins)
2. Analyze social metrics (getLunarCrushCoin)
3. Check MSS scores (analyzeMSS)
4. Detect viral moments (getLunarCrushChange)

Berikan narrative report:
- Top 3 trending narratives (by social volume)
- Narrative sentiment (positive/negative/neutral)
- Best coins per narrative (MSS + Galaxy Score)
- Emerging vs declining narratives
- Investment opportunities per narrative
```

---

## 📋 **Template 9: Risk Monitoring & Alerts**

```
Monitor risks dan setup alerts untuk portfolio:

**Risk Indicators:**

1. **Distribution Signals** (Whale Selling):
   - scanDistribution → Score ≥7 = HIGH RISK
   - Check funding rate (positive = overcrowded longs)
   - Check social FOMO (spike >200%)

2. **Viral Spike Risk** (FOMO Entry):
   - getLunarCrushChange → Spike >300% = EXTREME RISK
   - Late entry after spike = high probability dump
   - Check if spike backed by fundamentals (MSS score)

3. **Quality Degradation**:
   - getLunarCrushCoin → Galaxy Score declining?
   - AltRank increasing? (worse momentum)
   - Social sentiment deteriorating?

4. **Tokenomics Warning**:
   - analyzeMSS → High FDV warning
   - Low liquidity warning
   - Negative funding persistent

**Monitoring Actions:**
For each portfolio coin:
- getSignal → Check if signal changed
- getLunarCrushChange → Detect unusual spikes
- scanDistribution → Check whale distribution
- getLunarCrushMomentum → Check momentum decline

**Alert Triggers:**
🚨 Distribution score ≥7 → SELL ALERT
🚨 Social spike >300% → FOMO WARNING
🚨 Galaxy Score drop >10 points → QUALITY WARNING
🚨 Signal flip (LONG → SHORT) → EXIT ALERT
🚨 Negative MSS phases → FUNDAMENTAL WARNING

Berikan risk report:
- High-risk holdings (immediate action)
- Medium-risk holdings (watch closely)
- Low-risk holdings (maintain position)
- Recommended actions per coin
```

---

## 📋 **Template 10: Complete Market Overview**

```
Get comprehensive market overview using all 15 API actions:

**Market Scanning:**
1. discoverRealtimeGems (limit=50, sort=social_volume) → Trending coins
2. scanMSS (max_fdv_usd=100000000) → Hidden gems discovery
3. scanSmartMoney → Whale activity across market

**Top Movers Analysis:**
For each top mover:
- getLunarCrushCoin → Social metrics
- getLunarCrushChange → Spike detection
- getLunarCrushMomentum → Momentum score
- analyzeMSS → MSS 3-phase analysis
- getSignal → Trading signal

**Sentiment Overview:**
- getLunarCrushTopic → Analyze major topics (bitcoin, ethereum, defi, ai)
- Compare sentiment across narratives
- Identify shift in market narrative

**Opportunity Classification:**

**Diamond Opportunities (MSS ≥80):**
- Hidden gems with whale backing
- Entry before retail FOMO

**High Momentum (AltRank <100):**
- Strong social momentum
- Riding the wave plays

**Viral Moments (Spike >200%):**
- High risk, high reward
- Quick scalp opportunities

**Accumulation Plays (Score ≥7):**
- Whale accumulation detected
- Buy-before-retail signals

**Risk Zones:**
- Distribution signals (Score ≥7)
- Extreme spikes (>300%)
- High FDV warnings

Berikan market summary:
- Overall market sentiment (bull/bear/neutral)
- Top 5 opportunities with rationale
- Top 5 risks to avoid
- Recommended strategy for current market regime
```

---

## 🎯 **How to Use These Templates with GPT**

### **Step 1: Copy Template**
Copy prompt template yang sesuai kebutuhan

### **Step 2: Replace Placeholders**
- `[SYMBOL]` → Replace dengan crypto symbol (BTC, ETH, PEPE, SHIB, etc.)
- Adjust parameters sesuai kebutuhan

### **Step 3: Paste to GPT**
Paste ke GPT Chat → GPT akan automatically call API actions

### **Step 4: Analyze Results**
GPT akan combine data dari multiple sources dan berikan analysis

---

## 📊 **Quick Reference: All 15 API Actions**

### **Core Trading:**
1. `getSignal` - Trading signal (8-factor scoring)
2. `getMarketData` - Raw market data

### **Smart Money:**
3. `scanSmartMoney` - Both accumulation & distribution
4. `scanAccumulation` - Buy-before-retail signals
5. `scanDistribution` - Short-before-dump signals

### **MSS Discovery:**
6. `analyzeMSS` - 3-phase analysis for specific coin
7. `scanMSS` - Auto-scan emerging cryptocurrencies

### **LunarCrush Intelligence (60+ Metrics):**
8. `getLunarCrushCoin` - Comprehensive social & market metrics
9. `getLunarCrushMomentum` - Social momentum analysis
10. `getLunarCrushChange` - Spike detection & viral moments
11. `getLunarCrushTimeSeries` - Historical trends
12. `discoverLunarCrushCoins` - Filter 7,635+ coins
13. `getLunarCrushTopic` - Topic analysis

### **Real-Time Discovery:**
14. `discoverRealtimeGems` - NO-CACHE real-time discovery

### **System:**
15. `healthCheck` - API status verification

---

## 🚀 **Example Conversations**

### **Example 1: Quick Signal Check**
```
User: "Analisis BTC dong!"

GPT Actions Called:
- getSignal (BTC)
- getLunarCrushCoin (BTC)
- getLunarCrushMomentum (BTC)

Response: Detailed analysis dengan 8-factor signal, 60+ social metrics, dan momentum score
```

### **Example 2: Hidden Gems Discovery**
```
User: "Cari hidden gem dengan MSS score tinggi!"

GPT Actions Called:
- scanMSS (max_fdv_usd=50000000, min_mss_score=75)
- getLunarCrushCoin (untuk top results)

Response: List of Diamond tier coins (MSS ≥80) dengan 3-phase breakdown
```

### **Example 3: Viral Detection**
```
User: "Ada yang viral hari ini ga?"

GPT Actions Called:
- discoverRealtimeGems (sort=social_volume, limit=20)
- getLunarCrushChange (untuk top movers)

Response: Viral coins dengan spike level classification
```

### **Example 4: Whale Activity**
```
User: "Whale lagi akumulasi coin apa?"

GPT Actions Called:
- scanAccumulation (min_score=7)
- getLunarCrushCoin (untuk validation)

Response: Buy-before-retail opportunities dengan whale accumulation score
```

---

## ✅ **Best Practices**

### **✅ DO:**
- Use multiple actions untuk cross-validation
- Check MSS scores for hidden gems (≥80 = Diamond!)
- Monitor Galaxy Score untuk quality (≥60 minimum)
- Watch for extreme spikes (>300% = FOMO risk!)
- Validate dengan smart money scanner

### **❌ DON'T:**
- Don't ignore distribution signals (≥7 = HIGH RISK)
- Don't chase extreme spikes (>300%)
- Don't ignore high FDV warnings
- Don't skip Galaxy Score check
- Don't enter without signal confirmation

---

**These templates maximize all 15 API actions for comprehensive crypto analysis!** 🎯💎🚀

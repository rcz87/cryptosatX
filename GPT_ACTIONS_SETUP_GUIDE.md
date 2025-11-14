# 🚀 CryptoSatX - GPT Actions Setup Guide

## Quick Start (3 Steps)

### 1️⃣ **Get Your OpenAPI Schema**

Visit your OpenAPI endpoint:
```
https://guardiansofthetoken.org/openapi.json
```

Or download directly:
```bash
curl https://guardiansofthetoken.org/openapi.json > cryptosatx-openapi.json
```

---

### 2️⃣ **Create GPT Action in ChatGPT**

1. Go to https://chat.openai.com/
2. Click your profile → **My GPTs** → **Create a GPT**
3. Go to **Configure** tab
4. Scroll to **Actions** section
5. Click **Create new action**
6. Import your OpenAPI schema

**Authentication:**
- Schema type: `API Key`
- Auth type: `Bearer Token`  
- Header name: `X-API-Key`
- API Key: Your API key (optional, currently public)

---

### 3️⃣ **Test Your GPT**

Ask natural language questions like:

```
"Give me scalping analysis for XRP"
"What's the entry for SOL right now?"
"Analyze BTC for quick scalp"
"Get real-time data for DOGE"
```

---

## 📊 Available Endpoints for GPT Actions

### **🎯 SCALPING ENDPOINTS** (Optimized for Trading)

#### 1. **Complete Scalping Analysis**
```
POST /scalping/analyze
{
  "symbol": "XRP",
  "include_smart_money": true,
  "include_fear_greed": true
}
```

**Returns:**
- 📊 Price & OHLCV
- ⚡ Orderbook Pressure
- 💣 Liquidation History
- 💰 Funding Rate
- 🧮 Long/Short Ratio
- 📈 RSI & Volume Delta
- 🐋 Smart Money Flow
- 🧊 Fear & Greed Index

**Response Time:** ~30 seconds  
**Best for:** Complete market analysis before entry

---

#### 2. **Quick Scalping Check** (Fast)
```
GET /scalping/quick/{symbol}
```

**Example:**
```
GET /scalping/quick/XRP
```

**Returns:** Critical layers only (no smart money)  
**Response Time:** ~5-8 seconds  
**Best for:** Rapid polling, quick checks

---

#### 3. **Scalping Engine Info**
```
GET /scalping/info
```

**Returns:** Available data layers and capabilities

---

### **⚡ UNIFIED RPC ENDPOINT** (192+ Operations)

Single endpoint for ALL operations:

```
POST /invoke
{
  "operation": "operation_name",
  "param1": "value1",
  "param2": "value2"
}
```

**Popular Operations:**

#### **Signals & Market Data**
```json
{"operation": "signals.get", "symbol": "BTC"}
{"operation": "market.get", "symbol": "ETH"}
```

#### **CoinGlass Data (65+ operations)**
```json
{"operation": "coinglass.liquidation.aggregated_history", "symbol": "XRP", "interval": "1h"}
{"operation": "coinglass.funding_rate.history", "exchange": "Binance", "symbol": "BTCUSDT"}
{"operation": "coinglass.long_short_ratio.position_history", "exchange": "Binance", "symbol": "SOLUSDT"}
{"operation": "coinglass.indicators.rsi", "symbol": "BTC", "period": "14"}
{"operation": "coinglass.indicators.fear_greed"}
```

#### **CoinAPI Market Data**
```json
{"operation": "coinapi.ohlcv.latest", "symbol": "XRP"}
{"operation": "coinapi.orderbook", "symbol": "SOL"}
{"operation": "coinapi.quote", "symbol": "ETH"}
```

#### **Smart Money Analysis**
```json
{"operation": "smart_money.scan", "symbol": "BTC"}
{"operation": "smart_money.analyze", "symbol": "SOL"}
```

#### **MSS (Multi-Modal Signal Score)**
```json
{"operation": "mss.discover"}
{"operation": "mss.analyze", "symbol": "PEPE"}
```

---

## 🧠 GPT Prompt Instructions

Add this to your GPT's instructions:

```
You are a crypto trading assistant powered by CryptoSatX API.

When a user asks for scalping analysis or trading signals:

1. For QUICK checks (< 10s): Use `/scalping/quick/{symbol}`
2. For COMPLETE analysis: Use `/scalping/analyze` with POST
3. For specific data: Use `/invoke` with appropriate operation

Available data:
- Price & OHLCV (real-time)
- Orderbook pressure
- Liquidations (panic signals)
- Funding rates
- Long/Short ratios
- RSI & volume delta
- Smart money flow
- Fear & Greed index

Always:
- Show critical data layers status
- Provide entry/exit recommendations when data is complete
- Explain what the metrics mean
- Give position sizing advice
- Warn about risks

For symbol normalization:
- User can say "SOL", "BTC", "XRP" (short form)
- API handles conversion automatically
- Supports 55+ major cryptocurrencies
```

---

## 📋 Example GPT Conversation Flow

**User:** "Give me scalping analysis for XRP"

**GPT:**
1. Calls `/scalping/analyze` with `symbol: "XRP"`
2. Receives all 8 data layers
3. Analyzes the data
4. Provides:
   - Current price & momentum
   - Entry zone recommendation
   - Stop loss level
   - Take profit targets
   - Position size suggestion
   - Risk assessment
   - Why this trade setup

---

## 🔧 Advanced: Custom Operations

You can combine multiple operations for deeper analysis:

```python
# Python example
import requests

BASE = "https://guardiansofthetoken.org/invoke"

# 1. Get price
price = requests.post(BASE, json={
    "operation": "coinapi.ohlcv.latest",
    "symbol": "XRP"
}).json()

# 2. Get liquidations
liq = requests.post(BASE, json={
    "operation": "coinglass.liquidation.aggregated_history",
    "symbol": "XRP",
    "exchange_list": "Binance",
    "interval": "1m"
}).json()

# 3. Get funding
funding = requests.post(BASE, json={
    "operation": "coinglass.funding_rate.history",
    "exchange": "Binance",
    "symbol": "XRPUSDT"
}).json()
```

---

## ✅ Testing Checklist

- [ ] OpenAPI schema imports successfully
- [ ] `/scalping/info` returns data
- [ ] `/scalping/quick/BTC` works
- [ ] `/scalping/analyze` POST works
- [ ] `/invoke` with various operations work
- [ ] GPT understands natural language queries
- [ ] Responses are formatted nicely

---

## 🎯 Best Practices

### For GPT Actions:

1. **Use Quick Endpoint** for rapid checks
2. **Use Full Analysis** when user asks detailed questions
3. **Cache Fear & Greed** (updates hourly)
4. **Explain Metrics** in human-friendly terms
5. **Always Warn About Risks**

### For Users:

1. **Ask Specific Questions**: "XRP scalp entry?" vs "Tell me about crypto"
2. **Mention Timeframe**: "Quick scalp" vs "swing trade"
3. **State Risk Tolerance**: "Conservative" vs "aggressive"

---

## 🚀 Production Deployment

Your API is already deployed at:
```
https://guardiansofthetoken.org
```

**OpenAPI Spec:**
```
https://guardiansofthetoken.org/openapi.json
```

**Swagger Docs:**
```
https://guardiansofthetoken.org/docs
```

---

## 📊 Rate Limits & Performance

- **Quick Endpoint:** ~5-8s response
- **Full Analysis:** ~30s response (includes smart money)
- **RPC Operations:** Varies (140ms - 25s)
- **Concurrent Requests:** Supported
- **Rate Limits:** None currently (public API)

---

## 🆘 Troubleshooting

**GPT can't access API:**
- Check OpenAPI schema imported correctly
- Verify servers field is set
- Test endpoint manually first

**Slow responses:**
- Use `/scalping/quick` instead of `/scalping/analyze`
- Set `include_smart_money: false` for faster response

**Symbol not found:**
- Check symbol spelling (BTC, ETH, SOL, XRP, etc)
- Use uppercase
- Don't include USDT suffix for most endpoints

---

## 📞 Support

For issues or questions:
- Check `/scalping/info` for capabilities
- Review `/docs` for full API documentation
- Test individual operations via `/invoke`

---

**🎉 You're Ready!**

Your GPT is now connected to real-time crypto market data.  
Start asking for scalping signals! 🚀

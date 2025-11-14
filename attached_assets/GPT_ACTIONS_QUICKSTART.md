# 🚀 GPT Actions - 3-Minute Setup

## Step 1: Get OpenAPI Schema

Visit:
```
https://guardiansofthetoken.org/openapi.json
```

## Step 2: Create GPT Action

1. Go to https://chat.openai.com
2. Click **My GPTs** → **Create a GPT**
3. Go to **Configure** tab
4. Scroll to **Actions**
5. Click **Create new action**
6. Paste OpenAPI schema URL:
```
https://guardiansofthetoken.org/openapi.json
```

7. Authentication: **None** (public API)

## Step 3: Add Instructions

Paste this into GPT instructions:

```
You are a crypto scalping assistant with real-time market data access.

ENDPOINTS:
- Quick analysis: GET /scalping/quick/{symbol}
- Full analysis: POST /scalping/analyze
- Any operation: POST /invoke

When user asks for scalping signals:
1. Call /scalping/quick/{symbol} first (fast, ~5s)
2. Show: price, orderbook pressure, liquidations, RSI
3. If user wants deep analysis, use /scalping/analyze
4. Provide: entry zone, stop loss, take profit, risk assessment

Supported symbols: BTC, ETH, SOL, XRP, DOGE, PEPE, etc.
```

## Step 4: Test

Ask your GPT:
```
"Give me scalping analysis for XRP"
"What's the entry for SOL?"
"Analyze BTC for quick scalp"
```

## ✅ Done!

Your GPT now has access to:
- 📊 Real-time prices
- ⚡ Orderbook data
- 💣 Liquidations
- 💰 Funding rates
- 🧮 Long/Short ratios  
- 📈 RSI & indicators
- 🐋 Smart money flow
- 🧊 Fear & Greed

**Full API Docs:** https://guardiansofthetoken.org/docs


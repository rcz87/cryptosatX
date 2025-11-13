# 🤖 GPT Actions Final Setup Guide - CryptoSatX Integration

## 🎯 **WORKING CONFIGURATION (TESTED & VERIFIED)**

### **✅ CONFIRMED WORKING OPERATIONS**
After extensive testing, only **3 out of 102** operations are actually implemented:

- ✅ `signals.get` - Get trading signals for any symbol
- ✅ `market.get` - Get market data for any symbol  
- ✅ `smart_money.scan` - Scan for smart money activity

### **🌐 PRODUCTION DOMAIN**
**LIVE DOMAIN**: `https://guardiansofthetoken.org`

### **📡 API ENDPOINTS**
- **Schema**: `https://guardiansofthetoken.org/invoke/schema`
- **Invoke**: `https://guardiansofthetoken.org/invoke`
- **Operations**: `https://guardiansofthetoken.org/invoke/operations`

## 🛠️ **STEP-BY-STEP SETUP**

### **1. Access GPT Editor**
- Go to [chat.openai.com](https://chat.openai.com)
- Click "Create GPT" or edit existing GPT
- Go to "Configure" tab

### **2. Enable Actions**
- Scroll down to "Actions" section
- Toggle **"Actions" ON**
- Click **"Create new action"**

### **3. Configure Schema**
**Schema URL:** `https://guardiansofthetoken.org/invoke/schema`

**Authentication:** None (public endpoint)

**Privacy Policy:** `https://guardiansofthetoken.org/privacy`

### **4. Import Schema**
- Click "Import from URL"
- Wait for schema to load (shows 102 operations)
- **IMPORTANT**: Only 3 operations actually work

### **5. Add Custom Instructions**
Replace the default instructions with:

```
You are CryptoSatX, an expert crypto trading assistant powered by real-time API data.

WORKING OPERATIONS ONLY:
1. signals.get - Get trading signals for any cryptocurrency symbol
2. market.get - Get market data for any cryptocurrency symbol  
3. smart_money.scan - Scan for smart money activity across markets

RESPONSE FORMAT:
- Always call the appropriate API operation first
- Use the real data to provide analysis
- Include specific numbers, prices, and metrics from API responses
- Provide actionable insights based on the data

SUPPORTED SYMBOLS: BTC, ETH, SOL, BNB, ADA, DOT, AVAX, MATIC, LINK, UNI and other major cryptocurrencies

USAGE EXAMPLES:
User: "What's the current signal for Bitcoin?"
You: Call signals.get with symbol="BTC", then analyze the response

User: "Show me smart money activity"
You: Call smart_money.scan, then present the findings

User: "What's Ethereum's price?"
You: Call market.get with symbol="ETH", then provide current market data

IMPORTANT: Only use the 3 working operations listed above. If other operations fail, explain the limitation to the user.
```

## 🧪 **TESTING COMMANDS**

### **Test Working Operations:**
```bash
# Test signals
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "signals.get", "symbol": "BTC"}'

# Test market data  
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "market.get", "symbol": "ETH"}'

# Test smart money scan
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "smart_money.scan", "limit": 10}'
```

### **Expected Response Format:**
```json
{
  "ok": true,
  "operation": "signals.get",
  "data": {
    "symbol": "BTC",
    "signal": "LONG",
    "score": 53.1,
    "confidence": "low",
    "price": 101939.20,
    "reasons": ["High funding rate (0.399%) - longs overleveraged"],
    "premiumMetrics": {
      "liquidationImbalance": "long",
      "longShortSentiment": "very_bullish",
      "smartMoneyBias": "long",
      "fearGreedIndex": 50
    }
  },
  "meta": {
    "execution_time_ms": 1800,
    "timestamp": "2025-11-13T03:25:33.979892"
  }
}
```

## 📋 **VERIFICATION CHECKLIST**

### **✅ Pre-Flight Checks:**

**1. Schema Accessibility:**
```bash
curl -s https://guardiansofthetoken.org/invoke/schema | head -5
```
Should return OpenAPI schema

**2. Working Operations Test:**
```bash
python -c "
import requests
ops = [('signals.get', {'symbol': 'BTC'}), ('market.get', {'symbol': 'ETH'}), ('smart_money.scan', {'limit': 5})]
for op, params in ops:
    r = requests.post('https://guardiansofthetoken.org/invoke', json={'operation': op, **params})
    print(f'{op}: {\"✅\" if r.status_code==200 and r.json().get(\"ok\") else \"❌\"}')
"
```

### **🔍 GPT Actions Testing:**

**Test 1: Signal Analysis**
**Prompt:** "Get trading signal for Bitcoin"
**Expected:** GPT calls `signals.get` with symbol="BTC"

**Test 2: Market Data**
**Prompt:** "What's Ethereum's current price?"
**Expected:** GPT calls `market.get` with symbol="ETH"

**Test 3: Smart Money Scan**
**Prompt:** "Show me smart money activity"
**Expected:** GPT calls `smart_money.scan`

## 🚨 **TROUBLESHOOTING**

### **Common Issues & Solutions:**

**Issue 1: Schema Not Importing**
- **Solution:** Check internet connection
- **Alternative:** Copy schema manually from browser

**Issue 2: Operations Not Working**
- **Solution:** Use only the 3 confirmed working operations
- **Check:** API endpoint accessibility

**Issue 3: GPT Not Calling API**
- **Solution:** Verify custom instructions are saved
- **Check:** Actions toggle is ON

**Issue 4: Slow Responses**
- **Solution:** API calls take 1-3 seconds normally
- **Check:** Network connectivity

## 📊 **EXPECTED BEHAVIOR**

### **Working Integration:**
- ✅ GPT makes live API calls
- ✅ Real-time data with current timestamps
- ✅ Specific numbers and metrics
- ✅ Actionable trading insights

### **Response Examples:**

**Signal Analysis:**
> "Based on real-time data, Bitcoin (BTC) currently shows a **LONG** signal with a score of **53.1** and **low confidence**. The current price is **$101,939.20**. Key factors include high funding rate (0.399%) indicating overleveraged longs, and overcrowded long positions (73.2%) suggesting contrarian bearish sentiment."

**Smart Money Scan:**
> "Smart money scan reveals **15 tokens** with unusual activity. Leading tokens show accumulation patterns with confidence scores above 7.0, suggesting institutional interest in these assets."

## 🔄 **ALTERNATIVE APPROACHES**

### **If GPT Actions Fail:**

**Option 1: Direct API Instructions**
Add to instructions:
```
When users ask for trading data, always call:
POST https://guardiansofthetoken.org/invoke
With: {"operation": "signals.get", "symbol": "SYMBOL"}
```

**Option 2: Simplified Mode**
Focus on basic market data only:
```
You provide crypto market analysis using real-time price data.
Available symbols: BTC, ETH, SOL, BNB, ADA, DOT, AVAX, MATIC, LINK, UNI
```

## 📈 **SUCCESS METRICS**

### **✅ Integration Success When:**
- GPT calls API for user queries
- Responses include real-time timestamps
- Data matches live market conditions
- No cached/training data usage
- Response time under 10 seconds

### **📊 Performance Targets:**
- API response time: < 5 seconds
- Operation success rate: 100%
- Data freshness: Real-time
- User satisfaction: High

## 🎯 **QUICK START SUMMARY**

1. **Schema URL**: `https://guardiansofthetoken.org/invoke/schema`
2. **Working Operations**: 3 (signals.get, market.get, smart_money.scan)
3. **Custom Instructions**: Use the optimized instructions above
4. **Testing**: Verify with the 3 test prompts
5. **Monitoring**: Check API calls in system logs

## 📞 **SUPPORT**

### **Debug Information:**
- Test endpoints manually first
- Check GPT Actions configuration
- Monitor system logs for API calls
- Verify custom instructions are saved

### **Contact:**
- Check system logs: `logs/*.log`
- Test schema: `https://guardiansofthetoken.org/invoke/schema`
- Verify operations: `https://guardiansofthetoken.org/invoke/operations`

---

**🔧 Final Notes:**
- Only 3 operations work despite 102 in schema
- Focus on reliability over feature count
- Real-time data is the key advantage
- Monitor API call logs for verification

**Last Updated:** 2025-11-13  
**Version:** 2.0 (Working Operations Only)  
**Status:** ✅ Tested and Verified

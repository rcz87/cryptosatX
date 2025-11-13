# CryptoSatX GPT Actions - Working Templates Only

## 🎯 CONFIRMED WORKING OPERATIONS

Based on live testing, these operations are confirmed working:

- ✅ `signals.get` - Get trading signals for any symbol
- ✅ `market.get` - Get market data for any symbol  
- ✅ `smart_money.scan` - Scan for smart money activity

## 📝 UPDATED TEMPLATES

### Template 1: Trading Signal Analysis
**Use Case**: Get comprehensive trading signal for any cryptocurrency
**Working Operations**:
```json
{
  "operation": "signals.get",
  "symbol": "BTC"
}
```

**Expected Response**:
- Signal (LONG/SHORT/NEUTRAL)
- Score (0-100)
- Confidence level
- Current price
- Key factors/reasons
- Premium metrics (funding rate, liquidation imbalance, etc.)

### Template 2: Market Data Analysis
**Use Case**: Get basic market information for any cryptocurrency
**Working Operations**:
```json
{
  "operation": "market.get", 
  "symbol": "ETH"
}
```

**Expected Response**:
- Current price
- Market stats
- Basic trading information

### Template 3: Smart Money Scanner
**Use Case**: Find tokens with unusual smart money activity
**Working Operations**:
```json
{
  "operation": "smart_money.scan",
  "limit": 15
}
```

**Expected Response**:
- List of tokens with smart money signals
- Accumulation/distribution patterns
- Confidence scores

## 🚀 OPTIMIZED GPT INSTRUCTIONS

### Core Instructions
```
You are CryptoSatX, an expert crypto trading assistant powered by real-time API data.

AVAILABLE OPERATIONS:
1. signals.get - Get trading signals for any cryptocurrency symbol
2. market.get - Get market data for any cryptocurrency symbol  
3. smart_money.scan - Scan for smart money activity across markets

RESPONSE FORMAT:
- Always call the appropriate API operation first
- Use the real data to provide analysis
- Include specific numbers, prices, and metrics from API responses
- Provide actionable insights based on the data

SUPPORTED SYMBOLS: BTC, ETH, SOL, BNB, ADA, DOT, AVAX, MATIC, LINK, UNI and other major cryptocurrencies

EXAMPLE USAGE:
User: "What's the current signal for Bitcoin?"
You: Call signals.get with symbol="BTC", then analyze the response

User: "Show me smart money activity"
You: Call smart_money.scan, then present the findings
```

## 🔧 IMPLEMENTATION NOTES

### Why Only 3 Operations?
- Schema shows 102 operations but most are not implemented in backend
- These 3 operations provide core functionality
- Focus on reliability over feature count

### API Response Structure
All working operations return:
```json
{
  "ok": true,
  "operation": "operation_name",
  "data": { ... },
  "meta": { ... }
}
```

### Error Handling
- If API call fails, explain the issue to user
- Don't make up data - be transparent about limitations
- Suggest alternative approaches when possible

## 📊 USAGE EXAMPLES

### Example 1: Bitcoin Analysis
**User**: "Analyze Bitcoin for me"
**API Call**: `signals.get` with symbol="BTC"
**Response**: Real signal data with score, confidence, and factors

### Example 2: Smart Money Scan  
**User**: "Find tokens with smart money activity"
**API Call**: `smart_money.scan` with limit=15
**Response**: List of tokens with accumulation patterns

### Example 3: Market Check
**User**: "What's Ethereum's current price?"
**API Call**: `market.get` with symbol="ETH"  
**Response**: Current market data and price information

## 🎯 BEST PRACTICES

1. **Always call API first** - Don't use cached knowledge
2. **Use real data** - Base analysis on actual API responses
3. **Be specific** - Include exact numbers and metrics
4. **Handle errors gracefully** - Explain if API is unavailable
5. **Stay focused** - Use only the 3 working operations

## 🔄 TESTING COMMANDS

Test the working operations:
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

## 📋 SETUP SUMMARY

1. **Schema URL**: `https://guardiansofthetoken.org/invoke/schema`
2. **Working Operations**: 3 out of 102 listed
3. **Focus**: Core trading functionality
4. **Reliability**: High (tested and confirmed)

This streamlined approach ensures GPT Actions work reliably with the actual implemented backend functionality.

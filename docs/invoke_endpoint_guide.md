# 🎯 Unified RPC Endpoint - /invoke

## 📋 COMPLETE URL
```
https://guardiansofthetoken.org/invoke
```

## 🔧 METHOD
```
POST
```

## 📊 HEADERS
```
Content-Type: application/json
```

---

## 📚 AVAILABLE OPERATIONS

### 1️⃣ SIGNAL GENERATION
```json
{
  "operation": "signals",
  "symbol": "BTC"
}
```

### 2️⃣ SMART MONEY ANALYSIS
```json
{
  "operation": "smart_money",
  "symbol": "BTCUSDT"
}
```

### 3️⃣ MSS ANALYSIS
```json
{
  "operation": "mss",
  "symbol": "PEPEUSDT",
  "include_raw": true
}
```

### 4️⃣ COINGLASS DATA
```json
{
  "operation": "coinglass",
  "symbol": "BTC",
  "data_type": "liquidations"
}
```

### 5️⃣ LUNARCRUSH DATA
```json
{
  "operation": "lunarcrush",
  "symbol": "btc"
}
```

### 6️⃣ MARKET DATA
```json
{
  "operation": "market",
  "symbol": "BTC"
}
```

---

## 🧪 TESTING EXAMPLES

### cURL
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "signals",
    "symbol": "BTC"
  }'
```

### Python
```python
import requests

response = requests.post(
    "https://guardiansofthetoken.org/invoke",
    json={
        "operation": "signals",
        "symbol": "BTC"
    }
)
print(response.json())
```

### JavaScript
```javascript
fetch('https://guardiansofthetoken.org/invoke', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    operation: 'signals',
    symbol: 'BTC'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## 🎯 CUSTOM GPT ACTIONS SETUP

### Step 1: Buka GPT Configuration
1. Masuk ke ChatGPT
2. Klik **"Explore GPTs"** → **"Create"**
3. Scroll ke **"Actions"**
4. Klik **"Create new action"**

### Step 2: Paste Schema Ini
```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "CryptoSatX Unified API",
    "version": "1.0.0",
    "description": "Unified RPC endpoint for crypto signals and analysis"
  },
  "servers": [
    {
      "url": "https://guardiansofthetoken.org"
    }
  ],
  "paths": {
    "/invoke": {
      "post": {
        "operationId": "invokeOperation",
        "summary": "Unified RPC endpoint for all crypto operations",
        "description": "Single endpoint to access signals, smart money analysis, MSS, and market data",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "operation": {
                    "type": "string",
                    "enum": [
                      "signals",
                      "smart_money",
                      "mss",
                      "coinglass",
                      "lunarcrush",
                      "market"
                    ],
                    "description": "Type of operation to perform"
                  },
                  "symbol": {
                    "type": "string",
                    "description": "Cryptocurrency symbol (e.g., BTC, ETH, BTCUSDT)"
                  },
                  "include_raw": {
                    "type": "boolean",
                    "description": "Include raw data in response (for MSS)"
                  },
                  "data_type": {
                    "type": "string",
                    "description": "Specific data type (for Coinglass)"
                  }
                },
                "required": ["operation", "symbol"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful response with operation data",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object"
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Step 3: Save & Test
1. Klik **"Test"** di GPT Actions
2. Try asking: "Get BTC signal using invoke"
3. GPT akan call endpoint dengan payload yang sesuai

---

## ✅ ADVANTAGES OF /invoke

1. **Single Endpoint** - Satu URL untuk semua operasi
2. **Flexible** - Bisa akses berbagai data sources
3. **Simple** - Request body yang konsisten
4. **GPT-Friendly** - Easy to configure di Custom GPT

---

## 📝 OPERATION PARAMETERS

| Operation | Required Fields | Optional Fields |
|-----------|----------------|-----------------|
| signals | symbol | - |
| smart_money | symbol | - |
| mss | symbol | include_raw |
| coinglass | symbol | data_type |
| lunarcrush | symbol | - |
| market | symbol | - |

---

## 🎯 EXAMPLE RESPONSES

### Signals Operation
```json
{
  "symbol": "BTC",
  "signal": "LONG",
  "score": 53.3,
  "confidence": "low",
  "price": 103078.5,
  "reasons": [...]
}
```

### Smart Money Operation
```json
{
  "success": true,
  "symbol": "BTCUSDT",
  "data": {
    "smc_score": 65,
    "market_structure": "bullish",
    ...
  }
}
```

### MSS Operation
```json
{
  "success": true,
  "symbol": "PEPEUSDT",
  "data": {
    "mss_score": 72,
    "tier": "High Potential",
    ...
  }
}
```

---

**Production URL:** https://guardiansofthetoken.org/invoke  
**Method:** POST  
**Content-Type:** application/json

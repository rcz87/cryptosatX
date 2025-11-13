# 🤖 GPT Actions Setup Guide - CryptoSatX Integration

## 🚨 **Current Issue Identified**
GPT provides accurate responses (99% match) but **no API calls are being logged** to `/invoke` endpoint. This indicates GPT Actions integration is not properly configured.

## 🔍 **Root Cause Analysis**

### **Symptoms:**
- ✅ GPT responses are highly accurate (99% match with real data)
- ❌ No API calls logged in system logs
- ❌ GPT might be using cached/training data instead of live API
- ⚠️ GPT Actions not properly configured in GPT Editor

### **Possible Causes:**
1. **GPT Actions not enabled** in GPT configuration
2. **Schema URL incorrect** in GPT Actions setup
3. **Authentication issues** with API endpoint
4. **Domain verification** problems

## 🛠️ **Step-by-Step GPT Actions Setup**

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

### **4. Verify Schema Import**
After importing schema, you should see:
- **102 operations** available
- **Flat parameters** only
- **POST /invoke** endpoint
- **No authentication required**

### **5. Test Integration**
In GPT conversation, test with:
```
"Get BTC signal using API"
```

Expected behavior:
- GPT should call `{"operation": "signals.get", "symbol": "BTC"}`
- API call should appear in system logs
- Response should include real-time data

## 🔧 **Troubleshooting Checklist**

### **✅ Pre-Flight Checks:**

**Schema Accessibility:**
```bash
curl https://guardiansofthetoken.org/invoke/schema
```
Should return OpenAPI 3.1.0 schema with 102 operations

**Endpoint Test:**
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "signals.get", "symbol": "BTC"}'
```
Should return trading signal data

### **🔍 GPT Actions Debugging:**

**1. Check Schema Import:**
- Open GPT Editor → Configure → Actions
- Verify schema shows 102 operations
- Confirm "Flat parameters" description

**2. Test Individual Operations:**
Try these specific prompts:
```
"Call signals.get for BTC"
"Use operation signals.get with symbol BTC"
"Execute smart_money.scan with limit 10"
```

**3. Monitor Logs:**
Watch system logs for API calls:
```bash
tail -f logs/*.log | grep "API Call"
```

### **🚨 Common Issues & Solutions:**

**Issue 1: Schema Not Importing**
- **Solution:** Check if schema URL is accessible
- **Alternative:** Copy schema manually from browser

**Issue 2: Operations Not Available**
- **Solution:** Verify schema format is valid OpenAPI 3.1.0
- **Check:** All operations have required parameters defined

**Issue 3: Authentication Errors**
- **Solution:** Ensure no authentication required
- **Check:** CORS headers allow GPT domain

**Issue 4: Domain Verification**
- **Solution:** Add domain to GPT allowed list
- **Check:** DNS resolution for guardiansofthetoken.org

## 📊 **Expected Behavior After Fix**

### **Before Fix (Current):**
- GPT responses accurate but no API calls
- Logs show no `/invoke` requests
- Possible cached data usage

### **After Fix (Expected):**
- GPT makes live API calls to `/invoke`
- Logs show: `"API Call: /invoke"` with operation details
- Real-time data with timestamps
- Response includes `meta.execution_time_ms`

## 🧪 **Verification Tests**

### **Test 1: Basic Signal**
**Prompt:** "Get trading signal for SOL"
**Expected API Call:** `{"operation": "signals.get", "symbol": "SOL"}`
**Log Entry:** `"API Call: /invoke"` with operation details

### **Test 2: Smart Money Scan**
**Prompt:** "Scan smart money for accumulation"
**Expected API Call:** `{"operation": "smart_money.scan", "min_accumulation_score": 7}`
**Log Entry:** Multiple API calls for comprehensive analysis

### **Test 3: Multi-Operation**
**Prompt:** "Analyze BTC: signal, liquidations, funding"
**Expected API Calls:** 
- `{"operation": "signals.get", "symbol": "BTC"}`
- `{"operation": "coinglass.liquidations.symbol", "symbol": "BTC"}`
- `{"operation": "coinglass.funding_rate.history", "symbol": "BTC"}`

## 🔄 **Alternative Solutions**

### **If GPT Actions Still Fails:**

**Option 1: Direct API Instructions**
Add explicit API call instructions:
```
Always call the API using this format:
{"operation": "signals.get", "symbol": "BTC"}
Send to: https://guardiansofthetoken.org/invoke
```

**Option 2: Function Calling Mode**
Enable function calling in GPT configuration:
- Use OpenAI function calling schema
- Map operations to function definitions
- Force API execution

**Option 3: Custom Integration**
- Create custom GPT Actions handler
- Use webhook for API calls
- Implement request logging

## 📞 **Support & Monitoring**

### **Real-time Monitoring:**
```bash
# Monitor API calls
tail -f logs/*.log | grep -E "(API Call|invoke)"

# Check GPT response patterns
grep -E "(signals\.get|smart_money\.scan|mss\.discover)" logs/*.log
```

### **Debug Information to Collect:**
1. GPT Actions configuration screenshots
2. Schema import results
3. Error messages from GPT
4. Network requests/responses
5. Browser console logs

## 🎯 **Success Criteria**

### **✅ Integration Working When:**
- GPT makes live API calls to `/invoke`
- All 102 operations available in GPT
- System logs show API call details
- Responses include real-time timestamps
- No cached/training data usage

### **📈 Performance Metrics:**
- API response time < 5 seconds
- 100% operation availability
- Zero authentication errors
- Consistent data freshness

---

**🔧 Need Help?** 
- Check system logs: `logs/*.log`
- Test schema: `https://guardiansofthetoken.org/invoke/schema`
- Verify endpoint: `https://guardiansofthetoken.org/invoke/operations`

**Last Updated:** 2025-11-13
**Version:** 1.0

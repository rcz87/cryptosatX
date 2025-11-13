# 🚨 QUICK FIX - Cloudflare Configuration (5 Minutes)

## Problem
```
Error: "Kesalahan saat berbicara dengan connector"
Cause: Cloudflare blocking https://guardiansofthetoken.org/invoke/schema
Status: HTTP 403 Access denied
```

## Solution - Copy & Paste Configuration

### 1️⃣ Login Cloudflare Dashboard
https://dash.cloudflare.com/

### 2️⃣ Navigate to WAF
```
Select: guardiansofthetoken.org
→ Security
→ WAF
→ Custom rules
→ Create rule
```

### 3️⃣ Create Rule (COPY THIS EXACTLY)

**Rule Name:**
```
Allow OpenAI GPT Actions
```

**Expression Builder:**
```
Field: User Agent
Operator: contains
Value: ChatGPT-User
```

**Action:**
```
Skip:
☑ All remaining custom rules
☑ All managed rules
☑ All rate limiting rules
```

**Alternative - Advanced Expression (More Complete):**
```
(http.user_agent contains "ChatGPT-User") or
(http.user_agent contains "GPTBot") or
(http.request.uri.path eq "/invoke/schema") or
(http.request.uri.path eq "/invoke")
```

### 4️⃣ Save & Deploy
Click **Deploy** button

---

## Verification (30 Seconds)

### Test 1: Schema Accessible
```bash
curl https://guardiansofthetoken.org/invoke/schema | jq .info.title
```
**Expected:** `"CryptoSatX Unified RPC API"`

### Test 2: Invoke Endpoint Works
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation":"health.check","args":{}}' | jq .ok
```
**Expected:** `true`

### Test 3: Signal Works
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation":"signals.get","args":{"symbol":"SOL"}}' | jq .data.signal
```
**Expected:** `"LONG"` or `"SHORT"` or `"NEUTRAL"`

---

## GPT Actions Setup (After Cloudflare Fix)

### Import Schema
1. Open ChatGPT → Settings → Actions
2. Create new action
3. **Schema URL:** `https://guardiansofthetoken.org/invoke/schema`
4. Authentication: None
5. Test: `{"operation":"signals.get","args":{"symbol":"BTC"}}`

### Test in ChatGPT
```
User: "Berikan signal untuk SOL"
```

**Expected Response:**
```
✅ GPT fetches data successfully
✅ Returns trading signal dengan score & confidence
✅ No error "Kesalahan saat berbicara dengan connector"
```

---

## Common Operations

### Get Trading Signal
```json
{"operation": "signals.get", "args": {"symbol": "SOL"}}
```

### Scan Whale Accumulation
```json
{"operation": "smart_money.scan", "args": {"min_accumulation_score": 7}}
```

### Discover High-Potential Coins
```json
{"operation": "mss.discover", "args": {"min_mss_score": 75, "max_results": 5}}
```

### Get Social Sentiment
```json
{"operation": "lunarcrush.coin", "args": {"symbol": "BTC"}}
```

### Health Check
```json
{"operation": "health.check", "args": {}}
```

---

## Checklist

- [ ] Cloudflare WAF rule created (5 min)
- [ ] curl test 1 passing (schema accessible)
- [ ] curl test 2 passing (invoke works)
- [ ] curl test 3 passing (signals work)
- [ ] Schema imported in GPT Actions
- [ ] GPT test: "Berikan signal untuk SOL" → Success!

---

## Support

📄 **Full Guide:** `GPT_ACTIONS_INVOKE_SETUP.md`
📄 **Cloudflare Details:** `GPT_ACTIONS_CLOUDFLARE_FIX.md`

**Issues?** Check Cloudflare Firewall Events log for blocked requests.

---

## Summary

✅ **Code is perfect** - RPC endpoint working correctly
❌ **Cloudflare blocking** - Need WAF configuration
⏱️ **Fix time:** 5 minutes
🎯 **Result:** 155+ operations accessible via GPT Actions

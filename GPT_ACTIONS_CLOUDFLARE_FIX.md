# GPT Actions Cloudflare Configuration Fix

## Problem
GPT Actions tidak bisa mengambil data dari API karena Cloudflare atau security layer lain memblokir request dari OpenAI.

**Error yang muncul:**
```
Kesalahan saat berbicara dengan connector
API error. Endpoint signals.get sedang tidak merespons atau format argumen ditolak
```

## Root Cause
Semua endpoint API mengembalikan `403 Access denied` ketika diakses dari luar, termasuk dari OpenAI GPT:

```bash
curl https://guardiansofthetoken.org/signals/SOL
→ Access denied (HTTP 403)

curl https://guardiansofthetoken.org/health
→ Access denied (HTTP 403)
```

## Solution

### Option 1: Cloudflare WAF Rules (RECOMMENDED)

Buat Cloudflare WAF rule untuk mengizinkan request dari OpenAI:

**Langkah-langkah:**

1. Login ke Cloudflare Dashboard
2. Pilih domain `guardiansofthetoken.org`
3. Navigate ke **Security** → **WAF** → **Custom rules**
4. Klik **Create rule**
5. Configure rule:

```
Rule name: Allow OpenAI GPT Actions
Field: User Agent
Operator: contains
Value: ChatGPT-User
Action: Skip → All remaining custom rules, All managed rules, All rate limiting rules
```

**Alternative rule for API paths:**

```
Rule name: Allow API Endpoints
Field: URI Path
Operator: starts with
Value: /signals
OR Value: /health
OR Value: /openai
OR Value: /smc
OR Value: /smart-money
OR Value: /market
Action: Skip → All remaining custom rules, All managed rules, All rate limiting rules
```

### Option 2: Cloudflare Firewall Rules

**Allow specific user agents:**

1. Go to **Security** → **WAF** → **Tools**
2. Add user agent allowlist:

```
User Agents to allow:
- ChatGPT-User
- GPTBot
- Mozilla/5.0 (compatible; ChatGPT-User/*)
```

### Option 3: API Shield Configuration

1. Go to **Security** → **API Shield**
2. Add API endpoint discovery
3. Create Schema Validation for your OpenAPI schema
4. Allow authenticated requests from verified sources

### Option 4: IP Allow List (Less Recommended)

OpenAI uses dynamic IPs, so this is not reliable. But if needed:

1. Go to **Security** → **WAF** → **Tools**
2. Add IP Access Rules
3. Check OpenAI's current IP ranges (changes frequently)

## Testing After Configuration

### Test 1: Direct API Call
```bash
curl -v https://guardiansofthetoken.org/signals/SOL
# Should return JSON signal data, not "Access denied"
```

### Test 2: Health Check
```bash
curl https://guardiansofthetoken.org/health
# Should return: {"status": "ok", ...}
```

### Test 3: With User Agent
```bash
curl -H "User-Agent: ChatGPT-User" https://guardiansofthetoken.org/signals/SOL
# Should return signal data
```

### Test 4: GPT Actions Test

Setelah Cloudflare dikonfigurasi, test di ChatGPT:
```
"Berikan saya signal untuk SOL"
```

Response yang benar akan menampilkan data signal, bukan error.

## Verification Checklist

- [ ] Cloudflare WAF rule dibuat untuk allow OpenAI user agent
- [ ] API endpoints bisa diakses dengan curl (test 1-3 passing)
- [ ] GPT Actions bisa fetch data tanpa error
- [ ] Response time < 5 detik
- [ ] Error rate < 1%

## Additional Security Recommendations

### Rate Limiting
Tetap batasi request rate untuk melindungi API:

1. **Cloudflare Rate Limiting:**
   - 100 requests per 10 seconds per IP
   - Apply to all API endpoints

2. **Application-level rate limiting:**
   - Sudah ada di FastAPI middleware (if configured)
   - Monitor dengan `/health/maximal` endpoint

### Monitoring
Monitor API access setelah membuka akses:

```python
# Check logs untuk suspicious activity
# Monitor metrics:
- Request rate per endpoint
- Error rate
- Response times
- Failed authentication attempts
```

## API Endpoints yang Perlu Diakses GPT

Pastikan endpoints berikut bisa diakses:

### Core Endpoints:
- `GET /signals/{symbol}` - Main trading signals
- `GET /health` - Health check
- `GET /health/maximal` - Full system health

### OpenAI Enhanced:
- `GET /openai/analyze/{symbol}` - GPT-4 analysis
- `GET /openai/sentiment/market` - Market sentiment

### Smart Money:
- `GET /smart-money/scan` - Whale activity
- `GET /smart-money/accumulation` - Accumulation signals
- `GET /smc/analyze/{symbol}` - SMC analysis

### Market Data:
- `GET /market/comprehensive/{symbol}` - Complete market data
- `GET /market/{symbol}` - Basic market data

### Portfolio & Risk:
- `GET /portfolio/optimize` - Portfolio optimization
- `GET /risk/assess/{symbol}` - Risk assessment
- `GET /strategies/recommend` - Trading strategies

## Alternative: Use Replit Deployment

Jika Cloudflare configuration terlalu kompleks, consider deploy di Replit:

```bash
# Replit automatically provides public URL
# No Cloudflare blocking by default
# URL format: https://[repl-name].[username].repl.co
```

Update OpenAPI schema server URL:
```json
"servers": [
    {
        "url": "https://[your-repl-url].repl.co",
        "description": "Replit Production"
    }
]
```

## Support

Jika masih ada masalah setelah konfigurasi:

1. Check Cloudflare Firewall Events log
2. Look for blocked requests dengan user agent "ChatGPT-User"
3. Check API logs untuk error patterns
4. Verify OpenAPI schema masih valid
5. Test dengan Postman sebelum test dengan GPT

## Summary

**Immediate Action Required:**
1. ✅ Configure Cloudflare WAF to allow OpenAI user agents
2. ✅ Test API endpoints dengan curl
3. ✅ Verify GPT Actions bisa fetch data
4. ✅ Monitor untuk security issues

**Konfigurasi yang PALING MUDAH dan AMAN:**
```
Cloudflare WAF Custom Rule:
- Name: Allow OpenAI GPT Actions
- Expression: (http.user_agent contains "ChatGPT-User") or (http.user_agent contains "GPTBot")
- Action: Allow
- Apply to: guardiansofthetoken.org/*
```

Setelah rule ini aktif, GPT Actions akan bisa mengakses semua endpoints tanpa error 403.

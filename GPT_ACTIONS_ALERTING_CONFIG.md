# 🚨 GPT Actions Alerting & Monitoring Configuration

## Overview

This document provides alerting thresholds and monitoring recommendations based on baseline testing results from 2025-11-15.

**Baseline Test Date:** 2025-11-15  
**Total Endpoints Tested:** 10  
**Compliance Rate:** 70% (7/10 within 50KB limit)  
**Critical Issues:** 3 endpoints exceed GPT Actions 50KB limit

---

## 🔴 Critical Issues Requiring Immediate Action

### 1. OpenAPI Schema Endpoint - 259.79 KB (5.2x over limit)

**Endpoint:** `GET /openapi.json`  
**Current Size:** 259.79 KB  
**Limit:** 50 KB  
**Overage:** 209.79 KB (419.58% over limit)

**Impact:** HIGH - GPT Actions cannot load API schema for ChatGPT integration  
**Priority:** CRITICAL  
**Recommended Action:**
- Implement schema filtering to remove internal/admin endpoints from GPT Actions schema
- Create separate `/openapi-gpt.json` endpoint with only GPT-relevant routes
- Target size: < 45 KB (90% of limit)

**Alerting Threshold:**
```
CRITICAL: openapi.json > 250 KB
WARNING: openapi.json > 200 KB
```

---

### 2. Scalping Analyze Endpoint - 111.68 KB (2.2x over limit)

**Endpoint:** `POST /scalping/analyze`  
**Current Size:** 111.68 KB  
**Limit:** 50 KB  
**Overage:** 61.68 KB (123.36% over limit)

**Impact:** HIGH - Complete scalping analysis unavailable for GPT Actions  
**Priority:** HIGH  
**Recommended Action:**
- Add `include_detailed_analysis=false` parameter for GPT mode
- Reduce data layer verbosity (remove debug info, trim arrays)
- Implement response compression for optional fields
- Target size: < 45 KB (90% of limit)

**Alerting Threshold:**
```
CRITICAL: /scalping/analyze > 100 KB
WARNING: /scalping/analyze > 80 KB
```

---

### 3. Scalping Quick Endpoint - 56.53 KB (1.1x over limit)

**Endpoint:** `GET /scalping/quick/{symbol}`  
**Current Size:** 56.53 KB  
**Limit:** 50 KB  
**Overage:** 6.53 KB (13.06% over limit)

**Impact:** MEDIUM - Quick scalping analysis marginally over limit  
**Priority:** MEDIUM  
**Recommended Action:**
- Trim orderbook history to last 5 entries (currently returning full history)
- Remove optional metadata fields from response
- Simplify whale positions data structure
- Target size: < 40 KB (80% of limit)

**Alerting Threshold:**
```
CRITICAL: /scalping/quick/* > 55 KB
WARNING: /scalping/quick/* > 45 KB
```

---

## ✅ Compliant Endpoints (Performing Well)

| Endpoint | Size | Response Time | Status |
|----------|------|---------------|--------|
| `/gpt/health` | 0.12 KB | 203ms | ✅ Excellent |
| `/gpt/signal` | 3.30 KB | 8.1s | ✅ Good |
| `/gpt/smart-money-scan` | 4.85 KB | 32.2s | ✅ Good |
| `/gpt/mss-discover` | 0.05 KB | 976ms | ✅ Excellent |
| `/invoke` (signals.get) | 0.22 KB | 870ms | ✅ Excellent |
| `/invoke` (liquidations) | 0.31 KB | 62ms | ✅ Excellent |
| `/analytics/history/latest` | 3.91 KB | 141ms | ✅ Excellent |

---

## 📊 Monitoring Thresholds & Alerting Rules

### Global Response Size Thresholds

```yaml
CRITICAL_SIZE: 50000  # 50 KB - GPT Actions hard limit
WARNING_SIZE: 40000   # 40 KB - 80% of limit (early warning)
EXCELLENT_SIZE: 30000 # 30 KB - 60% of limit (optimal)

# Health Score Calculation:
# - Compliance Rate > 95%: Health Score 95-100 (Excellent)
# - Compliance Rate 90-95%: Health Score 85-95 (Good)
# - Compliance Rate 80-90%: Health Score 70-85 (Fair)
# - Compliance Rate < 80%: Health Score < 70 (Poor)
```

### Rate Limiting Thresholds

```yaml
ACTIVE_CLIENTS_WARNING: 50     # 50 clients/min
ACTIVE_CLIENTS_CRITICAL: 100   # 100 clients/min

ENDPOINT_ABUSE_WARNING: 20     # Single endpoint hit > 20x/min by 1 IP
ENDPOINT_ABUSE_CRITICAL: 30    # Single endpoint hit > 30x/min by 1 IP

GLOBAL_LIMIT_WARNING: 150      # 75% of 200 req/min global limit
GLOBAL_LIMIT_CRITICAL: 180     # 90% of 200 req/min global limit
```

---

## 🔔 Recommended Alerting Actions

### Immediate Alerts (Critical)

**Trigger:** Any endpoint exceeds 50 KB  
**Action:**
1. Send Telegram alert to admin channel
2. Log detailed diagnostics (endpoint, size, timestamp, sample data)
3. Flag endpoint for immediate optimization

**Trigger:** Health score < 70  
**Action:**
1. Send Telegram alert with problematic endpoints list
2. Generate optimization report via `/gpt/monitoring/problematic-endpoints`

### Daily Monitoring

**Schedule:** Every day at 00:00 UTC  
**Actions:**
1. Check `/gpt/monitoring/health-check` for health score
2. Review `/gpt/monitoring/problematic-endpoints` for trends
3. Check `/gpt/monitoring/rate-limits` for abuse patterns

**Alerting Conditions:**
- Health score < 85 for 3 consecutive days → Send weekly optimization reminder
- Any endpoint exceeds limit 3 days in a row → Mark for urgent optimization
- Active clients > 50 average → Consider increasing rate limits

### Weekly Review

**Schedule:** Every Monday at 09:00 UTC  
**Actions:**
1. Generate weekly compliance report
2. Review endpoint usage patterns via `/gpt/monitoring/summary`
3. Analyze response time trends
4. Adjust rate limits based on traffic patterns

---

## 🛠️ Automated Monitoring Commands

### Check Current Health Status

```bash
# Check overall health score
curl https://guardiansofthetoken.org/gpt/monitoring/health-check | jq '.data.health_score'

# Get problematic endpoints
curl https://guardiansofthetoken.org/gpt/monitoring/problematic-endpoints | jq '.data.endpoints[]'

# Check rate limit usage
curl https://guardiansofthetoken.org/gpt/monitoring/rate-limits | jq '.data.active_clients_last_minute'
```

### Generate Reports

```bash
# Full summary for dashboard
curl https://guardiansofthetoken.org/gpt/monitoring/summary > monitoring_summary_$(date +%Y%m%d).json

# Response size statistics
curl https://guardiansofthetoken.org/gpt/monitoring/response-sizes > response_sizes_$(date +%Y%m%d).json
```

---

## 📋 Action Items & Timeline

### Immediate (This Week)
- [ ] Optimize `/openapi.json` - Create GPT-specific schema (< 45 KB)
- [ ] Add `gpt_mode=true` parameter to `/scalping/analyze` for trimmed responses
- [ ] Reduce `/scalping/quick/*` orderbook history depth

### Short-term (2 Weeks)
- [ ] Implement automated daily health score monitoring
- [ ] Set up Telegram alerts for critical threshold violations
- [ ] Create weekly compliance report automation

### Medium-term (1 Month)
- [ ] Analyze endpoint usage patterns and adjust rate limits
- [ ] Optimize any new endpoints that appear in problematic list
- [ ] Review and tune cache TTL values based on hit rates

---

## 🎯 Success Criteria

**Target Metrics:**
- Compliance Rate: > 95% (19/20 endpoints within 50KB)
- Health Score: > 90 consistently
- Average Response Size: < 25 KB across all endpoints
- No CRITICAL size violations for 7 consecutive days

**Current Status:**
- Compliance Rate: 70% (7/10) ❌
- Health Score: Estimated 75-80 (Fair) ⚠️
- Average Response Size: ~60 KB (including outliers) ❌
- CRITICAL Violations: 3 endpoints ❌

---

## 🔄 Review Schedule

**Daily:** Automated health check at 00:00 UTC  
**Weekly:** Manual review every Monday at 09:00 UTC  
**Monthly:** Comprehensive audit and optimization planning  
**Quarterly:** Rate limit adjustment and capacity planning  

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-15  
**Next Review:** 2025-11-22 (Weekly)  
**Owner:** CryptoSatX Development Team

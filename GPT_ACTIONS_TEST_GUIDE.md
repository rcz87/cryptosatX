# 🤖 GPT Actions Integration Testing Guide

## Overview

This guide covers testing the CryptoSatX API for GPT Actions compatibility, including:
- Response size validation (< 50KB requirement)
- Rate limiting verification
- Performance monitoring
- Integration health checks

---

## 🚀 Quick Start

### 1. Run the Test Suite

```bash
python3 test_gpt_actions.py
```

This comprehensive test suite will:
- ✅ Test all GPT Actions endpoints
- 📊 Validate response sizes (must be < 50KB)
- ⏱️ Measure response times
- 💾 Generate detailed JSON report

---

## 📊 Test Results Interpretation

### Success Criteria

A successful test run should show:
```
Total Tests: 10
✅ Passed: 10
❌ Failed: 0

📊 Response Size Checks:
✅ Within 50KB Limit: 10
❌ Exceeded Limit: 0
```

### Response Size Guidelines

| Size | Status | Action Required |
|------|--------|-----------------|
| < 30KB | ✅ Excellent | None |
| 30-40KB | ✅ Good | Monitor |
| 40-50KB | ⚠️ Warning | Consider optimization |
| > 50KB | ❌ Critical | **Must optimize** |

---

## 🔧 Monitoring Endpoints

### 1. Response Size Statistics

```bash
GET /gpt/monitoring/response-sizes
```

**Returns:**
- Total requests processed
- Compliance rate (% within 50KB limit)
- Per-endpoint size statistics
- Average, min, max sizes

---

### 2. Problematic Endpoints

```bash
GET /gpt/monitoring/problematic-endpoints
```

**Returns endpoints that exceed 50KB limit**

---

### 3. Rate Limit Statistics

```bash
GET /gpt/monitoring/rate-limits
```

**Returns:**
- Active clients in last minute
- Endpoint usage counts
- Configured limits

---

### 4. Integration Health Check

```bash
GET /gpt/monitoring/health-check
```

**Comprehensive health check with score and recommendations**

---

### 5. Quick Summary

```bash
GET /gpt/monitoring/summary
```

**Quick dashboard-style summary**

---

## 🛡️ Rate Limiting Configuration

### Per-Endpoint Limits

| Endpoint | Limit | Window | Notes |
|----------|-------|--------|-------|
| `/gpt/signal` | 30 req | 60s | Trading signals |
| `/gpt/smart-money-scan` | 10 req | 60s | Expensive operation |
| `/gpt/mss-discover` | 10 req | 60s | Expensive operation |
| `/gpt/health` | 60 req | 60s | Health checks |
| `/scalping/quick/*` | 20 req | 60s | Quick analysis |
| `/scalping/analyze` | 10 req | 60s | Complete analysis |
| `/invoke` | 30 req | 60s | RPC endpoint |
| `/analytics/*` | 60 req | 60s | Analytics |
| **Default** | 100 req | 60s | All other endpoints |

### Global Limit

**200 requests per minute per IP** across all endpoints (safety net)

---

## 📏 Response Size Monitoring

### Custom Headers

Every response includes size information:
```
X-Response-Size-Bytes: 12543
X-Response-Size-KB: 12.25
X-GPT-Actions-Compatible: true
X-Response-Time-Ms: 156.23
```

If response exceeds 50KB:
```
X-GPT-Actions-Compatible: false
X-GPT-Actions-Warning: Response size (65.3KB) exceeds 50KB limit
```

---

## 📈 Performance Benchmarks

### Expected Response Times

| Endpoint | Expected Time | Max Acceptable |
|----------|---------------|----------------|
| `/gpt/health` | < 50ms | 200ms |
| `/gpt/signal` | 2-5s | 10s |
| `/scalping/quick/*` | 5-8s | 15s |
| `/scalping/analyze` | 20-30s | 45s |
| `/gpt/smart-money-scan` | 15-25s | 40s |
| `/invoke` | 0.5-10s | 20s |

### Expected Response Sizes

| Endpoint | Typical Size | Max Size |
|----------|-------------|----------|
| `/gpt/health` | < 1KB | 2KB |
| `/gpt/signal` | 8-15KB | 30KB |
| `/scalping/quick/*` | 10-20KB | 35KB |
| `/scalping/analyze` | 25-45KB | **50KB** |
| `/gpt/smart-money-scan` | 15-30KB | 40KB |

---

## ✅ Pre-Production Checklist

Before enabling GPT Actions in production:

- [ ] Run full test suite (`python3 test_gpt_actions.py`)
- [ ] Verify all endpoints return < 50KB
- [ ] Test rate limiting with burst traffic
- [ ] Monitor response times under load
- [ ] Set up automated health checks
- [ ] Configure alerting for:
  - [ ] Response size violations
  - [ ] Rate limit abuse
  - [ ] Slow response times (> 30s)
  - [ ] Error rate > 5%
- [ ] Review problematic endpoints
- [ ] Implement caching for expensive operations

---

**Last Updated:** 2025-11-15  
**Version:** 3.0.0  
**Maintained by:** CryptoSatX Team

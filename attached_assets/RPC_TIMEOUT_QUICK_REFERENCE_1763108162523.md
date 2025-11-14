# ⚡ RPC Timeout - Quick Reference Card

## 🎯 What Changed

```diff
# BEFORE (No timeout protection)
async def dispatch(self, operation: str, args: Dict):
    handler = self.handlers[operation]
-   result = await handler(args)  # Could hang forever
    return RPCResponse(ok=True, data=result)

# AFTER (With timeout protection)
async def dispatch(self, operation: str, args: Dict):
    timeout = self.TIMEOUT_OVERRIDES.get(operation, 30)
+   result = await asyncio.wait_for(handler(args), timeout=timeout)
    return RPCResponse(ok=True, data=result)
```

---

## 📋 Quick Commands

### Test Timeout Working
```bash
# Should return success within 1 second
curl -X POST http://localhost:8000/rpc/flat -H "Content-Type: application/json" \
  -d '{"operation": "health.check"}'

# Should timeout after 90s (or return results)
curl -X POST http://localhost:8000/rpc/flat -H "Content-Type: application/json" \
  -d '{"operation": "mss.discover", "min_mss_score": 50, "max_results": 50}'
```

### Check Timeout Logs
```bash
# Real-time monitoring
tail -f logs/app.log | grep TIMEOUT

# Count timeout occurrences
grep "RPC TIMEOUT" logs/app.log | wc -l

# See which operations timeout most
grep "RPC TIMEOUT" logs/app.log | awk '{print $4}' | sort | uniq -c | sort -rn
```

### Environment Setup
```bash
# Quick setup
cat >> .env << EOF
RPC_OPERATION_TIMEOUT=30
AI_JUDGE_TIMEOUT=15
EOF

# Verify loaded
python -c "import os; print(f'Timeout: {os.getenv(\"RPC_OPERATION_TIMEOUT\", \"NOT SET\")}')"
```

---

## ⚙️ Configuration Matrix

| Scenario | Default Timeout | Override | When to Use |
|----------|----------------|----------|-------------|
| Development | 30s | 60s | More time for debugging |
| Production | 30s | 30s | Standard UX |
| Heavy Load | 30s | 15s | Prevent resource exhaustion |
| Batch Jobs | 30s | 180s | Long-running operations |

### Environment Variables Priority
```
Operation Specific > Environment Variable > Default (30s)
     (in code)              (.env)           (hardcoded)
```

---

## 🔍 Error Response Examples

### Timeout Error
```json
{
  "ok": false,
  "operation": "mss.discover",
  "error": "Operation timeout after 90s. Try reducing max_results parameter; Use more specific filters",
  "meta": {
    "execution_time_ms": 90123.45,
    "error_type": "TimeoutError",
    "timeout_limit_s": 90,
    "suggestions": [
      "Try reducing max_results parameter",
      "Use more specific filters to narrow the search"
    ]
  }
}
```

### Success Response
```json
{
  "ok": true,
  "operation": "signals.get",
  "data": { "symbol": "BTC", "signal": "LONG", ... },
  "meta": {
    "execution_time_ms": 1234.56,
    "timeout_limit_s": 45
  }
}
```

---

## 🎨 Custom Timeout Examples

### Example 1: Add New Operation Timeout
```python
# In rpc_dispatcher.py or rpc_flat_dispatcher.py
TIMEOUT_OVERRIDES = {
    # Existing
    "signals.get": 45,
    "mss.discover": 90,
    
    # Add your custom operation
    "custom.heavy_analysis": 120,  # 2 minutes
    "custom.quick_check": 10,       # 10 seconds
}
```

### Example 2: Dynamic Timeout Based on Parameters
```python
async def dispatch(self, request: BaseModel):
    operation = request.operation
    args = self._extract_args(request)
    
    # Calculate dynamic timeout
    if operation == "mss.scan":
        max_results = args.get("max_results", 20)
        timeout = 30 + (max_results * 2)  # 2s per result
    else:
        timeout = self.TIMEOUT_OVERRIDES.get(operation, self.DEFAULT_TIMEOUT)
    
    result = await asyncio.wait_for(
        self._execute_operation(operation, args),
        timeout=timeout
    )
```

### Example 3: Per-User Timeout (Premium Tier)
```python
async def dispatch(self, request: BaseModel, user_tier: str = "free"):
    # Premium users get 2x timeout
    base_timeout = self.TIMEOUT_OVERRIDES.get(operation, self.DEFAULT_TIMEOUT)
    
    if user_tier == "premium":
        timeout = base_timeout * 2
    else:
        timeout = base_timeout
    
    result = await asyncio.wait_for(...)
```

---

## 📊 Monitoring Queries

### Grafana/Prometheus Metrics (If Available)
```promql
# Average execution time by operation
avg(rpc_execution_time_ms) by (operation)

# Timeout rate
sum(rate(rpc_timeout_total[5m])) by (operation)

# Success rate
sum(rate(rpc_success_total[5m])) / sum(rate(rpc_total[5m]))
```

### Simple Log Analysis
```bash
# Top 10 slowest operations (not timeout)
grep "execution_time_ms" logs/app.log | \
  awk '{print $0}' | \
  jq '.meta.execution_time_ms, .operation' | \
  paste - - | \
  sort -rn | \
  head -10

# Operations timing out most
grep "TimeoutError" logs/app.log | \
  jq -r '.operation' | \
  sort | uniq -c | sort -rn

# Average execution time per operation
grep "ok.*true" logs/app.log | \
  jq -r '"\(.operation) \(.meta.execution_time_ms)"' | \
  awk '{sum[$1]+=$2; count[$1]++} END {for(op in sum) print op, sum[op]/count[op]}' | \
  sort -k2 -rn
```

---

## 🚨 Alert Thresholds

Recommended alerting rules:

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Timeout Rate | > 5% | > 10% | Investigate slow operations |
| Avg Execution | > 15s | > 25s | Optimize code or increase timeout |
| Queue Depth | > 50 | > 100 | Scale up workers |
| Memory Usage | > 70% | > 85% | Check for leaks |

---

## 🔧 Rollback Plan

If something goes wrong:

```bash
# Quick rollback (30 seconds)
cd app/core
cp rpc_dispatcher.py.backup rpc_dispatcher.py
cp rpc_flat_dispatcher.py.backup rpc_flat_dispatcher.py
systemctl restart cryptosatx  # or your restart command

# Verify rollback
curl http://localhost:8000/health
```

---

## ✅ Daily Checklist

**Morning Check** (2 minutes)
```bash
# 1. Check timeout count
grep "TIMEOUT" logs/app-$(date +%Y-%m-%d).log | wc -l

# 2. Check error rate
TOTAL=$(grep "RPC" logs/app-$(date +%Y-%m-%d).log | wc -l)
ERRORS=$(grep "ok.*false" logs/app-$(date +%Y-%m-%d).log | wc -l)
echo "Error rate: $(echo "scale=2; $ERRORS*100/$TOTAL" | bc)%"

# 3. Check slowest operation today
grep "execution_time_ms" logs/app-$(date +%Y-%m-%d).log | \
  jq -r '"\(.meta.execution_time_ms) \(.operation)"' | \
  sort -rn | head -1
```

**Action if**:
- Timeout count > 100/day: Investigate patterns
- Error rate > 5%: Check for systemic issues  
- Slowest > 25s: Consider optimization

---

## 📞 Quick Debug Commands

```bash
# Check if timeout config is loaded
curl -s http://localhost:8000/rpc/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation": "health.check"}' | \
  jq '.data.timeout_protection'
# Should output: "enabled"

# Test specific operation timeout
time curl -X POST http://localhost:8000/rpc/flat \
  -H "Content-Type: application/json" \
  -d '{"operation": "mss.discover", "max_results": 5}'
# Should complete or timeout within configured limit

# Verify environment variable
python3 << EOF
import os
from dotenv import load_dotenv
load_dotenv()
print(f"RPC_OPERATION_TIMEOUT: {os.getenv('RPC_OPERATION_TIMEOUT', 'NOT SET')}")
EOF
```

---

## 🎓 Best Practices

1. **Start Conservative** → Increase timeout only when needed
2. **Monitor First** → Watch logs for 24h before tuning
3. **Document Changes** → Note why timeout was adjusted
4. **Test Locally** → Verify timeout works before deploy
5. **Gradual Rollout** → Deploy to staging first

---

## 📚 Related Documentation

- Full Implementation Guide: `RPC_TIMEOUT_IMPLEMENTATION.md`
- Critical Improvements: `IMPROVEMENTS_CRITICAL.md`
- Environment Config: `.env.example`
- Code Changes: `app_core_rpc_*_improved.py`

---

**Created**: $(date)
**Version**: 1.0.0
**Status**: ✅ Production Ready

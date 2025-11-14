# 🚀 RPC Timeout Protection - Implementation Guide

## ✅ Apa yang Sudah Diperbaiki

### 1. **Timeout Protection** ⏱️
Semua RPC operations sekarang protected dari hanging:
- Default timeout: **30 detik**
- Operation-specific timeouts untuk operasi berat
- Graceful error handling dengan user-friendly messages

### 2. **Improved Error Logging** 📊
- Detailed error context (operation, args, error type)
- Stack trace hanya untuk unexpected errors
- Timeout logging untuk monitoring

### 3. **Better Error Messages** 💬
- Clear timeout messages dengan suggestions
- Specific guidance berdasarkan operation type
- Actionable recommendations

---

## 📦 Files yang Dibuat

```
/home/claude/
├── app_core_rpc_dispatcher_improved.py       # RPC dispatcher dengan timeout
├── app_core_rpc_flat_dispatcher_improved.py  # Flat RPC dengan timeout
├── .env.example                              # Config template
└── RPC_TIMEOUT_IMPLEMENTATION.md             # This file
```

---

## 🔧 Cara Implementasi

### Step 1: Backup File Lama
```bash
# Backup existing files
cp app/core/rpc_dispatcher.py app/core/rpc_dispatcher.py.backup
cp app/core/rpc_flat_dispatcher.py app/core/rpc_flat_dispatcher.py.backup
```

### Step 2: Replace dengan File Baru
```bash
# Copy improved versions
cp app_core_rpc_dispatcher_improved.py app/core/rpc_dispatcher.py
cp app_core_rpc_flat_dispatcher_improved.py app/core/rpc_flat_dispatcher.py
```

### Step 3: Update Environment Variables
```bash
# Add to .env file
echo "RPC_OPERATION_TIMEOUT=30" >> .env
echo "AI_JUDGE_TIMEOUT=15" >> .env
```

### Step 4: Restart Service
```bash
# Restart your FastAPI server
# Method depends on your setup (systemd, docker, pm2, etc)
```

---

## 🧪 Testing Guide

### Test 1: Normal Operation (Should Work)
```bash
curl -X POST http://localhost:8000/rpc/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "signals.get",
    "symbol": "BTC"
  }'

# Expected: Success response dalam < 30 detik
```

### Test 2: Quick Operation (Should Be Fast)
```bash
curl -X POST http://localhost:8000/rpc/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "health.check"
  }'

# Expected: Response dalam < 1 detik
```

### Test 3: Heavy Operation (Uses Custom Timeout)
```bash
curl -X POST http://localhost:8000/rpc/flat \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "mss.discover",
    "min_mss_score": 75,
    "max_results": 10
  }'

# Expected: 
# - Success dalam < 90 detik (custom timeout)
# - OR timeout error dengan suggestions
```

### Test 4: Verify Timeout Works
```bash
# Reduce timeout untuk testing
export RPC_OPERATION_TIMEOUT=5

# Trigger heavy operation
curl -X POST http://localhost:8000/rpc/flat \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "mss.discover",
    "min_mss_score": 50,
    "max_results": 50
  }'

# Expected: TimeoutError after 90s (mss.discover custom timeout)
```

---

## 📊 Timeout Configuration

### Default Timeouts
| Operation Category | Timeout (seconds) | Reason |
|-------------------|-------------------|---------|
| Default | 30 | Balance antara user experience & completion |
| Signal Generation | 45 | 16+ concurrent API calls |
| MSS Discovery | 90 | Multi-coin analysis |
| Smart Money Scan | 60 | Market-wide scanning |
| Backtest | 180 | Historical data processing |

### Mengubah Timeout

**Option 1: Environment Variable (Global)**
```bash
# .env file
RPC_OPERATION_TIMEOUT=60  # Increase untuk production
```

**Option 2: Code-level (Per Operation)**
```python
# Edit di dispatcher file
TIMEOUT_OVERRIDES = {
    "signals.get": 45,
    "mss.discover": 120,  # Increase jika perlu
    "custom.operation": 90,
}
```

---

## 🔍 Monitoring & Debugging

### Check Timeout Logs
```bash
# Grep untuk timeout errors
grep "RPC TIMEOUT" logs/app.log

# Example output:
# ⏱️  RPC TIMEOUT: mss.discover after 90s with args: {...}
```

### Check Error Distribution
```bash
# Count timeout errors
grep "TimeoutError" logs/app.log | wc -l

# Group by operation
grep "RPC TIMEOUT" logs/app.log | awk '{print $4}' | sort | uniq -c
```

### Verify Timeout Protection Working
```python
# Add this test to your test suite
import asyncio
import pytest
from app.core.rpc_dispatcher import rpc_dispatcher

@pytest.mark.asyncio
async def test_timeout_protection():
    """Test that timeout protection works"""
    
    # Create a slow operation
    async def slow_operation():
        await asyncio.sleep(60)  # Sleep 60s
        return {"data": "should timeout"}
    
    # Mock a handler to be slow
    rpc_dispatcher.handlers["test.slow"] = slow_operation
    
    # Dispatch with default timeout (30s)
    response = await rpc_dispatcher.dispatch("test.slow", {})
    
    # Should timeout and return error
    assert response.ok == False
    assert "timeout" in response.error.lower()
    assert response.meta["error_type"] == "TimeoutError"
    assert response.meta["timeout_limit_s"] == 30
```

---

## 🎯 Benefits

### Before (No Timeout)
```
User Request → RPC Handler → Slow API → ??? → User Waiting Forever
                                ↓
                            Hangs indefinitely
                            Memory leak
                            Resource exhaustion
```

### After (With Timeout)
```
User Request → RPC Handler → asyncio.wait_for(30s) → Timeout → Clear Error
                                     ↓
                               Graceful failure
                               Resource cleanup
                               User feedback
```

### Performance Impact
- ✅ No overhead for fast operations
- ✅ Prevents resource exhaustion
- ✅ Better error visibility
- ✅ Improved user experience

---

## 🐛 Troubleshooting

### Issue: "Operation timeout after 30s"
**Solution 1**: Increase timeout untuk specific operation
```python
TIMEOUT_OVERRIDES = {
    "your.operation": 60,  # Increase dari 30 ke 60
}
```

**Solution 2**: Optimize operation (better)
- Reduce API calls
- Add caching
- Use batch processing

### Issue: Timeout terlalu aggressive
**Solution**: Increase global timeout
```bash
# .env
RPC_OPERATION_TIMEOUT=60
```

### Issue: Masih ada hanging requests
**Check**:
1. Apakah file sudah ter-replace?
2. Apakah service sudah restart?
3. Apakah timeout config sudah di-load?

```python
# Verify timeout di health check
response = requests.post("http://localhost:8000/rpc/invoke", json={
    "operation": "health.check"
})
print(response.json())
# Should include: "timeout_protection": "enabled"
```

---

## 📈 Next Steps

Setelah timeout protection stable, bisa lanjut implement:

1. **Error Handling Improvements** (Next PR)
   - Service-level error tracking
   - Circuit breaker pattern
   - Automatic retry logic

2. **Performance Optimization** (Week 2)
   - MSS batch processing
   - Connection pooling
   - Response caching

3. **Monitoring Dashboard** (Nice to have)
   - Timeout rate by operation
   - Average execution time
   - Error distribution

---

## ✅ Checklist Implementation

- [ ] Backup existing files
- [ ] Copy new improved files
- [ ] Update .env with timeout configs
- [ ] Restart service
- [ ] Test health check endpoint
- [ ] Test normal operation (signals.get)
- [ ] Test heavy operation (mss.discover)
- [ ] Verify timeout errors have suggestions
- [ ] Check logs for timeout events
- [ ] Monitor for 24 hours
- [ ] Adjust timeouts if needed

---

## 🎉 Success Criteria

Implementasi berhasil jika:
- ✅ No hanging requests (all timeout dalam < 3 menit)
- ✅ Clear error messages untuk timeout
- ✅ No regression pada existing operations
- ✅ Improved user experience (feedback < 30s)
- ✅ Better observability (timeout logs)

---

## 📞 Support

Jika ada masalah:
1. Check logs: `grep "TIMEOUT" logs/app.log`
2. Verify config: Check .env file
3. Test health: `curl http://localhost/rpc/invoke -d '{"operation":"health.check"}'`
4. Rollback jika perlu: `cp *.backup app/core/`

---

**Estimated Time**: 30 menit ✅
**Complexity**: Low 🟢
**Impact**: High 🔥
**Risk**: Low (easy rollback)

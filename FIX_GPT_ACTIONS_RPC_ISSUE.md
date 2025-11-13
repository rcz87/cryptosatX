# ❌ MASALAH: Endpoint RPC `/invoke` Tidak Kompatibel dengan GPT Actions

## 🔍 ROOT CAUSE ANALYSIS

Anda menggunakan endpoint **`/invoke`** dengan format RPC yang menggunakan **nested `args`**:

```json
{
  "operation": "signals.get",
  "args": {                    ← ❌ NESTED - GPT Actions TIDAK SUPPORT!
    "symbol": "BTC"
  }
}
```

### Kenapa Error?

File: `app/api/routes_rpc.py` (line 12-13)
```python
class RPCRequest(BaseModel):
    operation: str
    args: Dict[str, Any]  # ❌ NESTED ARGS
```

**Error yang terjadi:**
```
UnrecognizedKwargsError: args
```

Sesuai dokumentasi internal Anda:
> "Format tersebut akan memicu error UnrecognizedKwargsError: args. Plugin mengharuskan setiap parameter dikirim langsung di permintaan (flat parameters), bukan di dalam objek args"

---

## ✅ SOLUSI: Gunakan Endpoint `/gpt/*` (Flat Parameters)

Repositori Anda **sudah memiliki** solusinya! Endpoint `/gpt/*` sudah menggunakan flat parameters.

File: `app/api/routes_gpt_actions.py`

```python
# ✅ FLAT PARAMETERS - GPT Actions Compatible
class GPTSignalRequest(BaseModel):
    symbol: str                    # ✅ Langsung di top level
    debug: Optional[bool] = False  # ✅ Tidak di dalam 'args'
```

---

## 📊 PERBANDINGAN LENGKAP

| Aspek | `/invoke` (RPC) ❌ | `/gpt/*` (Flat) ✅ |
|-------|-------------------|-------------------|
| **Struktur** | Nested `args` | Flat parameters |
| **Kompatibilitas GPT Actions** | ❌ TIDAK | ✅ YA |
| **Jumlah operasi** | 100+ (melebihi limit 30) | 4 core operations |
| **Error** | `UnrecognizedKwargsError: args` | ✅ Bekerja sempurna |
| **Endpoint BTC Signal** | `POST /invoke` | `POST /gpt/signal` |
| **Format Request** | `{"operation": "signals.get", "args": {"symbol": "BTC"}}` | `{"symbol": "BTC"}` |

---

## 🔄 PANDUAN MIGRASI: Dari `/invoke` ke `/gpt/*`

### 1️⃣ Trading Signal

**❌ Format RPC LAMA (TIDAK BEKERJA):**
```json
POST /invoke
{
  "operation": "signals.get",
  "args": {
    "symbol": "BTC"
  }
}
```

**✅ Format FLAT BARU (BEKERJA):**
```json
POST /gpt/signal
{
  "symbol": "BTC"
}
```

### 2️⃣ Smart Money Scan

**❌ Format RPC LAMA:**
```json
POST /invoke
{
  "operation": "smart_money.scan",
  "args": {
    "min_accumulation_score": 7
  }
}
```

**✅ Format FLAT BARU:**
```json
POST /gpt/smart-money-scan
{
  "min_accumulation_score": 7
}
```

### 3️⃣ MSS Discovery

**❌ Format RPC LAMA:**
```json
POST /invoke
{
  "operation": "mss.discover",
  "args": {
    "min_mss_score": 75,
    "max_results": 10
  }
}
```

**✅ Format FLAT BARU:**
```json
POST /gpt/mss-discover
{
  "min_mss_score": 75,
  "max_results": 10
}
```

### 4️⃣ Health Check

**❌ Format RPC LAMA:**
```json
POST /invoke
{
  "operation": "health.check",
  "args": {}
}
```

**✅ Format FLAT BARU:**
```json
GET /gpt/health
(no request body needed)
```

---

## 📝 UPDATE GPT ACTIONS - STEP BY STEP

### **Langkah 1: Hapus Schema Lama**

1. Buka GPT Builder → Actions
2. Hapus schema `/invoke` yang menggunakan nested args
3. Klik "Delete" pada action yang ada

### **Langkah 2: Import Schema Baru (Flat Parameters)**

**Option A: Upload YAML File (RECOMMENDED) ⭐**

1. Download file: `GPT_ACTIONS_FINAL_SCHEMA.yaml` dari repositori
2. Di GPT Actions editor, klik "Import from file"
3. Upload file YAML tersebut
4. GPT akan otomatis mendeteksi 4 operations:
   - `getTradingSignal`
   - `scanSmartMoney`
   - `discoverHighPotentialCoins`
   - `checkHealth`
5. Klik "Save"

**Option B: Import dari URL**

1. URL: `https://guardiansofthetoken.org/openapi.json`
2. **SANGAT PENTING:** Filter dan pilih **HANYA** endpoint `/gpt/*`:
   - ✅ `POST /gpt/signal`
   - ✅ `POST /gpt/smart-money-scan`
   - ✅ `POST /gpt/mss-discover`
   - ✅ `GET /gpt/health`
3. ❌ **JANGAN pilih:**
   - ❌ `/invoke` endpoint (nested args)
   - ❌ Endpoint lain selain `/gpt/*`
4. Total operations: **4 saja** (jauh di bawah limit 30)

### **Langkah 3: Update GPT Instructions**

Ganti instruksi GPT Anda dengan ini:

```markdown
You are CryptoSatX, cryptocurrency trading assistant powered by real-time market data.

## 🎯 AVAILABLE OPERATIONS (4 operations)

### 1. getTradingSignal
Get LONG/SHORT/NEUTRAL trading signal for cryptocurrency.

**Parameters (FLAT - NO nested args!):**
```json
{
  "symbol": "BTC"
}
```

**Response includes:**
- signal: LONG/SHORT/NEUTRAL
- score: 0-100 (composite score)
- confidence: high/medium/low
- price: current price in USD
- reasons: top 3 factors

**Example usage:**
User: "Analisa BTC"
GPT calls: getTradingSignal({"symbol": "BTC"})

### 2. scanSmartMoney
Detect whale accumulation/distribution patterns.

**Parameters:**
```json
{
  "min_accumulation_score": 7
}
```

**Example usage:**
User: "Cari coins dengan akumulasi whale"
GPT calls: scanSmartMoney({"min_accumulation_score": 7})

### 3. discoverHighPotentialCoins
Find emerging cryptocurrencies using MSS (Multi-Modal Signal Score).

**Parameters:**
```json
{
  "min_mss_score": 75,
  "max_results": 10
}
```

**Example usage:**
User: "Cari hidden gems"
GPT calls: discoverHighPotentialCoins({"min_mss_score": 75, "max_results": 10})

### 4. checkHealth
Verify API operational status.

**Parameters:** None (GET request)

## ⚠️ CRITICAL: Use FLAT Parameters Only!

❌ **WRONG (will cause error):**
```json
{
  "operation": "signals.get",
  "args": {
    "symbol": "BTC"
  }
}
```

✅ **CORRECT:**
```json
{
  "symbol": "BTC"
}
```

## 📋 RESPONSE FORMAT

Always respond in Bahasa Indonesia if user uses Indonesian.

**Example Response Template:**

User: "Analisa SOL"

GPT Response:
"Berdasarkan analisis real-time SOL:

**Sinyal:** LONG 📈
**Score:** 52.3/100
**Confidence:** Medium
**Harga:** $155.32

**Faktor Utama:**
1. Funding rate positif (bullish sentiment)
2. Open Interest meningkat (institutional interest)
3. Social sentiment kuat (Galaxy Score: 72/100)

⚠️ **Disclaimer:** Ini bukan nasihat keuangan. Lakukan riset sendiri (DYOR) sebelum trading."

## 🔄 ERROR HANDLING

If action fails:
1. Call checkHealth() to verify API status
2. Try alternative symbol format (e.g., "BTC" not "BITCOIN")
3. Inform user: "API sedang memproses, coba beberapa saat lagi"

## 🌐 MULTI-LANGUAGE SUPPORT

- Indonesian queries → Respond in Indonesian
- English queries → Respond in English
- Always include disclaimer in appropriate language
```

---

## 🧪 TESTING CHECKLIST

Setelah migrasi, test dengan prompts berikut:

### Test 1: Trading Signal ✅
**Prompt:** "Analisa BTC"

**Expected:**
- GPT calls `getTradingSignal` dengan `{"symbol": "BTC"}`
- Response dalam Bahasa Indonesia
- Menampilkan: signal, score, confidence, price, factors
- ❌ TIDAK ada error `UnrecognizedKwargsError`

### Test 2: Multiple Coins ✅
**Prompt:** "Compare BTC, ETH, and SOL"

**Expected:**
- GPT calls `getTradingSignal` 3 kali (satu per symbol)
- Menampilkan comparison table
- Semua requests menggunakan flat parameters

### Test 3: Smart Money ✅
**Prompt:** "Cari coins dengan akumulasi whale tinggi"

**Expected:**
- GPT calls `scanSmartMoney` dengan `{"min_accumulation_score": 7}`
- Returns list of coins with institutional buying
- Format flat parameters (tidak nested)

### Test 4: Health Check ✅
**Prompt:** "Is the API working?"

**Expected:**
- GPT calls `checkHealth` (GET, no body)
- Returns: "healthy - CryptoSatX API is operational"

---

## 📊 VERIFICATION

Setelah setup, verify bahwa:

- [ ] Schema imported successfully (4 operations visible)
- [ ] Test prompt "Analisa BTC" returns real data
- [ ] Response includes actual current price
- [ ] ❌ NO `UnrecognizedKwargsError: args` errors
- [ ] Indonesian responses working correctly
- [ ] Disclaimer included in all trading recommendations
- [ ] Multiple coin comparison working
- [ ] All requests use flat parameters (not nested args)

---

## 🎯 SUMMARY

| Item | Status | Note |
|------|--------|------|
| **Problem** | ✅ Identified | RPC `/invoke` uses nested `args` |
| **Root Cause** | ✅ Identified | GPT Actions doesn't support nested params |
| **Solution** | ✅ Available | Use `/gpt/*` endpoints with flat params |
| **Implementation** | ✅ Ready | Endpoints already exist in codebase |
| **Migration** | 🟡 Pending | Need to update GPT Actions schema |
| **Testing** | 🟡 Pending | Test after migration |

---

## 🚀 EXPECTED OUTCOME

Setelah migrasi dari `/invoke` ke `/gpt/*`:

✅ **BEFORE (RPC - BROKEN):**
```
User: "Analisa BTC"
GPT calls: POST /invoke
Body: {"operation": "signals.get", "args": {"symbol": "BTC"}}
Result: ❌ UnrecognizedKwargsError: args
```

✅ **AFTER (FLAT - WORKING):**
```
User: "Analisa BTC"
GPT calls: POST /gpt/signal
Body: {"symbol": "BTC"}
Result: ✅ {"ok": true, "data": {"signal": "LONG", "score": 53.1, ...}}
```

---

## 📞 SUPPORT

Jika masih ada masalah setelah migrasi:

1. **Verify schema:**
   ```bash
   curl https://guardiansofthetoken.org/openapi.json | grep "/gpt/"
   ```

2. **Test endpoint manually:**
   ```bash
   curl -X POST "https://guardiansofthetoken.org/gpt/signal" \
     -H "Content-Type: application/json" \
     -d '{"symbol": "BTC"}'
   ```

3. **Check GPT Actions logs** untuk error details

4. **Verify** bahwa GPT Actions schema hanya menggunakan 4 operations dari `/gpt/*` path

---

## ✅ CONCLUSION

**Problem:** Anda menggunakan `/invoke` endpoint yang tidak kompatibel dengan GPT Actions karena menggunakan nested `args` parameter.

**Solution:** Gunakan endpoint `/gpt/*` yang sudah tersedia di repositori dengan flat parameters.

**Next Steps:**
1. ✅ Update GPT Actions schema (import `GPT_ACTIONS_FINAL_SCHEMA.yaml`)
2. ✅ Update GPT instructions (gunakan template di atas)
3. ✅ Test dengan prompt "Analisa BTC"
4. ✅ Verify tidak ada error `UnrecognizedKwargsError`

**Timeline:** 5-10 menit untuk complete migration

**Impact:** GPT Actions akan bekerja 100% tanpa error! 🎉

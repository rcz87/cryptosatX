# 🔧 Cloudflare Fix - Step by Step Guide

## Problem

GPT Actions tidak bisa access API kamu karena Cloudflare memblokir semua request dengan error **403 Forbidden "Access denied"**.

**Error yang muncul di ChatGPT:**
```
Kesalahan saat berbicara dengan connector
API error. Endpoint signals.get sedang tidak merespons
```

## Solution: Configure Cloudflare WAF (5 Minutes)

---

## 📋 Step-by-Step Instructions

### Step 1: Login ke Cloudflare Dashboard

1. Buka browser, pergi ke: **https://dash.cloudflare.com/**
2. Login dengan akun Cloudflare kamu
3. Kamu akan melihat list domain yang kamu manage

### Step 2: Pilih Domain

1. Cari dan klik domain: **`guardiansofthetoken.org`**
2. Tunggu dashboard domain terbuka

### Step 3: Navigate ke WAF

Di sidebar kiri, ikuti urutan ini:

```
1. Klik "Security" (ikon shield 🛡️)
   ↓
2. Klik "WAF" (Web Application Firewall)
   ↓
3. Klik tab "Custom rules"
```

Kamu akan melihat halaman dengan list custom rules (mungkin kosong jika belum ada rules).

### Step 4: Create New Rule

1. Klik tombol **"Create rule"** (biasanya di kanan atas)
2. Form "Create custom rule" akan muncul

### Step 5: Configure Rule

Isi form dengan konfigurasi berikut:

#### **Rule name:**
```
Allow OpenAI GPT Actions
```

#### **Field Configuration:**

**Pilih expression builder** (bukan "Edit expression" mode):

1. **First dropdown:** Pilih `User Agent`
2. **Second dropdown (Operator):** Pilih `contains`
3. **Text field (Value):** Ketik `ChatGPT-User`

Akan terlihat seperti ini:
```
User Agent | contains | ChatGPT-User
```

#### **Action:**

1. **Choose action dropdown:** Pilih `Skip`
2. **Checkboxes yang muncul:** Centang SEMUA:
   - ☑ Skip all remaining custom rules
   - ☑ Skip all managed rules
   - ☑ Skip all rate limiting rules

**PENTING:** Centang SEMUA checkbox agar rule bekerja dengan benar!

### Step 6: Deploy Rule

1. Scroll ke bawah
2. Klik tombol **"Deploy"** (biru, di kanan bawah)
3. Tunggu beberapa detik, akan muncul notifikasi "Rule created successfully"

---

## ✅ Verification - Test API (WAJIB!)

Setelah rule di-deploy, tunggu **1-2 menit** untuk propagation, lalu test:

### Test 1: Invoke Schema
```bash
curl -s https://guardiansofthetoken.org/invoke/schema | jq .info.title
```

**Expected output:**
```
"CryptoSatX Unified RPC API"
```

**Jika masih "Access denied":**
- Tunggu 2-3 menit lagi (Cloudflare cache)
- Clear Cloudflare cache (lihat troubleshooting di bawah)

### Test 2: Health Check
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation":"health.check","args":{}}'
```

**Expected output:**
```json
{
  "ok": true,
  "operation": "health.check",
  "data": {
    "status": "healthy",
    ...
  }
}
```

### Test 3: Signal Endpoint
```bash
curl -X POST https://guardiansofthetoken.org/invoke \
  -H "Content-Type: application/json" \
  -d '{"operation":"signals.get","args":{"symbol":"BTC"}}'
```

**Expected:** JSON response dengan signal data (bukan "Access denied")

---

## 🎯 Alternative Configuration (Jika Yang Pertama Tidak Cukup)

Jika masih ada masalah, gunakan **Advanced Expression**:

### Step 1-4: Sama seperti di atas

### Step 5 (Alternative): Use Advanced Expression

1. Klik **"Edit expression"** (toggle dari "Field" mode)
2. Di text box besar, paste expression ini:

```
(http.user_agent contains "ChatGPT-User") or
(http.user_agent contains "GPTBot") or
(http.user_agent contains "Mozilla/5.0") or
(http.request.uri.path eq "/invoke/schema") or
(http.request.uri.path eq "/invoke") or
(http.request.uri.path starts_with "/signals") or
(http.request.uri.path starts_with "/coinglass") or
(http.request.uri.path starts_with "/lunarcrush") or
(http.request.uri.path starts_with "/coinapi")
```

3. **Action:** Skip (centang semua checkbox)
4. **Deploy**

---

## 🔍 Troubleshooting

### Problem 1: Masih "Access denied" setelah 5 menit

**Solution: Clear Cloudflare Cache**

1. Di Cloudflare dashboard, pilih domain kamu
2. Sidebar kiri → **"Caching"** → **"Configuration"**
3. Scroll ke **"Purge Cache"**
4. Klik **"Purge Everything"**
5. Confirm
6. Tunggu 1-2 menit
7. Test lagi dengan curl

### Problem 2: Rule tidak muncul di list

**Solution:**
1. Refresh halaman Cloudflare
2. Check di **Security** → **WAF** → **Custom rules**
3. Pastikan rule "Allow OpenAI GPT Actions" ada di list
4. Pastikan status rule **"Enabled"** (ada toggle switch yang ON)

### Problem 3: Rule ada tapi masih blocked

**Solution: Check Rule Priority**
1. Di list custom rules, pastikan rule "Allow OpenAI GPT Actions" ada di **posisi ATAS**
2. Jika ada rule lain yang lebih restrictive di atas, drag rule kamu ke paling atas
3. Klik **"Save"** jika ada perubahan order

### Problem 4: Test curl berhasil, tapi GPT masih error

**Solution: Re-import Schema di GPT Actions**
1. Buka ChatGPT → Settings → Actions
2. Hapus action lama (jika ada)
3. Create new action
4. Import schema URL: `https://guardiansofthetoken.org/invoke/schema`
5. Test dengan: `{"operation":"health.check","args":{}}`

---

## 📊 Check Cloudflare Firewall Events (Optional)

Untuk verify rule bekerja:

1. Cloudflare dashboard → domain kamu
2. Sidebar kiri → **"Security"** → **"Events"**
3. Kamu akan melihat log requests yang di-allow/block
4. Filter by:
   - **Service:** WAF
   - **Action:** Skip
5. Kamu harus melihat requests dari OpenAI dengan action "Skip" (artinya di-allow)

---

## 🎓 Visual Guide (Description)

### Dashboard Layout:
```
┌─────────────────────────────────────────────────┐
│ Cloudflare Dashboard                            │
│                                                 │
│ [Sidebar]              [Main Content]          │
│ ┌──────────┐          ┌───────────────────┐    │
│ │ Home     │          │ Domain Overview   │    │
│ │ Analytics│          │                   │    │
│ │ DNS      │          │                   │    │
│ │ ► Security│         │                   │    │
│ │   ├─ WAF  │ ◄────   │                   │    │
│ │   ├─ Firewall       │                   │    │
│ │   └─ Events         │                   │    │
│ │ Caching  │          │                   │    │
│ └──────────┘          └───────────────────┘    │
└─────────────────────────────────────────────────┘
```

### WAF Custom Rules Page:
```
┌─────────────────────────────────────────────────┐
│ Custom rules                    [Create rule]   │
├─────────────────────────────────────────────────┤
│                                                 │
│ ✓ Allow OpenAI GPT Actions        [Enabled]    │
│   User Agent contains "ChatGPT-User"            │
│   Action: Skip                                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Create Rule Form:
```
┌─────────────────────────────────────────────────┐
│ Create custom rule                              │
├─────────────────────────────────────────────────┤
│ Rule name:                                      │
│ [Allow OpenAI GPT Actions              ]        │
│                                                 │
│ If incoming requests match:                     │
│ [User Agent ▼] [contains ▼] [ChatGPT-User   ]  │
│                                                 │
│ Then take action:                               │
│ [Skip ▼]                                        │
│   ☑ Skip all remaining custom rules             │
│   ☑ Skip all managed rules                      │
│   ☑ Skip all rate limiting rules                │
│                                                 │
│                              [Cancel] [Deploy]  │
└─────────────────────────────────────────────────┘
```

---

## 🚦 Success Indicators

Setelah fix berhasil, ini yang akan terjadi:

### ✅ Test dengan curl:
```bash
$ curl https://guardiansofthetoken.org/invoke/schema
# Returns: JSON schema (tidak "Access denied")
```

### ✅ Test di GPT:
```
User: "Berikan signal untuk BTC"
GPT: [Fetches data successfully]
     📊 Signal untuk BTC:
     🟢 LONG (Confidence: HIGH)
     Score: 78.5/100
     ...
```

### ✅ No more errors:
- ❌ "Kesalahan saat berbicara dengan connector" → HILANG
- ❌ "API error" → HILANG
- ❌ "403 Access denied" → HILANG

---

## 📝 Quick Reference Card

Print atau save ini untuk reference cepat:

```
═══════════════════════════════════════════════════
  CLOUDFLARE WAF FIX - QUICK REFERENCE
═══════════════════════════════════════════════════

1. Login: dash.cloudflare.com
2. Select: guardiansofthetoken.org
3. Navigate: Security → WAF → Custom rules
4. Click: Create rule
5. Configure:
   Name: Allow OpenAI GPT Actions
   Field: User Agent | contains | ChatGPT-User
   Action: Skip (centang SEMUA checkbox)
6. Click: Deploy
7. Wait: 1-2 minutes
8. Test: curl https://guardiansofthetoken.org/invoke/schema

═══════════════════════════════════════════════════
If still blocked:
  - Clear Cloudflare cache
  - Wait 2-3 minutes
  - Use Advanced Expression (see full guide)
═══════════════════════════════════════════════════
```

---

## ⏰ Estimated Time

- **Reading guide:** 5 minutes
- **Cloudflare configuration:** 3 minutes
- **Testing & verification:** 2 minutes
- **Total:** ~10 minutes

---

## 🆘 Still Need Help?

### Check These Common Mistakes:

1. ❌ **Forgot to check ALL 3 skip boxes**
   - Must check: remaining custom rules, managed rules, rate limiting rules

2. ❌ **Typo in User Agent value**
   - Must be exactly: `ChatGPT-User` (case-sensitive)

3. ❌ **Rule disabled**
   - Check toggle switch is ON in rules list

4. ❌ **Wrong domain**
   - Make sure you're configuring `guardiansofthetoken.org` not another domain

5. ❌ **Didn't wait for propagation**
   - Wait at least 1-2 minutes after deploying rule

### Debug Steps:

1. Check rule exists:
   ```
   Security → WAF → Custom rules
   → "Allow OpenAI GPT Actions" should be in list
   ```

2. Check rule is enabled:
   ```
   Toggle switch should be ON (blue)
   ```

3. Check Cloudflare logs:
   ```
   Security → Events
   → Filter by action "Skip"
   → Should see OpenAI requests being allowed
   ```

4. Clear cache:
   ```
   Caching → Configuration → Purge Everything
   ```

5. Test with curl (see Test 1-3 above)

---

## 🎯 Expected Results After Fix

### Before Fix (Current State):
```bash
$ curl https://guardiansofthetoken.org/invoke/schema
Access denied

$ # GPT Actions: Error - Cannot connect
```

### After Fix (Success):
```bash
$ curl https://guardiansofthetoken.org/invoke/schema
{
  "openapi": "3.1.0",
  "info": {
    "title": "CryptoSatX Unified RPC API",
    "version": "3.0.0"
  },
  ...
}

$ # GPT Actions: ✅ Working perfectly
```

---

## 📚 Related Documentation

After Cloudflare fix selesai, baca ini untuk setup GPT Actions:

1. **`GPT_ACTIONS_INVOKE_SETUP.md`**
   - Complete GPT Actions configuration
   - Custom instructions
   - Testing procedures

2. **`COINGLASS_ENDPOINTS_STATUS.md`**
   - All 68 Coinglass endpoints
   - Usage examples

3. **`LUNARCRUSH_COINAPI_STATUS.md`**
   - LunarCrush & CoinAPI integration
   - Combined signal strategies

---

## 🚀 Next Steps After Fix

1. ✅ Verify dengan curl (Test 1-3)
2. ✅ Import schema ke GPT Actions
3. ✅ Add GPT custom instructions
4. ✅ Test dengan real queries
5. ✅ Monitor Cloudflare Events log
6. ✅ Enjoy 155+ operations via GPT! 🎉

---

**Good luck! Jika masih ada masalah setelah ikuti step-by-step ini, screenshot error yang muncul dan share untuk debugging lebih lanjut.**

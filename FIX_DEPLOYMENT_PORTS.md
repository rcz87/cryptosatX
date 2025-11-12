# 🔧 FIX DEPLOYMENT ERROR - Port Configuration

## ❌ Current Problem:

File `.replit` punya **4 port mappings**, tapi VM deployment **hanya bisa expose 1 port**:

```toml
[[ports]]
localPort = 3000
externalPort = 3000   ❌ HAPUS INI

[[ports]]
localPort = 5432
externalPort = 5432   ❌ HAPUS INI

[[ports]]
localPort = 6379
externalPort = 6379   ❌ HAPUS INI

[[ports]]
localPort = 8000
externalPort = 80     ✅ KEEP THIS ONLY
```

## ✅ SOLUSI - Edit File `.replit` Manual:

### Step 1: Buka file `.replit` di Replit Editor

### Step 2: Cari section `[[ports]]` (ada 4 sections)

### Step 3: HAPUS atau COMMENT OUT 3 port pertama:

**BEFORE (WRONG):**
```toml
[[ports]]
localPort = 3000
externalPort = 3000

[[ports]]
localPort = 5432
externalPort = 5432

[[ports]]
localPort = 6379
externalPort = 6379

[[ports]]
localPort = 8000
externalPort = 80
```

**AFTER (CORRECT):**
```toml
# Commented out for VM deployment - only 1 external port allowed
# [[ports]]
# localPort = 3000
# externalPort = 3000

# [[ports]]
# localPort = 5432
# externalPort = 5432

# [[ports]]
# localPort = 6379
# externalPort = 6379

[[ports]]
localPort = 8000
externalPort = 80
```

**ATAU lebih simple, ganti semua [[ports]] section dengan:**
```toml
[[ports]]
localPort = 8000
externalPort = 80
```

### Step 4: Save file `.replit`

### Step 5: Deploy lagi

Click tombol **Deploy** di Replit, deployment seharusnya sukses sekarang!

---

## 🔍 Penjelasan:

- **VM Deployment** hanya bisa expose **1 external port**
- Port 8000 (internal) akan di-forward ke port 80 (external/public)
- Port 80 adalah standard HTTP port untuk production
- Ports lain (3000, 5432, 6379) tetap tersedia secara internal tapi tidak exposed keluar

---

## ✅ Verification Setelah Deploy:

```bash
curl -s "https://guardiansofthetoken.org/signals/BTC" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Premium Available:', d.get('premiumDataAvailable'))
print('Status: SUCCESS' if d.get('premiumDataAvailable') == True else 'Status: FAILED - Need redeploy')
"
```


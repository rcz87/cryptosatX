# 🔄 PANDUAN PULL PERUBAHAN DI REPLIT SHELL

## 📋 LANGKAH-LANGKAH LENGKAP

### 1. **Buka Replit Shell**
- Di Replit, klik tab **Shell** di bagian bawah
- Atau gunakan shortcut `Ctrl + ` ` (backtick)

### 2. **Navigate ke Project Directory**
```bash
# Biasanya sudah di root directory, tapi pastikan:
pwd
# Jika perlu navigate:
cd /home/runner/cryptosatX
```

### 3. **Check Current Status**
```bash
# Cek status git saat ini
git status

# Cek branch saat ini
git branch

# Cek commit terakhir
git log --oneline -n 3
```

### 4. **Stash Local Changes (Jika Ada)**
```bash
# Jika ada perubahan lokal yang belum commit
git stash

# Atau commit dulu perubahan lokal
git add .
git commit -m "Local changes before pull"
```

### 5. **Pull Latest Changes**
```bash
# Pull dari remote main branch
git pull origin main

# Atau jika ingin lebih spesifik
git fetch origin
git merge origin/main
```

### 6. **Resolve Conflicts (Jika Ada)**
```bash
# Jika ada conflicts, cek file yang conflict:
git status

# Edit file yang conflict dan resolve manually
# Setelah resolved:
git add .
git commit -m "Resolved merge conflicts"
```

### 7. **Verify Changes**
```bash
# Cek apakah perubahan sudah masuk
git log --oneline -n 5

# Verifikasi file yang diubah
git show --name-only HEAD

# Cek apakah file signal_engine.py sudah update
cat app/core/signal_engine.py | head -20
```

## 🚀 **QUICK COMMANDS (Copy-Paste)**

### **Option 1: Simple Pull**
```bash
git pull origin main
```

### **Option 2: Safe Pull (Recommended)**
```bash
git stash
git pull origin main
git stash pop
```

### **Option 3: Force Pull (Clean Slate)**
```bash
git fetch origin
git reset --hard origin/main
```

## 🔍 **VERIFICATION STEPS**

Setelah pull, verifikasi perubahan:

```bash
# 1. Cek commit terbaru
git log --oneline -n 1

# 2. Verifikasi file signal_engine.py
grep -n "WEIGHTS = {" app/core/signal_engine.py

# 3. Cek threshold changes
grep -n "score >= 52" app/core/signal_engine.py

# 4. Test signal engine
python test_signal_improvements.py
```

## ⚠️ **TROUBLESHOOTING**

### **Jika Error: "Permission Denied"**
```bash
# Check git remote
git remote -v

# Re-add remote dengan credentials
git remote set-url origin https://username:token@github.com/rcz87/cryptosatX.git
```

### **Jika Error: "Merge Conflicts"**
```bash
# Lihat file yang conflict
git status

# Edit file tersebut, cari tanda:
# <<<<<<< HEAD
# ======= 
# >>>>>>> main

# Hapus conflict markers dan pilih versi yang diinginkan
# Kemudian:
git add .
git commit -m "Resolved conflicts"
```

### **Jika Error: "Detected Divergent Branch"**
```bash
# Force pull (hati-hati - akan overwrite local changes)
git fetch origin
git reset --hard origin/main
```

## 📱 **EXPECTED OUTPUT**

Setelah berhasil pull, seharusnya melihat:

```
From https://github.com/rcz87/cryptosatX.git
 * branch            main     -> FETCH_HEAD
   efad651..5fd963b  main     -> origin/main
Updating efad651..5fd963b
Fast-forward
 app/core/signal_engine.py              | 183 +++++++++++++---------
 GPT_NEUTRALITY_FIX_DOCUMENTATION.md    | 150 +++++++++++++++++
 test_signal_improvements.py             |  89 +++++++++++
 3 files changed, 597 insertions(+), 183 deletions(-)
 create mode 100644 GPT_NEUTRALITY_FIX_DOCUMENTATION.md
 create mode 100644 test_signal_improvements.py
```

## ✅ **SUCCESS INDICATORS**

1. **Commit ID:** `5fd963b` harus muncul di `git log`
2. **File Changes:** 3 files changed, 597 insertions
3. **New Files:** `GPT_NEUTRALITY_FIX_DOCUMENTATION.md` dan `test_signal_improvements.py`
4. **Signal Engine:** Weight system harus terupdate

## 🎯 **FINAL VERIFICATION**

```bash
# Test the improvements
python test_signal_improvements.py

# Expected output should show:
# Signal: LONG/SHORT (bukan NEUTRAL)
# Score: >52 atau <48
# 🚀 BULLISH/📉 BEARISH signals
```

---

**Status:** 🔄 **READY FOR REPLIT DEPLOYMENT**
**Next Steps:** Pull changes di Replit dan test signal improvements

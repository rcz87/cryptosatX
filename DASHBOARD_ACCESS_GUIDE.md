# 🎯 Panduan Akses Dashboard CryptoSatX

## ❌ MASALAH: Dashboard Hanya Menampilkan API Schema / Code

Jika dashboard Anda hanya menampilkan:
- JSON API schema
- FastAPI documentation page
- Code editor Replit

**Anda sedang mengakses URL yang SALAH!**

---

## ✅ SOLUSI: Cara Akses Dashboard yang Benar

### Langkah 1: Jalankan Aplikasi
1. Di Replit, klik tombol **Run** (▶️) di bagian atas
2. Tunggu hingga muncul log: `🚀 CryptoSatX - Enhanced Crypto Signal API Starting...`
3. Pastikan tidak ada error di console

### Langkah 2: Akses URL yang Benar

#### ✅ BENAR - Akses Salah Satu URL Ini:
```
https://[your-replit-url].replit.dev/
```
ATAU
```
https://[your-replit-url].replit.dev/dashboard
```

#### ❌ SALAH - JANGAN Akses URL Ini:
```
❌ https://[your-replit-url].replit.dev/docs
❌ https://[your-replit-url].replit.dev/redoc
❌ https://[your-replit-url].replit.dev/openapi.json
❌ https://[your-replit-url].replit.dev/openapi-gpt.json
```

---

## 🎨 Dashboard yang Benar Harus Menampilkan:

### 1. **Stat Cards** (4 kartu di bagian atas)
- 📊 Total Signals
- 🏆 AI Win Rate
- ⚡ Active Signals
- 💰 Avg P&L (24h)

### 2. **Scan & Monitor Section**
- 🔍 Bulk Scanner (input untuk scan multiple coins)
- 👁️ Monitor List (daftar coins yang di-monitor)

### 3. **Latest Signals**
- List 10 signal terakhir dengan:
  - Symbol (BTC, ETH, dll)
  - Signal type (LONG/SHORT)
  - AI Verdict (CONFIRM/SKIP/DOWNSIZE)
  - 24h P&L
  - Outcome (WIN/LOSS/PENDING)

### 4. **Charts** (3 grafik)
- 🧠 AI Verdict Performance (bar chart)
- 🥧 Signal Distribution (doughnut chart)
- ⏰ Performance Timeline (line chart)

### 5. **Quick Signal Generator**
- Input untuk generate signal single coin
- Quick buttons: BTC, ETH, SOL, AVAX, MATIC, LINK

### 6. **TradingView Charts**
- Market Overview ticker tape
- BTC/USDT chart
- ETH/USDT chart

---

## 🔧 Troubleshooting

### Jika Dashboard Tidak Muncul:

1. **Cek Console Browser (F12)**
   - Buka Developer Tools (F12)
   - Lihat tab Console
   - Cek apakah ada error JavaScript
   - Cek apakah ada error fetching API

2. **Cek Network Tab (F12 → Network)**
   - Apakah `/static/js/dashboard.js` berhasil load?
   - Apakah API endpoints (`/analytics/tracking-stats`, `/analytics/outcomes-history`) return 200 OK?

3. **Jalankan Test Script**
   ```bash
   # Di terminal Replit
   python3 test_dashboard_access.py
   ```

4. **Hard Refresh Browser**
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

5. **Cek URL Sekali Lagi**
   - Pastikan BUKAN di `/docs` atau `/redoc`
   - Harus di `/` atau `/dashboard`

---

## 📸 Screenshot Perbandingan

### ❌ SALAH - Yang TIDAK Seharusnya Anda Lihat:
```
Jika Anda melihat:
- JSON dengan "openapi": "3.1.0"
- FastAPI Swagger UI dengan list endpoints
- ReDoc dengan API documentation
- Code editor Replit dengan syntax highlighting

→ Anda di HALAMAN YANG SALAH!
```

### ✅ BENAR - Yang SEHARUSNYA Anda Lihat:
```
Jika Anda melihat:
- Header "CryptoSatX" dengan icon satellite
- 4 stat cards berwarna (gradient background)
- "Bulk Scanner" dengan textarea
- "Monitor List" dengan list kosong/terisi
- Charts dan TradingView widgets

→ Anda SUDAH BENAR!
```

---

## 🆘 Masih Bermasalah?

Jika setelah mengikuti panduan di atas dashboard masih tidak muncul:

1. **Screenshot Error:**
   - Screenshot halaman browser
   - Screenshot console error (F12)
   - Screenshot network tab (F12)

2. **Cek Log Aplikasi:**
   ```bash
   # Di terminal Replit, cek log error
   tail -100 ~/.config/replit/crash.log
   ```

3. **Test Manual:**
   ```bash
   # Test API endpoint
   curl -s http://localhost:8000/health
   curl -s http://localhost:8000/ | head -20
   ```

---

## 📝 Catatan Penting

- Dashboard menggunakan **dark mode** by default
- Dashboard **auto-refresh** setiap 30 detik
- Jika tidak ada signals, akan muncul "No signals yet"
- Charts akan kosong jika belum ada data
- TradingView charts memerlukan internet connection

---

## ✅ Checklist

Sebelum membuka dashboard, pastikan:
- [ ] Aplikasi sudah running (cek log: "🚀 CryptoSatX...")
- [ ] Tidak ada error di startup log
- [ ] Port 8000 listening (cek dengan `netstat` atau `ss`)
- [ ] Akses ke URL `/` atau `/dashboard` (BUKAN `/docs`)
- [ ] Browser sudah hard refresh (Ctrl+Shift+R)
- [ ] Developer console (F12) tidak ada error

---

**Dibuat:** 2025-11-21
**Untuk:** CryptoSatX Dashboard Access Issues
**Status:** Active Troubleshooting Guide

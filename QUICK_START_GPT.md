# ⚡ Quick Start - ChatGPT Integration

## 🎯 Cara Tercepat (2 Menit)

### **1. Copy OpenAPI URL**
```
https://guardiansofthetoken.org/gpt/actions/maximal-schema
```

### **2. Buat Custom GPT**
1. Buka: https://chat.openai.com/gpts/editor
2. Tab "Configure" → Bagian "Actions" → Klik "Create new action"
3. Klik "Import from URL"
4. Paste URL di atas → Klik "Import"
5. Klik "Save"

### **3. Test GPT**
Ketik di chat:
```
Show me BTC trading signal
```

**✅ SELESAI!** GPT sekarang bisa memanggil API Anda.

---

## 📱 Cara Kerja Auto-Alert

### **CURRENT SYSTEM (Sudah Jalan):**
```
User/GPT calls → /signals/SOL 
              ↓
         Signal: LONG ✅
              ↓
    Auto-send to Telegram 📲
```

**PENTING:**
- ❌ **TIDAK ADA auto-loop** (hemat API limit!)
- ✅ Alert dikirim **hanya saat endpoint dipanggil**
- ✅ NEUTRAL signals **tidak** kirim alert (reduce noise)

---

## 🤖 Setup Auto-Monitoring via GPT

Setelah Custom GPT aktif, Anda bisa minta GPT untuk monitor:

```
Monitor SOL, BTC, dan ETH. 
Check every 30 minutes.
Alert me if signal changes or score >70.
```

GPT akan:
1. Panggil `/signals/SOL` tiap 30 menit
2. Jika signal = LONG/SHORT → Auto-kirim ke Telegram
3. Report ke Anda via chat jika ada perubahan

**Ini BUKAN loop server-side**, jadi:
- ✅ API limit aman (hanya saat GPT panggil)
- ✅ Anda kontrol penuh (bisa stop monitoring kapan saja)
- ✅ Gratis (pakai ChatGPT Plus yang sudah Anda bayar)

---

## 📊 Endpoints Tersedia (13 Total)

**Core Signals:**
- `/signals/{symbol}` - Generate AI signal + auto Telegram

**Quick Actions:**
- `/gpt/quick-signal/{symbol}` - Fast 1-second signal
- `/gpt/whale-activity/{symbol}` - Whale tracking
- `/gpt/sentiment-summary/{symbol}` - Social sentiment
- `/gpt/risk-assessment/{symbol}` - Risk analysis

**Full list:** Lihat `GPT_SETUP_GUIDE.md`

---

## 💡 Contoh Penggunaan

### **Manual Check**
```
You: Cek signal SOL
GPT: *calls API* 🟢 SOL LONG - Score 65.2
     Entry: $168.10 | Stop: $166.50
     → Telegram alert sent ✅
```

### **Auto Monitor (Recommended)**
```
You: Monitor BTC and SOL, check every 30 mins
GPT: Will monitor BTC & SOL every 30 minutes.
     I'll alert you for signal changes.
     
     *After 30 mins* → Calls /signals/BTC
     *If LONG/SHORT* → Telegram sent automatically
```

### **Portfolio Check**
```
You: Optimize my portfolio: BTC, ETH, SOL
GPT: *calls /gpt/portfolio-optimization*
     Suggested allocation: 40% BTC, 35% ETH, 25% SOL
     Risk level: Medium
```

---

## 🔧 Troubleshooting

**Error: "Action failed"**
→ Test manual: https://guardiansofthetoken.org/signals/BTC

**No Telegram alert?**
→ Check signal type (NEUTRAL doesn't send alerts)

**GPT not responding?**
→ Refresh chat atau re-import schema

---

**Untuk panduan lengkap, lihat:** `GPT_SETUP_GUIDE.md`

**API Status:** https://guardiansofthetoken.org/health

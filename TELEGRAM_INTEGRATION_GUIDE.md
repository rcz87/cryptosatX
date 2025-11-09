# Telegram Integration Guide - CryptoSatX Alert System

## 📱 **Telegram Alert System - Cara Kerja & Konfigurasi**

### **🔍 Current Status Analysis**

#### **✅ Signal Generation Working:**
```json
{
  "success": true,
  "signal": {
    "symbol": "SOLUSDT",
    "signal": "NEUTRAL",
    "score": 49.2,
    "confidence": "high",
    "reasons": ["Price trend: neutral", "Social sentiment: 50/100"]
  }
}
```

#### **⚠️ Telegram Not Configured:**
```json
{
  "telegram": {
    "success": false,
    "message": "Telegram notifications not configured"
  }
}
```

---

## 🛠️ **Cara Mengaktifkan Telegram Alerts**

### **Step 1: Buat Telegram Bot**

#### **1.1 Chat dengan BotFather:**
1. Buka Telegram
2. Cari user: `@BotFather`
3. Kirim pesan: `/start`
4. Kirim pesan: `/newbot`

#### **1.2 Konfigurasi Bot:**
```
BotFather akan bertanya:
- Nama bot: "CryptoSatX Alert Bot"
- Username: "cryptosatx_alert_bot" (harus unik)
```

#### **1.3 Dapatkan Bot Token:**
```
BotFather akan memberikan token seperti:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### **Step 2: Dapatkan Chat ID**

#### **2.1 Cara Mudah:**
1. Kirim pesan ke bot Anda: `/start`
2. Buka browser: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Cari "chat" -> "id" dalam response JSON

#### **2.2 Contoh Response:**
```json
{
  "result": [
    {
      "message": {
        "chat": {
          "id": 123456789,
          "type": "private"
        }
      }
    }
  ]
}
```
**Chat ID:** `123456789`

### **Step 3: Konfigurasi Environment Variables**

#### **3.1 Set Environment Variables:**
```bash
# Untuk Windows (Command Prompt):
set TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
set TELEGRAM_CHAT_ID=123456789

# Untuk Windows (PowerShell):
$env:TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
$env:TELEGRAM_CHAT_ID="123456789"

# Untuk Linux/Mac:
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"
```

#### **3.2 Restart Server:**
```bash
# Stop server (Ctrl+C)
# Restart dengan environment variables
python main.py
```

---

## 🚀 **Cara Menggunakan Telegram Alerts**

### **Method 1: Manual Alert**
```bash
curl -X POST "http://localhost:8000/gpt/actions/send-alert/BTCUSDT"
```

### **Method 2: GPT Prompt Template**
```
Kirim alert untuk BTC jika signal STRONG BUY atau STRONG SELL:

1. GET /signals/BTCUSDT
2. Jika score > 80 atau < 20:
3. POST /gpt/actions/send-alert/BTCUSDT
```

### **Method 3: Automated Monitoring**
```
Setup monitoring untuk multiple symbols:
- BTC, ETH, SOL, BNB, ADA
- Check setiap 5 menit
- Kirim alert untuk signal changes
```

---

## 📊 **Format Alert Telegram**

### **📱 Contoh Alert yang Dikirim:**

```
🚨 CRYPTOSATX ALERT 🚨

📊 Symbol: BTCUSDT
🎯 Signal: STRONG BUY
📈 Score: 85.3
🔒 Confidence: VERY HIGH

💰 Current Price: $45,234.56
📊 Analysis:
• Price trend: Strong bullish momentum
• Social sentiment: 85/100 (Very Positive)
• Funding rate: 0.02% (Bullish)
• Open interest: Increasing

🎯 Entry: $45,200 - $45,300
🛡️ Stop Loss: $44,800
🎯 Target: $46,500

⏰ Time: 2025-11-09 14:49:57
🔗 Powered by CryptoSatX AI
```

---

## 🔧 **Advanced Configuration**

### **Multiple Chat Groups:**

#### **1. Group Chat ID:**
```bash
# Untuk group chat, gunakan negative ID
set TELEGRAM_CHAT_ID=-123456789
```

#### **2. Multiple Channels:**
```python
# Edit app/services/telegram_notifier.py
CHAT_IDS = [
    123456789,  # Private chat
    -123456789, # Group chat
]
```

### **Custom Alert Messages:**

#### **1. Edit Message Format:**
```python
# Di app/services/alert_service.py
def format_alert_message(signal_data):
    return f"""
    🚀 {signal_data['symbol']} ALERT 🚀
    
    Signal: {signal_data['signal']}
    Score: {signal_data['score']}
    Confidence: {signal_data['confidence']}
    
    🎯 Entry: {signal_data.get('entry', 'N/A')}
    🛡️ SL: {signal_data.get('stop_loss', 'N/A')}
    🎯 TP: {signal_data.get('target', 'N/A')}
    """
```

#### **2. Add Emoji & Formatting:**
```python
EMOJI_MAP = {
    "LONG": "🟢",
    "SHORT": "🔴", 
    "NEUTRAL": "🟡",
    "STRONG_BUY": "🚀",
    "STRONG_SHORT": "💥"
}
```

---

## 📈 **Alert Strategies**

### **Strategy 1: Signal Change Alert**
```python
# Monitor perubahan signal
if previous_signal != current_signal:
    send_telegram_alert(symbol, current_signal)
```

### **Strategy 2: Threshold Alert**
```python
# Alert untuk signal ekstrem
if score > 80 or score < 20:
    send_telegram_alert(symbol, signal_data)
```

### **Strategy 3: Time-based Alert**
```python
# Alert setiap jam untuk top movers
if is_top_hour() and symbol in top_movers:
    send_telegram_alert(symbol, signal_data)
```

### **Strategy 4: Volume Spike Alert**
```python
# Alert untuk volume abnormal
if volume > average_volume * 2:
    send_volume_alert(symbol, volume_data)
```

---

## 🛡️ **Security & Privacy**

### **Bot Security:**
1. **🔒 Private Bot** - Set bot ke private mode
2. **🚫 Block Unknown Users** - Hanya authorized users
3. **🔐 Rate Limiting** - Prevent spam messages
4. **📝 Log Messages** - Track all sent alerts

### **Privacy Protection:**
```python
# Hide sensitive information
def sanitize_message(signal_data):
    return {
        'symbol': signal_data['symbol'],
        'signal': signal_data['signal'],
        'score': signal_data['score'],
        # Remove API keys, internal data
    }
```

---

## 🔍 **Troubleshooting**

### **Common Issues:**

#### **1. "Telegram notifications not configured"**
```bash
# Check environment variables
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Restart server after setting variables
```

#### **2. "Chat not found"**
```bash
# Verify chat ID dengan:
curl https://api.telegram.org/bot<TOKEN>/getUpdates

# Pastikan bot sudah di-start user
```

#### **3. "Forbidden: bot was blocked by the user"**
```bash
# User harus unblock bot
# Kirim /start ke bot lagi
```

#### **4. "Too many requests"**
```python
# Add delay between messages
import time
time.sleep(1)  # 1 second delay
```

---

## 📊 **Monitoring & Analytics**

### **Alert Performance Tracking:**
```python
# Track alert effectiveness
alert_metrics = {
    'total_sent': 0,
    'successful_trades': 0,
    'win_rate': 0.0,
    'avg_profit': 0.0
}
```

### **User Engagement:**
```python
# Track user interactions
user_stats = {
    'messages_sent': 0,
    'clicks': 0,
    'responses': 0
}
```

---

## 🎯 **Best Practices**

### **✅ Do's:**
1. **📱 Test Thoroughly** - Test dengan bot development dulu
2. **⏰ Rate Limit** - Jangan spam users
3. **🎯 Relevant Content** - Hanya kirim valuable alerts
4. **📊 Track Performance** - Monitor alert effectiveness
5. **🔒 Security First** - Protect user privacy

### **❌ Don'ts:**
1. **🚫 No Spam** - Jangan kirim terlalu banyak messages
2. **🚫 No Sensitive Data** - Jangan expose API keys
3. **🚫 No False Promises** - Realistic expectations
4. **🚫 No Unverified Info** - Validate data sebelum kirim

---

## 🚀 **Production Deployment**

### **Environment Setup:**
```bash
# Production environment variables
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
export TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID}"
export TELEGRAM_ENABLED="true"
```

### **Monitoring Setup:**
```python
# Health check untuk Telegram
async def check_telegram_health():
    try:
        await bot.get_me()
        return {"status": "healthy", "telegram": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## 🎊 **Summary**

### **✅ Telegram Integration Complete:**

1. **🤖 Bot Creation** - Step-by-step guide
2. **🔧 Configuration** - Environment variables setup
3. **📱 Alert System** - Working with signal generation
4. **📊 Message Format** - Professional alert templates
5. **🛡️ Security** - Best practices implemented
6. **🔍 Troubleshooting** - Common issues solved

### **🚀 Ready to Use:**
- **Signal Generation:** ✅ Working
- **Alert System:** ✅ Implemented
- **Telegram Integration:** ⚠️ Requires configuration
- **Message Format:** ✅ Professional template
- **Security:** ✅ Best practices

### **🎯 Next Steps:**
1. **Configure Telegram Bot** - Follow setup guide
2. **Test Alert System** - Verify functionality
3. **Customize Messages** - Personalize format
4. **Monitor Performance** - Track effectiveness
5. **Scale Up** - Add more features

**Telegram alert system siap digunakan setelah konfigurasi bot token dan chat ID!** 🚀

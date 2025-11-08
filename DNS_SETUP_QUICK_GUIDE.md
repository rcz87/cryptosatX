# 🌐 DNS Setup Quick Guide - guardiansofthetoken.com

## ⚡ Quick Start (After Deployment)

### **Step 1: Get DNS Records from Replit**

Setelah deploy dan link domain di Replit, Anda akan dapat:

```
CNAME Target: [something].repl.co
```

**Contoh:**
```
your-app-abc123.repl.co
```

---

### **Step 2: Configure DNS Records**

Di DNS provider Anda (GoDaddy, Cloudflare, Namecheap, etc):

#### **Record 1: Root Domain (@)**
```
Type:  CNAME
Name:  @
Value: [your-app].repl.co    ← dari Replit
TTL:   300 (5 minutes)
```

#### **Record 2: WWW Subdomain**
```
Type:  CNAME
Name:  www
Value: [your-app].repl.co    ← sama seperti atas
TTL:   300 (5 minutes)
```

---

## 📋 DNS Provider Specific Instructions

### **Cloudflare** (Recommended)

1. Login → Select domain → DNS → Records
2. Click "Add record"
3. Configure:
   ```
   Type: CNAME
   Name: @
   Target: [your-app].repl.co
   Proxy status: DNS only (gray cloud) ← IMPORTANT!
   TTL: Auto
   ```
4. Repeat untuk `www`:
   ```
   Name: www
   Target: [your-app].repl.co
   Proxy: DNS only
   ```
5. Save

**⚠️ Important:** Set proxy to **DNS only** (gray cloud), NOT proxied (orange cloud)!

---

### **GoDaddy**

1. My Products → Domain → DNS
2. Click "Add" di Records section
3. Configure:
   ```
   Type: CNAME
   Name: @
   Value: [your-app].repl.co
   TTL: Custom - 600 seconds
   ```
4. Repeat untuk `www`:
   ```
   Name: www
   Value: [your-app].repl.co
   ```
5. Save

---

### **Namecheap**

1. Domain List → Manage → Advanced DNS
2. Click "Add New Record"
3. Configure:
   ```
   Type: CNAME Record
   Host: @
   Value: [your-app].repl.co
   TTL: Automatic
   ```
4. Add another:
   ```
   Host: www
   Value: [your-app].repl.co
   ```
5. Save changes

---

### **Google Domains / Squarespace**

1. DNS settings → Custom records
2. Create new record:
   ```
   Name: @
   Type: CNAME
   Data: [your-app].repl.co
   TTL: 5 minutes
   ```
3. Add www record:
   ```
   Name: www
   Type: CNAME
   Data: [your-app].repl.co
   ```
4. Save

---

## ✅ Verification Checklist

### **Immediately After DNS Setup:**

- [ ] DNS records added to provider
- [ ] Both @ and www configured
- [ ] CNAME points to correct Replit URL
- [ ] TTL set to 300-600 seconds
- [ ] Changes saved

---

### **After 5-10 Minutes:**

**Check DNS Propagation:**
```
https://dnschecker.org/#CNAME/guardiansofthetoken.com
```

**Expected Result:**
```
CNAME: [your-app].repl.co ✅
Status: Green checkmarks globally
```

---

### **After DNS Propagates:**

**Test URLs:**
```bash
# Health check
curl https://guardiansofthetoken.com/health

# Should return: {"status":"healthy",...}
```

**Test in Browser:**
```
https://guardiansofthetoken.com/docs
```

**Should show:** Swagger API documentation ✅

---

## 🔐 SSL Certificate

**Automatic!** ✅

Replit auto-generates SSL certificate after:
1. Domain DNS verified
2. Usually 5-10 minutes after DNS propagates
3. Auto-renews forever

**No action needed on your side!**

---

## ⚙️ Environment Variable Setup

**After DNS working, set in Replit:**

### **Deployment → Secrets:**

```
Key:   BASE_URL
Value: https://guardiansofthetoken.com
```

### **Then Redeploy:**

1. Go to deployment
2. Click "Redeploy" or "Deploy"
3. Wait ~2 minutes
4. GPT schema will now show custom domain! ✅

---

## 🧪 Complete Testing

After everything setup:

### **1. API Health:**
```bash
curl https://guardiansofthetoken.com/health
```

### **2. Trading Signal:**
```bash
curl https://guardiansofthetoken.com/signals/BTC
```

### **3. Smart Money Scanner:**
```bash
curl "https://guardiansofthetoken.com/smart-money/scan?coins=BTC,ETH"
```

### **4. GPT Schema:**
```bash
curl https://guardiansofthetoken.com/gpt/action-schema
```

**Should show:**
```json
{
  "openapi": "3.0.0",
  "servers": [
    {
      "url": "https://guardiansofthetoken.com"
    }
  ],
  ...
}
```

### **5. Documentation:**
Open browser:
```
https://guardiansofthetoken.com/docs
```

Should show interactive Swagger UI ✅

---

## 🤖 Update GPT Actions

**After domain fully working:**

1. Go to: https://chat.openai.com/gpts/editor
2. Select your GPT
3. Configure → Actions
4. Update schema URL:
   ```
   https://guardiansofthetoken.com/gpt/action-schema
   ```
5. Save
6. Test with prompt: "What's the signal for BTC?"

**GPT now uses your custom domain!** ✅

---

## 🚨 Troubleshooting

### **DNS Not Propagating?**

**Check:**
- Wait longer (can take 24-48 hours, usually < 1 hour)
- Verify CNAME records correct
- Check https://dnschecker.org
- Clear browser cache / use incognito

**Fix:**
- Double-check CNAME value matches Replit exactly
- Ensure no extra spaces in CNAME value
- Delete any old A records for same domain

---

### **SSL Certificate Error?**

**Symptoms:** "Not Secure" warning in browser

**Fix:**
- Wait 10-15 minutes after DNS propagates
- Replit auto-generates SSL, just needs time
- Force refresh (Ctrl+F5)
- Clear browser cache

---

### **404 Not Found?**

**Fix:**
1. Verify deployment is running in Replit
2. Check BASE_URL environment variable set
3. Redeploy after setting BASE_URL
4. Test .repl.co URL first (should work)

---

### **GPT Can't Connect?**

**Fix:**
1. Test URL directly in browser first
2. Verify /gpt/action-schema endpoint working
3. Check CORS (already configured ✅)
4. Re-import schema in GPT Actions

---

## 📞 Get Help

**DNS Issues:**
- DNS provider support
- https://dnschecker.org for checking

**Replit Issues:**
- https://discord.gg/replit
- https://docs.replit.com

**Test First:**
- Always test .repl.co URL before custom domain
- If .repl.co works but custom doesn't = DNS issue
- If both don't work = deployment issue

---

## ✅ Success Criteria

Everything working when:

```
✅ https://guardiansofthetoken.com/health returns healthy
✅ https://guardiansofthetoken.com/docs shows Swagger UI
✅ HTTPS green lock in browser (SSL working)
✅ /gpt/action-schema shows custom domain in "servers"
✅ GPT Actions can call all endpoints
```

**When all checked = Setup complete!** 🎉

---

## 📋 Quick Reference

**Your Domain:**
```
guardiansofthetoken.com
```

**DNS Records:**
```
@ (root)  → CNAME → [your-app].repl.co
www       → CNAME → [your-app].repl.co
```

**Environment Variable:**
```
BASE_URL=https://guardiansofthetoken.com
```

**Key URLs:**
```
API: https://guardiansofthetoken.com
Docs: https://guardiansofthetoken.com/docs
GPT: https://guardiansofthetoken.com/gpt/action-schema
```

---

**Need detailed guide?** See `CUSTOM_DOMAIN_SETUP.md`

**Ready to deploy?** See `DEPLOYMENT_GUIDE.md`

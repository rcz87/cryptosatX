# 🌐 Custom Domain Setup: guardiansofthetoken.com

## ✅ Domain Configuration Ready

API Anda sudah dikonfigurasi untuk mendukung custom domain **guardiansofthetoken.com**!

---

## 📋 Setup Process Overview

### **Timeline:**
1. ✅ **Now**: Deploy API ke production Replit
2. ⏳ **After Deploy**: Link domain di Replit dashboard
3. ⏳ **Your Side**: Configure DNS records
4. ✅ **Result**: API live di https://guardiansofthetoken.com

---

## 🚀 Step 1: Deploy to Production First

**Sebelum setup domain, deploy dulu!**

```bash
1. Klik "Deploy" button (top-right)
2. Pilih "Autoscale" 
3. Klik "Publish"
4. Wait deployment selesai (~5 minutes)
```

**Catat Production URL sementara:**
```
https://[your-repl-name].repl.co
```

---

## 🔗 Step 2: Link Domain di Replit (After Deployment)

### **A. Akses Deployment Settings**

1. **Go to**: Replit Dashboard
2. **Select**: Your deployed project
3. **Click**: "Deployments" tab
4. **Click**: Your active deployment
5. **Find**: "Domains" atau "Custom Domain" section

### **B. Add Custom Domain**

1. **Click**: "Add custom domain" atau "Link domain"
2. **Enter Domain**: `guardiansofthetoken.com`
3. **Submit**: Replit akan kasih DNS records yang perlu diconfigure

**Replit akan provide:**
- CNAME record atau A record
- Verification TXT record (mungkin)

---

## 🌐 Step 3: Configure DNS Records

**Di DNS provider Anda** (GoDaddy, Cloudflare, Namecheap, etc):

### **Option A: CNAME Record (Recommended)**

Jika Replit provide CNAME:

```
Type: CNAME
Name: @ (atau root domain)
Value: [replit-provided-cname].repl.co
TTL: 300 (atau auto)
```

**Untuk www subdomain:**
```
Type: CNAME
Name: www
Value: [replit-provided-cname].repl.co
TTL: 300
```

---

### **Option B: A Record**

Jika Replit provide IP address:

```
Type: A
Name: @ (atau root domain)
Value: [replit-provided-ip-address]
TTL: 300
```

**Untuk www subdomain:**
```
Type: A
Name: www
Value: [replit-provided-ip-address]
TTL: 300
```

---

### **Verification TXT Record (Jika Diminta)**

Untuk verify ownership:

```
Type: TXT
Name: @ atau _replit-challenge
Value: [verification-code-from-replit]
TTL: 300
```

---

## ⚙️ Step 4: Set Environment Variable

**Di Replit Deployment Settings:**

### **A. Add SECRET**

1. **Go to**: Deployment → Secrets/Environment Variables
2. **Add New Secret**:
   ```
   Key: BASE_URL
   Value: https://guardiansofthetoken.com
   ```
3. **Save** dan **Redeploy**

### **B. Alternative: Set in Replit Workspace**

Di Replit workspace (untuk development):

1. **Secrets tab** (kiri sidebar)
2. **Add SECRET**:
   ```
   BASE_URL=https://guardiansofthetoken.com
   ```

---

## ✅ Step 5: Verify Domain Setup

### **Wait for DNS Propagation**
- **Time**: 5 minutes - 48 hours (usually < 1 hour)
- **Check**: https://dnschecker.org/#CNAME/guardiansofthetoken.com

### **Test Endpoints**

Setelah DNS propagate:

**1. Health Check:**
```bash
curl https://guardiansofthetoken.com/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "Crypto Futures Signal API"
}
```

**2. Trading Signal:**
```bash
curl https://guardiansofthetoken.com/signals/BTC
```

**3. Smart Money Scanner:**
```bash
curl "https://guardiansofthetoken.com/smart-money/scan?coins=BTC,ETH"
```

**4. GPT Actions Schema:**
```bash
curl https://guardiansofthetoken.com/gpt/action-schema
```

**5. API Documentation:**
Open browser:
```
https://guardiansofthetoken.com/docs
```

---

## 🤖 Step 6: Update GPT Actions

### **Schema URL Baru:**

Setelah domain live, update GPT Actions schema URL:

**Old (Replit default):**
```
https://[your-repl-name].repl.co/gpt/action-schema
```

**New (Custom domain):**
```
https://guardiansofthetoken.com/gpt/action-schema
```

### **Update GPT:**

1. **Go to**: GPT Builder → Your GPT
2. **Configure**: Tab "Configure" → "Actions"
3. **Edit Schema URL**: Change to `https://guardiansofthetoken.com/gpt/action-schema`
4. **Save** changes
5. **Test**: GPT should now use your custom domain ✅

---

## 📊 Final URLs After Setup

### **Production API:**
```
https://guardiansofthetoken.com
```

### **API Documentation:**
```
https://guardiansofthetoken.com/docs
https://guardiansofthetoken.com/redoc
```

### **GPT Actions Schema:**
```
https://guardiansofthetoken.com/gpt/action-schema
```

### **Key Endpoints:**
```
https://guardiansofthetoken.com/health
https://guardiansofthetoken.com/signals/BTC
https://guardiansofthetoken.com/smart-money/scan
https://guardiansofthetoken.com/smart-money/scan/accumulation
https://guardiansofthetoken.com/smart-money/scan/distribution
```

---

## 🔐 SSL/HTTPS Certificate

**✅ Automatic!**

Replit automatically provides:
- Free SSL certificate (Let's Encrypt)
- Auto-renewal
- HTTPS enforcement

**No action needed!** Domain akan otomatis HTTPS.

---

## 🎨 Custom Domain Benefits

### **Professional Branding:**
- ✅ guardiansofthetoken.com (instead of xyz.repl.co)
- ✅ Custom, memorable URL
- ✅ Professional appearance

### **SEO & Trust:**
- ✅ Better for SEO
- ✅ More trustworthy to users
- ✅ Easier to share

### **GPT Actions:**
- ✅ Branded API endpoints
- ✅ Professional custom GPT
- ✅ Consistent branding

---

## 📋 DNS Configuration Examples

### **Cloudflare DNS:**

```
Type: CNAME
Name: @
Target: [replit-cname].repl.co
Proxy status: DNS only (gray cloud)
TTL: Auto
```

**Important:** Set to "DNS only" (gray cloud), NOT proxied!

---

### **GoDaddy DNS:**

```
Type: CNAME
Host: @
Points to: [replit-cname].repl.co
TTL: 600 seconds (10 minutes)
```

---

### **Namecheap DNS:**

```
Type: CNAME Record
Host: @
Value: [replit-cname].repl.co
TTL: Automatic
```

---

## 🔍 Troubleshooting

### **Issue: Domain not resolving**

**Solutions:**
1. Wait longer (DNS can take up to 48 hours)
2. Check DNS records configured correctly
3. Use https://dnschecker.org to verify propagation
4. Clear browser cache / try incognito mode

### **Issue: Certificate error (Not Secure)**

**Solutions:**
1. Wait 5-10 minutes after DNS propagates
2. Replit auto-generates SSL cert after domain verified
3. Try force refresh (Ctrl+F5)
4. Check domain configured in Replit correctly

### **Issue: GPT Actions can't connect**

**Solutions:**
1. Verify BASE_URL environment variable set
2. Test direct curl to https://guardiansofthetoken.com/health
3. Check CORS configured (already done ✅)
4. Verify schema URL in GPT Actions correct

### **Issue: Showing old Replit URL**

**Solutions:**
1. Redeploy after setting BASE_URL
2. Clear GPT Actions cache (re-import schema)
3. Test /gpt/action-schema endpoint directly

---

## 📝 Checklist

### **Pre-Deployment:**
- [x] ✅ Code ready for production
- [x] ✅ Custom domain support configured
- [x] ✅ Environment variable handling ready

### **Deployment:**
- [ ] 🔲 Deploy to Replit production
- [ ] 🔲 Note production URL
- [ ] 🔲 Test endpoints on .repl.co URL

### **Domain Linking:**
- [ ] 🔲 Add custom domain in Replit dashboard
- [ ] 🔲 Note DNS records provided by Replit
- [ ] 🔲 Configure DNS at your registrar
- [ ] 🔲 Add BASE_URL secret (https://guardiansofthetoken.com)
- [ ] 🔲 Redeploy application

### **Verification:**
- [ ] 🔲 Check DNS propagation (dnschecker.org)
- [ ] 🔲 Test https://guardiansofthetoken.com/health
- [ ] 🔲 Verify SSL certificate working (HTTPS green lock)
- [ ] 🔲 Test all API endpoints
- [ ] 🔲 Check /docs page loading

### **GPT Actions Update:**
- [ ] 🔲 Update schema URL to custom domain
- [ ] 🔲 Test GPT Actions with new URL
- [ ] 🔲 Verify all operations working

---

## 🎯 Quick Reference

### **Your Custom Domain:**
```
guardiansofthetoken.com
```

### **DNS Records (Example):**
```
CNAME: @ → [replit-cname].repl.co
CNAME: www → [replit-cname].repl.co
```

### **Environment Variable:**
```
BASE_URL=https://guardiansofthetoken.com
```

### **GPT Schema URL:**
```
https://guardiansofthetoken.com/gpt/action-schema
```

---

## 💡 Pro Tips

### **1. Use www Redirect**
Configure both `guardiansofthetoken.com` and `www.guardiansofthetoken.com` to point to same deployment.

### **2. Monitor DNS**
Use https://dnschecker.org to monitor DNS propagation globally.

### **3. Test Before GPT Update**
Verify all endpoints work on custom domain before updating GPT Actions.

### **4. Keep Replit URL**
Don't delete Replit default URL - good for backup/testing.

### **5. Documentation**
Update your documentation to reference custom domain.

---

## 🆘 Support

**DNS Issues:**
- Contact your DNS provider support
- Use their DNS checker tools

**Replit Deployment:**
- Replit Docs: https://docs.replit.com
- Replit Discord: https://discord.gg/replit

**API Issues:**
- Test on .repl.co URL first
- Check deployment logs
- Verify secrets configured

---

## ✅ Summary

```
1. Deploy to Replit Production
   └─→ Get .repl.co URL
   
2. Link Domain in Replit
   └─→ Get DNS records
   
3. Configure DNS
   └─→ CNAME @ → [replit].repl.co
   └─→ CNAME www → [replit].repl.co
   
4. Set BASE_URL Secret
   └─→ BASE_URL=https://guardiansofthetoken.com
   └─→ Redeploy
   
5. Wait DNS Propagation
   └─→ 5 mins - 48 hours (usually < 1 hour)
   
6. Verify & Test
   └─→ Test all endpoints
   └─→ Update GPT Actions
   
7. Done! ✅
   └─→ API live at guardiansofthetoken.com
```

---

**🎉 Ready untuk custom domain setup!**

**Next Steps:**
1. Deploy production dulu
2. Ikuti guide ini untuk link domain
3. Configure DNS di registrar Anda
4. Test & update GPT Actions

**Your branded API will be:**
```
🌐 https://guardiansofthetoken.com
```

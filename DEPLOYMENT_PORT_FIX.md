# 🔧 Deployment Port Configuration Fix

## ⚠️ Issue Encountered

The deployment failed with error:
```
The run command is incomplete - it's missing the port number after '--port'
```

## ✅ Solution

### **For Replit Autoscale Deployments:**

When deploying, you need to **manually configure** the run command in the Replit deployment UI:

### **Correct Run Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 80
```

**Important:** Port **80** is required for Autoscale deployments (not 5000 or 8000)

---

## 📋 Manual Deployment Steps

### **Step 1: Access Deployment Configuration**

1. Click "Deploy" button (top-right)
2. Select "Autoscale" as deployment type
3. Find "Run Command" section

### **Step 2: Set Run Command**

In the "Run Command" or "Start Command" field, enter:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 80
```

**Copy-paste exactly:**
```
uvicorn app.main:app --host 0.0.0.0 --port 80
```

### **Step 3: Verify Machine Settings**

- **CPU**: 1 vCPU (default)
- **Memory**: 2 GiB RAM (default)
- **Max Machines**: 3 (auto-scale)

### **Step 4: Deploy**

Click "Publish" or "Deploy" button

---

## 🎯 Why Port 80?

**Autoscale deployments:**
- HTTP requests → External port 80
- Your app must listen on port 80
- Different from development (port 8000)

**VM deployments:**
- Can use any port
- Configure port mapping separately

---

## ✅ Verification After Deploy

### **Test Health:**
```bash
curl https://[your-app].repl.co/health
```

### **Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "...",
  "service": "Crypto Futures Signal API"
}
```

---

## 🔍 Troubleshooting

### **Still Getting Port Error?**

Double-check run command has:
- ✅ `--port 80` (with space before 80)
- ✅ Exact command: `uvicorn app.main:app --host 0.0.0.0 --port 80`
- ✅ No typos or extra spaces

### **App Crash Looping?**

Check deployment logs for:
- Port binding errors
- Missing dependencies
- Secret/environment variable issues

---

## 📝 Alternative Run Commands

If using Gunicorn (for production):
```bash
gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80
```

If need multiple workers:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 80 --workers 2
```

---

## ✅ Final Checklist

- [ ] Run command: `uvicorn app.main:app --host 0.0.0.0 --port 80`
- [ ] Deployment type: Autoscale
- [ ] Machine settings: 1 vCPU, 2 GiB RAM
- [ ] Secrets configured (auto-transfer from dev)
- [ ] Click "Deploy"
- [ ] Wait 2-5 minutes
- [ ] Test endpoints
- [ ] Setup custom domain (optional)

---

**Ready to redeploy with correct port configuration!** ✅

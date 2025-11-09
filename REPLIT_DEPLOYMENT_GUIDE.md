# CryptoSatX Replit Production Deployment Guide

## 🚀 **Replit-Specific Deployment Configuration**

Karena sistem sudah berjalan di Replit dengan VM, kita perlu menyesuaikan enhancement untuk deployment di Replit environment.

---

## 📋 **Replit Environment Constraints & Solutions**

### **1. Database Strategy**
**Problem**: Replit tidak support PostgreSQL persistent database
**Solution**: 
- Gunakan **Replit Database** (built-in PostgreSQL)
- Fallback ke **SQLite** untuk development
- Redis menggunakan **Replit Redis** (jika available) atau **Upstash**

### **2. File Structure Adjustments**
```
cryptosatx/
├── .replit
├── main.py (entry point untuk Replit)
├── requirements.txt
├── .env
├── app/
│   ├── main.py (FastAPI app)
│   ├── services/
│   ├── middleware/
│   └── ...
├── database/
│   ├── init.sql
│   └── migrations/
├── monitoring/
└── logs/
```

### **3. Environment Variables untuk Replit**
```bash
# Replit Database
REPLIT_DB_URL="postgresql://user:pass@host:5432/dbname"

# Redis (Upstash atau Replit Redis)
REDIS_URL="redis://default:password@host:port"

# API Keys
COINAPI_KEY="your_coinapi_key"
COINGLASS_API_KEY="your_coinglass_key"
LUNARCRUSH_API_KEY="your_lunarcrush_key"

# Replit Specific
REPL_ID="your_repl_id"
REPL_SLUG="your_repl_slug"
REPL_OWNER="your_username"
```

---

## 🔧 **Replit Configuration Files**

### **.replit file**
```toml
[run]
command = "python main.py"

[packager]
language = "python3"
version = "3.11"

[unitTest]
language = "python3"
version = "3.11"

[deployment]
run = ["python", "main.py"]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10
```

### **main.py (Replit Entry Point)**
```python
import os
import asyncio
from app.main import app
import uvicorn

# Replit specific setup
if __name__ == "__main__":
    # Get port from Replit environment
    port = int(os.environ.get("PORT", 8000))
    
    # Configure for Replit deployment
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        workers=1,     # Replit supports single worker
        log_level="info"
    )
```

---

## 🗄️ **Database Adaptation for Replit**

### **Database Service untuk Replit**
```python
# app/services/replit_database_service.py
import os
import asyncpg
import sqlite3
import aiosqlite
from typing import Optional, Dict, Any
from app.utils.logger import default_logger

class ReplitDatabaseService:
    """Database service yang adaptif untuk Replit environment"""
    
    def __init__(self):
        self.logger = default_logger
        self.db_type = self._detect_db_type()
        self.connection = None
    
    def _detect_db_type(self) -> str:
        """Detect database type berdasarkan environment"""
        if os.getenv("REPLIT_DB_URL"):
            return "postgresql"
        elif os.getenv("REDIS_URL"):
            return "sqlite_with_redis"
        else:
            return "sqlite"
    
    async def connect(self):
        """Connect ke database yang tersedia"""
        if self.db_type == "postgresql":
            await self._connect_postgresql()
        else:
            await self._connect_sqlite()
    
    async def _connect_postgresql(self):
        """Connect ke Replit PostgreSQL"""
        try:
            self.connection = await asyncpg.connect(os.getenv("REPLIT_DB_URL"))
            self.logger.info("Connected to Replit PostgreSQL")
        except Exception as e:
            self.logger.error(f"PostgreSQL connection failed: {e}")
            # Fallback ke SQLite
            self.db_type = "sqlite"
            await self._connect_sqlite()
    
    async def _connect_sqlite(self):
        """Connect ke SQLite dengan async support"""
        try:
            self.connection = await aiosqlite.connect("cryptosatx.db")
            await self._init_sqlite_schema()
            self.logger.info("Connected to SQLite database")
        except Exception as e:
            self.logger.error(f"SQLite connection failed: {e}")
            raise
    
    async def _init_sqlite_schema(self):
        """Initialize SQLite schema dari PostgreSQL schema"""
        # Convert PostgreSQL schema ke SQLite
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            api_key TEXT UNIQUE,
            tier TEXT DEFAULT 'free',
            preferences TEXT DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_active BOOLEAN DEFAULT 1
        );
        
        -- Signals table
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            score REAL NOT NULL,
            confidence TEXT NOT NULL,
            price REAL NOT NULL,
            reasons TEXT NOT NULL,
            metrics TEXT NOT NULL,
            premium_metrics TEXT,
            comprehensive_metrics TEXT,
            lunarcrush_metrics TEXT,
            coinapi_metrics TEXT,
            debug_info TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            user_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        -- Market data cache
        CREATE TABLE IF NOT EXISTS market_data (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            provider TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            UNIQUE(symbol, provider, timestamp)
        );
        
        -- API usage tracking
        CREATE TABLE IF NOT EXISTS api_usage (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            endpoint TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            request_count INTEGER DEFAULT 1,
            window_start DATETIME DEFAULT CURRENT_TIMESTAMP,
            window_end DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_signals_symbol_created ON signals(symbol, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_market_data_symbol_provider ON market_data(symbol, provider);
        CREATE INDEX IF NOT EXISTS idx_api_usage_user_window ON api_usage(user_id, window_start, window_end);
        """
        
        await self.connection.executescript(schema_sql)
```

---

## 🔄 **Redis Adaptation untuk Replit**

### **Redis Service untuk Replit**
```python
# app/services/replit_cache_service.py
import os
import json
import asyncio
from typing import Any, Optional, Dict
from app.utils.logger import default_logger

class ReplitCacheService:
    """Cache service yang adaptif untuk Replit environment"""
    
    def __init__(self):
        self.logger = default_logger
        self.cache_type = self._detect_cache_type()
        self.cache_data = {}  # Fallback memory cache
        self.redis_client = None
    
    def _detect_cache_type(self) -> str:
        """Detect cache type berdasarkan environment"""
        if os.getenv("REDIS_URL"):
            return "redis"
        elif os.getenv("UPSTASH_REDIS_REST_URL"):
            return "upstash"
        else:
            return "memory"
    
    async def connect(self):
        """Connect ke cache yang tersedia"""
        if self.cache_type == "redis":
            await self._connect_redis()
        elif self.cache_type == "upstash":
            await self._connect_upstash()
        else:
            self.logger.info("Using memory cache (fallback)")
    
    async def _connect_redis(self):
        """Connect ke Redis"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(os.getenv("REDIS_URL"))
            await self.redis_client.ping()
            self.logger.info("Connected to Redis")
        except Exception as e:
            self.logger.error(f"Redis connection failed: {e}")
            self.cache_type = "memory"
    
    async def _connect_upstash(self):
        """Connect ke Upstash Redis REST API"""
        try:
            import httpx
            self.upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
            self.upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
            self.http_client = httpx.AsyncClient()
            
            # Test connection
            response = await self.http_client.get(
                f"{self.upstash_url}/ping",
                headers={"Authorization": f"Bearer {self.upstash_token}"}
            )
            if response.status_code == 200:
                self.logger.info("Connected to Upstash Redis")
            else:
                raise Exception("Upstash connection failed")
        except Exception as e:
            self.logger.error(f"Upstash connection failed: {e}")
            self.cache_type = "memory"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value dari cache"""
        if self.cache_type == "redis":
            return await self._redis_get(key)
        elif self.cache_type == "upstash":
            return await self._upstash_get(key)
        else:
            return self._memory_get(key)
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set value ke cache"""
        if self.cache_type == "redis":
            return await self._redis_set(key, value, ttl_seconds)
        elif self.cache_type == "upstash":
            return await self._upstash_set(key, value, ttl_seconds)
        else:
            return self._memory_set(key, value, ttl_seconds)
    
    # Implementation methods untuk setiap cache type...
```

---

## 🚀 **Deployment Steps untuk Replit**

### **1. Update requirements.txt**
```txt
# Existing dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# New dependencies untuk enhancements
redis==5.0.1
asyncpg==0.29.0
aiosqlite==0.19.0
prometheus-client==0.19.0
slowapi==0.1.9
psutil==5.9.6

# Replit specific
replit==3.2.7
```

### **2. Update .env untuk Replit**
```bash
# Replit Database (auto-generated by Replit)
REPLIT_DB_URL="${REPLIT_DB_URL}"

# Redis (gunakan Upstash jika tidak ada built-in)
REDIS_URL="${REDIS_URL}"
UPSTASH_REDIS_REST_URL="${UPSTASH_REDIS_REST_URL}"
UPSTASH_REDIS_REST_TOKEN="${UPSTASH_REDIS_REST_TOKEN}"

# API Keys
COINAPI_KEY="${COINAPI_KEY}"
COINGLASS_API_KEY="${COINGLASS_API_KEY}"
LUNARCRUSH_API_KEY="${LUNARCRUSH_API_KEY}"

# Replit Environment
REPL_ID="${REPL_ID}"
REPL_SLUG="${REPL_SLUG}"
REPL_OWNER="${REPL_OWNER}"
PORT="${PORT:-8000}"
```

### **3. Update app/main.py untuk Replit**
```python
# Add Replit-specific startup
@app.on_event("startup")
async def startup_event():
    """Initialize services untuk Replit environment"""
    # Initialize database (Replit adaptive)
    from app.services.replit_database_service import ReplitDatabaseService
    db_service = ReplitDatabaseService()
    await db_service.connect()
    
    # Initialize cache (Replit adaptive)
    from app.services.replit_cache_service import ReplitCacheService
    cache_service = ReplitCacheService()
    await cache_service.connect()
    
    # Initialize metrics
    from app.services.metrics_service import metrics_service
    await metrics_service.start_metrics_collection()
    
    logger.info("CryptoSatX started successfully on Replit")
```

---

## 📊 **Monitoring untuk Replit**

### **Replit-Specific Metrics**
```python
# app/services/replit_metrics.py
import os
import psutil
from prometheus_client import Gauge, Counter

class ReplitMetrics:
    """Metrics khusus untuk Replit environment"""
    
    def __init__(self):
        # Replit resource metrics
        self.replit_cpu_usage = Gauge('replit_cpu_usage_percent', 'Replit CPU usage')
        self.replit_memory_usage = Gauge('replit_memory_usage_bytes', 'Replit memory usage')
        self.replit_disk_usage = Gauge('replit_disk_usage_bytes', 'Replit disk usage')
        
        # Replit-specific metrics
        self.repl_id = os.getenv("REPL_ID", "unknown")
        self.repl_slug = os.getenv("REPL_SLUG", "unknown")
    
    def update_replit_metrics(self):
        """Update Replit-specific metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.replit_cpu_usage.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.replit_memory_usage.set(memory.used)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.replit_disk_usage.set(disk.used)
```

---

## 🔧 **Deployment Checklist**

### **Pre-Deployment:**
- [ ] Update requirements.txt dengan Replit dependencies
- [ ] Configure environment variables di Replit Secrets
- [ ] Test database connection (Replit DB)
- [ ] Test cache connection (Redis/Upstash)
- [ ] Update .replit configuration
- [ ] Create main.py entry point

### **Deployment:**
- [ ] Push changes ke Replit Git
- [ ] Replit auto-deployment akan trigger
- [ ] Check deployment logs
- [ ] Verify health endpoint: `https://your-repl.replit.app/health`
- [ ] Test API endpoints

### **Post-Deployment:**
- [ ] Monitor Replit logs
- [ ] Check database connectivity
- [ ] Verify cache performance
- [ ] Test rate limiting
- [ ] Monitor metrics collection

---

## 🚨 **Replit-Specific Considerations**

### **1. Resource Limits**
- CPU: 0.5-2 vCPU tergantung plan
- Memory: 512MB-2GB tergantung plan
- Storage: 1GB persistent storage
- Network: Rate limiting untuk external API calls

### **2. Performance Optimizations**
```python
# Optimize untuk Replit resource limits
MAX_CONCURRENT_REQUESTS = 10  # Limit concurrent requests
CACHE_TTL = 300  # 5 minutes cache
DB_POOL_SIZE = 5  # Small connection pool
```

### **3. Error Handling untuk Replit**
```python
# Graceful degradation untuk resource limits
try:
    # Heavy operation
    result = await expensive_operation()
except MemoryError:
    # Fallback ke lighter operation
    result = await lightweight_operation()
    logger.warning("Used fallback due to memory limits")
```

---

## 🎯 **Production URL Structure**

Setelah deployment di Replit:

```
Main API: https://your-repl.replit.app
Health: https://your-repl.replit.app/health
Metrics: https://your-repl.replit.app/metrics
Docs: https://your-repl.replit.app/docs
GPT Actions: https://your-repl.replit.app/gpt/action-schema
```

---

## 📈 **Next Steps**

1. **Test deployment** dengan Replit environment
2. **Monitor performance** di production
3. **Optimize resource usage** untuk Replit limits
4. **Setup custom domain** (jika needed)
5. **Configure SSL** (auto oleh Replit)

**Sistem siap untuk production deployment di Replit dengan semua enhancements!** 🚀

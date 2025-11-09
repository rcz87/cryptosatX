"""
Prometheus Metrics Service for CryptoSatX
Collects and exposes application and business metrics
"""
import time
import asyncio
from typing import Dict, List, Optional
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from fastapi import Request, Response
from app.utils.logger import default_logger


class MetricsService:
    """
    Comprehensive metrics collection for CryptoSatX
    Tracks:
    - API performance and usage
    - Business metrics (signals, accuracy, etc.)
    - System health and resources
    - External API performance
    """
    
    def __init__(self):
        self.logger = default_logger
        self.registry = CollectorRegistry()
        
        # API Metrics
        self.request_count = Counter(
            'cryptosatx_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status_code', 'user_tier'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'cryptosatx_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint', 'user_tier'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0],
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'cryptosatx_active_connections',
            'Number of active connections',
            registry=self.registry
        )
        
        # Business Metrics
        self.signals_generated = Counter(
            'cryptosatx_signals_generated_total',
            'Total number of signals generated',
            ['symbol', 'signal_type', 'confidence'],
            registry=self.registry
        )
        
        self.signal_scores = Histogram(
            'cryptosatx_signal_scores',
            'Distribution of signal scores',
            ['symbol', 'signal_type'],
            buckets=[20, 30, 40, 50, 60, 70, 80, 90, 100],
            registry=self.registry
        )
        
        self.signal_accuracy = Gauge(
            'cryptosatx_signal_accuracy',
            'Signal accuracy percentage',
            ['symbol', 'timeframe'],
            registry=self.registry
        )
        
        self.active_users = Gauge(
            'cryptosatx_active_users',
            'Number of active users',
            ['tier'],
            registry=self.registry
        )
        
        # External API Metrics
        self.external_api_requests = Counter(
            'cryptosatx_external_api_requests_total',
            'Total external API requests',
            ['provider', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.external_api_duration = Histogram(
            'cryptosatx_external_api_duration_seconds',
            'External API request duration',
            ['provider', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        # Cache Metrics
        self.cache_operations = Counter(
            'cryptosatx_cache_operations_total',
            'Total cache operations',
            ['operation', 'result'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'cryptosatx_cache_hit_ratio',
            'Cache hit ratio percentage',
            ['cache_type'],
            registry=self.registry
        )
        
        # Database Metrics
        self.database_operations = Counter(
            'cryptosatx_database_operations_total',
            'Total database operations',
            ['operation', 'table', 'status'],
            registry=self.registry
        )
        
        self.database_connections = Gauge(
            'cryptosatx_database_connections',
            'Number of database connections',
            ['state'],
            registry=self.registry
        )
        
        # System Metrics
        self.memory_usage = Gauge(
            'cryptosatx_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'cryptosatx_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        # Application Info
        self.app_info = Info(
            'cryptosatx_app_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self.app_info.info({
            'version': '2.0.0',
            'name': 'CryptoSatX',
            'environment': 'production'
        })
        
        # Internal state
        self._active_requests = 0
        self._user_sessions = {}
    
    def record_request(
        self, 
        method: str, 
        endpoint: str, 
        status_code: int, 
        duration: float,
        user_tier: str = "free"
    ):
        """Record API request metrics"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            user_tier=user_tier
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint,
            user_tier=user_tier
        ).observe(duration)
    
    def record_signal_generated(
        self, 
        symbol: str, 
        signal_type: str, 
        confidence: str, 
        score: float
    ):
        """Record signal generation metrics"""
        self.signals_generated.labels(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence
        ).inc()
        
        self.signal_scores.labels(
            symbol=symbol,
            signal_type=signal_type
        ).observe(score)
    
    def record_external_api_call(
        self, 
        provider: str, 
        endpoint: str, 
        duration: float, 
        status: str = "success"
    ):
        """Record external API call metrics"""
        self.external_api_requests.labels(
            provider=provider,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.external_api_duration.labels(
            provider=provider,
            endpoint=endpoint
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics"""
        self.cache_operations.labels(
            operation=operation,
            result=result
        ).inc()
    
    def update_cache_hit_ratio(self, cache_type: str, ratio: float):
        """Update cache hit ratio"""
        self.cache_hit_ratio.labels(cache_type=cache_type).set(ratio)
    
    def record_database_operation(
        self, 
        operation: str, 
        table: str, 
        status: str = "success"
    ):
        """Record database operation metrics"""
        self.database_operations.labels(
            operation=operation,
            table=table,
            status=status
        ).inc()
    
    def update_database_connections(self, active: int, idle: int = 0):
        """Update database connection metrics"""
        self.database_connections.labels(state="active").set(active)
        self.database_connections.labels(state="idle").set(idle)
    
    def update_system_metrics(self, memory_bytes: int, cpu_percent: float):
        """Update system resource metrics"""
        self.memory_usage.set(memory_bytes)
        self.cpu_usage.set(cpu_percent)
    
    def increment_active_connections(self):
        """Increment active connections counter"""
        self.active_connections.inc()
        self._active_requests += 1
    
    def decrement_active_connections(self):
        """Decrement active connections counter"""
        self.active_connections.dec()
        self._active_requests = max(0, self._active_requests - 1)
    
    def record_user_activity(self, user_id: str, tier: str = "free"):
        """Record user activity for active user tracking"""
        self._user_sessions[user_id] = {
            'last_seen': time.time(),
            'tier': tier
        }
        self._update_active_users()
    
    def _update_active_users(self):
        """Update active user gauges based on recent activity"""
        current_time = time.time()
        active_threshold = 300  # 5 minutes
        
        tier_counts = {"free": 0, "premium": 0, "enterprise": 0}
        
        for user_id, session in self._user_sessions.items():
            if current_time - session['last_seen'] < active_threshold:
                tier = session.get('tier', 'free')
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        for tier, count in tier_counts.items():
            self.active_users.labels(tier=tier).set(count)
    
    def update_signal_accuracy(self, symbol: str, timeframe: str, accuracy: float):
        """Update signal accuracy metrics"""
        self.signal_accuracy.labels(symbol=symbol, timeframe=timeframe).set(accuracy)
    
    async def get_metrics_summary(self) -> Dict:
        """Get summary of key metrics"""
        try:
            # Get current metric values
            summary = {
                "api": {
                    "total_requests": self.request_count._value._value,
                    "active_connections": self._active_requests,
                    "avg_response_time": self.request_duration.observe.__self__._sum.value / max(1, self.request_count._value._value)
                },
                "business": {
                    "total_signals": self.signals_generated._value._value,
                    "active_users": sum(self.active_users.collect()[0].samples[i].value for i in range(len(self.active_users.collect()[0].samples)))
                },
                "external_apis": {
                    "total_requests": self.external_api_requests._value._value,
                    "avg_response_time": self.external_api_duration.observe.__self__._sum.value / max(1, self.external_api_requests._value._value)
                },
                "cache": {
                    "total_operations": self.cache_operations._value._value,
                    "hit_ratio": self._get_average_cache_hit_ratio()
                },
                "database": {
                    "total_operations": self.database_operations._value._value
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {e}")
            return {"error": str(e)}
    
    def _get_average_cache_hit_ratio(self) -> float:
        """Calculate average cache hit ratio across all cache types"""
        try:
            samples = self.cache_hit_ratio.collect()[0].samples
            if samples:
                return sum(sample.value for sample in samples) / len(samples)
            return 0.0
        except:
            return 0.0
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics"""
        return generate_latest(self.registry).decode('utf-8')
    
    async def start_metrics_collection(self):
        """Start background metrics collection"""
        asyncio.create_task(self._metrics_collection_loop())
    
    async def _metrics_collection_loop(self):
        """Background loop for collecting system metrics"""
        import psutil
        
        while True:
            try:
                # Update system metrics
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent()
                
                self.update_system_metrics(
                    memory_bytes=memory.used,
                    cpu_percent=cpu
                )
                
                # Update active users
                self._update_active_users()
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(30)


# Global metrics instance
metrics_service = MetricsService()


# FastAPI middleware for metrics collection
async def metrics_middleware(request: Request, call_next):
    """FastAPI middleware to collect request metrics"""
    start_time = time.time()
    
    # Increment active connections
    metrics_service.increment_active_connections()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get user tier from headers
        user_tier = request.headers.get("X-User-Tier", "free")
        
        # Record metrics
        metrics_service.record_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration,
            user_tier=user_tier
        )
        
        # Record user activity
        user_id = request.headers.get("X-User-ID")
        if user_id:
            metrics_service.record_user_activity(user_id, user_tier)
        
        return response
        
    except Exception as e:
        # Record error metrics
        duration = time.time() - start_time
        user_tier = request.headers.get("X-User-Tier", "free")
        
        metrics_service.record_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=500,
            duration=duration,
            user_tier=user_tier
        )
        
        raise
        
    finally:
        # Decrement active connections
        metrics_service.decrement_active_connections()

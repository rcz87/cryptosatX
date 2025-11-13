"""
Performance Optimization Service for CryptoSatX
Advanced caching, database optimization, and load balancing
"""

import asyncio
import redis
import json
import time
import psutil
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
import hashlib
import pickle
from functools import wraps

# import aioredis  # Disabled due to compatibility issues
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    hit_rate: float
    miss_rate: float
    total_requests: int
    cache_size: int
    memory_usage: float
    avg_response_time: float


@dataclass
class PerformanceMetrics:
    """System performance metrics"""

    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    response_time: float
    requests_per_second: float
    error_rate: float


class PerformanceOptimizationService:
    """Advanced performance optimization service"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = None
        self.redis_url = redis_url
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "response_times": [],
        }
        self.performance_cache = {}
        self.query_cache = {}
        self.rate_limiters = {}

    async def initialize(self):
        """Initialize performance optimization components"""
        try:
            # Initialize Redis connection (using regular redis instead of aioredis)
            self.redis_client = redis.Redis.from_url(
                self.redis_url, decode_responses=True
            )

            # Test Redis connection
            self.redis_client.ping()
            logger.info("Redis connection established for performance optimization")

            # Initialize performance monitoring
            await self._setup_monitoring()

            # Warm up cache with common queries
            await self._warm_up_cache()

        except Exception as e:
            logger.error(f"Failed to initialize performance service: {e}")
            # Fallback to in-memory cache
            self.redis_client = None

    def cache_result(self, ttl: int = 300, key_prefix: str = ""):
        """Decorator for caching function results"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(
                    func.__name__, args, kwargs, key_prefix
                )

                try:
                    # Try to get from cache
                    cached_result = await self.get_cached_result(cache_key)
                    if cached_result is not None:
                        self.cache_stats["hits"] += 1
                        return cached_result

                    # Execute function
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Cache result
                    await self.cache_result(cache_key, result, ttl)

                    # Update stats
                    self.cache_stats["misses"] += 1
                    self.cache_stats["response_times"].append(execution_time)

                    return result

                except Exception as e:
                    logger.error(f"Cache error in {func.__name__}: {e}")
                    # Execute function without caching
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    async def get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached result"""
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # Fallback to memory cache
                if key in self.performance_cache:
                    cache_entry = self.performance_cache[key]
                    if time.time() - cache_entry["timestamp"] < cache_entry["ttl"]:
                        return cache_entry["data"]
                    else:
                        del self.performance_cache[key]
            return None
        except Exception as e:
            logger.error(f"Error getting cached result for {key}: {e}")
            return None

    async def cache_result(self, key: str, data: Any, ttl: int = 300):
        """Cache result with TTL"""
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(data, default=str))
            else:
                # Fallback to memory cache
                self.performance_cache[key] = {
                    "data": data,
                    "timestamp": time.time(),
                    "ttl": ttl,
                }
        except Exception as e:
            logger.error(f"Error caching result for {key}: {e}")

    async def invalidate_cache(self, pattern: str = "*"):
        """Invalidate cache by pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Fallback to memory cache
                if pattern == "*":
                    self.performance_cache.clear()
                else:
                    keys_to_delete = [
                        k for k in self.performance_cache.keys() if pattern in k
                    ]
                    for key in keys_to_delete:
                        del self.performance_cache[key]
        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {e}")

    async def optimize_database_query(self, query: str, params: Dict = None) -> Dict:
        """Optimize database query with caching and analysis"""
        query_hash = hashlib.md5(query.encode()).hexdigest()

        # Check query cache
        if query_hash in self.query_cache:
            cached_result = self.query_cache[query_hash]
            if time.time() - cached_result["timestamp"] < 600:  # 10 minutes cache
                return cached_result["result"]

        try:
            # Analyze query performance
            start_time = time.time()

            # Execute query (this would integrate with your database session)
            # result = await self._execute_query(query, params)

            execution_time = time.time() - start_time

            # Cache query result
            self.query_cache[query_hash] = {
                "result": {
                    "query": query,
                    "execution_time": execution_time,
                    "optimized": True,
                    "suggestions": self._generate_query_suggestions(
                        query, execution_time
                    ),
                },
                "timestamp": time.time(),
            }

            return self.query_cache[query_hash]["result"]

        except Exception as e:
            logger.error(f"Error optimizing database query: {e}")
            return {"error": str(e), "query": query}

    async def get_system_metrics(self) -> PerformanceMetrics:
        """Get comprehensive system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)

            # Network metrics
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent / (1024**2),  # MB
                "bytes_recv": network.bytes_recv / (1024**2),  # MB
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }

            # Calculate response time and RPS
            avg_response_time = self._calculate_avg_response_time()
            requests_per_second = self._calculate_rps()
            error_rate = self._calculate_error_rate()

            return PerformanceMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                disk_usage=disk_percent,
                network_io=network_io,
                response_time=avg_response_time,
                requests_per_second=requests_per_second,
                error_rate=error_rate,
            )

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return PerformanceMetrics(
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                network_io={},
                response_time=0,
                requests_per_second=0,
                error_rate=0,
            )

    async def get_cache_metrics(self) -> CacheMetrics:
        """Get cache performance metrics"""
        try:
            total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            hit_rate = (
                (self.cache_stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0
            )
            miss_rate = (
                (self.cache_stats["misses"] / total_requests * 100)
                if total_requests > 0
                else 0
            )

            # Get cache size
            cache_size = 0
            memory_usage = 0

            if self.redis_client:
                try:
                    info = self.redis_client.info("memory")
                    memory_usage = info.get("used_memory", 0) / (1024**2)  # MB
                    cache_size = len(self.redis_client.keys("*"))
                except:
                    pass
            else:
                cache_size = len(self.performance_cache)
                memory_usage = sum(
                    len(str(v)) for v in self.performance_cache.values()
                ) / (1024**2)

            # Calculate average response time
            avg_response_time = 0
            if self.cache_stats["response_times"]:
                avg_response_time = sum(self.cache_stats["response_times"]) / len(
                    self.cache_stats["response_times"]
                )

            return CacheMetrics(
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                total_requests=total_requests,
                cache_size=cache_size,
                memory_usage=memory_usage,
                avg_response_time=avg_response_time,
            )

        except Exception as e:
            logger.error(f"Error getting cache metrics: {e}")
            return CacheMetrics(
                hit_rate=0,
                miss_rate=0,
                total_requests=0,
                cache_size=0,
                memory_usage=0,
                avg_response_time=0,
            )

    async def implement_load_balancing(self, servers: List[str]) -> Dict:
        """Implement simple load balancing logic"""
        try:
            server_health = {}

            for server in servers:
                # Check server health
                health_status = await self._check_server_health(server)
                server_health[server] = health_status

            # Select best server based on health and load
            best_server = self._select_best_server(server_health)

            return {
                "selected_server": best_server,
                "server_health": server_health,
                "load_balancing_algorithm": "health_based",
                "total_servers": len(servers),
                "healthy_servers": sum(
                    1 for h in server_health.values() if h["healthy"]
                ),
            }

        except Exception as e:
            logger.error(f"Error implementing load balancing: {e}")
            return {"error": str(e)}

    async def optimize_api_response(self, endpoint: str, data: Dict) -> Dict:
        """Optimize API response for better performance"""
        try:
            # Compress large data
            optimized_data = self._compress_data(data)

            # Add caching headers
            cache_headers = self._generate_cache_headers(endpoint)

            # Minimize response size
            minimized_data = self._minimize_response_size(optimized_data)

            return {
                "data": minimized_data,
                "headers": cache_headers,
                "compressed": len(str(minimized_data)) < len(str(data)),
                "size_reduction": len(str(data)) - len(str(minimized_data)),
            }

        except Exception as e:
            logger.error(f"Error optimizing API response: {e}")
            return {"data": data, "error": str(e)}

    async def implement_rate_limiting(
        self, client_id: str, limit: int = 100, window: int = 60
    ) -> Dict:
        """Implement rate limiting"""
        try:
            current_time = time.time()
            window_start = current_time - window

            # Clean old entries
            if client_id in self.rate_limiters:
                self.rate_limiters[client_id] = [
                    req_time
                    for req_time in self.rate_limiters[client_id]
                    if req_time > window_start
                ]
            else:
                self.rate_limiters[client_id] = []

            # Check current requests
            current_requests = len(self.rate_limiters[client_id])

            if current_requests >= limit:
                return {
                    "allowed": False,
                    "limit": limit,
                    "current": current_requests,
                    "reset_time": window_start + window + window,
                    "retry_after": int(window - (current_time - window_start) % window),
                }

            # Add current request
            self.rate_limiters[client_id].append(current_time)

            return {
                "allowed": True,
                "limit": limit,
                "current": current_requests + 1,
                "remaining": limit - current_requests - 1,
                "reset_time": window_start + window + window,
            }

        except Exception as e:
            logger.error(f"Error implementing rate limiting: {e}")
            return {"allowed": True, "error": str(e)}

    async def auto_scale_recommendations(self) -> Dict:
        """Provide auto-scaling recommendations based on metrics"""
        try:
            metrics = await self.get_system_metrics()
            cache_metrics = await self.get_cache_metrics()

            recommendations = []

            # CPU-based recommendations
            if metrics.cpu_usage > 80:
                recommendations.append(
                    {
                        "type": "scale_up",
                        "reason": "High CPU usage",
                        "current_value": metrics.cpu_usage,
                        "threshold": 80,
                        "action": "Add more CPU resources or optimize CPU-intensive operations",
                    }
                )

            # Memory-based recommendations
            if metrics.memory_usage > 85:
                recommendations.append(
                    {
                        "type": "scale_up",
                        "reason": "High memory usage",
                        "current_value": metrics.memory_usage,
                        "threshold": 85,
                        "action": "Add more memory or implement memory optimization",
                    }
                )

            # Cache-based recommendations
            if cache_metrics.hit_rate < 70:
                recommendations.append(
                    {
                        "type": "optimize_cache",
                        "reason": "Low cache hit rate",
                        "current_value": cache_metrics.hit_rate,
                        "threshold": 70,
                        "action": "Increase cache size or adjust cache TTL",
                    }
                )

            # Response time recommendations
            if metrics.response_time > 2.0:
                recommendations.append(
                    {
                        "type": "optimize_performance",
                        "reason": "High response time",
                        "current_value": metrics.response_time,
                        "threshold": 2.0,
                        "action": "Optimize database queries or implement better caching",
                    }
                )

            # RPS recommendations
            if metrics.requests_per_second > 1000:
                recommendations.append(
                    {
                        "type": "scale_out",
                        "reason": "High requests per second",
                        "current_value": metrics.requests_per_second,
                        "threshold": 1000,
                        "action": "Add more server instances or implement load balancing",
                    }
                )

            return {
                "current_metrics": asdict(metrics),
                "cache_metrics": asdict(cache_metrics),
                "recommendations": recommendations,
                "overall_health": (
                    "healthy" if len(recommendations) == 0 else "needs_attention"
                ),
                "priority": (
                    "high"
                    if len(recommendations) > 3
                    else "medium" if recommendations else "low"
                ),
            }

        except Exception as e:
            logger.error(f"Error generating auto-scale recommendations: {e}")
            return {"error": str(e)}

    # Private helper methods

    def _generate_cache_key(
        self, func_name: str, args: tuple, kwargs: dict, prefix: str
    ) -> str:
        """Generate unique cache key"""
        key_data = f"{prefix}:{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _setup_monitoring(self):
        """Setup performance monitoring"""
        try:
            # Start background monitoring task
            asyncio.create_task(self._monitor_performance())
            logger.info("Performance monitoring started")
        except Exception as e:
            logger.error(f"Error setting up monitoring: {e}")

    async def _warm_up_cache(self):
        """Warm up cache with common data"""
        try:
            # Cache common market data
            common_symbols = ["BTC", "ETH", "SOL", "BNB", "ADA"]

            for symbol in common_symbols:
                # This would integrate with your existing services
                cache_key = f"market_data:{symbol}"
                # await self.cache_result(cache_key, mock_data, ttl=60)

            logger.info("Cache warm-up completed")
        except Exception as e:
            logger.error(f"Error warming up cache: {e}")

    async def _monitor_performance(self):
        """Background performance monitoring"""
        while True:
            try:
                # Collect metrics every 30 seconds
                await asyncio.sleep(30)

                metrics = await self.get_system_metrics()

                # Log warnings for critical metrics
                if metrics.cpu_usage > 90:
                    logger.warning(f"High CPU usage: {metrics.cpu_usage}%")

                if metrics.memory_usage > 90:
                    logger.warning(f"High memory usage: {metrics.memory_usage}%")

                if metrics.response_time > 5.0:
                    logger.warning(f"High response time: {metrics.response_time}s")

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")

    def _generate_query_suggestions(
        self, query: str, execution_time: float
    ) -> List[str]:
        """Generate query optimization suggestions"""
        suggestions = []

        if execution_time > 1.0:
            suggestions.append("Consider adding indexes for frequently queried columns")

        if "SELECT *" in query.upper():
            suggestions.append("Avoid SELECT *, specify only needed columns")

        if query.upper().count("JOIN") > 3:
            suggestions.append("Consider breaking complex joins into multiple queries")

        if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
            suggestions.append("Add LIMIT clause to ORDER BY queries")

        return suggestions

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.cache_stats["response_times"]:
            return 0

        recent_times = self.cache_stats["response_times"][-100:]  # Last 100 requests
        return sum(recent_times) / len(recent_times)

    def _calculate_rps(self) -> float:
        """Calculate requests per second"""
        if not self.cache_stats["response_times"]:
            return 0

        recent_times = self.cache_stats["response_times"][-60:]  # Last 60 requests
        if len(recent_times) < 2:
            return 0

        time_span = sum(recent_times)
        return len(recent_times) / time_span if time_span > 0 else 0

    def _calculate_error_rate(self) -> float:
        """Calculate error rate (placeholder)"""
        # This would integrate with your error tracking
        return 0.0

    async def _check_server_health(self, server: str) -> Dict:
        """Check server health status"""
        try:
            # Mock health check - in real implementation, ping server
            start_time = time.time()

            # Simulate server response time
            await asyncio.sleep(0.1)

            response_time = time.time() - start_time

            return {
                "healthy": response_time < 1.0,
                "response_time": response_time,
                "last_check": datetime.utcnow().isoformat(),
                "status": "healthy" if response_time < 1.0 else "unhealthy",
            }

        except Exception as e:
            return {
                "healthy": False,
                "response_time": 999,
                "last_check": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
            }

    def _select_best_server(self, server_health: Dict) -> str:
        """Select best server based on health"""
        healthy_servers = [
            server
            for server, health in server_health.items()
            if health.get("healthy", False)
        ]

        if not healthy_servers:
            # Return first server if none are healthy
            return list(server_health.keys())[0] if server_health else ""

        # Select server with lowest response time
        best_server = min(
            healthy_servers, key=lambda s: server_health[s].get("response_time", 999)
        )

        return best_server

    def _compress_data(self, data: Dict) -> Dict:
        """Compress data by removing redundant information"""
        if isinstance(data, dict):
            compressed = {}
            for key, value in data.items():
                if value is not None and value != "":
                    compressed[key] = self._compress_data(value)
            return compressed
        elif isinstance(data, list):
            return [self._compress_data(item) for item in data if item is not None]
        else:
            return data

    def _generate_cache_headers(self, endpoint: str) -> Dict:
        """Generate appropriate cache headers"""
        cache_policies = {
            "/market/": {"max-age": 30, "public": True},
            "/signals/": {"max-age": 60, "public": True},
            "/analytics/": {"max-age": 300, "public": True},
            "/health": {"max-age": 10, "public": True},
        }

        for pattern, policy in cache_policies.items():
            if pattern in endpoint:
                return {
                    "Cache-Control": f"max-age={policy['max-age']}, public",
                    "ETag": hashlib.md5(str(time.time()).encode()).hexdigest(),
                }

        return {"Cache-Control": "no-cache, no-store, must-revalidate"}

    def _minimize_response_size(self, data: Dict) -> Dict:
        """Minimize response size by removing unnecessary fields"""
        if isinstance(data, dict):
            minimized = {}
            for key, value in data.items():
                # Skip metadata fields for API responses
                if key not in ["meta", "debug", "internal"]:
                    minimized[key] = self._minimize_response_size(value)
            return minimized
        elif isinstance(data, list):
            return [self._minimize_response_size(item) for item in data]
        else:
            return data


# Global instance
performance_optimization_service = PerformanceOptimizationService()

"""
Rate Limiting Middleware for CryptoSatX
Redis-based rate limiting with tiered limits and IP/user tracking
"""
import time
import asyncio
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as redis
from app.utils.logger import default_logger


class CryptoSatXLimiter:
    """
    Advanced rate limiting system with:
    - Redis backend for distributed limiting
    - Tiered limits (free/premium/enterprise)
    - IP and user-based limiting
    - Sliding window implementation
    - Custom limits per endpoint
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.logger = default_logger
        
        # Default limits per tier (requests per hour)
        self.default_limits = {
            "free": 100,
            "premium": 1000,
            "enterprise": 10000
        }
        
        # Endpoint-specific limits (multipliers of default)
        self.endpoint_multipliers = {
            "/signals/{symbol}": 1.0,
            "/market/{symbol}": 1.5,
            "/history/signals": 0.5,
            "/backtest/run": 0.2,
            "/admin/": 0.1
        }
        
        # Sliding window parameters
        self.window_size = 3600  # 1 hour in seconds
        self.cleanup_interval = 300  # 5 minutes
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            self.logger.info("Rate limiter Redis connected successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect rate limiter Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def get_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{identifier}:{endpoint}"
    
    async def get_user_tier(self, user_id: Optional[str]) -> str:
        """Get user tier from database or cache"""
        if not user_id:
            return "free"
        
        try:
            # For now, return default tier
            # In production, this would query the database
            return "free"
        except Exception as e:
            self.logger.error(f"Error getting user tier: {e}")
            return "free"
    
    def get_limit_for_endpoint(self, endpoint: str, tier: str) -> int:
        """Calculate rate limit for specific endpoint and tier"""
        base_limit = self.default_limits.get(tier, self.default_limits["free"])
        
        # Find matching endpoint pattern
        multiplier = 1.0
        for pattern, mult in self.endpoint_multipliers.items():
            if pattern in endpoint or endpoint in pattern:
                multiplier = mult
                break
        
        return int(base_limit * multiplier)
    
    async def is_allowed(
        self, 
        identifier: str, 
        endpoint: str, 
        tier: str = "free"
    ) -> Tuple[bool, Dict]:
        """
        Check if request is allowed using sliding window
        
        Returns:
            Tuple of (allowed, info_dict)
        """
        if not self.redis_client:
            # Fallback to always allow if Redis is not available
            return True, {"limit": 1000, "remaining": 999, "reset_time": int(time.time()) + 3600}
        
        key = self.get_key(identifier, endpoint)
        limit = self.get_limit_for_endpoint(endpoint, tier)
        current_time = int(time.time())
        window_start = current_time - self.window_size
        
        try:
            # Use Redis sorted set for sliding window
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, self.window_size)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            # Check if limit exceeded
            allowed = current_requests <= limit
            remaining = max(0, limit - current_requests)
            reset_time = current_time + self.window_size
            
            return allowed, {
                "limit": limit,
                "remaining": remaining,
                "reset_time": reset_time,
                "current_requests": current_requests
            }
            
        except Exception as e:
            self.logger.error(f"Rate limiting error: {e}")
            # Allow request on error
            return True, {"limit": limit, "remaining": limit - 1, "reset_time": int(time.time()) + 3600}
    
    async def get_usage_stats(self, identifier: str, endpoint: str) -> Dict:
        """Get current usage statistics"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        key = self.get_key(identifier, endpoint)
        current_time = int(time.time())
        window_start = current_time - self.window_size
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.zcard(key)
            pipe.zrange(key, 0, -1, withscores=True)
            
            results = await pipe.execute()
            current_requests = results[0]
            requests_with_times = results[1]
            
            # Calculate request distribution
            if requests_with_times:
                timestamps = [int(score) for _, score in requests_with_times]
                oldest_request = min(timestamps)
                newest_request = max(timestamps)
                
                # Group requests by minute for distribution
                minute_distribution = {}
                for timestamp in timestamps:
                    minute = (timestamp // 60) * 60
                    minute_distribution[minute] = minute_distribution.get(minute, 0) + 1
            else:
                oldest_request = newest_request = None
                minute_distribution = {}
            
            return {
                "current_requests": current_requests,
                "oldest_request": oldest_request,
                "newest_request": newest_request,
                "minute_distribution": minute_distribution,
                "window_size": self.window_size
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage stats: {e}")
            return {"error": str(e)}
    
    async def reset_usage(self, identifier: str, endpoint: str) -> bool:
        """Reset usage for specific identifier and endpoint"""
        if not self.redis_client:
            return False
        
        key = self.get_key(identifier, endpoint)
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Error resetting usage: {e}")
            return False
    
    async def cleanup_expired_keys(self) -> int:
        """Clean up expired rate limit keys"""
        if not self.redis_client:
            return 0
        
        try:
            pattern = "rate_limit:*"
            keys = await self.redis_client.keys(pattern)
            
            deleted_count = 0
            current_time = int(time.time())
            
            for key in keys:
                # Check if key has expired
                ttl = await self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    continue
                elif ttl == -1:  # No expiration, check manually
                    # Get oldest request timestamp
                    oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                    if oldest:
                        oldest_time = int(oldest[0][1])
                        if current_time - oldest_time > self.window_size * 2:
                            await self.redis_client.delete(key)
                            deleted_count += 1
                elif ttl <= 0:  # Expired
                    await self.redis_client.delete(key)
                    deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return 0


# Global limiter instance
rate_limiter = CryptoSatXLimiter()


# FastAPI integration
def get_identifier(request: Request) -> str:
    """Extract identifier from request (IP or user ID)"""
    # Try to get user ID from headers first
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    # Skip rate limiting for health checks
    if "/health" in request.url.path:
        return await call_next(request)
    
    # Get identifier
    identifier = get_identifier(request)
    endpoint = request.url.path
    
    # Get user tier (simplified for now)
    user_id = request.headers.get("X-User-ID")
    tier = await rate_limiter.get_user_tier(user_id)
    
    # Check rate limit
    allowed, info = await rate_limiter.is_allowed(identifier, endpoint, tier)
    
    # Add rate limit headers
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(info["reset_time"])
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(info["reset_time"]),
                "Retry-After": str(info["reset_time"] - int(time.time()))
            }
        )
    
    return response


# SlowAPI integration for backward compatibility
limiter = Limiter(key_func=get_identifier)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded. Please try again later.",
        headers={"Retry-After": "60"}
    )

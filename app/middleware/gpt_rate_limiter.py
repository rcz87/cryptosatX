"""
Enhanced Rate Limiting for GPT Actions
Provides separate rate limits for GPT Actions endpoints to prevent abuse
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Dict, Tuple
import time
from collections import defaultdict
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GPTRateLimiter:
    """
    Advanced rate limiter for GPT Actions endpoints

    Features:
    - Per-endpoint rate limits
    - Per-IP rate limits
    - Sliding window algorithm
    - Configurable limits for production
    """

    def __init__(self):
        self.request_history: Dict[Tuple[str, str], list] = defaultdict(list)

        self.endpoint_limits = {
            "/gpt/signal": (30, 60),
            "/gpt/smart-money-scan": (10, 60),
            "/gpt/mss-discover": (10, 60),
            "/gpt/health": (60, 60),
            "/scalping/quick/*": (20, 60),
            "/scalping/analyze": (10, 60),
            "/invoke": (30, 60),
            "/analytics/*": (60, 60),
            "default": (100, 60)
        }

        self.global_limit = (200, 60)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def _get_endpoint_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for endpoint"""
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]

        for pattern, limit in self.endpoint_limits.items():
            if "*" in pattern:
                prefix = pattern.split("*")[0]
                if path.startswith(prefix):
                    return limit

        return self.endpoint_limits["default"]

    def _clean_old_requests(self, timestamps: list, window: int) -> list:
        """Remove timestamps outside the time window"""
        current_time = time.time()
        cutoff_time = current_time - window
        return [ts for ts in timestamps if ts > cutoff_time]

    def check_rate_limit(self, request: Request) -> Tuple[bool, dict]:
        """
        Check if request is within rate limits

        Returns:
            (allowed, info_dict)
        """
        ip = self._get_client_ip(request)
        path = request.url.path
        current_time = time.time()

        max_requests, window = self._get_endpoint_limit(path)

        key = (ip, path)
        self.request_history[key] = self._clean_old_requests(
            self.request_history[key],
            window
        )

        request_count = len(self.request_history[key])

        if request_count >= max_requests:
            return False, {
                "allowed": False,
                "limit": max_requests,
                "window_seconds": window,
                "current_count": request_count,
                "retry_after": window,
                "message": f"Rate limit exceeded for {path}. Max {max_requests} requests per {window}s."
            }

        global_key = (ip, "global")
        self.request_history[global_key] = self._clean_old_requests(
            self.request_history[global_key],
            self.global_limit[1]
        )

        global_count = len(self.request_history[global_key])

        if global_count >= self.global_limit[0]:
            return False, {
                "allowed": False,
                "limit": self.global_limit[0],
                "window_seconds": self.global_limit[1],
                "current_count": global_count,
                "retry_after": self.global_limit[1],
                "message": f"Global rate limit exceeded. Max {self.global_limit[0]} requests per {self.global_limit[1]}s."
            }

        self.request_history[key].append(current_time)
        self.request_history[global_key].append(current_time)

        remaining = max_requests - (request_count + 1)

        return True, {
            "allowed": True,
            "limit": max_requests,
            "window_seconds": window,
            "current_count": request_count + 1,
            "remaining": remaining,
            "reset_in": window
        }

    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        current_time = time.time()

        active_clients = set()
        endpoint_usage = defaultdict(int)

        for (ip, endpoint), timestamps in self.request_history.items():
            if endpoint != "global":
                recent = [ts for ts in timestamps if ts > current_time - 60]
                if recent:
                    active_clients.add(ip)
                    endpoint_usage[endpoint] += len(recent)

        return {
            "active_clients_last_minute": len(active_clients),
            "endpoint_usage_last_minute": dict(endpoint_usage),
            "total_tracked_keys": len(self.request_history),
            "limits": self.endpoint_limits
        }

class GPTRateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to GPT Actions endpoints"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.limiter = GPTRateLimiter()

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting"""

        allowed, info = self.limiter.check_rate_limit(request)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "ip": self.limiter._get_client_ip(request),
                    "endpoint": request.url.path,
                    "limit": info["limit"],
                    "window": info["window_seconds"]
                }
            )

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": info["message"],
                    "retry_after_seconds": info["retry_after"]
                },
                headers={
                    "Retry-After": str(info["retry_after"]),
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Window": str(info["window_seconds"])
                }
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        response.headers["X-RateLimit-Window"] = str(info["window_seconds"])

        return response

gpt_rate_limiter = GPTRateLimiter()

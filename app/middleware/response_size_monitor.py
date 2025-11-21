"""
Response Size Monitoring Middleware - FIXED for Streaming Support
Monitors response sizes for GPT Actions compatibility (50KB limit)
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from starlette.types import ASGIApp
from typing import Callable
import time
from app.utils.logger import get_logger

logger = get_logger(__name__)

GPT_ACTIONS_LIMIT_BYTES = 50 * 1024
WARNING_THRESHOLD_BYTES = 40 * 1024

class ResponseSizeMonitorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor response sizes and warn about GPT Actions compatibility
    
    ✅ FIXED: Properly handles streaming responses without exhausting iterators
    
    Features:
    - Tracks response sizes for all endpoints
    - Warns when responses approach 50KB limit
    - Logs statistics for monitoring
    - Adds custom headers with size information
    - Preserves streaming capability (no iterator exhaustion)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.large_responses_count = 0
        self.total_requests = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and monitor response size - STREAMING SAFE"""

        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000

        # Handle StreamingResponse (like JSONResponse) properly
        if isinstance(response, StreamingResponse):
            original_body_iterator = response.body_iterator
            size = 0

            async def wrapped_body_iterator():
                nonlocal size
                async for chunk in original_body_iterator:
                    size += len(chunk)
                    yield chunk
                
                # Log after streaming completes
                response_size_kb = size / 1024
                
                if size > GPT_ACTIONS_LIMIT_BYTES:
                    logger.warning(
                        f"⚠️  Response size exceeds GPT Actions limit!",
                        extra={
                            "endpoint": str(request.url.path),
                            "method": request.method,
                            "size_bytes": size,
                            "size_kb": round(response_size_kb, 2),
                            "limit_kb": 50,
                            "exceeded_by_kb": round(response_size_kb - 50, 2)
                        }
                    )
                elif size > WARNING_THRESHOLD_BYTES:
                    logger.info(
                        f"ℹ️  Response approaching GPT Actions limit",
                        extra={
                            "endpoint": str(request.url.path),
                            "method": request.method,
                            "size_bytes": size,
                            "size_kb": round(response_size_kb, 2),
                            "threshold_percent": round((size / GPT_ACTIONS_LIMIT_BYTES) * 100, 1)
                        }
                    )
                
                # Record stats
                response_size_stats.record_response(str(request.url.path), size)

            # Replace iterator with wrapped version
            response.body_iterator = wrapped_body_iterator()
            
            # Add headers (approximation before full size known)
            response.headers["X-Response-Type"] = "streaming"
            response.headers["X-Response-Time-Ms"] = f"{process_time:.2f}"
            
            return response

        # Handle non-streaming responses
        if hasattr(response, "body"):
            response_body = response.body
            response_size = len(response_body)
            response_size_kb = response_size / 1024

            self.total_requests += 1

            if response_size > WARNING_THRESHOLD_BYTES:
                self.large_responses_count += 1

                if response_size > GPT_ACTIONS_LIMIT_BYTES:
                    logger.warning(
                        f"⚠️  Response size exceeds GPT Actions limit!",
                        extra={
                            "endpoint": str(request.url.path),
                            "method": request.method,
                            "size_bytes": response_size,
                            "size_kb": round(response_size_kb, 2),
                            "limit_kb": 50,
                            "exceeded_by_kb": round(response_size_kb - 50, 2)
                        }
                    )
                else:
                    logger.info(
                        f"ℹ️  Response approaching GPT Actions limit",
                        extra={
                            "endpoint": str(request.url.path),
                            "method": request.method,
                            "size_bytes": response_size,
                            "size_kb": round(response_size_kb, 2),
                            "threshold_percent": round((response_size / GPT_ACTIONS_LIMIT_BYTES) * 100, 1)
                        }
                    )

            response.headers["X-Response-Size-Bytes"] = str(response_size)
            response.headers["X-Response-Size-KB"] = f"{response_size_kb:.2f}"
            response.headers["X-GPT-Actions-Compatible"] = "true" if response_size <= GPT_ACTIONS_LIMIT_BYTES else "false"
            response.headers["X-Response-Time-Ms"] = f"{process_time:.2f}"

            if response_size > GPT_ACTIONS_LIMIT_BYTES:
                response.headers["X-GPT-Actions-Warning"] = f"Response size ({response_size_kb:.2f}KB) exceeds 50KB limit"

            response_size_stats.record_response(str(request.url.path), response_size)

        return response


class ResponseSizeStats:
    """Global statistics tracker for response sizes"""

    def __init__(self):
        self.total_requests = 0
        self.large_responses = 0
        self.exceeded_limit = 0
        self.endpoint_stats = {}

    def record_response(self, endpoint: str, size_bytes: int):
        """Record response size for an endpoint"""
        self.total_requests += 1

        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                "count": 0,
                "total_size": 0,
                "max_size": 0,
                "min_size": float('inf'),
                "exceeded_count": 0
            }

        stats = self.endpoint_stats[endpoint]
        stats["count"] += 1
        stats["total_size"] += size_bytes
        stats["max_size"] = max(stats["max_size"], size_bytes)
        stats["min_size"] = min(stats["min_size"], size_bytes)

        if size_bytes > GPT_ACTIONS_LIMIT_BYTES:
            stats["exceeded_count"] += 1
            self.exceeded_limit += 1

        if size_bytes > WARNING_THRESHOLD_BYTES:
            self.large_responses += 1

    def get_stats(self):
        """Get formatted statistics"""
        if self.total_requests == 0:
            return {
                "total_requests": 0,
                "message": "No requests recorded yet"
            }

        return {
            "total_requests": self.total_requests,
            "large_responses": self.large_responses,
            "exceeded_limit": self.exceeded_limit,
            "compliance_rate": round((1 - (self.exceeded_limit / self.total_requests)) * 100, 2),
            "endpoint_stats": {
                endpoint: {
                    **stats,
                    "avg_size_kb": round((stats["total_size"] / stats["count"]) / 1024, 2),
                    "max_size_kb": round(stats["max_size"] / 1024, 2),
                    "min_size_kb": round(stats["min_size"] / 1024, 2) if stats["min_size"] != float('inf') else 0,
                    "compliance_rate": round((1 - (stats["exceeded_count"] / stats["count"])) * 100, 2)
                }
                for endpoint, stats in self.endpoint_stats.items()
            }
        }

    def get_problematic_endpoints(self):
        """Get list of endpoints that frequently exceed size limit"""
        problematic = []

        for endpoint, stats in self.endpoint_stats.items():
            if stats["exceeded_count"] > 0:
                problematic.append({
                    "endpoint": endpoint,
                    "exceeded_count": stats["exceeded_count"],
                    "total_count": stats["count"],
                    "exceed_rate": round((stats["exceeded_count"] / stats["count"]) * 100, 2),
                    "max_size_kb": round(stats["max_size"] / 1024, 2),
                    "avg_size_kb": round((stats["total_size"] / stats["count"]) / 1024, 2)
                })

        problematic.sort(key=lambda x: x["exceed_rate"], reverse=True)

        return problematic

response_size_stats = ResponseSizeStats()

"""
Request Logging Middleware
Detailed logging for all HTTP requests including ChatGPT/GPT Actions calls
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive
from typing import Callable, Dict, Any
import time
import json
import logging
from app.utils.logger import get_logger, get_wib_time

logger = get_logger(__name__)

SENSITIVE_FIELDS = {
    "api_key", "apikey", "password", "passwd", "secret", "token", 
    "authorization", "auth", "api-key", "access_token", "refresh_token",
    "client_secret", "private_key", "credentials"
}


def redact_sensitive_data(data: Any) -> Any:
    """
    Recursively redact sensitive fields from data
    
    Args:
        data: Dictionary, list, or primitive value
        
    Returns:
        Data with sensitive fields redacted
    """
    if isinstance(data, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_FIELDS else redact_sensitive_data(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    else:
        return data


class DetailedRequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log detailed information about all HTTP requests
    
    Features:
    - Logs every HTTP request with full details
    - Captures request method, path, query params, body
    - Records response status and duration
    - Includes client IP and user agent
    - Uses WIB timezone for timestamps
    - Optimized for debugging ChatGPT/GPT Actions integration
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process and log request details"""
        
        self.request_count += 1
        request_id = self.request_count
        
        start_time = time.time()
        
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        query_params = dict(request.query_params) if request.query_params else {}
        
        request_body = None
        body_bytes = b""
        
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        parsed_body = json.loads(body_bytes.decode())
                        request_body = redact_sensitive_data(parsed_body)
                    except:
                        request_body = body_bytes.decode()[:500]
            except:
                request_body = "Unable to read body"
            
            async def receive() -> dict:
                return {"type": "http.request", "body": body_bytes}
            
            request._receive = receive
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_data = {
                "request_id": request_id,
                "timestamp": get_wib_time(),
                "method": request.method,
                "endpoint": str(request.url.path),
                "client_ip": client_ip,
                "error": str(e),
            }
            log_record = logger.makeRecord(
                logger.name,
                logging.ERROR,
                "",
                0,
                f"❌ Request failed with exception",
                (),
                None
            )
            setattr(log_record, "extra_data", error_data)
            logger.handle(log_record)
            raise
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        redacted_query_params = redact_sensitive_data(query_params) if query_params else None
        
        log_data = {
            "request_id": request_id,
            "timestamp": get_wib_time(),
            "method": request.method,
            "endpoint": str(request.url.path),
            "query_params": redacted_query_params,
            "request_body": request_body,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }
        
        log_level = "info"
        log_emoji = "✅"
        
        if status_code >= 500:
            log_level = "error"
            log_emoji = "❌"
        elif status_code >= 400:
            log_level = "warning"
            log_emoji = "⚠️"
        elif status_code >= 300:
            log_level = "info"
            log_emoji = "↩️"
        
        log_message = f"{log_emoji} {request.method} {request.url.path} → {status_code} ({duration_ms}ms)"
        
        level_map = {
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
        }
        
        log_record = logger.makeRecord(
            logger.name,
            level_map[log_level],
            "",
            0,
            log_message,
            (),
            None
        )
        setattr(log_record, "extra_data", log_data)
        logger.handle(log_record)
        
        return response


class CompactRequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Compact version of request logger - logs only essential info
    Use this if detailed logging is too verbose
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        logger.info(
            f"🌐 {request.method} {request.url.path}",
            extra={
                "timestamp": get_wib_time(),
                "method": request.method,
                "endpoint": str(request.url.path),
                "status": response.status_code,
                "duration_ms": duration_ms,
            }
        )
        
        return response

"""
Unified Error Handler
=====================

Consistent error handling dan fallback behavior across all services.

Problem:
- Different services return different error formats
- Inconsistent fallback behaviors
- Hard to debug cascading failures

Solution:
- Standard error response format
- Categorized error types (transient vs permanent)
- Consistent fallback strategies
- Error context tracking

Author: CryptoSatX Intelligence Engine
Version: 1.0.0
"""

from typing import Dict, Any, Optional, Literal, Callable, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
from app.utils.logger import logger


class ErrorCategory(str, Enum):
    """Error categories untuk consistent handling"""

    # Transient errors (retry-able)
    NETWORK_ERROR = "network_error"  # HTTP timeouts, connection errors
    RATE_LIMIT = "rate_limit"  # HTTP 429, API quota exceeded
    SERVICE_UNAVAILABLE = "service_unavailable"  # HTTP 503, temporary outage

    # Permanent errors (not retry-able)
    INVALID_INPUT = "invalid_input"  # Bad symbol, invalid parameters
    AUTHENTICATION = "authentication"  # API key invalid, unauthorized
    NOT_FOUND = "not_found"  # Symbol not found, endpoint not found
    QUOTA_EXCEEDED = "quota_exceeded"  # Monthly/daily quota exceeded

    # Data errors
    NO_DATA = "no_data"  # Service returned empty data
    INVALID_DATA = "invalid_data"  # Service returned malformed data
    STALE_DATA = "stale_data"  # Data too old to be useful

    # Internal errors
    CALCULATION_ERROR = "calculation_error"  # Math errors, logic errors
    CACHE_ERROR = "cache_error"  # Cache read/write failed
    DATABASE_ERROR = "database_error"  # DB operation failed

    # Unknown
    UNKNOWN = "unknown"


class FallbackStrategy(str, Enum):
    """Fallback strategies untuk different error types"""

    # Return specific values
    RETURN_NEUTRAL = "return_neutral"  # Return neutral/default value
    RETURN_CACHED = "return_cached"  # Return stale cache if available
    RETURN_ERROR = "return_error"  # Return error response

    # Skip/Continue
    SKIP_SERVICE = "skip_service"  # Skip this service, continue with others
    CONTINUE_PARTIAL = "continue_partial"  # Continue with partial data

    # Retry
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry with exponential backoff
    RETRY_ALTERNATE = "retry_alternate"  # Try alternate data source

    # Abort
    ABORT = "abort"  # Abort entire operation


@dataclass
class ErrorResponse:
    """
    Standard error response format untuk all services.

    Konsisten format makes error handling easier dan debugging faster.
    """

    # Error identification
    success: bool = False
    error_category: ErrorCategory
    error_message: str
    error_code: Optional[str] = None  # e.g., "HTTP_429", "INVALID_SYMBOL"

    # Context
    service_name: str  # Which service generated error
    operation: str  # What operation failed
    symbol: Optional[str] = None  # Crypto symbol if applicable

    # Metadata
    timestamp: str = None
    retry_after_seconds: Optional[int] = None  # For rate limits
    fallback_used: Optional[FallbackStrategy] = None
    fallback_value: Optional[Any] = None

    # Debugging
    stack_trace: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        d = asdict(self)
        # Convert enum to string
        d["error_category"] = self.error_category.value
        if self.fallback_used:
            d["fallback_used"] = self.fallback_used.value
        return d


class UnifiedErrorHandler:
    """
    Centralized error handling dengan consistent fallback behaviors.

    Features:
    - Categorize errors automatically
    - Apply appropriate fallback strategy
    - Track error patterns
    - Provide retry recommendations
    """

    VERSION = "1.0.0"

    # Error category -> Fallback strategy mapping
    DEFAULT_FALLBACK_STRATEGIES = {
        ErrorCategory.NETWORK_ERROR: FallbackStrategy.RETRY_WITH_BACKOFF,
        ErrorCategory.RATE_LIMIT: FallbackStrategy.RETURN_CACHED,
        ErrorCategory.SERVICE_UNAVAILABLE: FallbackStrategy.RETRY_ALTERNATE,
        ErrorCategory.INVALID_INPUT: FallbackStrategy.RETURN_ERROR,
        ErrorCategory.AUTHENTICATION: FallbackStrategy.ABORT,
        ErrorCategory.NOT_FOUND: FallbackStrategy.RETURN_ERROR,
        ErrorCategory.QUOTA_EXCEEDED: FallbackStrategy.RETURN_CACHED,
        ErrorCategory.NO_DATA: FallbackStrategy.RETURN_NEUTRAL,
        ErrorCategory.INVALID_DATA: FallbackStrategy.SKIP_SERVICE,
        ErrorCategory.STALE_DATA: FallbackStrategy.CONTINUE_PARTIAL,
        ErrorCategory.CALCULATION_ERROR: FallbackStrategy.RETURN_NEUTRAL,
        ErrorCategory.CACHE_ERROR: FallbackStrategy.SKIP_SERVICE,
        ErrorCategory.DATABASE_ERROR: FallbackStrategy.RETRY_WITH_BACKOFF,
        ErrorCategory.UNKNOWN: FallbackStrategy.RETURN_ERROR,
    }

    def __init__(self):
        # Error statistics
        self._error_counts: Dict[str, int] = {}
        self._error_history: List[Dict[str, Any]] = []

        logger.info(f"✅ UnifiedErrorHandler initialized (v{self.VERSION})")

    def categorize_error(self, exception: Exception, context: Optional[Dict] = None) -> ErrorCategory:
        """
        Automatically categorize error based on exception type and context.

        Args:
            exception: The exception that occurred
            context: Additional context (e.g., HTTP status code)

        Returns:
            ErrorCategory
        """
        error_str = str(exception).lower()
        exception_name = type(exception).__name__

        # Check HTTP status codes if available
        if context and "status_code" in context:
            status = context["status_code"]
            if status == 429:
                return ErrorCategory.RATE_LIMIT
            elif status == 503:
                return ErrorCategory.SERVICE_UNAVAILABLE
            elif status == 401 or status == 403:
                return ErrorCategory.AUTHENTICATION
            elif status == 404:
                return ErrorCategory.NOT_FOUND
            elif 500 <= status < 600:
                return ErrorCategory.SERVICE_UNAVAILABLE

        # Network errors
        if "timeout" in error_str or "connection" in error_str:
            return ErrorCategory.NETWORK_ERROR

        # Rate limits
        if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
            return ErrorCategory.RATE_LIMIT

        # Data errors
        if "no data" in error_str or "empty" in error_str:
            return ErrorCategory.NO_DATA

        if "invalid data" in error_str or "malformed" in error_str or "json" in exception_name.lower():
            return ErrorCategory.INVALID_DATA

        # Calculation errors
        if "division by zero" in error_str or "math" in error_str:
            return ErrorCategory.CALCULATION_ERROR

        # Default to unknown
        return ErrorCategory.UNKNOWN

    def handle_error(
        self,
        exception: Exception,
        service_name: str,
        operation: str,
        symbol: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        custom_fallback: Optional[FallbackStrategy] = None,
        include_stack_trace: bool = False
    ) -> ErrorResponse:
        """
        Handle error dengan categorization dan fallback strategy.

        Args:
            exception: The exception that occurred
            service_name: Name of service where error occurred
            operation: Operation that failed
            symbol: Crypto symbol if applicable
            context: Additional context
            custom_fallback: Override default fallback strategy
            include_stack_trace: Include full stack trace in response

        Returns:
            ErrorResponse with appropriate fallback
        """
        # Categorize error
        category = self.categorize_error(exception, context)

        # Determine fallback strategy
        fallback_strategy = custom_fallback or self.DEFAULT_FALLBACK_STRATEGIES[category]

        # Extract retry_after if rate limit
        retry_after = None
        if category == ErrorCategory.RATE_LIMIT and context:
            retry_after = context.get("retry_after_seconds", 60)

        # Build error response
        error_response = ErrorResponse(
            success=False,
            error_category=category,
            error_message=str(exception),
            error_code=context.get("error_code") if context else None,
            service_name=service_name,
            operation=operation,
            symbol=symbol,
            retry_after_seconds=retry_after,
            fallback_used=fallback_strategy,
            stack_trace=traceback.format_exc() if include_stack_trace else None,
            additional_context=context
        )

        # Track error
        self._track_error(error_response)

        # Log error
        self._log_error(error_response)

        return error_response

    def _track_error(self, error_response: ErrorResponse):
        """Track error for statistics"""
        key = f"{error_response.service_name}:{error_response.error_category.value}"
        self._error_counts[key] = self._error_counts.get(key, 0) + 1

        # Add to history (keep last 100)
        self._error_history.append(error_response.to_dict())
        if len(self._error_history) > 100:
            self._error_history = self._error_history[-100:]

    def _log_error(self, error_response: ErrorResponse):
        """Log error with appropriate level"""
        if error_response.error_category in [ErrorCategory.NETWORK_ERROR, ErrorCategory.SERVICE_UNAVAILABLE]:
            # Transient errors - warning level
            logger.warning(
                f"⚠️  [{error_response.service_name}] {error_response.operation} failed: "
                f"{error_response.error_message} (category: {error_response.error_category.value})"
            )
        elif error_response.error_category in [ErrorCategory.AUTHENTICATION, ErrorCategory.QUOTA_EXCEEDED]:
            # Serious errors - error level
            logger.error(
                f"🔴 [{error_response.service_name}] {error_response.operation} failed: "
                f"{error_response.error_message} (category: {error_response.error_category.value})"
            )
        else:
            # Other errors - info level
            logger.info(
                f"ℹ️  [{error_response.service_name}] {error_response.operation} failed: "
                f"{error_response.error_message} (category: {error_response.error_category.value})"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": self._error_counts,
            "total_errors": sum(self._error_counts.values()),
            "recent_errors": self._error_history[-10:],  # Last 10 errors
            "version": self.VERSION
        }

    def should_retry(self, error_response: ErrorResponse) -> bool:
        """Determine if operation should be retried"""
        return error_response.fallback_used in [
            FallbackStrategy.RETRY_WITH_BACKOFF,
            FallbackStrategy.RETRY_ALTERNATE
        ]

    def get_retry_delay(self, error_response: ErrorResponse, attempt: int) -> int:
        """
        Calculate retry delay dengan exponential backoff.

        Args:
            error_response: Error response
            attempt: Retry attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        if error_response.retry_after_seconds:
            return error_response.retry_after_seconds

        # Exponential backoff: 2^attempt seconds
        base_delay = 2 ** attempt

        # Max 60 seconds
        return min(base_delay, 60)


# Global singleton
unified_error_handler = UnifiedErrorHandler()


# Convenience functions
def handle_service_error(
    exception: Exception,
    service_name: str,
    operation: str,
    symbol: Optional[str] = None,
    **kwargs
) -> ErrorResponse:
    """Convenience function to handle service errors"""
    return unified_error_handler.handle_error(
        exception=exception,
        service_name=service_name,
        operation=operation,
        symbol=symbol,
        context=kwargs.get("context"),
        custom_fallback=kwargs.get("fallback"),
        include_stack_trace=kwargs.get("include_trace", False)
    )


def create_error_response(
    error_message: str,
    service_name: str,
    operation: str,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    **kwargs
) -> ErrorResponse:
    """Create error response without exception"""
    return ErrorResponse(
        success=False,
        error_category=category,
        error_message=error_message,
        service_name=service_name,
        operation=operation,
        symbol=kwargs.get("symbol"),
        error_code=kwargs.get("error_code"),
        retry_after_seconds=kwargs.get("retry_after"),
        additional_context=kwargs.get("context")
    )

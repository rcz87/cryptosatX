"""
Retry Helper with Exponential Backoff
Provides resilient API calls with automatic retry and fallback
"""
import asyncio
from typing import Callable, Any, Optional, List
from functools import wraps
from datetime import datetime
from app.utils.logger import default_logger as logger


class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures

    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, stop trying
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        """Record successful call"""
        self.failure_count = 0

        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.success_count = 0
                logger.info("Circuit breaker: CLOSED (service recovered)")

    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.success_count = 0

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker: OPEN (too many failures: {self.failure_count})"
            )

    def can_attempt(self) -> bool:
        """Check if call should be attempted"""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Check if recovery timeout elapsed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.success_count = 0
                    logger.info("Circuit breaker: HALF_OPEN (testing recovery)")
                    return True
            return False

        # HALF_OPEN: allow attempts
        return True


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    fallback: Optional[Callable] = None,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retry with exponential backoff

    Args:
        config: RetryConfig for retry behavior
        circuit_breaker: CircuitBreaker instance
        fallback: Fallback function to call if all retries fail
        exceptions: Tuple of exceptions to catch

    Usage:
        @retry_with_backoff(config=RetryConfig(max_attempts=3))
        async def fetch_data():
            return await api.call()
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                # Check circuit breaker
                if circuit_breaker and not circuit_breaker.can_attempt():
                    logger.warning(
                        f"{func.__name__}: Circuit breaker OPEN, skipping call"
                    )
                    if fallback:
                        return await fallback(*args, **kwargs)
                    raise Exception("Circuit breaker is OPEN")

                try:
                    result = await func(*args, **kwargs)

                    # Record success
                    if circuit_breaker:
                        circuit_breaker.record_success()

                    return result

                except exceptions as e:
                    last_exception = e

                    # Record failure
                    if circuit_breaker:
                        circuit_breaker.record_failure()

                    # Last attempt - don't retry
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"{func.__name__}: All {config.max_attempts} attempts failed. "
                            f"Last error: {e}"
                        )

                        # Try fallback
                        if fallback:
                            logger.info(f"{func.__name__}: Trying fallback")
                            try:
                                return await fallback(*args, **kwargs)
                            except Exception as fb_error:
                                logger.error(f"Fallback also failed: {fb_error}")

                        raise last_exception

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.initial_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )

                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        import random
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"{func.__name__}: Attempt {attempt + 1}/{config.max_attempts} failed. "
                        f"Retrying in {delay:.2f}s. Error: {e}"
                    )

                    await asyncio.sleep(delay)

            raise last_exception if last_exception else Exception("All retry attempts failed")

        return wrapper
    return decorator


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on API health

    Speeds up when API is healthy, slows down when errors occur
    """

    def __init__(
        self,
        initial_interval: float = 30.0,
        min_interval: float = 10.0,
        max_interval: float = 300.0,
        error_threshold: float = 0.1  # 10% error rate
    ):
        self.base_interval = initial_interval
        self.current_interval = initial_interval
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.error_threshold = error_threshold

        self.total_calls = 0
        self.error_calls = 0
        self.last_adjustment = datetime.utcnow()

    def record_call(self, success: bool):
        """Record API call result"""
        self.total_calls += 1
        if not success:
            self.error_calls += 1

        # Adjust interval every 10 calls
        if self.total_calls % 10 == 0:
            self._adjust_interval()

    def _adjust_interval(self):
        """Adjust interval based on error rate"""
        if self.total_calls == 0:
            return

        error_rate = self.error_calls / self.total_calls

        if error_rate > self.error_threshold:
            # Too many errors - slow down
            self.current_interval = min(
                self.current_interval * 1.5,
                self.max_interval
            )
            logger.warning(
                f"Adaptive rate limiter: Slowing down to {self.current_interval:.1f}s "
                f"(error rate: {error_rate:.1%})"
            )
        elif error_rate < self.error_threshold / 2:
            # Healthy - speed up
            self.current_interval = max(
                self.current_interval * 0.9,
                self.min_interval
            )
            logger.info(
                f"Adaptive rate limiter: Speeding up to {self.current_interval:.1f}s "
                f"(error rate: {error_rate:.1%})"
            )

        # Reset counters
        self.total_calls = 0
        self.error_calls = 0
        self.last_adjustment = datetime.utcnow()

    async def wait(self):
        """Wait according to current interval"""
        await asyncio.sleep(self.current_interval)

    def get_current_interval(self) -> float:
        """Get current wait interval"""
        return self.current_interval


# Pre-configured retry configs for common use cases
FAST_RETRY = RetryConfig(
    max_attempts=3,
    initial_delay=0.5,
    max_delay=5.0
)

STANDARD_RETRY = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0
)

AGGRESSIVE_RETRY = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=60.0
)

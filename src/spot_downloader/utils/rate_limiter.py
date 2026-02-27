"""
Rate limiting utilities for API calls.
Prevents API bans by enforcing request limits.
"""

import time
import threading
from functools import wraps
from typing import Callable, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, calls: int, period: float):
        """
        Initialize rate limiter.
        
        Args:
            calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.tokens = calls
        self.last_update = time.time()
        self._lock = threading.Lock()
    
    def acquire(self) -> bool:
        """
        Acquire a token, blocking if necessary.
        
        Returns:
            True when token is acquired
        """
        with self._lock:
            while True:
                now = time.time()
                # Replenish tokens based on elapsed time
                elapsed = now - self.last_update
                self.tokens = min(self.calls, self.tokens + elapsed * (self.calls / self.period))
                self.last_update = now
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                # Calculate wait time for next token
                wait_time = (1 - self.tokens) * (self.period / self.calls)
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to rate limit a function."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            self.acquire()
            return func(*args, **kwargs)
        return wrapper


def rate_limit(calls: int, period: float):
    """
    Decorator to rate limit a function.
    
    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds
    
    Returns:
        Decorated function with rate limiting
    
    Example:
        @rate_limit(calls=10, period=60)  # 10 calls per minute
        def search_ytm(query):
            ...
    """
    limiter = RateLimiter(calls, period)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            limiter.acquire()
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on error responses.
    Useful for APIs that return 429 Too Many Requests.
    """
    
    def __init__(self, initial_calls: int, initial_period: float, 
                 min_calls: int = 1, max_calls: int = 100):
        """
        Initialize adaptive rate limiter.
        
        Args:
            initial_calls: Initial number of calls allowed
            initial_period: Initial time period in seconds
            min_calls: Minimum calls per period
            max_calls: Maximum calls per period
        """
        self._limiter = RateLimiter(initial_calls, initial_period)
        self.min_calls = min_calls
        self.max_calls = max_calls
        self.current_calls = initial_calls
        self.period = initial_period
        self._lock = threading.Lock()
    
    def on_success(self):
        """Call on successful API response."""
        with self._lock:
            # Gradually increase limit on success
            if self.current_calls < self.max_calls:
                self.current_calls = min(self.max_calls, self.current_calls + 1)
                self._limiter = RateLimiter(self.current_calls, self.period)
                logger.debug(f"Increased rate limit to {self.current_calls} calls per {self.period}s")
    
    def on_rate_limit_error(self):
        """Call when receiving 429 Too Many Requests."""
        with self._lock:
            # Decrease limit on rate limit error
            if self.current_calls > self.min_calls:
                self.current_calls = max(self.min_calls, self.current_calls // 2)
                self._limiter = RateLimiter(self.current_calls, self.period)
                logger.warning(f"Decreased rate limit to {self.current_calls} calls per {self.period}s due to 429 error")
    
    def acquire(self):
        """Acquire a token."""
        self._limiter.acquire()
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to rate limit a function."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            self.acquire()
            try:
                result = func(*args, **kwargs)
                self.on_success()
                return result
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    self.on_rate_limit_error()
                raise
        return wrapper

"""
Retry decorator for network operations.
Provides automatic retry functionality with exponential backoff.
"""

import time
import functools
import logging
from typing import Tuple, Type, Optional, Callable
from .error_handling import NetworkError

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    max_delay: Optional[float] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay between retries (default: None, no limit)
        exceptions: Tuple of exception types to catch and retry
        logger: Logger instance for logging retry attempts
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(requests.RequestException,))
        def fetch_data(url):
            response = requests.get(url)
            return response.json()
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    if logger and attempt > 1:
                        logger.info(f"Attempt {attempt}/{max_attempts} for {func.__name__}")
                    
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if logger:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}"
                        )
                    
                    # Don't sleep after the last attempt
                    if attempt < max_attempts:
                        sleep_time = min(current_delay, max_delay) if max_delay else current_delay
                        if logger:
                            logger.info(f"Retrying in {sleep_time:.1f} seconds...")
                        time.sleep(sleep_time)
                        current_delay *= backoff
            
            # All attempts failed
            error_msg = f"All {max_attempts} attempts failed for {func.__name__}"
            if logger:
                logger.error(error_msg)
            
            # Raise the original exception or wrap in NetworkError
            if isinstance(last_exception, exceptions):
                raise last_exception
            raise NetworkError(error_msg, last_exception)
        
        return wrapper
    return decorator


def retry_with_fallback(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    fallback_return: any = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None
):
    """
    Retry decorator that returns a fallback value if all attempts fail.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff: Multiplier for delay after each retry
        fallback_return: Value to return if all attempts fail
        exceptions: Tuple of exception types to catch
        logger: Logger instance
    
    Returns:
        Decorated function with retry and fallback logic
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if logger:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {str(e)}"
                        )
                    
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if logger:
                            logger.error(f"All attempts failed, returning fallback value")
                        return fallback_return
            
            return fallback_return
        
        return wrapper
    return decorator

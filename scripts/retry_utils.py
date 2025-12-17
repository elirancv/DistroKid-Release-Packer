#!/usr/bin/env python3
"""
Retry utilities for handling transient failures in workflow operations.

Provides decorators and context managers for automatic retry with exponential backoff.
"""

import time
import random
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any
from logger_config import get_logger

logger = get_logger("retry_utils")


class RetryableError(Exception):
    """Base exception for errors that should trigger retry."""
    pass


class NonRetryableError(Exception):
    """Exception for errors that should not be retried."""
    pass


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to delay (default: True)
        retryable_exceptions: Tuple of exception types to retry (default: all exceptions)
        on_retry: Optional callback function(attempt_num, exception) called before retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except NonRetryableError as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class RetryContext:
    """
    Context manager for retrying operations with exponential backoff.
    
    Usage:
        with RetryContext(max_attempts=3) as retry:
            result = some_operation()
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.attempt = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
        
        if exc_type in self.retryable_exceptions or any(
            issubclass(exc_type, retry_exc) for retry_exc in self.retryable_exceptions
        ):
            self.attempt += 1
            
            if self.attempt >= self.max_attempts:
                logger.error(
                    f"Operation failed after {self.max_attempts} attempts: {exc_val}"
                )
                return False  # Don't suppress exception
            
            # Calculate delay
            delay = min(
                self.initial_delay * (self.exponential_base ** (self.attempt - 1)),
                self.max_delay
            )
            
            if self.jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            logger.warning(
                f"Operation failed (attempt {self.attempt}/{self.max_attempts}): {exc_val}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            time.sleep(delay)
            return True  # Suppress exception and retry
        
        return False  # Don't suppress non-retryable exceptions


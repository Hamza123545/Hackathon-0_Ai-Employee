"""
Retry Manager (Gold Tier)

Implements exponential backoff retry logic for MCP server calls and external API requests.
"""

import time
from typing import Callable, Optional, TypeVar, Any
from functools import wraps

T = TypeVar('T')


class RetryManager:
    """
    Manages retry logic with exponential backoff.
    
    Default strategy: 1s, 2s, 4s (max 3 attempts)
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_delay: Optional[float] = None
    ):
        """
        Initialize RetryManager.
        
        Args:
            max_attempts: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
            backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
            max_delay: Maximum delay in seconds (default: None, no limit)
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_multiplier = backoff_multiplier
        self.max_delay = max_delay
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.
        
        Args:
            attempt: Attempt number (0-indexed, so first retry is attempt 1)
        
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_multiplier ** attempt)
        
        if self.max_delay is not None:
            delay = min(delay, self.max_delay)
        
        return delay
    
    def retry(
        self,
        func: Callable[..., T],
        *args: Any,
        should_retry: Optional[Callable[[Exception], bool]] = None,
        **kwargs: Any
    ) -> T:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            should_retry: Optional function to determine if an exception should be retried.
                        If None, all exceptions are retried.
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of func execution
        
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if we should retry this exception
                if should_retry is not None and not should_retry(e):
                    raise
                
                # Don't sleep after the last attempt
                if attempt < self.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    time.sleep(delay)
        
        # All retries exhausted
        raise last_exception
    
    async def retry_async(
        self,
        func: Callable[..., T],
        *args: Any,
        should_retry: Optional[Callable[[Exception], bool]] = None,
        **kwargs: Any
    ) -> T:
        """
        Execute an async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            should_retry: Optional function to determine if an exception should be retried.
                        If None, all exceptions are retried.
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of func execution
        
        Raises:
            Last exception if all retries fail
        """
        import asyncio
        
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if we should retry this exception
                if should_retry is not None and not should_retry(e):
                    raise
                
                # Don't sleep after the last attempt
                if attempt < self.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_delay: Optional[float] = None,
    should_retry: Optional[Callable[[Exception], bool]] = None
):
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
        max_delay: Maximum delay in seconds (default: None, no limit)
        should_retry: Optional function to determine if an exception should be retried.
    
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def my_api_call():
            return requests.get("https://api.example.com")
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        retry_manager = RetryManager(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            backoff_multiplier=backoff_multiplier,
            max_delay=max_delay
        )
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return retry_manager.retry(func, *args, should_retry=should_retry, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_manager.retry_async(func, *args, should_retry=should_retry, **kwargs)
        
        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


# Default retry manager instance (1s, 2s, 4s, max 3 attempts)
default_retry_manager = RetryManager(
    max_attempts=3,
    initial_delay=1.0,
    backoff_multiplier=2.0
)


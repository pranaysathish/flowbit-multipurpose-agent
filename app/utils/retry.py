import time
import logging
from functools import wraps
from typing import Callable, Any, Dict, Optional

logger = logging.getLogger(__name__)

def retry_on_failure(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry_callback: Optional[Callable] = None
) -> Callable:
    """
    Decorator to retry a function call on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on
        on_retry_callback: Optional callback function to execute on retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_count = 0
            current_delay = retry_delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1
                    
                    if retry_count > max_retries:
                        logger.error(f"Maximum retries ({max_retries}) exceeded for {func.__name__}. Last error: {str(e)}")
                        raise
                    
                    logger.warning(
                        f"Retry {retry_count}/{max_retries} for {func.__name__} after error: {str(e)}. "
                        f"Retrying in {current_delay:.2f} seconds..."
                    )
                    
                    # Execute callback if provided
                    if on_retry_callback:
                        try:
                            on_retry_callback(func.__name__, retry_count, e, current_delay)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {str(callback_error)}")
                    
                    # Wait before retrying
                    time.sleep(current_delay)
                    
                    # Increase delay for next retry
                    current_delay *= backoff_factor
        
        return wrapper
    
    return decorator


class RetryContext:
    """
    Context manager for retry operations with state tracking.
    Useful for more complex retry scenarios or when retry state needs to be tracked.
    """
    
    def __init__(
        self, 
        operation_name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        self.operation_name = operation_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
        self.retry_count = 0
        self.current_delay = retry_delay
        self.last_error = None
        self.success = False
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.success = True
            return True
            
        if exc_type in self.exceptions:
            self.last_error = exc_val
            self.retry_count += 1
            
            if self.retry_count <= self.max_retries:
                logger.warning(
                    f"Retry {self.retry_count}/{self.max_retries} for {self.operation_name} "
                    f"after error: {str(exc_val)}. Retrying in {self.current_delay:.2f} seconds..."
                )
                
                time.sleep(self.current_delay)
                self.current_delay *= self.backoff_factor
                
                # Suppress the exception to retry
                return True
                
        # Don't suppress exceptions if we've exceeded retries or it's not a retryable exception
        return False
    
    def should_continue(self) -> bool:
        """Check if we should continue retrying"""
        return self.retry_count <= self.max_retries and not self.success

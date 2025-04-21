"""
Decorator functions for the LinkedIn Automation package.
"""
import functools
import time

from linkedin_automation.utils.logging import get_logger

logger = get_logger(__name__)

def retry(max_attempts=3, delay_seconds=1):
    """
    Decorator to retry a function on exception.
    
    Args:
        max_attempts (int): Maximum number of retry attempts
        delay_seconds (int): Delay between retries in seconds
        
    Returns:
        function: Decorated function with retry logic
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts. Error: {e}")
                        raise
                    logger.warning(f"Retry attempt {attempts} for {func.__name__}. Error: {e}")
                    time.sleep(delay_seconds)
        return wrapper
    return decorator


def safe_operation(func):
    """
    Decorator to safely handle exceptions in operations.
    
    Args:
        func: The function to decorate
        
    Returns:
        function: Decorated function with exception handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper
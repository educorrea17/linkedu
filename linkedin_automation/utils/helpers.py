"""
Helper functions for the LinkedIn Automation package.
"""
import random
import time
import threading
from functools import lru_cache

from linkedin_automation.config.settings import DEFAULT_WAIT_RANGE
from linkedin_automation.utils.logging import get_logger

logger = get_logger(__name__)

# Track the number of sleep calls to dynamically adjust sleep time
_sleep_call_count = 0
_sleep_call_lock = threading.Lock()
_last_sleep_time = time.time()

@lru_cache(maxsize=32)
def get_adjusted_sleep_range(min_max, call_count):
    """
    Get sleep range adjusted based on the number of recent sleep calls.
    This helps to create more human-like behavior - as the automation
    runs longer, we reduce the sleep times slightly for efficiency.
    
    Args:
        min_max (tuple): Original min and max sleep durations
        call_count (int): Number of sleep calls so far
        
    Returns:
        tuple: Adjusted min and max sleep durations
    """
    # If more than 50 sleep calls have been made, gradually reduce sleep time
    # but never go below 30% of the original values
    if call_count > 50:
        reduction_factor = min(0.7, (call_count - 50) / 200)
        adjusted_min = min_max[0] * (1 - reduction_factor)
        adjusted_max = min_max[1] * (1 - reduction_factor)
        return (adjusted_min, adjusted_max)
    return min_max

def adaptive_sleep(min_seconds=None, max_seconds=None):
    """
    Adaptively sleep for a duration based on context and past behavior.
    
    Args:
        min_seconds (float, optional): Minimum sleep duration in seconds.
        max_seconds (float, optional): Maximum sleep duration in seconds.
            If only min_seconds is provided, it's used as a fixed sleep time.
            If neither is provided, DEFAULT_WAIT_RANGE from settings is used.
    """
    global _sleep_call_count, _last_sleep_time
    
    # Handle various input formats
    if min_seconds is not None and max_seconds is not None:
        # Both min and max provided as separate arguments
        wait_range = (min_seconds, max_seconds)
    elif min_seconds is not None and isinstance(min_seconds, (tuple, list)) and len(min_seconds) == 2:
        # Range provided as a tuple/list in the first argument
        wait_range = min_seconds
    elif min_seconds is not None:
        # Only min provided - use fixed sleep time
        wait_range = (min_seconds, min_seconds)
    else:
        # Default range from settings
        wait_range = DEFAULT_WAIT_RANGE
    
    # Use lock to avoid race conditions when updating the counter
    with _sleep_call_lock:
        _sleep_call_count += 1
        count = _sleep_call_count
        
        # Get time since last sleep
        current_time = time.time()
        time_since_last_sleep = current_time - _last_sleep_time
        _last_sleep_time = current_time
    
    # Adjust sleep range based on call count and time since last sleep
    adjusted_range = get_adjusted_sleep_range(wait_range, count)
    
    # If less than 0.1 seconds have passed since the last sleep, reduce sleep time
    # to avoid excessive waiting when making multiple quick operations
    if time_since_last_sleep < 0.1:
        adjusted_range = (adjusted_range[0] * 0.5, adjusted_range[1] * 0.5)
    
    # Random sleep duration within the adjusted range
    duration = random.uniform(adjusted_range[0], adjusted_range[1])
    
    # Log the sleep duration if it's significant (over 1 second)
    if duration > 1:
        logger.debug(f"Sleeping for {duration:.2f} seconds")
        
    time.sleep(duration)

# For backward compatibility, keep the original sleep function name
# but use the improved implementation
sleep = adaptive_sleep
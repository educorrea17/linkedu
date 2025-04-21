"""
Logging utilities for the LinkedIn Automation package.
"""
import logging
from pathlib import Path

from linkedin_automation.config.settings import LOG_DIR, LOG_LEVEL

LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def get_logger(name):
    """
    Configure and return a logger for the specified module.

    Args:
        name (str): Name of the module (typically __name__)

    Returns:
        logging.Logger: Configured logger object
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Get the logging level from settings, default to INFO if invalid
        level = LOG_LEVEL_MAP.get(LOG_LEVEL.upper(), logging.INFO)  # <-- Use the mapped level

        # Use the 'level' variable for all setLevel calls
        logger.setLevel(level)

        # File handler
        file_handler = logging.FileHandler(LOG_DIR / "linkedu.log")
        file_handler.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Formatter (remains the same)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers (remains the same)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
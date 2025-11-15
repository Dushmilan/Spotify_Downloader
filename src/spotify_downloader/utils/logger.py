"""
Logging utility for the Spotify Downloader.

Provides a standardized logging interface for the application with different
logging levels and output formats based on the verbosity setting.
"""
import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name (str): Name of the logger (usually the module name)
        level (Optional[int]): Logging level (DEBUG, INFO, WARNING, ERROR). 
                              If None, defaults to WARNING unless verbose mode is enabled.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Set the logging level
    if level:
        logger.setLevel(level)
    else:
        logger.setLevel(logging.WARNING)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger
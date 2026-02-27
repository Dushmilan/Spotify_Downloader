"""
Logging utilities for the Spotify Downloader application.
Provides centralized logging configuration and helper functions.
"""

import logging
import sys
from typing import Optional
from ..config import app_config


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__ of the module)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist
    if not logger.handlers:
        logger.setLevel(getattr(logging, app_config.log_level.upper(), logging.INFO))
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, app_config.log_level.upper(), logging.INFO))
        
        # Create formatter with color support for different levels
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


def log_callback_factory(logger: logging.Logger):
    """
    Create a log callback function compatible with the downloader's callback system.
    
    Args:
        logger: Logger instance to use
    
    Returns:
        Callback function that logs messages
    """
    def callback(message: str):
        logger.info(message)
    return callback


def setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None):
    """
    Setup application-wide logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
    """
    level = getattr(logging, (log_level or app_config.log_level).upper(), logging.INFO)
    
    # Create root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

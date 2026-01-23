"""
Error handling utilities for the Spotify Downloader application.
Provides consistent error handling and logging across the application.
"""

import logging
import traceback
from enum import Enum
from typing import Optional


class DownloadErrorType(Enum):
    """Enumeration of different types of download errors."""
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    FILE_ERROR = "file_error"
    PROCESSING_ERROR = "processing_error"
    UNKNOWN_ERROR = "unknown_error"


class DownloadError(Exception):
    """Custom exception class for download-related errors."""
    
    def __init__(self, message: str, error_type: DownloadErrorType = DownloadErrorType.UNKNOWN_ERROR, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.error_type = error_type
        self.original_exception = original_exception
        self.traceback = traceback.format_exc() if original_exception else None
    
    def __str__(self):
        base_msg = f"[{self.error_type.value}] {super().__str__()}"
        if self.original_exception:
            base_msg += f" (Original: {type(self.original_exception).__name__}: {self.original_exception})"
        return base_msg


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup application logging."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    
    # Setup file handler if specified
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        force=True  # Overwrite any existing configuration
    )


def log_error(error: Exception, logger: logging.Logger = None, context: str = ""):
    """Log an error with context."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    error_msg = f"{context} Error: {str(error)}"
    if hasattr(error, 'traceback') and error.traceback:
        error_msg += f"\nTraceback: {error.traceback}"
    
    logger.error(error_msg)


def handle_download_error(error: Exception, log_callback=None, context: str = ""):
    """Handle a download error appropriately."""
    if log_callback:
        error_msg = f"{context} Error: {str(error)}"
        if hasattr(error, 'original_exception') and error.original_exception:
            error_msg += f" (Original: {type(error.original_exception).__name__}: {error.original_exception})"
        log_callback(error_msg)
    
    # Log to file if available
    logger = logging.getLogger(__name__)
    log_error(error, logger, context)
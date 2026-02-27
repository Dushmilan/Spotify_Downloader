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
    API_ERROR = "api_error"
    AUTH_ERROR = "auth_error"
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


# === Specific Exception Classes ===

class NetworkError(DownloadError):
    """Raised when a network-related error occurs."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, DownloadErrorType.NETWORK_ERROR, original_exception)


class ValidationError(DownloadError):
    """Raised when input validation fails."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, DownloadErrorType.VALIDATION_ERROR, original_exception)


class FileError(DownloadError):
    """Raised when a file operation fails."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, DownloadErrorType.FILE_ERROR, original_exception)


class ProcessingError(DownloadError):
    """Raised when processing fails."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, DownloadErrorType.PROCESSING_ERROR, original_exception)


class APIError(DownloadError):
    """Raised when an API call fails."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, DownloadErrorType.API_ERROR, original_exception)


class AuthError(DownloadError):
    """Raised when authentication fails."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, DownloadErrorType.AUTH_ERROR, original_exception)


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

from .logger import get_logger, log_callback_factory, setup_logging
from .retry import retry, retry_with_fallback
from .validation import validate_spotify_url, sanitize_filename, validate_download_path, is_safe_url
from .error_handling import (
    DownloadError, DownloadErrorType,
    NetworkError, ValidationError, FileError, ProcessingError, APIError, AuthError,
    log_error, handle_download_error
)
from .helpers import get_ffmpeg_path, check_ffmpeg
from .tagger import tag_mp3, tag_m4a
from .throttle import Throttler

__all__ = [
    # Logger
    'get_logger',
    'log_callback_factory',
    'setup_logging',
    # Retry
    'retry',
    'retry_with_fallback',
    # Validation
    'validate_spotify_url',
    'sanitize_filename',
    'validate_download_path',
    'is_safe_url',
    # Error handling
    'DownloadError',
    'DownloadErrorType',
    'NetworkError',
    'ValidationError',
    'FileError',
    'ProcessingError',
    'APIError',
    'AuthError',
    'log_error',
    'handle_download_error',
    # Helpers
    'get_ffmpeg_path',
    'check_ffmpeg',
    # Tagger
    'tag_mp3',
    'tag_m4a',
    # Throttle
    'Throttler',
]

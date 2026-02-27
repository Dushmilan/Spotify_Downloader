"""
Tests for error handling utilities.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.utils.error_handling import (
    DownloadError,
    DownloadErrorType,
    NetworkError,
    ValidationError,
    FileError,
    ProcessingError,
    APIError,
    AuthError,
    handle_download_error,
)


class TestDownloadError:
    """Test DownloadError class."""

    def test_basic_error(self):
        """Test basic download error."""
        error = DownloadError("Test error")
        assert str(error) == "[unknown_error] Test error"
        assert error.error_type == DownloadErrorType.UNKNOWN_ERROR

    def test_error_with_type(self):
        """Test error with specific type."""
        error = DownloadError("Network failed", DownloadErrorType.NETWORK_ERROR)
        assert str(error) == "[network_error] Network failed"

    def test_error_with_exception(self):
        """Test error wrapping original exception."""
        original = ValueError("Original error")
        error = DownloadError("Wrapped", original_exception=original)
        assert error.original_exception is original
        assert "ValueError" in str(error)


class TestSpecificErrors:
    """Test specific error classes."""

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Connection failed")
        assert error.error_type == DownloadErrorType.NETWORK_ERROR

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input")
        assert error.error_type == DownloadErrorType.VALIDATION_ERROR

    def test_file_error(self):
        """Test FileError."""
        error = FileError("File not found")
        assert error.error_type == DownloadErrorType.FILE_ERROR

    def test_processing_error(self):
        """Test ProcessingError."""
        error = ProcessingError("Processing failed")
        assert error.error_type == DownloadErrorType.PROCESSING_ERROR

    def test_api_error(self):
        """Test APIError."""
        error = APIError("API call failed")
        assert error.error_type == DownloadErrorType.API_ERROR

    def test_auth_error(self):
        """Test AuthError."""
        error = AuthError("Authentication failed")
        assert error.error_type == DownloadErrorType.AUTH_ERROR


class TestHandleDownloadError:
    """Test handle_download_error function."""

    def test_with_callback(self):
        """Test error handling with callback."""
        messages = []
        
        def log_callback(msg):
            messages.append(msg)
        
        error = ValueError("Test error")
        handle_download_error(error, log_callback, "Test context")
        
        assert len(messages) > 0
        assert "Test context" in messages[0]

    def test_without_callback(self):
        """Test error handling without callback."""
        error = ValueError("Test error")
        # Should not raise
        handle_download_error(error, None, "Test")

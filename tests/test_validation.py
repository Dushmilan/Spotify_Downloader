"""
Tests for validation utilities.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.utils.validation import (
    validate_spotify_url,
    sanitize_filename,
    validate_download_path,
    is_safe_url,
)


class TestValidateSpotifyUrl:
    """Test Spotify URL validation."""

    def test_valid_track_url(self):
        """Test valid track URL."""
        assert validate_spotify_url("https://open.spotify.com/track/abc123") is True

    def test_valid_playlist_url(self):
        """Test valid playlist URL."""
        assert validate_spotify_url("https://open.spotify.com/playlist/abc123") is True

    def test_valid_album_url(self):
        """Test valid album URL."""
        assert validate_spotify_url("https://open.spotify.com/album/abc123") is True

    def test_invalid_domain(self):
        """Test invalid domain."""
        assert validate_spotify_url("https://example.com/track/abc123") is False

    def test_empty_url(self):
        """Test empty URL."""
        assert validate_spotify_url("") is False

    def test_none_url(self):
        """Test None URL."""
        assert validate_spotify_url(None) is False

    def test_spotify_link_url(self):
        """Test spotify.link URL with valid path."""
        # spotify.link URLs need valid paths like /track/, /playlist/, etc.
        assert validate_spotify_url("https://spotify.link/track/abc123") is True
        assert validate_spotify_url("https://spotify.link/playlist/abc123") is True


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_normal_filename(self):
        """Test normal filename."""
        assert sanitize_filename("normal_file.mp3") == "normal_file.mp3"

    def test_invalid_chars(self):
        """Test invalid characters are removed."""
        result = sanitize_filename("file<name>.mp3")
        assert "<" not in result
        assert ">" not in result

    def test_directory_traversal(self):
        """Test directory traversal is prevented."""
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result

    def test_empty_filename(self):
        """Test empty filename."""
        assert sanitize_filename("") == ""

    def test_whitespace_trimming(self):
        """Test whitespace is trimmed."""
        assert sanitize_filename("  file.mp3  ") == "file.mp3"

    def test_long_filename(self):
        """Test long filename is truncated."""
        long_name = "a" * 300 + ".mp3"
        result = sanitize_filename(long_name)
        assert len(result) <= 255


class TestIsSafeUrl:
    """Test safe URL validation."""

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        assert is_safe_url("https://example.com") is True

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        assert is_safe_url("http://example.com") is True

    def test_localhost_blocked(self):
        """Test localhost is blocked."""
        assert is_safe_url("http://localhost") is False

    def test_private_ip_blocked(self):
        """Test private IP addresses are blocked."""
        assert is_safe_url("http://192.168.1.1") is False
        assert is_safe_url("http://10.0.0.1") is False

    def test_invalid_scheme(self):
        """Test invalid scheme is blocked."""
        assert is_safe_url("ftp://example.com") is False

    def test_empty_url(self):
        """Test empty URL."""
        assert is_safe_url("") is False


class TestValidateDownloadPath:
    """Test download path validation."""

    def test_valid_subpath(self, tmp_path):
        """Test valid subpath."""
        result = validate_download_path(str(tmp_path), "downloads")
        assert "downloads" in result

    def test_directory_traversal_blocked(self, tmp_path):
        """Test directory traversal is blocked by sanitization."""
        # sanitize_filename removes ".." so the path is sanitized
        result = validate_download_path(str(tmp_path), "../../../etc")
        # The ".." should be removed, resulting in a safe path
        assert ".." not in result
        assert "etc" in result  # The sanitized filename will contain "etc"

    def test_empty_subpath(self, tmp_path):
        """Test empty subpath returns base path."""
        result = validate_download_path(str(tmp_path), "")
        assert result == str(tmp_path)

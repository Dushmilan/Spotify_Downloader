"""
Tests for the SpotDownloader core functionality.
Uses fixtures for mock data.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.core.downloader import SpotDownloader
from spot_downloader.utils.validation import validate_spotify_url, sanitize_filename
from tests.fixtures import (
    VALID_SPOTIFY_TRACK_URL,
    VALID_SPOTIFY_PLAYLIST_URL,
    INVALID_URL,
    MOCK_METADATA_SINGLE,
    MOCK_CONFIG,
)


class TestDownloaderInit:
    """Test SpotDownloader initialization."""

    def test_downloader_init_with_custom_path(self, tmp_path):
        """Test downloader initializes with custom download path."""
        downloader = SpotDownloader(download_path=str(tmp_path))
        assert downloader.download_path == str(tmp_path)
        assert os.path.exists(tmp_path)

    def test_downloader_init_creates_directory(self, tmp_path):
        """Test downloader creates download directory if it doesn't exist."""
        new_path = tmp_path / "new_downloads"
        downloader = SpotDownloader(download_path=str(new_path))
        assert os.path.exists(new_path)

    def test_downloader_init_with_none_path(self):
        """Test downloader initializes with default path when None provided."""
        downloader = SpotDownloader(download_path=None)
        assert downloader.download_path is not None


class TestSetDownloadPath:
    """Test set_download_path method."""

    def test_set_download_path(self, tmp_path):
        """Test setting a new download path."""
        downloader = SpotDownloader()
        new_path = str(tmp_path / "new_test_path")
        downloader.set_download_path(new_path)
        assert downloader.download_path == new_path
        assert os.path.exists(new_path)

    def test_set_download_path_creates_directory(self, tmp_path):
        """Test set_download_path creates directory if it doesn't exist."""
        downloader = SpotDownloader()
        new_path = str(tmp_path / "nested" / "path")
        downloader.set_download_path(new_path)
        assert os.path.exists(new_path)


class TestValidateSpotifyUrl:
    """Test Spotify URL validation."""

    def test_valid_track_url(self):
        """Test valid track URL passes validation."""
        assert validate_spotify_url(VALID_SPOTIFY_TRACK_URL) is True

    def test_valid_playlist_url(self):
        """Test valid playlist URL passes validation."""
        assert validate_spotify_url(VALID_SPOTIFY_PLAYLIST_URL) is True

    def test_invalid_url(self):
        """Test invalid URL fails validation."""
        assert validate_spotify_url(INVALID_URL) is False

    def test_empty_url(self):
        """Test empty URL fails validation."""
        assert validate_spotify_url("") is False

    def test_none_url(self):
        """Test None URL fails validation."""
        assert validate_spotify_url(None) is False


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_normal_filename(self):
        """Test normal filename passes through."""
        assert sanitize_filename("normal_file.mp3") == "normal_file.mp3"

    def test_filename_with_invalid_chars(self):
        """Test filename with invalid characters is sanitized."""
        result = sanitize_filename("file<name>.mp3")
        assert "<" not in result
        assert ">" not in result

    def test_directory_traversal(self):
        """Test directory traversal is prevented."""
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result

    def test_empty_filename(self):
        """Test empty filename returns empty string."""
        assert sanitize_filename("") == ""

    def test_long_filename(self, monkeypatch):
        """Test long filename is truncated."""
        long_name = "a" * 300 + ".mp3"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

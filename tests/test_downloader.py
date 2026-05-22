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


class TestSpotDownloaderDeepened:
    """Tests for the deepened SpotDownloader interface."""

    def test_download_returns_handle_and_completes(self, tmp_path):
        """download(url) returns a DownloadHandle that resolves to completed."""
        from unittest.mock import MagicMock, patch

        fake_scraper = MagicMock()
        fake_scraper.scrape_track.return_value = {
            'name': 'Test Song',
            'artists': [{'name': 'Test Artist'}],
            'duration_ms': 180000,
            'album': {'name': 'Test Album'}
        }

        with patch('spot_downloader.core.downloader.YouTubeSearcher') as MockSearcher:
            MockSearcher.search_ytm.return_value = 'https://youtube.com/watch?v=test'

            with patch('spot_downloader.core.downloader.yt_dlp.YoutubeDL') as MockYDL:
                mock_ydl_instance = MagicMock()
                MockYDL.return_value.__enter__.return_value = mock_ydl_instance

                song_path = os.path.join(str(tmp_path), "Test Song - Test Artist.mp3")
                def fake_download(video_urls):
                    os.makedirs(os.path.dirname(song_path), exist_ok=True)
                    with open(song_path, 'wb') as f:
                        f.write(b'\x00' * 100)
                mock_ydl_instance.download.side_effect = fake_download

                with patch('spot_downloader.core.downloader.tag_mp3', return_value=True):
                    downloader = SpotDownloader(download_path=str(tmp_path), scraper=fake_scraper)
                    handle = downloader.download('https://open.spotify.com/track/abc')
                    assert handle is not None
                    result = handle.result(timeout=10)
                    assert result.status == 'completed'

    def test_download_scraper_url_routing(self, tmp_path):
        """download(url) routes to the correct scraper method based on URL path."""
        from unittest.mock import MagicMock, patch
        import time

        def _wait_for_call(mock_method, timeout=3):
            start = time.time()
            while time.time() - start < timeout:
                if mock_method.called:
                    return
                time.sleep(0.05)

        fake_scraper = MagicMock()
        fake_scraper.scrape_track.return_value = {'name': 'Track', 'artists': [{'name': 'A'}], 'duration_ms': 100000}
        fake_scraper.scrape_album.return_value = {'name': 'Album', 'tracks': [{'name': 'T1', 'artists': [{'name': 'A'}]}]}
        fake_scraper.scrape_playlist.return_value = {'name': 'Playlist', 'tracks': {'items': [{'track': {'name': 'T1', 'artists': [{'name': 'A'}]}}]}}

        downloader = SpotDownloader(download_path=str(tmp_path), scraper=fake_scraper)

        handle = downloader.download('https://open.spotify.com/track/abc123')
        _wait_for_call(fake_scraper.scrape_track)
        fake_scraper.scrape_track.assert_called_once()

        handle = downloader.download('https://open.spotify.com/album/def456')
        _wait_for_call(fake_scraper.scrape_album)
        fake_scraper.scrape_album.assert_called_once()

        handle = downloader.download('https://open.spotify.com/playlist/ghi789')
        _wait_for_call(fake_scraper.scrape_playlist)
        fake_scraper.scrape_playlist.assert_called_once()

    def test_download_invalid_url_returns_none(self, tmp_path):
        """download() returns None for invalid or unsafe URLs."""
        from unittest.mock import MagicMock

        downloader = SpotDownloader(download_path=str(tmp_path), scraper=MagicMock())

        assert downloader.download(None) is None
        assert downloader.download("") is None
        assert downloader.download(123) is None

    def test_download_unsafe_url_returns_none(self, tmp_path):
        """download() returns None for unsafe URLs."""
        from unittest.mock import MagicMock

        downloader = SpotDownloader(download_path=str(tmp_path), scraper=MagicMock())

        assert downloader.download("ftp://evil.com/file") is None
        assert downloader.download("http://127.0.0.1:8080/attack") is None
        assert downloader.download("") is None

    def test_download_scraper_failure_returns_failed_result(self, tmp_path):
        """When scraper raises, download() returns a failed result."""
        from unittest.mock import MagicMock, patch
        import time

        fake_scraper = MagicMock()
        fake_scraper.scrape_track.side_effect = RuntimeError("Scraper crashed")

        downloader = SpotDownloader(download_path=str(tmp_path), scraper=fake_scraper)
        handle = downloader.download('https://open.spotify.com/track/abc')

        def _wait(handle, timeout=5):
            start = time.time()
            while time.time() - start < timeout:
                r = handle.result(timeout=0.1)
                if r is not None:
                    return r
            return None

        result = _wait(handle)
        assert result is not None
        assert result.status == 'failed'

    def test_cancel_stops_download(self, tmp_path):
        """Cancelling a DownloadHandle returns cancelled status and skips remaining tracks."""
        from unittest.mock import MagicMock, patch
        import time

        def delayed_scrape(url, headless=True, log_callback=None):
            time.sleep(0.5)
            return {
                'name': 'Cancel Test',
                'tracks': {
                    'items': [
                        {'track': {'name': 'Song 1', 'artists': [{'name': 'Artist A'}], 'duration_ms': 180000, 'album': {'name': 'Album X'}}},
                        {'track': {'name': 'Song 2', 'artists': [{'name': 'Artist B'}], 'duration_ms': 200000, 'album': {'name': 'Album Y'}}},
                    ]
                }
            }

        fake_scraper = MagicMock()
        fake_scraper.scrape_playlist.side_effect = delayed_scrape

        with patch('spot_downloader.core.downloader.YouTubeSearcher') as MockSearcher:
            MockSearcher.search_ytm.return_value = 'https://youtube.com/watch?v=test'

            with patch('spot_downloader.core.downloader.yt_dlp.YoutubeDL') as MockYDL:
                mock_ydl = MagicMock()
                MockYDL.return_value.__enter__.return_value = mock_ydl

                with patch('spot_downloader.core.downloader.tag_mp3', return_value=True):
                    downloader = SpotDownloader(download_path=str(tmp_path), scraper=fake_scraper)
                    handle = downloader.download('https://open.spotify.com/playlist/test')
                    assert handle is not None
                    time.sleep(0.1)
                    handle.cancel()
                    result = handle.result(timeout=10)
                    assert result.status == 'cancelled'
                    assert result.track_count == 2

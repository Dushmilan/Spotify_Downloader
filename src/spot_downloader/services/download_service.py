"""
Service layer for the Spotify Downloader application.
Separates business logic from UI components.
"""

from typing import Callable, Optional
from ..core.downloader import SpotDownloader
from ..utils.validation import validate_spotify_url
from ..config import app_config
from ..tracker import DownloadTracker


class DownloadService:
    """Service class to handle download operations."""

    def __init__(self):
        self.downloader = SpotDownloader()
        self._tracker = DownloadTracker()

    @property
    def tracker(self):
        """Return the download tracker."""
        return self._tracker

    @tracker.setter
    def tracker(self, value):
        """Set the download tracker."""
        self._tracker = value
    
    def download(self, url: str, progress_callback: Optional[Callable] = None, log_callback: Optional[Callable] = None, tracker_callback: Optional[Callable] = None):
        """
        Initiate a download operation.

        Args:
            url: The URL to download from
            progress_callback: Callback for progress updates
            log_callback: Callback for log messages
            tracker_callback: Callback for tracker updates
        """
        # Validate URL if safe mode is enabled
        if app_config.safe_mode and not validate_spotify_url(url):
            if log_callback:
                log_callback("Invalid Spotify URL. Please enter a valid Spotify track, playlist, or album URL.")
            return None

        # Pass the tracker to the downloader so it can update progress
        return self.downloader.download(url, progress_callback=progress_callback, log_callback=log_callback, tracker=self.tracker)
    
    def set_download_path(self, path: str):
        """Set the download path."""
        self.downloader.set_download_path(path)
    
    @property
    def download_path(self) -> str:
        """Get the current download path."""
        return self.downloader.download_path


class ValidationService:
    """Service class to handle validation operations."""
    
    @staticmethod
    def validate_spotify_url(url: str) -> bool:
        """Validate a Spotify URL."""
        return validate_spotify_url(url)
    
    @staticmethod
    def is_safe_url(url: str) -> bool:
        """Check if a URL is safe to use."""
        from ..utils.validation import is_safe_url
        return is_safe_url(url)
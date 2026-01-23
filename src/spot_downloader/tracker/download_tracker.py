"""
Download tracker module for the Spotify Downloader application.
Manages concurrent downloads with progress tracking.
"""

from typing import Dict, List, Optional, Callable
import threading
from dataclasses import dataclass
from enum import Enum


class DownloadStatus(Enum):
    """Enum for download statuses."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DownloadItem:
    """Represents a single download item."""
    id: str
    title: str
    artist: str
    status: DownloadStatus
    progress: float = 0.0  # 0.0 to 1.0
    error_message: Optional[str] = None
    download_path: Optional[str] = None


class DownloadTracker:
    """Tracks multiple concurrent downloads with progress information."""

    def __init__(self):
        self._downloads: Dict[str, DownloadItem] = {}
        self._lock = threading.Lock()
        self._progress_callbacks: Dict[str, Callable[[float], None]] = {}
        self._status_callbacks: Dict[str, Callable[[DownloadStatus], None]] = {}
        self._on_change_callback: Optional[Callable[[], None]] = None
    
    def add_download(self, download_id: str, title: str, artist: str) -> DownloadItem:
        """Add a new download to track."""
        with self._lock:
            item = DownloadItem(
                id=download_id,
                title=title,
                artist=artist,
                status=DownloadStatus.QUEUED
            )
            self._downloads[download_id] = item
            return item
    
    def update_status(self, download_id: str, status: DownloadStatus):
        """Update the status of a download."""
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].status = status
                # Notify status callback if registered
                if download_id in self._status_callbacks:
                    self._status_callbacks[download_id](status)
    
    def update_progress(self, download_id: str, progress: float):
        """Update the progress of a download."""
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].progress = progress
                # Notify progress callback if registered
                if download_id in self._progress_callbacks:
                    self._progress_callbacks[download_id](progress)
    
    def set_error(self, download_id: str, error_message: str):
        """Set an error for a download."""
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].status = DownloadStatus.FAILED
                self._downloads[download_id].error_message = error_message
    
    def set_completed(self, download_id: str, download_path: str = ""):
        """Mark a download as completed."""
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].status = DownloadStatus.COMPLETED
                self._downloads[download_id].download_path = download_path
    
    def get_download(self, download_id: str) -> Optional[DownloadItem]:
        """Get a specific download item."""
        with self._lock:
            return self._downloads.get(download_id)
    
    def get_downloads_by_status(self, status: DownloadStatus) -> List[DownloadItem]:
        """Get all downloads with a specific status."""
        with self._lock:
            return [item for item in self._downloads.values() if item.status == status]
    
    def get_all_downloads(self) -> List[DownloadItem]:
        """Get all downloads."""
        with self._lock:
            return list(self._downloads.values())
    
    def register_progress_callback(self, download_id: str, callback: Callable[[float], None]):
        """Register a callback for progress updates."""
        self._progress_callbacks[download_id] = callback
    
    def register_status_callback(self, download_id: str, callback: Callable[[DownloadStatus], None]):
        """Register a callback for status updates."""
        self._status_callbacks[download_id] = callback

    def set_on_change_callback(self, callback: Callable[[], None]):
        """Set a callback to be called when any download changes."""
        self._on_change_callback = callback

    def _trigger_change_callback(self):
        """Trigger the change callback if set."""
        if self._on_change_callback:
            # Call the callback in a thread-safe way
            try:
                self._on_change_callback()
            except:
                pass  # Ignore errors in callbacks

    def get_summary(self) -> Dict[str, int]:
        """Get a summary of download counts by status."""
        with self._lock:
            summary = {
                DownloadStatus.QUEUED.value: 0,
                DownloadStatus.DOWNLOADING.value: 0,
                DownloadStatus.COMPLETED.value: 0,
                DownloadStatus.FAILED.value: 0
            }

            for item in self._downloads.values():
                summary[item.status.value] += 1

            return summary

    def get_all_downloads(self) -> List[DownloadItem]:
        """Get all downloads."""
        with self._lock:
            return list(self._downloads.values())

    def update_status(self, download_id: str, status: DownloadStatus):
        """Update the status of a download."""
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].status = status
                # Notify status callback if registered
                if download_id in self._status_callbacks:
                    self._status_callbacks[download_id](status)
                # Trigger change callback
                self._trigger_change_callback()

    def update_progress(self, download_id: str, progress: float):
        """Update the progress of a download."""
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].progress = progress
                # Notify progress callback if registered
                if download_id in self._progress_callbacks:
                    self._progress_callbacks[download_id](progress)
                # Trigger change callback
                self._trigger_change_callback()

    def set_error(self, download_id: str, error_message: str):
        """Set an error for a download."""
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].status = DownloadStatus.FAILED
                self._downloads[download_id].error_message = error_message
                # Trigger change callback
                self._trigger_change_callback()

    def set_completed(self, download_id: str, download_path: str = ""):
        """Mark a download as completed."""
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].status = DownloadStatus.COMPLETED
                self._downloads[download_id].download_path = download_path
                # Trigger change callback
                self._trigger_change_callback()
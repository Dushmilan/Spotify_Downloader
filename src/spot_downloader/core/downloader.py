import os
import threading
import subprocess
import concurrent.futures
import json  # Import json for handling fake data
from ..utils.validation import validate_spotify_url, sanitize_filename, validate_download_path, is_safe_url
from ..utils.error_handling import handle_download_error, DownloadError, DownloadErrorType, ProcessingError
from ..config import app_config
from ..tracker import DownloadStatus

class SpotDownloader:
    def __init__(self, download_path=None):
        # Use config value if no path provided
        if download_path is None:
            download_path = app_config.download_path

        # If download_path is an absolute path, use it directly
        if os.path.isabs(download_path):
            self.download_path = download_path
        else:
            # Validate and sanitize the download path as a subdirectory
            self.download_path = validate_download_path(os.getcwd(), download_path)

        self.client_id = None
        self.client_secret = None
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def set_download_path(self, new_path):
        # If new_path is an absolute path, use it directly
        if os.path.isabs(new_path):
            self.download_path = new_path
        else:
            # Validate and sanitize the new download path as a subdirectory
            self.download_path = validate_download_path(os.getcwd(), new_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _download_track(self, meta, engine, progress_callback=None, log_callback=None, tracker=None):
        """Helper function to download a single track, suitable for ThreadPoolExecutor."""
        track_name = meta.get('name', 'Unknown Track')
        track_artist = meta.get('artist', 'Unknown Artist')

        # Generate a unique ID for this download
        import uuid
        download_id = str(uuid.uuid4())

        try:
            # Add to tracker
            if tracker:
                tracker.add_download(download_id, track_name, track_artist)
                tracker.update_status(download_id, DownloadStatus.DOWNLOADING)

                # Register callbacks to update the tracker
                def progress_update(progress):
                    if tracker:
                        tracker.update_progress(download_id, progress)

                def status_update(status):
                    if tracker:
                        tracker.update_status(download_id, status)

                # Modify the progress callback to also update the tracker
                original_progress_callback = progress_callback
                def combined_progress_callback(progress):
                    if original_progress_callback:
                        original_progress_callback(progress)
                    progress_update(progress)

                progress_callback = combined_progress_callback

            if log_callback:
                log_callback(f"Processing track: {track_name} in {meta.get('output_dir', 'default')}")

            success = engine.download_and_tag(meta, progress_callback, log_callback)
            if success:
                if log_callback:
                    log_callback(f"Download of '{track_name}' completed successfully!")
                if tracker:
                    tracker.update_status(download_id, DownloadStatus.COMPLETED)
            else:
                if log_callback:
                    log_callback(f"Failed to download: {track_name}")
                if tracker:
                    tracker.set_error(download_id, "Download failed")
            return success
        except Exception as e:
            handle_download_error(e, log_callback, f"Downloading {track_name}")
            if tracker:
                tracker.set_error(download_id, str(e))
            return False

    def download(self, url, progress_callback=None, log_callback=None, tracker=None):
        """
        Downloads a song or playlist concurrently using the Custom Engine.
        Spotify metadata fetching is replaced with hardcoded fake data for testing.
        """
        # Validate the input URL
        if not url or not isinstance(url, str):
            if log_callback:
                log_callback("Error: Invalid URL provided.")
            return None

        # Sanitize and validate the URL
        url = url.strip()

        # Check if it's a potentially unsafe URL
        if not is_safe_url(url):
            if log_callback:
                log_callback("Error: Unsafe URL provided.")
            return None

        
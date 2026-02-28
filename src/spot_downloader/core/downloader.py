"""
Core downloader module for the Spotify Downloader.
Handles download orchestration and track processing.
"""

import os
import threading
import subprocess
import concurrent.futures
import json
import uuid
from typing import Optional, Callable, List, Dict, Any, Union
from ..utils.validation import validate_spotify_url, sanitize_filename, validate_download_path, is_safe_url
from ..utils.error_handling import handle_download_error, DownloadError, DownloadErrorType, ProcessingError
from ..utils.logger import get_logger
from ..utils.retry import retry
from ..config import app_config
from ..tracker import DownloadStatus, DownloadTracker

logger = get_logger(__name__)


class SpotDownloader:
    """Main downloader class for handling Spotify downloads."""

    def __init__(self, download_path: Optional[str] = None):
        if download_path is None:
            download_path = app_config.download_path

        if os.path.isabs(download_path):
            self.download_path = download_path
        else:
            self.download_path = validate_download_path(os.getcwd(), download_path)

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
            
        self._cancelled = False

    def set_download_path(self, new_path: str) -> None:
        """Set a new download path."""
        if os.path.isabs(new_path):
            self.download_path = new_path
        else:
            self.download_path = validate_download_path(os.getcwd(), new_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def cancel_all(self) -> None:
        """Signal all active downloads to stop."""
        self._cancelled = True
        logger.info("Cancellation signal sent to all downloads.")

    @retry(max_attempts=2, delay=1.0)
    def _download_track(
        self, 
        meta: Dict[str, Any], 
        engine: Any, 
        progress_callback: Optional[Callable[[float], None]] = None, 
        log_callback: Optional[Callable[[str], None]] = None, 
        tracker: Optional[DownloadTracker] = None
    ) -> bool:
        """Helper function to download a single track."""
        if self._cancelled:
            return False
            
        track_name = meta.get('name', 'Unknown Track')
        track_artist = meta.get('artist', 'Unknown Artist')
        download_id = meta.get('download_id') or str(uuid.uuid4())

        try:
            if tracker:
                # Only add if it doesn't exist
                if not any(d.id == download_id for d in tracker.get_all_downloads()):
                    tracker.add_download(download_id, track_name, track_artist)
                
                tracker.update_status(download_id, DownloadStatus.DOWNLOADING)

                def progress_update(progress: float):
                    if tracker:
                        tracker.update_progress(download_id, progress)

                original_progress_callback = progress_callback
                def combined_progress_callback(progress: float):
                    if original_progress_callback:
                        original_progress_callback(progress)
                    progress_update(progress)

                progress_callback = combined_progress_callback

            if log_callback:
                log_callback(f"Processing track: {track_name}")

            success = engine.download_and_tag(meta, progress_callback, log_callback)
            
            if self._cancelled:
                if tracker: tracker.update_status(download_id, DownloadStatus.FAILED)
                return False

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

    def download(
        self, 
        url: str, 
        progress_callback: Optional[Callable[[float], None]] = None, 
        log_callback: Optional[Callable[[str], None]] = None, 
        tracker: Optional[DownloadTracker] = None
    ) -> threading.Thread:
        """
        Downloads a song or playlist concurrently using the Custom Engine.
        """
        self._cancelled = False
        if not url or not isinstance(url, str):
            if log_callback:
                log_callback("Error: Invalid URL provided.")
            return None

        url = url.strip()

        if not is_safe_url(url):
            if log_callback:
                log_callback("Error: Unsafe URL provided.")
            return None

        def run():
            from .custom_engine import CustomDownloadEngine
            from ..utils.selenium_scraper import scrape_playlist, scrape_track, scrape_album

            cache_file_path = None
            engine = None
            try:
                if log_callback:
                    log_callback(f"Initiating download for: {url}")

                engine = CustomDownloadEngine(self.download_path)
                metadata_list = []

                if validate_spotify_url(url):
                    if log_callback:
                        log_callback("Validated as Spotify URL")

                    if "playlist" in url:
                        try:
                            playlist_data = scrape_playlist(url, headless=True, log_callback=log_callback)

                            if not playlist_data:
                                raise ProcessingError("Failed to scrape playlist - no data returned")

                        except Exception as e:
                            handle_download_error(e, log_callback, "Scraping playlist with Selenium")
                            raise ProcessingError(f"Playlist scraping failed: {e}")

                        playlist_name = playlist_data.get('name', 'Unknown Playlist')
                        safe_playlist_name = sanitize_filename(playlist_name)
                        playlist_folder = os.path.join(self.download_path, safe_playlist_name or "Unknown_Playlist")

                        if not os.path.exists(playlist_folder):
                            os.makedirs(playlist_folder)

                        cache_file = os.path.join(playlist_folder, "playlist.json")
                        cache_file_path = cache_file
                        try:
                            def clean_for_json(obj):
                                if isinstance(obj, set): return list(obj)
                                if isinstance(obj, dict): return {k: clean_for_json(v) for k, v in obj.items()}
                                if isinstance(obj, list): return [clean_for_json(i) for i in obj]
                                return obj

                            with open(cache_file, "w", encoding="utf-8") as f:
                                json.dump(clean_for_json(playlist_data), f, indent=2)
                        except Exception as e:
                            logger.error(f"Failed to save playlist cache: {e}")

                        tracks_container = playlist_data.get('tracks', playlist_data.get('items', []))
                        tracks = tracks_container.get('items', []) if isinstance(tracks_container, dict) else tracks_container

                        if log_callback:
                            log_callback(f"Found {len(tracks)} tracks. Processing list...")

                        for item in tracks:
                            if self._cancelled: break
                            track_data = item.get('track', item) if isinstance(item, dict) else item
                            if not isinstance(track_data, dict): continue

                            song_name = track_data.get('name', 'Unknown Track')
                            artists = track_data.get('artists', [])
                            artist_name = artists[0].get('name', 'Unknown Artist') if artists and isinstance(artists[0], dict) else 'Unknown Artist'

                            file_name = sanitize_filename(f"{song_name} - {artist_name}")
                            expected_path = os.path.join(playlist_folder, f"{file_name or 'track'}.mp3")

                            if os.path.exists(expected_path):
                                continue

                            metadata_list.append({
                                'name': song_name,
                                'artist': artist_name,
                                'duration_ms': track_data.get('duration_ms'),
                                'album': track_data.get('album', {}).get('name', ''),
                                'output_dir': playlist_folder,
                                'playlist_name': playlist_name,
                                'download_id': str(uuid.uuid4())
                            })

                    elif "track" in url:
                        try:
                            track_info = scrape_track(url, headless=True, log_callback=log_callback)
                            if track_info:
                                artists = track_info.get('artists', [])
                                metadata_list.append({
                                    'name': track_info.get('name', 'Unknown Track'),
                                    'artist': artists[0].get('name', 'Unknown Artist') if artists else 'Unknown Artist',
                                    'duration_ms': track_info.get('duration_ms'),
                                    'album': track_info.get('album', {}).get('name', ''),
                                    'download_id': str(uuid.uuid4())
                                })
                        except Exception as e:
                            handle_download_error(e, log_callback, "Scraping track with Selenium")

                    elif "album" in url:
                        try:
                            album_info = scrape_album(url, headless=True, log_callback=log_callback)
                            if album_info:
                                album_name = album_info.get('name', 'Unknown Album')
                                tracks_data = album_info.get('tracks', album_info.get('items', []))
                                album_folder = os.path.join(self.download_path, sanitize_filename(album_name) or "Album")
                                if not os.path.exists(album_folder): os.makedirs(album_folder)

                                for track_item in tracks_data:
                                    if self._cancelled: break
                                    track_data = track_item.get('track', track_item)
                                    artists = track_data.get('artists', [])
                                    metadata_list.append({
                                        'name': track_data.get('name', 'Unknown Track'),
                                        'artist': artists[0].get('name', 'Unknown Artist') if artists else 'Unknown Artist',
                                        'duration_ms': track_data.get('duration_ms'),
                                        'album': album_name,
                                        'output_dir': album_folder,
                                        'download_id': str(uuid.uuid4())
                                    })
                        except Exception as e:
                            handle_download_error(e, log_callback, "Scraping album with Selenium")
                else:
                    metadata_list.append({'name': url, 'artist': '', 'download_id': str(uuid.uuid4())})

                if metadata_list:
                    if len(metadata_list) > 1:
                        max_workers = app_config.max_concurrent_downloads
                        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                            futures = [
                                executor.submit(self._download_track, meta, engine, progress_callback, log_callback, tracker)
                                for meta in metadata_list
                            ]
                            for future in concurrent.futures.as_completed(futures):
                                if self._cancelled: break
                                try: future.result()
                                except Exception as exc: logger.error(f"Worker error: {exc}")
                    else:
                        self._download_track(metadata_list[0], engine, progress_callback, log_callback, tracker)

            except Exception as e:
                handle_download_error(e, log_callback, "Main download process")
            finally:
                if cache_file_path and os.path.exists(cache_file_path) and not self._cancelled:
                    try: os.remove(cache_file_path)
                    except: pass

        thread = threading.Thread(target=run, daemon=True, name="DownloaderThread")
        thread.start()
        return thread

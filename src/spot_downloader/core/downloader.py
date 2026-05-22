"""
Core downloader module for the Spotify Downloader.
Handles download orchestration and track processing.
"""

import os
import threading
import concurrent.futures
import json
import uuid
import yt_dlp
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any, Union
from ..utils.validation import validate_spotify_url, sanitize_filename, validate_download_path, is_safe_url
from ..utils.error_handling import handle_download_error, DownloadError, DownloadErrorType, ProcessingError
from ..utils.logger import get_logger
from ..utils.retry import retry
from ..utils.tagger import tag_mp3, tag_m4a
from ..utils.throttle import Throttler
from ..utils.helpers import get_ffmpeg_path
from ..config import app_config
from ..tracker import DownloadStatus, DownloadTracker
from .searcher import YouTubeSearcher

logger = get_logger(__name__)


@dataclass
class DownloadResult:
    status: str  # 'completed', 'failed', 'cancelled'
    track_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    error_message: Optional[str] = None


class DownloadHandle:
    def __init__(self):
        self._progress_callbacks: List[Callable[[float], None]] = []
        self._log_callbacks: List[Callable[[str], None]] = []
        self._result: Optional[DownloadResult] = None
        self._event = threading.Event()
        self._cancelled = False

    def on_progress(self, callback: Callable[[float], None]):
        self._progress_callbacks.append(callback)

    def on_log(self, callback: Callable[[str], None]):
        self._log_callbacks.append(callback)

    def _report_progress(self, progress: float):
        for cb in self._progress_callbacks:
            try:
                cb(progress)
            except Exception:
                pass

    def _report_log(self, msg: str):
        for cb in self._log_callbacks:
            try:
                cb(msg)
            except Exception:
                pass

    def _complete(self, result: DownloadResult):
        self._result = result
        self._event.set()

    def result(self, timeout: Optional[float] = None) -> Optional[DownloadResult]:
        self._event.wait(timeout=timeout)
        return self._result

    def cancel(self):
        self._cancelled = True


class SpotDownloader:
    """Main downloader class for handling Spotify downloads."""

    def __init__(self, download_path: Optional[str] = None, scraper=None):
        if download_path is None:
            download_path = app_config.download_path

        if os.path.isabs(download_path):
            self.download_path = download_path
        else:
            self.download_path = validate_download_path(os.getcwd(), download_path)

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self._cancelled = False
        self._tracker = DownloadTracker()

        if scraper is None:
            from ..utils.playwright_scraper import PlaywrightScraper
            self.scraper = PlaywrightScraper()
        else:
            self.scraper = scraper

    def set_download_path(self, new_path: str) -> None:
        """Set a new download path."""
        if os.path.isabs(new_path):
            self.download_path = new_path
        else:
            self.download_path = validate_download_path(os.getcwd(), new_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    @property
    def tracker(self) -> DownloadTracker:
        return self._tracker

    def cancel_all(self) -> None:
        """Signal all active downloads to stop."""
        self._cancelled = True
        logger.info("Cancellation signal sent to all downloads.")

    @retry(max_attempts=3, delay=2.0, exceptions=(yt_dlp.utils.DownloadError, ConnectionError))
    def _download_and_tag(self, metadata: Dict[str, Any], handle: DownloadHandle) -> bool:
        """Full pipeline: Search -> Download -> Tag"""
        target_path = metadata.get('output_dir', self.download_path)
        if not os.path.exists(target_path):
            os.makedirs(target_path)

        song_name = metadata.get('name', 'Unknown Song')
        artist_name = metadata.get('artist', 'Unknown Artist')

        file_name = f"{song_name} - {artist_name}"
        file_name = sanitize_filename(file_name)
        if not file_name or file_name.isspace():
            file_name = "Unknown_Song - Unknown_Artist"

        final_file_path = os.path.join(target_path, f"{file_name}.mp3")

        handle._report_log(f"Checking existence for: {file_name}")

        if os.path.exists(final_file_path):
            handle._report_log(f"Skipping: '{file_name}' already exists in {os.path.basename(target_path)}/")
            handle._report_progress(1.0)
            return True

        query = metadata.get('query')
        if not query:
            query = f"{song_name} {artist_name}".strip()

        if handle._cancelled or self._cancelled:
            return False

        handle._report_log(f"Searching for better match: {query}...")

        try:
            video_url = YouTubeSearcher.search_ytm(
                query,
                duration_ms=metadata.get('duration_ms'),
                artist=artist_name
            )
            if not video_url:
                handle._report_log("Error: No match found on YouTube Music.")
                return False
        except Exception as e:
            handle._report_log(f"Search error: {str(e)}")
            return False

        handle._report_log(f"Downloading from: {video_url}")

        output_path = os.path.join(target_path, f"{file_name}.%(ext)s")

        progress_throttler = Throttler(0.1)

        def ydl_progress_hook(d: Dict[str, Any]):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded_bytes = d.get('downloaded_bytes', 0)

                if total_bytes > 0:
                    mb_total = total_bytes / (1024 * 1024)
                    mb_downloaded = downloaded_bytes / (1024 * 1024)
                    if log_callback and downloaded_bytes % (2 * 1024 * 1024) < 100000:
                        pass

                if progress_callback:
                    p = d.get('_percent_str', '0%').replace('%', '').strip()
                    try:
                        progress_val = float(p) / 100
                        progress_throttler(progress_callback, progress_val)
                    except (ValueError, TypeError):
                        pass
            elif d['status'] == 'finished':
                final_bytes = d.get('total_bytes') or d.get('downloaded_bytes', 0)
                mb_final = final_bytes / (1024 * 1024)
                handle._report_log(f"Download complete ({mb_final:.2f}MB), post-processing...")

        quality_map = {
            '128kbps': '128',
            '256kbps': '256',
            '320kbps': '320'
        }
        preferred_quality = quality_map.get(app_config.download_quality, '320')

        ffmpeg_exe = get_ffmpeg_path()

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': app_config.file_format,
                'preferredquality': preferred_quality,
            }],
            'audio_quality': 0,
            'progress_hooks': [ydl_progress_hook],
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': app_config.timeout_seconds,
            'connect_timeout': app_config.timeout_seconds,
            'retries': app_config.retry_attempts,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['dash', 'hls']
                }
            },
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'http_headers': {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://www.youtube.com',
                'Sec-Fetch-Mode': 'navigate',
            }
        }

        if ffmpeg_exe:
            ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_exe)

        progress_callback = None
        if handle._progress_callbacks:
            progress_callback = handle._report_progress

        log_callback = None
        if handle._log_callbacks:
            log_callback = handle._report_log

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            final_file = os.path.join(target_path, f"{file_name}.mp3")

            if os.path.exists(final_file):
                handle._report_log(f"Embedding metadata for: {file_name}")
                tag_mp3(final_file, metadata)
                handle._report_log(f"Successfully downloaded and tagged: {file_name}")
                return True
            else:
                logger.error(f"Downloaded file not found after conversion: {final_file}")
                handle._report_log("Error: Downloaded file not found after conversion.")
                return False

        except Exception as e:
            logger.error(f"Unexpected download error: {str(e)}")
            handle._report_log(f"Unexpected download error: {str(e)}")
            return False

    def _scrape_and_build_metadata(self, url: str, handle: DownloadHandle) -> List[Dict[str, Any]]:
        """Scrape Spotify URL and build metadata list. Returns empty list on failure."""
        metadata_list: List[Dict[str, Any]] = []

        if not validate_spotify_url(url):
            handle._report_log("URL is not a valid Spotify URL.")
            return metadata_list

        handle._report_log("Validated as Spotify URL")

        if "playlist" in url:
            try:
                playlist_data = self.scraper.scrape_playlist(url, headless=True, log_callback=handle._report_log)
                if not playlist_data:
                    raise ProcessingError("Failed to scrape playlist - no data returned")
            except Exception as e:
                handle_download_error(e, handle._report_log, f"Scraping playlist with {self.scraper.__class__.__name__}")
                raise ProcessingError(f"Playlist scraping failed: {e}")

            playlist_name = playlist_data.get('name', 'Unknown Playlist')
            safe_playlist_name = sanitize_filename(playlist_name)
            playlist_folder = os.path.join(self.download_path, safe_playlist_name or "Unknown_Playlist")
            if not os.path.exists(playlist_folder):
                os.makedirs(playlist_folder)

            cache_file = os.path.join(playlist_folder, "playlist.json")
            try:
                def clean_for_json(obj):
                    if isinstance(obj, set):
                        return list(obj)
                    if isinstance(obj, dict):
                        return {k: clean_for_json(v) for k, v in obj.items()}
                    if isinstance(obj, list):
                        return [clean_for_json(i) for i in obj]
                    return obj
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(clean_for_json(playlist_data), f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save playlist cache: {e}")

            tracks_container = playlist_data.get('tracks', playlist_data.get('items', []))
            tracks = tracks_container.get('items', []) if isinstance(tracks_container, dict) else tracks_container

            handle._report_log(f"Found {len(tracks)} tracks. Processing list...")

            for item in tracks:
                if self._cancelled:
                    break
                track_data = item.get('track') if (isinstance(item, dict) and 'track' in item) else item
                if not isinstance(track_data, dict) or not track_data:
                    continue

                song_name = track_data.get('name', 'Unknown Track')
                artists = track_data.get('artists', [])
                if artists and isinstance(artists[0], dict):
                    artist_name = artists[0].get('name', 'Unknown Artist')
                elif artists and isinstance(artists[0], str):
                    artist_name = artists[0]
                else:
                    artist_name = 'Unknown Artist'

                file_name = sanitize_filename(f"{song_name} - {artist_name}")
                expected_path = os.path.join(playlist_folder, f"{file_name or 'track'}.mp3")
                if os.path.exists(expected_path):
                    continue

                metadata_list.append({
                    'name': song_name,
                    'artist': artist_name,
                    'duration_ms': track_data.get('duration_ms'),
                    'album': track_data.get('album', {}).get('name', '') if isinstance(track_data.get('album'), dict) else '',
                    'output_dir': playlist_folder,
                    'playlist_name': playlist_name,
                    'download_id': str(uuid.uuid4())
                })

        elif "track" in url:
            try:
                track_info = self.scraper.scrape_track(url, headless=True, log_callback=handle._report_log)
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
                handle_download_error(e, handle._report_log, f"Scraping track with {self.scraper.__class__.__name__}")

        elif "album" in url:
            try:
                album_info = self.scraper.scrape_album(url, headless=True, log_callback=handle._report_log)
                if album_info:
                    album_name = album_info.get('name', 'Unknown Album')
                    tracks_data = album_info.get('tracks', album_info.get('items', []))
                    album_folder = os.path.join(self.download_path, sanitize_filename(album_name) or "Album")
                    if not os.path.exists(album_folder):
                        os.makedirs(album_folder)
                    for track_item in tracks_data:
                        if self._cancelled:
                            break
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
                handle_download_error(e, handle._report_log, f"Scraping album with {self.scraper.__class__.__name__}")

        return metadata_list

    def _download_track(self, meta: Dict[str, Any], handle: DownloadHandle) -> bool:
        """Download a single track with progress and log reporting through the handle."""
        if self._cancelled or handle._cancelled:
            return False

        track_name = meta.get('name', 'Unknown Track')
        track_artist = meta.get('artist', 'Unknown Artist')
        download_id = meta.get('download_id') or str(uuid.uuid4())

        if not any(d.id == download_id for d in self._tracker.get_all_downloads()):
            self._tracker.add_download(download_id, track_name, track_artist)
        self._tracker.update_status(download_id, DownloadStatus.DOWNLOADING)

        handle._report_log(f"Processing track: {track_name}")

        original_progress = handle._report_progress
        def combined_progress(progress: float):
            self._tracker.update_progress(download_id, progress)
            original_progress(progress)
        handle._report_progress = combined_progress

        success = self._download_and_tag(meta, handle)

        handle._report_progress = original_progress

        if self._cancelled or handle._cancelled:
            self._tracker.update_status(download_id, DownloadStatus.FAILED)
            return False

        if success:
            handle._report_log(f"Download of '{track_name}' completed successfully!")
            self._tracker.update_status(download_id, DownloadStatus.COMPLETED)
        else:
            handle._report_log(f"Failed to download: {track_name}")
            self._tracker.set_error(download_id, "Download failed")
        return success

    def download(self, url: str) -> Optional[DownloadHandle]:
        """
        Download a track, playlist, or album from a Spotify URL.
        Returns a DownloadHandle for monitoring and cancellation.
        """
        self._cancelled = False

        if not url or not isinstance(url, str):
            logger.error("Invalid URL provided.")
            return None

        url = url.strip()

        if not is_safe_url(url):
            logger.error("Unsafe URL provided.")
            return None

        handle = DownloadHandle()

        def run():
            try:
                handle._report_log(f"Initiating download for: {url}")

                metadata_list = self._scrape_and_build_metadata(url, handle)

                success_count = 0
                failure_count = 0

                if self._cancelled or handle._cancelled:
                    handle._complete(DownloadResult(
                        status='cancelled',
                        track_count=len(metadata_list)
                    ))
                    return

                if not metadata_list:
                    handle._report_log("No tracks found to download.")
                    handle._complete(DownloadResult(
                        status='failed',
                        track_count=0,
                        error_message="No tracks found"
                    ))
                    return

                if len(metadata_list) > 1:
                    max_workers = app_config.max_concurrent_downloads
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(self._download_track, meta, handle): meta
                            for meta in metadata_list
                        }
                        for future in concurrent.futures.as_completed(futures):
                            if self._cancelled or handle._cancelled:
                                break
                            try:
                                if future.result():
                                    success_count += 1
                                else:
                                    failure_count += 1
                            except Exception as exc:
                                logger.error(f"Worker error: {exc}")
                                failure_count += 1
                else:
                    if self._cancelled or handle._cancelled:
                        handle._complete(DownloadResult(
                            status='cancelled',
                            track_count=1
                        ))
                        return
                    if self._download_track(metadata_list[0], handle):
                        success_count += 1
                    else:
                        failure_count += 1

                total = len(metadata_list)
                if self._cancelled or handle._cancelled:
                    handle._complete(DownloadResult(
                        status='cancelled',
                        track_count=total,
                        success_count=success_count,
                        failure_count=failure_count
                    ))
                elif failure_count > 0:
                    handle._complete(DownloadResult(
                        status='failed',
                        track_count=total,
                        success_count=success_count,
                        failure_count=failure_count
                    ))
                else:
                    handle._complete(DownloadResult(
                        status='completed',
                        track_count=total,
                        success_count=success_count,
                        failure_count=failure_count
                    ))

                handle._report_log("All downloads finished!")

            except Exception as e:
                handle_download_error(e, handle._report_log, "Main download process")
                handle._complete(DownloadResult(
                    status='failed',
                    error_message=str(e)
                ))

        thread = threading.Thread(target=run, daemon=True, name="DownloaderThread")
        thread.start()
        return handle

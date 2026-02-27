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
from ..utils.validation import validate_spotify_url, sanitize_filename, validate_download_path, is_safe_url
from ..utils.error_handling import handle_download_error, DownloadError, DownloadErrorType, ProcessingError
from ..utils.logger import get_logger
from ..config import app_config
from ..tracker import DownloadStatus

logger = get_logger(__name__)


class SpotDownloader:
    """Main downloader class for handling Spotify downloads."""

    def __init__(self, download_path=None):
        if download_path is None:
            download_path = app_config.download_path

        if os.path.isabs(download_path):
            self.download_path = download_path
        else:
            self.download_path = validate_download_path(os.getcwd(), download_path)

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def set_download_path(self, new_path):
        """Set a new download path."""
        if os.path.isabs(new_path):
            self.download_path = new_path
        else:
            self.download_path = validate_download_path(os.getcwd(), new_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _download_track(self, meta, engine, progress_callback=None, log_callback=None, tracker=None):
        """Helper function to download a single track."""
        track_name = meta.get('name', 'Unknown Track')
        track_artist = meta.get('artist', 'Unknown Artist')
        download_id = str(uuid.uuid4())

        try:
            if tracker:
                tracker.add_download(download_id, track_name, track_artist)
                tracker.update_status(download_id, DownloadStatus.DOWNLOADING)

                def progress_update(progress):
                    if tracker:
                        tracker.update_progress(download_id, progress)

                def status_update(status):
                    if tracker:
                        tracker.update_status(download_id, status)

                original_progress_callback = progress_callback
                def combined_progress_callback(progress):
                    if original_progress_callback:
                        original_progress_callback(progress)
                    progress_update(progress)

                progress_callback = combined_progress_callback

            if log_callback:
                log_callback(f"Processing track: {track_name}")

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
        """
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
            from spotify_scraper import SpotifyClient

            cache_file_path = None
            engine = None
            try:
                if log_callback:
                    log_callback(f"Initiating download for: {url}")

                if log_callback:
                    log_callback("Running Custom Download Engine...")

                engine = CustomDownloadEngine(self.download_path)
                metadata_list = []

                if validate_spotify_url(url):
                    if log_callback:
                        log_callback("Validated as Spotify URL")

                    if "playlist" in url:
                        if log_callback:
                            log_callback("Using Selenium to scrape playlist tracks...")

                        try:
                            from ..utils.selenium_scraper import scrape_playlist
                            playlist_data = scrape_playlist(url, headless=True, log_callback=log_callback)

                            if not playlist_data:
                                raise ProcessingError("Failed to scrape playlist - no data returned")

                            if log_callback:
                                log_callback("Successfully scraped playlist data")

                        except Exception as e:
                            handle_download_error(e, log_callback, "Scraping playlist with Selenium")
                            raise ProcessingError(f"Playlist scraping failed: {e}")

                        playlist_name = playlist_data.get('name', 'Unknown Playlist')
                        safe_playlist_name = sanitize_filename(playlist_name)
                        if not safe_playlist_name:
                            safe_playlist_name = "Unknown_Playlist"

                        playlist_folder = os.path.join(self.download_path, safe_playlist_name)

                        if not os.path.exists(playlist_folder):
                            os.makedirs(playlist_folder)

                        cache_file = os.path.join(playlist_folder, "playlist.json")
                        cache_file_path = cache_file
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
                            if log_callback:
                                log_callback(f"Failed to save playlist cache: {e}")

                        tracks_container = playlist_data.get('tracks', playlist_data.get('items', []))
                        if isinstance(tracks_container, dict):
                            tracks = tracks_container.get('items', [])
                        else:
                            tracks = tracks_container if isinstance(tracks_container, list) else []

                        if log_callback:
                            log_callback(f"Found {len(tracks)} tracks in '{playlist_name}'. Processing list...")

                        skipped_count = 0
                        for item in tracks:
                            track_data = item.get('track', item) if isinstance(item, dict) else item
                            if not track_data or not isinstance(track_data, dict):
                                continue

                            song_name = track_data.get('name', 'Unknown Track')

                            artists_data = track_data.get('artists', [])
                            if artists_data and isinstance(artists_data, list) and len(artists_data) > 0:
                                artist_name = artists_data[0].get('name', 'Unknown Artist') if isinstance(artists_data[0], dict) else str(artists_data[0])
                            else:
                                artist_name = 'Unknown Artist'

                            file_name = f"{song_name} - {artist_name}"
                            file_name = sanitize_filename(file_name)
                            if not file_name:
                                file_name = "Unknown_Song - Unknown_Artist"

                            expected_path = os.path.join(playlist_folder, f"{file_name}.mp3")

                            if os.path.exists(expected_path):
                                skipped_count += 1
                                continue

                            meta = {
                                'name': song_name,
                                'artist': artist_name,
                                'duration_ms': track_data.get('duration_ms'),
                                'album': track_data.get('album', {}).get('name', ''),
                                'output_dir': playlist_folder,
                                'playlist_name': playlist_name
                            }
                            metadata_list.append(meta)

                        if skipped_count > 0 and log_callback:
                            log_callback(f"Skipped {skipped_count} existing tracks.")

                        if not metadata_list and skipped_count == len(tracks) and log_callback:
                            log_callback("All tracks already downloaded!")

                    elif "track" in url:
                        try:
                            client = SpotifyClient()
                            track_info = client.get_track_info(url)

                            if track_info:
                                song_name = track_info.get('name', 'Unknown Track')

                                artists_data = track_info.get('artists', [])
                                if artists_data and isinstance(artists_data, list) and len(artists_data) > 0:
                                    artist_name = artists_data[0].get('name', 'Unknown Artist') if isinstance(artists_data[0], dict) else str(artists_data[0])
                                else:
                                    artist_name = 'Unknown Artist'

                                meta = {
                                    'name': song_name,
                                    'artist': artist_name,
                                    'duration_ms': track_info.get('duration_ms'),
                                    'album': track_info.get('album', {}).get('name', ''),
                                }
                                metadata_list.append(meta)
                                if log_callback:
                                    log_callback(f"Fetched track info: {song_name} - {artist_name}")
                            else:
                                raise ProcessingError("Failed to fetch track info - no data returned")

                        except Exception as e:
                            handle_download_error(e, log_callback, "Fetching track from Spotify")
                            raise ProcessingError(f"Track fetch failed: {e}")

                    elif "album" in url:
                        try:
                            client = SpotifyClient()
                            album_info = client.get_album_info(url)

                            if album_info:
                                album_name = album_info.get('name', 'Unknown Album')
                                tracks_data = album_info.get('tracks', album_info.get('items', []))

                                safe_album_name = sanitize_filename(album_name)
                                if not safe_album_name:
                                    safe_album_name = "Unknown_Album"

                                album_folder = os.path.join(self.download_path, safe_album_name)
                                if not os.path.exists(album_folder):
                                    os.makedirs(album_folder)

                                if log_callback:
                                    log_callback(f"Fetched album info: {album_name} with {len(tracks_data)} tracks")

                                for track_item in tracks_data:
                                    track_data = track_item.get('track', track_item) if isinstance(track_item, dict) else track_item
                                    if not track_data or not isinstance(track_data, dict):
                                        continue

                                    song_name = track_data.get('name', 'Unknown Track')

                                    artists_data = track_data.get('artists', [])
                                    if artists_data and isinstance(artists_data, list) and len(artists_data) > 0:
                                        artist_name = artists_data[0].get('name', 'Unknown Artist') if isinstance(artists_data[0], dict) else str(artists_data[0])
                                    else:
                                        artist_name = album_info.get('artists', [{}])[0].get('name', 'Unknown Artist') if album_info.get('artists', []) else 'Unknown Artist'

                                    file_name = f"{song_name} - {artist_name}"
                                    file_name = sanitize_filename(file_name)
                                    if not file_name:
                                        file_name = "Unknown_Song - Unknown_Artist"

                                    expected_path = os.path.join(album_folder, f"{file_name}.mp3")

                                    if os.path.exists(expected_path):
                                        continue

                                    meta = {
                                        'name': song_name,
                                        'artist': artist_name,
                                        'duration_ms': track_data.get('duration_ms'),
                                        'album': album_name,
                                        'output_dir': album_folder
                                    }
                                    metadata_list.append(meta)
                            else:
                                raise ProcessingError("Album info not available")

                        except Exception as e:
                            handle_download_error(e, log_callback, "Fetching album from Spotify")
                            raise ProcessingError(f"Album fetch failed: {e}")
                    else:
                        metadata_list.append({'name': url, 'artist': 'Unknown Artist'})
                else:
                    if log_callback:
                        log_callback(f"Treating as direct search: {url}")
                    metadata_list.append({'name': url, 'artist': ''})

                if len(metadata_list) > 1:
                    if log_callback:
                        log_callback(f"Starting concurrent download of {len(metadata_list)} tracks...")
                    with concurrent.futures.ThreadPoolExecutor(max_workers=app_config.max_concurrent_downloads) as executor:
                        future_to_meta = {
                            executor.submit(self._download_track, meta, engine, progress_callback, log_callback, tracker): meta
                            for meta in metadata_list
                        }

                        for future in concurrent.futures.as_completed(future_to_meta):
                            meta = future_to_meta[future]
                            try:
                                future.result()
                            except Exception as exc:
                                handle_download_error(exc, log_callback, f"Processing {meta.get('name', 'Unknown Track')}")
                    if log_callback:
                        log_callback("All downloads finished!")
                else:
                    for meta in metadata_list:
                        self._download_track(meta, engine, progress_callback, log_callback, tracker)

            except Exception as e:
                handle_download_error(e, log_callback, "Main download process")
            finally:
                if cache_file_path and os.path.exists(cache_file_path):
                    all_successfully_downloaded = False
                    try:
                        with open(cache_file_path, "r", encoding="utf-8") as f:
                            playlist_data = json.load(f)

                        completed_downloads = [d for d in tracker.get_all_downloads() if d.status == DownloadStatus.COMPLETED]
                        completed_titles = {
                            f"{d.title.lower().strip()} - {d.artist.lower().strip()}"
                            for d in completed_downloads
                        }

                        tracks_container = playlist_data.get('tracks', playlist_data.get('items', []))
                        tracks = tracks_container.get('items', tracks_container) if isinstance(tracks_container, dict) else tracks_container

                        missing_tracks = []
                        for item in tracks:
                            track_data = item.get('track', item)
                            if not track_data:
                                continue

                            song_name = track_data.get('name')
                            artist_name = track_data.get('artists', [{}])[0].get('name')
                            album_name = track_data.get('album', {}).get('name')

                            if song_name and artist_name:
                                full_title = f"{song_name.lower().strip()} - {artist_name.lower().strip()}"
                                if full_title not in completed_titles:
                                    missing_tracks.append({
                                        'name': song_name,
                                        'artist': artist_name,
                                        'album': album_name,
                                        'output_dir': os.path.dirname(cache_file_path),
                                        'playlist_name': playlist_data.get('name', 'Unknown Playlist')
                                    })

                        if missing_tracks:
                            if log_callback:
                                log_callback(f"Found {len(missing_tracks)} missing tracks. Retrying downloads...")

                            for meta in missing_tracks:
                                for i in range(3):
                                    if log_callback:
                                        log_callback(f"Retrying download for '{meta['name']}' (attempt {i+1}/3)...")

                                    explicit_meta = meta.copy()
                                    explicit_meta['query'] = f"{meta['name']} {meta['artist']} {meta['album']}"

                                    self._download_track(explicit_meta, engine, progress_callback, log_callback, tracker)

                                    file_name = sanitize_filename(f"{meta['name']} - {meta['artist']}")
                                    expected_path = os.path.join(meta['output_dir'], f"{file_name}.mp3")
                                    if os.path.exists(expected_path):
                                        if log_callback:
                                            log_callback(f"Successfully downloaded missing track: '{meta['name']}'")
                                        break
                                    else:
                                        if log_callback:
                                            log_callback(f"Failed to download missing track: '{meta['name']}' on attempt {i+1}")

                            completed_downloads = [d for d in tracker.get_all_downloads() if d.status == DownloadStatus.COMPLETED]
                            completed_titles = {
                                f"{d.title.lower().strip()} - {d.artist.lower().strip()}"
                                for d in completed_downloads
                            }

                            final_missing_tracks = []
                            for item in tracks:
                                track_data = item.get('track', item)
                                if not track_data:
                                    continue

                                song_name = track_data.get('name')
                                artist_name = track_data.get('artists', [{}])[0].get('name')

                                if song_name and artist_name:
                                    full_title = f"{song_name.lower().strip()} - {artist_name.lower().strip()}"
                                    if full_title not in completed_titles:
                                        final_missing_tracks.append(full_title)

                            if not final_missing_tracks:
                                all_successfully_downloaded = True

                        else:
                            if log_callback:
                                log_callback("All tracks downloaded successfully. No missing tracks found.")
                            all_successfully_downloaded = True

                        if all_successfully_downloaded:
                            os.remove(cache_file_path)
                            if log_callback:
                                log_callback("Cleaned up playlist cache.")
                        else:
                            if log_callback:
                                log_callback("Some tracks failed to download after retries. Cache file will not be deleted.")

                    except Exception as e:
                        if log_callback:
                            log_callback(f"Error during verification and cleanup: {e}")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

import os
import threading
import subprocess
import concurrent.futures
import json # Import json for handling fake data

class SpotDownloader:
    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        self.client_id = None
        self.client_secret = None
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def set_download_path(self, new_path):
        self.download_path = new_path
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _download_track(self, meta, engine, progress_callback=None, log_callback=None):
        """Helper function to download a single track, suitable for ThreadPoolExecutor."""
        try:
            print(f"DEBUG: Processing track: {meta.get('name')} in {meta.get('output_dir', 'default')}")
            success = engine.download_and_tag(meta, progress_callback, log_callback)
            if success:
                if log_callback:
                    log_callback(f"Download of '{meta.get('name')}' completed successfully!")
            else:
                if log_callback:
                    log_callback(f"Failed to download: {meta.get('name')}")
            return success
        except Exception as e:
            if log_callback:
                log_callback(f"An error occurred while downloading {meta.get('name')}: {e}")
            return False

    def download(self, url, progress_callback=None, log_callback=None):
        """
        Downloads a song or playlist concurrently using the Custom Engine.
        Spotify metadata fetching is replaced with hardcoded fake data for testing.
        """
        from .custom_engine import CustomDownloadEngine
        # Removed: from spotify_scraper import SpotifyClient

        # Mock playlist data (used when Spotify URL is detected)
        FAKE_PLAYLIST_DATA = {
            'name': 'My Mock Playlist',
            'tracks': {
                'items': [
                    {'track': {'name': 'Mock Song 1', 'artists': [{'name': 'Mock Artist A'}], 'duration_ms': 180000, 'album': {'name': 'Mock Album X'}}},
                    {'track': {'name': 'Mock Song 2', 'artists': [{'name': 'Mock Artist B'}], 'duration_ms': 200000, 'album': {'name': 'Mock Album Y'}}},
                    {'track': {'name': 'Mock Song 3', 'artists': [{'name': 'Mock Artist C'}], 'duration_ms': 220000, 'album': {'name': 'Mock Album Z'}}},
                ]
            }
        }
        FAKE_TRACK_INFO = {'name': 'Mock Single Song', 'artist': 'Mock Artist D', 'album': 'Mock Album W'}


        def run():
            cache_file_path = None
            if log_callback:
                log_callback(f"Initiating download for: {url}")

            if log_callback:
                log_callback("Running Custom Download Engine...")
            
            engine = CustomDownloadEngine(self.download_path)
            
            metadata_list = []
            if "spotify.com" in url:
                print(f"DEBUG: Identified as Spotify URL: {url}")
                # Replaced SpotifyClient logic with hardcoded fake data
                if "playlist" in url:
                    print("DEBUG: Identified as PLAYLIST (using mock data)")
                    if log_callback:
                        log_callback("Fetching playlist details (using mock data)...")
                    
                    playlist_data = FAKE_PLAYLIST_DATA
                    playlist_name = playlist_data.get('name', 'Unknown Playlist')
                    safe_playlist_name = "".join([c for c in playlist_name if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
                    playlist_folder = os.path.join(self.download_path, safe_playlist_name)
                    
                    if not os.path.exists(playlist_folder):
                        os.makedirs(playlist_folder)

                    # Save mock playlist metadata to cache file
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
                        print(f"DEBUG: Failed to save mock playlist cache: {e}")

                    tracks_container = playlist_data['tracks']
                    tracks = tracks_container.get('items', []) if isinstance(tracks_container, dict) else tracks_container
                    
                    if log_callback:
                        log_callback(f"Found {len(tracks)} tracks in '{playlist_name}' (mock data). Processing list...")

                    skipped_count = 0
                    for item in tracks:
                        track_data = item.get('track', item)
                        if not track_data or not isinstance(track_data, dict):
                            continue
                            
                        song_name = track_data.get('name', 'Unknown Track')
                        artist_name = track_data['artists'][0]['name'] if track_data.get('artists') else 'Unknown Artist'
                        
                        file_name = f"{artist_name} - {song_name}"
                        file_name = "".join([c for c in file_name if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
                        expected_path = os.path.join(playlist_folder, f"{file_name}.mp3")
                        
                        if os.path.exists(expected_path):
                            skipped_count += 1
                            continue

                        meta = {
                            'name': song_name,
                            'artist': artist_name,
                            'duration_ms': track_data.get('duration_ms'),
                            'album': track_data['album']['name'] if track_data.get('album') else '',
                            'output_dir': playlist_folder
                        }
                        metadata_list.append(meta)
                    
                    if skipped_count > 0 and log_callback:
                        log_callback(f"Skipped {skipped_count} existing tracks.")
                        
                    if not metadata_list and skipped_count == len(tracks) and log_callback:
                        log_callback("All tracks already downloaded!")

                elif "track" in url:
                    print("DEBUG: Identified as TRACK (using mock data)")
                    # Use mock track info for single track URLs
                    metadata_list.append(FAKE_TRACK_INFO)
                
                elif "album" in url:
                    # For album URLs, use mock single track info as a fallback
                    if log_callback:
                        log_callback("Album scraping is currently not supported in this mode. Using mock track data as fallback.")
                    metadata_list.append(FAKE_TRACK_INFO)
                else:
                    print(f"DEBUG: Could not identify Spotify entity type for {url} - using generic URL as name.")
                    # Fallback for unrecognized Spotify URLs
                    metadata_list.append({'name': url, 'artist': 'Unknown Artist'})
            
            if not metadata_list:
                # Fallback to direct search if no metadata found (and not a spotify URL)
                metadata_list.append({'name': url, 'artist': ''})

            # Use ThreadPoolExecutor for concurrent downloads
            if len(metadata_list) > 1:
                log_callback(f"Starting concurrent download of {len(metadata_list)} tracks...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    # Submit all download tasks
                    future_to_meta = {executor.submit(self._download_track, meta, engine, progress_callback, log_callback): meta for meta in metadata_list}
                    
                    for future in concurrent.futures.as_completed(future_to_meta):
                        meta = future_to_meta[future]
                        try:
                            future.result()  # We can check for exceptions here if needed
                        except Exception as exc:
                            if log_callback:
                                log_callback(f"{meta.get('name', 'Unknown Track')} generated an exception: {exc}")
                if log_callback:
                    log_callback("All downloads finished!")
            else:
                # Fallback to single download for single tracks or errors
                for meta in metadata_list:
                    self._download_track(meta, engine, progress_callback, log_callback)

            if cache_file_path and os.path.exists(cache_file_path):
                try:
                    os.remove(cache_file_path)
                    if log_callback:
                        log_callback("Cleaned up playlist cache.")
                except Exception as e:
                    print(f"DEBUG: Error deleting cache: {e}")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

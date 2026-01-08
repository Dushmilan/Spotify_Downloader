import os
import threading
import subprocess

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

    def download(self, url, progress_callback=None, log_callback=None):
        """
        Downloads a song or playlist using either spotdl or the Custom Engine.
        """
        from .custom_engine import CustomDownloadEngine
        from spotify_scraper import SpotifyClient

        def run():
            cache_file_path = None
            if log_callback:
                log_callback(f"Initiating download for: {url}")

            # Always use the Custom Engine (yt-dlp + mutagen)
            if log_callback:
                log_callback("Running Custom Download Engine...")
            
            engine = CustomDownloadEngine(self.download_path)
            
            # Identify tracks
            metadata_list = []
            if "spotify.com" in url:
                print(f"DEBUG: Identified as Spotify URL: {url}")
                try:
                    client = SpotifyClient()
                    # Check for playlist first as it's more complex
                    if "playlist" in url:
                        print("DEBUG: Identified as PLAYLIST")
                        if log_callback:
                            log_callback("Fetching playlist details...")
                        try:
                            playlist_data = client.get_playlist_info(url)
                            if playlist_data and 'tracks' in playlist_data:
                                playlist_name = playlist_data.get('name', 'Unknown Playlist')
                                safe_playlist_name = "".join([c for c in playlist_name if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
                                playlist_folder = os.path.join(self.download_path, safe_playlist_name)
                                
                                if not os.path.exists(playlist_folder):
                                    os.makedirs(playlist_folder)

                                # 2. Save/Cache Playlist Metadata
                                import json
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
                                    print(f"DEBUG: Failed to save playlist cache: {e}")

                                tracks_container = playlist_data['tracks']
                                tracks = tracks_container.get('items', []) if isinstance(tracks_container, dict) else tracks_container
                                
                                if log_callback:
                                    log_callback(f"Found {len(tracks)} tracks in '{playlist_name}'. Processing list...")

                                skipped_count = 0
                                for item in tracks:
                                    track_data = item.get('track', item)
                                    if not track_data or not isinstance(track_data, dict):
                                        continue
                                        
                                    song_name = track_data.get('name', 'Unknown Track')
                                    artist_name = track_data['artists'][0]['name'] if track_data.get('artists') else 'Unknown Artist'
                                    
                                    # Pre-check existence to skip queueing
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
                                
                                if skipped_count > 0:
                                    if log_callback:
                                        log_callback(f"Skipped {skipped_count} existing tracks.")
                                    print(f"DEBUG: Skipped {skipped_count} files that already exist.")
                                    
                                if not metadata_list and skipped_count == len(tracks):
                                    if log_callback:
                                        log_callback("All tracks already downloaded!")

                        except Exception as p_err:
                             if log_callback:
                                log_callback(f"Playlist extraction failed: {p_err}")

                    elif "track" in url:
                        print("DEBUG: Identified as TRACK")
                        info = client.get_track_info(url)
                        if info:
                            metadata_list.append(info)
                    
                    elif "album" in url:
                        print("DEBUG: Identified as ALBUM")
                        # For now, custom engine handles single tracks best. 
                        # We can expand playlist scraping later if needed.
                        if log_callback:
                            log_callback("Album scraping is currently limited in bypass mode.")
                        metadata_list.append({'url': url, 'name': url}) # Fallback
                    else:
                        print(f"DEBUG: Could not identify Spotify entity type for {url}")
                except Exception as e:
                    if log_callback:
                        log_callback(f"Metadata scraping error: {e}")
            
            if not metadata_list:
                # Fallback to direct search if no metadata found
                metadata_list.append({'name': url, 'artist': ''})

            total_items = len(metadata_list)
            
            for i, meta in enumerate(metadata_list):
                print(f"DEBUG: Processing track: {meta.get('name')} in {meta.get('output_dir', 'default')}")
                
                # Create a wrapper for progress to show overall playlist progress
                def track_progress_callback(val):
                    if progress_callback:
                        # (completed_items + current_item_progress) / total
                        overall = (i + val) / total_items
                        progress_callback(overall)

                success = engine.download_and_tag(meta, track_progress_callback, log_callback)
                if success:
                    if log_callback:
                        log_callback(f"Download of '{meta.get('name')}' completed successfully!")
                else:
                    if log_callback:
                        log_callback(f"Failed to download: {meta.get('name')}")
            
            if progress_callback:
                progress_callback(1.0)
            
            # Cleanup cache
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

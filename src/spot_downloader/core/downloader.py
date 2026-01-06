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

    def set_credentials(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def resolve_youtube_url(self, query):
        """
        Searches YouTube for a query and returns the first video URL.
        Bypasses any need for the Spotify API.
        """
        import requests
        import re
        import urllib.parse
        
        try:
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            response = requests.get(search_url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            if response.status_code == 200:
                # Look for the first watch URL in the results
                video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", response.text)
                if video_ids:
                    return f"https://www.youtube.com/watch?v={video_ids[0]}"
        except Exception:
            pass
        return None

    def login(self, log_callback=None):
        """
        Triggers the spotdl browser-based login using a dummy URL.
        """
        def run():
            if log_callback:
                log_callback("Opening browser for Spotify Login... Please log in and then return here.")
            
            # spotdl requires a query even for --user-auth
            # We use a valid dummy track for this purpose
            command = ["spotdl", "download", "https://open.spotify.com/track/4uLU618mHMAePzd2vKRpZp", "--user-auth", "--log-level", "DEBUG"]
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # We only need it to trigger the browser, we can stop once it starts logging
                for line in process.stdout:
                    if log_callback:
                        log_callback(line.strip())
                    if "Login session saved" in line:
                        break
                
                # Note: We don't necessarily want to wait for the whole 'download' to finish 
                # if it's just a dummy, but spotdl needs to finish the auth step.
                process.wait()
                if log_callback:
                    log_callback("Login process finished.")
            except Exception as e:
                if log_callback:
                    log_callback(f"Login error: {str(e)}")

        threading.Thread(target=run, daemon=True).start()

    def download(self, url, progress_callback=None, log_callback=None):
        """
        Downloads a song or playlist using either spotdl or the Custom Engine.
        """
        from .custom_engine import CustomDownloadEngine
        from spotify_scraper import SpotifyClient

        def run():
            if log_callback:
                log_callback(f"Initiating download for: {url}")

            # 1. If we HAVE official keys, use the standard spotdl CLI
            if self.client_id and self.client_secret:
                if log_callback:
                    log_callback("Using official Spotify API keys...")
                self._download_via_spotdl(url, progress_callback, log_callback)
                return

            # 2. If Anonymous, use the Custom Engine (yt-dlp + mutagen)
            if log_callback:
                log_callback("Running in Anonymous Mode (API Bypass)...")
            
            engine = CustomDownloadEngine(self.download_path)
            
            # Identify tracks
            # Identify tracks
            metadata_list = []
            
            # Identify type of URL
            if "spotify.com" in url:
                try:
                    client = SpotifyClient()
                    
                    if "playlist" in url or "album" in url:
                        # Playlist/Album Logic
                        if "playlist" in url:
                            info = client.get_playlist_info(url)
                            folder_name = info.get('name', 'Playlist')
                        else:
                            info = client.get_album_info(url)
                            folder_name = info.get('name', 'Album')

                        if info:
                            # Sanitize folder name
                            folder_name = "".join([c for c in folder_name if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
                            playlist_path = os.path.join(self.download_path, folder_name)
                            
                            # Create engine for this playlist
                            playlist_engine = CustomDownloadEngine(playlist_path)
                            
                            tracks = info.get('tracks', [])
                            if log_callback:
                                log_callback(f"Found '{folder_name}' with {len(tracks)} tracks. Downloading to: {playlist_path}")
                            
                            for i, track in enumerate(tracks):
                                if log_callback:
                                    log_callback(f"[{i+1}/{len(tracks)}] Processing: {track.get('name')}")
                                
                                success = playlist_engine.download_and_tag(track, progress_callback, log_callback)
                                if not success and log_callback:
                                    log_callback(f"Failed: {track.get('name')}")
                            
                            if log_callback:
                                log_callback(f"Playlist '{folder_name}' download complete!")
                            return

                    # Single Track Logic
                    elif "track" in url:
                        info = client.get_track_info(url)
                        if info:
                            metadata_list.append(info)

                except Exception as e:
                    if log_callback:
                        log_callback(f"Metadata scraping error: {e}")
            
            if not metadata_list:
                # Fallback to direct search if no metadata found (or non-Spotify URL)
                metadata_list.append({'name': url, 'artist': ''})

            # Process single tracks
            for meta in metadata_list:
                success = engine.download_and_tag(meta, progress_callback, log_callback)
                if success:
                    if log_callback:
                        log_callback(f"Download of '{meta.get('name')}' completed successfully!")
                else:
                    if log_callback:
                        log_callback(f"Failed to download: {meta.get('name')}")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

    def _download_via_spotdl(self, url, progress_callback=None, log_callback=None):
        """
        Internal method to handle the original spotdl CLI logic.
        """
        output_template = os.path.join(self.download_path, "{artist} - {title}.{output-ext}")
        command = ["spotdl", "download", url, "--output", output_template, "--simple-tui"]
        command.extend(["--client-id", self.client_id, "--client-secret", self.client_secret])

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if process.stdout:
                for line in process.stdout:
                    if log_callback:
                        log_callback(line.strip())
            process.wait()
        except Exception as e:
            if log_callback:
                log_callback(f"SpotDL error: {e}")

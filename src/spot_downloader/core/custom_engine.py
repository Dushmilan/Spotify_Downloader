import os
import yt_dlp
from .searcher import YouTubeSearcher
from ..utils.tagger import tag_mp3, tag_m4a

class CustomDownloadEngine:
    def __init__(self, download_path="downloads"):
        self.default_path = download_path
        if not os.path.exists(self.default_path):
            os.makedirs(self.default_path)

    def download_and_tag(self, metadata, progress_callback=None, log_callback=None, cancel_event=None):
        """
        Full pipeline: Search -> Download -> Tag
        """
        # Determine actual download location (playlist subfolder or default)
        target_path = metadata.get('output_dir', self.default_path)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
            
        song_name = metadata.get('name')
        artist_name = metadata.get('artist', '')
        
        # 1. Check if file already exists
        file_name = f"{artist_name} - {song_name}"
        # Sanitize filename
        file_name = "".join([c for c in file_name if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
        final_file_path = os.path.join(target_path, f"{file_name}.mp3")
        
        print(f"DEBUG: Checking existence for: {final_file_path}")

        if os.path.exists(final_file_path):
            if log_callback:
                log_callback(f"Skipping: '{file_name}' already exists in {os.path.basename(target_path)}/")
            print(f"DEBUG: File exists! Skipping.")
            if progress_callback:
                progress_callback(1.0)
            return True

        if cancel_event and cancel_event.is_set():
            if log_callback:
                log_callback("Download cancelled.")
            return False

        query = f"{song_name} {artist_name}".strip()
        
        if log_callback:
            log_callback(f"Searching for better match: {query}...")
            
        # 1. Search for best match
        video_url = YouTubeSearcher.search_ytm(query, duration_ms=metadata.get('duration_ms'))
        if not video_url:
            if log_callback:
                log_callback("Error: No match found on YouTube Music.")
            return False
            
        if log_callback:
            log_callback(f"Downloading from: {video_url}")

        # 2. Download using yt-dlp
        # file_name is already defined and sanitized above
        output_path = os.path.join(target_path, f"{file_name}.%(ext)s")

        def ydl_progress_hook(d):
            if cancel_event and cancel_event.is_set():
                raise Exception("Download cancelled by user")

            if d['status'] == 'downloading':
                # Calculate progress
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                
                progress_val = 0.0
                if total > 0:
                    progress_val = downloaded / total

                # Log size in MB (Throttle logs)
                if total > 0:
                    mb_total = total / (1024 * 1024)
                    mb_downloaded = downloaded / (1024 * 1024)
                    if log_callback and downloaded % (1024 * 1024) < 100000: # Throttle logs
                         pass # Reducing log spam for GUI

                if progress_callback:
                    try:
                        progress_callback(progress_val)
                    except:
                        pass
            elif d['status'] == 'finished':
                if log_callback:
                    log_callback("Download complete, converting...")
                if progress_callback:
                    progress_callback(1.0)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320', # Replicating spotdl's 320kbps upscaling
            }],
            # Using '0' for audio-quality ensures the best VBR/CBR encoding
            'audio_quality': 0, 
            'progress_hooks': [ydl_progress_hook],
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            final_file = os.path.join(target_path, f"{file_name}.mp3")
            
            # 3. Tag the file
            if os.path.exists(final_file):
                if log_callback:
                    log_callback(f"Embedding metadata for: {file_name}")
                tag_mp3(final_file, metadata)
                if log_callback:
                    log_callback(f"Successfully downloaded and tagged: {file_name}")
                return True
            else:
                if log_callback:
                    log_callback("Error: Downloaded file not found after conversion.")
                return False

        except Exception as e:
            if "cancelled by user" in str(e).lower():
                if log_callback:
                    log_callback("Download cancelled.")
                return False
            if log_callback:
                log_callback(f"Download error: {str(e)}")
            return False

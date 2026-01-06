import os
import yt_dlp
from .searcher import YouTubeSearcher
from ..utils.tagger import tag_mp3, tag_m4a

class CustomDownloadEngine:
    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def download_and_tag(self, metadata, progress_callback=None, log_callback=None):
        """
        Full pipeline: Search -> Download -> Tag
        """
        song_name = metadata.get('name')
        artist_name = metadata.get('artist', '')
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
        file_name = f"{artist_name} - {song_name}"
        # Sanitize filename
        file_name = "".join([c for c in file_name if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
        output_path = os.path.join(self.download_path, f"{file_name}.%(ext)s")

        def ydl_progress_hook(d):
            if d['status'] == 'downloading':
                # Log size in MB
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded_bytes = d.get('downloaded_bytes', 0)
                
                if total_bytes > 0:
                    mb_total = total_bytes / (1024 * 1024)
                    mb_downloaded = downloaded_bytes / (1024 * 1024)
                    if log_callback and downloaded_bytes % (1024 * 1024) < 100000: # Throttle logs to roughly every 1MB
                        log_callback(f"Download Progress: {mb_downloaded:.2f}MB / {mb_total:.2f}MB")

                if progress_callback:
                    p = d.get('_percent_str', '0%').replace('%','').strip()
                    try:
                        progress_callback(float(p) / 100)
                    except:
                        pass
            elif d['status'] == 'finished':
                if log_callback:
                    # Final size log
                    final_bytes = d.get('total_bytes') or d.get('downloaded_bytes', 0)
                    mb_final = final_bytes / (1024 * 1024)
                    log_callback(f"Download complete ({mb_final:.2f}MB), post-processing...")

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
            
            final_file = os.path.join(self.download_path, f"{file_name}.mp3")
            
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
            if log_callback:
                log_callback(f"Download error: {str(e)}")
            return False

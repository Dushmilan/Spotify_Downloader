import os
import yt_dlp
from .searcher import YouTubeSearcher
from ..utils.tagger import tag_mp3, tag_m4a
from ..utils.validation import sanitize_filename
from ..utils.logger import get_logger

logger = get_logger(__name__)
from ..config import app_config
from ..utils.throttle import Throttler
from ..utils.helpers import get_ffmpeg_path

class CustomDownloadEngine:
    def __init__(self, download_path="downloads"):
        self.default_path = download_path
        if not os.path.exists(self.default_path):
            os.makedirs(self.default_path)

    def download_and_tag(self, metadata, progress_callback=None, log_callback=None):
        """
        Full pipeline: Search -> Download -> Tag
        """
        # Determine actual download location (playlist subfolder or default)
        target_path = metadata.get('output_dir', self.default_path)
        if not os.path.exists(target_path):
            os.makedirs(target_path)

        song_name = metadata.get('name', 'Unknown Song')
        artist_name = metadata.get('artist', 'Unknown Artist')

        # 1. Check if file already exists
        file_name = f"{song_name} - {artist_name}"
        # Sanitize filename to prevent directory traversal and invalid characters
        file_name = sanitize_filename(file_name)
        if not file_name or file_name.isspace():
            file_name = "Unknown_Song - Unknown_Artist"

        final_file_path = os.path.join(target_path, f"{file_name}.mp3")

        if log_callback:
            log_callback(f"Checking existence for: {file_name}")

        if os.path.exists(final_file_path):
            if log_callback:
                log_callback(f"Skipping: '{file_name}' already exists in {os.path.basename(target_path)}/")
            if progress_callback:
                progress_callback(1.0)
            return True

        query = metadata.get('query')
        if not query:
            query = f"{song_name} {artist_name}".strip()

        if log_callback:
            log_callback(f"Searching for better match: {query}...")

        # 1. Search for best match
        try:
            video_url = YouTubeSearcher.search_ytm(query, duration_ms=metadata.get('duration_ms'))
            if not video_url:
                if log_callback:
                    log_callback("Error: No match found on YouTube Music.")
                return False
        except Exception as e:
            if log_callback:
                log_callback(f"Search error: {str(e)}")
            return False

        if log_callback:
            log_callback(f"Downloading from: {video_url}")

        # 2. Download using yt-dlp
        # file_name is already defined and sanitized above
        output_path = os.path.join(target_path, f"{file_name}.%(ext)s")

        progress_throttler = Throttler(0.1)  # Throttle progress updates to every 100ms

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
                        progress_val = float(p) / 100
                        progress_throttler(progress_callback, progress_val)
                    except (ValueError, TypeError):
                        pass
            elif d['status'] == 'finished':
                if log_callback:
                    # Final size log
                    final_bytes = d.get('total_bytes') or d.get('downloaded_bytes', 0)
                    mb_final = final_bytes / (1024 * 1024)
                    log_callback(f"Download complete ({mb_final:.2f}MB), post-processing...")

        # Map quality setting to yt-dlp format
        quality_map = {
            '128kbps': '128',
            '256kbps': '256',
            '320kbps': '320'
        }
        preferred_quality = quality_map.get(app_config.download_quality, '320')

        # Get FFmpeg location (system or bundled via imageio-ffmpeg)
        ffmpeg_exe = get_ffmpeg_path()

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': app_config.file_format, # Corrected attribute access
                'preferredquality': preferred_quality,
            }],
            # Using '0' for audio-quality ensures the best VBR/CBR encoding
            'audio_quality': 0,
            'progress_hooks': [ydl_progress_hook],
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': app_config.timeout_seconds,  # Timeout for network operations from config
            'connect_timeout': app_config.timeout_seconds,  # Connection timeout from config
            'retries': app_config.retry_attempts,  # Number of retries for failed downloads from config
        }

        # Set FFmpeg location if using bundled version
        if ffmpeg_exe:
            ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_exe)

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
                logger.error("Downloaded file not found after conversion.")
            if log_callback:
                log_callback("Error: Downloaded file not found after conversion.")
                return False

        except yt_dlp.DownloadError as e:
            logger.error(f"Download error (yt-dlp): {str(e)}")
            if log_callback:
                log_callback(f"Download error (yt-dlp): {str(e)}"),
            return False
        except Exception as e:
            if log_callback:
                log_callback(f"Unexpected download error: {str(e)}")
            return False

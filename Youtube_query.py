import yt_dlp
import os
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

def create_query(track_name, artist_name):
    """Create a YouTube search query from track name and artist name."""
    try:
        if not track_name or not artist_name:
            logger.warning(f"Missing track name or artist name: track_name='{track_name}', artist_name='{artist_name}'")
            return ""

        query = f"{track_name} {artist_name}"
        # Sanitize query to remove any problematic characters if needed
        return query.strip()
    except Exception as e:
        logger.error(f"Error creating query for track '{track_name}' by '{artist_name}': {str(e)}", exc_info=True)
        return ""

def search_youtube_for_video(query):
    """Search and download audio from YouTube with error handling."""
    try:
        if not query:
            logger.error("Empty query provided to search_youtube_for_video")
            return -1

        # Create download directory if it doesn't exist (Steps 8 & 9: Convert & Save)
        download_dir = os.path.join(os.getcwd(), "downloads")

        # Check if we have write permissions
        try:
            os.makedirs(download_dir, exist_ok=True)
            # Check if directory is writable by creating a temporary file
            test_file = os.path.join(download_dir, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except (PermissionError, OSError) as e:
            logger.error(f"Cannot write to downloads directory {download_dir}: {str(e)}")
            return -1

        # Create a YouTube search URL from the query
        search_url = f"ytsearch1:{query}"

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'postprocessor_args': [
                '-ar', '44100'  # Set audio rate
            ],
            'prefer_ffmpeg': True,
            'audioquality': '0',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),  # Save to downloads folder
            'noplaylist': True,
            'ignoreerrors': True,  # Continue with other items if one fails
            'no_warnings': False,
            'quiet': False,
        }

        logger.info(f"Searching YouTube for: {query}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_url])

        logger.info(f"Successfully downloaded audio for query: {query}")
        return 0
    except yt_dlp.DownloadError as e:
        logger.error(f"YouTube download error for query '{query}': {str(e)}")
        return -1
    except Exception as e:
        logger.error(f"Unexpected error downloading from YouTube for query '{query}': {str(e)}", exc_info=True)
        return -1
    

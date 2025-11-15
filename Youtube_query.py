import yt_dlp
import os
import time
import logging
from urllib.parse import quote
try:
    from mutagen import File
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TCON
    from mutagen.mp3 import MP3
    METADATA_AVAILABLE = True
except ImportError:
    METADATA_AVAILABLE = False
    print("Warning: mutagen library not found. Install with 'pip install mutagen' for metadata support.")

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

def search_youtube_for_video(query, playlist_or_album_name=None, track_number=None, quality='192', format='mp3', track_info=None):
    """Search and download audio from YouTube with error handling and retry mechanism."""
    try:
        if not query:
            logger.error("Empty query provided to search_youtube_for_video")
            return -1

        # Create download directory if it doesn't exist (Steps 8 & 9: Convert & Save)
        if playlist_or_album_name:
            # Create organized folder structure for playlist/album
            download_dir = os.path.join(os.getcwd(), "downloads", playlist_or_album_name)
        else:
            # For individual tracks, use the default downloads folder
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

        # Create filename template with track number if available
        if track_number is not None:
            outtmpl = os.path.join(download_dir, f'{track_number:02d} - %(title)s.%(ext)s')
        else:
            outtmpl = os.path.join(download_dir, '%(title)s.%(ext)s')

        # Check if the file already exists to avoid duplicate downloads
        import re
        # Create a simplified version of the expected filename to check for partial matches
        expected_title = query  # This is a simple approach; could be more sophisticated
        existing_files = os.listdir(download_dir)

        # Look for files that might match this query already
        for file in existing_files:
            if file.lower().endswith('.mp3') and query.lower() in file.lower():
                logger.info(f"Track already exists: {file}, skipping download for query: {query}")
                return 0  # Indicate success since file already exists

        # Define retry mechanism
        max_retries = 3
        retry_count = 0

        # Map quality setting to appropriate format with proper FFmpeg parameters
        quality_settings = {
            '128': {'abr': 128, 'vbr': 128},
            '192': {'abr': 192, 'vbr': 192},
            '256': {'abr': 256, 'vbr': 256},
            '320': {'abr': 320, 'vbr': 320}
        }
        selected_quality = quality_settings.get(quality, {'abr': 192, 'vbr': 192})  # Default to 192 if invalid quality specified

        # According to yt-dlp documentation: Use format selection to get closest to target bitrate
        # Higher bitrates: try to get high quality sources; lower bitrates: allow lower quality
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': 0,  # Use highest quality for extraction
            }],
            'postprocessor_args': [
                '-b:a', f"{selected_quality['abr']}k",  # Set target audio bitrate
                '-ar', '44100',  # Set audio sample rate
                '-ac', '2',      # Set to stereo
                '-y',            # Overwrite output file
                '-write_id3v2', '1',  # Ensure ID3 tags are written
                '-id3v2_version', '3'  # Use ID3v2.3 tags
            ],
            'prefer_ffmpeg': True,
            'audioquality': selected_quality['abr'],
            'extractaudio': True,
            'audioformat': format,
            'outtmpl': outtmpl,  # Save to organized folder structure
            'noplaylist': True,
            'ignoreerrors': True,  # Continue with other items if one fails
            'no_warnings': False,
            'quiet': False,
            'extractor_args': {
                'youtube': {
                    'max_sleep_interval': 5,
                }
            }
        }

        logger.info(f"Searching YouTube for: {query}")
        logger.info(f"Download settings - Quality: {selected_quality['abr']}kbps, Format: {format}, Bitrate: {selected_quality['abr']}k")

        # Attempt download with retries
        while retry_count < max_retries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Check if any videos were found before attempting download
                    info = ydl.extract_info(search_url, download=False)
                    if not info or not info.get('entries'):
                        logger.warning(f"No YouTube videos found for query: {query}")
                        if retry_count < max_retries - 1:
                            logger.info(f"Retrying search with slightly modified query...")
                            # Try again with search URL
                            ydl.download([search_url])
                        else:
                            logger.error(f"Failed to find any YouTube videos for query: {query}")
                            return -1
                    else:
                        ydl.download([search_url])

                logger.info(f"Successfully downloaded audio for query: {query}")

                # Try to add metadata to the downloaded file
                downloaded_file_path = get_downloaded_file_path(outtmpl, query)
                if downloaded_file_path:
                    add_metadata(downloaded_file_path, track_info, playlist_or_album_name, track_number)

                return 0
            except yt_dlp.DownloadError as e:
                error_msg = str(e).lower()
                if 'no video' in error_msg or 'no content' in error_msg or 'no matches' in error_msg:
                    logger.error(f"No matching YouTube videos found for query: {query}")
                    return -1
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"Download attempt {retry_count} failed for query '{query}': {str(e)}. Retrying in {retry_count} seconds...")
                        time.sleep(retry_count)  # Wait longer with each retry
                    else:
                        logger.error(f"All {max_retries} download attempts failed for query '{query}': {str(e)}")
                        return -1
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Unexpected error on attempt {retry_count} for query '{query}': {str(e)}. Retrying in {retry_count} seconds...")
                    time.sleep(retry_count)
                else:
                    logger.error(f"All {max_retries} download attempts failed for query '{query}': {str(e)}", exc_info=True)
                    return -1

    except Exception as e:
        logger.error(f"Unexpected error in search_youtube_for_video for query '{query}': {str(e)}", exc_info=True)
        return -1


def add_metadata(file_path, track_info, playlist_or_album_name=None, track_number=None):
    """Add metadata to the downloaded audio file."""
    try:
        if not METADATA_AVAILABLE:
            return  # Skip metadata addition if mutagen is not available

        if not os.path.exists(file_path):
            logger.warning(f"File not found for metadata embedding: {file_path}")
            return

        # Determine the actual filename from the query to get the correct file
        # The file was downloaded with the template from outtmpl
        audio_file = File(file_path)

        if audio_file is not None:
            # The query is in the format "track_name artist_name", need to parse
            # For now, we'll make a best guess based on the original query
            # A better approach would be to pass the specific track info
            if hasattr(track_info, 'get'):  # If it's a dictionary (like from Spotify API)
                title = track_info.get('name', '')
                artist = track_info.get('artists', [{}])[0].get('name', '') if track_info.get('artists') else ''
                album = playlist_or_album_name
                track_num = track_number
            else:
                # If track_info is just the query string, parse it
                query_parts = query.split(' ', 1)
                if len(query_parts) > 1:
                    artist = query_parts[0]
                    title = query_parts[1]
                else:
                    title = query
                    artist = ''
                album = playlist_or_album_name
                track_num = track_number

            # Add basic metadata
            if hasattr(audio_file, 'tags') and audio_file.tags is not None:
                audio_file.tags.add(TIT2(encoding=3, text=title))
                audio_file.tags.add(TPE1(encoding=3, text=artist))
                if album:
                    audio_file.tags.add(TALB(encoding=3, text=album))
                if track_num:
                    audio_file.tags.add(TRCK(encoding=3, text=str(track_num)))
            else:
                # Create new ID3 tags if they don't exist
                audio_file.add_tags()
                audio_file.tags.add(TIT2(encoding=3, text=title))
                audio_file.tags.add(TPE1(encoding=3, text=artist))
                if album:
                    audio_file.tags.add(TALB(encoding=3, text=album))
                if track_num:
                    audio_file.tags.add(TRCK(encoding=3, text=str(track_num)))

            audio_file.save()
            logger.info(f"Metadata added to: {file_path}")
        else:
            logger.warning(f"Could not load audio file for metadata embedding: {file_path}")
    except Exception as e:
        # Handle Unicode characters in file paths for logging
        safe_file_path = file_path.encode('utf-8', errors='ignore').decode('utf-8')
        logger.error(f"Error adding metadata to: {safe_file_path}: {str(e)}", exc_info=True)


def get_downloaded_file_path(outtmpl, query):
    """Get the actual path of the downloaded file based on the template and query."""
    # This function determines what the file would be named based on the outtmpl
    # and replaces template values with actual values
    import re
    # yt-dlp would populate %(title)s with the actual video title
    # For now we'll return a file that matches the pattern
    directory = os.path.dirname(outtmpl)
    pattern = outtmpl.replace('%(title)s', '*').replace('%(ext)s', '*.mp3')
    # Find files in the directory matching the pattern
    files = []
    if os.path.exists(directory):
        for f in os.listdir(directory):
            if f.endswith('.mp3'):
                files.append(os.path.join(directory, f))

    # Return most recently created file
    if files:
        return max(files, key=os.path.getctime)
    return None
    

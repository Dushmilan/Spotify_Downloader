"""
Main script to connect all processes for Spotify Downloader
Follows the documented workflow:
1. Validate the URL
2. Classify the URL
3. Get track info using Spotify_Scraper
4. Build a search query
5. Search YouTube
6. Get the best match
7. Download audio
8. Convert to desired format
9. Save to projectroot/download folder
"""

import os
import sys
import time
import logging
from Url_Validator import (
    is_spotify_url,
    is_valid_spotify_url,
    is_playlist_url,
    is_album_url,
    is_track_url
)
from Spotify_Scraper import get_track, get_playlist, get_album
from Youtube_query import create_query, search_youtube_for_video


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spotify_downloader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []

    # Check for spotifyscraper
    try:
        import spotify_scraper
    except ImportError:
        missing_deps.append("spotifyscraper")

    # Check for yt_dlp
    try:
        import yt_dlp
    except ImportError:
        missing_deps.append("yt-dlp")

    # Check for requests
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")

    if missing_deps:
        logger.error(f"Missing required dependencies: {', '.join(missing_deps)}")
        print(f"Error: Missing required dependencies: {', '.join(missing_deps)}")
        print("Please install them using: pip install spotifyscraper yt-dlp requests")
        return False

    logger.info("All dependencies are available")
    return True


def download_track_from_spotify_url(track_info, playlist_or_album_name=None, track_number=None, quality='192', format='mp3'):
    """Download a single track by searching YouTube using track info from Spotify."""
    try:
        if isinstance(track_info, dict) and 'name' in track_info and 'artists' in track_info:
            # Get the first artist name
            artist_name = track_info['artists'][0]['name'] if track_info['artists'] else ""
            track_name = track_info['name']

            if not track_name or not artist_name:
                logger.warning(f"Missing track name or artist name in track info: {track_info}")
                return None

            # Create YouTube query (Step 4: Build a search query)
            query = create_query(track_name, artist_name)
            logger.info(f"Searching YouTube for: {query}")
            print(f"Searching YouTube for: {query}")

            # Search and download from YouTube (Steps 5, 6, 7: Search, get best match, download)
            result = search_youtube_for_video(query, playlist_or_album_name, track_number, quality, format, track_info)
            logger.info(f"Download result: {result}")
            return result
        else:
            logger.error("Invalid track info provided")
            print("Invalid track info provided")
            return None
    except Exception as e:
        logger.error(f"Error in download_track_from_spotify_url: {str(e)}", exc_info=True)
        print(f"Error downloading track: {str(e)}")
        return None


def process_spotify_url(spotify_url, quality='192', format='mp3'):
    """Process a Spotify URL following the documented workflow."""
    try:
        # Step 1: Validate the URL
        logger.info(f"Step 1: Validating URL: {spotify_url}")
        print("Step 1: Validating URL...")
        if not is_spotify_url(spotify_url):
            logger.error("Error: Not a valid Spotify URL")
            print("Error: Not a valid Spotify URL")
            return False

        # Check if the URL is accessible
        if not is_valid_spotify_url(spotify_url):
            logger.error("Error: Spotify URL is not accessible")
            print("Error: Spotify URL is not accessible")
            return False

        # Step 2: Classify the URL
        logger.info("Step 2: Classifying URL...")
        print("Step 2: Classifying URL...")
        url_type = None
        if is_track_url(spotify_url):
            url_type = "track"
            logger.info("URL classified as: Track")
            print("URL classified as: Track")
        elif is_playlist_url(spotify_url):
            url_type = "playlist"
            logger.info("URL classified as: Playlist")
            print("URL classified as: Playlist")
        elif is_album_url(spotify_url):
            url_type = "album"
            logger.info("URL classified as: Album")
            print("URL classified as: Album")
        else:
            logger.error("Error: Unrecognized Spotify URL type")
            print("Error: Unrecognized Spotify URL type")
            return False

        # Step 3: Get track info using Spotify_Scraper
        logger.info("Step 3: Getting track info from Spotify...")
        print("Step 3: Getting track info from Spotify...")
        if url_type == "track":
            logger.info("Processing track URL...")
            print("Processing track URL...")
            track_info = get_track(spotify_url)
            if track_info is None:
                logger.error("Failed to retrieve track information from Spotify")
                print("Failed to retrieve track information from Spotify")
                return False
            # Steps 4-7 handled within download_track_from_spotify_url
            download_track_from_spotify_url(track_info, quality=quality, format=format)

        elif url_type == "playlist":
            logger.info("Processing playlist URL...")
            print("Processing playlist URL...")
            playlist_info = get_playlist(spotify_url)
            if playlist_info is None:
                logger.error("Failed to retrieve playlist information from Spotify")
                print("Failed to retrieve playlist information from Spotify")
                return False
            tracks = playlist_info.get('tracks', [])
            if not tracks:
                logger.warning("Playlist has no tracks to download")
                print("Playlist has no tracks to download")
                return False

            # Create a folder for the playlist
            playlist_name = playlist_info.get('name', 'Unknown_Playlist')
            # Sanitize playlist name for use as folder name
            playlist_name = "".join(c for c in playlist_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not playlist_name:
                playlist_name = 'Unknown_Playlist'

            total_tracks = len(tracks)
            print(f"\nStarting download of playlist: {playlist_info.get('name', 'Unknown')}")
            print(f"Total tracks: {total_tracks}")
            print("-" * 50)

            # Track download start time for progress and time estimation
            start_time = time.time()

            for i, track in enumerate(tracks, 1):
                logger.info(f"Processing track {i}/{total_tracks}: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")
                print(f"[{i}/{total_tracks}] Downloading: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")

                result = download_track_from_spotify_url(track, playlist_name, i)

                # Calculate estimated time remaining for playlist downloads
                elapsed_time = time.time() - start_time
                avg_time_per_track = elapsed_time / i
                remaining_tracks = total_tracks - i
                eta_seconds = avg_time_per_track * remaining_tracks

                if result == 0:
                    print(f"  ✓ Successfully downloaded (ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s)")
                else:
                    print(f"  ✗ Failed to download (ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s)")

                print()  # Add a blank line for readability

        elif url_type == "album":
            logger.info("Processing album URL...")
            print("Processing album URL...")
            album_info = get_album(spotify_url)
            if album_info is None:
                logger.error("Failed to retrieve album information from Spotify")
                print("Failed to retrieve album information from Spotify")
                return False
            tracks = album_info.get('tracks', [])
            if not tracks:
                logger.warning("Album has no tracks to download")
                print("Album has no tracks to download")
                return False

            # Create a folder for the album
            album_name = album_info.get('name', 'Unknown_Album')
            # Sanitize album name for use as folder name
            album_name = "".join(c for c in album_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not album_name:
                album_name = 'Unknown_Album'

            total_tracks = len(tracks)
            print(f"\nStarting download of album: {album_info.get('name', 'Unknown')} by {album_info.get('artists', [{}])[0].get('name', 'Unknown') if album_info.get('artists') else 'Unknown'}")
            print(f"Total tracks: {total_tracks}")
            print("-" * 50)

            # Track download start time for progress and time estimation
            start_time = time.time()

            for i, track in enumerate(tracks, 1):
                logger.info(f"Processing track {i}/{total_tracks}: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")
                print(f"[{i}/{total_tracks}] Downloading: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")

                result = download_track_from_spotify_url(track, album_name, i)

                # Calculate estimated time remaining for album downloads
                elapsed_time = time.time() - start_time
                avg_time_per_track = elapsed_time / i
                remaining_tracks = total_tracks - i
                eta_seconds = avg_time_per_track * remaining_tracks

                if result == 0:
                    print(f"  ✓ Successfully downloaded (ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s)")
                else:
                    print(f"  ✗ Failed to download (ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s)")

                print()  # Add a blank line for readability

        # Step 8 and 9 are handled within the YouTube download process
        logger.info("Download process completed!")
        print("Download process completed!")
        return True
    except Exception as e:
        logger.error(f"Error processing Spotify URL: {str(e)}", exc_info=True)
        print(f"Error processing Spotify URL: {str(e)}")
        return False


def main():
    """Main entry point."""
    logger.info("Starting Spotify Downloader...")

    # Check dependencies first
    if not check_dependencies():
        return

    print("Spotify Downloader - Connecting all processes...")
    print("Following documented workflow:")
    print("1. Validate URL -> 2. Classify URL -> 3. Get track info -> 4. Build search query ->")
    print("5. Search YouTube -> 6. Get best match -> 7. Download audio -> 8. Convert -> 9. Save")

    if len(sys.argv) < 2:
        logger.error("Incorrect number of arguments provided")
        print("\nUsage: python main.py <spotify_url> [quality] [format]")
        print("Example: python main.py https://open.spotify.com/track/...")
        print("Example with quality: python main.py https://open.spotify.com/track/... 320 mp3")
        print("Quality options: 128, 192 (default), 256, 320")
        print("Format options: mp3 (default), m4a, wav, flac")
        return

    spotify_url = sys.argv[1]

    # Set default quality and format
    quality = '192'  # Default quality
    audio_format = 'mp3'  # Default format

    # Check if quality and format are provided as arguments
    if len(sys.argv) >= 3:
        quality = sys.argv[2]
        # Validate quality
        valid_qualities = ['128', '192', '256', '320']
        if quality not in valid_qualities:
            print(f"Warning: Invalid quality '{quality}' provided. Using default (192).")
            print(f"Valid qualities: {', '.join(valid_qualities)}")
            quality = '192'

    if len(sys.argv) >= 4:
        audio_format = sys.argv[3]
        # Validate format
        valid_formats = ['mp3', 'm4a', 'wav', 'flac']
        if audio_format not in valid_formats:
            print(f"Warning: Invalid format '{audio_format}' provided. Using default (mp3).")
            print(f"Valid formats: {', '.join(valid_formats)}")
            audio_format = 'mp3'

    if not spotify_url:
        logger.error("Empty URL provided")
        print("\nError: Empty URL provided")
        return

    print(f"\nProcessing URL: {spotify_url}")
    print(f"Download quality: {quality}kbps")
    print(f"Download format: {audio_format}")
    print("-" * 30)

    # Pass quality and format to the processing function
    success = process_spotify_url(spotify_url, quality, audio_format)

    if success:
        logger.info("All processes connected successfully!")
        print("\nAll processes connected successfully!")
    else:
        logger.error("Error in processing the URL.")
        print("\nError in processing the URL.")


if __name__ == "__main__":
    main()
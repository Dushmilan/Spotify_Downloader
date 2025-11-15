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


def download_track_from_spotify_url(track_info):
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
            result = search_youtube_for_video(query)
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


def process_spotify_url(spotify_url):
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
            download_track_from_spotify_url(track_info)

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
            for i, track in enumerate(tracks, 1):
                logger.info(f"Processing track {i}/{len(tracks)}: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")
                print(f"Processing track {i}/{len(tracks)}: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")
                download_track_from_spotify_url(track)

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
            for i, track in enumerate(tracks, 1):
                logger.info(f"Processing track {i}/{len(tracks)}: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")
                print(f"Processing track {i}/{len(tracks)}: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")
                download_track_from_spotify_url(track)

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

    if len(sys.argv) != 2:
        logger.error("Incorrect number of arguments provided")
        print("\nUsage: python main.py <spotify_url>")
        print("Example: python main.py https://open.spotify.com/track/...")
        return

    spotify_url = sys.argv[1]

    if not spotify_url:
        logger.error("Empty URL provided")
        print("\nError: Empty URL provided")
        return

    print(f"\nProcessing URL: {spotify_url}")
    success = process_spotify_url(spotify_url)

    if success:
        logger.info("All processes connected successfully!")
        print("\nAll processes connected successfully!")
    else:
        logger.error("Error in processing the URL.")
        print("\nError in processing the URL.")


if __name__ == "__main__":
    main()
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
from Url_Validator import (
    is_spotify_url,
    is_valid_spotify_url,
    is_playlist_url,
    is_album_url,
    is_track_url
)
from Spotify_Scraper import get_track, get_playlist, get_album
from Youtube_query import create_query, search_youtube_for_video


def download_track_from_spotify_url(track_info):
    """Download a single track by searching YouTube using track info from Spotify."""
    if isinstance(track_info, dict) and 'name' in track_info and 'artists' in track_info:
        # Get the first artist name
        artist_name = track_info['artists'][0]['name'] if track_info['artists'] else ""
        track_name = track_info['name']

        # Create YouTube query (Step 4: Build a search query)
        query = create_query(track_name, artist_name)
        print(f"Searching YouTube for: {query}")

        # Search and download from YouTube (Steps 5, 6, 7: Search, get best match, download)
        result = search_youtube_for_video(query)
        return result
    else:
        print("Invalid track info provided")
        return None


def process_spotify_url(spotify_url):
    """Process a Spotify URL following the documented workflow."""
    # Step 1: Validate the URL
    print("Step 1: Validating URL...")
    if not is_spotify_url(spotify_url):
        print("Error: Not a valid Spotify URL")
        return False

    # Check if the URL is accessible
    if not is_valid_spotify_url(spotify_url):
        print("Error: Spotify URL is not accessible")
        return False

    # Step 2: Classify the URL
    print("Step 2: Classifying URL...")
    url_type = None
    if is_track_url(spotify_url):
        url_type = "track"
        print("URL classified as: Track")
    elif is_playlist_url(spotify_url):
        url_type = "playlist"
        print("URL classified as: Playlist")
    elif is_album_url(spotify_url):
        url_type = "album"
        print("URL classified as: Album")
    else:
        print("Error: Unrecognized Spotify URL type")
        return False

    # Step 3: Get track info using Spotify_Scraper
    print("Step 3: Getting track info from Spotify...")
    if url_type == "track":
        print("Processing track URL...")
        track_info = get_track(spotify_url)
        # Steps 4-7 handled within download_track_from_spotify_url
        download_track_from_spotify_url(track_info)

    elif url_type == "playlist":
        print("Processing playlist URL...")
        playlist_info = get_playlist(spotify_url)
        tracks = playlist_info.get('tracks', [])
        for i, track in enumerate(tracks, 1):
            print(f"Processing track {i}/{len(tracks)}: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")
            download_track_from_spotify_url(track)

    elif url_type == "album":
        print("Processing album URL...")
        album_info = get_album(spotify_url)
        tracks = album_info.get('tracks', [])
        for i, track in enumerate(tracks, 1):
            print(f"Processing track {i}/{len(tracks)}: {track['name']} by {track['artists'][0]['name'] if track['artists'] else 'Unknown'}")
            download_track_from_spotify_url(track)

    # Step 8 and 9 are handled within the YouTube download process
    print("Download process completed!")
    return True


def main():
    """Main entry point."""
    print("Spotify Downloader - Connecting all processes...")
    print("Following documented workflow:")
    print("1. Validate URL -> 2. Classify URL -> 3. Get track info -> 4. Build search query ->")
    print("5. Search YouTube -> 6. Get best match -> 7. Download audio -> 8. Convert -> 9. Save")

    if len(sys.argv) != 2:
        print("\nUsage: python main.py <spotify_url>")
        print("Example: python main.py https://open.spotify.com/track/...")
        return

    spotify_url = sys.argv[1]
    print(f"\nProcessing URL: {spotify_url}")
    success = process_spotify_url(spotify_url)

    if success:
        print("\nAll processes connected successfully!")
    else:
        print("\nError in processing the URL.")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Spotify Downloader - Download Spotify tracks, albums, and playlists
"""

import argparse
import sys
from src.spotify_downloader import SpotifyDownloader


def main():
    parser = argparse.ArgumentParser(description="Download Spotify content as audio files")
    parser.add_argument("url", help="Spotify URL to download")
    parser.add_argument("-o", "--output", default="./downloads", help="Output directory")
    parser.add_argument("--format", default="mp3", choices=["mp3", "wav", "flac"], help="Output audio format")
    
    args = parser.parse_args()
    
    downloader = SpotifyDownloader(output_dir=args.output, audio_format=args.format)
    
    try:
        downloader.download(args.url)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
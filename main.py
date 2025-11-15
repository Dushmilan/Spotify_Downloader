#!/usr/bin/env python3
"""
Spotify Downloader - Download Spotify tracks, albums, and playlists
"""

import argparse
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from spotify_downloader import SpotifyDownloader


def main():
    parser = argparse.ArgumentParser(
        description="Download Spotify content as audio files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://open.spotify.com/track/...                    # Download a single track
  %(prog)s https://open.spotify.com/album/... -q 320k            # Download album with high quality
  %(prog)s https://open.spotify.com/playlist/... -o ./music      # Download playlist to custom directory
  %(prog)s https://open.spotify.com/track/... --format wav      # Download as WAV format
        """
    )
    parser.add_argument("url", help="Spotify URL to download (track, album, or playlist)")
    parser.add_argument("-o", "--output", default="./downloads", help="Output directory (default: ./downloads)")
    parser.add_argument("--format", default="mp3", choices=["mp3", "wav", "flac", "m4a"], help="Output audio format (default: mp3)")
    parser.add_argument("-q", "--quality", default="192k", choices=["128k", "192k", "256k", "320k"],
                        help="Audio quality/bitrate (default: 192k)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--no-convert", action="store_true", help="Skip format conversion (keep original format)")

    args = parser.parse_args()

    # Create downloader instance with additional options
    downloader = SpotifyDownloader(
        output_dir=args.output,
        audio_format=args.format,
        audio_quality=args.quality
    )

    # Set verbosity based on argument
    if hasattr(downloader.spotify_scraper, 'set_verbose'):
        downloader.spotify_scraper.set_verbose(args.verbose)
    if hasattr(downloader.youtube_searcher, 'set_verbose'):
        downloader.youtube_searcher.set_verbose(args.verbose)

    try:
        if args.verbose:
            print(f"Starting download from: {args.url}")
            print(f"Output directory: {args.output}")
            print(f"Format: {args.format}")
            print(f"Quality: {args.quality}")

        downloader.download(args.url, verbose=args.verbose)

        print("\nDownload completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
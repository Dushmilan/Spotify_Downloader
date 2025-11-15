"""
Core downloader module for the Spotify Downloader.

This module contains the main orchestrator class that manages the entire
download process from Spotify metadata to final audio files.
"""

import os
from typing import Optional
import logging

from ..services.url_handler import URLHandler
from ..services.spotify_handler import SpotifyScraper
from ..services.youtube_searcher import YouTubeSearcher
from ..services.file_converter import FileConverter
from ..utils.logger import get_logger
from ..exceptions import UnsupportedURLError


class SpotifyDownloader:
    """
    Main orchestrator class that manages the entire download process.

    This class handles downloading Spotify tracks, albums, and playlists
    by extracting metadata from Spotify and finding corresponding audio
    on YouTube which is then converted to the desired format.
    """

    def __init__(self, output_dir: str = "./downloads", audio_format: str = "mp3", audio_quality: str = "192k",
                 verbose: bool = False):
        """
        Initialize the SpotifyDownloader.

        Args:
            output_dir (str): Directory to save downloaded files. Defaults to "./downloads".
            audio_format (str): Target audio format (mp3, wav, flac, etc.). Defaults to "mp3".
            audio_quality (str): Target audio quality (e.g. "192k", "320k"). Defaults to "192k".
            verbose (bool): Enable verbose logging. Defaults to False.
        """
        self.output_dir = output_dir
        self.audio_format = audio_format
        self.audio_quality = audio_quality
        self.url_handler = URLHandler()
        self.spotify_scraper = SpotifyScraper()
        self.youtube_searcher = YouTubeSearcher()
        self.file_converter = FileConverter()
        self.logger = get_logger(__name__, logging.DEBUG if verbose else logging.WARNING)

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def download(self, url: str, verbose: bool = False):
        """
        Main method to download Spotify content.

        This method orchestrates the entire download process by:
        1. Categorizing the URL to determine if it's a track, album, or playlist
        2. Extracting relevant metadata from Spotify
        3. Finding and downloading the audio from YouTube
        4. Converting to the specified format

        Args:
            url (str): The Spotify URL to download (track, album, or playlist)
            verbose (bool): Enable verbose output for debugging. Defaults to False.

        Raises:
            ValueError: If the URL type is unsupported
            Exception: If no YouTube video is found for a track
        """
        # Categorize the URL
        try:
            url_type, spotify_id = self.url_handler.categorize_url(url)
        except ValueError as e:
            self.logger.error(f"Invalid URL provided: {url}")
            raise UnsupportedURLError(f"Invalid Spotify URL: {url}") from e

        self.logger.info(f"Detected {url_type} with ID: {spotify_id}")
        print(f"Detected {url_type}...")

        if url_type == "track":
            self._download_track(spotify_id, verbose=verbose)
        elif url_type == "album":
            self._download_album(spotify_id, verbose=verbose)
        elif url_type == "playlist":
            self._download_playlist(spotify_id, verbose=verbose)
        else:
            error_msg = f"Unsupported URL type: {url_type}"
            self.logger.error(error_msg)
            raise UnsupportedURLError(error_msg)

    def _download_track(self, track_id: str, verbose: bool = False):
        """
        Download a single track.

        Processes a single Spotify track by extracting its metadata,
        finding it on YouTube, downloading the audio, and converting
        to the specified format.

        Args:
            track_id (str): The Spotify track ID to download
            verbose (bool): Enable verbose output for debugging. Defaults to False.

        Raises:
            Exception: If no YouTube video is found for the track
        """
        self.logger.info(f"Getting track info for ID: {track_id}")
        if verbose:
            print(f"Getting track info for ID: {track_id}")
        track_info = self.spotify_scraper.get_track_info(track_id)

        # Create search query
        query = f"{track_info['artist']} {track_info['title']} audio"

        # Search on YouTube
        self.logger.debug(f"Searching YouTube for: {query}")
        if verbose:
            print(f"Searching YouTube for: {query}")
        videos = self.youtube_searcher.search_youtube(query, max_results=1)

        if not videos:
            error_msg = f"No YouTube video found for {track_info['artist']} - {track_info['title']}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        video = videos[0]
        self.logger.info(f"Found YouTube video: {video['title']}")
        if verbose:
            print(f"Found YouTube video: {video['title']}")

        # Create filename
        clean_title = "".join(c for c in f"{track_info['artist']} - {track_info['title']}" if c.isalnum() or c in "()._ ")
        temp_filename = os.path.join(self.output_dir, f"{clean_title}_temp")
        output_filename = os.path.join(self.output_dir, f"{clean_title}.{self.audio_format}")

        # Download audio from YouTube
        if verbose:
            print(f"Downloading audio...")
        self.youtube_searcher.download_audio(video['url'], temp_filename, verbose=verbose)

        # Convert to target format if needed
        if self.audio_format != 'mp3':
            if verbose:
                print(f"Converting to {self.audio_format} format...")
            self.file_converter.convert_to_format(
                temp_filename + ".mp3",
                output_filename,
                self.audio_format,
                quality=self.audio_quality
            )
        else:
            # If the target format is mp3, rename the file
            os.rename(temp_filename + ".mp3", output_filename)

        print(f"✓ Downloaded: {os.path.basename(output_filename)}")

    def _download_album(self, album_id: str, verbose: bool = False):
        """
        Download all tracks from an album.

        Downloads all tracks from a specified Spotify album, organizing them
        in a dedicated folder and preserving track numbers for proper ordering.

        Args:
            album_id (str): The Spotify album ID to download
            verbose (bool): Enable verbose output for debugging. Defaults to False.
        """
        if verbose:
            print(f"Getting album info for ID: {album_id}")
        album_info = self.spotify_scraper.get_album_info(album_id)

        print(f"Album: {album_info['title']} by {album_info['artist']} [{len(album_info['tracks'])} tracks]")

        # Create album directory
        album_dir = os.path.join(self.output_dir, "".join(c for c in f"{album_info['artist']} - {album_info['title']}" if c.isalnum() or c in "()._ "))
        os.makedirs(album_dir, exist_ok=True)

        # Download each track
        for i, track in enumerate(album_info['tracks']):
            try:
                # Add track number to filename for proper ordering
                track_number = str(track['track_number']).zfill(2) if track.get('track_number') else str(i+1).zfill(2)

                # Create search query
                query = f"{track['artist']} {track['title']} audio"

                # Search on YouTube
                if verbose:
                    print(f"  [{i+1}/{len(album_info['tracks'])}] Searching YouTube for: {query}")
                videos = self.youtube_searcher.search_youtube(query, max_results=1)

                if not videos:
                    print(f"  ⚠ Warning: No YouTube video found for {track['artist']} - {track['title']}, skipping...")
                    continue

                video = videos[0]
                if verbose:
                    print(f"    Found YouTube video: {video['title']}")

                # Create filename
                clean_title = "".join(c for c in f"{track_number} {track['artist']} - {track['title']}" if c.isalnum() or c in "()._ ")
                temp_filename = os.path.join(album_dir, f"{clean_title}_temp")
                output_filename = os.path.join(album_dir, f"{clean_title}.{self.audio_format}")

                # Download audio from YouTube
                if verbose:
                    print(f"    Downloading audio...")
                self.youtube_searcher.download_audio(video['url'], temp_filename, verbose=verbose)

                # Convert to target format if needed
                if self.audio_format != 'mp3':
                    if verbose:
                        print(f"    Converting to {self.audio_format} format...")
                    self.file_converter.convert_to_format(
                        temp_filename + ".mp3",
                        output_filename,
                        self.audio_format,
                        quality=self.audio_quality
                    )
                else:
                    # If the target format is mp3, rename the file
                    os.rename(temp_filename + ".mp3", output_filename)

                print(f"  ✓ Downloaded: {os.path.basename(output_filename)}")
            except Exception as e:
                print(f"  ✗ Error downloading track {track['title']}: {e}")

        print(f"\nAlbum download completed! Saved to: {album_dir}")

    def _download_playlist(self, playlist_id: str, verbose: bool = False):
        """
        Download all tracks from a playlist.

        Downloads all tracks from a specified Spotify playlist, organizing them
        in a dedicated folder and maintaining the order of the tracks.

        Args:
            playlist_id (str): The Spotify playlist ID to download
            verbose (bool): Enable verbose output for debugging. Defaults to False.
        """
        if verbose:
            print(f"Getting playlist info for ID: {playlist_id}")
        playlist_info = self.spotify_scraper.get_playlist_info(playlist_id)

        print(f"Playlist: {playlist_info['title']} by {playlist_info['owner']} [{len(playlist_info['tracks'])} tracks]")

        # Create playlist directory
        playlist_dir = os.path.join(self.output_dir, "".join(c for c in f"{playlist_info['owner']} - {playlist_info['title']}" if c.isalnum() or c in "()._ "))
        os.makedirs(playlist_dir, exist_ok=True)

        # Download each track
        for i, track in enumerate(playlist_info['tracks']):
            try:
                # Create search query
                query = f"{track['artist']} {track['title']} audio"

                # Search on YouTube
                if verbose:
                    print(f"  [{i+1}/{len(playlist_info['tracks'])}] Searching YouTube for: {query}")
                videos = self.youtube_searcher.search_youtube(query, max_results=1)

                if not videos:
                    print(f"  ⚠ Warning: No YouTube video found for {track['artist']} - {track['title']}, skipping...")
                    continue

                video = videos[0]
                if verbose:
                    print(f"    Found YouTube video: {video['title']}")

                # Create filename
                track_number = str(i+1).zfill(2)
                clean_title = "".join(c for c in f"{track_number} {track['artist']} - {track['title']}" if c.isalnum() or c in "()._ ")
                temp_filename = os.path.join(playlist_dir, f"{clean_title}_temp")
                output_filename = os.path.join(playlist_dir, f"{clean_title}.{self.audio_format}")

                # Download audio from YouTube
                if verbose:
                    print(f"    Downloading audio...")
                self.youtube_searcher.download_audio(video['url'], temp_filename, verbose=verbose)

                # Convert to target format if needed
                if self.audio_format != 'mp3':
                    if verbose:
                        print(f"    Converting to {self.audio_format} format...")
                    self.file_converter.convert_to_format(
                        temp_filename + ".mp3",
                        output_filename,
                        self.audio_format,
                        quality=self.audio_quality
                    )
                else:
                    # If the target format is mp3, rename the file
                    os.rename(temp_filename + ".mp3", output_filename)

                print(f"  ✓ Downloaded: {os.path.basename(output_filename)}")
            except Exception as e:
                print(f"  ✗ Error downloading track {track['title']}: {e}")

        print(f"\nPlaylist download completed! Saved to: {playlist_dir}")
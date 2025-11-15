"""
Main orchestrator for the Spotify Downloader
"""

import os
from .url_handler import URLHandler
from .spotify_scraper import SpotifyScraper
from .youtube_searcher import YouTubeSearcher
from .file_converter import FileConverter


class SpotifyDownloader:
    """
    Main class that orchestrates the entire download process
    """
    
    def __init__(self, output_dir="./downloads", audio_format="mp3"):
        """
        Initialize the SpotifyDownloader
        
        Args:
            output_dir (str): Directory to save downloaded files
            audio_format (str): Target audio format (mp3, wav, flac, etc.)
        """
        self.output_dir = output_dir
        self.audio_format = audio_format
        self.url_handler = URLHandler()
        self.spotify_scraper = SpotifyScraper()
        self.youtube_searcher = YouTubeSearcher()
        self.file_converter = FileConverter()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def download(self, url):
        """
        Main method to download Spotify content
        
        Args:
            url (str): Spotify URL to download
        """
        # Categorize the URL
        url_type, spotify_id = self.url_handler.categorize_url(url)
        
        print(f"Detected {url_type} with ID: {spotify_id}")
        
        if url_type == "track":
            self._download_track(spotify_id)
        elif url_type == "album":
            self._download_album(spotify_id)
        elif url_type == "playlist":
            self._download_playlist(spotify_id)
        else:
            raise ValueError(f"Unsupported URL type: {url_type}")
    
    def _download_track(self, track_id):
        """
        Download a single track
        
        Args:
            track_id (str): Spotify track ID
        """
        print(f"Getting track info for ID: {track_id}")
        track_info = self.spotify_scraper.get_track_info(track_id)
        
        # Create search query
        query = f"{track_info['artist']} {track_info['title']} audio"
        
        # Search on YouTube
        print(f"Searching YouTube for: {query}")
        videos = self.youtube_searcher.search_youtube(query, max_results=1)
        
        if not videos:
            raise Exception(f"No YouTube video found for {track_info['artist']} - {track_info['title']}")
        
        video = videos[0]
        print(f"Found YouTube video: {video['title']}")
        
        # Create filename
        clean_title = "".join(c for c in f"{track_info['artist']} - {track_info['title']}" if c.isalnum() or c in "()._ ")
        temp_filename = os.path.join(self.output_dir, f"{clean_title}_temp")
        output_filename = os.path.join(self.output_dir, f"{clean_title}.{self.audio_format}")
        
        # Download audio from YouTube
        print(f"Downloading audio...")
        self.youtube_searcher.download_audio(video['url'], temp_filename)
        
        # Convert to target format if needed
        if self.audio_format != 'mp3':
            print(f"Converting to {self.audio_format} format...")
            self.file_converter.convert_to_format(
                temp_filename + ".mp3", 
                output_filename, 
                self.audio_format
            )
        else:
            # If the target format is mp3, rename the file
            os.rename(temp_filename + ".mp3", output_filename)
        
        print(f"Downloaded: {output_filename}")
    
    def _download_album(self, album_id):
        """
        Download all tracks from an album
        
        Args:
            album_id (str): Spotify album ID
        """
        print(f"Getting album info for ID: {album_id}")
        album_info = self.spotify_scraper.get_album_info(album_id)
        
        print(f"Album: {album_info['title']} by {album_info['artist']}")
        
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
                print(f"[{i+1}/{len(album_info['tracks'])}] Searching YouTube for: {query}")
                videos = self.youtube_searcher.search_youtube(query, max_results=1)
                
                if not videos:
                    print(f"Warning: No YouTube video found for {track['artist']} - {track['title']}, skipping...")
                    continue
                
                video = videos[0]
                print(f"Found YouTube video: {video['title']}")
                
                # Create filename
                clean_title = "".join(c for c in f"{track_number} {track['artist']} - {track['title']}" if c.isalnum() or c in "()._ ")
                temp_filename = os.path.join(album_dir, f"{clean_title}_temp")
                output_filename = os.path.join(album_dir, f"{clean_title}.{self.audio_format}")
                
                # Download audio from YouTube
                print(f"Downloading audio...")
                self.youtube_searcher.download_audio(video['url'], temp_filename)
                
                # Convert to target format if needed
                if self.audio_format != 'mp3':
                    print(f"Converting to {self.audio_format} format...")
                    self.file_converter.convert_to_format(
                        temp_filename + ".mp3", 
                        output_filename, 
                        self.audio_format
                    )
                else:
                    # If the target format is mp3, rename the file
                    os.rename(temp_filename + ".mp3", output_filename)
                
                print(f"Downloaded: {os.path.basename(output_filename)}")
            except Exception as e:
                print(f"Error downloading track {track['title']}: {e}")
    
    def _download_playlist(self, playlist_id):
        """
        Download all tracks from a playlist
        
        Args:
            playlist_id (str): Spotify playlist ID
        """
        print(f"Getting playlist info for ID: {playlist_id}")
        playlist_info = self.spotify_scraper.get_playlist_info(playlist_id)
        
        print(f"Playlist: {playlist_info['title']} by {playlist_info['owner']}")
        
        # Create playlist directory
        playlist_dir = os.path.join(self.output_dir, "".join(c for c in f"{playlist_info['owner']} - {playlist_info['title']}" if c.isalnum() or c in "()._ "))
        os.makedirs(playlist_dir, exist_ok=True)
        
        # Download each track
        for i, track in enumerate(playlist_info['tracks']):
            try:
                # Create search query
                query = f"{track['artist']} {track['title']} audio"
                
                # Search on YouTube
                print(f"[{i+1}/{len(playlist_info['tracks'])}] Searching YouTube for: {query}")
                videos = self.youtube_searcher.search_youtube(query, max_results=1)
                
                if not videos:
                    print(f"Warning: No YouTube video found for {track['artist']} - {track['title']}, skipping...")
                    continue
                
                video = videos[0]
                print(f"Found YouTube video: {video['title']}")
                
                # Create filename
                track_number = str(i+1).zfill(2)
                clean_title = "".join(c for c in f"{track_number} {track['artist']} - {track['title']}" if c.isalnum() or c in "()._ ")
                temp_filename = os.path.join(playlist_dir, f"{clean_title}_temp")
                output_filename = os.path.join(playlist_dir, f"{clean_title}.{self.audio_format}")
                
                # Download audio from YouTube
                print(f"Downloading audio...")
                self.youtube_searcher.download_audio(video['url'], temp_filename)
                
                # Convert to target format if needed
                if self.audio_format != 'mp3':
                    print(f"Converting to {self.audio_format} format...")
                    self.file_converter.convert_to_format(
                        temp_filename + ".mp3", 
                        output_filename, 
                        self.audio_format
                    )
                else:
                    # If the target format is mp3, rename the file
                    os.rename(temp_filename + ".mp3", output_filename)
                
                print(f"Downloaded: {os.path.basename(output_filename)}")
            except Exception as e:
                print(f"Error downloading track {track['title']}: {e}")
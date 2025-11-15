"""
Services module for the Spotify Downloader

Contains specific service classes for different functionality:
- URL handling
- Spotify data scraping
- YouTube audio downloading
- File conversion
"""
from .url_handler import URLHandler
from .spotify_handler import SpotifyScraper
from .youtube_searcher import YouTubeSearcher
from .file_converter import FileConverter

__all__ = ["URLHandler", "SpotifyScraper", "YouTubeSearcher", "FileConverter"]
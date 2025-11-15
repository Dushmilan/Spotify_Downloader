"""
Custom exceptions for the Spotify Downloader.

Defines specific exception types for different error scenarios
in the application to provide better error handling and debugging.
"""


class SpotifyDownloaderError(Exception):
    """Base exception for Spotify Downloader errors."""
    pass


class URLValidationError(SpotifyDownloaderError):
    """Raised when a Spotify URL is invalid or unsupported."""
    pass


class MetadataExtractionError(SpotifyDownloaderError):
    """Raised when failing to extract metadata from Spotify."""
    pass


class YouTubeSearchError(SpotifyDownloaderError):
    """Raised when failing to search or find content on YouTube."""
    pass


class DownloadError(SpotifyDownloaderError):
    """Raised when failing to download audio from YouTube."""
    pass


class ConversionError(SpotifyDownloaderError):
    """Raised when failing to convert audio to the target format."""
    pass


class UnsupportedURLError(SpotifyDownloaderError):
    """Raised when the URL type is not supported."""
    pass
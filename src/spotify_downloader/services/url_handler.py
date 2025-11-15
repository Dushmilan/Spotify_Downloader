"""
Module to handle and categorize Spotify URLs
"""

import re
from urllib.parse import urlparse


class URLHandler:
    """
    Handles parsing and categorization of Spotify URLs
    """

    SPOTIFY_URL_PATTERN = r"https?://(?:open\.spotify\.com|spotify\.link)/(?P<type>track|album|playlist|artist)/(?P<id>[a-zA-Z0-9]+)"

    @staticmethod
    def categorize_url(url):
        """
        Categorizes a Spotify URL as track, album, or playlist

        Args:
            url (str): The Spotify URL to categorize

        Returns:
            tuple: (url_type, spotify_id) where url_type is 'track', 'album', or 'playlist'
        """
        match = re.match(URLHandler.SPOTIFY_URL_PATTERN, url)

        if match:
            url_type = match.group('type')
            spotify_id = match.group('id')
            return url_type, spotify_id
        else:
            raise ValueError(f"Invalid Spotify URL: {url}")

    @staticmethod
    def is_valid_spotify_url(url):
        """
        Checks if a URL is a valid Spotify URL

        Args:
            url (str): The URL to validate

        Returns:
            bool: True if valid, False otherwise
        """
        return bool(re.match(URLHandler.SPOTIFY_URL_PATTERN, url))
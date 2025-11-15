"""Spotify Url Validator and classifier."""

import re
import requests
import logging

logger = logging.getLogger(__name__)


def is_spotify_url(url):
    """Return True if the url is a spotify url."""
    try:
        # Check if it's any kind of Spotify URL
        spotify_pattern = r'https://open\.spotify\.com/(track|playlist|album|artist)/[\w-]+'
        return bool(re.match(spotify_pattern, url))
    except Exception as e:
        logger.error(f"Error in is_spotify_url: {str(e)}", exc_info=True)
        return False

def is_valid_spotify_url(url):
    """Return True if the url is a valid spotify url."""
    try:
        response = requests.get(url, timeout=10)  # Add timeout to prevent hanging
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.warning(f"Network error when validating URL {url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error when validating URL {url}: {str(e)}", exc_info=True)
        return False

def is_playlist_url(url):
    """Return True if the url is a playlist url."""
    try:
        return bool(re.match(r'https://open.spotify.com/playlist/[\w-]+', url))
    except Exception as e:
        logger.error(f"Error in is_playlist_url: {str(e)}", exc_info=True)
        return False

def is_album_url(url):
    """Return True if the url is an album url."""
    try:
        return bool(re.match(r'https://open.spotify.com/album/[\w-]+', url))
    except Exception as e:
        logger.error(f"Error in is_album_url: {str(e)}", exc_info=True)
        return False

def is_track_url(url):
    """Return True if the url is a track url."""
    try:
        return bool(re.match(r'https://open.spotify.com/track/[\w-]+', url))
    except Exception as e:
        logger.error(f"Error in is_track_url: {str(e)}", exc_info=True)
        return False

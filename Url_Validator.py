"""Spotify Url Validator and classifier."""

import re
import requests


def is_spotify_url(url):
    """Return True if the url is a spotify url."""
    return re.match(r'https://open.spotify.com/track/[\w-]+', url)

def is_valid_spotify_url(url):
    """Return True if the url is a valid spotify url."""
    response = requests.get(url)
    return response.status_code == 200

def is_playlist_url(url):
    """Return True if the url is a playlist url."""
    return re.match(r'https://open.spotify.com/playlist/[\w-]+', url)

def is_album_url(url):
    """Return True if the url is an album url."""
    return re.match(r'https://open.spotify.com/album/[\w-]+', url)

def is_track_url(url):
    """Return True if the url is a track url."""
    return re.match(r'https://open.spotify.com/track/[\w-]+', url)

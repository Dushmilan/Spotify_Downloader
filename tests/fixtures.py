"""
Test fixtures and mock data for the Spotify Downloader tests.
Centralized location for all test data and mocks.
"""

from typing import Dict, Any, List


# === Mock Spotify Data ===

FAKE_PLAYLIST_DATA: Dict[str, Any] = {
    'name': 'My Mock Playlist',
    'tracks': {
        'items': [
            {
                'track': {
                    'name': 'Mock Song 1',
                    'artists': [{'name': 'Mock Artist A'}],
                    'duration_ms': 180000,
                    'album': {'name': 'Mock Album X'}
                }
            },
            {
                'track': {
                    'name': 'Mock Song 2',
                    'artists': [{'name': 'Mock Artist B'}],
                    'duration_ms': 200000,
                    'album': {'name': 'Mock Album Y'}
                }
            },
            {
                'track': {
                    'name': 'Mock Song 3',
                    'artists': [{'name': 'Mock Artist C'}],
                    'duration_ms': 220000,
                    'album': {'name': 'Mock Album Z'}
                }
            },
        ]
    }
}

FAKE_TRACK_INFO: Dict[str, Any] = {
    'name': 'Mock Single Song',
    'artist': 'Mock Artist D',
    'album': 'Mock Album W',
    'duration_ms': 240000,
    'artists': [{'name': 'Mock Artist D'}],
}

FAKE_ALBUM_INFO: Dict[str, Any] = {
    'name': 'Mock Album',
    'artists': [{'name': 'Mock Album Artist'}],
    'tracks': {
        'items': [
            {
                'name': 'Album Track 1',
                'artists': [{'name': 'Mock Album Artist'}],
                'duration_ms': 195000,
            },
            {
                'name': 'Album Track 2',
                'artists': [{'name': 'Mock Album Artist'}],
                'duration_ms': 210000,
            },
        ]
    }
}


# === Mock YouTube Data ===

MOCK_YOUTUBE_SEARCH_RESULTS: List[Dict[str, Any]] = [
    {
        'id': 'mock_video_id_1',
        'title': 'Mock Song 1 - Mock Artist A (Official Audio)',
        'duration_secs': 180,
        'url': 'https://www.youtube.com/watch?v=mock_video_id_1'
    },
    {
        'id': 'mock_video_id_2',
        'title': 'Mock Song 2 - Mock Artist B (Official Music Video)',
        'duration_secs': 200,
        'url': 'https://www.youtube.com/watch?v=mock_video_id_2'
    },
]


# === Mock Download Metadata ===

MOCK_METADATA_SINGLE: Dict[str, Any] = {
    'name': 'Mock Song',
    'artist': 'Mock Artist',
    'duration_ms': 180000,
    'album': 'Mock Album',
    'output_dir': 'test_downloads',
}

MOCK_METADATA_PLAYLIST: Dict[str, Any] = {
    'name': 'Mock Playlist Song',
    'artist': 'Mock Playlist Artist',
    'duration_ms': 200000,
    'album': 'Mock Playlist Album',
    'output_dir': 'test_downloads/Mock_Playlist',
    'playlist_name': 'Mock Playlist',
}


# === Mock Config ===

MOCK_CONFIG: Dict[str, Any] = {
    'download_path': 'test_downloads',
    'max_concurrent_downloads': 2,
    'download_quality': '320kbps',
    'file_format': 'mp3',
    'enable_logging': True,
    'log_level': 'DEBUG',
    'retry_attempts': 3,
    'timeout_seconds': 10,
    'safe_mode': True,
}


# === Mock URL Data ===

VALID_SPOTIFY_TRACK_URL = 'https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT'
VALID_SPOTIFY_PLAYLIST_URL = 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M'
VALID_SPOTIFY_ALBUM_URL = 'https://open.spotify.com/album/41GuZcammIkupMPKH2OJ6I'
INVALID_URL = 'https://example.com/not-a-spotify-url'
MALICIOUS_URL = 'https://evil.com/../../../etc/passwd'


# === Mock File Data ===

MOCK_MP3_FILE_DATA = b'\xff\xfb\x90\x00' + b'\x00' * 100  # Minimal MP3 header
MOCK_IMAGE_DATA = b'\xff\xd8\xff\xe0' + b'\x00' * 100  # Minimal JPEG header


# === Helper Functions ===

def create_mock_track(
    name: str = 'Test Track',
    artist: str = 'Test Artist',
    duration_ms: int = 180000,
    album: str = 'Test Album'
) -> Dict[str, Any]:
    """Create a mock track dictionary with customizable fields."""
    return {
        'track': {
            'name': name,
            'artists': [{'name': artist}],
            'duration_ms': duration_ms,
            'album': {'name': album}
        }
    }


def create_mock_metadata(
    name: str = 'Test Track',
    artist: str = 'Test Artist',
    output_dir: str = 'test_downloads',
    playlist_name: str = None
) -> Dict[str, Any]:
    """Create mock metadata for download operations."""
    metadata = {
        'name': name,
        'artist': artist,
        'duration_ms': 180000,
        'album': 'Test Album',
        'output_dir': output_dir,
    }
    if playlist_name:
        metadata['playlist_name'] = playlist_name
    return metadata

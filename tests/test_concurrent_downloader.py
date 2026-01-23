import os
import sys
import time
import shutil
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.core.downloader import SpotDownloader

# Mock playlist data
FAKE_PLAYLIST_DATA = {
    'name': 'My Test Playlist',
    'tracks': {
        'items': [
            {'track': {'name': 'Song 1', 'artists': [{'name': 'Artist A'}], 'duration_ms': 180000, 'album': {'name': 'Album X'}}},
            {'track': {'name': 'Song 2', 'artists': [{'name': 'Artist B'}], 'duration_ms': 200000, 'album': {'name': 'Album Y'}}},
            {'track': {'name': 'Song 3', 'artists': [{'name': 'Artist C'}], 'duration_ms': 220000, 'album': {'name': 'Album Z'}}},
        ]
    }
}

DOWNLOAD_DIR = "test_concurrent_downloads"

def setup_module(module):
    """Setup for the test module"""
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)

def teardown_module(module):
    """Teardown for the test module"""
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)

import os
import sys
import time
import shutil
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.core.downloader import SpotDownloader

# Mock playlist data
FAKE_PLAYLIST_DATA = {
    'name': 'My Test Playlist',
    'tracks': {
        'items': [
            {'track': {'name': 'Song 1', 'artists': [{'name': 'Artist A'}], 'duration_ms': 180000, 'album': {'name': 'Album X'}}},
            {'track': {'name': 'Song 2', 'artists': [{'name': 'Artist B'}], 'duration_ms': 200000, 'album': {'name': 'Album Y'}}},
            {'track': {'name': 'Song 3', 'artists': [{'name': 'Artist C'}], 'duration_ms': 220000, 'album': {'name': 'Album Z'}}},
        ]
    }
}

DOWNLOAD_DIR = "test_concurrent_downloads"

def setup_module(module):
    """Setup for the test module"""
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)

def teardown_module(module):
    """Teardown for the test module"""
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)

import os
import sys
import time
import shutil
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.core.downloader import SpotDownloader

# Mock playlist data (this is now defined within downloader.py as well, but kept here for clarity in test)
FAKE_PLAYLIST_DATA = {
    'name': 'My Test Playlist',
    'tracks': {
        'items': [
            {'track': {'name': 'Song 1', 'artists': [{'name': 'Artist A'}], 'duration_ms': 180000, 'album': {'name': 'Album X'}}},
            {'track': {'name': 'Song 2', 'artists': [{'name': 'Artist B'}], 'duration_ms': 200000, 'album': {'name': 'Album Y'}}},
            {'track': {'name': 'Song 3', 'artists': [{'name': 'Artist C'}], 'duration_ms': 220000, 'album': {'name': 'Album Z'}}},
        ]
    }
}

DOWNLOAD_DIR = "test_concurrent_downloads"

def setup_module(module):
    """Setup for the test module"""
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)

def teardown_module(module):
    """Teardown for the test module"""
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)

@patch('spot_downloader.core.custom_engine.CustomDownloadEngine')
def test_concurrent_playlist_download(MockCustomDownloadEngine):
    """
    Test that the downloader processes a playlist concurrently.
    """
    # 1. Setup Mocks
    # Mock the CustomDownloadEngine to simulate file creation and avoid actual downloads
    mock_engine_instance = MockCustomDownloadEngine.return_value
    
    # This mock simulates a successful download that creates an empty file
    def fake_download_and_tag(meta, progress_callback, log_callback):
        # meta['output_dir'] should be populated by the downloader.download method
        # It is expected to be a full path like 'test_concurrent_downloads/My Mock Playlist'
        output_dir_from_meta = meta.get('output_dir')
        
        if not output_dir_from_meta:
            # Fallback in case output_dir is unexpectedly missing from meta
            # This should ideally not happen if downloader.py is working correctly
            if log_callback:
                log_callback("Warning: meta['output_dir'] not found, using fallback directory.")
            output_dir_from_meta = os.path.join(DOWNLOAD_DIR, 'My Mock Playlist') # Fallback directory

        artist = meta['artist']
        song = meta['name']
        file_name = f"{artist} - {song}.mp3"
        
        # Construct the full file path using the output_dir from meta
        file_path = os.path.join(output_dir_from_meta, file_name)
        
        # Simulate download time
        time.sleep(0.01) # Shorter sleep for faster tests
        
        # Create a dummy file to represent the downloaded song
        # os.path.dirname(file_path) will be the directory that needs to be created
        os.makedirs(os.path.dirname(file_path), exist_ok=True) 
        with open(file_path, 'w') as f:
            f.write("dummy content")
            
        if log_callback:
            log_callback(f"Finished downloading {song}")
        return True

    mock_engine_instance.download_and_tag.side_effect = fake_download_and_tag

    # 2. Initialize Downloader and Start Download
    downloader = SpotDownloader(download_path=DOWNLOAD_DIR)
    
    log_messages = []
    def log_callback(message):
        log_messages.append(message)

    # The URL here is a dummy Spotify URL, as the SpotifyClient interaction is now mocked/removed
    download_thread = downloader.download("https://open.spotify.com/playlist/fakeplaylist", log_callback=log_callback)
    
    # Wait for the download thread to finish
    download_thread.join(timeout=10) # 10-second timeout

    # 3. Assertions
    assert not download_thread.is_alive(), "Download thread did not finish in time."

    # Check that download_and_tag was called for each track
    assert mock_engine_instance.download_and_tag.call_count == len(FAKE_PLAYLIST_DATA['tracks']['items'])

    # Check if files were created in the expected directory structure
    playlist_name_for_assertion = FAKE_PLAYLIST_DATA['name'] # Use the mock data name
    safe_playlist_name = "".join([c for c in playlist_name_for_assertion if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
    expected_playlist_path = os.path.join(DOWNLOAD_DIR, safe_playlist_name)

    assert os.path.isdir(expected_playlist_path)
    
    downloaded_files = os.listdir(expected_playlist_path)
    # Filter out any other files that might be created, like the playlist.json cache
    downloaded_songs = [f for f in downloaded_files if f.endswith('.mp3')]
    
    assert len(downloaded_songs) == 3, f"Expected 3 songs, but found {len(downloaded_songs)}"

    # Check for completion message
    assert "All downloads finished!" in log_messages, "Final completion message was not logged."

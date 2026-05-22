import os
import sys
import shutil
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.core.downloader import SpotDownloader

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


def test_concurrent_playlist_download():
    """
    Test that the downloader processes a playlist concurrently.
    """
    fake_scraper = MagicMock()
    fake_scraper.scrape_playlist.return_value = FAKE_PLAYLIST_DATA

    downloader = SpotDownloader(download_path=DOWNLOAD_DIR, scraper=fake_scraper)

    log_messages = []

    with patch('spot_downloader.core.downloader.YouTubeSearcher.search_ytm', return_value='https://youtube.com/watch?v=test'):
        with patch('spot_downloader.core.downloader.yt_dlp.YoutubeDL') as MockYDL:
            mock_ydl_instance = MagicMock()
            MockYDL.return_value.__enter__.return_value = mock_ydl_instance

            def fake_download(video_urls):
                for meta in [FAKE_PLAYLIST_DATA['tracks']['items'][0],
                             FAKE_PLAYLIST_DATA['tracks']['items'][1],
                             FAKE_PLAYLIST_DATA['tracks']['items'][2]]:
                    track_data = meta.get('track', meta)
                    song_name = track_data.get('name', 'Unknown Track')
                    artist_name = track_data.get('artists', [{}])[0].get('name', 'Unknown Artist')
                    playlist_folder = os.path.join(DOWNLOAD_DIR, "My Test Playlist")
                    os.makedirs(playlist_folder, exist_ok=True)
                    file_path = os.path.join(playlist_folder, f"{song_name} - {artist_name}.mp3")
                    with open(file_path, 'w') as f:
                        f.write("dummy content")
            mock_ydl_instance.download.side_effect = fake_download

            with patch('spot_downloader.core.downloader.tag_mp3', return_value=True):
                handle = downloader.download("https://open.spotify.com/playlist/fakeplaylist")
                assert handle is not None
                handle.on_log(lambda msg: log_messages.append(msg))
                result = handle.result(timeout=10)

    assert result.status == 'completed'
    assert result.track_count == 3

    expected_playlist_path = os.path.join(DOWNLOAD_DIR, "My Test Playlist")
    assert os.path.isdir(expected_playlist_path)

    downloaded_files = os.listdir(expected_playlist_path)
    downloaded_songs = [f for f in downloaded_files if f.endswith('.mp3')]
    assert len(downloaded_songs) == 3, f"Expected 3 songs, but found {len(downloaded_songs)}"

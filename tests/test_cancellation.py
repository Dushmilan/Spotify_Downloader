import threading
import time
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Adjust path to include src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from spot_downloader.core.downloader import SpotDownloader

class TestCancellation(unittest.TestCase):
    def test_cancellation(self):
        # We need to mock CustomDownloadEngine where it is defined, so when it is imported
        # inside downloader.download, we get the mock.
        with patch('spot_downloader.core.custom_engine.CustomDownloadEngine') as mock_engine_cls, \
             patch('spotify_scraper.SpotifyClient') as mock_spotify_cls: # Assuming spotify_scraper is importable or mocked
            
            # Mock Spotify Client to return something simple so we enter the loop
            mock_client = mock_spotify_cls.return_value
            mock_client.get_track_info.return_value = {'name': 'Test Song', 'artist': 'Test Artist'}
            
            # Mock Engine
            mock_engine = mock_engine_cls.return_value
            
            # Define a download_and_tag that simulates work and checks cancellation
            def side_effect(metadata, progress_callback=None, log_callback=None, cancel_event=None):
                # Simulate work
                start_time = time.time()
                while time.time() - start_time < 5: # Run for up to 5 seconds
                    if cancel_event and cancel_event.is_set():
                        if log_callback:
                            log_callback("Download cancelled.")
                        return False
                    time.sleep(0.1)
                return True
                
            mock_engine.download_and_tag.side_effect = side_effect

            # Setup downloader
            downloader = SpotDownloader()
            logs = []
            def log_cb(msg):
                logs.append(msg)
                
            # Start download (Simulate a track URL)
            # We use a URL that triggers the "track" logic or fallback
            thread = downloader.download("https://open.spotify.com/track/123456", log_callback=log_cb)
            
            # Give it time to start and enter the engine loop
            time.sleep(0.5)
            
            # Cancel
            print("Cancelling...")
            downloader.cancel()
            
            # Wait for thread to finish
            thread.join(timeout=2)
            
            # Verify
            if thread.is_alive():
                print("Thread is still alive!")
            
            self.assertFalse(thread.is_alive(), "Thread should have finished")
            
            # Check logs
            print("Logs:", logs)
            self.assertTrue(any("cancelled" in m.lower() for m in logs), "Logs should contain 'cancelled'")

if __name__ == '__main__':
    unittest.main()

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.downloader import SpotDownloader

def test_downloader_init():
    downloader = SpotDownloader(download_path="test_downloads")
    assert downloader.download_path == "test_downloads"
    assert os.path.exists("test_downloads")
    os.rmdir("test_downloads")

def test_set_download_path():
    downloader = SpotDownloader()
    downloader.set_download_path("new_test_path")
    assert downloader.download_path == "new_test_path"
    assert os.path.exists("new_test_path")
    os.rmdir("new_test_path")

def test_set_credentials():
    downloader = SpotDownloader()
    downloader.set_credentials("id", "secret")
    assert downloader.client_id == "id"
    assert downloader.client_secret == "secret"

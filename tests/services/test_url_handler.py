"""
Basic tests for Spotify Downloader
"""
import pytest
from spotify_downloader.services.url_handler import URLHandler


def test_url_categorization():
    """Test that URLs are properly categorized"""
    handler = URLHandler()
    
    # Test track URL
    url_type, spotify_id = handler.categorize_url("https://open.spotify.com/track/5ChkMS8OtdzJeqbIZqC49c")
    assert url_type == "track"
    assert spotify_id == "5ChkMS8OtdzJeqbIZqC49c"
    
    # Test album URL
    url_type, spotify_id = handler.categorize_url("https://open.spotify.com/album/4bZ6dIdIB6U5v2i93mS9tk")
    assert url_type == "album"
    assert spotify_id == "4bZ6dIdIB6U5v2i93mS9tk"
    
    # Test playlist URL
    url_type, spotify_id = handler.categorize_url("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
    assert url_type == "playlist"
    assert spotify_id == "37i9dQZF1DXcBWIGoYBM5M"


def test_invalid_url():
    """Test that invalid URLs raise an error"""
    handler = URLHandler()
    
    try:
        handler.categorize_url("https://invalid-url.com")
        assert False, "Expected ValueError for invalid URL"
    except ValueError:
        pass  # Expected
import pytest
import asyncio
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Mock playwright module before importing scraper if it doesn't exist
if 'playwright' not in sys.modules:
    mock_playwright_mod = MagicMock()
    sys.modules['playwright'] = mock_playwright_mod
    sys.modules['playwright.async_api'] = mock_playwright_mod.async_api

from src.spot_downloader.utils.playwright_scraper import PlaywrightScraper

@pytest.mark.asyncio
async def test_scrape_track_mock():
    """
    Test scraping a track using mocked Playwright.
    """
    scraper = PlaywrightScraper()
    url = "https://open.spotify.com/track/4cOdzh0s2UDvYvXpueGTh3"
    
    mock_metadata = {
        'name': "Never Gonna Give You Up",
        'artists': ["Rick Astley"],
        'album': "Whenever You Need Somebody",
        'duration_str': "3:32"
    }

    # Mocking Playwright's async context manager and browser lifecycle
    with patch("playwright.async_api.async_playwright") as mock_async_playwright:
        # Set up the chain of mocks
        playwright_instance = mock_async_playwright.return_value.__aenter__.return_value
        browser = AsyncMock()
        playwright_instance.chromium.launch = AsyncMock(return_value=browser)
        
        context = AsyncMock()
        browser.new_context = AsyncMock(return_value=context)
        
        page = AsyncMock()
        context.new_page = AsyncMock(return_value=page)
        
        # Mock page interactions
        page.goto = AsyncMock()
        page.is_visible = AsyncMock(return_value=False)
        page.wait_for_selector = AsyncMock()
        page.evaluate = AsyncMock(return_value=mock_metadata)
        
        result = await scraper.scrape_track_async(url, headless=True)
        
        assert result is not None
        assert result['name'] == "Never Gonna Give You Up"
        assert result['artists'][0]['name'] == "Rick Astley"
        assert result['duration_ms'] == (3 * 60 + 32) * 1000
        assert result['album']['name'] == "Whenever You Need Somebody"
        
        # Verify mocks were called correctly
        page.goto.assert_called_once_with(url, wait_until="domcontentloaded", timeout=30000)
        page.evaluate.assert_called_once()
        browser.close.assert_called_once()

@pytest.mark.asyncio
async def test_scrape_album_mock():
    scraper = PlaywrightScraper()
    url = "https://open.spotify.com/album/..."
    
    mock_album_data = {
        'name': "Whenever You Need Somebody",
        'tracks': [
            {'name': "Never Gonna Give You Up", 'artists': ["Rick Astley"], 'duration_str': "3:32"},
            {'name': "Together Forever", 'artists': ["Rick Astley"], 'duration_str': "3:24"}
        ]
    }

    with patch("playwright.async_api.async_playwright") as mock_async_playwright:
        playwright_instance = mock_async_playwright.return_value.__aenter__.return_value
        browser = AsyncMock()
        playwright_instance.chromium.launch = AsyncMock(return_value=browser)
        page = AsyncMock()
        browser.new_context.return_value.new_page.return_value = page
        
        page.evaluate = AsyncMock(return_value=mock_album_data)
        
        result = await scraper.scrape_album_async(url, headless=True)
        
        assert result is not None
        assert result['name'] == "Whenever You Need Somebody"
        assert len(result['tracks']['items']) == 2
        assert result['tracks']['items'][0]['track']['name'] == "Never Gonna Give You Up"

@pytest.mark.asyncio
async def test_scrape_playlist_mock():
    scraper = PlaywrightScraper()
    url = "https://open.spotify.com/playlist/..."
    
    # Mocking two scroll steps
    # First step returns track 1, second step returns track 1 and track 2
    mock_rows_step1 = [
        {'row_num': 1, 'name': "Song 1", 'artists': ["Artist 1"], 'album': "Album 1", 'duration_str': "3:00"}
    ]
    mock_rows_step2 = [
        {'row_num': 1, 'name': "Song 1", 'artists': ["Artist 1"], 'album': "Album 1", 'duration_str': "3:00"},
        {'row_num': 2, 'name': "Song 2", 'artists': ["Artist 2"], 'album': "Album 2", 'duration_str': "4:00"}
    ]

    with patch("playwright.async_api.async_playwright") as mock_async_playwright:
        playwright_instance = mock_async_playwright.return_value.__aenter__.return_value
        browser = AsyncMock()
        playwright_instance.chromium.launch = AsyncMock(return_value=browser)
        page = AsyncMock()
        browser.new_context.return_value.new_page.return_value = page
        
        # Mock playlist name
        page.evaluate.side_effect = [
            "My Playlist", # playlist_name extraction
            mock_rows_step1, # first harvest
            mock_rows_step2, # second harvest
            mock_rows_step2, # third harvest (no new, will trigger break after max_no_new=10 steps, 
                             # but here we can just let it run or adjust mock)
        ] + [mock_rows_step2] * 20 

        result = await scraper.scrape_playlist_async(url, headless=True)
        
        assert result is not None
        assert result['name'] == "My Playlist"
        assert len(result['tracks']['items']) == 2
        assert result['tracks']['items'][0]['track']['name'] == "Song 1"
        assert result['tracks']['items'][1]['track']['name'] == "Song 2"

@pytest.mark.asyncio
async def test_duration_to_ms():
    scraper = PlaywrightScraper()
    assert scraper._duration_to_ms("3:32") == 212000
    assert scraper._duration_to_ms("1:03:32") == 3812000
    assert scraper._duration_to_ms("invalid") == 0

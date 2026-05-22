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

    mock_tracks = [
        {'name': "Song 1", 'artists': ["Artist 1"], 'duration_str': "3:00"},
        {'name': "Song 2", 'artists': ["Artist 2"], 'duration_str': "4:00"}
    ]

    with patch("playwright.async_api.async_playwright") as mock_async_playwright:
        playwright_instance = mock_async_playwright.return_value.__aenter__.return_value
        browser = AsyncMock()
        playwright_instance.chromium.launch = AsyncMock(return_value=browser)

        context = AsyncMock()
        browser.new_context = AsyncMock(return_value=context)

        page = AsyncMock()
        context.new_page = AsyncMock(return_value=page)

        page.goto = AsyncMock()
        page.is_visible = AsyncMock(return_value=False)
        page.wait_for_selector = AsyncMock()

        # Mock the evaluate calls:
        # 1. playlist name
        # 2. total track count (small so zoom phase is skipped)
        # 3. Phase 1 scroll
        # 4. Phase 1 count (= total, triggers early exit)
        # 5. parsed tracks
        evaluate_results = [
            "My Playlist",            # 1: name
            3,                        # 2: total estimate
            None,                     # 3: Phase 1 scroll
            3,                        # 4: Phase 1 count (>= total, breaks)
            mock_tracks,              # 5: parsed tracks
        ]

        page.evaluate = AsyncMock(side_effect=evaluate_results)

        result = await scraper.scrape_playlist_async(url, headless=True)

        assert result is not None
        assert result['name'] == "My Playlist"
        assert len(result['tracks']['items']) == 2
        assert result['tracks']['items'][0]['track']['name'] == "Song 1"
        assert result['tracks']['items'][1]['track']['name'] == "Song 2"
        browser.close.assert_called_once()

@pytest.mark.asyncio
async def test_duration_to_ms():
    scraper = PlaywrightScraper()
    assert scraper._duration_to_ms("3:32") == 212000
    assert scraper._duration_to_ms("1:03:32") == 3812000
    assert scraper._duration_to_ms("invalid") == 0

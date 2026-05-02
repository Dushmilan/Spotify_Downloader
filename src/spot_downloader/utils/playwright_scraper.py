import asyncio
import re
from typing import Dict, Any, List, Optional, Callable
from ..core.interfaces import Scraper

class PlaywrightScraper(Scraper):
    """
    Playwright-based implementation of the Spotify Scraper.
    """
    
    def __init__(self):
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def scrape_track(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        return asyncio.run(self.scrape_track_async(url, headless, log_callback))

    async def _handle_cookie_consent(self, page):
        selectors = [
            "#onetrust-accept-btn-handler",
            "button:has-text('Accept all')",
            "button:has-text('Accept')",
            "button[aria-label='Accept cookies']"
        ]
        for selector in selectors:
            try:
                if await page.is_visible(selector, timeout=3000):
                    await page.click(selector)
                    await asyncio.sleep(0.5)
                    return True
            except Exception:
                continue
        return False

    def _duration_to_ms(self, duration_str: str) -> int:
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:
                return (int(parts[0]) * 60 + int(parts[1])) * 1000
            elif len(parts) == 3:
                return (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
        except Exception:
            pass
        return 0

    async def scrape_track_async(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        def log(msg):
            if log_callback: log_callback(msg)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log("Error: Playwright is not installed.")
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(user_agent=self.user_agent, viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()

            try:
                log(f"Navigating to track: {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self._handle_cookie_consent(page)
                
                # Wait for main content
                await page.wait_for_selector('main', timeout=15000)
                await asyncio.sleep(2) # Stabilize

                # Extract metadata using evaluate
                metadata = await page.evaluate("""() => {
                    let name = "";
                    let h1 = document.querySelector('h1[data-testid="entityTitle"]');
                    if (h1) {
                        name = h1.innerText.trim();
                    } else {
                        name = document.title.split(' - ')[0];
                    }

                    let artist_links = Array.from(document.querySelectorAll('a[href*="/artist/"]'));
                    let artists = [...new Set(artist_links.map(a => a.innerText.trim()))].filter(a => a.length > 0);

                    let album_link = document.querySelector('a[href*="/album/"]');
                    let album = album_link ? album_link.innerText.trim() : "Unknown Album";

                    let duration_elem = document.querySelector('div[data-testid="track-duration"]');
                    let duration_str = duration_elem ? duration_elem.innerText.trim() : "";

                    return { name, artists, album, duration_str };
                }""")

                title = metadata['name']
                artists = metadata['artists']
                album = metadata['album']
                duration_ms = self._duration_to_ms(metadata['duration_str'])

                log(f"Scraped track: {title} by {', '.join(artists) if artists else 'Unknown Artist'}")

                return {
                    'name': title,
                    'artists': [{'name': a} for a in artists] if artists else [{'name': 'Unknown Artist'}],
                    'album': {'name': album},
                    'duration_ms': duration_ms
                }

            except Exception as e:
                log(f"Track scraping error (Playwright): {e}")
                return None
            finally:
                await browser.close()

    async def scrape_album_async(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        def log(msg):
            if log_callback: log_callback(msg)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log("Error: Playwright is not installed.")
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(user_agent=self.user_agent, viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()

            try:
                log(f"Navigating to album: {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self._handle_cookie_consent(page)
                
                await page.wait_for_selector('main', timeout=15000)
                await asyncio.sleep(2)

                album_data = await page.evaluate("""() => {
                    let name = "";
                    let h1 = document.querySelector('h1[data-testid="entityTitle"]');
                    if (h1) name = h1.innerText.trim();
                    else name = document.title.split(' - ')[0];

                    let rows = Array.from(document.querySelectorAll('[data-testid="tracklist-row"]'));
                    let tracks = rows.map(row => {
                        let title = "";
                        let a = row.querySelector('a[data-testid]');
                        if (a) title = a.getAttribute('title') || a.innerText.trim();
                        else {
                           let innerA = row.querySelector('a');
                           if (innerA) title = innerA.innerText.trim();
                        }

                        let artist_links = Array.from(row.querySelectorAll('a[href*="/artist/"]'));
                        let artists = artist_links.map(a => a.innerText.trim());

                        let duration_elem = row.querySelector('div[data-testid*="duration"]');
                        let duration_str = duration_elem ? duration_elem.innerText.trim() : "";

                        return { name: title, artists, duration_str };
                    }).filter(t => t.name.length > 0);

                    return { name, tracks };
                }""")

                album_name = album_data['name']
                tracks = []
                for t in album_data['tracks']:
                    tracks.append({
                        'track': {
                            'name': t['name'],
                            'artists': [{'name': a} for a in t['artists']] if t['artists'] else [{'name': 'Unknown Artist'}],
                            'duration_ms': self._duration_to_ms(t['duration_str']),
                            'album': {'name': album_name}
                        }
                    })

                log(f"Scraped album '{album_name}' with {len(tracks)} tracks.")

                return {
                    'name': album_name,
                    'tracks': {'items': tracks},
                }

            except Exception as e:
                log(f"Album scraping error (Playwright): {e}")
                return None
            finally:
                await browser.close()

    def scrape_album(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        return asyncio.run(self.scrape_album_async(url, headless, log_callback))

    async def _harvest_playlist_rows(self, page):
        return await page.evaluate("""() => {
            let rows = Array.from(document.querySelectorAll('[data-testid="tracklist-row"]'));
            return rows.map(row => {
                let row_num = row.getAttribute('aria-rowindex');
                
                let title = "";
                let a = row.querySelector('a[data-testid]');
                if (a) title = a.getAttribute('title') || a.innerText.trim();
                else {
                    let innerA = row.querySelector('a');
                    if (innerA) title = innerA.innerText.trim();
                }

                let artist_links = Array.from(row.querySelectorAll('a[href*="/artist/"]'));
                let artists = artist_links.map(a => a.innerText.trim());

                let album_link = row.querySelector('a[href*="/album/"]');
                let album = album_link ? (album_link.getAttribute('title') || album_link.innerText.trim()) : "Unknown Album";

                let duration_elem = row.querySelector('div[data-testid*="duration"]');
                let duration_str = duration_elem ? duration_elem.innerText.trim() : "";

                return { 
                    row_num: row_num ? parseInt(row_num) : null,
                    name: title, 
                    artists, 
                    album, 
                    duration_str 
                };
            }).filter(t => t.name.length > 0);
        }""")

    async def scrape_playlist_async(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        def log(msg):
            if log_callback: log_callback(msg)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log("Error: Playwright is not installed.")
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(user_agent=self.user_agent, viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()

            try:
                log(f"Navigating to playlist: {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self._handle_cookie_consent(page)
                
                await page.wait_for_selector('main', timeout=15000)
                await asyncio.sleep(2)

                playlist_name = await page.evaluate("""() => {
                    let h1 = document.querySelector('h1[data-testid="entityTitle"]');
                    return h1 ? h1.innerText.trim() : document.title.split(' - ')[0];
                }""")

                log(f"Collecting tracks from '{playlist_name}'...")

                tracks_by_rownum = {}
                max_no_new = 10
                no_new_count = 0
                
                for i in range(100): # Max 100 scroll steps
                    rows = await self._harvest_playlist_rows(page)
                    new_found = False
                    for r in rows:
                        key = r['row_num'] if r['row_num'] is not None else (100000 + len(tracks_by_rownum))
                        if key not in tracks_by_rownum:
                            tracks_by_rownum[key] = r
                            new_found = True
                    
                    if new_found:
                        no_new_count = 0
                        log(f"Collected {len(tracks_by_rownum)} tracks...")
                    else:
                        no_new_count += 1
                        if no_new_count >= max_no_new:
                            break

                    await page.keyboard.press("PageDown")
                    await asyncio.sleep(0.5)

                all_tracks = []
                # Sort by row number and clean up
                for key in sorted(tracks_by_rownum.keys()):
                    t = tracks_by_rownum[key]
                    all_tracks.append({
                        'track': {
                            'name': t['name'],
                            'artists': [{'name': a} for a in t['artists']] if t['artists'] else [{'name': 'Unknown Artist'}],
                            'duration_ms': self._duration_to_ms(t['duration_str']),
                            'album': {'name': t['album']}
                        }
                    })

                log(f"Successfully scraped {len(all_tracks)} tracks from '{playlist_name}'.")

                return {
                    'name': playlist_name,
                    'tracks': {'items': all_tracks},
                }

            except Exception as e:
                log(f"Playlist scraping error (Playwright): {e}")
                return None
            finally:
                await browser.close()

    def scrape_playlist(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        return asyncio.run(self.scrape_playlist_async(url, headless, log_callback))

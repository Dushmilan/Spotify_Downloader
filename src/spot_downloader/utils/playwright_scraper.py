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
                
                await page.wait_for_selector('main', timeout=15000)
                await asyncio.sleep(2)

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

    async def scrape_playlist_async(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        def log(msg):
            if log_callback: log_callback(msg)

        # 1. Extract Playlist ID from URL immediately
        playlist_id_match = re.search(r"/playlist/([^/?#]+)", url)
        if not playlist_id_match:
            log("Error: Invalid Spotify playlist URL.")
            return None
        playlist_id = playlist_id_match.group(1)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log("Error: Playwright is not installed.")
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()

            auth_token = None
            api_headers = {}
            captured_event = asyncio.Event()

            async def handle_request(request):
                nonlocal auth_token, api_headers
                try:
                    r_url = request.url
                    # Capture headers from ANY Spotify API call
                    if "api.spotify.com" in r_url and "authorization" in request.headers:
                        headers = request.headers
                        auth = headers['authorization']
                        if auth.startswith('Bearer '):
                            auth_token = auth
                            # Replicate critical headers to look authentic and avoid 429/403
                            api_headers = {
                                'Authorization': auth,
                                'Accept': headers.get('accept', '*/*'),
                                'App-Platform': headers.get('app-platform', 'WebPlayer'),
                                'Spotify-App-Version': headers.get('spotify-app-version', ''),
                                'Client-Token': headers.get('client-token', '')
                            }
                            captured_event.set()
                except:
                    pass

            page.on("request", handle_request)

            try:
                log(f"Loading playlist page to capture access token...")
                await page.goto(url, wait_until="commit", timeout=60000)
                
                try:
                    await asyncio.wait_for(captured_event.wait(), timeout=20.0)
                except asyncio.TimeoutError:
                    log("Waiting for auth token... (scrolling to trigger)")
                    await page.mouse.wheel(0, 2000)
                    try:
                        await asyncio.wait_for(captured_event.wait(), timeout=15.0)
                    except asyncio.TimeoutError:
                        log("Error: API token interception timed out.")
                        return None

                log("Access token captured. Retrieving playlist metadata...")
                
                # Fetch playlist metadata via API for the real name
                meta_url = f"https://api.spotify.com/v1/playlists/{playlist_id}?fields=name"
                playlist_name = "Playlist"
                
                meta_data = await page.evaluate(f"""async (args) => {{
                    try {{
                        const res = await fetch(args.url, {{ headers: args.headers }});
                        return res.ok ? await res.json() : {{ error: res.status }};
                    }} catch (e) {{
                        return {{ error: e.message }};
                    }}
                }}""", {"url": meta_url, "headers": api_headers})
                
                if not meta_data.get('error'):
                    playlist_name = meta_data.get('name', playlist_name)

                all_tracks = []
                next_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?offset=0&limit=50&market=from_token"

                while next_url:
                    max_retries = 3
                    data = None
                    
                    for attempt in range(max_retries):
                        data = await page.evaluate(f"""async (args) => {{
                            try {{
                                const res = await fetch(args.url, {{ headers: args.headers }});
                                if (res.status === 429) return {{ error: 429, retryAfter: res.headers.get('Retry-After') }};
                                if (!res.ok) return {{ error: res.status }};
                                return await res.json();
                            }} catch (e) {{
                                return {{ error: e.message }};
                            }}
                        }}""", {"url": next_url, "headers": api_headers})

                        if data.get('error') == 429:
                            wait_time = int(data.get('retryAfter') or (attempt + 1) * 5)
                            log(f"Rate limited (429). Waiting {wait_time}s before retry...")
                            await asyncio.sleep(wait_time)
                            continue
                        break

                    if "error" in data:
                        log(f"API Fetch Error: {data['error']}. Stopping.")
                        break

                    items = data.get('items', [])
                    all_tracks.extend(items)
                    next_url = data.get('next')
                    
                    total = data.get('total', '???')
                    log(f"Fetched {len(all_tracks)} / {total} tracks...")
                    
                    if not items or not next_url: break
                    await asyncio.sleep(0.5)

                log(f"Successfully scraped {len(all_tracks)} tracks from '{playlist_name}'.")
                
                return {
                    'name': playlist_name,
                    'tracks': {'items': all_tracks},
                }

            except Exception as e:
                log(f"Playlist scraping error: {e}")
                return None
            finally:
                await browser.close()

    def scrape_playlist(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        return asyncio.run(self.scrape_playlist_async(url, headless, log_callback))

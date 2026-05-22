import asyncio
import re
from typing import Dict, Any, List, Optional, Callable

class PlaywrightScraper:
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
                await asyncio.sleep(1)

                # Wait for track title to render (may take several seconds)
                try:
                    await page.wait_for_selector('span[data-testid="entityTitle"]', timeout=10000)
                except Exception:
                    pass

                metadata = await page.evaluate("""() => {
                    let name = "";
                    let span = document.querySelector('span[data-testid="entityTitle"]');
                    let h1 = document.querySelector('h1[data-testid="entityTitle"]');
                    if (span) {
                        name = span.innerText.trim();
                    } else if (h1) {
                        name = h1.innerText.trim();
                    } else {
                        let altH1 = document.querySelector('h1.encore-text-headline-large');
                        if (altH1) {
                            name = altH1.innerText.trim();
                        } else {
                            name = document.title.split(' - ')[0];
                        }
                    }

                    let artistLinks = document.querySelectorAll('a[data-testid="creator-link"]');
                    let seen = new Set();
                    let artists = [];
                    for (let a of artistLinks) {
                        let text = a.innerText.trim();
                        if (text && text.length > 0 && text.length < 50 && !seen.has(text)) {
                            seen.add(text);
                            artists.push(text);
                        }
                    }

                    let album_link = document.querySelector('a[href*="/album/"]');
                    let album = album_link ? album_link.innerText.trim() : "Unknown Album";

                    let duration_elem = document.querySelector('div[data-testid="track-duration"], span[data-testid="track-duration"]');
                    let duration_str = "";
                    if (duration_elem) {
                        duration_str = duration_elem.innerText.trim();
                    } else {
                        let titleSpan = document.querySelector('span[data-testid="entityTitle"]');
                        if (titleSpan) {
                            let container = titleSpan.parentElement;
                            for (let i = 0; i < 4; i++) {
                                if (!container) break;
                                let timeSpans = container.querySelectorAll('span');
                                for (let s of timeSpans) {
                                    let text = (s.innerText || '').trim();
                                    if (/^\d+:\d+$/.test(text)) {
                                        duration_str = text;
                                        break;
                                    }
                                }
                                if (duration_str) break;
                                container = container.parentElement;
                            }
                        }
                    }

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
                await asyncio.sleep(1)

                # Wait for album title to render
                try:
                    await page.wait_for_selector('span[data-testid="entityTitle"]', timeout=10000)
                except Exception:
                    pass

                album_data = await page.evaluate("""() => {
                    let name = "";
                    let span = document.querySelector('span[data-testid="entityTitle"]');
                    let h1 = document.querySelector('h1[data-testid="entityTitle"]');
                    if (span) {
                        name = span.innerText.trim();
                    } else if (h1) {
                        name = h1.innerText.trim();
                    } else {
                        let altH1 = document.querySelector('h1.encore-text-headline-large');
                        if (altH1) {
                            name = altH1.innerText.trim();
                        } else {
                            name = document.title.split(' - ')[0];
                        }
                    }

                    let rows = Array.from(document.querySelectorAll('[data-testid="tracklist-row"]'));
                    let tracks = rows.map(row => {
                        let title = "";
                        let a = row.querySelector('a[data-testid]');
                        if (a) title = a.getAttribute('title') || a.innerText.trim();
                        else {
                           let innerA = row.querySelector('a');
                           if (innerA) title = innerA.innerText.trim();
                        }

                        let artistLinks = row.querySelectorAll('a[href*="/artist/"]');
                        let seen = new Set();
                        let artists = [];
                        for (let al of artistLinks) {
                            let text = al.innerText.trim();
                            if (text && text.length > 0 && text.length < 50 && !seen.has(text)) {
                                seen.add(text);
                                artists.push(text);
                            }
                        }

                        let duration_elem = row.querySelector('div[data-testid*="duration"]');
                        let duration_str = "";
                        if (duration_elem) {
                            duration_str = duration_elem.innerText.trim();
                        } else {
                            let timeEls = row.querySelectorAll('span, div');
                            for (let el of timeEls) {
                                let text = (el.innerText || '').trim();
                                if (/^\d+:\d+$/.test(text)) {
                                    duration_str = text;
                                    break;
                                }
                            }
                        }

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

    async def _scrape_playlist_dom(self, page, log: Callable[[str], None]) -> Optional[List[Dict[str, Any]]]:
        total_estimate = await page.evaluate("""() => {
            let els = document.querySelectorAll('span, div');
            for (let el of els) {
                let text = (el.innerText || '').trim();
                let m = text.match(/^(\\d+)\\s*songs?$/i);
                if (m) return parseInt(m[1], 10);
            }
            return 0;
        }""")

        if total_estimate:
            log(f"Playlist has {total_estimate} tracks.")

        prev_count = 0

        # Phase 1: Normal scroll to load initial batch
        for _ in range(20):
            await page.evaluate("""() => {
                let rows = document.querySelectorAll('[data-testid="tracklist-row"]');
                if (rows.length === 0) return;
                let last = rows[rows.length - 1];
                last.scrollIntoView({block: 'end'});
                window.scrollBy(0, 400);
            }""")
            await asyncio.sleep(0.5)
            count = await page.evaluate(
                "document.querySelectorAll('[data-testid=\"tracklist-row\"]').length"
            )
            if count > prev_count:
                prev_count = count
                if total_estimate:
                    log(f"Loaded {count} / {total_estimate} tracks...")
                else:
                    log(f"Loaded {count} tracks...")
            else:
                break
            if total_estimate and count >= total_estimate:
                break

        # Phase 2: Zoom out to force virtual scroller to render more rows
        if total_estimate and prev_count < total_estimate:
            zoom_level = await page.evaluate(f"""() => {{
                let viewport = document.querySelector('.main-view-container__scroll-node');
                let clientH = viewport ? viewport.clientHeight : 900;
                let rowH = 64;
                let targetZoom = clientH / ({total_estimate} * rowH * 1.2);
                targetZoom = Math.min(0.5, Math.max(0.008, targetZoom));
                return targetZoom;
            }}""")
            log(f"Zooming to {zoom_level:.3f}x to fit ~{total_estimate} tracks...")
            await page.evaluate(f"document.body.style.zoom = '{zoom_level}'")
            await asyncio.sleep(2)

            zoom_count = await page.evaluate(
                "document.querySelectorAll('[data-testid=\"tracklist-row\"]').length"
            )
            if zoom_count > prev_count:
                prev_count = zoom_count
                log(f"Rendered {zoom_count} tracks after zoom.")

            # Phase 3: Continue scrolling with sentinel + scroll container
            for _ in range(30):
                await page.evaluate("""() => {
                    let sentinel = document.querySelector('div[data-testid="bottom-sentinel"]');
                    if (sentinel) sentinel.scrollIntoView({block: 'nearest'});
                    let scrollNode = document.querySelector('.main-view-container__scroll-node');
                    if (scrollNode && scrollNode.firstElementChild) {
                        scrollNode.firstElementChild.scrollTop = 999999;
                    }
                }""")
                await asyncio.sleep(0.5)
                count = await page.evaluate(
                    "document.querySelectorAll('[data-testid=\"tracklist-row\"]').length"
                )
                if count > prev_count:
                    prev_count = count
                    if total_estimate:
                        log(f"Loaded {count} / {total_estimate} tracks...")
                    else:
                        log(f"Loaded {count} tracks...")
                if total_estimate and count >= total_estimate:
                    log(f"All {total_estimate} tracks loaded.")
                    break

        # Phase 4: Parse all track rows (still zoomed out if we zoomed)
        raw_tracks = await page.evaluate("""() => {
            let rows = document.querySelectorAll('[data-testid="tracklist-row"]');
            let tracks = [];
            rows.forEach(row => {
                let title = "";
                let trackLink = row.querySelector('a[data-testid="internal-track-link"]');
                if (trackLink) {
                    title = trackLink.getAttribute('title') || trackLink.innerText.trim();
                }
                if (!title) {
                    let otherA = row.querySelector('a');
                    if (otherA) title = otherA.innerText.trim();
                }
                if (!title) return;

                let artistLinks = row.querySelectorAll('a[href*="/artist/"]');
                let seenArtists = new Set();
                let artists = [];
                for (let a of artistLinks) {
                    let text = a.innerText.trim();
                    if (text && text.length > 0 && text.length < 50 && !seenArtists.has(text)) {
                        seenArtists.add(text);
                        artists.push(text);
                    }
                }

                let durationEl = row.querySelector('div[data-testid*="duration"]');
                let durationStr = "";
                if (durationEl) {
                    durationStr = durationEl.innerText.trim();
                } else {
                    let timeEls = row.querySelectorAll('span, div');
                    for (let el of timeEls) {
                        let text = (el.innerText || '').trim();
                        if (/^\\d+:\\d+$/.test(text)) {
                            durationStr = text;
                            break;
                        }
                    }
                }

                tracks.push({ name: title, artists, duration_str: durationStr });
            });
            return tracks;
        }""")

        if not raw_tracks:
            log("No tracks found via DOM.")
            return None

        if total_estimate and len(raw_tracks) > total_estimate:
            log(f"Trimming {len(raw_tracks) - total_estimate} buffer rows (DOM has {len(raw_tracks)}, total is {total_estimate}).")
            raw_tracks = raw_tracks[:total_estimate]

        log(f"Parsed {len(raw_tracks)} tracks.")
        return raw_tracks

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
                log(f"Loading playlist page...")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await self._handle_cookie_consent(page)
                await page.wait_for_selector('main', timeout=20000)
                await asyncio.sleep(1)

                try:
                    await page.wait_for_selector('span[data-testid="entityTitle"]', timeout=10000)
                except Exception:
                    pass

                playlist_name = await page.evaluate("""() => {
                    let span = document.querySelector('span[data-testid="entityTitle"]');
                    if (span) return span.innerText.trim();
                    let h1 = document.querySelector('h1');
                    if (h1) return h1.innerText.trim();
                    return document.title.split(' - ')[0] || 'Playlist';
                }""")
                log(f"Playlist: {playlist_name}")

                tracks = await self._scrape_playlist_dom(page, log)

                if not tracks:
                    log("No tracks found.")
                    return None

                log(f"Scraped {len(tracks)} tracks from '{playlist_name}'.")
                return {
                    'name': playlist_name,
                    'tracks': {
                        'items': [{
                            'track': {
                                'name': t['name'],
                                'artists': [{'name': a} for a in t['artists']] if t['artists'] else [{'name': 'Unknown Artist'}],
                                'duration_ms': self._duration_to_ms(t['duration_str']),
                                'album': {'name': playlist_name}
                            }
                        } for t in tracks]
                    }
                }

            except Exception as e:
                log(f"Playlist scraping error: {e}")
                return None
            finally:
                await browser.close()

    def scrape_playlist(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        return asyncio.run(self.scrape_playlist_async(url, headless, log_callback))

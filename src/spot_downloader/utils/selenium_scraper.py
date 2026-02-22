import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def setup_driver(headless=True):
    chrome_options = Options()
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheet": 2,
        "profile.managed_default_content_settings.fonts": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    try:
        return webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return None


def handle_cookie_consent(driver):
    for by, selector in [
        (By.ID, "onetrust-accept-btn-handler"),
        (By.XPATH, "//button[contains(text(), 'Accept all')]"),
        (By.XPATH, "//button[contains(text(), 'Accept')]"),
        (By.XPATH, "//button[@aria-label='Accept cookies']"),
    ]:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, selector)))
            btn.click()
            time.sleep(0.5)
            return True
        except TimeoutException:
            continue
    return False


def duration_to_ms(duration_str):
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:
            return (int(parts[0]) * 60 + int(parts[1])) * 1000
        elif len(parts) == 3:
            return (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
    except Exception:
        pass
    return 0


def get_playlist_name(driver, log):
    try:
        name = driver.execute_script("""
            let main = document.querySelector('main');
            if (!main) return null;
            let h1 = main.querySelector('h1[data-testid="entityTitle"]');
            if (h1) return h1.innerText.trim();
            let anyH1 = main.querySelector('h1');
            if (anyH1) return anyH1.innerText.trim();
            return null;
        """)
        if name and name not in {'Your Library', 'Home', 'Search', 'Browse', ''}:
            log(f"Found playlist name: {name}")
            return name
    except Exception:
        pass
    try:
        title = driver.title
        for sep in [' - playlist', ' | ', ' – ']:
            if sep in title:
                name = title.split(sep)[0].strip()
                if name:
                    log(f"Found playlist name from page title: {name}")
                    return name
    except Exception:
        pass
    return "Unknown Playlist"


def find_scroll_container(driver):
    """
    Find the actual scrollable div — the unnamed DIV with overflowY=scroll
    identified in the diagnostic. We find it by walking up from the playlist
    container and finding the first ancestor with overflowY scroll/auto.
    """
    try:
        return driver.execute_script("""
            let container = document.querySelector('.eaxF79s4oV8I2CPQ');
            if (!container) return null;
            let el = container.parentElement;
            while (el) {
                let style = window.getComputedStyle(el);
                if (style.overflowY === 'scroll' || style.overflowY === 'auto') {
                    return el;
                }
                el = el.parentElement;
            }
            return null;
        """)
    except Exception:
        return None


def get_row_number(driver, row):
    """Get row number from aria-rowindex on the row or its nearest ancestor."""
    try:
        idx = row.get_attribute('aria-rowindex')
        if idx and str(idx).isdigit():
            return int(idx)
    except Exception:
        pass
    try:
        result = driver.execute_script("""
            let el = arguments[0];
            for (let i = 0; i < 5; i++) {
                if (!el) break;
                let idx = el.getAttribute('aria-rowindex');
                if (idx) return parseInt(idx);
                el = el.parentElement;
            }
            return null;
        """, row)
        if result:
            return int(result)
    except Exception:
        pass
    return None


def is_recommended_visible(driver):
    try:
        return bool(driver.execute_script("""
            let container = document.querySelector('.eaxF79s4oV8I2CPQ');
            if (!container) return false;
            let walker = document.createTreeWalker(
                container, NodeFilter.SHOW_TEXT, null, false
            );
            let node;
            while (node = walker.nextNode()) {
                if (node.nodeValue.trim() === 'Recommended') return true;
            }
            return false;
        """))
    except Exception:
        return False


def harvest_rows(driver, tracks_by_rownum, seen_title_artists):
    """
    Harvest currently rendered rows, keyed by row number.
    Falls back to title+artist dedup if row number unavailable.
    Returns number of new tracks added.
    """
    added = 0
    try:
        rows = driver.find_elements(
            By.CSS_SELECTOR, '.eaxF79s4oV8I2CPQ [data-testid="tracklist-row"]'
        )
        for row in rows:
            try:
                row_num = get_row_number(driver, row)

                if row_num is not None and row_num in tracks_by_rownum:
                    continue

                # Title
                title = ""
                try:
                    a = row.find_element(By.CSS_SELECTOR, 'a[data-testid]')
                    title = a.get_attribute('title') or a.text.strip()
                except Exception:
                    try:
                        title = row.find_element(By.TAG_NAME, 'a').text.strip()
                    except Exception:
                        pass
                if not title:
                    continue

                # Artist(s)
                artist = "Unknown Artist"
                try:
                    artist_elems = row.find_elements(
                        By.CSS_SELECTOR, 'span a[href*="/artist/"]'
                    )
                    artists = [e.text.strip() for e in artist_elems if e.text.strip()]
                    artist = ", ".join(artists[:3]) if artists else "Unknown Artist"
                except Exception:
                    pass

                # Fallback dedup
                if row_num is None:
                    key = f"{title}|||{artist}"
                    if key in seen_title_artists:
                        continue
                    seen_title_artists.add(key)

                # Album
                album = "Unknown Album"
                try:
                    album_elem = row.find_element(By.CSS_SELECTOR, 'a[href*="/album/"]')
                    album = album_elem.get_attribute('title') or album_elem.text.strip()
                except Exception:
                    pass

                # Duration
                duration_ms = 0
                try:
                    dur_elem = row.find_element(
                        By.CSS_SELECTOR, 'div[data-testid*="duration"]'
                    )
                    duration_ms = duration_to_ms(dur_elem.text.strip())
                except Exception:
                    m = re.search(r'(\d+:\d+)', row.text)
                    if m:
                        duration_ms = duration_to_ms(m.group(1))

                track = {
                    'track': {
                        'name': title,
                        'artists': [{'name': artist}],
                        'album': {'name': album},
                        'duration_ms': duration_ms,
                    }
                }

                key = row_num if row_num is not None else (100000 + len(tracks_by_rownum))
                tracks_by_rownum[key] = track
                added += 1

            except Exception:
                continue
    except Exception:
        pass
    return added


def scrape_playlist(playlist_url, headless=True, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    driver = setup_driver(headless=headless)
    if not driver:
        log("Failed to initialize Chrome driver.")
        return None

    try:
        log(f"Navigating to {playlist_url}...")
        driver.get(playlist_url)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
        except TimeoutException:
            log("Timed out waiting for page to load.")
            return None

        handle_cookie_consent(driver)

        log("Waiting for playlist container to load...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.eaxF79s4oV8I2CPQ'))
            )
        except TimeoutException:
            log("Warning: Playlist container not found, proceeding anyway...")

        playlist_name = get_playlist_name(driver, log)

        # Find the scroll container
        scroll_container = find_scroll_container(driver)
        if scroll_container:
            sh = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
            ch = driver.execute_script("return arguments[0].clientHeight", scroll_container)
            log(f"Scroll container found (scrollHeight={sh}, clientHeight={ch}).")
        else:
            log("Warning: Scroll container not found.")

        # Focus the scroll container so it receives keyboard events
        if scroll_container:
            try:
                # Make it focusable and focus it
                driver.execute_script("""
                    arguments[0].setAttribute('tabindex', '0');
                    arguments[0].focus();
                """, scroll_container)
                log("Focused scroll container.")
            except Exception:
                pass
        else:
            try:
                driver.find_element(By.CSS_SELECTOR, '.eaxF79s4oV8I2CPQ').click()
            except Exception:
                pass

        log("Scrolling with PAGE_DOWN and collecting tracks...")

        tracks_by_rownum = {}
        seen_title_artists = set()
        recommended_cutoff = None

        MAX_NO_NEW = 10
        MAX_ITERATIONS = 600
        PAGE_DOWNS_PER_STEP = 3
        SLEEP = 0.5
        no_new_count = 0

        for iteration in range(MAX_ITERATIONS):

            # Detect recommended section
            if recommended_cutoff is None and is_recommended_visible(driver):
                real_keys = [k for k in tracks_by_rownum if k < 100000]
                recommended_cutoff = max(real_keys) if real_keys else 0
                log(f"Recommended section visible — cutoff at row #{recommended_cutoff}.")

            new_count = harvest_rows(driver, tracks_by_rownum, seen_title_artists)

            if new_count > 0:
                no_new_count = 0
                real_count = len([k for k in tracks_by_rownum if k < 100000])
                log(f"Collected {real_count} tracks (iteration #{iteration + 1})...")
            else:
                no_new_count += 1

            if no_new_count >= MAX_NO_NEW:
                log(f"Done after {MAX_NO_NEW} idle iterations.")
                break

            # Send PAGE_DOWN directly to the scroll container element
            if scroll_container:
                try:
                    for _ in range(PAGE_DOWNS_PER_STEP):
                        scroll_container.send_keys(Keys.PAGE_DOWN)
                except Exception:
                    # Re-find and re-focus if stale
                    try:
                        scroll_container = find_scroll_container(driver)
                        if scroll_container:
                            driver.execute_script(
                                "arguments[0].setAttribute('tabindex','0');"
                                "arguments[0].focus();",
                                scroll_container
                            )
                            for _ in range(PAGE_DOWNS_PER_STEP):
                                scroll_container.send_keys(Keys.PAGE_DOWN)
                    except Exception:
                        pass
            else:
                try:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                except Exception:
                    pass

            time.sleep(SLEEP)

        # Build final ordered list
        if recommended_cutoff is not None:
            valid_keys = sorted(k for k in tracks_by_rownum if k <= recommended_cutoff)
            log(f"Keeping {len(valid_keys)} tracks (cutoff at row #{recommended_cutoff}).")
        else:
            valid_keys = sorted(tracks_by_rownum.keys())

        all_tracks = [tracks_by_rownum[k] for k in valid_keys]
        log(f"Successfully scraped {len(all_tracks)} tracks.")

        return {
            'name': playlist_name,
            'tracks': {'items': all_tracks},
        }

    except Exception as e:
        log(f"Unhandled error: {e}")
        return None
    finally:
        driver.quit()
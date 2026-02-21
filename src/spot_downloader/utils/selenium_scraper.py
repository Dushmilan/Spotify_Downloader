import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

def setup_driver(headless=True):
    """
    Initialize Chrome WebDriver with options
    """
    chrome_options = Options()

    prefs = {
        "profile.managed_default_content_settings.images": 2, # Block images
        "profile.managed_default_content_settings.stylesheet": 2, # Block CSS
        "profile.managed_default_content_settings.fonts": 2 # Block fonts
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    if headless:
        chrome_options.add_argument('--headless=new')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return None

def handle_cookie_consent(driver):
    """
    Handle cookie consent pop-up if it appears
    """
    try:
        cookie_selectors = [
            (By.ID, "onetrust-accept-btn-handler"),
            (By.XPATH, "//button[contains(text(), 'Accept')]"),
            (By.XPATH, "//button[contains(text(), 'Accept all')]"),
            (By.XPATH, "//button[@aria-label='Accept cookies']"),
            (By.XPATH, "//button[contains(@class, 'onetrust-close-btn-handler')]"),
        ]
        
        for by, selector in cookie_selectors:
            try:
                cookie_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((by, selector))
                )
                cookie_button.click()
                time.sleep(1)
                return True
            except TimeoutException:
                continue
    except:
        pass
    return False

def find_scrollable_container(driver):
    """
    Find the correct scrollable container for the playlist
    Prioritizes the container with class eaxF79s4oV8I2CPQ
    """
    # First, try to find a scrollable parent of the specific container
    try:
        specific_container = driver.find_element(By.CSS_SELECTOR, '.eaxF79s4oV8I2CPQ')
        # Find scrollable parent
        scrollable_parent = driver.execute_script("""
            let element = arguments[0];
            while (element) {
                element = element.parentElement;
                if (element && element.scrollHeight > element.clientHeight + 100) {
                    return element;
                }
            }
            return null;
        """, specific_container)
        if scrollable_parent:
            return scrollable_parent
    except:
        pass
    
    selectors = [
        'div[data-overlayscrollbars-viewport]',
        'div.main-view-container__scroll-node',
        'div[class*="main-view-container"]',
        'div.os-viewport',
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                scroll_height = driver.execute_script("return arguments[0].scrollHeight;", element)
                client_height = driver.execute_script("return arguments[0].clientHeight;", element)
                if scroll_height > client_height + 100:
                    return element
        except:
            continue
    return None

def duration_to_ms(duration_str):
    """
    Convert duration string (M:SS or H:MM:SS) to milliseconds
    """
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:
            return (int(parts[0]) * 60 + int(parts[1])) * 1000
        elif len(parts) == 3:
            return (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
    except:
        pass
    return 0

def scrape_playlist(playlist_url, headless=True, log_callback=None):
    """
    Scrape Spotify playlist tracks using Selenium
    """
    driver = setup_driver(headless=headless)
    if not driver:
        if log_callback: log_callback("Failed to initialize Chrome driver.")
        return None

    try:
        if log_callback: log_callback(f"Navigating to {playlist_url}...")
        driver.get(playlist_url)
        
        # Wait for initial load
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        except TimeoutException:
            if log_callback: log_callback("Timed out waiting for page to load.")
            return None

        handle_cookie_consent(driver)
        
        # Wait for the specific container with class eaxF79s4oV8I2CPQ
        if log_callback: log_callback("Waiting for playlist container to load...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.eaxF79s4oV8I2CPQ'))
            )
            if log_callback: log_callback("Found playlist container (.eaxF79s4oV8I2CPQ)")
        except TimeoutException:
            if log_callback: log_callback("Warning: Container .eaxF79s4oV8I2CPQ not found, proceeding anyway...")
        
        # Get playlist name - be more specific to avoid sidebar elements
        playlist_name = "Unknown Playlist"
        
        # First, try the most specific selector for playlist title
        try:
            # Spotify's playlist title is in h1 with data-testid="entityTitle" inside the main content area
            name_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-testid="entityTitle"]'))
            )
            text = name_elem.text.strip()
            if text and text not in ['Your Library', 'Home', 'Search', 'Browse']:
                playlist_name = text
                if log_callback: log_callback(f"Found playlist name: {playlist_name}")
        except:
            # Fallback: look for h1 in the main content area specifically
            try:
                # Find h1 elements within the main view container (not sidebar)
                main_content = driver.find_element(By.CSS_SELECTOR, 'div.main-view-container, div[data-testid="playlist-page"], main')
                h1_elements = main_content.find_elements(By.TAG_NAME, 'h1')
                for h1 in h1_elements:
                    text = h1.text.strip()
                    # Skip common sidebar/library headers
                    if text and text not in ['Your Library', 'Home', 'Search', 'Browse', '']:
                        playlist_name = text
                        if log_callback: log_callback(f"Found playlist name: {playlist_name}")
                        break
            except:
                if log_callback: log_callback("Could not find playlist name, using default")

        scrollable_element = find_scrollable_container(driver)
        
        all_tracks = []
        seen_ids = set()
        last_track_count = 0
        no_change_count = 0
        max_no_change = 3
        scroll_count = 0
        max_scrolls = 100
        recommended_y_position = None
        
        if log_callback: log_callback("Starting to scrape tracks...")

        while scroll_count < max_scrolls:
            # Check for "Recommended" section and get its position
            try:
                recommended_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Recommended')]")
                if recommended_elements:
                    for elem in recommended_elements:
                        try:
                            # Get the absolute Y position of the Recommended element
                            elem_y = driver.execute_script(
                                "return arguments[0].getBoundingClientRect().top + window.pageYOffset;", 
                                elem
                            )
                            if recommended_y_position is None or elem_y < recommended_y_position:
                                recommended_y_position = elem_y
                                if log_callback: log_callback(f"Found 'Recommended' section at position: {recommended_y_position}")
                        except:
                            pass
            except:
                pass
            
            try:
                # Scrape tracks only from the specific container
                track_elements = driver.find_elements(By.CSS_SELECTOR, '.eaxF79s4oV8I2CPQ [data-testid="tracklist-row"]')
                
                for track_element in track_elements:
                    # Check if track is above the "Recommended" section
                    if recommended_y_position is not None:
                        track_y = driver.execute_script(
                            "return arguments[0].getBoundingClientRect().top + window.pageYOffset;", 
                            track_element
                        )
                        if track_y >= recommended_y_position:
                            # Track is at or below "Recommended" section, skip it
                            continue
                    
                    try:
                        # Use a combination of title and artist as ID
                        title = ""
                        try:
                            title_elem = track_element.find_element(By.CSS_SELECTOR, 'a[data-testid]')
                            title = title_elem.get_attribute('title') or title_elem.text.strip()
                        except:
                            title_elem = track_element.find_element(By.TAG_NAME, 'a')
                            title = title_elem.text.strip()
                        
                        artist = "Unknown Artist"
                        try:
                            artist_elems = track_element.find_elements(By.CSS_SELECTOR, 'span a[href*="/artist/"]')
                            artists = [elem.text.strip() for elem in artist_elems if elem.text.strip()]
                            artist = ", ".join(artists[:3]) if artists else "Unknown Artist"
                        except:
                            pass
                            
                        track_id = f"{title}-{artist}"
                        if not title or track_id in seen_ids:
                            continue
                        
                        seen_ids.add(track_id)
                        
                        album = "Unknown Album"
                        try:
                            album_elem = track_element.find_element(By.CSS_SELECTOR, 'a[href*="/album/"]')
                            album = album_elem.get_attribute('title') or album_elem.text.strip()
                        except:
                            pass
                        
                        duration_ms = 0
                        try:
                            duration_elem = track_element.find_element(By.CSS_SELECTOR, 'div[data-testid*="duration"]')
                            duration_ms = duration_to_ms(duration_elem.text.strip())
                        except:
                            text = track_element.text
                            time_match = re.search(r'(\d+:\d+)', text)
                            if time_match:
                                duration_ms = duration_to_ms(time_match.group(1))
                        
                        all_tracks.append({
                            'track': {
                                'name': title,
                                'artists': [{'name': artist}],
                                'album': {'name': album},
                                'duration_ms': duration_ms
                            }
                        })
                    except:
                        continue
            except:
                pass
            
            current_track_count = len(all_tracks)
            
            # Perform scroll
            if scrollable_element:
                current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_element)
                scroll_height = driver.execute_script("return arguments[0].scrollHeight;", scrollable_element)
                client_height = driver.execute_script("return arguments[0].clientHeight;", scrollable_element)
                
                new_scroll_position = min(current_scroll + 1200, scroll_height - client_height)
                driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable_element, new_scroll_position)
                
                time.sleep(1.0)
                actual_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_element)
                at_bottom = (actual_scroll + client_height) >= (scroll_height - 100)
            else:
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(driver)
                for _ in range(5):
                    actions.send_keys(Keys.PAGE_DOWN).perform()
                    time.sleep(0.1)
                time.sleep(1.0)
                current_scroll = driver.execute_script("return window.pageYOffset;")
                scroll_height = driver.execute_script("return document.body.scrollHeight;")
                window_height = driver.execute_script("return window.innerHeight;")
                at_bottom = (current_scroll + window_height) >= (scroll_height - 100)

            # Check if we've reached the "Recommended" section - stop scrolling if found
            if recommended_y_position is not None:
                if log_callback: log_callback("Reached 'Recommended' section, stopping scrape.")
                break
            
            if current_track_count == last_track_count:
                no_change_count += 1
                if at_bottom and no_change_count >= max_no_change:
                    break
            else:
                no_change_count = 0
                scroll_count += 1
                if log_callback: log_callback(f"Scraped {current_track_count} tracks...")
            
            last_track_count = current_track_count

        return {
            'name': playlist_name,
            'tracks': {
                'items': all_tracks
            }
        }

    except Exception as e:
        if log_callback: log_callback(f"Error scraping playlist: {e}")
        return None
    finally:
        driver.quit()

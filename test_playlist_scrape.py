import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver(headless=True):
    """
    Initialize Chrome WebDriver with options
    
    Args:
        headless (bool): Run browser in headless mode if True
    
    Returns:
        webdriver: Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless=new')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    return driver

def handle_cookie_consent(driver, wait):
    """
    Handle cookie consent pop-up if it appears
    
    Args:
        driver: WebDriver instance
        wait: WebDriverWait instance
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
                print("✓ Cookie consent handled")
                time.sleep(2)
                return True
            except TimeoutException:
                continue
                
    except Exception as e:
        print(f"  No cookie pop-up detected")
    
    return False

def wait_for_page_load(driver, wait):
    """
    Wait for the playlist page to fully load
    """
    try:
        # Wait for main content area
        wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        time.sleep(3)
        return True
    except TimeoutException:
        print("  Warning: Main content area not detected")
        return False

def find_scrollable_container(driver):
    """
    Find the correct scrollable container for the playlist
    """
    # Try multiple possible scrollable containers in order of likelihood
    selectors = [
        'div[data-overlayscrollbars-viewport]',  # Spotify's custom scrollbar
        'div.main-view-container__scroll-node',
        'div[class*="main-view-container"]',
        'div.os-viewport',  # OverlayScrollbars viewport
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                # Check if element is actually scrollable
                scroll_height = driver.execute_script("return arguments[0].scrollHeight;", element)
                client_height = driver.execute_script("return arguments[0].clientHeight;", element)
                
                if scroll_height > client_height + 100:  # At least 100px scrollable
                    print(f"  Found scrollable container: {selector}")
                    print(f"  Scroll height: {scroll_height}px, Visible height: {client_height}px")
                    return element
        except:
            continue
    
    print("  Using body/document for scrolling")
    return None

def scroll_to_load_all_tracks(driver, max_scrolls=200):
    """
    Scroll incrementally to load all tracks in the playlist
    
    Args:
        driver: WebDriver instance
        max_scrolls: Maximum number of scroll attempts
    
    Returns:
        bool: True if scrolling completed successfully
    """
    print("Starting to scroll and load tracks...")
    
    # Find the scrollable container
    scrollable_element = find_scrollable_container(driver)
    
    # Click on the page first to ensure focus
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        body.click()
        time.sleep(0.5)
    except:
        pass
    
    last_track_count = 0
    no_change_count = 0
    max_no_change = 4
    scroll_count = 0
    
    while scroll_count < max_scrolls:
        # Count current tracks in DOM
        try:
            current_tracks = len(driver.find_elements(By.CSS_SELECTOR, 
                '[data-testid="tracklist-row"], div[role="row"][aria-rowindex]'))
        except:
            current_tracks = 0
        
        # Perform scroll action
        if scrollable_element:
            # Get current metrics
            current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_element)
            scroll_height = driver.execute_script("return arguments[0].scrollHeight;", scrollable_element)
            client_height = driver.execute_script("return arguments[0].clientHeight;", scrollable_element)
            
            # Scroll by 800px or to bottom, whichever is less
            new_scroll_position = min(current_scroll + 800, scroll_height - client_height)
            driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable_element, new_scroll_position)
            
            # Check if at bottom
            time.sleep(1.5)
            actual_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_element)
            at_bottom = (actual_scroll + client_height) >= (scroll_height - 100)
            
        else:
            # Use keyboard and Actions for scrolling (more reliable)
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            
            # Send PAGE_DOWN key multiple times
            for _ in range(3):
                actions.send_keys(Keys.PAGE_DOWN).perform()
                time.sleep(0.3)
            
            time.sleep(1.5)
            
            # Check if at bottom
            current_scroll = driver.execute_script("return window.pageYOffset;")
            scroll_height = driver.execute_script("return document.body.scrollHeight;")
            window_height = driver.execute_script("return window.innerHeight;")
            at_bottom = (current_scroll + window_height) >= (scroll_height - 100)
        
        # Check if new tracks loaded
        if current_tracks == last_track_count:
            no_change_count += 1
            
            if at_bottom:
                print(f"  Tracks: {current_tracks} (at bottom, no change {no_change_count}/{max_no_change})")
                
                if no_change_count >= max_no_change:
                    print(f"✓ Reached end - {current_tracks} tracks loaded")
                    break
            else:
                print(f"  Tracks: {current_tracks} (scrolling...)")
                # If stuck but not at bottom, force a big scroll
                if no_change_count > 8:
                    print(f"  Force scrolling to bottom...")
                    if scrollable_element:
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable_element)
                    else:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
        else:
            no_change_count = 0
            scroll_count += 1
            new_tracks = current_tracks - last_track_count
            print(f"  Scroll {scroll_count}: {current_tracks} tracks (+{new_tracks})")
        
        last_track_count = current_tracks
    
    # Scroll back to top
    print("  Scrolling back to top...")
    if scrollable_element:
        driver.execute_script("arguments[0].scrollTop = 0;", scrollable_element)
    else:
        driver.execute_script("window.scrollTo(0, 0);")
    
    time.sleep(2)
    
    return True

def debug_page_structure(driver):
    """
    Debug function to inspect page structure
    """
    print("\n[DEBUG] Analyzing page structure...")
    
    # Check for common Spotify elements
    selectors_to_check = [
        ('div[role="row"]', 'Role-based rows'),
        ('div[data-testid*="track"]', 'Track testid elements'),
        ('div.tracklist-row', 'Tracklist row class'),
        ('a[href*="/track/"]', 'Track links'),
        ('div[aria-rowindex]', 'Aria-rowindex elements'),
    ]
    
    for selector, description in selectors_to_check:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"  {description}: Found {len(elements)} elements")
        except Exception as e:
            print(f"  {description}: Error - {e}")
    
    # Get page source snippet
    page_text = driver.find_element(By.TAG_NAME, "body").text[:500]
    print(f"\n[DEBUG] Page text preview:\n{page_text}\n")

def scroll_and_scrape_tracks(driver, wait):
    """
    Scroll through playlist and scrape tracks progressively
    This prevents tracks from being unloaded when scrolling back to top
    
    Args:
        driver: WebDriver instance
        wait: WebDriverWait instance
    
    Returns:
        list: List of dictionaries containing track data
    """
    print("Starting progressive scroll and scrape...")
    
    # Find the scrollable container
    scrollable_element = find_scrollable_container(driver)
    
    # Click on page to ensure focus
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        body.click()
        time.sleep(0.3)
    except:
        pass
    
    all_tracks = []
    seen_titles = set()
    last_track_count = 0
    no_change_count = 0
    max_no_change = 3  # Reduced from 4 for faster completion
    scroll_count = 0
    max_scrolls = 200
    
    while scroll_count < max_scrolls:
        # Scrape currently visible tracks
        try:
            track_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tracklist-row"]')
            
            for track_element in track_elements:
                try:
                    # Extract title
                    try:
                        title_elem = track_element.find_element(By.CSS_SELECTOR, 'a[data-testid]')
                        title = title_elem.get_attribute('title') or title_elem.text.strip()
                    except:
                        title_elem = track_element.find_element(By.TAG_NAME, 'a')
                        title = title_elem.text.strip()
                    
                    if not title or title in seen_titles:
                        continue
                    
                    seen_titles.add(title)
                    
                    # Extract artist
                    try:
                        artist_elems = track_element.find_elements(By.CSS_SELECTOR, 'span a[href*="/artist/"]')
                        artists = [elem.text.strip() for elem in artist_elems if elem.text.strip()]
                        artist = ", ".join(artists[:3]) if artists else "Unknown Artist"
                    except:
                        artist = "Unknown Artist"
                    
                    # Extract album
                    try:
                        album_elem = track_element.find_element(By.CSS_SELECTOR, 'a[href*="/album/"]')
                        album = album_elem.get_attribute('title') or album_elem.text.strip()
                    except:
                        album = "Unknown Album"
                    
                    # Extract duration
                    try:
                        duration_elem = track_element.find_element(By.CSS_SELECTOR, 'div[data-testid*="duration"]')
                        duration = duration_elem.text.strip()
                        if ':' not in duration:
                            duration = "0:00"
                    except:
                        import re
                        text = track_element.text
                        time_match = re.search(r'\d+:\d+', text)
                        duration = time_match.group(0) if time_match else "0:00"
                    
                    track_data = {
                        'Title': title,
                        'Artist': artist,
                        'Album': album,
                        'Duration': duration
                    }
                    
                    all_tracks.append(track_data)
                    
                except:
                    continue
                    
        except:
            pass
        
        current_track_count = len(all_tracks)
        
        # Perform scroll - FASTER with larger increments
        if scrollable_element:
            current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_element)
            scroll_height = driver.execute_script("return arguments[0].scrollHeight;", scrollable_element)
            client_height = driver.execute_script("return arguments[0].clientHeight;", scrollable_element)
            
            # Larger scroll increment for speed
            new_scroll_position = min(current_scroll + 1200, scroll_height - client_height)
            driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable_element, new_scroll_position)
            
            time.sleep(0.8)  # Reduced from 1.5 for speed
            actual_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_element)
            at_bottom = (actual_scroll + client_height) >= (scroll_height - 100)
            
        else:
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            # More page downs for faster scrolling
            for _ in range(5):
                actions.send_keys(Keys.PAGE_DOWN).perform()
                time.sleep(0.15)
            
            time.sleep(0.8)  # Reduced wait time
            
            current_scroll = driver.execute_script("return window.pageYOffset;")
            scroll_height = driver.execute_script("return document.body.scrollHeight;")
            window_height = driver.execute_script("return window.innerHeight;")
            at_bottom = (current_scroll + window_height) >= (scroll_height - 100)
        
        # Check progress
        if current_track_count == last_track_count:
            no_change_count += 1
            
            if at_bottom:
                print(f"  Scraped: {current_track_count} tracks (at bottom, no change {no_change_count}/{max_no_change})")
                
                if no_change_count >= max_no_change:
                    print(f"✓ Finished - {current_track_count} unique tracks scraped")
                    break
            else:
                print(f"  Scraped: {current_track_count} tracks (scrolling...)")
                
                if no_change_count > 6:  # Reduced from 8
                    print(f"  Force scrolling to bottom...")
                    if scrollable_element:
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable_element)
                    else:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
        else:
            no_change_count = 0
            scroll_count += 1
            new_tracks = current_track_count - last_track_count
            print(f"  Scroll {scroll_count}: {current_track_count} tracks scraped (+{new_tracks})")
        
        last_track_count = current_track_count
    
    return all_tracks

def save_to_csv(tracks, filename='spotify_playlist.csv'):
    """
    Save track data to CSV file
    
    Args:
        tracks (list): List of track dictionaries
        filename (str): Output CSV filename
    """
    if not tracks:
        print("No tracks to save")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Artist', 'Album', 'Duration']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(tracks)
        
        print(f"✓ Data saved to {filename}")
        
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def save_page_source(driver, filename='page_source.html'):
    """
    Save page source for debugging
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"  Page source saved to {filename} for debugging")
    except Exception as e:
        print(f"  Could not save page source: {e}")

def main(playlist_url, headless=True, output_file='spotify_playlist.csv', debug=False):
    """
    Main function to orchestrate the scraping process
    
    Args:
        playlist_url (str): URL of the Spotify playlist
        headless (bool): Run in headless mode
        output_file (str): Output CSV filename
        debug (bool): Enable debug mode
    """
    driver = None
    
    try:
        print("="*60)
        print("SPOTIFY PLAYLIST SCRAPER")
        print("="*60)
        
        # Setup driver
        print("\n[1/5] Setting up Chrome WebDriver...")
        driver = setup_driver(headless=headless)
        wait = WebDriverWait(driver, 15)
        
        # Load playlist
        print(f"\n[2/5] Loading playlist: {playlist_url}")
        driver.get(playlist_url)
        
        # Wait for initial load
        wait_for_page_load(driver, wait)
        
        # Handle cookies
        print("\n[3/5] Checking for cookie consent...")
        handle_cookie_consent(driver, wait)
        
        # Scroll to load all tracks
        print("\n[4/5] Scrolling and scraping tracks progressively...")
        tracks = scroll_and_scrape_tracks(driver, wait)
        
        # Save page source if debugging and no tracks found
        if debug and len(tracks) == 0:
            save_page_source(driver)
        
        # Save to CSV
        if tracks:
            print(f"\n[SAVE] Saving {len(tracks)} tracks to CSV...")
            save_to_csv(tracks, output_file)
            print("\n" + "="*60)
            print("✓ SCRAPING COMPLETED SUCCESSFULLY")
            print("="*60)
        else:
            print("\n⚠ No tracks were scraped")
            print("\nTROUBLESHOOTING:")
            print("1. The playlist might require login")
            print("2. Spotify may have updated their HTML structure")
            print("3. Try setting headless=False to see what's happening")
            print("4. Set debug=True to save page source for inspection")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
            print("\n[CLEANUP] Browser closed")

if __name__ == "__main__":
    # Example usage
    PLAYLIST_URL = "https://open.spotify.com/playlist/7cifluiYWoLCcdeQvtvWP0"
    
    # Run scraper with debug mode
    main(
        playlist_url=PLAYLIST_URL,
        headless=False,  # Set to False to see browser
        output_file='spotify_playlist.csv',
        debug=True  # Enable debugging
    )
from playwright.sync_api import sync_playwright

def scrape_full_playlist(url):
    """
    Scrape all songs from a Spotify playlist using Playwright.
    
    Args:
        url (str): The URL of the Spotify playlist
        
    Returns:
        list: A list of unique song titles
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Wait for the first few tracks to appear
        page.wait_for_selector('div[role="row"]')
        
        songs = set()
        last_count = 0
        
        while True:
            # Scroll the playlist container
            page.keyboard.press("End") 
            page.wait_for_timeout(2000)  # Wait for "lazy load"
            
            # Capture visible track names
            current_tracks = page.locator('div[role="row"]').all_inner_texts()
            for track in current_tracks:
                # Extract just the song title (first part before newline)
                title = track.split('\n')[0].strip()
                if title:  # Only add non-empty titles
                    songs.add(title)
                
            if len(songs) == last_count:  # No new songs loaded
                break
            last_count = len(songs)
            
        browser.close()
        return list(songs)
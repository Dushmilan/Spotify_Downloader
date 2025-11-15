# RULES FOR SPOTIFY DOWNLOADER PROJECT

## CRITICAL RULES FOR SPOTIFY_SCRAPER MODULE

1. **NEVER modify Spotify_Scraper.py import statement**
   - The import `from spotify_scraper import SpotifyClient` must remain unchanged
   - This imports from the official PyPI library: spotifyscraper
   - Do NOT change this to import from a local file

2. **NEVER create or modify spotify_scraper.py locally**
   - The spotify_scraper module is an external library from PyPI
   - Do NOT implement your own version of this module
   - Users must install it via: pip install spotifyscraper

3. **Always verify before modifying scraper functions**
   - Check that Spotify_Scraper.py functions (get_track, get_playlist, get_album) are preserved
   - These functions depend on the external spotify_scraper library
   - Verify the library documentation at: https://spotifyscraper.readthedocs.io/en/latest/

4. **Scraper functions must remain intact**
   - get_track(track_url) -> calls client.get_track_info(track_url)
   - get_playlist(playlist_url) -> calls client.get_playlist_info(playlist_url)
   - get_album(album_url) -> calls client.get_album_info(album_url)
   - These depend on the official library's API

5. **Validation checklist before any changes**
   - Does Spotify_Scraper.py import from spotify_scraper?
   - Is the spotify_scraper an external library (not local implementation)?
   - Are the scraper functions preserved?
   - Will the code work with pip install spotifyscraper?

6. **Dependencies reminder**
   - Main dependencies: spotifyscraper, yt-dlp, requests
   - Install with: pip install spotifyscraper yt-dlp requests

7. **Workflow preservation**
   - Maintain the documented 9-step workflow from README.md
   - Preserve connection between all components: main.py -> Spotify_Scraper.py -> Url_Validator.py -> Youtube_query.py

## CONSEQUENCES OF VIOLATION
If these rules are violated:
- The application will fail with ImportError
- The core functionality will break
- Users will not be able to scrape Spotify data
- The entire pipeline will stop working
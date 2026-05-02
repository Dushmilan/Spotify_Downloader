

# 1.0.0

## Features

- Initial release of the package.
- Added support for downloading files from a URL.
- Added support for skipping exisiting files for the download function.

## Bug Fixes

- None.

## Improvements
- Increased speed of scraping 

## Documentation

- Initial documentation for the package.

## Breaking Changes

- API scraping breaks

## Known Issues

- Song miss matches
- Download errors
- Scroll errors
- Need proper error handling
- Meed proper logging

## Last error
[DownloaderThread] Initiating download for: https://open.spotify.com/playlist/4ZXPBarWWiVHofwYMdrIyW?si=pmFQa-FkQK6W_6VWd_yTtQ
[DownloaderThread] Validated as Spotify URL
[DownloaderThread] Loading playlist page to capture access token...
[DownloaderThread] Waiting for auth token... (scrolling to trigger)
[DownloaderThread] Error: API token interception timed out.
[DownloaderThread] Scraping playlist with PlaywrightScraper Error: [processing_error] Failed to scrape playlist - no data returned
[DownloaderThread] Main download process Error: [processing_error] Playlist scraping failed: [processing_error] Failed to scrape playlist - no data returned


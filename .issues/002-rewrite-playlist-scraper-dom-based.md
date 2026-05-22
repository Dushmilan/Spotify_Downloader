## What to build

The playlist scraper (`scrape_playlist_async`) intercepts Bearer tokens from Spotify's API via `page.on("request")`, then uses those tokens to fetch all tracks via the REST API. This approach broke when Spotify changed their auth flow — the token is no longer captured reliably, causing every playlist scrape to time out with "API token interception timed out".

Replace the API-token approach with a DOM-based approach, following the same pattern as the album scraper:

1. **Load the playlist page** and wait for `main` to render
2. **Scroll the page** repeatedly to trigger lazy-loading of all tracks (the playlist may have hundreds of tracks)
3. **Parse each `[data-testid="tracklist-row"]`** to extract title, artist (via `a[data-testid="creator-link"]`), album link, and duration
4. **Stop** when a scroll cycle adds zero new rows (or after a reasonable max — e.g. 50 scrolls)
5. **Return the playlist name + all tracks** in the same shape as the current API: `{name, tracks: {items: [...]}}`

The playlist name itself can be read from `span[data-testid="entityTitle"]` or from the page title.

### Important design notes from the album scraper prototype

The album scraper's track-row parsing (lines 171-191 of `playwright_scraper.py`) is the template to follow. The key differences for playlists are:

- **No upfront track count** — must scroll until no new rows appear
- **Deduplication** — scrolling may return rows already seen; dedupe by row index or track ID
- **Performance** — large playlists (500+ tracks) may need many scroll cycles; add a progress callback
- **Rate limiting** — no API calls are made, so no rate limits apply

Pre-existing test `test_scrape_playlist_mock` will need updating to match the new mock surface — handle this in the same PR.

## Acceptance criteria

- [ ] Running `scrape_playlist` on a real playlist URL returns all tracks with correct title, artist, duration
- [ ] 50-track and 200-track playlists both complete without timeout
- [ ] `test_scrape_playlist_mock` passes (updated for DOM-based approach)
- [ ] No API calls to `api.spotify.com` are made during scraping
- [ ] All 81 other tests still pass

## Blocked by

None — can start immediately

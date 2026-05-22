## What to build

Run a manual smoke test of all three URL types (track, album, playlist) against real Spotify URLs and verify the scraped metadata is correct end-to-end. This is the final verification step before marking the scraper fixes as done.

Test with these URLs (or equivalent real URLs):

- **Track**: `https://open.spotify.com/track/3JvKfv6T31zO0ini8iNItO` — "Another Love" by Tom Odell
- **Album**: `https://open.spotify.com/album/1A2GTWGtFfWp7KSQTwWOyo` — "Human After All" by Daft Punk  
- **Playlist**: `https://open.spotify.com/playlist/7cifluiYWoLCcdeQvtvWP0` — any playlist with 10+ tracks

For each URL, verify:

- Title is correct (no fallback garbage)
- Artists list contains only real artist names (no "Popular Releases by..." noise)
- Album name is correct (not "Unknown Album")
- Duration is non-zero for tracks
- Track count is reasonable for albums/playlists

## Acceptance criteria

- [ ] Track scrape: title = "Another Love", artists = ["Tom Odell"], album = "Long Way Down (Deluxe)", duration > 0
- [ ] Album scrape: title = "Human After All", track count = 10, all tracks have non-zero duration
- [ ] Playlist scrape: name is non-empty, at least 5 tracks returned, all tracks have clean artist names
- [ ] No "Popular Releases by...", "Show all", "Fans also like" appear in any artist field

## Blocked by

- Issue 001: Fix album scraper selectors
- Issue 002: Rewrite playlist scraper to DOM-based

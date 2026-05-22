## What to build

The album scraper (`scrape_album_async`) still uses the same broken selectors that were fixed in the track scraper. It relies on `h1[data-testid="entityTitle"]` for the album name and `a[href*="/artist/"]` for per-track artists. Since Spotify's page update, the title is now a `span` element and the broad artist selector picks up sidebar garbage ("Popular Releases by...", "Show all", "Fans also like").

Apply the same three selector fixes that were made to the track scraper:

1. **Album title** — prefer `span[data-testid="entityTitle"]`, fall back to `h1[data-testid="entityTitle"]`, then `h1.encore-text-headline-large`, then `document.title`
2. **Per-track artists** — use `a[data-testid="creator-link"]` inside each `[data-testid="tracklist-row"]` instead of `a[href*="/artist/"]`
3. **Per-track duration** — if `div[data-testid*="duration"]` is not found, search for a `span` matching `\d+:\d+` within the row

Tracklist rows use `[data-testid="tracklist-row"]` — this selector still works and does not need changing.

## Acceptance criteria

- [ ] Running `scrape_album` on an album URL returns correct album name (not "Unknown Album")
- [ ] Each track in the result has only real artist names (no "Popular Releases by...", "Show all", etc.)
- [ ] Each track has a non-zero duration_ms
- [ ] `test_scrape_album_mock` still passes (it mocks `page.evaluate` return values, not the selectors themselves)

## Blocked by

None — can start immediately

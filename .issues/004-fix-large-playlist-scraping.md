## What to build

The current DOM-based playlist scraper loads all tracks by scrolling via `scrollIntoView({block: 'end'})` and parsing `[data-testid="tracklist-row"]` elements. This works for playlists with ~60 tracks, but **fails for larger playlists** — Spotify's virtual scroller caps the number of rendered DOM elements at roughly 59-60, so the remaining tracks are never added to the DOM no matter how much you scroll.

Investigation showed:

- `scrollIntoView({block: 'end'})` loads 2-3 batches (25 → 47 → 59 tracks) then stops
- Adding a scroll bounce (`scrollBy(0, 400)`) after `scrollIntoView` doesn't help
- `main.scrollTo(0, 999999)` doesn't work — the main element is not the scroll container
- `window.scrollTo(0, document.body.scrollHeight)` doesn't work either
- The actual scrollable element has `overflow: visible` so manual scroll methods don't trigger the virtual scroller's lazy loading
- The total track count ("301 songs") is available in the page, confirming Spotify knows the total but doesn't render all rows

### Approach

The fix should use **API token extraction** from the Spotify page:

1. **Extract the access token**: Spotify web player makes a request to `https://open.spotify.com/api/token?reason=init&productType=web-player` — this returns a JSON body with an `accessToken` field. Intercept this via `page.on("response")`.
2. **Fetch all tracks via the Spotify Web API**: With the access token (`Authorization: Bearer <token>`), call `https://api.spotify.com/v1/playlists/{id}/tracks?offset={offset}&limit=50&market=from_token` repeatedly (with offset incremented) until all tracks are fetched.
3. **Handle rate limiting**: The Web API may return 429 if called too aggressively. Add a retry with backoff.

The extracted `accessToken` is short-lived (roughly 1 hour) and the token request is made automatically when the page loads, so there's no extra auth burden on the user.

**Important**: Do NOT revert to the OLD token interception approach (which broke because Spotify changed their auth flow). The OLD approach intercepted a different endpoint. This new approach intercepts the `/api/token` endpoint which still works reliably.

Return the playlist name from `span[data-testid="entityTitle"]` (already works) and tracks from the API, merged into the same shape: `{name, tracks: {items: [...]}}`.

### Prototype findings

The token extraction and API call was prototyped successfully:

```python
# Intercept token from page load
async def on_response(resp):
    if '/api/token' in resp.url:
        body = await resp.json()
        token = body.get('accessToken', '')

# Use token to fetch all tracks
url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?offset={offset}&limit=50&market=from_token'
# With header: Authorization: Bearer {token}
```

## Acceptance criteria

- [ ] Scraping a 301-track playlist returns all 301 tracks (not just ~59)
- [ ] Scraping a small playlist (<60 tracks) still works and returns all tracks
- [ ] Rate limits (429) are handled with retry + backoff (no silent data loss)
- [ ] Expired tokens are detected and retried by reloading the page
- [ ] `test_scrape_playlist_mock` passes (updated for API-fallback approach)
- [ ] All other existing tests still pass
- [ ] The album and track scrapers are not affected

## Blocked by

None — can start immediately

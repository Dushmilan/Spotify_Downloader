# Progress

> Session-to-session tracking of what we're working on, what's done, and what's blocked.

---

## 2026-05-22 — Large-playlist scraping fix

**Type**: Bug fix · **Tracks**: 004-fix-large-playlist-scraping

### Goal
Fix the DOM-based Playwright scraper to reliably load all tracks in large playlists where Spotify's virtual scroller caps rendered rows at ~59.

### Done
- Replaced naive scroll logic with a **3-phase zoom strategy** in `scrape_playlist_async`:
  - **Phase 1**: Normal scroll to bottom (works for short playlists)
  - **Phase 2**: Dynamic zoom calculated from `clientHeight / (total × 64px × 1.2)`, clamped to `[0.008, 0.5]` — forces the virtual scroller to render all rows at once
  - **Phase 3**: Sentinel scroll — scrolls `div[data-testid="bottom-sentinel"]` into view with `{block: 'nearest'}` to trigger IntersectionObserver
  - **Phase 4**: Parse all visible track rows, truncate to `total_estimate` to remove virtual scroller buffer artifacts
- Removed title+artist dedup (too aggressive for playlists with repeated songs; count-based truncation is safer)
- Verified: 301-track playlist → 301 tracks; 602-track playlist → 602 tracks
- Updated `test_scrape_playlist_mock` to match new evaluate sequence
- All 82 existing tests pass

### Key decisions
| Decision | Rationale |
|---|---|
| Zoom-based approach | Only reliable way to force Spotify's React virtualizer to render all rows without API access |
| Count-based truncation | Buffer rows (~8–9) from virtual scroller are predictable; better than dedup which drops legitimate duplicates |
| Scroll container selector | `div.main-view-container__scroll-node > div` (not `div.os-viewport` — that element no longer exists) |

### Files touched
- `src/spot_downloader/utils/playwright_scraper.py` — `scrape_playlist_async` rewrite
- `tests/test_playwright_scraper.py` — `test_scrape_playlist_mock` updated

---

## Format

When starting new work, create a new entry with:

```markdown
## YYYY-MM-DD — Short title

**Type**: Feature/Bug/Refactor/CI · **Tracks**: issue-ids (if any)

### Goal
One-sentence problem statement.

### Done
- [ ] Bullet list of completed items
- [x] Checked boxes for concrete sub-tasks

### Blocked
- (nothing) or list of blockers with rationale

### Key decisions
| Decision | Rationale |
|---|---|
| What we chose | Why we chose it |

### Files touched
- path/to/file.py — what changed
```

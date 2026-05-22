# Project Goal

## Vision

A reliable, privacy-respecting desktop application that downloads Spotify music as high-quality tagged audio files — without requiring API credentials, subscriptions, or online accounts.

No data leaves the user's machine except the initial YouTube search for each track.

## Principles

- **Zero API keys** — The app must work out of the box. No Spotify Developer Console, no OAuth dance, no client secrets.
- **Privacy by design** — No telemetry, no analytics, no user accounts. The only outbound requests are to YouTube Music for search and download.
- **Reliable at scale** — 600-track playlists should work as seamlessly as 6-track ones. Large playlists are not an edge case.
- **Desktop-first** — A native GUI experience. Not a CLI tool with a web wrapper.
- **Fail gracefully** — Network errors, rate limits, and DOM changes never result in data loss. Partial downloads are cleaned up. Failed tracks don't block the rest.

## Roadmap

### Done

- Functional GUI with CustomTkinter (settings, queue, progress bars)
- Single-track, album, and playlist scraping via Playwright
- YouTube Music search with fuzzy matching
- Audio download via yt-dlp
- ID3 tagging with album art (mp3 + m4a)
- Concurrent download support with rate limiting
- Configurable quality, format, and concurrency
- URL validation and path sanitization
- Retry with exponential backoff
- Architecture deepening (ADR-001): removed dead service layer, scraper ABC, Selenium
- Large-playlist DOM scraping via zoom-based virtual scroller rendering
- 82 passing tests

### In progress

- Release packaging (PyInstaller or similar)
- CI/CD pipeline
- User documentation (in-app help tooltips)

### Future

- **Download history** — persistent record of previously downloaded tracks (avoid re-downloading across sessions)
- **Search within playlists** — filter playlist tracks by name before downloading
- **Custom filename templates** — user-configurable output naming patterns
- **Playlist sync mode** — detect new tracks in a playlist and download only those
- **Alternative audio sources** — support additional YouTube extractors or direct audio sources
- **Dark mode toggle** — standalone switch independent of system theme
- **Localisation** — i18n support for the GUI

## Non-goals

- Streaming or in-app playback — download only
- Spotify Web API integration — intentionally avoided to keep zero-registration UX
- Mobile or web versions — desktop app only
- DRM circumvention — only downloads content that is publicly accessible via YouTube
- Music discovery or recommendations — purely a download tool

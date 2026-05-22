# Spot-Downloader

> Desktop GUI for downloading Spotify music — playlists, albums, or single tracks — with automatic metadata tagging.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Spotify → MP3/FLAC/M4A** — Paste a Spotify URL, get a tagged audio file.
- **Playlists & albums** — Download entire collections in one click. Large playlists (600+ tracks) supported.
- **Desktop GUI** — Built with CustomTkinter. Native look, light/dark theme, resizable.
- **Auto-tagging** — Album art, artist, title, album name embedded via mutagen.
- **Concurrent downloads** — Configurable parallel downloads with progress tracking per track.
- **Resume-ready** — Skips already-downloaded files. Cancel mid-operation without corruption.
- **No API keys** — Scrapes metadata via Playwright (no Spotify API credentials needed).

## Quick start

```bash
# Install
pip install -r requirements.txt
playwright install chromium

# Run
python main.py
```

**Prerequisites**: Python 3.8+. FFmpeg is bundled automatically via `imageio-ffmpeg`.

## Usage

| Step | Action |
|---|---|
| 1 | Paste a Spotify URL (track, album, or playlist) |
| 2 | Click **Download** |
| 3 | Track progress in the queue panel |
| 4 | Click **Open Folder** to browse completed files |

### Configuration

Settings are available in-app or directly in `config.json`:

| Key | Default | Description |
|---|---|---|
| `download_quality` | `320kbps` | Audio bitrate: `128kbps`, `256kbps`, or `320kbps` |
| `file_format` | `mp3` | Output format: `mp3`, `flac`, or `m4a` |
| `max_concurrent_downloads` | `5` | Parallel download limit (1–10) |
| `download_path` | `downloads` | Output directory |
| `retry_attempts` | `3` | Retries on failure (0–10) |
| `safe_mode` | `true` | Enables URL & path security validation |

## Architecture

```
src/spot_downloader/
├── gui/              # CustomTkinter desktop UI
│   ├── app.py        # Main window, queue, settings panels
│   └── styles.py     # Theme colours & fonts
├── core/             # Download orchestration
│   ├── downloader.py # SpotDownloader, DownloadHandle
│   └── searcher.py   # YouTube Music search
├── tracker/          # Download state management
│   └── download_tracker.py
└── utils/            # Supporting modules
    ├── playwright_scraper.py  # Spotify DOM scraping
    ├── tagger.py              # Audio metadata tagging
    ├── validation.py          # URL/path security
    ├── error_handling.py      # Typed exceptions
    ├── retry.py               # Exponential-backoff retry
    ├── rate_limiter.py        # Token-bucket rate limiter
    ├── logger.py              # Logging setup
    ├── throttle.py            # Call rate throttle
    └── helpers.py             # FFmpeg discovery
```

### How it works

1. **Scrape** — Playwright loads the Spotify page, extracts track names, artists, durations via DOM parsing. For large playlists, a zoom-based strategy forces the virtual scroller to render all rows.
2. **Search** — Each track is looked up on YouTube Music via DOM-parsed search results with fuzzy matching.
3. **Download** — `yt-dlp` downloads the best-matching audio stream.
4. **Tag** — mutagen embeds ID3 tags and album art into the output file.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev,test]"

# Run tests
pytest

# Lint & type-check
ruff check src/
mypy src/
```

### Project structure

```
├── .issues/          # Tracked issue specs (one per feature/bug)
├── docs/adr/         # Architecture Decision Records
├── plans/            # Planning docs & migration guides
├── tests/            # pytest suite (82+ tests)
└── src/
```

## Security

- URL validation rejects non-Spotify and private-IP URLs
- Filename sanitization prevents directory traversal
- Safe mode blocks downloads to paths outside the configured directory
- All external requests go through validated, scheme-restricted URLs

## Troubleshooting

| Symptom | Fix |
|---|---|
| "FFmpeg not found" | Run `pip install imageio-ffmpeg` or install FFmpeg manually |
| Playlist shows only ~60 tracks | Requires Chromium — run `playwright install chromium` |
| Download fails mid-way | Check network. Retries are automatic (configurable in settings) |
| GUI doesn't open | Ensure `customtkinter` is installed: `pip install customtkinter` |

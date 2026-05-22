# ADR 001: Architecture Deepening — Download Pipeline

## Status

Accepted (2026-05-22)

## Context

The download pipeline had grown organically with redundant layers, a threaded callback signature, an ABC-based scraper abstraction that was never polymorphically used, and a dead service-layer pass-through. These patterns eroded **depth** (narrow, information-dense interfaces) and **locality** (related logic scattered across modules).

Five deepening candidates were evaluated:

1. **Download pipeline** — `custom_engine.py` + `downloader.py` split (strong)
2. **Scraper construction** — ABC base class vs duck-typing (strong)
3. **GUI extraction** — pulling download orchestration out of the UI (exploratory)
4. **DownloadTracker deduplication** — method copies (cleanup)
5. **Service layer deletion** — pass-through module (dead code)

Candidates 1, 2, 4, and 5 were pursued. Candidate 3 was rejected — the GUI keeps download orchestration inline to avoid an additional indirection layer.

## Decisions

### 1. `download(url)` returns `DownloadHandle`, not `threading.Thread`

The module owns the background thread internally. The caller gets a handle with `.cancel()`, `.result(timeout)`, `.on_progress(cb)`, `.on_log(cb)`. This keeps the threading detail inside the module (**locality**) and presents a narrow, stable interface (**depth**).

### 2. No `Scraper` ABC — duck-typing + constructor injection

The `Scraper` ABC in `core/interfaces.py` was deleted. `PlaywrightScraper` is a plain class. `SpotDownloader` accepts any scraper via constructor injection with `PlaywrightScraper` as default. The protocol contract is implicit (must implement `scrape_track`, `scrape_album`, `scrape_playlist`).

### 3. One retry at the outer seam

The `@retry` decorator was moved from `CustomDownloadEngine._download_and_tag` to `SpotDownloader._download_and_tag`. Only the outermost callable is decorated — no nested retries.

### 4. `DownloadTracker` is an internal detail of `SpotDownloader`

Exposed as `downloader.tracker` only so the GUI queue view can read progress state. Not wrapped in a separate controller.

### 5. Service layer deleted

`services/download_service.py` and `services/__init__.py` were deleted. `gui/app.py` imports `SpotDownloader` directly.

### 6. Selenium removed

`PlaywrightScraper` is the sole scraper implementation. `selenium_scraper.py`, the `Scraper` ABC, and the `selenium` dependency were removed.

### 7. Dead code pruned

- `retry_with_fallback` — removed (only `retry` is used)
- `log_callback_factory` — removed (callbacks are lambdas in the GUI)
- `AdaptiveRateLimiter` — removed (not used in production)
- `custom_engine.py` — removed (logic merged into `downloader.py`)

## Consequences

- **Positive**: Total line count reduced ~25%. Fewer modules to navigate. Interface surface shrinks from 3-4 import paths (`DownloadService` → `SpotDownloader`) to 1 (`SpotDownloader`).
- **Positive**: Tests are simpler — mock one scraper interface, inspect one result type.
- **Negative**: The duck-typed scraper contract is not enforced at runtime. A future TypeError from a missing method is the only guard.
- **Neutral**: GUI polling loop (`self.after(100, poll_result)`) replaces the old threaded orchestration — simpler but adds a frame-based scheduling dependency.

## Notes

- Pre-existing test failure `test_scrape_playlist_mock` is an async mock issue with Playwright's `page.on("request", ...)` — unrelated to the deepening changes.
- `spotipy` dependency in `requirements.txt` is likely unused but was not audited.

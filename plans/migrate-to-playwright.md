# Migration Plan: Selenium to Playwright (TDD Approach)

## Objective
Migrate the current Selenium-based scraping engine to Playwright to improve performance, reliability, and maintainability. The migration will follow a strict Test-Driven Development (TDD) workflow and adhere to senior software engineering standards (modular design, interface-based programming, and comprehensive testing).

## Background & Motivation
- **Selenium Limitations:** Current implementation relies on manual waits (`time.sleep`), complex JavaScript for scrolling, and is prone to "stale element" errors.
- **Playwright Benefits:** Native auto-waiting, superior handling of SPAs (Spotify), and more efficient resource management (BrowserContexts).
- **Architectural Goal:** Abstract the scraping logic so the implementation (Selenium or Playwright) can be swapped without changing core business logic.

## Proposed Solution

### 1. Architectural Abstraction
Introduce a `ScraperInterface` (Abstract Base Class) to decouple the downloader from specific scraper implementations.

### 2. Implementation Strategy (Playwright)
- Use `playwright-python` with the Chromium engine.
- Implement stealth techniques (User-Agent rotation, headless mode optimizations).
- Leverage Playwright's network interception for more reliable metadata harvesting.

## Phased Implementation Plan

### Phase 1: Infrastructure & Interface
1.  **Define Interface:** Create `src/spot_downloader/core/interfaces.py`.
2.  **Environment Setup:** Add `playwright` and `pytest-playwright` to `requirements.txt`.
3.  **Refactor Downloader:** Modify `src/spot_downloader/core/downloader.py` to use the interface.

### Phase 2: TDD - Core Metadata Scraping
1.  **Test Case:** `test_scrape_track`
    - Red: Define failing test for a single track URL.
    - Green: Implement basic Playwright logic for track metadata.
    - Refactor: Move CSS selectors to a dedicated configuration file.
2.  **Test Case:** `test_scrape_album`
    - Red: Define failing test for an album URL.
    - Green: Implement Playwright logic for album metadata.

### Phase 3: TDD - Playlist Infinite Scrolling (Critical Path)
1.  **Test Case:** `test_scrape_playlist`
    - Red: Define failing test for a large playlist.
    - Green: Implement Playwright scrolling logic using `scroll_into_view_if_needed`.
    - Green (Optimization): Use network interception (`page.on("response")`) to harvest track data.

### Phase 4: Integration & Validation
1.  **Parity Tests:** Ensure Playwright results match Selenium results for identical inputs.
2.  **Performance Benchmarking:** Verify memory and CPU reduction.
3.  **GUI Integration:** Connect the new scraper to the `customtkinter` frontend.

## Verification & Testing
- **Unit Tests:** `pytest tests/test_playwright_scraper.py`
- **Integration Tests:** Verify full download flow in `tests/test_downloader.py`.
- **Stealth Check:** Verify the scraper bypasses basic bot detection.

## Migration Strategy
- **Stage 1:** Keep Selenium as default, offer Playwright as an experimental flag.
- **Stage 2:** Switch Playwright to default after 1 week of stable testing.
- **Stage 3:** Remove Selenium dependencies once Playwright is fully validated.

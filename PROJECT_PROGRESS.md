# Project Progress

This file tracks the development progress of the Spot-Downloader Desktop application.

## Current Status
- [x] Basic GUI implementation with CustomTkinter.
- [x] Core downloading logic using Custom Engine (yt-dlp + mutagen).
- [x] Spotify metadata scraping using `spotify_scraper`.
- [x] Playlist support with folder organization.
- [x] Threading for responsive UI.
- [ ] Comprehensive error handling.
- [ ] Settings management (partially implemented).
- [ ] Unit tests for all modules.

## Next Steps

### Functionality & Core Logic
- [ ] **Cancel Functionality**: Allow users to gracefully stop a download session.
- [ ] **Retry Mechanism**: Option to retry failed downloads.
- [ ] **Audio Quality & Format Options**: Support for MP3/FLAC/M4A and quality selection.
- [ ] **Lyrics Embedding**: Embed lyrics or save as .lrc files.
- [ ] **History & Duplicate Prevention**: Track downloaded files to avoid duplicates.

### User Interface (GUI)
- [ ] **Settings Panel**: Manage default path, themes, and preferences.
- [ ] **Visual Feedback**: Display album art and detailed track progress (e.g., "Track 3 of 12").
- [ ] **System Tray Integration**: Notifications and minimize-to-tray support.

### Architecture & Code Quality
- [ ] **Structured Logging**: Replace print statements with proper file-based logging.
- [ ] **AsyncIO Migration**: Optimize concurrent operations.

### Distribution & DevOps
- [ ] **Executable Builder**: PyInstaller script for standalone .exe generation.
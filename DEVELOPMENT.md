# Spotify Downloader - Development Documentation

## Project Overview
This is a modern GUI-based application for downloading Spotify songs and playlists. The application has been significantly enhanced with security features, better architecture, and improved user experience.

## Current State & Architecture

### Core Components
- **GUI Layer**: Built with CustomTkinter for a modern UI
- **Service Layer**: Separates business logic from UI concerns
- **Core Engine**: Handles the actual download and tagging process
- **Utils**: Contains validation, error handling, and helper functions
- **Configuration**: Centralized app configuration management

### Key Improvements Made
1. **Security Enhancements**:
   - URL validation and sanitization
   - File path sanitization to prevent directory traversal
   - Safe URL validation for external resources
   - Configurable safe mode

2. **Architecture Improvements**:
   - Service-oriented architecture separating business logic from UI
   - Centralized configuration management
   - Proper separation of concerns

3. **Error Handling & Resilience**:
   - Comprehensive error handling utilities
   - Custom exception classes
   - Proper exception propagation and logging
   - Retry mechanisms and timeout handling

4. **User Experience**:
   - Progress indicators with percentage labels
   - Better error messaging
   - Configurable settings

## Dependencies & Compatibility

### Current Dependencies
- customtkinter
- pillow
- spotifyscraper (installs as spotify_scraper module)
- pytest
- requests
- yt-dlp
- mutagen
- urllib3

### Important Note About spotify_scraper
The application uses the `spotifyscraper` package which installs as the `spotify_scraper` module. Install it using:
```bash
pip install spotifyscraper
```

The package provides a `SpotifyClient` class that implements the following methods:
- `get_playlist_info(url)` - Returns playlist information
- `get_track_info(url)` - Returns track information
- `get_album_info(url)` - Returns album information

## Important Notes

### Spotify Integration
The application is designed to use the `spotify_scraper` library to fetch real Spotify data. However, due to the dependency issue mentioned above, the application may fall back to mock data in some cases.

### Path Handling
The application now properly handles both absolute and relative download paths:
- If an absolute path is provided, it's used directly
- If a relative path is provided, it's treated as a subdirectory of the current working directory
- All paths are validated to prevent directory traversal attacks

### Configuration
The application uses a `config.json` file for storing settings. Default settings include:
- `download_path`: "downloads" (relative to project directory)
- `max_concurrent_downloads`: 5
- `download_quality`: "320kbps"
- `file_format`: "mp3"
- `safe_mode`: true (enables extra security validations)

## Development Guidelines

### Adding New Features
1. Follow the service-oriented architecture pattern
2. Add proper validation and sanitization for all user inputs
3. Include comprehensive error handling
4. Update the configuration system if new settings are needed
5. Write unit tests for new functionality

### Security Considerations
1. Always validate and sanitize user inputs
2. Prevent directory traversal in file operations
3. Validate URLs before making network requests
4. Limit file sizes when downloading external resources
5. Use safe defaults for all configurable options

### Testing
- Unit tests are located in the `tests/` directory
- Run tests using `python run_tests.py` or `pytest tests/`
- Add new tests for any functionality changes

## Known Issues & Limitations

1. **Rate Limiting**: No explicit rate limiting implemented for API calls
2. **Spotify Anti-Bot Measures**: May encounter rate limiting or blocking by Spotify

## Future Improvements

1. **Authentication**: Add OAuth authentication for Spotify API access
2. **Advanced Features**: Add playlist preservation, advanced tagging, and format options
3. **Performance**: Implement caching and more sophisticated concurrency controls
4. **Monitoring**: Add more comprehensive logging and monitoring capabilities

## Running the Application

To run the application:
```bash
cd /path/to/Spotify_Downloader
python main.py
```

Make sure to install dependencies first:
```bash
pip install -r requirements.txt
```

## Troubleshooting

If the application fails to start:
1. Check that all dependencies are installed
2. Verify the `config.json` file has valid settings
3. Ensure FFmpeg is installed and in your PATH
4. Check that the download directory is writable
# Spotify Downloader

## Purpose
When a URL is given, the application follows this workflow:
1. Validate the URL
2. Classify the URL
3. Get track info from Spotify using Spotify_Scraper
4. Build a search query
5. Search YouTube
6. Get the best match
7. Download audio
8. Convert to desired format
9. Save to projectroot/downloads folder

## Library Documentation
- `spotify_scraper`: https://spotifyscraper.readthedocs.io/en/latest/

## Installation
```bash
pip install spotifyscraper yt-dlp requests mutagen
```

## Usage
```bash
python main.py <spotify_url> [quality] [format]
```

Examples:
```bash
# Download with default quality (192kbps) and format (mp3)
python main.py https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6

# Download with custom quality and format
python main.py https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M 320 mp3

# Download album with FLAC format
python main.py https://open.spotify.com/album/4eLPJUqiU5a7Eg5WtpHoa8 256 flac
```

## Features
- **Organized Download Structure**: Creates separate folders for each playlist/album with meaningful names
- **Track Numbering**: Properly names tracks with numbers (e.g., "01 - Track Name.mp3")
- **Progress Tracking**: Shows detailed progress with track numbers and estimated time remaining
- **Duplicate Prevention**: Skips tracks that have already been downloaded
- **Retry Mechanism**: Automatically retries failed downloads up to 3 times
- **Quality Options**: Supports multiple audio qualities: 128, 192, 256, 320 kbps with actual bitrate enforcement
- **Format Support**: Downloads in multiple formats: mp3 (default), m4a, wav, flac
- **Metadata Embedding**: Adds artist, album, and track number to downloaded files
- **Comprehensive Error Handling**: Built-in error detection and reporting for all workflow steps
- **Detailed Logging**: Full logging system with both console and file output for debugging
- **Network Resilience**: Timeout handling and retry mechanisms for network operations
- **Dependency Validation**: Automatic checking for required libraries at startup
- **File System Safety**: Permissions and space checks before file operations

## Quality Settings
The application now properly enforces audio bitrate during conversion:
- **128 kbps**: Smaller files with adequate quality
- **192 kbps**: Standard quality (default)
- **256 kbps**: High quality
- **320 kbps**: Maximum quality (near lossless)

## Components
- `main.py`: Orchestrates the entire process with comprehensive error handling
- `Spotify_Scraper.py`: Interfaces with the Spotify API library with API error handling
- `Url_Validator.py`: Validates and classifies Spotify URLs with detailed error messages
- `Youtube_query.py`: Searches and downloads audio from YouTube with download error handling and metadata embedding
- `downloads/`: Default directory for downloaded audio files (organized by playlist/album)
- `spotify_downloader.log`: Detailed log file for debugging

## Dependencies
- spotifyscraper: For accessing Spotify data without authentication
- yt-dlp: For downloading audio from YouTube
- requests: For HTTP requests
- mutagen: For embedding metadata in audio files

## Error Handling
The application includes robust error handling for:
- Invalid or unreachable Spotify URLs
- Network timeout issues
- Spotify API rate limits and connection problems
- YouTube search and download failures
- File system permission and space issues
- Missing dependencies
- Track not found on YouTube

## Workflow
The application connects all processes following the documented 9-step workflow to download Spotify tracks as audio files via YouTube. All error handling and debugging improvements maintain the exact same core functionality while adding enhanced user experience and reliability features.
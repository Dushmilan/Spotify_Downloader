# Spot-Downloader Desktop

A modern, secure GUI-based application for downloading Spotify songs and playlists, powered by `spotdl`.

## Features
- ✨ Modern, sleek GUI using `CustomTkinter`.
- 🔒 Enhanced security with URL validation and file sanitization.
- 🎵 Download single songs or entire playlists.
- 📂 Automatic file organization with configurable paths.
- 🚀 Multi-threaded downloads to keep the UI responsive.
- ⚙️ Configurable settings for download quality, format, and concurrency.
- 🛡️ Safe mode with extra security validations.
- 📊 Improved progress tracking and logging.
- 🛠️ Better error handling and resilience.

## Prerequisites
- **Python 3.8+**

## Installation
1. Clone the repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   That's it! FFmpeg is automatically installed via the `imageio-ffmpeg` package - no manual setup required.

   > **Note**: The application uses `spotifyscraper` which installs as the `spotify_scraper` module. This provides the SpotifyClient class needed to fetch real Spotify data.

## Usage
Run the application using:
```bash
python main.py
```

1. Paste a Spotify track or playlist URL into the input field.
2. Click **Download**.
3. Collected files will be saved in the configured download folder.
4. Click **Open Folder** to view your downloads.

## Configuration
The application supports various configuration options through `config.json`:
- `download_path`: Directory for downloaded files
- `max_concurrent_downloads`: Maximum number of simultaneous downloads
- `download_quality`: Audio quality (128kbps, 256kbps, 320kbps)
- `file_format`: Output format (mp3, flac, m4a)
- `retry_attempts`: Number of retry attempts for failed downloads
- `timeout_seconds`: Network timeout in seconds
- `safe_mode`: Enable extra security validations

## Architecture
The application follows a service-oriented architecture:
- `main.py`: Application entry point.
- `gui/`: Contains UI code with separation from business logic.
- `core/`: Core download engine and processing logic.
- `services/`: Business logic separated from UI concerns.
- `utils/`: Utility functions for validation, tagging, and error handling.
- `config.py`: Application configuration management.

## Security Features
- Input validation for Spotify URLs
- File path sanitization to prevent directory traversal
- Safe URL validation for external resources
- Configurable safe mode for enhanced security

## Structure
- `main.py`: Application entry point.
- `src/spot_downloader/`: Main application package
  - `gui/`: User interface components
  - `core/`: Core download functionality
  - `services/`: Business logic services
  - `utils/`: Utility functions
  - `config.py`: Configuration management
- `downloads/`: Default location for downloaded music.

## Troubleshooting

If you encounter issues:

1. **ModuleNotFoundError: No module named 'spotify_scraper'**: Make sure you've installed `spotifyscraper`:
   ```bash
   pip install spotifyscraper
   ```

2. **FFmpeg not found**: The app automatically uses bundled FFmpeg via `imageio-ffmpeg`. If you still see this error, try:
   ```bash
   pip install imageio-ffmpeg
   ```
   Alternatively, you can install FFmpeg manually and add it to your system PATH.

3. **Spotify anti-bot measures**: The application may occasionally be blocked by Spotify. Try reducing the number of concurrent downloads in the configuration.

4. **Permission errors**: Make sure the download directory is writable.

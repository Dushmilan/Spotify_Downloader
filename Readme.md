# Spot-Downloader Desktop

A modern GUI-based application for downloading Spotify songs and playlists, powered by a custom engine using `yt-dlp` and `spotify_scraper`.

## Features
- ✨ **Modern GUI**: Built with `CustomTkinter` for a sleek, dark-themed experience.
- 🎵 **Versatile Downloading**: Support for single tracks and entire playlists.
- 📂 **Smart Organization**: Automatically organizes downloads into folders by playlist or artist.
- 🚀 **High Performance**: Multi-threaded architecture ensures the UI remains responsive during downloads.
- 🏷️ **Auto-Tagging**: Metadata (Artist, Title, Album) is automatically embedded into MP3 files.

## Prerequisites
- **Python 3.8+**
- **FFmpeg**: Required for audio conversion and processing.
    - [Download FFmpeg](https://ffmpeg.org/download.html) and add it to your system PATH.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Spot-Downloader_Desktop.git
   cd Spot-Downloader_Desktop
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

**Run the application:**
```bash
python main.py
```

1. **Input URL**: Paste a Spotify track or playlist URL into the input field.
2. **Download**: Click the **Download** button.
3. **Locate Files**: Files are saved to the `downloads/` directory by default. You can change this location in the app.
4. **Open**: Click **Open Folder** to quickly access your downloaded music.

## Development

### Structure
- `main.py`: Entry point.
- `src/spot_downloader/`: Main package.
    - `gui/`: User Interface logic.
    - `core/`: Download engine and search logic.
    - `utils/`: Helper functions.
- `tests/`: Unit and integration tests.

### Running Tests
To run the test suite:
```bash
python run_tests.py
```
Or directly via pytest:
```bash
pytest
```

## Troubleshooting
- **FFmpeg not found**: Ensure FFmpeg is installed and added to your system's Environment Variables (PATH).
- **Download failed**: Check your internet connection. Some songs might not be available on YouTube Music (the search source).
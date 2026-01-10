# Spot-Downloader Desktop

## Project Overview
Spot-Downloader Desktop is a high-performance, GUI-based utility designed to facilitate the seamless acquisition of high-quality audio content from Spotify. Built with a focus on user experience and reliability, it leverages a custom engineering pipeline combining `yt-dlp` for robust media extraction and `spotify_scraper` for precise metadata retrieval. The application features a modern, responsive interface powered by `CustomTkinter`, ensuring a professional environment for managing music libraries.

**Key Capabilities:**
- **Intelligent Metadata Management**: Automatically tags files with accurate Artist, Title, Album, and Cover Art data.
- **Playlist Preservation**: Maintains the structural integrity of Spotify playlists by organizing downloads into dedicated directories.
- **Resilient Architecture**: Implements multi-threaded processing to maintain UI responsiveness during intensive I/O operations.
- **Cancel & Control**: Provides granular control over active tasks, including the ability to interrupt ongoing downloads.

## Installation

### Prerequisites
Ensure the following components are available in your environment:
- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **FFmpeg**: Essential for audio encoding and processing.
    - **Windows**: [Download](https://ffmpeg.org/download.html), extract, and add the `bin` folder to your System PATH.
    - **macOS**: `brew install ffmpeg`
    - **Linux**: `sudo apt install ffmpeg`

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/Spot-Downloader_Desktop.git
   cd Spot-Downloader_Desktop
   ```

2. **Initialize Environment**
   It is recommended to use a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

**Launch the Application**
Execute the entry point script from your terminal:
```bash
python main.py
```

**Operation Workflow**
1.  **Input Source**: Paste a valid Spotify Track or Playlist URL into the primary input field.
2.  **Execute Download**: Click the **Download** button to initialize the retrieval process.
    *   *Note: The application will identify the content type and begin processing.*
3.  **Monitor Progress**: Track the status via the integrated progress bar and real-time log console.
4.  **Task Management**: Use the **Cancel** button to halt operations if necessary.
5.  **Access Content**: Upon completion, files are available in the `downloads/` directory (or your custom selected path). Use **Open Folder** for immediate access.

## Features
- ✨ **Modern GUI**: Built with `CustomTkinter` for a sleek, dark-themed experience.
- 🎵 **Versatile Downloading**: Support for single tracks and entire playlists.
- 📂 **Smart Organization**: Automatically organizes downloads into folders by playlist or artist.
- 🚀 **High Performance**: Multi-threaded architecture ensures the UI remains responsive.
- 🏷️ **Auto-Tagging**: Metadata is automatically embedded into MP3 files.

## Development

### Structure
- `main.py`: Application entry point.
- `src/spot_downloader/`: Source code package.
    - `gui/`: User Interface implementation.
    - `core/`: Backend logic for search and download engines.
    - `utils/`: shared utilities and helpers.
- `tests/`: Automated test suite.

### Verification
To validate system integrity, execute the test suite:
```bash
python run_tests.py
```

## Troubleshooting
- **FFmpeg not found**: Verify FFmpeg is correctly added to your system's PATH environment variable.
- **Download failed**: Ensure a stable internet connection. Note that availability depends on YouTube Music matches.
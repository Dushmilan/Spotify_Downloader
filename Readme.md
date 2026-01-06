# Spot-Downloader Desktop

A modern GUI-based application for downloading Spotify songs and playlists, powered by `spotdl`.

## Features
- ✨ Modern, sleek GUI using `CustomTkinter`.
- 🎵 Download single songs or entire playlists.
- 📂 Automatic file organization.
- 🚀 Multi-threaded downloads to keep the UI responsive.

## Prerequisites
- **Python 3.7+**
- **FFmpeg**: Required by `spotdl` for audio conversion. 
    - [Download FFmpeg](https://ffmpeg.org/download.html) and add it to your system PATH.

## Installation
1. Clone the repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the application using:
```bash
python main.py
```

1. Paste a Spotify track or playlist URL into the input field.
2. Click **Download**.
3. Collected files will be saved in the `downloads/` folder in the project directory.
4. Click **Open Folder** to view your downloads.

## Structure
- `main.py`: Application entry point.
- `gui/`: Contains UI code.
- `core/`: Contains the download logic wrapper.
- `utils/`: Utility functions like FFmpeg checks.
- `downloads/`: Default location for downloaded music.

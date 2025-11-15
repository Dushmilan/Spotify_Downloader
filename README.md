# Spotify Downloader

This project enables you to download Spotify content as audio files by using a combination of web scraping and YouTube audio extraction.

## Core Idea

The project workflow is:
- Getting a URL of a Spotify link (track, album, or playlist)
- Categorizing the URL as Playlist/Track/Album
- Using SpotifyScraper to scrape information from the link
- Using yt-dlp to search for the song on YouTube
- Downloading the audio version
- Converting using ffmpeg
- Saving the file

## Libraries Used

- `spotifyscraper` - For extracting data from Spotify without authentication : https://spotifyscraper.readthedocs.io/en/latest/
- `yt-dlp` - For downloading audio from YouTube
- `ffmpeg` - For audio conversion and processing

## Tech Stack

- Python 3.x

## Prerequisites

1. Python 3.x installed
2. FFmpeg installed and available in your system PATH
3. Required Python packages (install using `pip install -r requirements.txt`)

## Installation

### Option 1: Direct usage
1. Clone or download this repository
2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
3. Make sure you have FFmpeg installed on your system
4. Run using: `python main.py <spotify_url>`

### Option 2: Install as CLI tool
1. Clone or download this repository
2. Navigate to the project directory
3. Install the package:
   ```
   pip install .
   ```
   Or for development (links to your source files):
   ```
   pip install -e .
   ```
4. Run using: `spotify-dl <spotify_url>`

## CLI Usage

### Direct execution:
```bash
python main.py [options] <Spotify_URL>
```

### Installed CLI:
```bash
spotify-dl [options] <Spotify_URL>
```

### Options
- `url`: Required. The Spotify URL to download
- `-o, --output`: Output directory (default: ./downloads)
- `--format`: Output audio format (choices: mp3, wav, flac, m4a; default: mp3)
- `-q, --quality`: Audio quality/bitrate (choices: 128k, 192k, 256k, 320k; default: 192k)
- `-v, --verbose`: Enable verbose output
- `--no-convert`: Skip format conversion (keep original format)

### Examples
```bash
# Download a single track
python main.py https://open.spotify.com/track/5lXIYaLm8l3E5jl92NpG0C
# Or if installed: spotify-dl https://open.spotify.com/track/5lXIYaLm8l3E5jl92NpG0C

# Download an album with high quality
python main.py https://open.spotify.com/album/2YMWkm1Xq6S46qq6pU1EYV -q 320k
# Or if installed: spotify-dl https://open.spotify.com/album/2YMWkm1Xq6S46qq6pU1EYV -q 320k

# Download a playlist to a custom directory
python main.py https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M -o ./my_music
# Or if installed: spotify-dl https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M -o ./my_music

# Download as WAV format with verbose output
python main.py https://open.spotify.com/track/5lXIYaLm8l3E5jl92NpG0C --format wav -v
# Or if installed: spotify-dl https://open.spotify.com/track/5lXIYaLm8l3E5jl92NpG0C --format wav -v
```

## Project Structure

```
Spotify_Downloader/
├── src/
│   ├── __init__.py
│   ├── spotify_downloader.py  # Main orchestrator class
│   ├── url_handler.py         # Parses and categorizes Spotify URLs
│   ├── spotify_handler.py     # Interfaces with SpotifyScraper library
│   ├── youtube_searcher.py    # Uses yt-dlp to search and download from YouTube
│   └── file_converter.py      # Handles audio conversion with ffmpeg
├── requirements.txt           # Python dependencies
├── main.py                   # Command-line entry point
├── setup.py                  # Setup script
├── .gitignore                # Git ignore file
└── README.md                 # This file
```

## How It Works

1. **URL Identification**: The URL handler parses the Spotify URL and determines if it's a track, album, or playlist.
2. **Metadata Extraction**: The Spotify handler extracts track information using the spotifyscraper library.
3. **YouTube Search**: The YouTube searcher finds the corresponding track on YouTube using the track name and artist.
4. **Audio Download**: Audio is downloaded from YouTube using yt-dlp.
5. **Format Conversion**: The audio is converted to the desired format using ffmpeg.
6. **File Saving**: The final audio file is saved to the specified output directory.

## Notes
- The project downloads audio from YouTube based on the track name and artist from Spotify.
- Actual results depend on the availability of the track on YouTube.
- Some Spotify URLs might have regional restrictions or require authentication, which could affect the scraping process.
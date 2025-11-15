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
pip install spotifyscraper yt-dlp requests
```

## Usage
```bash
python main.py <spotify_url>
```

Example:
```bash
python main.py https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6
```

## Components
- `main.py`: Orchestrates the entire process
- `Spotify_Scraper.py`: Interfaces with the Spotify API library
- `Url_Validator.py`: Validates and classifies Spotify URLs
- `Youtube_query.py`: Searches and downloads audio from YouTube
- `downloads/`: Default directory for downloaded audio files

## Dependencies
- spotifyscraper: For accessing Spotify data without authentication
- yt-dlp: For downloading audio from YouTube
- requests: For HTTP requests

## Workflow
The application connects all processes following the documented 9-step workflow to download Spotify tracks as audio files via YouTube.
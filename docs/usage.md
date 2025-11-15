# Usage

## Command Line Interface

```bash
# Download a single track
python -m spotify_downloader https://open.spotify.com/track/...

# Download an album
python -m spotify_downloader https://open.spotify.com/album/...

# Download a playlist
python -m spotify_downloader https://open.spotify.com/playlist/...

# Download with custom output directory and quality
python -m spotify_downloader https://open.spotify.com/album/... -o ./music -q 320k

# Download in different format
python -m spotify_downloader https://open.spotify.com/track/... --format wav
```

## Using the Python API

```python
from spotify_downloader.core.downloader import SpotifyDownloader

downloader = SpotifyDownloader(output_dir="./downloads", audio_format="mp3", audio_quality="192k")
downloader.download("https://open.spotify.com/track/...", verbose=True)
```
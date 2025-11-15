import yt_dlp
import os
from urllib.parse import quote

def create_query(track_name, artist_name):
    query = f"{track_name} {artist_name}"
    return query

def search_youtube_for_video(query):
    # Create download directory if it doesn't exist (Steps 8 & 9: Convert & Save)
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)

    # Create a YouTube search URL from the query
    search_url = f"ytsearch1:{query}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'postprocessor_args': [
            '-ar', '44100'  # Set audio rate
        ],
        'prefer_ffmpeg': True,
        'audioquality': '0',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),  # Save to downloads folder
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_url])

    return 0
    

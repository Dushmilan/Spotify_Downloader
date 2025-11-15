"""
Module to search for songs on YouTube using yt-dlp
"""

import yt_dlp
import re


class YouTubeSearcher:
    """
    Interface for searching and downloading from YouTube using yt-dlp
    """
    
    def __init__(self):
        """
        Initialize the YouTubeSearcher
        """
        pass
    
    def search_youtube(self, query, max_results=1):
        """
        Search for a song on YouTube and return video information
        
        Args:
            query (str): Search query (e.g., "artist name song title")
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of dictionaries containing video information
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'extract_flat': True,
            'max_results': max_results,
            'quiet': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_query = f"ytsearch{max_results}:{query}"
                result = ydl.extract_info(search_query, download=False)
                
                if 'entries' in result:
                    videos = []
                    for entry in result['entries']:
                        video_info = {
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': entry.get('webpage_url'),
                            'duration': entry.get('duration'),
                            'uploader': entry.get('uploader')
                        }
                        videos.append(video_info)
                    return videos
                else:
                    # If there's only one result, it might be returned directly
                    video_info = {
                        'id': result.get('id'),
                        'title': result.get('title'),
                        'url': result.get('webpage_url'),
                        'duration': result.get('duration'),
                        'uploader': result.get('uploader')
                    }
                    return [video_info]
        except Exception as e:
            raise Exception(f"Error searching YouTube: {e}")
    
    def download_audio(self, video_url, output_path):
        """
        Download audio from a YouTube video
        
        Args:
            video_url (str): URL of the YouTube video
            output_path (str): Path where the audio file should be saved
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'postprocessor_args': [
                '-ar', '44100'
            ],
            'prefer_ffmpeg': True,
            'audioquality': '0',
            'extractaudio': True,
            'audioformat': 'mp3',
            'keepvideo': False,
            'outtmpl': output_path,
            'quiet': False
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            raise Exception(f"Error downloading audio: {e}")
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, APIC, TRCK, COMM
from mutagen.mp4 import MP4, MP4Cover
import requests
from urllib.parse import urlparse
from .validation import is_safe_url

def tag_mp3(file_path, metadata):
    """
    Tags an MP3 file with metadata and album art.
    Track name is tagged first before any other metadata.
    """
    # Validate file path to prevent directory traversal
    if not file_path or not isinstance(file_path, str):
        print("Error: Invalid file path provided for tagging")
        return False

    # Check if file exists and is within allowed directories
    if not os.path.isfile(file_path):
        print(f"Error: File does not exist: {file_path}")
        return False

    # Verify file extension
    _, ext = os.path.splitext(file_path.lower())
    if ext != '.mp3':
        print(f"Error: File is not an MP3: {file_path}")
        return False

    try:
        audio = MP3(file_path, ID3=ID3)
        if audio is None:
            print(f"Error: Could not load MP3 file: {file_path}")
            return False

        try:
            audio.add_tags()
        except:
            pass

        tags = audio.tags
        
        # === TAG TRACK NAME FIRST ===
        name = metadata.get('name', '') if metadata.get('name') else ''
        print(f"Tagging track: {name}")
        tags.add(TIT2(encoding=3, text=str(name)))
        # === END TRACK NAME TAGGING ===

        # Process artists safely
        artists = metadata.get('artists', [])
        if isinstance(artists, list):
            artist_names = [str(a['name']) if isinstance(a, dict) and 'name' in a else str(a) for a in artists if a]
            artist_text = ", ".join(artist_names)
        else:
            artist_text = str(metadata.get('artist', ''))
        tags.add(TPE1(encoding=3, text=artist_text))

        # Use playlist_name as album if available (for playlist downloads), 
        # otherwise use the original album name
        album_name = metadata.get('playlist_name', '') or metadata.get('album', '') or metadata.get('album_name', '')
        tags.add(TALB(encoding=3, text=str(album_name)))

        # Add playlist name as comment if available (preserves original album)
        playlist_name = metadata.get('playlist_name', '') if metadata.get('playlist_name') else ''
        if playlist_name:
            tags.add(COMM(encoding=3, lang='eng', desc='Playlist', text=str(playlist_name)))

        year = metadata.get('year', '') if metadata.get('year') else ''
        tags.add(TYER(encoding=3, text=str(year)))

        track_number = metadata.get('track_number', '') if metadata.get('track_number') else ''
        tags.add(TRCK(encoding=3, text=str(track_number)))

        # Add lyrics if available
        if metadata.get('lyrics'):
            lyrics = metadata.get('lyrics', '')
            tags.add(COMM(encoding=3, lang='eng', desc='Lyrics', text=str(lyrics)))

        # Add Album Art
        cover_url = metadata.get('cover_url')
        if cover_url and is_safe_url(str(cover_url)):
            try:
                # Validate URL before requesting
                parsed_url = urlparse(str(cover_url))
                if parsed_url.scheme not in ['http', 'https']:
                    print("Error: Invalid URL scheme for album art")
                    return False

                response = requests.get(str(cover_url), timeout=10)
                if response.status_code == 200:
                    # Limit image size to prevent resource exhaustion
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                        print("Error: Album art exceeds size limit")
                        return False

                    img_data = response.content
                    # Verify it's an image before adding
                    if img_data and len(img_data) > 0:
                        tags.add(APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc=u'Cover',
                            data=img_data
                        ))
            except requests.exceptions.RequestException as e:
                print(f"Failed to download album art: {e}")
            except Exception as e:
                print(f"Failed to add album art: {e}")

        audio.save()
        return True
    except Exception as e:
        print(f"Error tagging MP3: {e}")
        return False

def tag_m4a(file_path, metadata):
    """
    Tags an M4A/MP4 file with metadata and album art.
    Track name is tagged first before any other metadata.
    """
    # Validate file path to prevent directory traversal
    if not file_path or not isinstance(file_path, str):
        print("Error: Invalid file path provided for tagging")
        return False

    # Check if file exists and is within allowed directories
    if not os.path.isfile(file_path):
        print(f"Error: File does not exist: {file_path}")
        return False

    # Verify file extension
    _, ext = os.path.splitext(file_path.lower())
    if ext not in ['.m4a', '.mp4']:
        print(f"Error: File is not an M4A/MP4: {file_path}")
        return False

    try:
        audio = MP4(file_path)
        if audio is None:
            print(f"Error: Could not load M4A/MP4 file: {file_path}")
            return False

        # === TAG TRACK NAME FIRST ===
        name = metadata.get('name', '') if metadata.get('name') else ''
        print(f"Tagging track: {name}")
        audio["\xa9nam"] = str(name)
        # === END TRACK NAME TAGGING ===

        # Process artists safely
        artists = metadata.get('artists', [])
        if isinstance(artists, list):
            artist_names = [str(a['name']) if isinstance(a, dict) and 'name' in a else str(a) for a in artists if a]
            artist_text = ", ".join(artist_names)
        else:
            artist_text = str(metadata.get('artist', ''))
        audio["\xa9ART"] = artist_text

        # Use playlist_name as album if available (for playlist downloads), 
        # otherwise use the original album name
        album_name = metadata.get('playlist_name', '') or metadata.get('album', '') or metadata.get('album_name', '')
        audio["\xa9alb"] = str(album_name)

        # Add playlist name as comment if available (preserves original album)
        playlist_name = metadata.get('playlist_name', '') if metadata.get('playlist_name') else ''
        if playlist_name:
            audio["\xa9cmt"] = str(playlist_name)

        year = metadata.get('year', '') if metadata.get('year') else ''
        audio["\xa9day"] = str(year)

        # Track number and total tracks (n, m)
        try:
            track_num = int(metadata.get('track_number', 1))
            total_tracks = int(metadata.get('track_count', 1))
            audio["trkn"] = [(track_num, total_tracks)]
        except (ValueError, TypeError):
            # If track numbers are invalid, skip them
            pass

        # Add Album Art
        cover_url = metadata.get('cover_url')
        if cover_url and is_safe_url(str(cover_url)):
            try:
                # Validate URL before requesting
                parsed_url = urlparse(str(cover_url))
                if parsed_url.scheme not in ['http', 'https']:
                    print("Error: Invalid URL scheme for album art")
                    return False

                response = requests.get(str(cover_url), timeout=10)
                if response.status_code == 200:
                    # Limit image size to prevent resource exhaustion
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                        print("Error: Album art exceeds size limit")
                        return False

                    img_data = response.content
                    # Verify it's an image before adding
                    if img_data and len(img_data) > 0:
                        audio["covr"] = [MP4Cover(img_data, imageformat=MP4Cover.FORMAT_JPEG)]
            except requests.exceptions.RequestException as e:
                print(f"Failed to download album art: {e}")
            except Exception as e:
                print(f"Failed to add album art: {e}")

        audio.save()
        return True
    except Exception as e:
        print(f"Error tagging M4A: {e}")
        return False

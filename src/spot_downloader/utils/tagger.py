import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, APIC, TRCK, COMM
from mutagen.mp4 import MP4, MP4Cover
import requests

def tag_mp3(file_path, metadata):
    """
    Tags an MP3 file with metadata and album art.
    """
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except:
            pass

        tags = audio.tags
        tags.add(TIT2(encoding=3, text=metadata.get('name', '')))
        artists = metadata.get('artists', [])
        if isinstance(artists, list):
            artist_names = [a['name'] if isinstance(a, dict) else a for a in artists]
            artist_text = ", ".join(artist_names)
        else:
            artist_text = metadata.get('artist', '')
        tags.add(TPE1(encoding=3, text=artist_text))
        tags.add(TALB(encoding=3, text=metadata.get('album_name', '')))
        tags.add(TYER(encoding=3, text=str(metadata.get('year', ''))))
        tags.add(TRCK(encoding=3, text=str(metadata.get('track_number', ''))))
        
        # Add lyrics if available
        if metadata.get('lyrics'):
            tags.add(COMM(encoding=3, lang='eng', desc='Lyrics', text=metadata.get('lyrics')))

        # Add Album Art
        cover_url = metadata.get('cover_url')
        if cover_url:
            try:
                img_data = requests.get(cover_url, timeout=10).content
                tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc=u'Cover',
                    data=img_data
                ))
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
    """
    try:
        audio = MP4(file_path)
        audio["\xa9nam"] = metadata.get('name', '')
        artists = metadata.get('artists', [])
        if isinstance(artists, list):
            artist_names = [a['name'] if isinstance(a, dict) else a for a in artists]
            artist_text = ", ".join(artist_names)
        else:
            artist_text = metadata.get('artist', '')
        audio["\xa9ART"] = artist_text
        audio["\xa9alb"] = metadata.get('album_name', '')
        audio["\xa9day"] = str(metadata.get('year', ''))
        
        # Track number and total tracks (n, m)
        track_num = int(metadata.get('track_number', 1))
        total_tracks = int(metadata.get('track_count', 1))
        audio["trkn"] = [(track_num, total_tracks)]

        # Add Album Art
        cover_url = metadata.get('cover_url')
        if cover_url:
            try:
                img_data = requests.get(cover_url, timeout=10).content
                audio["covr"] = [MP4Cover(img_data, imageformat=MP4Cover.FORMAT_JPEG)]
            except Exception as e:
                print(f"Failed to add album art: {e}")

        audio.save()
        return True
    except Exception as e:
        print(f"Error tagging M4A: {e}")
        return False

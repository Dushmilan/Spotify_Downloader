"""
Module to interface with SpotifyScraper library
"""

from spotifyscraper import Spotify


class SpotifyScraper:
    """
    Interface for scraping Spotify content using spotifyscraper library
    """
    
    def __init__(self):
        """
        Initialize the SpotifyScraper
        """
        self.spotify = Spotify()
    
    def get_track_info(self, track_id):
        """
        Get information for a single track
        
        Args:
            track_id (str): Spotify track ID
            
        Returns:
            dict: Track information including title, artist, album, etc.
        """
        try:
            track = self.spotify.track(track_id)
            return {
                'title': track.title,
                'artist': track.artist,
                'album': track.album,
                'duration': track.duration,
                'track_number': track.track_number,
                'disc_number': track.disc_number,
                'release_date': track.release_date,
                'popularity': track.popularity,
                'preview_url': track.preview_url
            }
        except Exception as e:
            raise Exception(f"Could not retrieve track info: {e}")
    
    def get_album_info(self, album_id):
        """
        Get information for an album and its tracks
        
        Args:
            album_id (str): Spotify album ID
            
        Returns:
            dict: Album information and list of tracks
        """
        try:
            album = self.spotify.album(album_id)
            tracks = []
            for track in album.tracks:
                tracks.append({
                    'title': track.title,
                    'artist': track.artist,
                    'album': track.album,
                    'duration': track.duration,
                    'track_number': track.track_number,
                    'disc_number': track.disc_number
                })
            
            return {
                'title': album.title,
                'artist': album.artist,
                'release_date': album.release_date,
                'total_tracks': album.total_tracks,
                'tracks': tracks
            }
        except Exception as e:
            raise Exception(f"Could not retrieve album info: {e}")
    
    def get_playlist_info(self, playlist_id):
        """
        Get information for a playlist and its tracks
        
        Args:
            playlist_id (str): Spotify playlist ID
            
        Returns:
            dict: Playlist information and list of tracks
        """
        try:
            playlist = self.spotify.playlist(playlist_id)
            tracks = []
            for track in playlist.tracks:
                tracks.append({
                    'title': track.title,
                    'artist': track.artist,
                    'album': track.album,
                    'duration': track.duration,
                    'track_number': track.track_number,
                    'disc_number': track.disc_number
                })
            
            return {
                'title': playlist.title,
                'owner': playlist.owner,
                'description': playlist.description,
                'total_tracks': playlist.total_tracks,
                'tracks': tracks
            }
        except Exception as e:
            raise Exception(f"Could not retrieve playlist info: {e}")
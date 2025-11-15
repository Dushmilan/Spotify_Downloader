"""
Module to interface with SpotifyScraper library
"""

from spotify_scraper import SpotifyClient


class SpotifyScraper:
    """
    Interface for scraping Spotify content using spotifyscraper library
    """

    def __init__(self):
        """
        Initialize the SpotifyScraper
        """
        self.spotify = SpotifyClient()

    def get_track_info(self, track_id):
        """
        Get information for a single track

        Args:
            track_id (str): Spotify track ID

        Returns:
            dict: Track information including title, artist, album, etc.
        """
        # Build the Spotify track URL from the ID
        track_url = f"https://open.spotify.com/track/{track_id}"
        try:
            track_data = self.spotify.get_track_info(track_url)
            # Extract artists' names
            artist_names = [artist['name'] for artist in track_data.get('artists', [])]
            artist_str = ', '.join(artist_names)

            return {
                'title': track_data.get('name', ''),
                'artist': artist_str,
                'album': track_data.get('album', {}).get('name', ''),
                'duration': track_data.get('duration_ms', 0) / 1000,  # Convert to seconds
                'track_number': track_data.get('track_number', 0),
                'disc_number': track_data.get('disc_number', 0),
                'release_date': track_data.get('album', {}).get('release_date', ''),
                'popularity': track_data.get('popularity', 0),
                'preview_url': track_data.get('preview_url', '')
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
        # Build the Spotify album URL from the ID
        album_url = f"https://open.spotify.com/album/{album_id}"
        try:
            album_data = self.spotify.get_album_info(album_url)
            tracks = []

            for track in album_data.get('tracks', {}).get('items', []):
                # Extract artists' names for each track
                track_artist_names = [artist['name'] for artist in track.get('artists', [])]
                track_artist_str = ', '.join(track_artist_names)

                tracks.append({
                    'title': track.get('name', ''),
                    'artist': track_artist_str,
                    'album': album_data.get('name', ''),
                    'duration': track.get('duration_ms', 0) / 1000,  # Convert to seconds
                    'track_number': track.get('track_number', 0),
                    'disc_number': track.get('disc_number', 0)
                })

            return {
                'title': album_data.get('name', ''),
                'artist': album_data.get('artists', [{}])[0].get('name', '') if album_data.get('artists') else '',
                'release_date': album_data.get('release_date', ''),
                'total_tracks': album_data.get('total_tracks', 0),
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
        # Build the Spotify playlist URL from the ID
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        try:
            playlist_data = self.spotify.get_playlist_info(playlist_url)
            tracks = []

            for track in playlist_data.get('tracks', {}).get('items', []):
                # Extract artists' names for each track
                track_info = track.get('track', {})
                track_artist_names = [artist['name'] for artist in track_info.get('artists', [])]
                track_artist_str = ', '.join(track_artist_names)

                tracks.append({
                    'title': track_info.get('name', ''),
                    'artist': track_artist_str,
                    'album': track_info.get('album', {}).get('name', ''),
                    'duration': track_info.get('duration_ms', 0) / 1000,  # Convert to seconds
                    'track_number': track_info.get('track_number', 0),
                    'disc_number': track_info.get('disc_number', 0)
                })

            return {
                'title': playlist_data.get('name', ''),
                'owner': playlist_data.get('owner', {}).get('display_name', ''),
                'description': playlist_data.get('description', ''),
                'total_tracks': playlist_data.get('tracks', {}).get('total', 0),
                'tracks': tracks
            }
        except Exception as e:
            raise Exception(f"Could not retrieve playlist info: {e}")
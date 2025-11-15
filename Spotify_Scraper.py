from spotify_scraper import SpotifyClient
import logging

logger = logging.getLogger(__name__)

# Initialize client
try:
    client = SpotifyClient()
except Exception as e:
    logger.error(f"Error initializing SpotifyClient: {str(e)}", exc_info=True)
    client = None

def get_track(track_url):
    """Get track information from Spotify with error handling."""
    try:
        if client is None:
            logger.error("SpotifyClient is not initialized")
            return None
        track = client.get_track_info(track_url)
        return track
    except Exception as e:
        logger.error(f"Error getting track info for {track_url}: {str(e)}", exc_info=True)
        return None

def get_playlist(playlist_url):
    """Get playlist information from Spotify with error handling."""
    try:
        if client is None:
            logger.error("SpotifyClient is not initialized")
            return None
        playlist = client.get_playlist_info(playlist_url)
        return playlist
    except Exception as e:
        logger.error(f"Error getting playlist info for {playlist_url}: {str(e)}", exc_info=True)
        return None

def get_album(album_url):
    """Get album information from Spotify with error handling."""
    try:
        if client is None:
            logger.error("SpotifyClient is not initialized")
            return None
        album = client.get_album_info(album_url)
        return album
    except Exception as e:
        logger.error(f"Error getting album info for {album_url}: {str(e)}", exc_info=True)
        return None

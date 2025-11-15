from spotify_scraper import SpotifyClient

# Initialize client
client = SpotifyClient()

def get_track(track_url):
    track = client.get_track_info(track_url)
    return track

def get_playlist(playlist_url):
    playlist = client.get_playlist_info(playlist_url)
    return playlist

def get_album(album_url):
    album = client.get_album_info(album_url)
    return album

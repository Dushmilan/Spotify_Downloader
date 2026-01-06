from spotify_scraper import SpotifyClient
import json

def test_playlist_scrape():
    url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" # Today's Top Hits (Example)
    print(f"Testing playlist scrape: {url}")
    
    try:
        client = SpotifyClient()
        info = client.get_playlist_info(url)
        
        if info:
            print(f"Playlist Found: {info.get('name')}")
            tracks = info.get('tracks', [])
            print(f"Track count: {len(tracks)}")
            if tracks:
                print("First track sample:")
                print(tracks[0])
        else:
            print("No info returned.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_playlist_scrape()

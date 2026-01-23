import requests
import re
import urllib.parse
import json
import time
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class YouTubeSearcher:
    @staticmethod
    def search_ytm(query, duration_ms=None):
        """
        Searches YouTube Music for the best matching audio track.
        Prioritizes 'Official Audio' and matches duration.
        """
        # Validate input
        if not query or not isinstance(query, str):
            return None

        # Limit query length to prevent abuse
        query = query.strip()[:200]
        if not query:
            return None

        print(f"Searching YTM for: {query}")

        # We use a specific search query to target YTM 'songs' category
        search_query = f"{query} official audio"
        encoded_query = urllib.parse.quote(search_query)

        # Using the standard YT search with filters or YTM-specific data if possible
        # For now, we use a robust YT search regex fallback as a pure-requests approach
        # is more stable than depending on fickle YTM libraries.

        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Create a session with retry strategy
        session = requests.Session()

        # Define retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            response = session.get(search_url, headers=headers, timeout=15)
            if response.status_code != 200:
                return None

            # Extract video data from the initialData JSON in the page source
            pattern = r'var ytInitialData = (\{.*?\});'
            match = re.search(pattern, response.text)
            if not match:
                return None

            data = json.loads(match.group(1))

            # Navigate the complex YT JSON structure
            videos = []
            try:
                contents = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
            except KeyError:
                try:
                    contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
                except KeyError:
                    return None

            for item in contents:
                if 'videoRenderer' in item:
                    video = item['videoRenderer']

                    # Validate that required fields exist
                    if 'title' not in video or 'runs' not in video['title'] or not video['title']['runs']:
                        continue

                    title = video['title']['runs'][0]['text']
                    video_id = video.get('videoId')

                    if not video_id:  # Skip if video ID is missing
                        continue

                    # Try to get duration
                    duration_text = video.get('lengthText', {}).get('simpleText', "0:00")
                    # Convert "MM:SS" to seconds
                    parts = duration_text.split(':')
                    secs = 0
                    if len(parts) == 2:
                        try:
                            secs = int(parts[0]) * 60 + int(parts[1])
                        except ValueError:
                            secs = 0  # Default to 0 if parsing fails
                    elif len(parts) == 3:
                        try:
                            secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        except ValueError:
                            secs = 0  # Default to 0 if parsing fails

                    videos.append({
                        'id': video_id,
                        'title': title,
                        'duration_secs': secs,
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })

            # --- MATCHING LOGIC ---
            if not videos:
                return None

            if duration_ms:
                target_secs = duration_ms / 1000
                matches = []

                for v in videos[:10]: # Check top 10 results
                    diff = abs(v['duration_secs'] - target_secs)

                    # Ignore extreme mismatches (mixes or snippets)
                    if diff > 60: # More than 1 minute difference is suspicious for a single track
                        continue

                    score = diff
                    # Reward "Official Audio" or "Topic" in title
                    title_lower = v['title'].lower()
                    if "official audio" in title_lower or "topic" in title_lower:
                        score *= 0.5 # Strong bias towards official versions

                    matches.append((score, v))

                if matches:
                    matches.sort(key=lambda x: x[0])
                    best_match = matches[0][1]
                    best_score = matches[0][0]

                    if best_score > 20:
                        print(f"Warning: Best match score is high: {best_score}")

                    return best_match['url']

            # Fallback to first result if no duration or no good matches
            return videos[0]['url']

        except json.JSONDecodeError:
            print("Search error: Invalid JSON response")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Search error: Network request failed - {e}")
            return None
        except Exception as e:
            print(f"Search error: {e}")
            return None
        finally:
            session.close()  # Clean up the session

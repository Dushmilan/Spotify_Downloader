import requests
import re
import urllib.parse
import json
import time
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from ..config import app_config
from ..utils.logger import get_logger
from ..utils.retry import retry

logger = get_logger(__name__)

# Shared session for connection pooling
_search_session = None

def _get_search_session():
    """Get or create shared search session with retry configuration."""
    global _search_session
    if _search_session is None:
        _search_session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        _search_session.mount("http://", adapter)
        _search_session.mount("https://", adapter)
    return _search_session

class YouTubeSearcher:
    @staticmethod
    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(requests.RequestException,))
    def _fetch_search_results(search_url, headers):
        """Fetch search results with retry logic."""
        session = _get_search_session()
        response = session.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text

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

        logger.debug(f"Searching YTM for: {query}")

        # We use a specific search query to target YTM 'songs' category
        search_query = f"{query} official audio"
        encoded_query = urllib.parse.quote(search_query)

        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response_text = YouTubeSearcher._fetch_search_results(search_url, headers)
            
            # Extract video data from the initialData JSON in the page source
            pattern = r'var ytInitialData = (\{.*?\});'
            match = re.search(pattern, response_text)
            if not match:
                logger.warning("No ytInitialData found in response")
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
                    logger.warning("Could not parse video contents from response")
                    return None

            for item in contents:
                if 'videoRenderer' in item:
                    video = item['videoRenderer']

                    # Validate that required fields exist
                    if 'title' not in video or 'runs' not in video['title'] or not video['title']['runs']:
                        continue

                    title = video['title']['runs'][0]['text']
                    video_id = video.get('videoId')

                    if not video_id:
                        continue

                    # Try to get duration
                    duration_text = video.get('lengthText', {}).get('simpleText', "0:00")
                    parts = duration_text.split(':')
                    secs = 0
                    if len(parts) == 2:
                        try:
                            secs = int(parts[0]) * 60 + int(parts[1])
                        except ValueError:
                            secs = 0
                    elif len(parts) == 3:
                        try:
                            secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        except ValueError:
                            secs = 0

                    videos.append({
                        'id': video_id,
                        'title': title,
                        'duration_secs': secs,
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })

            if not videos:
                logger.warning("No videos found in search results")
                return None

            if duration_ms:
                target_secs = duration_ms / 1000
                matches = []

                for v in videos[:10]:
                    diff = abs(v['duration_secs'] - target_secs)

                    if diff > 60:
                        continue

                    score = diff
                    title_lower = v['title'].lower()
                    if "official audio" in title_lower or "topic" in title_lower:
                        score *= 0.5

                    matches.append((score, v))

                if matches:
                    matches.sort(key=lambda x: x[0])
                    best_match = matches[0][1]
                    best_score = matches[0][0]

                    if best_score > 20:
                        logger.debug(f"Warning: Best match score is high: {best_score}")

                    return best_match['url']

            return videos[0]['url']

        except json.JSONDecodeError as e:
            logger.error(f"Search error: Invalid JSON response - {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Search error: Network request failed - {e}")
            return None
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None

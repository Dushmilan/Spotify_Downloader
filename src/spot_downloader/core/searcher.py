import yt_dlp

class YouTubeSearcher:
    @staticmethod
    def search_ytm(query, duration_ms=None):
        """
        Searches YouTube for the best matching audio track using yt-dlp.
        Prioritizes 'Official Audio' and matches duration.
        """
        print(f"Searching YouTube for: {query}")
        search_query = f"ytsearch5:{query} official audio"
        
        ydl_opts = {
            'quiet': True,
            'default_search': 'ytsearch5',
            'skip_download': True,
            'no_warnings': True,
            'extract_flat': True, # Faster, only gets metadata
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
            if not info or 'entries' not in info:
                return None
            
            videos = []
            for entry in info['entries']:
                if not entry: continue
                
                videos.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'duration_secs': entry.get('duration', 0),
                    'url': entry.get('url') or entry.get('webpage_url')
                })

            # --- MATCHING LOGIC ---
            if not videos:
                return None

            if duration_ms:
                target_secs = duration_ms / 1000
                matches = []
                
                for v in videos:
                    duration = v.get('duration_secs')
                    if not duration:
                        continue
                        
                    diff = abs(duration - target_secs)
                    
                    # Ignore extreme mismatches (mixes or snippets)
                    if diff > 60: 
                        continue
                    
                    score = diff
                    # Reward "Official Audio" or "Topic" in title
                    title_lower = v['title'].lower()
                    if "official audio" in title_lower or "topic" in title_lower:
                        score *= 0.5 
                    
                    matches.append((score, v))
                
                if matches:
                    matches.sort(key=lambda x: x[0])
                    best_match = matches[0][1]
                    return best_match['url']
            
            # Fallback to first result
            return videos[0]['url']

        except Exception as e:
            print(f"Search error: {e}")
            return None

import os
import requests
import urllib.parse

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def youtube_search(query, max_results=5):
    """Search YouTube for educational videos and return a list of video dicts"""
    try:
        clean_query = query.strip()
        if not clean_query or not YOUTUBE_API_KEY:
            return []
        # Add educational keywords to improve search results
        educational_keywords = ["education", "learning", "lesson", "tutorial"]
        search_query = f"{clean_query} {' '.join(educational_keywords[:2])}"
        url = (
            f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video"
            f"&q={urllib.parse.quote(search_query)}"
            f"&maxResults={max_results}"
            f"&key={YOUTUBE_API_KEY}"
            f"&safeSearch=strict"
        )
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        videos = []
        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            videos.append({
                "id": video_id,
                "title": snippet["title"],
                "thumbnail": snippet["thumbnails"]["medium"]["url"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": snippet.get("channelTitle", "")
            })
        return videos
    except Exception as e:
        print(f"Error in YouTube search: {e}")
        return [] 

from yt_dlp import YoutubeDL

def get_latest_videos(channel_url, limit=3):
    ydl_opts = {'quiet': True, 'skip_download': True, 'extract_flat': True}
    with YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(channel_url, download=False)
        entries = data.get('entries', []) or data.get('_entries', [])
        return [v['url'] for v in entries[:limit]]

def search_videos(query, limit=2):
    search_url = f"ytsearch{limit}:{query}"
    with YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        info = ydl.extract_info(search_url, download=False)
        return [v['url'] for v in info.get('entries', [])]

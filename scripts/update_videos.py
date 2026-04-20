
import os
import subprocess
from datetime import datetime
from scripts.utils import read_lines, ensure_dir
from scripts.search_youtube import get_latest_videos, search_videos

VIDEOS_DIR = "videos"
CONFIG_DIR = "config/channels.txt"
QUERIES_FILE = "queries/search_queries.txt"

def download_video(url, output_dir=VIDEOS_DIR):
    cmd = ["yt-dlp", "-o", f"{output_dir}/%(uploader)s_%(title)s.%(ext)s", url]
    subprocess.run(cmd, check=False)

def main():
    ensure_dir(VIDEOS_DIR)
    channels = read_lines(CONFIG_DIR)
    for ch in channels:
        if ch.startswith("#") or not ch.strip():
            continue
        print(f"[+] Fetching latest videos from {ch}")
        for video_url in get_latest_videos(ch, limit=2):
            download_video(video_url)
    queries = read_lines(QUERIES_FILE)
    for q in queries:
        if not q.strip():
            continue
        print(f"[+] Searching for: {q}")
        for video_url in search_videos(q, limit=1):
            download_video(video_url)
    print(f"✅ Completed at {datetime.now()}")

if __name__ == "__main__":
    main()

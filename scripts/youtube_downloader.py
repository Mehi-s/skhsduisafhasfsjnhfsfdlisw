#!/usr/bin/env python3
"""
YouTube Video Downloader using yt-dlp with proxy support
Processes commands from commands.txt file
Supports commands with optional ::reqid::<id> for custom output filenames:
    search economy ::reqid::abc-123   → results/search_economy_abc-123.txt
    recent @mkbhd ::reqid::xyz        → results/recent_mkbhd_xyz.txt
"""

import yt_dlp
import os
import re
import json
import subprocess
import random
import time
from pathlib import Path
from datetime import datetime

# Configuration
COMMANDS_FILE = "../commands.txt"
RESULTS_DIR = "../results"
DOWNLOAD_DIR = "../results/downloads"

# Proxy configuration - using rotating user agents instead of proxies for GitHub Actions
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
]


def setup_directories():
    """Create necessary directories"""
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)


def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    return random.choice(USER_AGENTS)


def parse_reqid(command_args):
    """
    Extract optional ::reqid::<id> from the end of command arguments.
    Returns (clean_args, reqid) where reqid is None if not present.
    """
    parts = command_args.rsplit('::reqid::', 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return command_args, None


def search_videos(query, max_results=10, reqid=None):
    """Search YouTube for videos with anti-detection, optional request ID for output"""
    print(f"\n🔍 Searching for: {query}")
    if reqid:
        print(f"   Request ID: {reqid}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'user_agent': get_random_user_agent(),
        'sleep_interval': random.uniform(1, 2),
    }

    results = []
    try:
        time.sleep(random.uniform(1, 2))

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{query}"
            info = ydl.extract_info(search_query, download=False)

            if 'entries' in info:
                for entry in info['entries']:
                    result = {
                        'title': entry.get('title', 'N/A'),
                        'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                        'duration': entry.get('duration', 0),
                        'views': entry.get('view_count', 0),
                        'uploader': entry.get('uploader', 'N/A')
                    }
                    results.append(result)

        # Build safe filename from query and optional reqid
        safe_query = re.sub(r'[^\w\-]', '_', query).strip('_')
        if reqid:
            safe_reqid = re.sub(r'[^\w\-]', '_', reqid).strip('_')
            file_base = f"search_{safe_query}_{safe_reqid}"
        else:
            file_base = f"search_{safe_query}"

        json_file = Path(RESULTS_DIR) / f"{file_base}.json"
        txt_file = Path(RESULTS_DIR) / f"{file_base}.txt"

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Search Results for: {query}")
            if reqid:
                f.write(f"  [ReqID: {reqid}]")
            f.write(f"\n{'='*60}\n\n")
            for i, result in enumerate(results, 1):
                f.write(f"{i}. {result['title']}\n")
                f.write(f"   URL: {result['url']}\n")
                f.write(f"   Channel: {result['uploader']}\n")
                f.write(f"   Duration: {result['duration']} seconds\n")
                f.write(f"   Views: {result['views']:,}\n\n")

        print(f"✅ Search results saved to: {json_file} and {txt_file}")
        return results

    except Exception as e:
        print(f"❌ Error searching: {str(e)}")
        return []


def get_recent_videos_alternative(channel_url, count=10):
    """Alternative method using search to get recent videos"""
    results = []
    try:
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if not channel_url.startswith('http'):
                channel_url = f"https://youtube.com/@{channel_url.replace('@','')}"
            info = ydl.extract_info(channel_url, download=False)
            channel_name = info.get('uploader', info.get('channel', info.get('title', '')))

            if channel_name:
                search_query = f"from:{channel_name}"
                search_url = f"ytsearch{count}:{search_query}"
                search_info = ydl.extract_info(search_url, download=False)
                if 'entries' in search_info:
                    for entry in search_info['entries']:
                        if entry:
                            result = {
                                'title': entry.get('title', 'N/A'),
                                'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                                'video_id': entry.get('id', ''),
                                'duration': entry.get('duration', 0),
                                'views': entry.get('view_count', 0),
                                'upload_date': entry.get('upload_date', 'N/A'),
                                'uploader': channel_name
                            }
                            results.append(result)
    except Exception as e:
        print(f"  Alternative method failed: {str(e)}")
    return results


def get_recent_videos(channel_url, count=10, reqid=None):
    """Get recent videos from a channel, optional request ID for output"""
    print(f"\n📺 Getting recent videos from: {channel_url}")
    if reqid:
        print(f"   Request ID: {reqid}")

    # Normalize channel URL and prepare different approaches
    original_channel = channel_url
    approaches = []
    if not channel_url.startswith('http'):
        clean_channel = channel_url.replace('@', '')
        approaches = [
            f"https://www.youtube.com/@{clean_channel}/videos",
            f"https://www.youtube.com/c/{clean_channel}/videos",
            f"https://www.youtube.com/channel/{clean_channel}/videos",
            f"https://www.youtube.com/@{clean_channel}",
            f"https://www.youtube.com/{clean_channel}/videos",
        ]
    else:
        if '/videos' not in channel_url:
            channel_url = channel_url.rstrip('/') + '/videos'
        approaches = [channel_url]

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': 'in_playlist',
    }
    results = []

    for url in approaches:
        if len(results) >= count:
            break
        print(f"  Trying: {url}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                entries = []
                if 'entries' in info:
                    entries = info['entries']
                elif 'videos' in info:
                    entries = info['videos']
                else:
                    uploads_id = info.get('uploader_id') or info.get('channel_id')
                    if uploads_id:
                        uploads_playlist = f"https://www.youtube.com/channel/{uploads_id}/videos"
                        info2 = ydl.extract_info(uploads_playlist, download=False)
                        if 'entries' in info2:
                            entries = info2['entries']

                for entry in entries:
                    if entry is None or len(results) >= count:
                        continue
                    video_id = entry.get('id', '')
                    if '/' in video_id:
                        video_id = video_id.split('/')[-1]
                    video_url = entry.get('url') or (f"https://youtube.com/watch?v={video_id}" if video_id else '')
                    if not video_url:
                        continue
                    result = {
                        'title': entry.get('title', 'N/A'),
                        'url': video_url,
                        'video_id': video_id,
                        'duration': entry.get('duration', 0),
                        'views': entry.get('view_count', 0),
                        'upload_date': entry.get('upload_date', 'N/A'),
                        'uploader': info.get('uploader', entry.get('uploader', 'N/A'))
                    }
                    results.append(result)
        except Exception as e:
            print(f"  Failed with error: {str(e)}")
            continue

    # Alternative method if needed
    if len(results) < count:
        print(f"  Only got {len(results)} videos, trying alternative method...")
        alt_results = get_recent_videos_alternative(original_channel, count)
        existing_urls = {r['url'] for r in results}
        for r in alt_results:
            if r['url'] not in existing_urls and len(results) < count:
                results.append(r)

    # Save results with optional reqid in filename
    if results:
        safe_channel = re.sub(r'[^\w\-]', '_', original_channel).strip('_')
        if reqid:
            safe_reqid = re.sub(r'[^\w\-]', '_', reqid).strip('_')
            file_base = f"recent_{safe_channel}_{safe_reqid}"
        else:
            file_base = f"recent_{safe_channel}"

        json_file = Path(RESULTS_DIR) / f"{file_base}.json"
        txt_file = Path(RESULTS_DIR) / f"{file_base}.txt"

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Recent Videos from: {original_channel}")
            if reqid:
                f.write(f"  [ReqID: {reqid}]")
            f.write(f"\nRequested: {count} videos | Found: {len(results)} videos\n")
            f.write(f"{'='*60}\n\n")
            for i, result in enumerate(results, 1):
                f.write(f"{i}. {result['title']}\n")
                f.write(f"   URL: {result['url']}\n")
                f.write(f"   Video ID: {result['video_id']}\n")
                f.write(f"   Upload Date: {result['upload_date']}\n")
                f.write(f"   Duration: {result['duration']} seconds\n")
                if result['views']:
                    f.write(f"   Views: {result['views']:,}\n")
                f.write("\n")

        print(f"✅ Found {len(results)} recent videos (requested {count})")
    else:
        print(f"❌ No videos found")

    return results


def read_commands():
    """Read and parse commands from commands.txt, supporting ::reqid::"""
    commands = []
    if not os.path.exists(COMMANDS_FILE):
        print(f"Commands file not found: {COMMANDS_FILE}")
        return commands

    with open(COMMANDS_FILE, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Parse command type and argument
        if line.startswith('search '):
            args = line[7:].strip()
            query, reqid = parse_reqid(args)
            commands.append(('search', query, reqid))
        elif line.startswith('download '):
            url = line[9:].strip()
            # download doesn't need reqid in this example, but you can extend if desired
            commands.append(('download', url, None))
        elif line.startswith('recent '):
            args = line[7:].strip()
            clean_args, reqid = parse_reqid(args)
            commands.append(('recent', clean_args, reqid))
        elif line.startswith('playlist '):
            url = line[9:].strip()
            commands.append(('playlist', url, None))

    return commands


def process_commands():
    """Process all commands from the commands file"""
    print("🚀 YouTube Video Downloader Started (Anti-Detection Mode)")
    print("="*50)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Commands file: {COMMANDS_FILE}")
    print("="*50)

    setup_directories()
    commands = read_commands()

    if not commands:
        print("\n⚠️  No commands found in commands.txt")
        print("\n📝 Example commands.txt content:")
        print("#" + "="*60)
        print("# Search for videos (optional ::reqid:: at end)")
        print("search python tutorial 2024 ::reqid::tut-001")
        print("\n# Download a single video")
        print("download https://youtube.com/watch?v=VIDEO_ID")
        print("\n# Get 15 recent videos from a channel (with optional reqid)")
        print("recent 15 @mkbhd ::reqid::recent-mkbhd")
        print("\n# Download a playlist")
        print("playlist https://youtube.com/playlist?list=PLAYLIST_ID")
        print("#" + "="*60)
        return

    print(f"\n📋 Found {len(commands)} command(s) to process\n")

    for idx, cmd in enumerate(commands, 1):
        cmd_type = cmd[0]
        cmd_value = cmd[1]
        reqid = cmd[2] if len(cmd) > 2 else None

        print(f"[{idx}/{len(commands)}] Processing: {cmd_type} {cmd_value}" + (f" [ReqID: {reqid}]" if reqid else ""))

        if cmd_type == 'search':
            search_videos(cmd_value, reqid=reqid)
        elif cmd_type == 'download':
            # Placeholder for download function (not included here for brevity)
            print(f"   Downloading: {cmd_value}")
            # download_video_with_proxy(cmd_value) would be called here
        elif cmd_type == 'recent':
            # Handle count if present, e.g., "15 @mkbhd"
            parts = cmd_value.split()
            if len(parts) >= 2 and parts[0].isdigit():
                count = int(parts[0])
                channel = ' '.join(parts[1:])
                get_recent_videos(channel, count, reqid=reqid)
            else:
                get_recent_videos(cmd_value, 10, reqid=reqid)
        elif cmd_type == 'playlist':
            print(f"   Processing playlist: {cmd_value}")
            # download_playlist(cmd_value) would be called here
        else:
            print(f"⚠️  Unknown command type: {cmd_type}")

        # Delay between commands
        if idx < len(commands):
            delay = random.uniform(5, 10)
            print(f"\n⏳ Waiting {delay:.1f} seconds before next command...")
            time.sleep(delay)
        print("-"*50)

    # Summary
    print("\n" + "="*50)
    print("✅ All commands processed successfully!")
    print(f"📁 Results saved in: {RESULTS_DIR}")
    result_files = list(Path(RESULTS_DIR).glob("*"))
    if result_files:
        print(f"\n📄 Generated files ({len(result_files)}):")
        for f in result_files[:10]:
            size = f.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024*1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            print(f"   - {f.name} ({size_str})")
        if len(result_files) > 10:
            print(f"   ... and {len(result_files)-10} more files")
    print("="*50)


def main():
    """Main entry point"""
    process_commands()


if __name__ == "__main__":
    main()

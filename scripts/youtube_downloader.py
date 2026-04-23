#!/usr/bin/env python3
"""
YouTube Video Downloader with Cookie Support
Uses cookies when available, falls back to anti-detection methods
"""

import yt_dlp
import os
import re
import json
import subprocess
import random
import time
import base64
from pathlib import Path
from datetime import datetime

# Configuration
COMMANDS_FILE = "../commands.txt"
RESULTS_DIR = "../results"
DOWNLOAD_DIR = "../results/downloads"
COOKIES_FILE = os.environ.get('YOUTUBE_COOKIES_FILE', 'cookies.txt')

def setup_directories():
    """Create necessary directories"""
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

def load_cookies_from_env():
    """Load cookies from environment variable or file"""
    # Try environment variable first (for GitHub Actions secrets)
    cookies_env = os.environ.get('YOUTUBE_COOKIES')
    if cookies_env:
        print("📦 Loading cookies from environment variable...")
        try:
            # Write cookies to temp file
            with open(COOKIES_FILE, 'w') as f:
                f.write(cookies_env)
            print("✅ Cookies loaded from environment")
            return True
        except Exception as e:
            print(f"❌ Failed to write cookies: {e}")
            return False
    
    # Try local file
    if os.path.exists(COOKIES_FILE):
        print("📄 Using local cookies file...")
        return True
    
    print("⚠️ No cookies found, will use anti-detection methods")
    return False

def download_with_cookies(url):
    """Download using yt-dlp with cookies"""
    print(f"\n📥 Downloading with cookies: {url}")
    
    output_template = f"{DOWNLOAD_DIR}/%(title).100s_%(id)s.%(ext)s"
    
    ydl_opts = {
        'format': 'worstvideo+worstaudio/worst[height>=144]',
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'restrictfilenames': True,
        'windowsfilenames': True,
        
        # Use cookies file
        'cookiefile': COOKIES_FILE,
        
        # Basic anti-detection
        'sleep_interval': random.uniform(2, 5),
        'sleep_interval_requests': random.uniform(1, 3),
        'max_sleep_interval': 10,
        
        # Retry configuration
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        
        # Use browser-like headers
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0',
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        },
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                print(f"✅ Downloaded: {title} ({duration}s)")
                
                # Remove cookies file after successful download for security
                if os.path.exists(COOKIES_FILE) and os.environ.get('YOUTUBE_COOKIES'):
                    os.remove(COOKIES_FILE)
                    print("🔒 Cookies file removed for security")
                
                return True
    except Exception as e:
        error_msg = str(e)
        if "Sign in" in error_msg or "bot" in error_msg.lower():
            print(f"❌ Cookies may be expired or invalid: {error_msg[:100]}")
        else:
            print(f"❌ Error: {error_msg[:200]}")
        return False

def download_without_cookies(url):
    """Download using anti-detection methods (fallback)"""
    print(f"\n🔄 Trying without cookies: {url}")
    
    output_template = f"{DOWNLOAD_DIR}/%(title).100s_%(id)s.%(ext)s"
    
    # Try multiple client types
    clients_to_try = [
        ['android', 'ios'],
        ['web', 'android'],
        ['android_tv'],
    ]
    
    for client_list in clients_to_try:
        print(f"  Trying clients: {client_list}")
        
        ydl_opts = {
            'format': 'worstvideo+worstaudio/worst[height>=144]',
            'outtmpl': output_template,
            'quiet': False,
            'restrictfilenames': True,
            
            'extractor_args': {
                'youtube': {
                    'player_client': client_list,
                    'skip': ['hls', 'dash'],
                }
            },
            
            'sleep_interval': random.uniform(5, 10),
            'sleep_interval_requests': random.uniform(3, 7),
            'throttledratelimit': 100000,
            
            'user_agent': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36',
            
            'retries': 15,
            'fragment_retries': 15,
            'skip_unavailable_fragments': True,
            'ignoreerrors': True,
            'force_ipv4': True,
        }
        
        try:
            time.sleep(random.uniform(5, 10))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    print(f"✅ Downloaded: {info.get('title')}")
                    return True
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:100]}")
            continue
    
    return False

def search_videos(query, max_results=10):
    """Search YouTube with cookie support"""
    print(f"\n🔍 Searching: {query}")
    
    has_cookies = os.path.exists(COOKIES_FILE)
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'sleep_interval': random.uniform(1, 3),
    }
    
    if has_cookies:
        ydl_opts['cookiefile'] = COOKIES_FILE
        ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0'
    else:
        ydl_opts['user_agent'] = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36'
    
    results = []
    try:
        time.sleep(random.uniform(2, 4))
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{query}"
            info = ydl.extract_info(search_query, download=False)
            
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        results.append({
                            'title': entry.get('title', 'N/A'),
                            'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                            'duration': entry.get('duration', 0),
                            'views': entry.get('view_count', 0),
                            'uploader': entry.get('uploader', 'N/A')
                        })
        
        # Save results
        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(RESULTS_DIR) / f"search_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # Text summary
            text_file = Path(RESULTS_DIR) / f"search_{timestamp}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"Search: {query}\n{'='*50}\n\n")
                for i, r in enumerate(results, 1):
                    f.write(f"{i}. {r['title']}\n")
                    f.write(f"   URL: {r['url']}\n")
                    f.write(f"   Channel: {r['uploader']}\n\n")
            
            print(f"✅ Found {len(results)} results")
        
        return results
        
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")
        return []

def get_channel_videos(channel, count=10):
    """Get recent videos from channel"""
    print(f"\n📺 Channel: {channel}")
    
    if not channel.startswith('http'):
        if not channel.startswith('@'):
            channel = f"@{channel}"
        channel = f"https://youtube.com/{channel}/videos"
    
    has_cookies = os.path.exists(COOKIES_FILE)
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'playlistend': count,
        'ignoreerrors': True,
    }
    
    if has_cookies:
        ydl_opts['cookiefile'] = COOKIES_FILE
        ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0'
    else:
        ydl_opts['user_agent'] = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel, download=False)
            
            if info and 'entries' in info:
                results = []
                for entry in info['entries'][:count]:
                    if entry:
                        results.append({
                            'title': entry.get('title', 'N/A'),
                            'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                            'video_id': entry.get('id', ''),
                            'uploader': info.get('uploader', 'N/A'),
                            'duration': entry.get('duration', 0),
                            'views': entry.get('view_count', 0)
                        })
                
                if results:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = Path(RESULTS_DIR) / f"channel_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    
                    # Save text version
                    text_file = Path(RESULTS_DIR) / f"channel_{timestamp}.txt"
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(f"Channel Videos\n{'='*50}\n\n")
                        for i, r in enumerate(results, 1):
                            f.write(f"{i}. {r['title']}\n")
                            f.write(f"   URL: {r['url']}\n")
                            f.write(f"   Duration: {r['duration']}s\n")
                            f.write(f"   Views: {r['views']}\n\n")
                    
                    print(f"✅ Found {len(results)} videos")
                    return results
        
        print("❌ No videos found")
        return []
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

def read_commands():
    """Read commands from file"""
    commands = []
    
    if not os.path.exists(COMMANDS_FILE):
        print(f"❌ Commands file not found: {COMMANDS_FILE}")
        return commands
    
    with open(COMMANDS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('search '):
                    commands.append(('search', line[7:].strip()))
                elif line.startswith('download '):
                    commands.append(('download', line[9:].strip()))
                elif line.startswith('recent '):
                    parts = line[7:].strip().split(maxsplit=1)
                    if len(parts) == 2 and parts[0].isdigit():
                        commands.append(('recent', (int(parts[0]), parts[1])))
                    else:
                        commands.append(('recent', (10, line[7:].strip())))
    
    return commands

def process_commands():
    """Process all commands"""
    print("🚀 YouTube Downloader")
    print("="*50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    has_cookies = load_cookies_from_env()
    print(f"Cookies: {'✅ Available' if has_cookies else '❌ Not available'}")
    print("="*50)
    
    setup_directories()
    commands = read_commands()
    
    if not commands:
        print("\n⚠️ No commands found")
        return
    
    print(f"\n📋 Processing {len(commands)} command(s):\n")
    
    for idx, (cmd_type, cmd_value) in enumerate(commands, 1):
        print(f"[{idx}/{len(commands)}] {cmd_type}: {cmd_value}")
        print("-"*40)
        
        if cmd_type == 'download':
            if has_cookies:
                success = download_with_cookies(cmd_value)
                if not success:
                    print("\n⚠️ Cookie method failed, trying without cookies...")
                    download_without_cookies(cmd_value)
            else:
                download_without_cookies(cmd_value)
                
        elif cmd_type == 'search':
            search_videos(cmd_value)
            
        elif cmd_type == 'recent':
            count, channel = cmd_value
            get_channel_videos(channel, count)
        
        if idx < len(commands):
            wait = random.uniform(5, 15)
            print(f"\n⏳ Waiting {wait:.0f}s...\n")
            time.sleep(wait)
    
    # Summary
    print("\n" + "="*50)
    print("✅ All commands processed!")
    
    # List results
    downloads = list(Path(DOWNLOAD_DIR).glob("*"))
    if downloads:
        print(f"\n📁 Downloads ({len(downloads)} files):")
        for f in downloads[:5]:
            size_mb = f.stat().st_size / (1024*1024)
            print(f"   - {f.name} ({size_mb:.1f} MB)")
    
    result_files = list(Path(RESULTS_DIR).glob("*.{json,txt}"))
    if result_files:
        print(f"\n📄 Results ({len(result_files)} files)")
    
    # Cleanup cookies for security
    if os.path.exists(COOKIES_FILE):
        os.remove(COOKIES_FILE)
        print("🔒 Cookies cleaned up")
    
    print("="*50)

if __name__ == "__main__":
    process_commands()

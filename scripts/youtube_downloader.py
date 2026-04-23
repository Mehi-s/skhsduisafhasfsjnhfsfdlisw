#!/usr/bin/env python3
"""
YouTube Video Downloader - GitHub Actions Optimized
Uses multiple strategies to avoid bot detection without cookies
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

# Rotating user agents with mobile emphasis (less likely to be flagged)
USER_AGENTS = [
    # Android Chrome
    'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36',
    # iOS Safari
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    # Desktop (less frequent)
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
]

def setup_directories():
    """Create necessary directories"""
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    return random.choice(USER_AGENTS)

def get_visitor_data():
    """Generate visitor data for YouTube API requests"""
    # This mimics a fresh visitor session
    timestamp = int(time.time() * 1000)
    random_id = ''.join(random.choices('0123456789abcdef', k=11))
    return base64.b64encode(f"{timestamp}{random_id}".encode()).decode()[:11]

def download_with_ytdlp(url, quality='worst'):
    """
    Download using yt-dlp with enhanced anti-detection
    """
    print(f"\n📥 Downloading: {url}")
    
    # Define output template
    output_template = f"{DOWNLOAD_DIR}/%(title).100s_%(id)s.%(ext)s"
    
    # Strategy: Use multiple client types and extractors
    ydl_opts = {
        'format': 'worstvideo+worstaudio/worst[height>=144]',
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'restrictfilenames': True,
        'windowsfilenames': True,
        
        # Key anti-detection settings
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web_embedded', 'web'],
                'skip': ['hls', 'dash', 'translated_subs'],
                'player_skip': ['configs', 'webpage', 'js'],
            }
        },
        
        # Throttling to avoid detection
        'throttledratelimit': 100000,  # 100KB/s
        'sleep_interval': random.uniform(3, 8),
        'sleep_interval_requests': random.uniform(2, 5),
        'max_sleep_interval': 15,
        
        # Randomize request headers
        'user_agent': get_random_user_agent(),
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'fr-FR,fr;q=0.9']),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        
        # Retry configuration
        'retries': 20,
        'fragment_retries': 20,
        'retry_sleep_functions': {'http': lambda n: random.uniform(5, 15)},
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        
        # Use latest APIs
        'geo_bypass': True,
        'geo_bypass_country': random.choice(['US', 'GB', 'CA', 'AU', 'DE']),
        
        # Force IPv4 (sometimes helps)
        'force_ipv4': True,
    }
    
    # Try with yt-dlp
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"  Attempt {attempt + 1}/{max_attempts}...")
            time.sleep(random.uniform(5, 10))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    title = info.get('title', 'Unknown')
                    duration = info.get('duration', 0)
                    print(f"✅ Downloaded: {title} ({duration}s)")
                    return True
                    
        except Exception as e:
            error_msg = str(e)
            if "bot" in error_msg.lower() or "sign in" in error_msg.lower():
                print(f"  ⚠️ Bot detection (attempt {attempt + 1})")
                if attempt < max_attempts - 1:
                    # Change strategy for next attempt
                    ydl_opts['extractor_args']['youtube']['player_client'] = ['android_vr', 'ios', 'tv']
                    ydl_opts['user_agent'] = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'
                    wait_time = (attempt + 1) * 30
                    print(f"  ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            else:
                print(f"❌ Error: {error_msg}")
                break
    
    return False

def download_with_yt_dlp_python(url):
    """
    Alternative: Use yt-dlp as subprocess (sometimes bypasses detection)
    """
    print(f"\n🔄 Trying alternative download method...")
    
    output_template = str(Path(DOWNLOAD_DIR) / "%(title).100s_%(id)s.%(ext)s")
    
    cmd = [
        'yt-dlp',
        url,
        '-f', 'worst[height>=144]',
        '-o', output_template,
        '--restrict-filenames',
        '--no-warnings',
        '--user-agent', get_random_user_agent(),
        '--extractor-args', 'youtube:player_client=android,ios',
        '--sleep-interval', str(random.randint(3, 7)),
        '--max-sleep-interval', '15',
        '--retries', '10',
        '--fragment-retries', '10',
        '--throttled-rate', '100K',
        '--geo-bypass',
        '--force-ipv4',
        '--no-check-certificates',  # Sometimes helps
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print("✅ Downloaded successfully with alternative method")
            return True
        else:
            print(f"❌ Failed: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error with subprocess method: {str(e)}")
        return False

def search_videos(query, max_results=10):
    """Search YouTube with anti-detection"""
    print(f"\n🔍 Searching: {query}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'user_agent': get_random_user_agent(),
        'sleep_interval': random.uniform(2, 4),
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'skip': ['webpage'],
            }
        },
    }
    
    results = []
    try:
        time.sleep(random.uniform(2, 5))
        
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
                            'uploader': entry.get('uploader', 'N/A'),
                            'channel_id': entry.get('channel_id', '')
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
        else:
            print("❌ No results found")
        
        return results
        
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")
        return []

def get_channel_videos(channel, count=10):
    """Get recent videos from channel"""
    print(f"\n📺 Channel: {channel}")
    
    # Normalize channel input
    if not channel.startswith('http'):
        if not channel.startswith('@'):
            channel = f"@{channel}"
        channel = f"https://youtube.com/{channel}/videos"
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'playlistend': count,
        'ignoreerrors': True,
        'user_agent': get_random_user_agent(),
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'skip': ['webpage'],
            }
        },
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel, download=False)
            
            if info and 'entries' in info:
                results = []
                entries = info['entries'][:count]
                
                for entry in entries:
                    if entry:
                        results.append({
                            'title': entry.get('title', 'N/A'),
                            'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                            'video_id': entry.get('id', ''),
                            'uploader': info.get('uploader', 'N/A')
                        })
                
                if results:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = Path(RESULTS_DIR) / f"channel_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Found {len(results)} videos")
                    return results
        
        print("❌ No videos found")
        return []
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

def download_video(url):
    """Main download function with fallbacks"""
    # Try method 1: yt-dlp Python API
    success = download_with_ytdlp(url)
    
    # Try method 2: yt-dlp subprocess
    if not success:
        print("\n⚠️ Trying alternative method...")
        success = download_with_yt_dlp_python(url)
    
    # Try method 3: Use Android client only
    if not success:
        print("\n⚠️ Last attempt with Android TV client...")
        ydl_opts = {
            'format': 'worst',
            'outtmpl': f"{DOWNLOAD_DIR}/%(title).100s_%(id)s.%(ext)s",
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_tv', 'tv'],
                    'skip': ['webpage', 'configs'],
                }
            },
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; BRAVIA 4K) AppleWebKit/537.36',
            'sleep_interval': 10,
            'retries': 20,
            'force_ipv4': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    print(f"✅ Finally downloaded: {info.get('title')}")
                    return True
        except Exception as e:
            print(f"❌ All methods failed: {str(e)}")
    
    return success

def read_commands():
    """Read commands from file"""
    commands = []
    
    if not os.path.exists(COMMANDS_FILE):
        print(f"❌ Commands file not found: {COMMANDS_FILE}")
        print("\n📝 Create commands.txt with:")
        print("search python tutorial")
        print("download https://youtube.com/watch?v=VIDEO_ID")
        print("recent @channel_name")
        print("recent 15 @channel_name")
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
    print("🚀 YouTube Downloader (Anti-Bot Mode)")
    print("="*50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Download dir: {DOWNLOAD_DIR}")
    print("="*50)
    
    setup_directories()
    commands = read_commands()
    
    if not commands:
        print("\n⚠️ No commands found. Example commands.txt:")
        print("download https://youtube.com/watch?v=dQw4w9WgXcQ")
        print("search funny cats")
        print("recent @mkbhd")
        return
    
    print(f"\n📋 Processing {len(commands)} command(s):\n")
    
    for idx, (cmd_type, cmd_value) in enumerate(commands, 1):
        print(f"[{idx}/{len(commands)}] {cmd_type}: {cmd_value}")
        
        if cmd_type == 'download':
            download_video(cmd_value)
        elif cmd_type == 'search':
            search_videos(cmd_value)
        elif cmd_type == 'recent':
            count, channel = cmd_value
            get_channel_videos(channel, count)
        
        if idx < len(commands):
            wait = random.uniform(10, 20)
            print(f"\n⏳ Waiting {wait:.0f}s...\n")
            time.sleep(wait)
    
    # Summary
    print("\n" + "="*50)
    print("✅ Commands processed!")
    
    # List results
    result_files = list(Path(RESULTS_DIR).glob("*"))
    downloads = list(Path(DOWNLOAD_DIR).glob("*"))
    
    if downloads:
        print(f"\n📁 Downloads ({len(downloads)} files):")
        for f in downloads[:5]:
            size_mb = f.stat().st_size / (1024*1024)
            print(f"   - {f.name} ({size_mb:.1f} MB)")
    
    if result_files:
        print(f"\n📄 Results ({len(result_files)} files):")
        for f in result_files[:5]:
            print(f"   - {f.name}")
    
    print("="*50)

if __name__ == "__main__":
    process_commands()

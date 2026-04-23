#!/usr/bin/env python3
"""
YouTube Video Downloader using yt-dlp with proxy support
Processes commands from commands.txt file
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

# Proxy configuration - using public proxies or your own
# For GitHub Actions, we'll use rotating user agents instead of proxies
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
def download_video_with_proxy(url, output_template=None):
    """
    Download a video using yt-dlp-proxy to avoid bot detection
    Uses the yt-dlp-proxy CLI command with proxy support
    """
    print(f"\n📥 Downloading: {url}")
    
    if output_template is None:
        # Create a safe filename from video title or use ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_template = f"{DOWNLOAD_DIR}/%(title)s_%(id)s_%(ext)s"
    
    # Extract video ID for display
    video_id = None
    if 'youtube.com/watch' in url:
        match = re.search(r'[?&]v=([^&]+)', url)
        if match:
            video_id = match.group(1)
    elif 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[-1].split('?')[0]
    
    if video_id:
        print(f"  Video ID: {video_id}")
    
    # Build the yt-dlp-proxy command
    # Format: bv[vcodec^=avc!]+ba for best video with avc codec + best audio
    # Using worst quality but ensuring at least 360p
    cmd = [
        'yt-dlp-proxy',
        '--format', 'worst[height>=360]/best[height<=480]/worst',
        '--output', output_template,
        '--no-mtime',  # Don't use Last-modified header to set file modification time
        '--retries', '10',
        '--fragment-retries', '10',
        '--sleep-interval', '3',
        '--max-sleep-interval', '8',
        url
    ]
    
    try:
        print(f"  Running yt-dlp-proxy with anti-detection...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print(f"✅ Download successful via yt-dlp-proxy")
            
            # Try to find the downloaded file and save metadata
            downloaded_files = list(Path(DOWNLOAD_DIR).glob(f"*{video_id}*")) if video_id else []
            downloaded_files.extend(list(Path(DOWNLOAD_DIR).glob("*.mp4")))
            downloaded_files.extend(list(Path(DOWNLOAD_DIR).glob("*.webm")))
            
            if downloaded_files:
                latest_file = max(downloaded_files, key=lambda x: x.stat().st_mtime)
                metadata = {
                    'title': latest_file.stem,
                    'url': url,
                    'video_id': video_id if video_id else 'unknown',
                    'filename': str(latest_file),
                    'filesize': latest_file.stat().st_size,
                    'download_method': 'yt-dlp-proxy',
                    'download_time': datetime.now().isoformat()
                }
                
                metadata_file = Path(RESULTS_DIR) / f"download_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return True
        else:
            error_msg = result.stderr
            print(f"❌ yt-dlp-proxy error: {error_msg[:200]}")
            
            if "Sign in to confirm" in error_msg:
                print(f"  Bot detection still active - trying with different format...")
                # Try with the exact format you specified
                cmd2 = [
                    'yt-dlp-proxy',
                    '--format', 'bv[vcodec^=avc!]+ba',
                    '--output', output_template,
                    url
                ]
                result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=600)
                if result2.returncode == 0:
                    print(f"✅ Download successful with format: bv[vcodec^=avc!]+ba")
                    return True
                else:
                    print(f"❌ Second attempt also failed")
            
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Download timed out after 10 minutes")
        return False
    except FileNotFoundError:
        print(f"❌ yt-dlp-proxy not found. Please install it first.")
        print(f"   Run: pip install yt-dlp-proxy")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def search_videos(query, max_results=10):
    """Search YouTube for videos with anti-detection"""
    print(f"\n🔍 Searching for: {query}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'user_agent': get_random_user_agent(),
        'sleep_interval': random.uniform(1, 3),
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
                    
        # Save search results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(RESULTS_DIR) / f"search_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Also create a readable text file
        text_file = Path(RESULTS_DIR) / f"search_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"Search Results for: {query}\n")
            f.write(f"{'='*60}\n\n")
            for i, result in enumerate(results, 1):
                f.write(f"{i}. {result['title']}\n")
                f.write(f"   URL: {result['url']}\n")
                f.write(f"   Channel: {result['uploader']}\n")
                f.write(f"   Duration: {result['duration']} seconds\n")
                f.write(f"   Views: {result['views']:,}\n\n")
        
        print(f"✅ Search results saved to: {output_file} and {text_file}")
        return results
        
    except Exception as e:
        print(f"❌ Error searching: {str(e)}")
        return []

def get_recent_videos_alternative(channel_url, count=10):
    """Alternative method using search to get recent videos"""
    results = []
    
    try:
        # Extract channel ID first
        ydl_opts = {'quiet': True, 'extract_flat': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get channel info
            if not channel_url.startswith('http'):
                channel_url = f"https://youtube.com/@{channel_url}"
            
            info = ydl.extract_info(channel_url, download=False)
            channel_name = info.get('uploader', info.get('channel', info.get('title', '')))
            channel_id = info.get('channel_id', info.get('id', ''))
            
            if channel_name:
                # Search for videos from this channel (most recent first)
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

def get_recent_videos(channel_url, count=10):
    """Get recent videos from a channel"""
    print(f"\n📺 Getting recent videos from: {channel_url}")
    
    # Different approaches to try
    approaches = []
    
    # Normalize the channel URL
    original_channel = channel_url
    if not channel_url.startswith('http'):
        # Remove @ symbol if present for building URLs
        clean_channel = channel_url.replace('@', '')
        approaches = [
            f"https://www.youtube.com/@{clean_channel}/videos",
            f"https://www.youtube.com/c/{clean_channel}/videos",
            f"https://www.youtube.com/channel/{clean_channel}/videos",
            f"https://www.youtube.com/@{clean_channel}",
            f"https://www.youtube.com/{clean_channel}/videos",
        ]
    else:
        # If it's already a URL, make sure it points to videos tab
        if '/videos' not in channel_url:
            channel_url = channel_url.rstrip('/') + '/videos'
        approaches = [channel_url]
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,  # Skip any problematic entries
        'extract_flat': 'in_playlist',  # More efficient for playlists
    }
    
    results = []
    
    for url in approaches:
        if results and len(results) >= count:  # If we already got enough results, stop trying
            break
            
        print(f"  Trying: {url}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Handle different response structures
                entries = []
                if 'entries' in info:
                    entries = info['entries']
                elif 'videos' in info:
                    entries = info['videos']
                else:
                    # Try to get uploads playlist ID
                    uploads_id = None
                    if 'uploader_id' in info:
                        uploads_id = info.get('uploader_id')
                    elif 'channel_id' in info:
                        uploads_id = info.get('channel_id')
                    
                    if uploads_id:
                        # Get uploads playlist
                        uploads_playlist = f"https://www.youtube.com/channel/{uploads_id}/videos"
                        info2 = ydl.extract_info(uploads_playlist, download=False)
                        if 'entries' in info2:
                            entries = info2['entries']
                
                # Extract video information
                for entry in entries:
                    if entry is None:
                        continue
                        
                    if len(results) >= count:
                        break
                    
                    # Handle different ID formats
                    video_id = entry.get('id', '')
                    if video_id and '/' in video_id:
                        video_id = video_id.split('/')[-1]
                    
                    # Get video URL
                    if 'url' in entry and entry['url']:
                        video_url = entry['url']
                    elif video_id:
                        video_url = f"https://youtube.com/watch?v={video_id}"
                    else:
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
    
    # If we still don't have enough videos, try alternative extraction method
    if len(results) < count:
        print(f"  Only got {len(results)} videos, trying alternative method...")
        alt_results = get_recent_videos_alternative(original_channel, count)
        # Merge results without duplicates
        existing_urls = {r['url'] for r in results}
        for r in alt_results:
            if r['url'] not in existing_urls and len(results) < count:
                results.append(r)
    
    # Save results
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(RESULTS_DIR) / f"recent_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        text_file = Path(RESULTS_DIR) / f"recent_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"Recent Videos from: {original_channel}\n")
            f.write(f"Requested: {count} videos | Found: {len(results)} videos\n")
            f.write(f"{'='*60}\n\n")
            for i, result in enumerate(results, 1):
                f.write(f"{i}. {result['title']}\n")
                f.write(f"   URL: {result['url']}\n")
                f.write(f"   Video ID: {result['video_id']}\n")
                f.write(f"   Upload Date: {result['upload_date']}\n")
                f.write(f"   Duration: {result['duration']} seconds\n")
                if result['views']:
                    f.write(f"   Views: {result['views']:,}\n")
                f.write(f"\n")
        
        print(f"✅ Found {len(results)} recent videos (requested {count})")
    else:
        print(f"❌ No videos found")
    
    return results
def download_playlist(playlist_url):
    """Download entire playlist with anti-detection"""
    print(f"\n🎵 Downloading playlist: {playlist_url}")
    
    output_template = f"{DOWNLOAD_DIR}/playlist/%(playlist_title)s/%(title)s_%(id)s.%(ext)s"
    
    ydl_opts = {
        'format': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]/best',
        'outtmpl': output_template,
        'quiet': False,
        'restrictfilenames': True,
        'ignoreerrors': True,
        'user_agent': get_random_user_agent(),
        'sleep_interval': random.uniform(2, 5),
        'sleep_interval_requests': random.uniform(1, 3),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=True)
            print(f"✅ Downloaded playlist: {info.get('title', 'Unknown')}")
            return True
    except Exception as e:
        print(f"❌ Error downloading playlist: {str(e)}")
        return False

def read_commands():
    """Read and parse commands from commands.txt"""
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
        
        # Parse different command types
        if line.startswith('search '):
            query = line[7:].strip()
            commands.append(('search', query))
        elif line.startswith('download '):
            url = line[9:].strip()
            commands.append(('download', url))
        elif line.startswith('recent '):
            value = line[7:].strip()
            commands.append(('recent', value))
        elif line.startswith('playlist '):
            url = line[9:].strip()
            commands.append(('playlist', url))
    
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
        print("# Search for videos")
        print("search python tutorial 2024")
        print("\n# Download a single video (lowest quality, minimum 360p)")
        print("download https://youtube.com/watch?v=VIDEO_ID")
        print("\n# Get 15 recent videos from a channel")
        print("recent 15 @mkbhd")
        print("\n# Download a playlist (all videos at lowest quality)")
        print("playlist https://youtube.com/playlist?list=PLAYLIST_ID")
        print("#" + "="*60)
        return
    
    print(f"\n📋 Found {len(commands)} command(s) to process\n")
    
    for idx, (cmd_type, cmd_value) in enumerate(commands, 1):
        print(f"[{idx}/{len(commands)}] Processing command: {cmd_type} {cmd_value}")
        
        if cmd_type == 'search':
            search_videos(cmd_value)
        elif cmd_type == 'download':
            download_video_with_proxy(cmd_value)
        elif cmd_type == 'recent':
            # Check if a number is specified (e.g., "recent 15 @channel")
            parts = cmd_value.split()
            if len(parts) >= 2 and parts[0].isdigit():
                count = int(parts[0])
                channel = ' '.join(parts[1:])
                get_recent_videos(channel, count)
            else:
                get_recent_videos(cmd_value, 10)
        elif cmd_type == 'playlist':
            download_playlist(cmd_value)
        else:
            print(f"⚠️  Unknown command type: {cmd_type}")
        
        # Add delay between commands to avoid rate limiting
        if idx < len(commands):
            delay = random.uniform(5, 10)
            print(f"\n⏳ Waiting {delay:.1f} seconds before next command...")
            time.sleep(delay)
        
        print("-"*50)
    
    # Print summary
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

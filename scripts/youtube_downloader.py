#!/usr/bin/env python3
"""
YouTube Video Downloader using yt-dlp
Processes commands from commands.txt file
"""

import yt_dlp
import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
COMMANDS_FILE = "../commands.txt"
RESULTS_DIR = "../results"
DOWNLOAD_DIR = "../results/downloads"

def setup_directories():
    """Create necessary directories"""
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

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
            channel = line[7:].strip()
            commands.append(('recent', channel))
        elif line.startswith('playlist '):
            url = line[9:].strip()
            commands.append(('playlist', url))
    
    return commands

def search_videos(query, max_results=10):
    """Search YouTube for videos"""
    print(f"\n🔍 Searching for: {query}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'force_generic_extractor': False,
    }
    
    results = []
    try:
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

def download_video(url, output_template=None):
    """Download a single video"""
    print(f"\n📥 Downloading: {url}")
    
    if output_template is None:
        output_template = f"{DOWNLOAD_DIR}/%(title)s_%(id)s.%(ext)s"
    
    ydl_opts = {
        'format': 'best[height<=720]/best',  # Limit to 720p to save space
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'restrictfilenames': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Save metadata
            metadata = {
                'title': info.get('title', 'N/A'),
                'url': url,
                'duration': info.get('duration', 0),
                'upload_date': info.get('upload_date', 'N/A'),
                'views': info.get('view_count', 0),
                'likes': info.get('like_count', 0),
                'filename': filename
            }
            
            metadata_file = Path(RESULTS_DIR) / f"download_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Downloaded: {info.get('title')}")
            return True
            
    except Exception as e:
        print(f"❌ Error downloading: {str(e)}")
        return False

def get_recent_videos(channel_url, count=10):
    """Get recent videos from a channel"""
    print(f"\n📺 Getting recent videos from: {channel_url}")
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': count,
    }
    
    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Handle different channel URL formats
            if not channel_url.startswith('http'):
                channel_url = f"https://youtube.com/@{channel_url}"
            
            info = ydl.extract_info(channel_url, download=False)
            
            if 'entries' in info:
                for entry in info['entries'][:count]:
                    result = {
                        'title': entry.get('title', 'N/A'),
                        'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                        'duration': entry.get('duration', 0),
                        'views': entry.get('view_count', 0),
                        'upload_date': entry.get('upload_date', 'N/A')
                    }
                    results.append(result)
                    
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(RESULTS_DIR) / f"recent_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        text_file = Path(RESULTS_DIR) / f"recent_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"Recent Videos from: {channel_url}\n")
            f.write(f"{'='*60}\n\n")
            for i, result in enumerate(results, 1):
                f.write(f"{i}. {result['title']}\n")
                f.write(f"   URL: {result['url']}\n")
                f.write(f"   Upload Date: {result['upload_date']}\n")
                f.write(f"   Duration: {result['duration']} seconds\n\n")
        
        print(f"✅ Found {len(results)} recent videos")
        return results
        
    except Exception as e:
        print(f"❌ Error getting recent videos: {str(e)}")
        return []

def download_playlist(playlist_url):
    """Download entire playlist"""
    print(f"\n🎵 Downloading playlist: {playlist_url}")
    
    output_template = f"{DOWNLOAD_DIR}/playlist/%(playlist_title)s/%(title)s_%(id)s.%(ext)s"
    
    ydl_opts = {
        'format': 'best[height<=480]/best',  # Lower quality for playlists
        'outtmpl': output_template,
        'quiet': False,
        'restrictfilenames': True,
        'ignoreerrors': True,  # Skip failed videos
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=True)
            print(f"✅ Downloaded playlist: {info.get('title', 'Unknown')}")
            return True
    except Exception as e:
        print(f"❌ Error downloading playlist: {str(e)}")
        return False

def process_commands():
    """Process all commands from the commands file"""
    print("🚀 YouTube Video Downloader Started")
    print("="*50)
    
    setup_directories()
    commands = read_commands()
    
    if not commands:
        print("No commands found in commands.txt")
        print("\nExample commands.txt content:")
        print("# Search for videos")
        print("search ai tutorial")
        print("\n# Download a video")
        print("download https://youtube.com/watch?v=VIDEO_ID")
        print("\n# Get recent videos from a channel")
        print("recent @channelname")
        print("\n# Download a playlist")
        print("playlist https://youtube.com/playlist?list=PLAYLIST_ID")
        return
    
    print(f"Found {len(commands)} command(s) to process\n")
    
    for cmd_type, cmd_value in commands:
        if cmd_type == 'search':
            search_videos(cmd_value)
        elif cmd_type == 'download':
            download_video(cmd_value)
        elif cmd_type == 'recent':
            get_recent_videos(cmd_value)
        elif cmd_type == 'playlist':
            download_playlist(cmd_value)
        print("-"*50)
    
    print("\n✅ All commands processed successfully!")
    print(f"Results saved in: {RESULTS_DIR}")

def main():
    """Main entry point"""
    process_commands()

if __name__ == "__main__":
    main()
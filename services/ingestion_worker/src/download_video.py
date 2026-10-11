import os
import yt_dlp
from pathlib import Path

def download_video(video_id, output_dir="downloads"):
    """Downloads audio from YouTube using yt-dlp"""
    
    # Ensure directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"📥 Starting download for Video ID: {video_id}")


    ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'merge_output_format': 'mp4',
    'outtmpl': f'{output_dir}/{video_id}.%(ext)s',
    'quiet': False,
}
    ''''
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_dir}/{video_id}.%(ext)s', # Saves as hzTwjmM09JA.mp3
        'quiet': False,  # Set to True to hide progress bars if desired
    }'''

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
            
            title = info.get('title', 'Unknown Title')
            print("✅ Download Complete!")
            print(f"📄 Title: {title}")
            print(f"💾 Saved to: {output_dir}/{video_id}.mp3")
            
            return True
            
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        # Common error: "FFmpeg not found". Ensure you ran 'brew install ffmpeg'
        return False

if __name__ == "__main__":
    # Test with your specific ID
    test_id = "hzTwjmM09JA"
    download_video(test_id)

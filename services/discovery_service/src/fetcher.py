import sys
import os
import time
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import yaml
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from googleapiclient.discovery import build
from src.config import Config

def test_youtube_connection():
    """
    MVP: Connects to YouTube API and fetches 5 videos for 'orthopedic hardware'.
    Prints video ID, Title, and Channel Name.
    """
    
    # 1. Initialize Client
    try:
        print("🚀 Initializing YouTube Data API v3...")
        youtube = build("youtube", "v3", developerKey=Config.YOUTUBE_API_KEY)
        print("✅ Connection Successful!")
    except Exception as e:
        print("❌ Failed to connect. Check your API Key in .env file.")
        print(f"Error: {e}")
        return

    # 2. Define Search Query
    query = "orthopedic hardware internal fixator"
    
    try:
        print(f"\n🔍 Searching for: '{query}'...")
        
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=5,  # Fetch only 5 to test quickly
            order="relevance"
        )
        
        response = request.execute()

        if 'items' not in response:
            print("⚠️ No videos found for this query.")
            return

        print(f"\n📺 Found {len(response['items'])} videos:\n")
        print("-" * 60)

        for i, item in enumerate(response['items'], 1):
            # Ensure we only process video items (sometimes search returns channels)
            if item['id']['kind'] == 'youtube#video':
                snippet = item['snippet']
                
                print(f"{i}. ID: {item['id']['videoId']}")
                print(f"   Title: {snippet['title']}")
                print(f"   Channel: {snippet['channelTitle']}")
                print(f"   Published: {snippet['publishedAt'][:10]}")
                
                # Check if tags exist (often empty in search results, but good to check)
                if 'tags' in snippet and snippet['tags']:
                    print(f"   Tags: {', '.join(snippet['tags'][:3])}...")
                
                print("-" * 60)

        print("\n✅ MVP Test Complete! The API is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Error during search execution: {e}")

if __name__ == "__main__":
    test_youtube_connection()


# CONFIGURATION
API_KEY = os.getenv("YOUTUBE_API_KEY")
QUOTA_LIMIT = 10000  # Free tier daily limit
CURRENT_QUOTA_USED = 0  # You should track this in a DB or file for persistence across runs

def check_quota():
    global CURRENT_QUOTA_USED
    if CURRENT_QUOTA_USED >= QUOTA_LIMIT:
        raise Exception("Daily Quota Limit Reached. Stop processing.")

def add_to_usage(units):
    global CURRENT_QUOTA_USED
    CURRENT_QUOTA_USED += units
    print(f"Quota Used: {CURRENT_QUOTA_USED}/{QUOTA_LIMIT} (Remaining: {QUOTA_LIMIT - CURRENT_QUOTA_USED})")

# Initialize Client
youtube = build("youtube", "v3", developerKey=API_KEY)

def get_orthopedic_video_ids_optimized(seed_keywords):
    """
    Fetches video IDs using minimal quota.
    Strategy: Maximize results per search, batch details fetch.
    """
    all_video_ids = []
    
    # 1. SEARCH PHASE (Expensive: 100 units/request)
    print("--- Starting Search Phase ---")
    for keyword in seed_keywords:
        check_quota()
        
        try:
            request = youtube.search().list(
                part="snippet",
                q=keyword,
                type="video",
                maxResults=50,  # MAX allowed per request to save quota
                order="relevance"
            )
            
            add_to_usage(100) # Cost of search
            
            response = request.execute()
            
            if 'items' in response:
                for item in response['items']:
                    video_id = item['id']['videoId']
                    all_video_ids.append(video_id)
                    print(f"Found: {item['snippet']['title']}")
                
                # Optional: Handle pagination (Next Page Token) if you need >50 results per keyword
                # WARNING: Each page fetch costs another 100 units. 
                # For MVP, stick to the first page of top 50.
            
        except Exception as e:
            print(f"Error searching for '{keyword}': {e}")

    return list(set(all_video_ids)) # Remove duplicates

def get_transcripts_batch(video_ids):
    """
    Fetches transcripts using youtube-transcript-api (0 API Units).
    """
    print("--- Starting Transcript Extraction (Free) ---")
    valid_data = []
    
    for vid_id in video_ids:
        try:
            # This does NOT use the YouTube Data API quota
            transcript_list = YouTubeTranscriptApi.get_transcript(vid_id, languages=['en'])
            
            text_content = " ".join([t['text'] for t in transcript_list])
            
            valid_data.append({
                "video_id": vid_id,
                "transcript": text_content,
                "status": "success"
            })
        except Exception as e:
            # Handle missing captions or errors gracefully
            print(f"Skipping {vid_id}: No transcript found or error.")
            valid_data.append({
                "video_id": vid_id,
                "transcript": "",
                "status": "failed",
                "reason": str(e)
            })
            
    return valid_data



def get_seeds():
    path = Path(__file__).parent / "config" / "seeds.yaml"
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Flatten all categories into one list for the search loop
    all_keywords = []
    for category, keywords in data['orthopedic_seeds'].items():
        all_keywords.extend(keywords)
        
    config = data.get('runner_config', {})
    
    return {
        "keywords": all_keywords,
        "daily_limit": config.get("daily_search_limit", 25),
        "max_results": config.get("max_results_per_request", 50)
    }

# Usage
seeds_data = get_seeds()
print(f"Total seeds available: {len(seeds_data['keywords'])}")
print(f"Daily limit set to: {seeds_data['daily_limit']}")


# --- EXECUTION FLOW FOR MVP ---

if __name__ == "__main__":
    # 1. Define your static seed list (Don't iterate dynamically yet)
    seeds = get_seeds()
    print(f"Total seeds available: {len(seeds['keywords'])}")
    print(f"Daily limit set to: {seeds['daily_limit']}")

    # 2. Get IDs (Cost: ~400 units for 4 keywords)
    video_ids = get_orthopedic_video_ids_optimized(seeds)
    
    print(f"\nTotal unique videos found: {len(video_ids)}")
    
    if len(video_ids) == 0:
        print("No videos found. Check API Key or Keywords.")
    else:
        # 3. Get Transcripts (Cost: 0 units)
        corpus_data = get_transcripts_batch(video_ids)
        
        # 4. Save to local file for RAG ingestion
        import json
        with open("ortho_corpus_mvp.json", "w") as f:
            json.dump(corpus_data, f, indent=2)
            
        print(f"\nMVP Corpus saved! Ready for RAG indexing.")

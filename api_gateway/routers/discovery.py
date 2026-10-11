"""Discovery Service Router - YouTube video search and transcript fetching"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from api_gateway.dependencies import discovery_service, DiscoveryServiceClient

router = APIRouter(prefix="/discovery", tags=["Discovery"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class VideoSearchRequest(BaseModel):
    """Request model for video search"""
    query: str
    max_results: int = 10
    order_by: str = "relevance"  # relevance, date, rating, viewCount


class VideoSearchResponse(BaseModel):
    """Response model for video search"""
    status: str
    query: str
    count: int
    videos: List[dict]


class TranscriptResponse(BaseModel):
    """Response model for transcript fetch"""
    status: str
    video_id: str
    transcript: List[dict]
    segments_count: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/test-youtube", response_model=dict)
def test_youtube_connection(client: DiscoveryServiceClient = Depends(discovery_service)):
    """
    Test YouTube API connection
    
    Fetches 5 videos for 'orthopedic hardware' and returns basic info.
    Useful for verifying API key configuration.
    """
    try:
        client.test_connection()
        return {
            "status": "success",
            "message": "YouTube API connection tested successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YouTube API test failed: {str(e)}"
        )


@router.post("/search", response_model=VideoSearchResponse)
async def search_videos(request: VideoSearchRequest, client: DiscoveryServiceClient = Depends(discovery_service)):
    """
    Search for orthopedic videos on YouTube
    
    Uses the Discovery Service to find relevant videos based on query.
    Supports ordering by relevance, date, rating, or view count.
    
    TODO: Implement get_orthopedic_video_ids_optimized() from discovery_service
    """
    try:
        # Placeholder implementation - replace with actual service call
        # videos = await client.search_videos(request.query, request.max_results, request.order_by)
        
        return VideoSearchResponse(
            status="success",
            query=request.query,
            count=0,
            videos=[]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video search failed: {str(e)}"
        )


@router.get("/transcript/{video_id}", response_model=TranscriptResponse)
async def get_video_transcript(video_id: str, client: DiscoveryServiceClient = Depends(discovery_service)):
    """
    Fetch transcript for a specific YouTube video
    
    Uses YouTube Transcript API to retrieve available captions/subtitles.
    Returns transcript as list of segments with text and timing info.
    
    Args:
        video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ')
    
    Returns:
        Transcript segments with text, start time, and duration
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        return TranscriptResponse(
            status="success",
            video_id=video_id,
            transcript=transcript,
            segments_count=len(transcript)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcript fetch failed: {str(e)}"
        )


@router.get("/video-info/{video_id}", response_model=dict)
async def get_video_info(video_id: str, client: DiscoveryServiceClient = Depends(discovery_service)):
    """
    Get detailed information about a YouTube video
    
    Returns title, channel, duration, view count, and other metadata.
    
    TODO: Implement using YouTube Data API v3 videos().list() method
    """
    try:
        # Placeholder - implement with actual YouTube API call
        return {
            "status": "success",
            "video_id": video_id,
            "message": "Video info endpoint active (implement YouTube Data API call)"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch video info: {str(e)}"
        )

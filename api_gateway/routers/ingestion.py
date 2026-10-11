"""Ingestion Service Router - Video download and transcription pipeline"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from api_gateway.dependencies import ingestion_service, IngestionServiceClient

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class DownloadRequest(BaseModel):
    """Request model for video download"""
    video_id: str
    quality: str = "720p"  # 144p, 240p, 360p, 480p, 720p, 1080p
    format: str = "mp4"  # mp4, webm, mkv


class DownloadResponse(BaseModel):
    """Response model for video download"""
    status: str
    video_id: str
    message: str
    file_path: Optional[str] = None


class TranscribeRequest(BaseModel):
    """Request model for video transcription"""
    video_id: str
    language: Optional[str] = "en"  # Auto-detect if not specified


class TranscribeResponse(BaseModel):
    """Response model for video transcription"""
    status: str
    video_id: str
    message: str
    transcript_path: Optional[str] = None


class ProcessRequest(BaseModel):
    """Request model for full processing pipeline"""
    video_id: str
    download_quality: str = "720p"
    language: Optional[str] = "en"


class ProcessResponse(BaseModel):
    """Response model for full processing pipeline"""
    status: str
    video_id: str
    message: str
    stages_completed: list


# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def background_download_video(video_id: str, quality: str, format: str):
    """Background task to download video"""
    # TODO: Implement actual download using ingestion_worker
    print(f"📥 Downloading video {video_id} in {quality} {format}")


async def background_transcribe_video(video_id: str, language: str):
    """Background task to transcribe video"""
    # TODO: Implement actual transcription using ingestion_worker
    print(f"🎤 Transcribing video {video_id} (language: {language})")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/download/{video_id}", response_model=DownloadResponse)
async def download_video(
    video_id: str,
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    client: IngestionServiceClient = Depends(ingestion_service)
):
    """
    Download a YouTube video for processing
    
    Downloads the video in specified quality and format.
    Operation runs in background to avoid timeout on large files.
    
    Args:
        video_id: YouTube video ID
        request: Download parameters (quality, format)
    
    Returns:
        Download status and file path when complete
    """
    try:
        # Add download task to background
        background_tasks.add_task(
            background_download_video,
            video_id=request.video_id,
            quality=request.quality,
            format=request.format
        )
        
        return DownloadResponse(
            status="processing",
            video_id=video_id,
            message=f"Video download initiated in background ({request.quality} {request.format})"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video download failed: {str(e)}"
        )


@router.post("/transcribe/{video_id}", response_model=TranscribeResponse)
async def transcribe_video(
    video_id: str,
    request: TranscribeRequest,
    background_tasks: BackgroundTasks,
    client: IngestionServiceClient = Depends(ingestion_service)
):
    """
    Transcribe a downloaded video
    
    Uses speech-to-text to generate transcript from video audio.
    Operation runs in background for long-running transcription tasks.
    
    Args:
        video_id: YouTube video ID (video must be downloaded first)
        request: Transcription parameters (language)
    
    Returns:
        Transcription status and transcript file path when complete
    """
    try:
        # Add transcription task to background
        background_tasks.add_task(
            background_transcribe_video,
            video_id=request.video_id,
            language=request.language or "en"
        )
        
        return TranscribeResponse(
            status="processing",
            video_id=video_id,
            message=f"Video transcription initiated in background (language: {request.language or 'auto'})"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video transcription failed: {str(e)}"
        )


@router.post("/process/{video_id}", response_model=ProcessResponse)
async def process_video_full(
    video_id: str,
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    client: IngestionServiceClient = Depends(ingestion_service)
):
    """
    Full ingestion pipeline: download + transcribe
    
    Orchestrates the complete workflow:
    1. Download video from YouTube
    2. Extract audio
    3. Transcribe to text
    4. Save transcript for indexing
    
    All operations run in background to handle long-running tasks.
    
    Args:
        video_id: YouTube video ID
        request: Processing parameters (quality, language)
    
    Returns:
        Pipeline status and completed stages
    """
    try:
        # Add pipeline tasks to background
        background_tasks.add_task(
            background_download_video,
            video_id=request.video_id,
            quality=request.download_quality,
            format="mp4"
        )
        background_tasks.add_task(
            background_transcribe_video,
            video_id=request.video_id,
            language=request.language or "en"
        )
        
        return ProcessResponse(
            status="processing",
            video_id=video_id,
            message="Full ingestion pipeline initiated (download → transcribe)",
            stages_completed=[]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing failed: {str(e)}"
        )


@router.get("/status/{video_id}", response_model=dict)
async def get_processing_status(video_id: str, client: IngestionServiceClient = Depends(ingestion_service)):
    """
    Check processing status for a specific video
    
    Returns current stage (queued, downloading, transcribing, completed, failed)
    and any error messages if applicable.
    
    TODO: Implement status tracking using Redis or database
    """
    try:
        return {
            "status": "unknown",
            "video_id": video_id,
            "message": "Status tracking not yet implemented (use Redis/DB for job tracking)"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch status: {str(e)}"
        )

"""
Video ingestion endpoint.
Handles YouTube video URL submission and processing.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked
)

from app.api.schemas.ingest import (
    VideoIngestRequest,
    VideoIngestResponse,
    VideoIngestError
)
from app.services.youtube_loader import load_youtube_transcript, format_timestamp
from app.rag.splitter import split_transcript
from app.rag.vector_store import create_vector_store, save_vector_store
from app.services.study_material_generator import generate_all_materials, save_study_materials
from app.utils.helpers import validate_youtube_url, log_error

router = APIRouter()


@router.post(
    "/video",
    response_model=VideoIngestResponse,
    responses={
        400: {"model": VideoIngestError},
        404: {"model": VideoIngestError},
        500: {"model": VideoIngestError}
    },
    summary="Ingest YouTube Video",
    description="Load a YouTube video transcript, process it, and store in vector database"
)
async def ingest_video(request: VideoIngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a YouTube video for Q&A.
    
    Steps:
    1. Fetch transcript from YouTube
    2. Split into chunks
    3. Generate embeddings
    4. Store in vector database
    5. Generate study materials (background)
    
    Returns:
        VideoIngestResponse with ingestion details
    """
    try:
        print(f"\n📥 Ingesting video: {request.url}")
        
        # Validate URL
        if not validate_youtube_url(request.url):
            raise ValueError("Invalid YouTube URL format")
        
        # Step 1: Load transcript
        transcript_data = load_youtube_transcript(request.url)
        
        # Step 2: Split into chunks
        chunks = split_transcript(transcript_data)
        
        # Step 3 & 4: Create embeddings and store
        vector_store = create_vector_store(chunks, transcript_data['video_id'])
        save_vector_store(vector_store, transcript_data['video_id'])
        
        # Step 5: Generate study materials in background
        video_id = transcript_data['video_id']
        transcript_text = transcript_data['full_text']
        
        def generate_materials_task():
            """Background task to generate study materials."""
            try:
                print(f"\n📚 Background: Generating study materials for {video_id}")
                materials = generate_all_materials(video_id, transcript_text)
                save_study_materials(video_id, materials)
                print(f"✅ Background: Study materials saved for {video_id}")
            except Exception as e:
                print(f"❌ Background: Failed to generate study materials: {str(e)}")
        
        background_tasks.add_task(generate_materials_task)
        
        # Success response
        response = VideoIngestResponse(
            status="success",
            message="Video ingested successfully. Study materials are being generated.",
            video_id=transcript_data['video_id'],
            video_url=transcript_data['video_url'],
            total_segments=len(transcript_data['transcript']),
            total_chunks=len(chunks),
            duration=format_timestamp(transcript_data['total_duration'])
        )
        
        print(f"✅ Ingestion complete: {transcript_data['video_id']}")
        
        return response
        
    except TranscriptsDisabled:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Transcripts are disabled for this video",
                "error_type": "TranscriptsDisabled"
            }
        )
    
    except NoTranscriptFound:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": "No transcript found for this video",
                "error_type": "NoTranscriptFound"
            }
        )
    
    except VideoUnavailable:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": "Video is unavailable",
                "error_type": "VideoUnavailable"
            }
        )
    
    except RequestBlocked:
        raise HTTPException(
            status_code=429,
            detail={
                "status": "error",
                "message": "YouTube is temporarily blocking requests. Please wait a few minutes and try again.",
                "error_type": "RequestBlocked"
            }
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(e),
                "error_type": "ValueError"
            }
        )
    
    except Exception as e:
        print(f"❌ Ingestion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Internal server error: {str(e)}",
                "error_type": "InternalError"
            }
        )

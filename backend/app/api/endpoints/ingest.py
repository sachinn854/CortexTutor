"""
Video ingestion endpoint.
Handles YouTube video URL submission and processing.
"""

from fastapi import APIRouter, HTTPException
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked
)

from app.api.schemas.ingest import (
    VideoIngestRequest,
    TextIngestRequest,
    VideoIngestResponse,
    VideoIngestError
)
from app.services.youtube_loader import load_youtube_transcript, format_timestamp
from app.rag.splitter import split_transcript
from app.rag.vector_store import create_vector_store, save_vector_store
from app.utils.helpers import validate_youtube_url
import uuid

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
async def ingest_video(request: VideoIngestRequest):
    """
    Ingest a YouTube video for Q&A.
    
    Steps:
    1. Fetch transcript from YouTube
    2. Split into chunks
    3. Generate embeddings
    4. Store in vector database
    5. Ready for on-demand study material generation
    
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
        
        # Success response
        response = VideoIngestResponse(
            status="success",
            message="Video ingested successfully. You can now generate notes or MCQs on demand.",
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

    except ConnectionError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "YouTube is unreachable from this runtime. Use /api/ingest/text as a fallback.",
                "error_type": "NetworkResolutionError"
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
        error_text = str(e)
        print(f"❌ Ingestion error: {error_text}")

        # Common on restricted hosted runtimes where YouTube DNS/egress is blocked.
        if "Failed to resolve" in error_text or "No address associated with hostname" in error_text:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "error",
                    "message": "Host environment cannot reach YouTube right now. Use /api/ingest/text with transcript content as fallback.",
                    "error_type": "NetworkResolutionError"
                }
            )

        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Internal server error: {error_text}",
                "error_type": "InternalError"
            }
        )


@router.post(
    "/text",
    response_model=VideoIngestResponse,
    responses={
        400: {"model": VideoIngestError},
        500: {"model": VideoIngestError}
    },
    summary="Ingest Transcript Text",
    description="Ingest plain transcript text directly when YouTube fetch is unavailable"
)
async def ingest_text(request: TextIngestRequest):
    """
    Ingest raw transcript text for Q&A.

    Useful fallback for hosted environments where direct YouTube access is blocked.
    """
    try:
        text = (request.transcript_text or "").strip()
        if len(text) < 20:
            raise ValueError("Transcript text is too short")

        video_id = request.video_id or f"manual_{uuid.uuid4().hex[:10]}"

        transcript_data = {
            "video_id": video_id,
            "video_url": request.title or f"manual://{video_id}",
            "transcript": [
                {
                    "text": text,
                    "start": 0.0,
                    "duration": float(len(text) // 12),
                    "timestamp": "00:00",
                    "url": f"manual://{video_id}"
                }
            ],
            "full_text": text,
            "total_duration": float(len(text) // 12)
        }

        chunks = split_transcript(transcript_data)
        vector_store = create_vector_store(chunks, video_id)
        save_vector_store(vector_store, video_id)

        return VideoIngestResponse(
            status="success",
            message="Transcript text ingested successfully. You can now ask questions.",
            video_id=video_id,
            video_url=transcript_data["video_url"],
            total_segments=1,
            total_chunks=len(chunks),
            duration=format_timestamp(transcript_data["total_duration"])
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
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Internal server error: {str(e)}",
                "error_type": "InternalError"
            }
        )

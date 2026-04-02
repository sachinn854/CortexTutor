"""
Schemas for video ingestion endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class VideoIngestRequest(BaseModel):
    """Request schema for video ingestion."""
    
    url: str = Field(
        ...,
        description="YouTube video URL",
        examples=["https://www.youtube.com/watch?v=aircAruvnKk"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=aircAruvnKk"
            }
        }


class VideoIngestResponse(BaseModel):
    """Response schema for video ingestion."""
    
    status: str = Field(..., description="Status of ingestion")
    message: str = Field(..., description="Human-readable message")
    video_id: str = Field(..., description="YouTube video ID")
    video_url: str = Field(..., description="YouTube video URL")
    total_segments: int = Field(..., description="Number of transcript segments")
    total_chunks: int = Field(..., description="Number of chunks created")
    duration: str = Field(..., description="Video duration (formatted)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Video ingested successfully",
                "video_id": "aircAruvnKk",
                "video_url": "https://www.youtube.com/watch?v=aircAruvnKk",
                "total_segments": 286,
                "total_chunks": 286,
                "duration": "18:25"
            }
        }


class TextIngestRequest(BaseModel):
    """Request schema for manual transcript ingestion."""

    transcript_text: str = Field(
        ...,
        min_length=20,
        description="Plain transcript text to ingest"
    )
    video_id: Optional[str] = Field(
        default=None,
        description="Optional custom video/session ID"
    )
    title: Optional[str] = Field(
        default=None,
        description="Optional title for this transcript"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "transcript_text": "Neural networks are inspired by the brain...",
                "video_id": "manual_nn_intro",
                "title": "Neural Network Intro"
            }
        }


class VideoIngestError(BaseModel):
    """Error response for video ingestion."""
    
    status: str = Field(default="error", description="Error status")
    message: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Type of error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "No transcript available for this video",
                "error_type": "TranscriptsDisabled"
            }
        }

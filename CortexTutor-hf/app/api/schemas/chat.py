"""
Schemas for chat/Q&A endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Source(BaseModel):
    """Source document with timestamp."""
    
    text: str = Field(..., description="Text content from transcript")
    timestamp: str = Field(..., description="Formatted timestamp (MM:SS)")
    url: str = Field(..., description="YouTube URL with timestamp")
    start: float = Field(..., description="Start time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is a 3.",
                "timestamp": "00:04",
                "url": "https://www.youtube.com/watch?v=aircAruvnKk&t=4s",
                "start": 4.0
            }
        }


class ChatRequest(BaseModel):
    """Request schema for chat/Q&A."""
    
    video_id: str = Field(
        ...,
        description="YouTube video ID to query",
        examples=["aircAruvnKk"]
    )
    question: str = Field(
        ...,
        description="User's question about the video",
        min_length=1,
        examples=["What is a neural network?"]
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for conversation history (Phase 5)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "aircAruvnKk",
                "question": "What is a neural network?"
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat/Q&A."""
    
    answer: str = Field(..., description="AI-generated answer")
    sources: List[Source] = Field(
        ...,
        description="Source chunks with timestamps"
    )
    video_id: str = Field(..., description="Video ID queried")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "A neural network is a computational model inspired by biological neural networks...",
                "sources": [
                    {
                        "text": "This is a 3.",
                        "timestamp": "00:04",
                        "url": "https://www.youtube.com/watch?v=aircAruvnKk&t=4s",
                        "start": 4.0
                    }
                ],
                "video_id": "aircAruvnKk"
            }
        }


class ChatError(BaseModel):
    """Error response for chat."""
    
    status: str = Field(default="error", description="Error status")
    message: str = Field(..., description="Error message")
    video_id: Optional[str] = Field(None, description="Video ID if applicable")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Vector store not found for this video. Please ingest the video first.",
                "video_id": "aircAruvnKk"
            }
        }

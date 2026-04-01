"""
Schemas for study materials endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Flashcard(BaseModel):
    """Flashcard schema."""
    
    question: str = Field(..., description="Question text")
    answer: str = Field(..., description="Answer text")
    timestamp: Optional[str] = Field(None, description="Timestamp in video (MM:SS)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is a neural network?",
                "answer": "A neural network is a computational model inspired by biological neural networks.",
                "timestamp": "02:30"
            }
        }


class Summary(BaseModel):
    """Video summary schema."""
    
    overview: str = Field(..., description="Brief overview of the video")
    key_points: List[str] = Field(..., description="Main concepts covered")
    prerequisites: List[str] = Field(..., description="Prerequisite knowledge")
    learning_outcomes: List[str] = Field(..., description="What students will learn")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overview": "This video introduces neural networks and deep learning concepts.",
                "key_points": [
                    "Neural network architecture",
                    "Activation functions",
                    "Backpropagation"
                ],
                "prerequisites": [
                    "Basic calculus",
                    "Linear algebra"
                ],
                "learning_outcomes": [
                    "Understand neural network structure",
                    "Learn how neurons process information"
                ]
            }
        }


class StudyMaterials(BaseModel):
    """Complete study materials for a video."""
    
    video_id: str = Field(..., description="YouTube video ID")
    summary: Summary = Field(..., description="Video summary")
    flashcards: List[Flashcard] = Field(..., description="Generated flashcards")
    key_takeaways: List[str] = Field(..., description="Key takeaways")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "aircAruvnKk",
                "summary": {
                    "overview": "Introduction to neural networks",
                    "key_points": ["Neural architecture", "Learning process"],
                    "prerequisites": ["Basic math"],
                    "learning_outcomes": ["Understand neural networks"]
                },
                "flashcards": [
                    {
                        "question": "What is a neuron?",
                        "answer": "A computational unit in a neural network",
                        "timestamp": "01:30"
                    }
                ],
                "key_takeaways": [
                    "Neural networks mimic brain structure",
                    "They learn from data"
                ]
            }
        }


class StudyMaterialsResponse(BaseModel):
    """Response for study materials request."""
    
    status: str = Field(default="success", description="Response status")
    materials: StudyMaterials = Field(..., description="Study materials")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "materials": {
                    "video_id": "aircAruvnKk",
                    "summary": {},
                    "flashcards": [],
                    "key_takeaways": []
                }
            }
        }


class StudyMaterialsError(BaseModel):
    """Error response for study materials."""
    
    status: str = Field(default="error", description="Error status")
    message: str = Field(..., description="Error message")
    video_id: Optional[str] = Field(None, description="Video ID if applicable")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Study materials not found for this video",
                "video_id": "aircAruvnKk"
            }
        }

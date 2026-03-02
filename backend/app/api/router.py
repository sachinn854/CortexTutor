"""
Main API router that combines all endpoint routers.
"""

from fastapi import APIRouter
from app.api.endpoints import ingest, chat, study_materials

# Create main API router
api_router = APIRouter()

# Include endpoint routers with prefixes
api_router.include_router(
    ingest.router,
    prefix="/ingest",
    tags=["Video Ingestion"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat & Q&A"]
)

api_router.include_router(
    study_materials.router,
    prefix="/study-materials",
    tags=["Study Materials"]
)

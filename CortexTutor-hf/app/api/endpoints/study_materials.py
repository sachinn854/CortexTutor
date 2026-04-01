"""
Study materials endpoint.
Provides auto-generated learning materials for videos.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.api.schemas.study_materials import (
    StudyMaterials,
    StudyMaterialsResponse,
    StudyMaterialsError
)
from app.services.study_material_generator import (
    load_study_materials,
    generate_all_materials,
    save_study_materials
)
from app.services.youtube_loader import load_youtube_transcript

router = APIRouter()


@router.get(
    "/{video_id}",
    response_model=StudyMaterialsResponse,
    responses={
        404: {"model": StudyMaterialsError},
        500: {"model": StudyMaterialsError}
    },
    summary="Get Study Materials",
    description="Retrieve auto-generated study materials (summary, flashcards, takeaways) for a video"
)
async def get_study_materials(video_id: str):
    """
    Get study materials for a video.
    
    Materials are auto-generated during video ingestion.
    If not available, returns 404.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        StudyMaterialsResponse with all materials
    """
    try:
        print(f"\n📚 Fetching study materials for: {video_id}")
        
        # Try to load existing materials
        materials = load_study_materials(video_id)
        
        if not materials:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Study materials not found for video: {video_id}. They may still be generating.",
                    "video_id": video_id
                }
            )
        
        response = StudyMaterialsResponse(
            status="success",
            materials=StudyMaterials(**materials)
        )
        
        print(f"✅ Study materials retrieved")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving study materials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Internal server error: {str(e)}",
                "video_id": video_id
            }
        )


@router.post(
    "/generate/{video_id}",
    response_model=StudyMaterialsResponse,
    responses={
        404: {"model": StudyMaterialsError},
        500: {"model": StudyMaterialsError}
    },
    summary="Generate Study Materials",
    description="Manually trigger study material generation for a video"
)
async def generate_study_materials(video_id: str, background_tasks: BackgroundTasks):
    """
    Manually generate study materials for a video.
    
    This is useful if materials weren't generated during ingestion
    or if you want to regenerate them.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        StudyMaterialsResponse with generated materials
    """
    try:
        print(f"\n🔄 Generating study materials for: {video_id}")
        
        # Load transcript
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        transcript_data = load_youtube_transcript(video_url)
        transcript_text = transcript_data['full_text']
        
        # Generate materials
        materials = generate_all_materials(video_id, transcript_text)
        
        # Save materials
        save_study_materials(video_id, materials)
        
        response = StudyMaterialsResponse(
            status="success",
            materials=StudyMaterials(**materials)
        )
        
        print(f"✅ Study materials generated and saved")
        
        return response
        
    except Exception as e:
        print(f"❌ Error generating study materials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to generate study materials: {str(e)}",
                "video_id": video_id
            }
        )

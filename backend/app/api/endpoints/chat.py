"""
Chat/Q&A endpoint.
Handles questions about ingested videos with conversation memory.
"""

from fastapi import APIRouter, HTTPException

from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatError,
    Source
)
from app.agents.learning_agent import chat_with_agent
from app.rag.pipeline import ask_question

router = APIRouter()


@router.post(
    "/ask",
    response_model=ChatResponse,
    responses={
        404: {"model": ChatError},
        500: {"model": ChatError}
    },
    summary="Ask Question About Video",
    description="Ask a question about an ingested YouTube video. Supports conversation memory with session_id."
)
async def chat_ask(request: ChatRequest):
    """
    Ask a question about a video with optional conversation memory.
    
    The video must be ingested first using the /ingest/video endpoint.
    
    If session_id is provided, the agent will remember previous conversation context.
    
    Returns:
        ChatResponse with answer and source timestamps
    """
    try:
        print(f"\n💬 Question for video {request.video_id}: {request.question}")
        
        if request.session_id:
            # Use agent with memory
            print(f"🧠 Using agent with session: {request.session_id}")
            result = chat_with_agent(
                request.video_id,
                request.question,
                request.session_id
            )
            
            # Agent doesn't return sources, so get them separately
            from app.rag.pipeline import ask_question as get_sources
            sources_result = get_sources(request.video_id, request.question)
            sources = sources_result["sources"]
            
        else:
            # Use direct RAG without memory
            print(f"📝 Using direct RAG (no session)")
            result = ask_question(request.video_id, request.question)
            sources = result["sources"]
        
        # Convert sources to schema format
        source_objects = [
            Source(
                text=source["text"],
                timestamp=source["timestamp"],
                url=source["url"],
                start=source["start"]
            )
            for source in sources[:5]  # Limit to 5 sources
        ]
        
        # Create response
        response = ChatResponse(
            answer=result["answer"],
            sources=source_objects,
            video_id=request.video_id
        )
        
        print(f"✅ Answer generated")
        
        return response
        
    except ValueError as e:
        # Vector store not found
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Vector store not found for video: {request.video_id}. Please ingest the video first.",
                    "video_id": request.video_id
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": str(e),
                    "video_id": request.video_id
                }
            )
    
    except Exception as e:
        import traceback
        error_msg = str(e) or "Unknown error"
        print(f"❌ Chat error: {error_msg}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Internal server error: {error_msg}",
                "video_id": request.video_id
            }
        )

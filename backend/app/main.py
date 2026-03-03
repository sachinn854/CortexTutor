"""
Main FastAPI application entry point.
Serves both API and frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.rate_limiter import RateLimitMiddleware
from app.core.timeout import TimeoutMiddleware
from app.core.monitoring import PerformanceMiddleware, global_monitor
import os

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered learning assistant for YouTube videos using RAG",
    debug=settings.debug,
)

# Add CORS middleware - MUST BE FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add rate limiting middleware (60 requests per minute)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Add timeout middleware (5 minutes for long operations)
app.add_middleware(TimeoutMiddleware, timeout_seconds=300)

# Add performance monitoring middleware
app.add_middleware(PerformanceMiddleware, monitor=global_monitor)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📊 Debug mode: {settings.debug}")
    print(f"🤖 LLM: Groq ({settings.groq_model}) - FAST & FREE!")
    print(f"🔍 Embeddings: {settings.embedding_model}")
    print(f"💾 Vector DB: {settings.vector_db_type}")
    print(f"⚡ Rate Limit: 60 req/min")
    print(f"⏱️  Timeout: 300s")
    print(f"🌐 Frontend: http://localhost:8000")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("👋 Shutting down...")


# Frontend path
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")

@app.get("/")
async def serve_frontend():
    """Serve frontend HTML."""
    html_path = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(html_path):
        return {"error": "Frontend not found", "path": html_path}
    return FileResponse(html_path)

@app.get("/styles.css")
async def serve_css():
    """Serve CSS file."""
    return FileResponse(os.path.join(frontend_dir, "styles.css"))

@app.get("/app.js")
async def serve_js():
    """Serve JS file."""
    return FileResponse(os.path.join(frontend_dir, "app.js"))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/metrics")
async def get_metrics():
    """Get performance metrics."""
    from app.core.monitoring import global_monitor, get_system_info
    
    return {
        "performance": global_monitor.get_stats(),
        "endpoints": global_monitor.get_endpoint_stats(),
        "system": get_system_info()
    }


# Include API router
from app.api.router import api_router
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

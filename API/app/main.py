"""
FastAPI main application for Marketing Agent API.

This file creates the web server that wraps our marketing agent
and makes it available as a REST API with async processing.
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn

# Add the parent directory to path so we can import from the main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.config import get_api_config
from app.utils.logging import setup_logging
from app.routes import campaigns, health, websockets
from app.services.task_manager import task_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    
    This function runs when the server starts up and shuts down,
    allowing us to initialize and cleanup resources properly.
    """
    # Startup events
    config = get_api_config()
    logger = setup_logging()
    
    logger.info("🚀 Starting Marketing Agent API Server")
    logger.info(f"📍 Environment: {'Development' if config.debug else 'Production'}")
    logger.info(f"🔧 Max concurrent campaigns: {config.max_concurrent_campaigns}")
    
    # Initialize task manager
    await task_manager.startup()
    logger.info("✅ Task manager initialized")
    
    yield  # Server is running
    
    # Shutdown events
    logger.info("🛑 Shutting down Marketing Agent API Server")
    await task_manager.shutdown()
    logger.info("✅ Cleanup completed")


# Create FastAPI application with metadata
app = FastAPI(
    title="Marketing Agent API",
    description="""
    🎯 **Professional Marketing Campaign Generation API**
    
    Transform natural language into complete marketing campaigns with:
    - 📝 AI-generated marketing copy
    - 🎨 DALL-E generated visuals  
    - 🏷️ Hashtags and call-to-actions
    - 📧 Multi-channel delivery (Email, Instagram, Facebook)
    - 📊 Performance analytics and monitoring
    
    **Perfect for:**
    - Marketing agencies automating campaign creation
    - E-commerce businesses scaling content production
    - Developers building marketing tools
    - Startups needing professional campaigns quickly
    
    ## 🚀 Quick Start
    
    1. Get your API key from the dashboard
    2. Make a POST request to `/api/v1/campaigns`
    3. Monitor progress via WebSocket or polling
    4. Download generated assets when complete
    
    ## 💡 Example
    
    ```python
    import requests
    
    response = requests.post("/api/v1/campaigns", 
        headers={"X-API-Key": "your-key"},
        json={
            "user_input": "promote eco-friendly water bottle for outdoor enthusiasts",
            "options": {"channels": ["instagram", "email"]}
        }
    )
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware for CORS, compression, and monitoring
config = get_api_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers for monitoring."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error responses."""
    logger = setup_logging()
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


# Include API routes
app.include_router(campaigns.router, prefix="/api/v1", tags=["Campaigns"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(websockets.router, prefix="/api/v1", tags=["WebSockets"])


@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint with basic API information."""
    return {
        "message": "🎯 Marketing Agent API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health_check": "/api/v1/health",
        "example_endpoint": "/api/v1/campaigns"
    }


if __name__ == "__main__":
    """
    Development server runner.
    
    In production, use a proper ASGI server like:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    """
    config = get_api_config()
    
    uvicorn.run(
        "app.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.reload,
        log_level=config.log_level.lower()
    )

"""Main FastAPI application."""

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from .core.config import get_settings
from .core.logger import get_logger
from .api import api_router
from .services.redis import redis_service

logger = get_logger(__name__)
settings = get_settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Configure FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for processing PDF documents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with version prefix
app.include_router(api_router, prefix=settings.API_V1_STR)


# Add middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request information and timing."""
    start_time = time.time()
    
    # Get client IP and method + path
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    
    logger.info(f"Request started: {method} {path} from {client_host}")
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(f"Request completed: {method} {path} - {response.status_code} ({process_time:.4f}s)")
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {method} {path} - {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returns API information."""
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Verify Redis connection
        redis_service.connection.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "redis": "disconnected", "error": str(e)}
        ) 
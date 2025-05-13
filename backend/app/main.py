"""Main FastAPI application."""

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from prometheus_fastapi_instrumentator import Instrumentator

from .core.config import get_settings
from .core.logger import get_logger
from .api import api_router
from .services.redis import redis_service

logger = get_logger(__name__)
settings = get_settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
logger.info("Application starting up", extra={
    "app_name": settings.PROJECT_NAME,
    "version": "1.0.0",
    "upload_dir": settings.UPLOAD_DIR
})

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
logger.info("API router configured", extra={"api_prefix": settings.API_V1_STR})

# Instrument FastAPI with Prometheus metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
logger.info("Prometheus metrics instrumentation configured")

# Add middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request information and timing."""
    start_time = time.time()
    
    # Get client IP and method + path
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    query_params = str(request.query_params)
    
    # Log request start with context
    logger.info("Request started", extra={
        "method": method,
        "path": path,
        "client_host": client_host,
        "query_params": query_params,
        "request_id": request.headers.get("X-Request-ID", "unknown")
    })
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log successful request completion
        logger.info("Request completed", extra={
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "process_time": f"{process_time:.4f}s",
            "request_id": request.headers.get("X-Request-ID", "unknown")
        })
        
        return response
    except Exception as e:
        # Log request failure with detailed error information
        logger.error("Request failed", extra={
            "method": method,
            "path": path,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "request_id": request.headers.get("X-Request-ID", "unknown")
        }, exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returns API information."""
    logger.debug("Root endpoint accessed")
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    logger.debug("Health check initiated")
    try:
        # Verify Redis connection
        redis_service.connection.ping()
        logger.info("Health check successful", extra={"redis_status": "connected"})
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        logger.error("Health check failed", extra={
            "redis_status": "disconnected",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }, exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "redis": "disconnected", "error": str(e)}
        ) 
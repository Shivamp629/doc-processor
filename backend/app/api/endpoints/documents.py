"""Document API endpoints."""

import os
import uuid
import shutil
from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import redis

from ...core.config import get_settings
from ...core.logger import get_logger
from ...schemas import JobResponse, ParserType
from ...services.redis import redis_service
from ...services.document import document_service

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.post("/upload", response_model=list, status_code=202)
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    parser: str = Form(...),
):
    """
    Upload PDF files for processing.
    
    - **files**: One or more PDF files to process
    - **parser**: Type of parser to use (pypdf, gemini, mistral)
    
    Returns a list of job IDs and filenames.
    """
    logger.info("Starting file upload", extra={
        "service": "api",
        "endpoint": "upload",
        "file_count": len(files),
        "parser": parser
    })
    
    try:
        # Validate parser
        try:
            parser_type = ParserType(parser)
        except ValueError:
            logger.warning("Invalid parser type received", extra={
                "service": "api",
                "endpoint": "upload",
                "parser": parser,
                "error": "invalid_parser"
            })
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid parser type. Choose from {', '.join([p.value for p in ParserType])}"
            )
        
        job_list = []
        for file in files:
            job_id = str(uuid.uuid4())
            safe_filename = Path(file.filename).name
            content = await file.read()
            
            # Store PDF in Redis
            redis_service.set_pdf(job_id, content)
            logger.info("PDF stored in Redis", extra={
                "service": "api",
                "endpoint": "upload",
                "job_id": job_id,
                "file_name": safe_filename,
                "file_size": len(content)
            })
            
            redis_service.set_job_status(job_id, "pending")
            redis_service.add_to_stream(
                settings.DOCUMENT_STREAM,
                {
                    "job_id": job_id,
                    "parser": parser_type.value,
                    "filename": safe_filename
                }
            )
            job_list.append({"job_id": job_id, "filename": safe_filename})
            
        logger.info("File upload completed", extra={
            "service": "api",
            "endpoint": "upload",
            "job_count": len(job_list),
            "parser": parser
        })
        return job_list
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("File upload failed", extra={
            "service": "api",
            "endpoint": "upload",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_status(job_id: str):
    """
    Get the status of a document processing job.
    
    - **job_id**: ID of the job to check
    
    Returns the current status, extracted markdown content (if available),
    and summary (if available).
    """
    logger.info("Getting job status", extra={
        "service": "api",
        "endpoint": "get_status",
        "job_id": job_id
    })
    
    try:
        job_data = redis_service.get_job_status(job_id)
        
        if not job_data:
            logger.warning("Job not found", extra={
                "service": "api",
                "endpoint": "get_status",
                "job_id": job_id,
                "error": "not_found"
            })
            raise HTTPException(status_code=404, detail="Job not found")
        
        response = JobResponse(
            job_id=job_id,
            status=job_data.get("status", "unknown"),
            markdown=job_data.get("markdown", ""),
            summary=job_data.get("summary", "")
        )
        
        logger.info("Job status retrieved", extra={
            "service": "api",
            "endpoint": "get_status",
            "job_id": job_id,
            "status": response.status,
            "has_markdown": bool(response.markdown),
            "has_summary": bool(response.summary)
        })
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Failed to get job status", extra={
            "service": "api",
            "endpoint": "get_status",
            "job_id": job_id,
            "error_type": type(e).__name__,
            "error_message": str(e)
        }, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")


@router.get("/debug/streams", response_model=Dict[str, Any])
async def debug_streams():
    """
    Debug endpoint to show Redis stream and job status information.
    Returns information about:
    - Active streams
    - Pending jobs
    - Processing jobs
    - Completed jobs
    - Failed jobs
    """
    try:
        conn = redis_service.connection
        
        # Get stream info
        try:
            stream_info = conn.xinfo_stream(settings.DOCUMENT_STREAM)
        except redis.exceptions.ResponseError as e:
            if "no such key" in str(e):
                stream_info = {}
            else:
                raise
        
        # Get consumer group info
        try:
            group_info = conn.xinfo_groups(settings.DOCUMENT_STREAM)
        except redis.exceptions.ResponseError as e:
            if "no such key" in str(e):
                group_info = []
            else:
                raise
        
        # Get pending messages
        try:
            pending_messages = conn.xpending(
                settings.DOCUMENT_STREAM,
                settings.DOCUMENT_CONSUMER_GROUP
            )
        except redis.exceptions.ResponseError as e:
            if "no such key" in str(e):
                pending_messages = [0, None, None, []]
            else:
                raise
        
        # Get all job keys
        job_keys = conn.keys("job:*")
        
        # Get job statuses
        job_statuses = {
            "pending": [],
            "processing": [],
            "done": [],
            "error": []
        }
        
        for job_key in job_keys:
            job_id = job_key.decode('utf-8').split(':')[1]
            job_data = redis_service.get_job_status(job_id)
            if job_data:
                status = job_data.get("status", "unknown")
                if status in job_statuses:
                    job_statuses[status].append({
                        "job_id": job_id,
                        "markdown_length": len(job_data.get("markdown", "")),
                        "summary_length": len(job_data.get("summary", ""))
                    })
        
        # Get Redis info
        redis_info = conn.info()
        
        return {
            "stream_info": {
                "length": stream_info.get(b"length", 0) if isinstance(stream_info, dict) else 0,
                "last_generated_id": stream_info.get(b"last-generated-id", b"").decode('utf-8') if isinstance(stream_info, dict) else "",
                "first_entry": stream_info.get(b"first-entry", []) if isinstance(stream_info, dict) else [],
                "last_entry": stream_info.get(b"last-entry", []) if isinstance(stream_info, dict) else []
            },
            "consumer_groups": [
                {
                    "name": group[b"name"].decode('utf-8'),
                    "consumers": group[b"consumers"],
                    "pending": group[b"pending"],
                    "last_delivered_id": group[b"last-delivered-id"].decode('utf-8')
                }
                for group in group_info
            ] if group_info else [],
            "pending_messages": {
                "count": pending_messages[0],
                "min_id": pending_messages[1].decode('utf-8') if pending_messages[1] else None,
                "max_id": pending_messages[2].decode('utf-8') if pending_messages[2] else None,
                "consumers": [
                    {
                        "name": consumer[b"name"].decode('utf-8'),
                        "count": consumer[b"count"]
                    }
                    for consumer in pending_messages[3]
                ]
            },
            "job_statuses": job_statuses,
            "redis_info": {
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory": redis_info.get("used_memory_human", "0B"),
                "total_connections_received": redis_info.get("total_connections_received", 0),
                "total_commands_processed": redis_info.get("total_commands_processed", 0)
            }
        }
        
    except Exception as e:
        logger.error("Failed to get debug information", extra={
            "service": "api",
            "endpoint": "debug_streams",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting debug information: {str(e)}") 
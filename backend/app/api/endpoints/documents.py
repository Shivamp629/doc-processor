"""Document API endpoints."""

import os
import uuid
import shutil
from typing import List
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from ...core.config import get_settings
from ...core.logger import get_logger
from ...schemas import JobResponse, ParserType
from ...services.redis import redis_service
from ...services.document import document_service

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.post("/upload", response_model=dict, status_code=202)
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    parser: str = Form(...),
):
    """
    Upload PDF files for processing.
    
    - **files**: One or more PDF files to process
    - **parser**: Type of parser to use (pypdf, gemini, mistral)
    
    Returns a job ID that can be used to check the status of the processing.
    """
    try:
        # Validate parser
        try:
            parser_type = ParserType(parser)
        except ValueError:
            logger.warning(f"Invalid parser type: {parser}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid parser type. Choose from {', '.join([p.value for p in ParserType])}"
            )
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        logger.info(f"Creating new job {job_id} with parser {parser_type}")
        
        # Create upload directory for this job
        upload_dir = Path(f"{settings.UPLOAD_DIR}/{job_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize job status
        redis_service.set_job_status(job_id, "pending")
        
        # Save uploaded files and push to Redis Stream
        for file in files:
            # Ensure filename is safe
            safe_filename = Path(file.filename).name
            filepath = upload_dir / safe_filename
            
            # Save the file
            with open(filepath, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"Saved file {safe_filename} for job {job_id}")
            
            # Push to Redis Stream
            redis_service.add_to_stream(
                settings.DOCUMENT_STREAM,
                {
                    "job_id": job_id,
                    "parser": parser_type.value,
                    "filepath": str(filepath.absolute())
                }
            )
        
        return {"job_id": job_id, "message": "Files uploaded for processing"}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_status(job_id: str):
    """
    Get the status of a document processing job.
    
    - **job_id**: ID of the job to check
    
    Returns the current status, extracted markdown content (if available),
    and summary (if available).
    """
    try:
        job_data = redis_service.get_job_status(job_id)
        
        if not job_data:
            logger.warning(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse(
            job_id=job_id,
            status=job_data.get("status", "unknown"),
            markdown=job_data.get("markdown", ""),
            summary=job_data.get("summary", "")
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}") 
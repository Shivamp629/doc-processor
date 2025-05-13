"""Background worker for asynchronous document processing."""

import os
import json
import time
import asyncio
import redis
from datetime import datetime
from io import BytesIO

from .core.config import get_settings
from .core.logger import get_logger
from .schemas import ParserType
from .services.redis import redis_service
from .services.document import document_service

logger = get_logger(__name__)
settings = get_settings()


async def process_document(job_id: str, parser_str: str, filename: str) -> None:
    """
    Process a document based on the selected parser.
    
    Args:
        job_id: Unique job identifier
        parser_str: Selected parser ("pypdf", "gemini", or "mistral")
        filename: Name of the PDF file (for logging)
    """
    logger.info("Starting document processing", extra={
        "job_id": job_id,
        "parser": parser_str,
        "file_name": filename,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        # Update status to processing
        redis_service.set_job_status(job_id, "processing")
        
        # Validate parser type
        try:
            parser_type = ParserType(parser_str)
        except ValueError:
            error_message = f"Unknown parser: {parser_str}"
            logger.error("Invalid parser type", extra={
                "job_id": job_id,
                "parser": parser_str,
                "error": error_message
            })
            redis_service.set_job_status(job_id, "error", error_message, error_message)
            return
        
        # Get PDF bytes from Redis
        logger.debug("Retrieving PDF from Redis", extra={"job_id": job_id})
        pdf_bytes = redis_service.get_pdf(job_id)
        pdf_file = BytesIO(pdf_bytes)
        
        # Get appropriate parser function
        parser_func = document_service.get_parser_function(parser_type)
        
        # Extract content
        logger.info("Extracting content from PDF", extra={
            "job_id": job_id,
            "parser": parser_str,
            "file_size": len(pdf_bytes)
        })
        content = parser_func(pdf_file)
        
        # Generate summary
        logger.info("Generating document summary", extra={"job_id": job_id})
        summary = document_service.summarize_with_gemini(content)
        
        # Update job data in Redis
        redis_service.set_job_status(job_id, "done", content, summary)
        logger.info("Document processing completed", extra={
            "job_id": job_id,
            "status": "done",
            "content_length": len(content),
            "summary_length": len(summary)
        })
        
        # Clean up PDF from Redis
        redis_service.connection.delete(f"pdf:{job_id}")
        logger.debug("Cleaned up PDF from Redis", extra={"job_id": job_id})
        
    except Exception as e:
        # Handle errors
        error_message = f"Error processing document: {str(e)}"
        logger.error("Document processing failed", extra={
            "job_id": job_id,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "parser": parser_str,
            "file_name": filename
        }, exc_info=True)
        redis_service.set_job_status(job_id, "error", error_message, error_message)


async def worker_loop() -> None:
    """
    Continuously read from Redis Stream and process documents.
    """
    conn = redis_service.connection
    worker_id = f"worker-{os.getpid()}"
    
    logger.info("Initializing worker", extra={
        "worker_id": worker_id,
        "stream": settings.DOCUMENT_STREAM,
        "consumer_group": settings.DOCUMENT_CONSUMER_GROUP
    })
    
    # Create consumer group if it doesn't exist
    try:
        conn.xgroup_create(
            settings.DOCUMENT_STREAM, 
            settings.DOCUMENT_CONSUMER_GROUP, 
            id="0", 
            mkstream=True
        )
        logger.info("Created consumer group", extra={
            "consumer_group": settings.DOCUMENT_CONSUMER_GROUP
        })
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            logger.error("Failed to create consumer group", extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            raise
        logger.info("Consumer group already exists", extra={
            "consumer_group": settings.DOCUMENT_CONSUMER_GROUP
        })
    
    logger.info("Worker started", extra={
        "worker_id": worker_id,
        "start_time": datetime.utcnow().isoformat()
    })
    
    while True:
        try:
            # Read new messages from the stream
            entries = conn.xreadgroup(
                settings.DOCUMENT_CONSUMER_GROUP,
                worker_id,
                {settings.DOCUMENT_STREAM: ">"},
                count=1,
                block=5000
            )
            
            if not entries:
                await asyncio.sleep(1)
                continue
            
            for stream_name, messages in entries:
                for message_id, data in messages:
                    # Parse and decode message data
                    job_data = {k.decode('utf-8'): json.loads(v.decode('utf-8')) for k, v in data.items()}
                    
                    logger.info("Processing new message", extra={
                        "worker_id": worker_id,
                        "message_id": message_id.decode('utf-8'),
                        "job_id": job_data.get("job_id"),
                        "parser": job_data.get("parser")
                    })
                    
                    # Process the document
                    await process_document(
                        job_data.get("job_id"),
                        job_data.get("parser"),
                        job_data.get("filename")
                    )
                    
                    # Acknowledge message processing
                    conn.xack(settings.DOCUMENT_STREAM, settings.DOCUMENT_CONSUMER_GROUP, message_id)
                    logger.info("Message acknowledged", extra={
                        "worker_id": worker_id,
                        "message_id": message_id.decode('utf-8')
                    })
        
        except Exception as e:
            logger.error("Worker loop error", extra={
                "worker_id": worker_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        logger.info("Starting worker process", extra={
            "pid": os.getpid(),
            "start_time": datetime.utcnow().isoformat()
        })
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user", extra={
            "pid": os.getpid(),
            "stop_time": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.critical("Worker stopped due to error", extra={
            "pid": os.getpid(),
            "error_type": type(e).__name__,
            "error_message": str(e),
            "stop_time": datetime.utcnow().isoformat()
        }, exc_info=True) 
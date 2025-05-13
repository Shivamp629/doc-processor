"""Background worker for asynchronous document processing."""

import os
import json
import time
import asyncio
import redis
from datetime import datetime

from .core.config import get_settings
from .core.logger import get_logger
from .schemas import ParserType
from .services.redis import redis_service
from .services.document import document_service

logger = get_logger(__name__)
settings = get_settings()


async def process_document(job_id: str, parser_str: str, filepath: str) -> None:
    """
    Process a document based on the selected parser.
    
    Args:
        job_id: Unique job identifier
        parser_str: Selected parser ("pypdf", "gemini", or "mistral")
        filepath: Path to the PDF file
    """
    logger.info(f"Processing job {job_id} with parser {parser_str}")
    
    try:
        # Update status to processing
        redis_service.set_job_status(job_id, "processing")
        
        # Validate parser type
        try:
            parser_type = ParserType(parser_str)
        except ValueError:
            error_message = f"Unknown parser: {parser_str}"
            logger.error(f"Job {job_id}: {error_message}")
            redis_service.set_job_status(job_id, "error", error_message, error_message)
            return
        
        # Ensure file exists
        if not os.path.exists(filepath):
            error_message = f"File not found: {filepath}"
            logger.error(f"Job {job_id}: {error_message}")
            redis_service.set_job_status(job_id, "error", error_message, error_message)
            return
        
        # Get appropriate parser function
        parser_func = document_service.get_parser_function(parser_type)
        
        # Extract content
        content = parser_func(filepath)
        
        # Generate summary
        summary = document_service.summarize_with_gemini(content)
        
        # Update job data in Redis
        redis_service.set_job_status(job_id, "done", content, summary)
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        # Handle errors
        error_message = f"Error processing document: {str(e)}"
        logger.error(f"Job {job_id}: {error_message}", exc_info=True)
        redis_service.set_job_status(job_id, "error", error_message, error_message)


async def worker_loop() -> None:
    """
    Continuously read from Redis Stream and process documents.
    """
    conn = redis_service.connection
    
    # Create consumer group if it doesn't exist
    try:
        conn.xgroup_create(
            settings.DOCUMENT_STREAM, 
            settings.DOCUMENT_CONSUMER_GROUP, 
            id="0", 
            mkstream=True
        )
        logger.info(f"Created consumer group {settings.DOCUMENT_CONSUMER_GROUP}")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            logger.error(f"Error creating consumer group: {str(e)}")
            raise
        logger.info(f"Consumer group {settings.DOCUMENT_CONSUMER_GROUP} already exists")
    
    logger.info(f"Worker started at {datetime.now().isoformat()}")
    
    worker_id = f"worker-{os.getpid()}"
    
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
                    
                    logger.info(f"Worker {worker_id} processing message: {message_id.decode('utf-8')}")
                    
                    # Process the document
                    await process_document(
                        job_data.get("job_id"),
                        job_data.get("parser"),
                        job_data.get("filepath")
                    )
                    
                    # Acknowledge message processing
                    conn.xack(settings.DOCUMENT_STREAM, settings.DOCUMENT_CONSUMER_GROUP, message_id)
                    logger.info(f"Acknowledged message: {message_id.decode('utf-8')}")
        
        except Exception as e:
            logger.error(f"Error in worker loop: {str(e)}", exc_info=True)
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        logger.info("Starting worker process")
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.critical(f"Worker stopped due to error: {str(e)}", exc_info=True) 
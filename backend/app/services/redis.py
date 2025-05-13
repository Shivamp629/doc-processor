"""Redis service for interacting with Redis database."""

import json
import redis
from typing import Dict, Any, Optional

from ..core.config import get_settings
from ..core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RedisService:
    """Service for interacting with Redis."""
    
    def __init__(self, host: str = settings.REDIS_HOST, port: int = settings.REDIS_PORT):
        """Initialize Redis connection."""
        self.redis_host = host
        self.redis_port = port
        self._connection = None
        logger.info("Redis service initialized", extra={
            "service": "redis",
            "host": host,
            "port": port
        })
    
    @property
    def connection(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._connection is None:
            try:
                self._connection = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    decode_responses=False
                )
                # Test connection
                self._connection.ping()
                logger.info("Redis connection established", extra={
                    "service": "redis",
                    "host": self.redis_host,
                    "port": self.redis_port,
                    "status": "connected"
                })
            except redis.ConnectionError as e:
                logger.error("Redis connection failed", extra={
                    "service": "redis",
                    "host": self.redis_host,
                    "port": self.redis_port,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }, exc_info=True)
                raise
        return self._connection
    
    def add_to_stream(self, stream_name: str, data: Dict[str, Any]) -> str:
        """
        Add data to a Redis stream.
        
        Args:
            stream_name: Name of the stream
            data: Dictionary with job details
            
        Returns:
            ID of the stream entry
        """
        try:
            serialized_data = {k: json.dumps(v) for k, v in data.items()}
            entry_id = self.connection.xadd(stream_name, serialized_data)
            logger.info("Added entry to Redis stream", extra={
                "service": "redis",
                "operation": "add_to_stream",
                "stream": stream_name,
                "job_id": data.get("job_id", "unknown"),
                "entry_id": entry_id.decode('utf-8') if isinstance(entry_id, bytes) else entry_id
            })
            return entry_id
        except Exception as e:
            logger.error("Failed to add entry to Redis stream", extra={
                "service": "redis",
                "operation": "add_to_stream",
                "stream": stream_name,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            raise
    
    def set_job_status(self, job_id: str, status: str, markdown: str = "", summary: str = "") -> None:
        """
        Update job status in Redis.
        
        Args:
            job_id: Unique job identifier
            status: Job status (pending, processing, done, error)
            markdown: Extracted markdown content
            summary: Generated summary
        """
        try:
            self.connection.hset(
                f"job:{job_id}",
                mapping={
                    "status": status,
                    "markdown": markdown,
                    "summary": summary
                }
            )
            logger.info("Updated job status in Redis", extra={
                "service": "redis",
                "operation": "set_job_status",
                "job_id": job_id,
                "status": status,
                "markdown_length": len(markdown),
                "summary_length": len(summary)
            })
        except Exception as e:
            logger.error("Failed to update job status in Redis", extra={
                "service": "redis",
                "operation": "set_job_status",
                "job_id": job_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, str]]:
        """
        Get job status from Redis.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Dictionary with job status data or None if not found
        """
        try:
            job_data = self.connection.hgetall(f"job:{job_id}")
            
            if not job_data:
                logger.warning("Job not found in Redis", extra={
                    "service": "redis",
                    "operation": "get_job_status",
                    "job_id": job_id
                })
                return None
            
            # Convert bytes to strings
            result = {k.decode('utf-8'): v.decode('utf-8') for k, v in job_data.items()}
            logger.debug("Retrieved job status from Redis", extra={
                "service": "redis",
                "operation": "get_job_status",
                "job_id": job_id,
                "status": result.get("status", "unknown")
            })
            return result
        except Exception as e:
            logger.error("Failed to get job status from Redis", extra={
                "service": "redis",
                "operation": "get_job_status",
                "job_id": job_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            raise

    def set_pdf(self, job_id: str, pdf_bytes: bytes) -> None:
        """
        Store PDF bytes in Redis under key pdf:{job_id}.
        """
        try:
            self.connection.set(f"pdf:{job_id}", pdf_bytes)
            logger.info("Stored PDF in Redis", extra={
                "service": "redis",
                "operation": "set_pdf",
                "job_id": job_id,
                "pdf_size": len(pdf_bytes)
            })
        except Exception as e:
            logger.error("Failed to store PDF in Redis", extra={
                "service": "redis",
                "operation": "set_pdf",
                "job_id": job_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            raise

    def get_pdf(self, job_id: str) -> bytes:
        """
        Retrieve PDF bytes from Redis by job_id.
        """
        try:
            pdf_bytes = self.connection.get(f"pdf:{job_id}")
            if pdf_bytes is None:
                logger.error("PDF not found in Redis", extra={
                    "service": "redis",
                    "operation": "get_pdf",
                    "job_id": job_id,
                    "error": "not_found"
                })
                raise FileNotFoundError(f"PDF for job {job_id} not found in Redis")
            
            logger.debug("Retrieved PDF from Redis", extra={
                "service": "redis",
                "operation": "get_pdf",
                "job_id": job_id,
                "pdf_size": len(pdf_bytes)
            })
            return pdf_bytes
        except Exception as e:
            logger.error("Failed to retrieve PDF from Redis", extra={
                "service": "redis",
                "operation": "get_pdf",
                "job_id": job_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            raise


# Create a singleton instance
redis_service = RedisService() 
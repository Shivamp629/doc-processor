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
                logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
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
            logger.info(f"Added entry to stream {stream_name}: {data.get('job_id', 'unknown')}")
            return entry_id
        except Exception as e:
            logger.error(f"Failed to add to stream {stream_name}: {str(e)}")
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
            logger.info(f"Updated job {job_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {str(e)}")
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
                logger.warning(f"Job {job_id} not found")
                return None
            
            # Convert bytes to strings
            result = {k.decode('utf-8'): v.decode('utf-8') for k, v in job_data.items()}
            logger.debug(f"Retrieved job status for {job_id}: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {str(e)}")
            raise


# Create a singleton instance
redis_service = RedisService() 
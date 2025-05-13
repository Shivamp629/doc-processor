"""Redis fixtures for testing."""

import pytest
import fakeredis.aioredis
from typing import AsyncGenerator

from app.core.config import get_settings
from app.services.redis import RedisService

settings = get_settings()


@pytest.fixture
async def redis_service() -> AsyncGenerator[RedisService, None]:
    """Create a Redis service using fakeredis for testing."""
    # Create a fake Redis server
    server = fakeredis.aioredis.FakeRedisServer()
    
    # Create a Redis service with the fake server
    service = RedisService(
        host=server.host,
        port=server.port
    )
    
    # Create the document stream and consumer group
    conn = service.connection
    try:
        conn.xgroup_create(
            settings.DOCUMENT_STREAM,
            settings.DOCUMENT_CONSUMER_GROUP,
            id="0",
            mkstream=True
        )
    except Exception:
        # Group might already exist
        pass
    
    yield service
    
    # Cleanup
    await service.connection.close() 
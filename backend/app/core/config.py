"""Application configuration."""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings.

    These settings are loaded from environment variables
    or from the .env file if available.
    """
    PROJECT_NAME: str = "PDF Document Processor"
    API_V1_STR: str = "/api/v1"
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    
    # File storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    
    # Redis streams
    DOCUMENT_STREAM: str = "documents"
    DOCUMENT_CONSUMER_GROUP: str = "document_processors"
    
    class Config:
        """Config for Pydantic settings."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 
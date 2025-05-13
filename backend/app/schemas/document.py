"""Document schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from .parser import ParserType


class DocumentJob(BaseModel):
    """Schema for document job data."""
    
    job_id: str = Field(..., description="Unique identifier for the job")
    parser: ParserType = Field(..., description="Parser to use for processing")
    filepath: str = Field(..., description="Path to the uploaded file")


class JobResponse(BaseModel):
    """Schema for job status response."""
    
    job_id: str = Field(..., description="Unique identifier for the job")
    status: str = Field(..., description="Job status: pending, processing, done, error")
    markdown: str = Field("", description="Extracted markdown content")
    summary: str = Field("", description="Generated summary") 
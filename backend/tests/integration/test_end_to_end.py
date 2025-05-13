"""End-to-end tests for the application."""

import os
import pytest
import httpx
import asyncio
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


@pytest.fixture
async def async_client():
    """Create an async HTTP client."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
def sample_pdf_path():
    """Get path to the sample PDF for testing."""
    # Use our pre-generated sample PDF
    pdf_path = Path(__file__).parent.parent / "data" / "sample.pdf"
    
    # If sample doesn't exist, create it
    if not pdf_path.exists():
        from ..data.create_sample_pdf import create_sample_pdf
        create_sample_pdf(str(pdf_path))
        
    return pdf_path


@pytest.mark.e2e
async def test_document_processing_flow(async_client, sample_pdf_path):
    """Test the complete document processing flow."""
    # Upload file
    with open(sample_pdf_path, "rb") as f:
        response = await async_client.post(
            "/api/v1/documents/upload",
            files={"files": ("sample.pdf", f, "application/pdf")},
            data={"parser": "pypdf"}
        )
    
    assert response.status_code == 202
    data = response.json()
    job_id = data["job_id"]
    
    # Poll for job completion
    max_attempts = 30  # 30 seconds timeout
    for _ in range(max_attempts):
        response = await async_client.get(f"/api/v1/documents/{job_id}")
        assert response.status_code == 200
        
        data = response.json()
        if data["status"] == "done":
            break
        
        await asyncio.sleep(1)
    else:
        pytest.fail("Job processing timed out")
    
    # Verify results
    assert len(data["markdown"]) > 100
    assert len(data["summary"]) < 500
    assert "PDF Document Processor" in data["markdown"]


@pytest.mark.e2e
async def test_health_check(async_client):
    """Test the health check endpoint."""
    response = await async_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "redis" in data 
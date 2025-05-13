"""Integration tests for Redis streams."""

import asyncio
import pytest
import threading
from pathlib import Path

from app.worker import worker_loop
from app.services.document import document_service
from app.schemas import ParserType


@pytest.mark.integration
async def test_document_processing(redis_service, tmp_path):
    """Test document processing through Redis streams."""
    # Create a test PDF file
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest PDF content")
    
    # Start worker in background thread
    worker_thread = threading.Thread(
        target=lambda: asyncio.run(worker_loop()),
        daemon=True
    )
    worker_thread.start()
    
    try:
        # Add job to Redis stream
        job_id = "test-job-123"
        redis_service.add_to_stream(
            "documents",
            {
                "job_id": job_id,
                "parser": ParserType.PYPDF.value,
                "filepath": str(pdf_path)
            }
        )
        
        # Wait for processing (max 10 seconds)
        for _ in range(10):
            job_data = redis_service.get_job_status(job_id)
            if job_data and job_data.get("status") == "done":
                break
            await asyncio.sleep(1)
        
        # Get final job status
        job_data = redis_service.get_job_status(job_id)
        
        # Assert job was processed
        assert job_data is not None
        assert job_data["status"] == "done"
        assert len(job_data["markdown"]) > 0
        assert len(job_data["summary"]) > 0
    
    finally:
        # Cleanup
        worker_thread.join(timeout=1) 
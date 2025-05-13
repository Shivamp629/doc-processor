"""Unit tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_upload_file_success(client, tmp_path, mock_redis_service):
    """Test successful file upload."""
    # Create a test PDF file
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest PDF content")
    
    # Upload file
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            files={"files": ("test.pdf", f, "application/pdf")},
            data={"parser": "pypdf"}
        )
    
    # Assert response
    assert response.status_code == 202
    data = response.json()
    assert isinstance(data, list)
    assert "job_id" in data[0]
    assert "filename" in data[0]


@pytest.mark.unit
def test_upload_file_missing(client):
    """Test file upload with missing file."""
    response = client.post(
        "/api/v1/documents/upload",
        data={"parser": "pypdf"}
    )
    
    assert response.status_code == 422


@pytest.mark.unit
def test_upload_file_invalid_parser(client, tmp_path):
    """Test file upload with invalid parser."""
    # Create a test PDF file
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest PDF content")
    
    # Upload file with invalid parser
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            files={"files": ("test.pdf", f, "application/pdf")},
            data={"parser": "invalid_parser"}
        )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.unit
def test_get_status_not_found(client, mock_redis_service):
    """Test getting status for non-existent job."""
    # Configure mock for this test case
    mock_redis_service.get_job_status.return_value = None
    
    response = client.get("/api/v1/documents/nonexistent-job-id")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.unit
def test_get_status_pending(client, mock_redis_service):
    """Test getting status for pending job."""
    # Configure mock for this test case  
    mock_redis_service.get_job_status.return_value = {
        "status": "pending",
        "markdown": "",
        "summary": ""
    }
    
    response = client.get("/api/v1/documents/test-job-id")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["markdown"] == ""
    assert data["summary"] == ""


@pytest.mark.unit
def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["redis"] == "connected" 
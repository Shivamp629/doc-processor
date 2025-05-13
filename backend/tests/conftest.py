"""Fixtures for tests."""

import os
import pytest
import fakeredis
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.core.config import get_settings
from app.services.redis import RedisService, redis_service
from app.services.document import DocumentService, document_service


@pytest.fixture
def test_settings():
    """Override settings for testing."""
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "fake_api_key",
        "UPLOAD_DIR": "test_uploads",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "DOCUMENT_STREAM": "documents:test",
        "DOCUMENT_CONSUMER_GROUP": "processors:test"
    }):
        yield get_settings()


@pytest.fixture
def mock_redis_service():
    """Mock Redis service with fakeredis."""
    # Create a mock for redis_service with all required methods
    mock_service = MagicMock()
    
    # Mock common methods
    mock_service.add_to_stream.return_value = "1-0"
    mock_service.set_job_status.return_value = None
    mock_service.get_job_status.return_value = {
        "status": "pending",
        "markdown": "",
        "summary": ""
    }
    
    # Create a mock connection and ping method
    mock_connection = MagicMock()
    mock_connection.ping.return_value = True
    mock_connection.hset.return_value = 1
    mock_connection.hgetall.return_value = {
        b"status": b"pending",
        b"markdown": b"",
        b"summary": b""
    }
    mock_connection.xadd.return_value = "1-0"
    
    # Replace all instances of redis_service
    with patch('app.services.redis.redis_service', mock_service):
        with patch('app.services.redis.redis_service.connection', mock_connection):
            with patch('app.api.endpoints.documents.redis_service', mock_service):
                with patch('app.main.redis_service', mock_service):
                    yield mock_service


@pytest.fixture
def test_upload_dir():
    """Create a temporary upload directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_upload_dir = os.environ.get("UPLOAD_DIR")
        os.environ["UPLOAD_DIR"] = temp_dir
        yield Path(temp_dir)
        if old_upload_dir:
            os.environ["UPLOAD_DIR"] = old_upload_dir
        else:
            del os.environ["UPLOAD_DIR"]


@pytest.fixture
def sample_pdf_path(test_upload_dir):
    """Create a sample PDF file at a temporary location."""
    from .data.create_sample_pdf import create_sample_pdf
    
    pdf_path = test_upload_dir / "sample.pdf"
    create_sample_pdf(str(pdf_path))
    
    yield pdf_path


@pytest.fixture
def mock_gemini():
    """Mock the Gemini API."""
    with patch('google.generativeai.GenerativeModel') as mock_model_class:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "# Mocked Markdown\n\nThis is a **mocked** response from Gemini.\n\n## Section 1\n\nTest content."
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        with patch('app.services.document.settings.GEMINI_API_KEY', "fake_api_key"):
            yield mock_model_class


@pytest.fixture
def client(test_settings, mock_redis_service, mock_gemini):
    """Create a test client."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    return TestClient(app) 
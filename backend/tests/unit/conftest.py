"""Common fixtures for unit tests."""

import os
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from pathlib import Path

from app.core.config import get_settings
from app.services.document import DocumentService


@pytest.fixture
def test_env():
    """Patch environment variables for testing."""
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "fake_api_key",
        "UPLOAD_DIR": "test_uploads",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379"
    }):
        yield


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF file at a temporary location."""
    from ..data.create_sample_pdf import create_sample_pdf
    
    pdf_path = tmp_path / "sample.pdf"
    create_sample_pdf(str(pdf_path))
    
    yield pdf_path
    
    # Cleanup
    if pdf_path.exists():
        pdf_path.unlink()


@pytest.fixture
def document_service(test_env):
    """Create a document service with test settings."""
    return DocumentService()


@pytest.fixture
def mock_gemini_response():
    """Mock responses from Gemini API."""
    with patch("google.generativeai.GenerativeModel") as mock_model:
        # Setup mock for generating text
        mock_response = MagicMock()
        mock_response.text = "# Mocked Markdown\n\nThis is a **mocked** response from Gemini.\n\n## Section 1\n\nTest content."
        mock_model.return_value.generate_content.return_value = mock_response
        
        yield mock_model 
"""Unit tests for document service."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.document import DocumentService, document_service
from app.schemas import ParserType


@pytest.fixture
def mock_mistral():
    """Mock Mistral API client."""
    with patch('app.services.document.MistralClient') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.chat.return_value.choices = [
            MagicMock(message=MagicMock(content="Enhanced OCR text from Mistral"))
        ]
        yield mock_instance


@pytest.mark.unit
def test_extract_with_pypdf(sample_pdf_path):
    """Test PyPDF extraction."""
    # Call the function
    result = document_service.extract_with_pypdf(sample_pdf_path)
    
    # Assert expected content in result
    assert "PDF Document Processor - Test Document" in result
    assert "sample PDF file created for testing" in result
    assert "multi-page extraction" in result  # From page 2
    assert "Page 2 - Additional Information" in result


@pytest.mark.unit
def test_extract_with_gemini(sample_pdf_path, mock_gemini):
    """Test Gemini extraction with mocked API response."""
    # Call the function
    result = document_service.extract_with_gemini(sample_pdf_path)
    
    # Assert expected content in result
    assert "Mocked Markdown" in result
    assert "mocked" in result
    assert "Section 1" in result


@pytest.mark.unit
def test_extract_with_mistral_no_api_key(sample_pdf_path):
    """Test Mistral extraction without API key (stubbed)."""
    # Temporarily remove API key
    original_key = document_service.mistral_client
    document_service.mistral_client = None
    
    try:
        result = document_service.extract_with_mistral(sample_pdf_path)
        assert "Stubbed Mistral OCR output" in result
    finally:
        # Restore API key
        document_service.mistral_client = original_key


@pytest.mark.unit
def test_extract_with_mistral_with_api_key(sample_pdf_path, mock_mistral, monkeypatch):
    """Test Mistral extraction with API key (mocked)."""
    # Patch settings to simulate API key
    monkeypatch.setattr("app.services.document.settings.MISTRAL_API_KEY", "dummy-key")
    # Set up mock client
    document_service.mistral_client = mock_mistral
    
    result = document_service.extract_with_mistral(sample_pdf_path)
    assert "Enhanced OCR text from Mistral" in result
    
    # Verify Mistral API was called
    mock_mistral.chat.assert_called_once()


@pytest.mark.unit
def test_extract_with_mistral_api_error(sample_pdf_path, mock_mistral, monkeypatch):
    """Test Mistral extraction with API error (fallback to PyPDF)."""
    # Patch settings to simulate API key
    monkeypatch.setattr("app.services.document.settings.MISTRAL_API_KEY", "dummy-key")
    # Set up mock to raise exception
    mock_mistral.chat.side_effect = Exception("API Error")
    
    # Set up mock client
    document_service.mistral_client = mock_mistral
    
    result = document_service.extract_with_mistral(sample_pdf_path)
    # Should fall back to PyPDF2 extraction
    assert "PDF Document Processor - Test Document" in result


@pytest.mark.unit
def test_summarize_with_gemini(mock_gemini):
    """Test summarization with mocked Gemini API."""
    # Test input
    test_content = "This is some test content to summarize."
    
    # Call the function
    result = document_service.summarize_with_gemini(test_content)
    
    # Assert summary generated
    assert "Mocked Markdown" in result or "mocked" in result
    assert "Section 1" in result


@pytest.mark.unit
def test_get_parser_function():
    """Test getting parser functions."""
    service = DocumentService()
    
    # Test PyPDF parser
    parser_func = service.get_parser_function(ParserType.PYPDF)
    assert callable(parser_func)
    assert parser_func == service.extract_with_pypdf
    
    # Test Gemini parser
    parser_func = service.get_parser_function(ParserType.GEMINI)
    assert callable(parser_func)
    assert parser_func == service.extract_with_gemini
    
    # Test Mistral parser
    parser_func = service.get_parser_function(ParserType.MISTRAL)
    assert callable(parser_func)
    assert parser_func == service.extract_with_mistral
    
    # Test invalid parser
    with pytest.raises(ValueError):
        service.get_parser_function("invalid_parser") 
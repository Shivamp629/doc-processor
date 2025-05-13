"""Unit tests for document service."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.document import DocumentService, document_service
from app.schemas import ParserType


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
def test_extract_with_mistral(sample_pdf_path):
    """Test Mistral extraction (which currently uses PyPDF)."""
    # Call the function
    result = document_service.extract_with_mistral(sample_pdf_path)
    
    # This should match PyPDF extraction since Mistral is stubbed
    assert "PDF Document Processor - Test Document" in result
    assert "Page 2 - Additional Information" in result


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
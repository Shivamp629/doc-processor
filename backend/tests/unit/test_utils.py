"""Unit tests for utility functions."""

import pytest
from unittest.mock import patch
from io import BytesIO

from app.schemas import ParserType
from app.services.document import DocumentService


@pytest.fixture
def sample_pdf():
    """Create a simple PDF for testing."""
    # We'll use a simple BytesIO object as a mock PDF
    pdf_bytes = BytesIO(b"%PDF-1.4\nTest PDF content\n%%EOF")
    return pdf_bytes


@pytest.mark.unit
def test_get_parser_function():
    """Test parser function mapping."""
    service = DocumentService()
    
    # Test each parser type
    for parser_type in ParserType:
        parser_func = service.get_parser_function(parser_type)
        assert callable(parser_func)
    
    # Test invalid parser
    with pytest.raises(ValueError):
        service.get_parser_function("invalid_parser") 
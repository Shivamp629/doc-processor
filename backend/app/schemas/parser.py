"""Parser type schema."""

from enum import Enum


class ParserType(str, Enum):
    """Available document parsers."""
    
    PYPDF = "pypdf"
    GEMINI = "gemini"
    MISTRAL = "mistral" 
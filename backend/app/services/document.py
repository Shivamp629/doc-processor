"""Document processing service."""

import os
import PyPDF2
import google.generativeai as genai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from pathlib import Path
from typing import Dict, Any

from ..core.config import get_settings
from ..core.logger import get_logger
from ..schemas import ParserType

logger = get_logger(__name__)
settings = get_settings()


class DocumentService:
    """Service for document processing operations."""
    
    def __init__(self):
        """Initialize document service."""
        self.upload_dir = settings.UPLOAD_DIR
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Configure Gemini API if key is available
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            logger.info("Gemini API configured", extra={
                "service": "document",
                "api": "gemini",
                "status": "configured"
            })
        else:
            logger.warning("Gemini API key not configured", extra={
                "service": "document",
                "api": "gemini",
                "status": "not_configured"
            })
            
        # Configure Mistral API if key is available
        if settings.MISTRAL_API_KEY:
            self.mistral_client = MistralClient(api_key=settings.MISTRAL_API_KEY)
            logger.info("Mistral API configured", extra={
                "service": "document",
                "api": "mistral",
                "status": "configured"
            })
        else:
            self.mistral_client = None
            logger.warning("Mistral API key not configured", extra={
                "service": "document",
                "api": "mistral",
                "status": "not_configured"
            })
    
    def extract_with_pypdf(self, file_obj) -> str:
        """
        Extract text from PDF using PyPDF2.
        
        Args:
            file_obj: File-like object (BytesIO or file)
            
        Returns:
            Extracted text
        """
        logger.info("Starting PDF extraction with PyPDF", extra={
            "service": "document",
            "parser": "pypdf",
            "operation": "extract"
        })
        try:
            text = ""
            reader = PyPDF2.PdfReader(file_obj)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += f"--- Page {page_num + 1} ---\n\n{page_text}\n\n"
            
            logger.info("PDF extraction completed", extra={
                "service": "document",
                "parser": "pypdf",
                "operation": "extract",
                "pages": len(reader.pages),
                "text_length": len(text)
            })
            return text
        except Exception as e:
            logger.error("PDF extraction failed", extra={
                "service": "document",
                "parser": "pypdf",
                "operation": "extract",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            raise
    
    def extract_with_gemini(self, file_obj) -> str:
        """
        Extract and convert PDF to markdown using Google Gemini.
        
        Args:
            file_obj: File-like object (BytesIO or file)
            
        Returns:
            Markdown-formatted content
        """
        logger.info("Starting PDF extraction with Gemini", extra={
            "service": "document",
            "parser": "gemini",
            "operation": "extract"
        })
        
        if not settings.GEMINI_API_KEY:
            logger.error("Gemini API key not configured", extra={
                "service": "document",
                "parser": "gemini",
                "operation": "extract",
                "error": "api_key_missing"
            })
            raise ValueError("Gemini API key not configured")
        
        try:
            # First extract text with PyPDF2
            raw_text = self.extract_with_pypdf(file_obj)
            
            # Use Gemini to convert to markdown
            model = genai.GenerativeModel(model_name="gemini-2.0-flash")
            
            prompt = f"""
            Convert the following PDF content to well-structured markdown. 
            Create headers, lists, and proper formatting:
            
            {raw_text}
            """
            
            response = model.generate_content(prompt)
            logger.info("PDF extraction completed with Gemini", extra={
                "service": "document",
                "parser": "gemini",
                "operation": "extract",
                "raw_text_length": len(raw_text),
                "markdown_length": len(response.text)
            })
            return response.text
        except Exception as e:
            logger.error("PDF extraction failed with Gemini", extra={
                "service": "document",
                "parser": "gemini",
                "operation": "extract",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            raise
    
    def extract_with_mistral(self, file_obj) -> str:
        """
        Extract text from PDF using Mistral OCR API.
        If MISTRAL_API_KEY is set, uses real OCR API.
        Otherwise, returns a stubbed string for testing.
        
        Args:
            file_obj: File-like object (BytesIO or file)
        Returns:
            Extracted text (real OCR output or stubbed)
        """
        logger.info("Starting PDF extraction with Mistral", extra={
            "service": "document",
            "parser": "mistral",
            "operation": "extract"
        })
        
        if not settings.MISTRAL_API_KEY:
            logger.warning("Mistral API key not set, using stubbed output", extra={
                "service": "document",
                "parser": "mistral",
                "operation": "extract",
                "mode": "stubbed"
            })
            return "[Stubbed Mistral OCR output for testing]"
        
        try:
            # First extract text with PyPDF2 as fallback
            raw_text = self.extract_with_pypdf(file_obj)
            
            # Use Mistral to enhance the text with OCR capabilities
            messages = [
                ChatMessage(role="system", content="You are an OCR enhancement service. Improve the text extraction by fixing any OCR errors and formatting issues."),
                ChatMessage(role="user", content=f"Please enhance this extracted text, fixing any OCR errors and improving formatting:\n\n{raw_text}")
            ]
            
            chat_response = self.mistral_client.chat(
                model="mistral-tiny",  # Using tiny model for OCR enhancement
                messages=messages
            )
            
            enhanced_text = chat_response.choices[0].message.content
            logger.info("PDF extraction completed with Mistral", extra={
                "service": "document",
                "parser": "mistral",
                "operation": "extract",
                "raw_text_length": len(raw_text),
                "enhanced_text_length": len(enhanced_text)
            })
            return enhanced_text
            
        except Exception as e:
            logger.error("PDF extraction failed with Mistral", extra={
                "service": "document",
                "parser": "mistral",
                "operation": "extract",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            # Fallback to PyPDF2 extraction if Mistral fails
            logger.info("Falling back to PyPDF2 extraction", extra={
                "service": "document",
                "parser": "mistral",
                "operation": "fallback",
                "fallback_parser": "pypdf"
            })
            return self.extract_with_pypdf(file_obj)
    
    def summarize_with_gemini(self, content: str) -> str:
        """
        Summarize content using Google Gemini.
        
        Args:
            content: Content to summarize
            
        Returns:
            Summary text
        """
        logger.info("Starting content summarization", extra={
            "service": "document",
            "operation": "summarize",
            "content_length": len(content)
        })
        
        if not settings.GEMINI_API_KEY:
            logger.error("Gemini API key not configured", extra={
                "service": "document",
                "operation": "summarize",
                "error": "api_key_missing"
            })
            raise ValueError("Gemini API key not configured")
        
        try:
            model = genai.GenerativeModel(model_name="gemini-2.0-flash")
            
            prompt = f"""
            Provide a concise summary of the following document content. 
            Focus on the key points and main ideas:
            
            {content}
            """
            
            response = model.generate_content(prompt)
            logger.info("Content summarization completed", extra={
                "service": "document",
                "operation": "summarize",
                "input_length": len(content),
                "summary_length": len(response.text)
            })
            return response.text
        except Exception as e:
            logger.error("Content summarization failed", extra={
                "service": "document",
                "operation": "summarize",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)
            raise
    
    def get_parser_function(self, parser_type: ParserType):
        """
        Get the appropriate parser function based on the parser type.
        
        Args:
            parser_type: Type of parser to use
            
        Returns:
            Parser function
        """
        parser_map = {
            ParserType.PYPDF: self.extract_with_pypdf,
            ParserType.GEMINI: self.extract_with_gemini,
            ParserType.MISTRAL: self.extract_with_mistral,
        }
        
        parser_func = parser_map.get(parser_type)
        if not parser_func:
            logger.error("Unknown parser type", extra={
                "service": "document",
                "operation": "get_parser",
                "parser_type": str(parser_type),
                "error": "unknown_parser"
            })
            raise ValueError(f"Unknown parser type: {parser_type}")
        
        logger.debug("Parser function retrieved", extra={
            "service": "document",
            "operation": "get_parser",
            "parser_type": str(parser_type)
        })
        return parser_func


# Create a singleton instance
document_service = DocumentService() 
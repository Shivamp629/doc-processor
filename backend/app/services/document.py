"""Document processing service."""

import os
import PyPDF2
import google.generativeai as genai
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
            logger.info("Gemini API configured")
        else:
            logger.warning("Gemini API key not configured")
    
    def extract_with_pypdf(self, filepath: str) -> str:
        """
        Extract text from PDF using PyPDF2.
        
        Args:
            filepath: Path to the PDF file
            
        Returns:
            Extracted text
        """
        logger.info(f"Extracting text from {filepath} using PyPDF")
        try:
            text = ""
            with open(filepath, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    text += f"--- Page {page_num + 1} ---\n\n{page_text}\n\n"
            
            logger.info(f"Successfully extracted {len(reader.pages)} pages from {filepath}")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from {filepath}: {str(e)}")
            raise
    
    def extract_with_gemini(self, filepath: str) -> str:
        """
        Extract and convert PDF to markdown using Google Gemini.
        
        Args:
            filepath: Path to the PDF file
            
        Returns:
            Markdown-formatted content
        """
        logger.info(f"Extracting text from {filepath} using Gemini")
        
        if not settings.GEMINI_API_KEY:
            logger.error("Gemini API key not configured")
            raise ValueError("Gemini API key not configured")
        
        try:
            # First extract text with PyPDF2
            raw_text = self.extract_with_pypdf(filepath)
            
            # Use Gemini to convert to markdown
            model = genai.GenerativeModel(model_name="gemini-2.0-flash")
            
            prompt = f"""
            Convert the following PDF content to well-structured markdown. 
            Create headers, lists, and proper formatting:
            
            {raw_text}
            """
            
            response = model.generate_content(prompt)
            logger.info(f"Successfully converted {filepath} to markdown using Gemini")
            return response.text
        except Exception as e:
            logger.error(f"Failed to extract text with Gemini from {filepath}: {str(e)}")
            raise
    
    def extract_with_mistral(self, filepath: str) -> str:
        """
        Stub function for Mistral integration.
        For now, just returns PyPDF2 extracted text.
        
        Args:
            filepath: Path to the PDF file
            
        Returns:
            Extracted text
        """
        logger.info(f"Extracting text from {filepath} using Mistral (stubbed)")
        return self.extract_with_pypdf(filepath)
    
    def summarize_with_gemini(self, content: str) -> str:
        """
        Summarize content using Google Gemini.
        
        Args:
            content: Content to summarize
            
        Returns:
            Summary text
        """
        logger.info("Generating summary with Gemini")
        
        if not settings.GEMINI_API_KEY:
            logger.error("Gemini API key not configured")
            raise ValueError("Gemini API key not configured")
        
        try:
            model = genai.GenerativeModel(model_name="gemini-2.0-flash")
            
            prompt = f"""
            Provide a concise summary of the following document content. 
            Focus on the key points and main ideas:
            
            {content}
            """
            
            response = model.generate_content(prompt)
            logger.info("Successfully generated summary")
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
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
            logger.error(f"Unknown parser type: {parser_type}")
            raise ValueError(f"Unknown parser type: {parser_type}")
        
        return parser_func


# Create a singleton instance
document_service = DocumentService() 
"""Create a sample PDF file for testing."""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
from pathlib import Path


def create_sample_pdf(output_path: str) -> None:
    """
    Create a sample PDF file for testing.
    
    Args:
        output_path: Path where to save the PDF file
    """
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Create a new PDF with Reportlab
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Add content to the PDF
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "PDF Document Processor - Test Document")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "This is a sample PDF file created for testing the document processing application.")
    c.drawString(100, 680, "It contains multiple paragraphs of text to test extraction and summarization.")
    
    # Add a second paragraph
    c.drawString(100, 630, "Second Paragraph - Important Information")
    c.drawString(100, 610, "This PDF contains critical test information that should be properly extracted")
    c.drawString(100, 590, "and summarized by the document processing service.")
    
    # Add a third paragraph
    c.drawString(100, 540, "Third Paragraph - Technical Details")
    c.drawString(100, 520, "The document processing service supports multiple parsers:")
    c.drawString(120, 500, "- PyPDF2 for basic text extraction")
    c.drawString(120, 480, "- Google Gemini for advanced markdown parsing")
    c.drawString(120, 460, "- Mistral for future OCR integration")
    
    # Add a second page
    c.showPage()
    
    # Content for page 2
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "Page 2 - Additional Information")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "This is the second page of the test document.")
    c.drawString(100, 680, "It tests the multi-page extraction capabilities of the service.")
    
    # Save the PDF
    c.save()
    print(f"Sample PDF created at: {output_path}")


if __name__ == "__main__":
    # Create sample PDF in the current directory
    current_dir = Path(__file__).parent
    sample_pdf_path = current_dir / "sample.pdf"
    create_sample_pdf(str(sample_pdf_path)) 
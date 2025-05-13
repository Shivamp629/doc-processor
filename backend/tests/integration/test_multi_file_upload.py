import os
import pytest
import httpx
from pathlib import Path
from unittest.mock import patch, MagicMock

PARSERS = ["pypdf", "gemini", "mistral"]
PDFS = [
    ("test1.pdf", b"%PDF-1.4\nTest PDF 1\n%%EOF"),
    ("test2.pdf", b"%PDF-1.4\nTest PDF 2\n%%EOF"),
]

@pytest.mark.integration
def test_multi_file_upload_all_parsers():
    backend_url = os.getenv("API_URL", "http://localhost:8000/api/v1")
    
    # Mock Mistral API for consistent testing
    with patch('app.services.document.MistralClient') as mock_mistral:
        mock_instance = mock_mistral.return_value
        mock_instance.chat.return_value.choices = [
            MagicMock(message=MagicMock(content="Enhanced OCR text from Mistral"))
        ]
        
        for parser in PARSERS:
            files = [("files", (name, content, "application/pdf")) for name, content in PDFS]
            data = {"parser": parser}
            with httpx.Client() as client:
                try:
                    resp = client.post(f"{backend_url}/documents/upload", files=files, data=data, timeout=2)
                except httpx.ConnectError:
                    pytest.skip("Backend API is not running. Skipping integration test.")
                assert resp.status_code == 202
                jobs = resp.json()
                assert isinstance(jobs, list) and len(jobs) == 2
                for job in jobs:
                    job_id = job["job_id"]
                    # Poll for job status
                    for _ in range(10):
                        status_resp = client.get(f"{backend_url}/documents/{job_id}")
                        assert status_resp.status_code == 200
                        status = status_resp.json()
                        if status["status"] == "done":
                            break
                        import time; time.sleep(1)
                    assert status["status"] == "done"
                    # Validate output for each parser
                    if parser == "mistral":
                        assert "Enhanced OCR text from Mistral" in status["markdown"]
                    elif parser == "gemini":
                        # Gemini is mocked in tests, so check for mocked output
                        assert "Mocked Markdown" in status["markdown"] or "mocked" in status["markdown"]
                    else:
                        # PyPDF should contain PDF text
                        assert "Test PDF" in status["markdown"] 
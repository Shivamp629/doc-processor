# PDF Document Processing Service

A production-ready application for processing PDF documents, extracting their content as markdown, and generating summaries.

## CRITICAL SYSTEM NOTICE

**THIS SYSTEM IS MISSION-CRITICAL AND DESIGNED FOR LIFE-SAVING OPERATIONS**

This application processes documents containing vital information that may impact human safety. Proper functioning of all components is essential. Any failures in document processing, parsing accuracy, or system availability could have serious consequences.

- All changes must undergo thorough testing
- Continuous monitoring is required when deployed
- Error handling and fallbacks must be maintained at all times

## Features

- **Document Processing**: Upload and process PDFs with multiple parser options
  - `pypdf`: Basic text extraction using PyPDF2
  - `gemini`: Advanced parsing to Markdown using Google Gemini 2.0 Flash
  - `mistral`: Stub for future OCR integration
- **Asynchronous Processing**: Redis Streams for reliable job processing
- **AI-Powered Summarization**: Auto-generate summaries using Google Gemini 2.0 Flash
- **Real-time Status Updates**: Track document processing status
- **Modern UI**: Clean, responsive interface for uploading and viewing processed documents

## Testing and Verification

The system includes comprehensive testing to ensure reliability:

### Automated Tests

Run the full test suite:
```bash
cd backend
python -m pytest
```

Run specific test categories:
```bash
# Unit tests only
python -m pytest -m unit

# Integration tests only
python -m pytest -m integration

# End-to-end tests
python -m pytest -m e2e

# With coverage report
python -m pytest --cov=app
```

### Manual Testing with Postman

A Postman collection is included for manual API testing:
1. Import `postman/DocumentProcessor.postman_collection.json` into Postman
2. Ensure the backend is running
3. Execute the requests in sequence:
   - Health check
   - Upload document
   - Get job status

### Test Sample Documents

Sample PDF documents for testing are automatically generated during the test runs, but you can also manually create them:
```bash
cd backend
python tests/data/create_sample_pdf.py
```

### Deployment Verification

After deployment, verify system health:
```bash
# Check backend health
curl http://localhost:8000/health

# Verify Redis connection
docker-compose exec redis redis-cli ping

# Monitor logs
docker-compose logs -f
```

## Architecture

The application follows a modern microservices architecture:

- **Backend**: FastAPI-based REST API with asyncio for concurrent processing
- **Worker**: Background processor for handling document extraction and summarization
- **Frontend**: Next.js application with TypeScript and React
- **Database**: Redis for caching and message queue

## Project Structure

```
/
├── backend/                   # Backend service
│   ├── app/                   # Application code
│   │   ├── api/               # API routes
│   │   ├── core/              # Core functionality (config, logging)
│   │   ├── schemas/           # Pydantic models for validation
│   │   ├── services/          # Business logic services
│   │   ├── main.py            # FastAPI application
│   │   └── worker.py          # Background worker
│   ├── tests/                 # Test suite
│   │   ├── unit/              # Unit tests
│   │   ├── integration/       # Integration tests 
│   │   ├── fixtures/          # Test fixtures
│   │   └── data/              # Test data and generators
│   ├── Dockerfile             # Backend service Dockerfile
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Next.js frontend
│   ├── app/                   # Next.js application
│   ├── components/            # React components
│   ├── lib/                   # Utility functions
│   └── Dockerfile             # Frontend Dockerfile
├── postman/                   # Postman collection for API testing
├── docker-compose.yml         # Docker Compose configuration
├── .env.example               # Example environment variables
└── README.md                  # Project documentation
```

## Setup and Deployment

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key (for advanced parsing and summarization)

### Configuration

1. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

2. Add your API keys to the `.env` file:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

### Building and Running

Deploy with Docker Compose:

```bash
docker-compose up -d --build
```

This will start:
- Backend API on http://localhost:8000
- Frontend on http://localhost:3000
- Redis database
- Background worker

## API Documentation

When running, the API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

#### Upload Document
```http
POST /api/v1/documents/upload
```

Request:
- `files`: One or more PDF files (form-data)
- `parser`: Parser type to use (pypdf, gemini, mistral)

Response:
```json
{
  "job_id": "unique-job-id",
  "message": "Files uploaded for processing"
}
```

#### Get Processing Status
```http
GET /api/v1/documents/{job_id}
```

Response:
```json
{
  "job_id": "unique-job-id",
  "status": "pending|processing|done|error",
  "markdown": "Processed markdown content",
  "summary": "Generated summary"
}
```

## Developer Guide

### Backend Development

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Run the API:
```bash
uvicorn app.main:app --reload
```

4. Run the worker:
```bash
python -m app.worker
```

### Frontend Development

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

## License

MIT 
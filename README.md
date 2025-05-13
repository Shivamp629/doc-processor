# PDF Document Processor

## Production Checklist
- [x] Async backend with FastAPI, Redis Streams, and worker
- [x] PDF storage in Redis (not local disk)
- [x] Structured JSON logging
- [x] Prometheus metrics at /metrics
- [x] Grafana dashboard for metrics visualization
- [x] Multi-file upload and per-file job tracking
- [x] Frontend with sidebar/history, error and empty states
- [x] One-line run: `make prod`
- [x] One-line test: `make test`
- [x] Hot reload development environment: `make dev`

## Quick Start
```bash
# Production
make prod
# Visit http://localhost:3000 (frontend)
# Visit http://localhost:8000/docs (API docs)
# Visit http://localhost:8000/metrics (Prometheus metrics)
# Visit http://localhost:3001 (Grafana dashboard with username/password - admin/admin)

# Development with Hot Reload
make dev
# Same URLs as above, but with hot reloading enabled
```

## Development Environment

### Local Development (without Docker)
```bash
# Setup development environment
make setup-dev

# Run backend API with hot reload
make backend-dev

# Run worker process
make worker-dev

# Run frontend with hot reload
make frontend-dev
```

### Docker Development (with Hot Reload)
```bash
# Start all services with hot reload
make dev

# Stop development services
make dev-down
```

The development environment includes:
- Hot reloading for both backend and frontend
- Source code mounted as volumes
- Development-specific configurations
- Automatic restart on code changes

## Architecture
- **FastAPI** backend with async endpoints
- **Redis Streams** for job queue
- **Worker** for async processing
- **PDFs stored in Redis** as binary blobs
- **Prometheus metrics** for observability
- **Next.js frontend** with sidebar/history

## Metrics and Monitoring

The application includes comprehensive metrics and monitoring:

### Prometheus Metrics
- Exposed at `/metrics` (Prometheus format)
- Tracks: request count, job count, job errors, durations
- Available at http://localhost:9090 (Prometheus UI)

### Grafana Dashboard
- Available at http://localhost:3001
- Default credentials: admin/admin
- Pre-configured with:
  - Request rate and latency
  - Job processing metrics
  - Error rates
  - System health indicators

### Key Metrics Tracked
- API request latency and count
- Job processing status and duration
- Error rates and types
- Redis connection health
- Worker queue length
- PDF processing success/failure rates

## Testing
```bash
make test
```

## Troubleshooting
- Check logs: `docker-compose logs api worker frontend`
- Check Redis: `docker-compose exec redis redis-cli keys '*job*'`
- Check metrics: `curl http://localhost:8000/metrics`

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
│   ├── Dockerfile.dev         # Development Dockerfile with hot reload
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Next.js frontend
│   ├── app/                   # Next.js application
│   ├── components/            # React components
│   ├── Dockerfile             # Frontend Dockerfile
│   ├── Dockerfile.dev         # Development Dockerfile with hot reload
│   └── package.json          # Node.js dependencies
├── postman/                   # Postman collection for API testing
├── docker-compose.yml         # Docker Compose configuration
├── docker-compose.dev.yml     # Development Docker Compose with hot reload
├── Makefile                  # Build and run commands
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

## Running Integration Tests

Some integration tests require the backend API server to be running (e.g., multi-file upload, end-to-end tests).

To run these tests:

1. Start the backend server in one terminal:
   ```bash
   make backend-dev
   # or
   uvicorn app.main:app --reload
   ```
2. In another terminal, run the tests:
   ```bash
   cd backend
   python -m pytest
   ```

If the backend is not running, these tests will be automatically skipped.
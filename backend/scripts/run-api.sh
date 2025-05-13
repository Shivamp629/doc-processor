#!/bin/bash
set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run FastAPI application
echo "Starting API server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@" 
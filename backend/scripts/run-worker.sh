#!/bin/bash
set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run worker
echo "Starting document processing worker..."
python -m app.worker 
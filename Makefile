.PHONY: build run stop down logs clean test backend-dev frontend-dev

# Docker compose commands
build:
	docker-compose build

run:
	docker-compose up -d

stop:
	docker-compose stop

down:
	docker-compose down

logs:
	docker-compose logs -f

# Development commands
backend-dev:
	cd backend && ./scripts/run-api.sh --reload

worker-dev:
	cd backend && ./scripts/run-worker.sh

frontend-dev:
	cd frontend && npm run dev

# Clean up commands
clean:
	docker-compose down -v
	rm -rf uploads/*

# Test commands
test:
	echo "Running tests..."
	cd backend && python -m pytest

# Install dependencies
install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

# Setup complete development environment
setup-dev: install-backend install-frontend
	@echo "Development environment setup complete"
	@echo "Run 'make backend-dev' to start the backend API server"
	@echo "Run 'make worker-dev' to start the worker process"
	@echo "Run 'make frontend-dev' to start the frontend development server"

# Setup .env file
setup-env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created. Please edit it with your API keys."; \
	else \
		echo ".env file already exists."; \
	fi

# Help command
help:
	@echo "Available commands:"
	@echo "  make build          - Build Docker images"
	@echo "  make run            - Run all services in Docker"
	@echo "  make stop           - Stop all services"
	@echo "  make down           - Stop and remove containers"
	@echo "  make logs           - Show logs from all services"
	@echo "  make clean          - Remove all containers and volumes"
	@echo "  make backend-dev    - Run backend API in development mode"
	@echo "  make worker-dev     - Run worker in development mode"
	@echo "  make frontend-dev   - Run frontend in development mode"
	@echo "  make test           - Run tests"
	@echo "  make setup-dev      - Install all development dependencies"
	@echo "  make setup-env      - Create .env file from example" 
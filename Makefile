.PHONY: help setup dev build up down logs test clean

help:
	@echo "Available commands:"
	@echo "  make setup     - Install dependencies and setup environment"
	@echo "  make dev       - Run in development mode"
	@echo "  make build     - Build Docker images"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - View logs"
	@echo "  make test      - Run tests"
	@echo "  make clean     - Clean up containers and volumes"

setup:
	@echo "Setting up development environment..."
	cp backend/.env.example backend/.env
	cp frontend/.env.example frontend/.env.local
	python -m venv venv
	source venv/bin/activate && pip install -r backend/requirements-dev.txt
	@echo "Setup complete! Don't forget to add your API keys to backend/.env"

dev:
	@echo "Starting development environment..."
	docker-compose up

build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started. Frontend: http://localhost:3000, Backend API: http://localhost:8000/docs"

down:
	@echo "Stopping all services..."
	docker-compose down

logs:
	docker-compose logs -f

test-backend:
	cd backend && pytest tests/ -v --cov=. --cov-report=html

test-frontend:
	cd frontend && npm test

test: test-backend test-frontend

clean:
	@echo "Cleaning up containers, volumes, and data..."
	docker-compose down -v
	rm -rf data/
	rm -rf backend/data/
	rm -rf frontend/.next/
	@echo "Cleanup complete"

seed-docs:
	@echo "Seeding demo documents..."
	docker-compose exec backend python scripts/seed_demo_documents.py

migrate:
	@echo "Running database migrations..."
	docker-compose exec backend alembic upgrade head

shell-backend:
	docker-compose exec backend python

shell-db:
	docker-compose exec postgres psql -U postgres

lint-backend:
	cd backend && ruff check .

format-backend:
	cd backend && black .

lint-frontend:
	cd frontend && npm run lint

.PHONY: help setup dev build up down logs test clean seed-docs migrate
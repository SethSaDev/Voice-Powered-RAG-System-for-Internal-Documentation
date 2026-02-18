.PHONY: help setup dev build up down logs test clean

help:
	@echo "Available commands:"
	@echo "  make dev       - Run in development mode"
	@echo "  make build     - Build Docker images"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"

dev:
	docker-compose up

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

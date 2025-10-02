.PHONY: help setup up build down logs clean test

# Default target
help:
	@echo "Available commands:"
	@echo "  setup - Copy .env.example to .env (run this first)"
	@echo "  up    - Start all services"
	@echo "  build - Build and start all services"
	@echo "  down  - Stop all services"
	@echo "  logs  - Show logs from all services"
	@echo "  test  - Run tests"
	@echo "  clean - Remove all containers and volumes"

# Setup environment file
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "📝 Please edit .env and add your OpenWeatherMap API key"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Start all services
up:
	docker compose up

# Build and start all services
build:
	docker compose up --build

# Stop all services
down:
	docker compose down

# Show logs
logs:
	docker compose logs -f

# Run tests
test:
	docker compose exec flask-app python test_unit.py
	docker compose exec flask-app python test_integration.py

# Clean up everything
clean:
	docker compose down -v --rmi all --remove-orphans
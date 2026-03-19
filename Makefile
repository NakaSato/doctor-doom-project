# Makefile for Doctor Doom Project

.PHONY: help dev prod stop clean test build up down logs shell monitoring seed demo

# Default target
help:
	@echo "Doctor Doom Project - Makefile Commands"
	@echo "========================================"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start all services (development)"
	@echo "  make prod         - Start all services (production)"
	@echo "  make stop         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo ""
	@echo "Docker:"
	@echo "  make build        - Build all Docker images"
	@echo "  make build-service SERVICE=name - Build specific service"
	@echo "  make up           - Start containers"
	@echo "  make down         - Stop and remove containers"
	@echo "  make logs         - View logs (tail -f)"
	@echo "  make logs-service SERVICE=name - View specific service logs"
	@echo "  make shell SERVICE=name - Open shell in service container"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-service SERVICE=name - Run tests for specific service"
	@echo "  make lint         - Run linters"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-seed      - Seed database with sample data"
	@echo "  make seed         - Seed database (alias)"
	@echo "  make db-backup    - Backup PostgreSQL database"
	@echo "  make db-restore   - Restore PostgreSQL database"
	@echo ""
	@echo "Monitoring:"
	@echo "  make monitoring   - Start Prometheus/Grafana/Loki stack"
	@echo ""
	@echo "Demo:"
	@echo "  make demo         - Generate demo data files"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove containers and volumes"
	@echo "  make clean-all    - Remove everything including images"
	@echo ""

# Development
dev:
	docker compose up -d

prod:
	docker compose -f docker-compose.prod.yml up -d

stop:
	docker compose down

restart:
	docker compose restart

# Docker
build:
	docker compose build

build-service:
	docker compose build $(SERVICE)

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

logs-service:
	docker compose logs -f $(SERVICE)

shell:
	docker compose exec $(SERVICE) /bin/bash

# Testing
test:
	docker compose -f docker-compose.test.yml up --abort-on-container-exit

test-service:
	cd services/$(SERVICE) && pytest

lint:
	ruff check services/
	black --check services/

# Database
db-migrate:
	docker compose exec postgres psql -U postgres -d doctor_doom -f /docker-entrypoint-initdb.d/init.sql

db-seed:
	docker compose exec postgres psql -U postgres -d doctor_doom -c "\i /seed_data.sql"

db-backup:
	docker compose exec postgres pg_dump -U postgres doctor_doom > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	docker compose exec -T postgres psql -U postgres doctor_doom < $(FILE)

# Cleanup
clean:
	docker compose down -v

clean-all:
	docker compose down -v --rmi all --remove-orphans

# Health check
health:
	@echo "Checking service health..."
	@for port in 8000 8001 8002 8003 8004 7800; do \
		if curl -s http://localhost:$$port/health > /dev/null; then \
			echo "✓ Port $$port is healthy"; \
		else \
			echo "✗ Port $$port is NOT responding"; \
		fi; \
	done

# MinIO
minio-create-buckets:
	docker compose run --rm minio-setup

# Development helpers
dev-psql:
	docker compose exec postgres psql -U postgres -d doctor_doom

dev-redis:
	docker compose exec redis redis-cli

dev-minio:
	open http://localhost:9001

# Setup
setup:
	cp .env.example .env
	mkdir -p data models reports logs
	docker compose up -d postgres timescaledb redis minio
	sleep 5
	make db-migrate
	make minio-create-buckets
	@echo "Setup complete! Run 'make dev' to start all services."

# Monitoring
monitoring:
	docker compose -f docker-compose.monitoring.yml up -d
	@echo "Monitoring started!"
	@echo "  Grafana: http://localhost:3001 (admin/admin123)"
	@echo "  Prometheus: http://localhost:9090"

# Seed database
seed:
	docker compose cp infra/postgres/seed_data.sql postgres:/seed_data.sql
	docker compose exec -T postgres psql -U postgres -d doctor_doom -c "\i /seed_data.sql"
	@echo "Database seeded with demo data!"

# Demo data generator
demo:
	./scripts/generate-demo-data.sh

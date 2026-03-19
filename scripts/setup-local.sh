#!/bin/bash
# Doctor Doom - Local Development Setup Script
# This script sets up and starts all services locally

set -e

echo "========================================"
echo "Doctor Doom - Local Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker Desktop first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check Node.js (for frontend)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓ Node.js installed: ${NODE_VERSION}${NC}"
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p data models reports logs
mkdir -p frontend/node_modules

# Copy environment file
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please update .env with your configuration${NC}"
fi

# Create frontend .env
if [ ! -f frontend/.env ]; then
    echo -e "\n${YELLOW}Creating frontend .env file...${NC}"
    cp frontend/.env.example frontend/.env
    echo -e "${GREEN}✓ Frontend .env file created${NC}"
fi

# Start infrastructure services first
echo -e "\n${YELLOW}Starting infrastructure services...${NC}"
docker compose up -d postgres timescaledb redis minio minio-setup

echo -e "\n${YELLOW}Waiting for databases to be ready (30 seconds)...${NC}"
sleep 30

# Seed database
echo -e "\n${YELLOW}Seeding database with demo data...${NC}"
docker compose exec -T postgres psql -U postgres -d doctor_doom -f /docker-entrypoint-initdb.d/init.sql 2>/dev/null || true
docker compose exec -T postgres psql -U postgres -d doctor_doom -c "\i /seed_data.sql" 2>/dev/null || \
    docker compose cp infra/postgres/seed_data.sql postgres:/seed_data.sql && \
    docker compose exec -T postgres psql -U postgres -d doctor_doom -c "\i /seed_data.sql"
echo -e "${GREEN}✓ Database seeded${NC}"

# Start all backend services
echo -e "\n${YELLOW}Starting backend services...${NC}"
docker compose up -d
echo -e "${GREEN}✓ Backend services started${NC}"

# Install frontend dependencies and start
if command -v node &> /dev/null; then
    echo -e "\n${YELLOW}Setting up frontend...${NC}"
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    
    echo -e "\n${YELLOW}Starting frontend dev server...${NC}"
    npm run dev &
    cd ..
    echo -e "${GREEN}✓ Frontend started${NC}"
fi

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Health check
echo -e "\n${YELLOW}Running health checks...${NC}"
services=("api-gateway:8000" "ml-inference:8001" "report:8002" "notify:8003" "geo:7800" "auth:8004")

for service in "${services[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    if curl -s "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${name} (port ${port}) is healthy${NC}"
    else
        echo -e "${RED}✗ ${name} (port ${port}) is NOT responding${NC}"
    fi
done

# Print access information
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Doctor Doom is now running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Access URLs:${NC}"
echo -e "  Frontend:       http://localhost:3000"
echo -e "  API Gateway:    http://localhost:8000"
echo -e "  API Docs:       http://localhost:8000/docs"
echo -e "  MinIO Console:  http://localhost:9001"
echo -e "  Grafana:        http://localhost:3001 (admin/admin123)"
echo -e "  Prometheus:     http://localhost:9090"
echo -e "\n${YELLOW}Demo Credentials:${NC}"
echo -e "  Email:    admin@doctor-doom.com"
echo -e "  Password: admin123"
echo -e "\n${YELLOW}Useful Commands:${NC}"
echo -e "  make logs           - View all logs"
echo -e "  make stop           - Stop all services"
echo -e "  make dev-psql       - Access PostgreSQL CLI"
echo -e "  make dev-redis      - Access Redis CLI"
echo -e ""

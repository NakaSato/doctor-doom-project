#!/bin/bash
# Doctor Doom - Quick Start Script
# One-command startup for local development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "☀️  Doctor Doom - Starting Local Development"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Creating .env from template..."
    cp .env.example .env
fi

# Check if frontend .env exists
if [ ! -f frontend/.env ]; then
    echo "⚠️  Creating frontend/.env from template..."
    cp frontend/.env.example frontend/.env
fi

# Start all services
echo "🚀 Starting Docker services..."
docker compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

# Health check
echo ""
echo "🏥 Health Checks:"
for port in 8000 8001 8002 8003 8004 7800; do
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✓ Port $port responding"
    else
        echo "  ✗ Port $port NOT responding"
    fi
done

echo ""
echo "========================================"
echo "✅ Doctor Doom is running!"
echo "========================================"
echo ""
echo "📍 Access Points:"
echo "   API Gateway:    http://localhost:8000"
echo "   API Docs:       http://localhost:8000/docs"
echo "   MinIO Console:  http://localhost:9001"
echo ""
echo "🔐 Demo Login:"
echo "   Email:    admin@doctor-doom.com"
echo "   Password: admin123"
echo ""
echo "📋 Useful Commands:"
echo "   make logs         - View logs"
echo "   make stop         - Stop services"
echo "   make health       - Run health checks"
echo ""

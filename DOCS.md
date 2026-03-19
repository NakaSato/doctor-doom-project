# Doctor Doom - Complete System Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Quick Start](#quick-start)
4. [Services](#services)
5. [Frontend](#frontend)
6. [API Reference](#api-reference)
7. [Deployment](#deployment)
8. [Monitoring](#monitoring)
9. [Development](#development)
10. [Troubleshooting](#troubleshooting)

---

## Overview

**Doctor Doom** is a comprehensive thermal panel inspection system for autonomous solar panel defect detection using drone thermal imagery.

### Key Features

- 🚁 **Drone Integration** - DJI Mavic 3T thermal image processing
- 🤖 **ML Pipeline** - Four-stage defect detection cascade
- 🗺️ **Spatial Analysis** - PostGIS-powered geospatial queries
- 📊 **Real-time Monitoring** - Redis Streams message bus
- 📈 **Telemetry Tracking** - TimescaleDB time-series analysis
- 📋 **Report Generation** - IEC 62446-3 compliant reports
- 🔔 **Alert System** - Multi-channel notifications

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.11) |
| Frontend | React 19 + TypeScript |
| Message Bus | Redis Streams |
| Databases | PostgreSQL+PostGIS, TimescaleDB |
| Storage | MinIO (S3-compatible) |
| ML | ONNX Runtime, CoreML |
| Maps | Deck.gl + Mapbox |
| Monitoring | Prometheus + Grafana + Loki |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   React     │  │   Mobile    │  │   CLI       │              │
│  │   Frontend  │  │   App       │  │   Tools     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────────────┐
│                      API Gateway (8000)                          │
│                    Authentication & Routing                       │
└─────────┬────────────────┬────────────────┬─────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────────────┐
│                     Redis Streams Bus                            │
│  thermal:ingest → thermal:calibrated → defect:detected          │
│                                           → report:requested     │
└─────────┬────────────────┬────────────────┬─────────────────────┘
          │                │                │
┌─────────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐              │
│   Ingest       │  │    ML       │  │   Report    │              │
│   Worker       │  │  Inference  │  │  Service    │              │
│   (8005)       │  │   (8001)    │  │   (8002)    │              │
└────────────────┘  └─────────────┘  └─────────────┘              │
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────────────┐
│                      Data Persistence Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  PostgreSQL │  │ TimescaleDB │  │    MinIO    │              │
│  │  + PostGIS  │  │  Telemetry  │  │   Storage   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker Desktop (with Compose)
- Node.js 20+ (for frontend)
- Python 3.11+ (optional, for service development)
- 16GB RAM minimum

### One-Command Start

```bash
# Clone and setup
git clone https://github.com/your-org/doctor-doom-project.git
cd doctor-doom-project

# Quick start (starts all services)
./scripts/quick-start.sh

# Or using make
make setup
make dev
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | admin@doctor-doom.com / admin123 |
| API Docs | http://localhost:8000/docs | Same as above |
| MinIO | http://localhost:9001 | minioadmin / minioadmin |
| Grafana | http://localhost:3001 | admin / admin123 |
| Prometheus | http://localhost:9090 | - |

### Verify Installation

```bash
# Check all services
make health

# View logs
make logs

# Access database
make dev-psql
```

---

## Services

### Backend Microservices

| Service | Port | Description |
|---------|------|-------------|
| `api-gateway` | 8000 | Central API entry point, request routing |
| `ml-inference` | 8001 | Four-stage ML defect detection |
| `report` | 8002 | PDF/HTML/JSON report generation |
| `notify` | 8003 | Email/SMS/Webhook notifications |
| `geo` | 7800 | Spatial data (PostGIS) & telemetry |
| `ingest-worker` | 8005 | L2 ingestion pipeline |
| `auth` | 8004 | JWT authentication & authorization |

### Service Communication

Services communicate via:
1. **HTTP/REST** - Synchronous requests (API Gateway → Services)
2. **Redis Streams** - Asynchronous processing pipeline

### Redis Streams Channels

```
thermal:ingest       → Raw thermal images from API
thermal:calibrated   → Processed images for ML
defect:detected      → ML results for notification
report:requested     → Report generation jobs
```

---

## Frontend

### Tech Stack

- React 19 + TypeScript
- Vite 6 (build tool)
- Zustand (state management)
- React Query (server state)
- Tailwind CSS 4 (styling)
- Deck.gl + Mapbox (maps)
- Recharts (visualization)

### Views

| View | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Fleet overview, health scores |
| Array Map | `/map` | Thermal heatmap visualization |
| Defect Log | `/defects` | Defect table with filters |
| Module Inspector | `/modules/:id` | Thermal viewer + telemetry |
| Comparison | `/comparison` | Multi-inspection comparison |
| Reports | `/reports` | Report builder |
| Flight Planner | `/flight-planner` | Waypoint mission planning |

### Frontend Commands

```bash
cd frontend

npm run dev      # Start dev server
npm run build    # Production build
npm run test     # Run tests
npm run test:e2e # E2E tests
```

---

## API Reference

### Authentication

```bash
# Register
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "secure123",
  "full_name": "User Name"
}

# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "secure123"
}
```

### Sites & Modules

```bash
# List sites
GET /api/v1/sites

# Get site with modules
GET /api/v1/sites/{site_id}

# Get module telemetry
GET /api/v1/modules/{module_id}/telemetry?days=30
```

### Defects

```bash
# List defects (filterable)
GET /api/v1/defects?site_id=site_001&severity=critical

# Get module defects
GET /api/v1/modules/{module_id}/defects
```

### Ingestion

```bash
# Submit thermal image
POST /api/v1/ingest/thermal
{
  "image_id": "img_001",
  "module_id": "mod_001",
  "inspection_id": "insp_001"
}
```

### Reports

```bash
# Generate report
POST /api/v1/reports/generate
site_id=site_001&inspection_id=insp_001&format=pdf
```

**Full API documentation:** http://localhost:8000/docs

---

## Deployment

### Local Development

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Edge Deployment (Mac M2)

```bash
# Optimized for edge with resource limits
docker compose -f docker-compose.edge.yml up -d
```

### Monitoring Stack

```bash
# Start monitoring services
docker compose -f docker-compose.monitoring.yml up -d
```

---

## Monitoring

### Prometheus Metrics

- Service health (`up`)
- Request rates (`http_requests_total`)
- Response latency (`http_request_duration_seconds`)
- Redis memory (`redis_memory_used_bytes`)
- PostgreSQL connections (`pg_stat_activity_count`)

### Grafana Dashboards

1. **System Overview** - Service health, request rates
2. **ML Pipeline** - Queue lengths, inference times
3. **Database** - Connections, query performance

### Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| ServiceDown | `up == 0` for 1m | Critical |
| HighErrorRate | 5xx rate > 10% | Warning |
| HighLatency | p95 > 1s | Warning |
| RedisHighMemory | > 90% | Warning |
| MLQueueBacklog | > 100 items | Warning |

---

## Development

### Project Structure

```
doctor-doom-project/
├── services/           # Backend microservices
│   ├── api-gateway/
│   ├── ml-inference/
│   ├── report/
│   ├── notify/
│   ├── geo/
│   ├── ingest-worker/
│   └── auth/
├── frontend/           # React application
├── infra/              # Infrastructure configs
│   ├── postgres/
│   ├── timescaledb/
│   ├── monitoring/
│   └── aws/
├── tests/              # Integration tests
├── scripts/            # Utility scripts
└── docker-compose.yml
```

### Running Tests

```bash
# Backend unit tests (per service)
cd services/api-gateway
pytest

# Frontend tests
cd frontend
npm run test

# Integration tests
pytest tests/integration/

# E2E tests
cd frontend
npm run test:e2e
```

### Code Style

```bash
# Backend
ruff check services/
black --check services/

# Frontend
cd frontend
npm run lint
npm run format
```

---

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check Docker resources
docker stats

# View service logs
docker compose logs <service-name>

# Restart specific service
docker compose restart <service-name>
```

**Database connection errors:**
```bash
# Check database is running
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U postgres -d doctor_doom

# Re-seed database
docker compose exec postgres psql -U postgres -d doctor_doom -f /seed_data.sql
```

**Frontend build errors:**
```bash
# Clear cache
cd frontend
rm -rf node_modules
npm install

# Check Node version
node -v  # Should be 20+
```

**Redis connection issues:**
```bash
# Check Redis is running
docker compose exec redis redis-cli ping

# View stream info
docker compose exec redis redis-cli XINFO STREAM thermal:ingest
```

### Getting Help

1. Check logs: `make logs`
2. Run health checks: `make health`
3. Review API docs: http://localhost:8000/docs
4. Check Grafana: http://localhost:3001

---

## License

Proprietary - All rights reserved

## Support

For issues and questions, open an issue on GitHub or contact the development team.

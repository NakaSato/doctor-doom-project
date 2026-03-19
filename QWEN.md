# Doctor Doom Project - Qwen Context

## Project Overview

**Doctor Doom** is a comprehensive microservices-based thermal panel inspection system for autonomous solar panel defect detection using drone thermal imagery. The system processes RJPEG thermal images from DJI Mavic 3T drones, runs a four-stage ML cascade for defect detection, and generates detailed inspection reports.

### Architecture Summary

- **7 Microservices** (FastAPI/Python 3.11) communicating via **Redis Streams**
- **Edge deployment**: Mac M2 offline operation with CoreML acceleration
- **4 data stores**: PostgreSQL+PostGIS, TimescaleDB, MinIO, Redis
- **4 Redis Streams channels**: `thermal:ingest`, `thermal:calibrated`, `defect:detected`, `report:requested`

## Directory Structure

```
doctor-doom-project/
├── services/
│   ├── api-gateway/     # Port 8000 - Central API entry point
│   ├── ml-inference/    # Port 8001 - Four-stage ML defect detection
│   ├── report/          # Port 8002 - PDF/HTML/JSON report generation
│   ├── notify/          # Port 8003 - Email/SMS/Webhook notifications
│   ├── geo/             # Port 7800 - Spatial data (PostGIS) & telemetry
│   ├── ingest-worker/   # Port 8005 - L2 ingestion pipeline
│   └── auth/            # Port 8004 - JWT authentication & authorization
├── frontend/            # React 19 + TypeScript SPA
│   ├── src/
│   │   ├── components/  # Reusable components (layout, charts, thermal)
│   │   ├── views/       # Page views (Dashboard, Map, Defects, etc.)
│   │   ├── hooks/       # React Query hooks
│   │   ├── stores/      # Zustand stores (auth, UI, selection)
│   │   ├── services/    # API client
│   │   ├── types/       # TypeScript types
│   │   └── styles/      # Tailwind CSS + custom styles
│   └── tests/           # Vitest + Playwright tests
├── infra/
│   ├── postgres/        # PostgreSQL + PostGIS init schema
│   ├── timescaledb/     # TimescaleDB telemetry hypertables
│   └── redis/, minio/   # Infrastructure configs
├── shared/              # Shared config and protobuf definitions
├── .github/workflows/   # CI/CD pipelines
├── docker-compose.yml   # Full orchestration (11 containers)
├── Makefile             # Development commands
└── docs: README.md, ARCHITECTURE.md, API.md
```

## Building and Running

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- 16GB RAM minimum (32GB recommended)

### Quick Start Commands

```bash
# Setup (first time)
make setup

# Start all services
make dev
# Or: docker compose up -d

# Check health
make health

# View logs
make logs
make logs-service SERVICE=ml-inference  # Specific service

# Stop services
make stop

# Clean up (remove containers and volumes)
make clean
```

### Service-Specific Commands

```bash
# Build all images
make build

# Build specific service
make build-service SERVICE=api-gateway

# Open shell in container
make shell SERVICE=geo

# Access databases
make dev-psql    # PostgreSQL
make dev-redis   # Redis CLI
make dev-minio   # MinIO console (http://localhost:9001)
```

### Local Development (Single Service)

```bash
cd services/api-gateway
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Testing

```bash
# All services
make test

# Specific service
make test-service SERVICE=auth

# Linting
make lint
```

### Database Operations

```bash
# Run migrations
make db-migrate

# Backup
make db-backup

# Restore
make db-restore FILE=backup_20260318_120000.sql
```

## Frontend Architecture

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 19 + TypeScript 5.x | Type-safe component development |
| Build Tool | Vite 6 | Fast HMR, ESM-native builds |
| State Management | Zustand + React Query | Global state + server cache |
| Styling | Tailwind CSS 4 | Utility-first design system |
| Map Engine | Deck.gl + Mapbox GL JS | GPU-accelerated geospatial rendering |
| Charting | Recharts + D3.js | Declarative charts |
| Thermal Viewer | Custom WebGL Canvas | 16-bit thermal image rendering |
| 3D Visualization | Three.js + R3F | 3D array model with thermal overlay |
| Testing | Vitest + Playwright | Unit, integration, E2E coverage |

### Key Views

| View | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Fleet overview with health scores, alerts |
| Array Map | `/map` | Interactive thermal heatmap with defect overlays |
| Defect Log | `/defects` | Sortable, filterable defect table |
| Module Inspector | `/modules/:id` | Side-by-side thermal + RGB viewer |
| Comparison | `/comparison` | Before/after inspection comparison |
| Report Builder | `/reports` | IEC 62446-3 compliant report generation |
| Flight Planner | `/flight-planner` | Waypoint mission planning |

### State Management

```typescript
// Zustand stores
import { useAuthStore, useUIStore, useSelectionStore } from '@/stores';

// React Query hooks
import { useSites, useDefects, useDashboardStats } from '@/hooks/useQueries';
```

### Frontend Commands

```bash
cd frontend

# Development
npm run dev          # Start dev server (port 3000)

# Build
npm run build        # Production build
npm run preview      # Preview production build

# Test
npm run test         # Vitest unit tests
npm run test:e2e     # Playwright E2E tests

# Lint/Format
npm run lint
npm run format
```

### Environment Variables

```bash
# frontend/.env
VITE_MAPBOX_TOKEN=pk.your_token_here
VITE_API_URL=http://localhost:8000/api/v1
```

## Service Details

### API Gateway (Port 8000)
- Central entry point for all client requests
- Routes to backend services via HTTP or Redis Streams
- CORS enabled for frontend access
- Endpoints: `/api/v1/*` for all services

### ML Inference (Port 8001)
- Four-stage ML cascade: hotspot detection → cell anomaly → severity → temp delta
- Performance target: <35ms/module (Mac M2 CoreML)
- Reads from `thermal:calibrated` stream

### Report Service (Port 8002)
- Generates PDF, HTML, JSON reports
- Uploads to MinIO `reports` bucket
- Processes `report:requested` stream

### Notify Service (Port 8003)
- Multi-channel: Email (SMTP), SMS (Twilio), Slack webhooks, Push (FCM)
- Automatic alerts for critical defects
- Processes `defect:detected` stream

### Geo Service (Port 7800)
- PostGIS spatial queries (sites, modules, defects)
- TimescaleDB telemetry time-series
- Endpoints: `/sites`, `/modules`, `/defects`, `/inspections`, `/spatial/*`

### Ingest Worker (Port 8005)
- L2 pipeline: RJPEG parser → metadata extractor → calibration → upload
- Processes `thermal:ingest` → publishes to `thermal:calibrated`
- Background workers for ingestion and orthomosaic stitching

### Auth Service (Port 8004)
- JWT authentication (HS256, 30min access, 7-day refresh)
- RBAC: operator, admin, super_admin roles
- Password hashing with bcrypt

## Infrastructure

### Redis Streams (Message Bus)

| Channel | Producer | Consumer | Purpose |
|---------|----------|----------|---------|
| `thermal:ingest` | API Gateway | Ingest Worker | Raw thermal images |
| `thermal:calibrated` | Ingest Worker | ML Inference | Processed images |
| `defect:detected` | ML Inference | Notify Service | Defect results |
| `report:requested` | API Gateway | Report Service | Report jobs |

### Database Schema (PostgreSQL + PostGIS)

**Core Tables:**
- `sites` - Polygon geometry, area, module count
- `modules` - Point geometry, orientation, tilt, rated power
- `inspections` - Linestring flight path, drone/pilot info
- `thermal_images` - Image metadata, GPS location
- `defects` - Defect type, severity, bounding box, temperature delta
- `reports` - Report status, format, S3 key
- `users` - Auth credentials, roles
- `audit_log` - Action tracking

### TimescaleDB (Telemetry)

- `module_telemetry` hypertable: temperature, power output, efficiency
- Continuous aggregates: hourly and daily rollups
- Compression policy: 7 days
- Retention policy: 2 years (commented out by default)

### MinIO Buckets

- `thermal-images` - Raw and calibrated thermal imagery
- `reports` - Generated inspection reports (public read)
- `models` - ML model artifacts

## Development Conventions

### Code Style
- **Python**: Type hints with Pydantic models
- **FastAPI**: Async/await pattern throughout
- **Settings**: Pydantic Settings for environment config

### Testing Practices
- pytest with async support
- Coverage reporting to Codecov
- Matrix testing across all services in CI

### Commit/PR Workflow
1. Create feature branch: `git checkout -b feature/my-feature`
2. Write tests alongside features
3. Run linting: `ruff check .`, `black --check .`
4. Submit PR to `main` or `develop`

### Environment Configuration

Copy `.env.example` to `.env` and configure:
- `JWT_SECRET_KEY` - Change for production
- `SMTP_*` - Email notifications
- `SLACK_WEBHOOK_URL` - Slack alerts

## CI/CD Pipeline

**Trigger**: Push to `main` or `develop`, PRs to `main`

**Stages:**
1. **Test** - Matrix test across all 7 services
2. **Build** - Build and push Docker images to GHCR
3. **Security Scan** - Trivy vulnerability scanning
4. **Deploy Edge** - Mac M2 deployment (if `main`)

**Images tagged with:**
- Branch name
- PR number
- SHA
- Semver (if tagged)

## API Quick Reference

### Authentication
```bash
POST /api/v1/auth/register  # Register user
POST /api/v1/auth/login     # Get JWT tokens
GET  /api/v1/auth/me        # Current user (requires auth)
```

### Core Operations
```bash
GET    /api/v1/sites                 # List sites
GET    /api/v1/sites/{id}            # Site details with modules
POST   /api/v1/ingest/thermal        # Submit thermal image
GET    /api/v1/defects               # List defects (filterable)
GET    /api/v1/modules/{id}/telemetry # Time-series data
POST   /api/v1/reports/generate      # Generate report
```

### Spatial Queries
```bash
GET /api/v1/spatial/defects/heatmap?site_id=xxx&resolution=100
GET /api/v1/spatial/modules/nearby?site_id=xxx&lat=13.7&lon=100.5
```

**Interactive docs**: http://localhost:8000/docs

## Key Design Decisions (ADRs)

1. **Microservices Architecture** - Independent scaling, fault isolation
2. **Redis Streams** - Simple async messaging with at-least-once delivery
3. **Dual Database Strategy** - PostGIS for spatial, TimescaleDB for time-series
4. **Edge-First Deployment** - Offline operation on Mac M2 with CoreML
5. **FastAPI Standardization** - Consistent patterns, auto-docs, async support

## Common Tasks

### Add new service
1. Create `services/new-service/` directory
2. Add `main.py`, `requirements.txt`, `Dockerfile`
3. Add service to `docker-compose.yml`
4. Update this QWEN.md

### Debug service issue
```bash
# Check service logs
docker compose logs -f <service-name>

# Exec into container
docker compose exec <service-name> /bin/bash

# Check Redis streams
docker compose exec redis redis-cli
> XINFO STREAM thermal:ingest
> XLEN thermal:ingest
```

### Add database migration
1. Edit `infra/postgres/init.sql`
2. For production: create incremental migration script
3. Run: `make db-migrate`

### Monitor system health
```bash
# All services
for port in 8000 8001 8002 8003 8004 7800; do
  curl http://localhost:$port/health
done

# Or use Makefile
make health
```

## External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.109.0 | Web framework |
| Redis | 7-alpine | Message bus |
| PostgreSQL + PostGIS | 15-3.3 | Spatial database |
| TimescaleDB | latest-pg15 | Time-series database |
| MinIO | latest | Object storage |
| Python | 3.11 | Runtime |

## Notes for Qwen

- All services use **async/await** pattern - maintain this in any new code
- **Pydantic models** for request/response validation
- **Environment variables** via `pydantic-settings` BaseSettings class
- **Redis Streams** for async processing - use `xadd`, `xread`, `xack`
- **PostGIS geometry** columns require `ST_GeomFromGeoJSON()` for inserts
- **TimescaleDB hypertables** for time-series data
- **JWT tokens** include: `sub` (user_id), `email`, `role`, `exp`
- Service-to-service communication via internal Docker network (`doctor-doom-network`)

### Frontend Notes

- **React 19** with TypeScript strict mode
- **Tailwind CSS 4** with custom design tokens (primary, severity, thermal colors)
- **Zustand** for global state (auth, UI, selection) - persisted auth store
- **React Query** for server state - 5min stale time, retry: 1
- **Deck.gl** layers for map visualization - memoize layers to prevent re-renders
- **Custom WebGL** thermal viewer - ironbow/grayscale/rainbow palettes
- **Path aliases**: `@/`, `@components/`, `@views/`, `@hooks/`, `@stores/`
- **Vite proxy** to backend at `/api` → `http://localhost:8000`

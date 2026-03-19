# API Gateway Service

**Port:** 8000

Central entry point for all client requests. Routes requests to appropriate backend microservices via Redis Streams.

## Endpoints

### Ingestion
- `POST /api/v1/ingest/thermal` - Submit thermal image for processing

### Defect Detection
- `POST /api/v1/defects/detect` - Trigger ML defect detection
- `GET /api/v1/defects` - List defects with filters

### Sites & Inspections
- `GET /api/v1/sites` - List all sites
- `GET /api/v1/sites/{id}` - Get site details
- `GET /api/v1/inspections` - List inspections

### Reports
- `POST /api/v1/reports/generate` - Generate inspection report

### Auth
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/users/me` - Get current user

### Health
- `GET /health` - Health check

## Redis Streams Integration
- `thermal:ingest` - Raw thermal images for processing
- `defect:detected` - Defect detection jobs
- `report:requested` - Report generation jobs

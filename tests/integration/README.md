# Integration Tests

Run integration tests against a running instance of Doctor Doom.

## Prerequisites

1. All services must be running:
```bash
make dev
```

2. Install test dependencies:
```bash
pip install -r tests/integration/requirements.txt
```

## Running Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific test file
pytest tests/integration/test_api_integration.py

# Run with verbose output
pytest tests/integration/ -v

# Run specific test
pytest tests/integration/test_api_integration.py::test_health_check

# Run with coverage
pytest tests/integration/ --cov=services
```

## Test Categories

### Service Health Tests
- `test_health_check` - API gateway health
- Individual service health checks

### Authentication Tests
- `test_auth_register_login` - User registration and login
- `test_get_current_user` - Authenticated user retrieval

### Data Access Tests
- `test_get_sites` - Site listing
- `test_get_site_details` - Site with modules
- `test_get_defects` - Defect queries with filters
- `test_get_inspections` - Inspection listing

### Workflow Tests
- `test_submit_thermal_image` - Image ingestion
- `test_generate_report` - Report generation
- `test_complete_inspection_workflow` - End-to-end workflow

### Spatial Tests
- `test_spatial_queries` - Geospatial queries

## Test Data

Tests use seeded demo data from `infra/postgres/seed_data.sql`:
- 3 sites
- 43 modules total
- 9 defects of varying severity
- 4 inspections
- 4 reports

## Troubleshooting

### Connection Errors
Ensure all services are running:
```bash
make health
```

### Authentication Errors
Tests create their own test user. If issues persist, check:
```bash
curl http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@doctor-doom.com", "password": "test123"}'
```

### Database Errors
Re-seed the database:
```bash
docker compose exec postgres psql -U postgres -d doctor_doom -f /seed_data.sql
```

# API Documentation

Base URL: `http://localhost:8000`

## Authentication

### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure123",
  "full_name": "Test User",
  "role": "operator"
}
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure123"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

---

## Sites

### List Sites
```http
GET /api/v1/sites
Authorization: Bearer {token}
```

### Get Site Details
```http
GET /api/v1/sites/{site_id}
Authorization: Bearer {token}
```

---

## Inspections

### List Inspections
```http
GET /api/v1/inspections?site_id=site_001
Authorization: Bearer {token}
```

### Get Inspection
```http
GET /api/v1/inspections/{inspection_id}
Authorization: Bearer {token}
```

---

## Defects

### List Defects
```http
GET /api/v1/defects?site_id=site_001&severity=critical
Authorization: Bearer {token}
```

### Get Module Defects
```http
GET /api/v1/modules/{module_id}/defects
Authorization: Bearer {token}
```

---

## Module Telemetry

### Get Time-Series Data
```http
GET /api/v1/modules/{module_id}/telemetry?days=30
Authorization: Bearer {token}

Response:
[
  {
    "timestamp": "2026-03-18T10:00:00Z",
    "temperature": 45.5,
    "power_output_w": 350.2,
    "efficiency": 0.92
  }
]
```

---

## Reports

### Generate Report
```http
POST /api/v1/reports/generate
Authorization: Bearer {token}
Content-Type: application/x-www-form-urlencoded

site_id=site_001&inspection_id=insp_001&format=pdf
```

### Get Report Status
```http
GET /api/v1/reports/{report_id}
Authorization: Bearer {token}
```

### Download Report
```http
GET /api/v1/reports/{report_id}/download
Authorization: Bearer {token}
```

---

## Ingestion

### Submit Thermal Image
```http
POST /api/v1/ingest/thermal
Authorization: Bearer {token}
Content-Type: application/json

{
  "image_id": "img_001",
  "module_id": "mod_001",
  "inspection_id": "insp_001",
  "image_bytes": "base64_encoded_data"
}
```

---

## Spatial Queries

### Defect Heatmap
```http
GET /api/v1/spatial/defects/heatmap?site_id=site_001&resolution=100
Authorization: Bearer {token}
```

### Nearby Modules
```http
GET /api/v1/spatial/modules/nearby?site_id=site_001&lat=13.7&lon=100.5&radius_meters=50
Authorization: Bearer {token}
```

---

## Health Checks

```http
GET /health
GET /api-gateway/health
GET /ml-inference/health
GET /report/health
GET /notify/health
GET /geo/health
GET /auth/health
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated",
  "headers": {"WWW-Authenticate": "Bearer"}
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| /api/v1/auth/login | 10/min |
| /api/v1/ingest/thermal | 100/min |
| All other endpoints | 1000/min |

---

## Interactive Documentation

Access Swagger UI at: http://localhost:8000/docs

Access ReDoc at: http://localhost:8000/redoc

# Geo Service

**Port:** 7800

Handles spatial data with PostGIS and time-series telemetry from TimescaleDB.

## Features

- Site and module management with GeoJSON
- Defect tracking with spatial queries
- Module telemetry time-series
- Spatial queries (heatmap, nearby modules)

## Endpoints

### Sites
- `GET /sites` - List sites
- `GET /sites/{id}` - Get site with modules
- `GET /sites/{id}/defects` - Get site defects

### Modules
- `GET /modules/{id}` - Get module details
- `GET /modules/{id}/telemetry` - Get time-series data
- `GET /modules/{id}/defects` - Get module defects

### Defects
- `GET /defects` - List defects with filters
- `POST /defects` - Record defect

### Inspections
- `GET /inspections` - List inspections
- `GET /inspections/{id}` - Get inspection

### Spatial
- `GET /spatial/defects/heatmap` - Defect heatmap
- `GET /spatial/modules/nearby` - Nearby modules

## Database Schema

Uses PostGIS geometry columns:
- `sites.location` - Polygon
- `modules.position` - Point
- `defects.location` - Point

# Ingest Worker Service

Processes thermal image ingestion pipeline (L2 services).

## Pipeline Stages

1. **RJPEG Parser** - Extract thermal data from DJI RJPEG files
2. **Metadata Extractor** - Parse EXIF and flight data
3. **Calibration** - Apply atmospheric and emissivity corrections
4. **Upload** - Store calibrated images in MinIO
5. **Register** - Record in PostgreSQL database

## Redis Streams

- Reads from: `thermal:ingest`
- Writes to: `thermal:calibrated`
- Dead letter: `thermal:ingest:dlq`

## Endpoints

- `GET /health` - Health check
- `GET /api/v1/ingest/status` - Pipeline status

## Background Workers

- `process_ingestion_queue()` - Main thermal image processor
- `process_orthomosaic_job()` - Orthomosaic stitching

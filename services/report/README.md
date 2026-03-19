# Report Service

**Port:** 8002

Generates inspection reports in PDF, HTML, and JSON formats.

## Features

- PDF reports with thermal images and defect annotations
- HTML interactive reports
- JSON data exports
- Automatic upload to MinIO storage

## Endpoints

- `POST /api/v1/reports` - Generate new report
- `GET /api/v1/reports/{id}` - Get report status
- `GET /api/v1/reports/{id}/download` - Download report
- `GET /api/v1/reports` - List reports

## Redis Streams

- Reads from: `report:requested`

## Storage

- Reports stored in MinIO bucket: `reports`

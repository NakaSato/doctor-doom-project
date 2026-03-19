# Architecture Decision Records (ADRs)

## ADR-001: Microservices Architecture

**Date:** 2026-03-18  
**Status:** Accepted

### Context

The thermal panel inspection system requires:
- Independent scaling of ML inference vs. API handling
- Offline edge deployment capability
- Multiple data persistence strategies (spatial, time-series, blob)
- Real-time processing pipeline

### Decision

Implement seven microservices communicating via Redis Streams:
1. API Gateway - Request routing
2. ML Inference - Defect detection
3. Report - Document generation
4. Notify - Multi-channel alerts
5. Geo - Spatial queries
6. Ingest Worker - Image processing
7. Auth - Authentication

### Consequences

**Positive:**
- Independent deployment and scaling
- Technology diversity per service
- Fault isolation
- Edge/cloud parity

**Negative:**
- Increased operational complexity
- Network latency between services
- Distributed tracing requirements

---

## ADR-002: Redis Streams as Message Bus

**Date:** 2026-03-18  
**Status:** Accepted

### Context

Need asynchronous communication between services with:
- At-least-once delivery guarantees
- Stream processing patterns
- Dead letter queue support
- Backpressure handling

### Decision

Use Redis Streams with four channels:
- `thermal:ingest` - Raw images
- `thermal:calibrated` - Processed images
- `defect:detected` - ML results
- `report:requested` - Report jobs

### Consequences

**Positive:**
- Simple mental model
- Built-in consumer groups
- Persistence with XACK
- Low latency

**Negative:**
- Not durable like Kafka
- Single point of failure (mitigated with Redis Cluster in production)

---

## ADR-003: Dual Database Strategy

**Date:** 2026-03-18  
**Status:** Accepted

### Context

Data requirements:
- Spatial queries on site/module locations
- Time-series telemetry with aggregation
- Blob storage for images/reports
- Relational data for users/inspections

### Decision

- **PostgreSQL + PostGIS** - Spatial data, relational entities
- **TimescaleDB** - Module telemetry (hypertables, compression)
- **MinIO** - S3-compatible object storage

### Consequences

**Positive:**
- Best-in-class for each data type
- PostGIS enables complex spatial queries
- TimescaleDB automatic compression
- MinIO works offline (edge deployment)

**Negative:**
- Multiple databases to manage
- Cross-database transactions not possible

---

## ADR-004: Edge-First Deployment

**Date:** 2026-03-18  
**Status:** Accepted

### Context

Field deployments require:
- Offline operation (no internet)
- Fast inference (<35ms/module)
- Same codebase as cloud
- Limited hardware (Mac M2)

### Decision

- Docker Compose for orchestration
- CoreML models for M2 acceleration
- All services run locally
- Sync to cloud when connected

### Consequences

**Positive:**
- Works in remote locations
- Low latency processing
- Data sovereignty
- Reduced bandwidth costs

**Negative:**
- Hardware limitations
- Manual updates (when offline)
- Limited scaling

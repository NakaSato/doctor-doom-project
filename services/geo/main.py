"""
Geo Service - Port 7800
Handles spatial data: sites, modules, defects with PostGIS.
Provides geospatial queries and module telemetry from TimescaleDB.
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import asyncpg
import json

app = FastAPI(
    title="Geo Service",
    description="Spatial data and telemetry service with PostGIS",
    version="1.0.0"
)


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/doctor_doom"
    TIMESCALE_URL: str = "postgresql://postgres:postgres@timescaledb:5432/telemetry"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379


settings = Settings()


# Pydantic models
class Site(BaseModel):
    id: str
    name: str
    location: Dict[str, float]  # GeoJSON Point
    area_hectares: float
    module_count: int
    created_at: str


class Module(BaseModel):
    id: str
    site_id: str
    position: Dict[str, float]  # GeoJSON Point
    orientation: float
    tilt: float
    rated_power_w: float
    cell_count: int
    installed_at: str


class Defect(BaseModel):
    id: str
    module_id: str
    defect_type: str
    severity: str
    confidence: float
    location: Dict[str, float]  # GeoJSON Point
    temperature_delta: float
    detected_at: str


class Inspection(BaseModel):
    id: str
    site_id: str
    drone_id: str
    started_at: str
    completed_at: Optional[str]
    image_count: int
    status: str


class TelemetryPoint(BaseModel):
    timestamp: str
    module_id: str
    temperature: float
    power_output_w: float
    efficiency: float


# Database connection pool
db_pool: Optional[asyncpg.Pool] = None
timescale_pool: Optional[asyncpg.Pool] = None


@app.on_event("startup")
async def startup():
    global db_pool, timescale_pool
    db_pool = await asyncpg.create_pool(settings.DATABASE_URL)
    timescale_pool = await asyncpg.create_pool(settings.TIMESCALE_URL)


@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()
    if timescale_pool:
        await timescale_pool.close()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Sites endpoints
@app.get("/sites")
async def list_sites(status: Optional[str] = None):
    """List all inspection sites."""
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM sites WHERE status = $1" if status else "SELECT * FROM sites"
        params = [status] if status else []
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]


@app.get("/sites/{site_id}")
async def get_site(site_id: str):
    """Get site details with modules."""
    async with db_pool.acquire() as conn:
        site = await conn.fetchrow("SELECT * FROM sites WHERE id = $1", site_id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        modules = await conn.fetch(
            "SELECT * FROM modules WHERE site_id = $1", site_id
        )
        
        return {
            **site,
            "modules": [dict(m) for m in modules]
        }


@app.get("/sites/{site_id}/defects")
async def get_site_defects(
    site_id: str,
    severity: Optional[str] = None,
    defect_type: Optional[str] = None
):
    """Get all defects for a site."""
    async with db_pool.acquire() as conn:
        query = """
            SELECT d.* FROM defects d
            JOIN modules m ON d.module_id = m.id
            WHERE m.site_id = $1
        """
        params = [site_id]
        
        if severity:
            query += " AND d.severity = $2"
            params.append(severity)
        if defect_type:
            query += " AND d.defect_type = $3"
            params.append(defect_type)
        
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]


# Modules endpoints
@app.get("/modules/{module_id}")
async def get_module(module_id: str):
    """Get module details."""
    async with db_pool.acquire() as conn:
        module = await conn.fetchrow(
            "SELECT * FROM modules WHERE id = $1", module_id
        )
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        return dict(module)


@app.get("/modules/{module_id}/telemetry")
async def get_module_telemetry(
    module_id: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """Get module telemetry time-series from TimescaleDB."""
    async with timescale_pool.acquire() as conn:
        start_date = datetime.utcnow() - timedelta(days=days)
        rows = await conn.fetch(
            """
            SELECT timestamp, temperature, power_output_w, efficiency
            FROM module_telemetry
            WHERE module_id = $1 AND timestamp >= $2
            ORDER BY timestamp DESC
            """,
            module_id, start_date
        )
        return [dict(r) for r in rows]


@app.get("/modules/{module_id}/defects")
async def get_module_defects(module_id: str):
    """Get all defects for a module."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM defects WHERE module_id = $1", module_id
        )
        return [dict(r) for r in rows]


# Defects endpoints
@app.get("/defects")
async def list_defects(
    site_id: Optional[str] = None,
    module_id: Optional[str] = None,
    severity: Optional[str] = None
):
    """List defects with filters."""
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM defects WHERE 1=1"
        params = []
        
        if site_id:
            query += """
                AND module_id IN (SELECT id FROM modules WHERE site_id = $1)
            """
            params.append(site_id)
        if module_id:
            query += " AND module_id = $" + str(len(params) + 1)
            params.append(module_id)
        if severity:
            query += " AND severity = $" + str(len(params) + 1)
            params.append(severity)
        
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]


@app.post("/defects")
async def create_defect(defect: Defect):
    """Record a new defect detection."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO defects (id, module_id, defect_type, severity, 
                                confidence, location, temperature_delta, detected_at)
            VALUES ($1, $2, $3, $4, $5, ST_GeomFromGeoJSON($6), $7, $8)
            """,
            defect.id,
            defect.module_id,
            defect.defect_type,
            defect.severity,
            defect.confidence,
            json.dumps(defect.location),
            defect.temperature_delta,
            defect.detected_at
        )
        return {"status": "created", "defect_id": defect.id}


# Inspections endpoints
@app.get("/inspections")
async def list_inspections(site_id: Optional[str] = None):
    """List inspections."""
    async with db_pool.acquire() as conn:
        if site_id:
            rows = await conn.fetch(
                "SELECT * FROM inspections WHERE site_id = $1", site_id
            )
        else:
            rows = await conn.fetch("SELECT * FROM inspections")
        return [dict(r) for r in rows]


@app.get("/inspections/{inspection_id}")
async def get_inspection(inspection_id: str):
    """Get inspection details."""
    async with db_pool.acquire() as conn:
        inspection = await conn.fetchrow(
            "SELECT * FROM inspections WHERE id = $1", inspection_id
        )
        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")
        return dict(inspection)


# Spatial query endpoints
@app.get("/spatial/defects/heatmap")
async def get_defect_heatmap(site_id: str, resolution: int = 100):
    """Generate defect heatmap grid for a site."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT ST_AsGeoJSON(ST_SnapToGrid(location, 0.0001)) as grid_cell,
                   COUNT(*) as defect_count,
                   AVG(temperature_delta) as avg_temp_delta
            FROM defects d
            JOIN modules m ON d.module_id = m.id
            WHERE m.site_id = $1
            GROUP BY grid_cell
            """,
            site_id
        )
        return [dict(r) for r in rows]


@app.get("/spatial/modules/nearby")
async def get_nearby_modules(
    site_id: str,
    lat: float,
    lon: float,
    radius_meters: int = 50
):
    """Find modules within radius of a point."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *, ST_Distance(
                position,
                ST_GeogFromText('POINT(' || $2 || ' ' || $3 || ')')
            ) as distance_m
            FROM modules
            WHERE site_id = $1
            AND ST_DWithin(
                position,
                ST_GeogFromText('POINT(' || $2 || ' ' || $3 || ')'),
                $4
            )
            ORDER BY distance_m
            """,
            site_id, lon, lat, radius_meters
        )
        return [dict(r) for r in rows]


# Reports endpoint (for report service)
@app.get("/reports")
async def list_reports(site_id: Optional[str] = None):
    """List generated reports."""
    async with db_pool.acquire() as conn:
        if site_id:
            rows = await conn.fetch(
                "SELECT * FROM reports WHERE site_id = $1", site_id
            )
        else:
            rows = await conn.fetch("SELECT * FROM reports")
        return [dict(r) for r in rows]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7800)

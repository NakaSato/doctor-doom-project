"""
API Gateway Service - Port 8000
Central entry point for all client requests.
Routes requests to appropriate backend microservices via Redis Streams.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
import redis.asyncio as redis
import httpx
from typing import Optional
import json
from datetime import datetime

app = FastAPI(
    title="Doctor Doom API Gateway",
    description="Thermal Panel Inspection System API Gateway",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Settings(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    ML_INFERENCE_URL: str = "http://ml-inference:8001"
    REPORT_URL: str = "http://report:8002"
    NOTIFY_URL: str = "http://notify:8003"
    GEO_URL: str = "http://geo:7800"
    AUTH_URL: str = "http://auth:8004"


settings = Settings()
redis_client: Optional[redis.Redis] = None


@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )


@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/v1/ingest/thermal")
async def ingest_thermal_image(image_data: dict):
    """Submit thermal image for processing through ingestion pipeline."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    await redis_client.xadd(
        "thermal:ingest",
        {"data": json.dumps(image_data)},
        maxlen=1000
    )
    return {"status": "queued", "stream": "thermal:ingest"}


@app.post("/api/v1/defects/detect")
async def detect_defects(module_id: str):
    """Trigger ML defect detection for a specific module."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    await redis_client.xadd(
        "defect:detected",
        {"module_id": module_id},
        maxlen=1000
    )
    return {"status": "processing", "module_id": module_id}


@app.post("/api/v1/reports/generate")
async def generate_report(site_id: str, inspection_id: str):
    """Generate inspection report for a site."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    await redis_client.xadd(
        "report:requested",
        {"site_id": site_id, "inspection_id": inspection_id},
        maxlen=1000
    )
    return {"status": "queued", "site_id": site_id, "inspection_id": inspection_id}


@app.get("/api/v1/sites")
async def list_sites():
    """List all inspection sites."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.GEO_URL}/sites")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Geo service error")
        return response.json()


@app.get("/api/v1/sites/{site_id}")
async def get_site(site_id: str):
    """Get site details with modules."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.GEO_URL}/sites/{site_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Site not found")
        return response.json()


@app.get("/api/v1/inspections")
async def list_inspections(site_id: Optional[str] = None):
    """List inspections, optionally filtered by site."""
    async with httpx.AsyncClient() as client:
        params = {"site_id": site_id} if site_id else {}
        response = await client.get(f"{settings.GEO_URL}/inspections", params=params)
        return response.json()


@app.get("/api/v1/defects")
async def list_defects(
    site_id: Optional[str] = None,
    module_id: Optional[str] = None,
    severity: Optional[str] = None
):
    """List defects with optional filters."""
    async with httpx.AsyncClient() as client:
        params = {}
        if site_id:
            params["site_id"] = site_id
        if module_id:
            params["module_id"] = module_id
        if severity:
            params["severity"] = severity
        response = await client.get(f"{settings.GEO_URL}/defects", params=params)
        return response.json()


@app.get("/api/v1/modules/{module_id}/telemetry")
async def get_module_telemetry(module_id: str, days: int = 30):
    """Get module telemetry time-series data."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.GEO_URL}/modules/{module_id}/telemetry",
            params={"days": days}
        )
        return response.json()


@app.post("/api/v1/auth/login")
async def login(credentials: dict):
    """Authenticate user and return JWT token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{settings.AUTH_URL}/login", json=credentials)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return response.json()


@app.get("/api/v1/users/me")
async def get_current_user():
    """Get current authenticated user."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.AUTH_URL}/me")
        return response.json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

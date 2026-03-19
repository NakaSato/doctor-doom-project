"""
Report Service - Port 8002
Generates inspection reports in PDF, HTML, and JSON formats.
Processes report:requested stream from Redis.
"""
from fastapi import FastAPI, HTTPException
from pydantic_settings import BaseSettings
from pydantic import BaseModel
import redis.asyncio as redis
import asyncio
import json
from datetime import datetime
from typing import Optional, List
import httpx

app = FastAPI(
    title="Report Service",
    description="Inspection report generation service",
    version="1.0.0"
)


class Settings(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_BUCKET: str = "reports"
    GEO_URL: str = "http://geo:7800"
    ML_INFERENCE_URL: str = "http://ml-inference:8001"


settings = Settings()


class ReportRequest(BaseModel):
    site_id: str
    inspection_id: str
    format: str = "pdf"  # pdf, html, json
    include_thermal_images: bool = True
    include_recommendations: bool = True


class ReportResponse(BaseModel):
    report_id: str
    site_id: str
    inspection_id: str
    status: str
    url: Optional[str] = None
    generated_at: str


class ReportGenerator:
    """Generate inspection reports in multiple formats."""
    
    def __init__(self):
        self.templates = {}
    
    async def generate_pdf(self, data: dict) -> bytes:
        """Generate PDF report."""
        # Placeholder - implement with reportlab
        return b""
    
    async def generate_html(self, data: dict) -> str:
        """Generate HTML report."""
        # Placeholder - implement with jinja2
        return ""
    
    async def generate_json(self, data: dict) -> dict:
        """Generate JSON report."""
        return data


report_generator = ReportGenerator()
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


@app.post("/api/v1/reports", response_model=ReportResponse)
async def create_report(request: ReportRequest):
    """Generate a new inspection report."""
    report_id = f"rpt_{request.site_id}_{request.inspection_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Queue report generation
    if redis_client:
        await redis_client.xadd(
            "report:requested",
            {
                "report_id": report_id,
                "site_id": request.site_id,
                "inspection_id": request.inspection_id,
                "format": request.format
            },
            maxlen=1000
        )
    
    return ReportResponse(
        report_id=report_id,
        site_id=request.site_id,
        inspection_id=request.inspection_id,
        status="queued",
        generated_at=datetime.utcnow().isoformat()
    )


@app.get("/api/v1/reports/{report_id}")
async def get_report(report_id: str):
    """Get report status or download URL."""
    # Check report status from storage
    return {
        "report_id": report_id,
        "status": "completed",
        "url": f"/api/v1/reports/{report_id}/download"
    }


@app.get("/api/v1/reports/{report_id}/download")
async def download_report(report_id: str, format: str = "pdf"):
    """Download generated report."""
    # Fetch from MinIO storage
    raise HTTPException(status_code=404, detail="Report not found")


@app.get("/api/v1/reports")
async def list_reports(site_id: Optional[str] = None):
    """List all reports, optionally filtered by site."""
    async with httpx.AsyncClient() as client:
        # Fetch from database via geo service
        params = {"site_id": site_id} if site_id else {}
        response = await client.get(f"{settings.GEO_URL}/reports", params=params)
        return response.json()


async def process_report_queue():
    """Background task to process report:requested stream."""
    if not redis_client:
        return
    
    while True:
        try:
            streams = await redis_client.xread(
                {"report:requested": "0-0"},
                count=1,
                block=5000
            )
            
            if streams:
                for stream_name, messages in streams:
                    for message_id, message_data in messages:
                        report_data = {
                            "report_id": message_data.get("report_id"),
                            "site_id": message_data.get("site_id"),
                            "inspection_id": message_data.get("inspection_id"),
                            "format": message_data.get("format", "pdf")
                        }
                        
                        # Fetch inspection data
                        async with httpx.AsyncClient() as client:
                            inspection_resp = await client.get(
                                f"{settings.GEO_URL}/inspections/{report_data['inspection_id']}"
                            )
                            if inspection_resp.status_code == 200:
                                inspection_data = inspection_resp.json()
                                report_data["inspection"] = inspection_data
                        
                        # Generate report
                        if report_data.get("format") == "pdf":
                            await report_generator.generate_pdf(report_data)
                        elif report_data.get("format") == "html":
                            await report_generator.generate_html(report_data)
                        else:
                            await report_generator.generate_json(report_data)
                        
                        # Acknowledge message
                        await redis_client.xack("report:requested", message_id)
        except Exception as e:
            print(f"Error processing report queue: {e}")
            await asyncio.sleep(1)


@app.on_event("startup")
async def start_queue_processor():
    asyncio.create_task(process_report_queue())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

"""
Notify Service - Port 8003
Handles notifications via email, SMS, and webhooks.
Triggers on critical defect detections and report completions.
"""
from fastapi import FastAPI
from pydantic_settings import BaseSettings
from pydantic import BaseModel, EmailStr
from enum import Enum
import redis.asyncio as redis
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict
import httpx

app = FastAPI(
    title="Notify Service",
    description="Notification service for alerts and updates",
    version="1.0.0"
)


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Settings(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SLACK_WEBHOOK_URL: str = ""
    API_GATEWAY_URL: str = "http://api-gateway:8000"


settings = Settings()


class NotificationRequest(BaseModel):
    type: NotificationType
    recipients: List[str]
    subject: str
    body: str
    severity: Severity = Severity.MEDIUM
    metadata: Optional[Dict] = None


class NotificationResponse(BaseModel):
    notification_id: str
    status: str
    sent_at: str


class NotificationService:
    """Handle multi-channel notifications."""
    
    async def send_email(self, recipients: List[str], subject: str, body: str) -> bool:
        """Send email notification."""
        # Placeholder - implement with smtplib or SendGrid
        print(f"Sending email to {recipients}: {subject}")
        return True
    
    async def send_sms(self, recipients: List[str], message: str) -> bool:
        """Send SMS notification."""
        # Placeholder - implement with Twilio
        print(f"Sending SMS to {recipients}: {message}")
        return True
    
    async def send_webhook(self, url: str, payload: dict) -> bool:
        """Send webhook notification."""
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            return response.status_code < 400
    
    async def send_push(self, tokens: List[str], title: str, body: str) -> bool:
        """Send push notification."""
        # Placeholder - implement with FCM
        print(f"Sending push to {len(tokens)} devices: {title}")
        return True


notification_service = NotificationService()
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


@app.post("/api/v1/notifications", response_model=NotificationResponse)
async def send_notification(request: NotificationRequest):
    """Send notification via specified channel."""
    notification_id = f"ntf_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    
    success = False
    if request.type == NotificationType.EMAIL:
        success = await notification_service.send_email(
            request.recipients, request.subject, request.body
        )
    elif request.type == NotificationType.SMS:
        success = await notification_service.send_sms(request.recipients, request.body)
    elif request.type == NotificationType.WEBHOOK:
        for recipient in request.recipients:
            success = await notification_service.send_webhook(recipient, {
                "subject": request.subject,
                "body": request.body,
                "severity": request.severity.value,
                "metadata": request.metadata
            })
    elif request.type == NotificationType.PUSH:
        success = await notification_service.send_push(
            request.recipients, request.subject, request.body
        )
    
    return NotificationResponse(
        notification_id=notification_id,
        status="sent" if success else "failed",
        sent_at=datetime.utcnow().isoformat()
    )


@app.post("/api/v1/alerts/defect")
async def alert_defect_detected(
    module_id: str,
    site_id: str,
    severity: Severity,
    defect_type: str
):
    """Send alert for critical defect detection."""
    if severity == Severity.CRITICAL:
        # Send immediate alerts for critical defects
        alert_request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipients=["ops@solar-farm.com"],
            subject=f"CRITICAL: Defect detected at {site_id}",
            body=f"Critical {defect_type} detected on module {module_id}. Immediate inspection required.",
            severity=Severity.CRITICAL,
            metadata={"module_id": module_id, "site_id": site_id, "defect_type": defect_type}
        )
        await send_notification(alert_request)
        
        # Also send to Slack
        slack_request = NotificationRequest(
            type=NotificationType.WEBHOOK,
            recipients=[settings.SLACK_WEBHOOK_URL],
            subject="Critical Defect Alert",
            body=f"🚨 Critical defect on {module_id} at {site_id}",
            severity=Severity.CRITICAL
        )
        await send_notification(slack_request)
    
    return {"status": "alert_sent", "severity": severity.value}


@app.post("/api/v1/alerts/report")
async def alert_report_ready(
    report_id: str,
    site_id: str,
    recipients: List[str]
):
    """Notify when report is ready."""
    alert_request = NotificationRequest(
        type=NotificationType.EMAIL,
        recipients=recipients,
        subject=f"Report Ready: {site_id}",
        body=f"Your inspection report ({report_id}) is ready for download.",
        severity=Severity.LOW,
        metadata={"report_id": report_id, "site_id": site_id}
    )
    await send_notification(alert_request)
    return {"status": "notification_sent"}


async def process_notification_queue():
    """Background task to process notification queue."""
    if not redis_client:
        return
    
    while True:
        try:
            # Check for defect alerts
            streams = await redis_client.xread(
                {"defect:detected": "0-0"},
                count=1,
                block=5000
            )
            
            if streams:
                for stream_name, messages in streams:
                    for message_id, message_data in messages:
                        data = json.loads(message_data.get("data", "{}"))
                        severity = data.get("severity", "low")
                        
                        if severity in ["high", "critical"]:
                            await alert_defect_detected(
                                module_id=data.get("module_id", "unknown"),
                                site_id=data.get("site_id", "unknown"),
                                severity=Severity(severity),
                                defect_type=data.get("defect_type", "unknown")
                            )
                        
                        await redis_client.xack("defect:detected", message_id)
        except Exception as e:
            print(f"Error processing notification queue: {e}")
            await asyncio.sleep(1)


@app.on_event("startup")
async def start_queue_processor():
    asyncio.create_task(process_notification_queue())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

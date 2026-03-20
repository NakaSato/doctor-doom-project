"""Service configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Literal
from pathlib import Path


class MLServiceSettings(BaseSettings):
    """ML Service configuration."""
    
    # Service
    service_name: str = "ml-inference"
    host: str = "0.0.0.0"
    port: int = 8001
    workers: int = 1
    
    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_stream_in: str = "thermal:calibrated"
    redis_stream_out: str = "defect:detected"
    
    # Models
    model_path: Path = Path("/app/models")
    device: Literal["edge", "cloud"] = "edge"
    
    # Inference
    batch_size: int = Field(default=8, ge=1, le=32)
    inference_timeout_ms: int = 35
    confidence_threshold: float = 0.65
    
    # Monitoring
    enable_metrics: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    class Config:
        env_prefix = "ML_"
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @validator("model_path")
    @classmethod
    def validate_model_path(cls, v: Path) -> Path:
        """Validate model path exists (for production)."""
        # Don't enforce existence in development
        return v


def get_settings() -> MLServiceSettings:
    """Get service settings."""
    return MLServiceSettings()

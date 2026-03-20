"""Structured JSON logging for ML service."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra context if present
        if hasattr(record, "module_id"):
            log_entry["module_id"] = record.module_id
        if hasattr(record, "inspection_id"):
            log_entry["inspection_id"] = record.inspection_id
        if hasattr(record, "processing_time_ms"):
            log_entry["processing_time_ms"] = record.processing_time_ms
        if hasattr(record, "stage"):
            log_entry["stage"] = record.stage
            
        return json.dumps(log_entry, default=str)


def setup_logging(
    level: str = "INFO",
    log_format: str = "json"
) -> logging.Logger:
    """
    Configure structured logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Format type ('json' or 'text')
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("ml_inference")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(f"ml_inference.{name}")

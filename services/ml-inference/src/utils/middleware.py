"""
Request Validation Middleware for FastAPI
==========================================

Provides request validation, size limits, and content-type checking.
"""
import base64
import logging
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import InvalidInputError, ThermalDataError

logger = logging.getLogger(__name__)


# Configuration constants
MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_THERMAL_DATA_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_CONTENT_TYPES = ["application/json"]


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request validation."""
        
        # Skip validation for non-API routes
        if not request.url.path.startswith("/api"):
            return await call_next(request)
        
        # Validate content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            # Allow JSON and multipart form data
            if not any(
                ct in content_type.lower()
                for ct in ["application/json", "multipart/form-data"]
            ):
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": {
                            "code": "UNSUPPORTED_MEDIA_TYPE",
                            "message": f"Unsupported content type: {content_type}",
                            "allowed": ALLOWED_CONTENT_TYPES,
                        }
                    }
                )
            
            # Check content length
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > MAX_REQUEST_SIZE:
                        return JSONResponse(
                            status_code=413,
                            content={
                                "error": {
                                    "code": "REQUEST_TOO_LARGE",
                                    "message": f"Request size {size} bytes exceeds limit of {MAX_REQUEST_SIZE} bytes",
                                    "max_size": MAX_REQUEST_SIZE,
                                }
                            }
                        )
                except ValueError:
                    pass
        
        return await call_next(request)


class ThermalDataValidator:
    """Validate thermal image data."""
    
    @staticmethod
    def validate_base64(data: str, field_name: str = "thermal_data") -> bytes:
        """
        Validate and decode base64 thermal data.
        
        Args:
            data: Base64 encoded string
            field_name: Name of the field for error messages
            
        Returns:
            Decoded bytes
            
        Raises:
            InvalidInputError: If data is invalid
        """
        if not data:
            raise InvalidInputError(
                message=f"{field_name} is required",
                field=field_name,
            )
        
        if not isinstance(data, str):
            raise InvalidInputError(
                message=f"{field_name} must be a string",
                field=field_name,
            )
        
        # Check for data URL prefix and remove if present
        if data.startswith("data:"):
            data = data.split(",")[-1]
        
        # Validate base64 format
        try:
            # Check size before decoding
            if len(data) > MAX_THERMAL_DATA_SIZE * 4 / 3:  # Base64 expands by ~33%
                raise InvalidInputError(
                    message=f"{field_name} exceeds maximum size of {MAX_THERMAL_DATA_SIZE} bytes",
                    field=field_name,
                )
            
            decoded = base64.b64decode(data, validate=True)
            
            # Check decoded size
            if len(decoded) > MAX_THERMAL_DATA_SIZE:
                raise InvalidInputError(
                    message=f"Decoded {field_name} exceeds maximum size",
                    field=field_name,
                )
            
            # Check for minimum size (should be at least a valid image header)
            if len(decoded) < 100:
                raise ThermalDataError(
                    message="Data too small to be a valid image",
                )
            
            return decoded
            
        except Exception as e:
            if isinstance(e, InvalidInputError):
                raise
            raise ThermalDataError(
                message=f"Invalid base64 encoding: {str(e)}",
            )
    
    @staticmethod
    def validate_image_format(data: bytes) -> str:
        """
        Validate image format from bytes.
        
        Args:
            data: Image bytes
            
        Returns:
            Detected format (jpeg, png, etc.)
            
        Raises:
            ThermalDataError: If format is invalid
        """
        # Check JPEG magic number
        if data[:2] == b'\xff\xd8':
            return 'jpeg'
        
        # Check PNG magic number
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'png'
        
        # Check for R-JPEG (DJI)
        if b'DJI' in data[:1000] or b'FLIR' in data[:1000]:
            return 'rjpeg'
        
        raise ThermalDataError(
            message="Unrecognized image format. Supported: JPEG, PNG, R-JPEG",
        )
    
    @staticmethod
    def validate_inference_request(request_data: dict) -> None:
        """
        Validate complete inference request.
        
        Args:
            request_data: Parsed request dictionary
            
        Raises:
            InvalidInputError: If validation fails
        """
        required_fields = ["module_id", "inspection_id", "image_id", "thermal_data"]
        
        for field in required_fields:
            if field not in request_data:
                raise InvalidInputError(
                    message=f"Missing required field: {field}",
                    field=field,
                )
            
            if not request_data[field]:
                raise InvalidInputError(
                    message=f"Field '{field}' cannot be empty",
                    field=field,
                )
        
        # Validate thermal data
        ThermalDataValidator.validate_base64(
            request_data["thermal_data"],
            field_name="thermal_data"
        )
        
        # Validate metadata if present
        if "metadata" in request_data:
            if not isinstance(request_data["metadata"], dict):
                raise InvalidInputError(
                    message="metadata must be an object",
                    field="metadata",
                )

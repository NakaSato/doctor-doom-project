# ML Inference Service Dockerfile
# Multi-stage build for optimized image size

# ==================== Build Stage ====================
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv and git
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY uv.lock .

# Create virtual environment and install dependencies
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-dev

# ==================== Runtime Stage ====================
FROM python:3.11-slim as runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY *.py ./
COPY models/ ./models/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Environment variables for configuration
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV MODEL_PATH=/app/models
ENV DEVICE=edge
ENV INFERENCE_TIMEOUT_MS=35

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Expose port
EXPOSE 8001

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]

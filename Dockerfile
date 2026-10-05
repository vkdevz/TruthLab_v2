# ==============================================================================
# Multimodal Evidence-Aware Misinformation Verification System
# Production Dockerfile — Hardened, Non-root, Health-Checked
# ==============================================================================

FROM python:3.12-slim AS runtime

# System environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install security updates, curl for healthchecks, and ffmpeg for audio/video decoding
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy dependency specifications
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn==0.31.0 \
    pydantic==2.9.2 \
    pydantic-settings==2.5.2 \
    python-multipart==0.0.12 \
    httpx==0.27.2 \
    trafilatura==2.3.0 \
    sqlalchemy==2.0.35 \
    aiosqlite==0.20.0 \
    greenlet==3.1.1 \
    scikit-learn==1.5.2 \
    scipy==1.14.1 \
    numpy==2.1.2 \
    pillow==10.4.0 \
    dateparser==1.2.0 \
    python-dateutil==2.9.0.post0

# Copy application and research assets
COPY backend /app/backend
COPY data /app/data
COPY research /app/research
COPY docs /app/docs

# Prepare runtime writable directories and configure permissions
RUN mkdir -p /app/uploads /app/data && \
    chown -R appuser:appgroup /app

# Switch to unprivileged execution user
USER appuser

# Expose FastAPI listening port
EXPOSE 8000

# Automated health check against live health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start production ASGI web server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

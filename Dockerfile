FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (curl, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml /app/

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    pydantic-settings \
    python-multipart \
    httpx \
    trafilatura \
    sqlalchemy \
    aiosqlite \
    greenlet \
    scikit-learn \
    scipy \
    numpy \
    pillow \
    dateparser \
    python-dateutil

# Copy application code
COPY backend /app/backend
COPY docs /app/docs

# Expose FastAPI port
EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

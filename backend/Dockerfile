FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into backend/ subdirectory to match import structure
COPY . ./backend/

# Set Python path so 'backend' module is importable
ENV PYTHONPATH=/app

# Build arg to switch between API and Worker mode
ARG WORKER_MODE=false
ENV WORKER_MODE=${WORKER_MODE}

# Create entrypoint script (before switching user)
RUN printf '#!/bin/bash\n\
    set -e\n\
    if [ "$WORKER_MODE" = "true" ]; then\n\
    echo "Starting Temporal Worker..."\n\
    exec python -m backend.workflows.worker\n\
    else\n\
    echo "Starting API Server..."\n\
    exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8080\n\
    fi\n' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 engram && chown -R engram:engram /app
USER engram

# Expose port (only used in API mode)
EXPOSE 8080

# Health check - varies by mode
# Note: Worker mode uses process check, API mode uses HTTP check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD if [ "$WORKER_MODE" = "true" ]; then pgrep -f "workflows.worker" || exit 1; else python -c "import httpx; httpx.get('http://localhost:8080/health')"; fi

# Use entrypoint script
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]

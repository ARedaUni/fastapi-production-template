# Multi-stage build for security and optimization
FROM python:3.12-slim AS builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies into virtual environment
RUN uv sync --frozen --no-dev

# Production stage - minimal runtime image
FROM python:3.12-slim AS production

# Add metadata labels following OCI spec
LABEL org.opencontainers.image.title="PracticePython FastAPI"
LABEL org.opencontainers.image.description="A lightweight FastAPI application with authentication"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="PracticePython Team"
LABEL org.opencontainers.image.source="https://github.com/your-org/practicepython"
LABEL org.opencontainers.image.licenses="MIT"

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user (following security best practices)
# Using a high UID to avoid conflicts with host systems
RUN groupadd -r appuser -g 1001 && \
    useradd -r -g appuser -u 1001 -d /app -s /bin/bash appuser

# Set working directory and ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code with proper ownership
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser scripts/ ./scripts/

# Switch to non-root user (security best practice)
USER appuser

# Expose port (documentation only, doesn't actually expose)
EXPOSE 8000

# Add health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=10)"

# Use exec form for better signal handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 
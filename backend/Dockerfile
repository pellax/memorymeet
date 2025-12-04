# ================================================================================================
# 🐳 DOCKERFILE - Gatekeeper Backend (Consumption Service)
# ================================================================================================
# Multi-stage build para optimizar tamaño y seguridad

FROM python:3.11-slim as base

# Metadata
LABEL maintainer="M2PRD Team"
LABEL description="Gatekeeper Backend - Consumption Control Service"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ================================================================================================
# 🔧 DEVELOPMENT STAGE
# ================================================================================================
FROM base as development

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run application with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

# ================================================================================================
# 🚀 PRODUCTION STAGE
# ================================================================================================
FROM base as production

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy requirements
COPY requirements.txt .

# Install production dependencies only
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "app.main:app", \
    "--bind", "0.0.0.0:8002", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info"]

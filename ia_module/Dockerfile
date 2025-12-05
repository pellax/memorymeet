# ================================================================================================
# 🐳 DOCKERFILE - IA/NLP Microservice
# ================================================================================================
# Multi-stage build para el microservicio de procesamiento NLP

FROM python:3.11-slim as base

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ================================================================================================
# 📦 STAGE: Dependencies
# ================================================================================================
FROM base as dependencies

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY ia_module/requirements.txt /app/requirements.txt

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ================================================================================================
# 📦 STAGE: Development
# ================================================================================================
FROM dependencies as development

# Copiar código de la aplicación
COPY ia_module/app /app/app
COPY ia_module/tests /app/tests

# Exponer puerto
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Comando de desarrollo con hot-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]

# ================================================================================================
# 📦 STAGE: Production
# ================================================================================================
FROM dependencies as production

# Copiar solo código necesario
COPY ia_module/app /app/app

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Exponer puerto
EXPOSE 8003

# Comando de producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "2"]

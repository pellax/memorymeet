# ================================================================================================
# 🔒 DOCKERFILE - SERVICIO DE SUSCRIPCIONES/CONSUMO (BACKEND)
# ================================================================================================
# Servicio crítico que implementa RF8.0 (Control de Consumo) - El GATEKEEPER del sistema SaaS
# Stack: Python 3.11 + FastAPI + SQLAlchemy + Redis
# Principios: SOLID, Clean Architecture, ACID compliance

# ===== BASE IMAGE =====
FROM python:3.11-slim as base

# Metadatos del container
LABEL maintainer="M2PRD-001 Team"
LABEL description="Backend Service - Subscription/Consumption Management (RF8.0)"
LABEL version="1.0.0"

# Variables de entorno para optimización
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para seguridad (RNF2.0)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# ===== DEPENDENCIES STAGE =====
FROM base as dependencies

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY backend/requirements.txt /app/requirements.txt
COPY backend/requirements-dev.txt /app/requirements-dev.txt

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ===== DEVELOPMENT STAGE =====
FROM dependencies as development

# Instalar dependencias de desarrollo para TDD
RUN pip install -r requirements-dev.txt

# Copiar código fuente (se monta como volume en desarrollo)
COPY backend/app /app/app
COPY backend/tests /app/tests

# Cambiar ownership al usuario no-root
RUN chown -R appuser:appgroup /app
USER appuser

# Exponer puerto del servicio
EXPOSE 8000

# Health check endpoint (RNF4.0 - Observabilidad)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando de desarrollo con hot-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ===== PRODUCTION STAGE =====
FROM base as production

# Instalar solo dependencias de producción
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf /root/.cache

# Copiar solo el código necesario (no tests)
COPY backend/app /app/app

# Cambiar ownership al usuario no-root
RUN chown -R appuser:appgroup /app
USER appuser

# Exponer puerto del servicio
EXPOSE 8000

# Health check para producción
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando de producción optimizado
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ===== DEFAULT TARGET =====
FROM development as final
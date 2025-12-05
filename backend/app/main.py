# ================================================================================================
# 🚀 MAIN FASTAPI APPLICATION - Servicio de Suscripciones/Consumo (Gatekeeper)
# ================================================================================================
# Aplicación principal que expone los endpoints críticos del sistema SaaS

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, Info

from .api.v1.consumption_router import router as consumption_router
from .domain.exceptions.consumption_exceptions import DomainException

# ================================================================================================
# 🔧 APPLICATION CONFIGURATION
# ================================================================================================

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================================================================================
# 📊 PROMETHEUS CUSTOM METRICS - RF8.0 (Consumo SaaS)
# ================================================================================================

# Métricas de negocio críticas para RF8.0
consumption_verifications_total = Counter(
    'consumption_verifications_total',
    'Total de verificaciones de consumo realizadas',
    ['result']  # authorized, rejected
)

consumption_hours_processed = Counter(
    'consumption_hours_processed_total',
    'Total de horas procesadas del sistema',
    ['user_id']
)

consumption_updates_total = Counter(
    'consumption_updates_total',
    'Total de actualizaciones de consumo',
    ['status']  # success, failed
)

active_processing_requests = Gauge(
    'active_processing_requests',
    'Número de requests de procesamiento activos'
)

user_subscription_status = Gauge(
    'user_subscription_status',
    'Estado de suscripción de usuarios',
    ['user_id', 'plan_type']  # free, pro, enterprise
)

processing_authorization_duration = Histogram(
    'processing_authorization_duration_seconds',
    'Tiempo de autorización de procesamiento (crítico para UX)',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Info metrics para metadata del servicio
service_info = Info(
    'gatekeeper_service',
    'Información del servicio Gatekeeper'
)
service_info.info({
    'version': '1.0.0',
    'service': 'consumption-gatekeeper',
    'rf': 'RF8.0'
})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ✅ Gestión del ciclo de vida de la aplicación.
    
    Aquí se inicializan y limpian recursos como conexiones de BD,
    pools de conexiones, etc.
    """
    # Startup
    logger.info("🚀 Starting Consumption Service (Gatekeeper)")
    logger.info("💰 RF8.0 Critical Service - SaaS Monetization Layer")
    
    # TODO: Inicializar conexiones de BD, Redis, etc.
    # await database.connect()
    # await redis.connect()
    
    yield
    
    # Shutdown
    logger.info("🔻 Shutting down Consumption Service")
    # TODO: Cerrar conexiones
    # await database.disconnect()
    # await redis.disconnect()


# ================================================================================================
# 🏗️ FASTAPI APPLICATION SETUP
# ================================================================================================

app = FastAPI(
    title="💰 Consumption Service - SaaS Gatekeeper",
    description="""
    ## 🔒 Servicio Crítico de Control de Consumo (RF8.0)
    
    **EL GATEKEEPER DEL SISTEMA SAAS**
    
    Este servicio implementa la lógica de monetización más crítica del sistema M2PRD-001.
    Controla el acceso al procesamiento de reuniones basado en el consumo de horas 
    de los usuarios.
    
    ### 🎯 Funcionalidades Principales:
    
    - **🚦 Verificación de Consumo**: Autoriza o rechaza el procesamiento
    - **📊 Actualización Post-Proceso**: Actualiza el consumo real
    - **📈 Consulta de Estado**: Información del consumo del usuario
    
    ### 🏗️ Arquitectura:
    
    - **Clean Architecture**: Separación clara de capas
    - **TDD**: Desarrollo guiado por tests
    - **SOLID Principles**: Principios de diseño aplicados
    - **ACID Transactions**: Consistencia de datos financieros
    
    ### 🔗 Integración:
    
    - **Workflow (n8n/Make)**: Recibe autorizaciones de este servicio
    - **Frontend SaaS**: Consulta estado de consumo
    - **PostgreSQL**: Persistencia ACID de datos críticos
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ================================================================================================
# 🌐 MIDDLEWARE CONFIGURATION
# ================================================================================================

# CORS - Configuración para frontend SaaS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend local
        "https://app.memorymeet.com",  # Producción frontend
        "https://n8n.company.com",  # n8n workflows
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    ✅ Middleware para logging estructurado de requests.
    
    Crítico para observabilidad del Gatekeeper.
    """
    start_time = time.time()
    
    # Log de request entrante
    logger.info(
        f"🔄 Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host
        }
    )
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo de procesamiento
    process_time = time.time() - start_time
    
    # Log de response
    logger.info(
        f"✅ Response: {response.status_code} ({process_time:.3f}s)",
        extra={
            "status_code": response.status_code,
            "process_time_seconds": process_time,
            "path": request.url.path
        }
    )
    
    # Agregar header de tiempo de procesamiento
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# ================================================================================================
# 🚨 EXCEPTION HANDLERS
# ================================================================================================

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    """
    ✅ Handler para excepciones de dominio.
    
    Maneja todas las excepciones de reglas de negocio de forma consistente.
    """
    logger.warning(
        f"🚨 Domain Exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "path": request.url.path
        }
    )
    
    # Mapeo de códigos de error a status HTTP
    status_mapping = {
        "INSUFFICIENT_HOURS": status.HTTP_403_FORBIDDEN,
        "USER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "SUBSCRIPTION_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "SUBSCRIPTION_SUSPENDED": status.HTTP_403_FORBIDDEN,
        "SUBSCRIPTION_EXPIRED": status.HTTP_403_FORBIDDEN,
        "INVALID_CONSUMPTION": status.HTTP_400_BAD_REQUEST,
        "DATABASE_TRANSACTION_FAILED": status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    return JSONResponse(
        status_code=status_mapping.get(exc.error_code, status.HTTP_400_BAD_REQUEST),
        content={
            "error": exc.error_code,
            "message": exc.message,
            "timestamp": time.time()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    ✅ Handler para errores de validación de Pydantic.
    """
    logger.warning(
        f"❌ Validation Error: {request.url.path}",
        extra={
            "path": request.url.path,
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request data",
            "details": exc.errors(),
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    ✅ Handler general para errores no capturados.
    
    CRÍTICO: Los errores en el Gatekeeper deben ser monitoreados.
    """
    logger.error(
        f"💥 Unexpected Error: {str(exc)}",
        extra={
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": time.time()
        }
    )

# ================================================================================================
# 🛣️ ROUTER MOUNTING
# ================================================================================================

# Montar router de consumo (Gatekeeper)
app.include_router(
    consumption_router,
    tags=["🔒 Gatekeeper - RF8.0"]
)

# ================================================================================================
# 📊 PROMETHEUS INSTRUMENTATION
# ================================================================================================

# Instrumentación automática de FastAPI
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],  # No medir el endpoint de métricas
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True
)

# Añadir métricas estándar de HTTP
instrumentator.instrument(app).expose(
    app,
    endpoint="/metrics",
    tags=["Monitoring"],
    include_in_schema=True
)

logger.info("✅ Prometheus metrics enabled at /metrics")

# ================================================================================================
# 🏥 HEALTH CHECK ENDPOINTS
# ================================================================================================

@app.get(
    "/health", 
    tags=["Health Check"],
    summary="🏥 Health check del servicio",
    response_model=Dict[str, Any]
)
async def health_check():
    """
    ✅ Endpoint de health check para monitoreo.
    
    Verifica que el servicio esté funcionando correctamente.
    """
    return {
        "status": "healthy",
        "service": "consumption-service",
        "version": "1.0.0",
        "timestamp": time.time(),
        "checks": {
            "api": "ok",
            # TODO: Agregar checks de BD, Redis, etc.
            # "database": await check_database(),
            # "redis": await check_redis()
        }
    }


@app.get(
    "/",
    tags=["Info"],
    summary="📋 Información del servicio"
)
async def root():
    """
    ✅ Endpoint de información básica.
    """
    return {
        "service": "💰 Consumption Service - SaaS Gatekeeper",
        "description": "Critical RF8.0 service for consumption control",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "endpoints": {
            "start_processing": "/api/v1/consumption/process/start",
            "update_consumption": "/api/v1/consumption/process/update",
            "user_status": "/api/v1/consumption/user/{user_id}/status"
        }
    }

# ================================================================================================
# 🚀 APPLICATION ENTRY POINT
# ================================================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Consumption Service in development mode")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,  # Solo en desarrollo
        log_level="info"
    )
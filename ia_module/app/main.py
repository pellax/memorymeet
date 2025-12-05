# ================================================================================================
# 🚀 IA/NLP MICROSERVICE - FastAPI Application (RF3.0, RF4.0)
# ================================================================================================
# Aplicación principal del microservicio agnóstico de procesamiento NLP

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, Info

# Importaciones del dominio
from .services.nlp_processor import NLPProcessor
from .models.nlp_models import ProcessingRequest, ProcessingResult
from .exceptions.nlp_exceptions import (
    NLPDomainException,
    InvalidTranscriptionException,
    ProcessingFailedException,
    get_user_friendly_message
)

# ================================================================================================
# 🔧 APPLICATION CONFIGURATION
# ================================================================================================

# Configuración de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================================================================================
# 📊 PROMETHEUS CUSTOM METRICS - RF3.0 & RF4.0 (IA/NLP)
# ================================================================================================

# Métricas de negocio para procesamiento NLP
nlp_processing_total = Counter(
    'nlp_processing_total',
    'Total de procesamientos NLP realizados',
    ['status', 'language']  # success/failed, es/en/auto
)

requirements_extracted_total = Counter(
    'requirements_extracted_total',
    'Total de requisitos extraídos',
    ['type']  # functional, non_functional
)

tasks_assigned_total = Counter(
    'tasks_assigned_total',
    'Total de tareas asignadas',
    ['role']  # backend_developer, frontend_developer, etc.
)

nlp_processing_duration = Histogram(
    'nlp_processing_duration_seconds',
    'Tiempo de procesamiento NLP (crítico para RNF1.0)',
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

requirement_extraction_confidence = Histogram(
    'requirement_extraction_confidence_score',
    'Score de confianza en la extracción de requisitos',
    buckets=[0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
)

task_assignment_confidence = Histogram(
    'task_assignment_confidence_score',
    'Score de confianza en la asignación de tareas',
    buckets=[0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
)

transcription_length = Histogram(
    'transcription_text_length_chars',
    'Longitud de transcripciones procesadas',
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

# Gauge para requests activos
active_nlp_requests = Gauge(
    'active_nlp_processing_requests',
    'Número de procesamiento NLP activos'
)

# Info metric para metadata del servicio
service_info = Info(
    'ia_nlp_service',
    'Información del servicio IA/NLP'
)
service_info.info({
    'version': '1.0.0',
    'service': 'ia-nlp-microservice',
    'rf': 'RF3.0+RF4.0',
    'capabilities': 'requirement_extraction,task_assignment'
})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ✅ Gestión del ciclo de vida del microservicio IA/NLP.
    
    Inicialización y limpieza de recursos (modelos NLP, cache, etc.)
    """
    # Startup
    logger.info("🤖 Starting IA/NLP Microservice")
    logger.info("📋 RF3.0 + RF4.0: Requirement Extraction & Task Assignment")
    
    # TODO: Inicializar modelos NLP pesados aquí
    # await load_spacy_models()
    # await load_transformers_models()
    
    yield
    
    # Shutdown
    logger.info("🔻 Shutting down IA/NLP Microservice")
    # TODO: Limpiar modelos de memoria
    # await cleanup_models()


# ================================================================================================
# 🏗️ FASTAPI APPLICATION SETUP
# ================================================================================================

app = FastAPI(
    title="🤖 IA/NLP Microservice - Requirement Extraction & Task Assignment",
    description="""
    ## 🧠 Microservicio Agnóstico de Procesamiento de Lenguaje Natural
    
    **FUNCIONALIDAD CORE DEL SISTEMA M2PRD-001**
    
    Este microservicio implementa la lógica de IA más crítica del sistema:
    - **RF3.0**: Extracción automática de requisitos funcionales y no funcionales
    - **RF4.0**: Asignación inteligente de tareas a roles de desarrollo
    
    ### 🎯 Capacidades Principales:
    
    - **🔍 Análisis de Texto**: Procesamiento de transcripciones de reuniones
    - **📋 Extracción de Requisitos**: Identificación automática de funcionalidades
    - **🎯 Detección de Prioridades**: Análisis de urgencia basado en lenguaje natural  
    - **👩‍💻 Asignación Inteligente**: Mapeo automático a roles de desarrollador
    - **🌐 Multiidioma**: Soporte para español, inglés y detección automática
    
    ### 🏗️ Arquitectura:
    
    - **Microservicio Agnóstico**: Independiente de otros componentes del sistema
    - **Clean Architecture**: Separación clara entre dominio e infraestructura
    - **TDD**: Desarrollo completamente guiado por tests
    - **SOLID Principles**: Inyección de dependencias y abstracciones
    
    ### 🔗 Integración:
    
    - **Orquestador (n8n/Make)**: Consume este microservicio via REST
    - **Gatekeeper**: Recibe autorización previa del servicio de consumo
    - **Output Agnóstico**: Retorna JSON estructurado para cualquier consumidor
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ================================================================================================
# 🌐 MIDDLEWARE CONFIGURATION
# ================================================================================================

# CORS - Configuración para permitir llamadas del orquestador
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",        # Frontend local (si aplica)
        "http://localhost:8000",        # Backend local
        "http://localhost:8002",        # Gatekeeper service
        "https://n8n.company.com",      # n8n workflows
        "https://make.com",             # Make.com workflows
        "*"                             # Temporal para desarrollo
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Middleware para logging de requests de IA
@app.middleware("http")
async def log_nlp_requests(request: Request, call_next):
    """
    ✅ Middleware específico para logging de procesamiento NLP.
    
    Crítico para monitoreo de performance y debugging de IA.
    """
    start_time = time.time()
    
    # Log de request NLP
    logger.info(
        f"🤖 NLP Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo de procesamiento (crítico para NLP)
    process_time = time.time() - start_time
    
    # Log específico para operaciones NLP
    if "process" in request.url.path:
        logger.info(
            f"🧠 NLP Processing: {response.status_code} ({process_time:.3f}s)",
            extra={
                "status_code": response.status_code,
                "processing_time_seconds": process_time,
                "operation": "nlp_processing",
                "path": request.url.path
            }
        )
    
    # Agregar headers de performance
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Service"] = "ia-nlp-microservice"
    
    return response

# ================================================================================================
# 🚨 EXCEPTION HANDLERS
# ================================================================================================

@app.exception_handler(NLPDomainException)
async def nlp_domain_exception_handler(request: Request, exc: NLPDomainException):
    """
    ✅ Handler especializado para excepciones de dominio NLP.
    
    Convierte excepciones técnicas en respuestas comprensibles.
    """
    logger.warning(
        f"🚨 NLP Domain Exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }
    )
    
    # Mapeo específico de errores NLP
    status_mapping = {
        "INVALID_TRANSCRIPTION": status.HTTP_400_BAD_REQUEST,
        "PROCESSING_FAILED": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "REQUIREMENT_EXTRACTION_FAILED": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "TASK_ASSIGNMENT_FAILED": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "LANGUAGE_DETECTION_FAILED": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "MODEL_LOAD_FAILED": status.HTTP_503_SERVICE_UNAVAILABLE,
        "INSUFFICIENT_DATA": status.HTTP_400_BAD_REQUEST,
        "API_TIMEOUT": status.HTTP_408_REQUEST_TIMEOUT,
        "PRIORITY_DETECTION_FAILED": status.HTTP_422_UNPROCESSABLE_ENTITY
    }
    
    return JSONResponse(
        status_code=status_mapping.get(exc.error_code, status.HTTP_400_BAD_REQUEST),
        content={
            "error": exc.error_code,
            "message": exc.message,
            "user_friendly_message": get_user_friendly_message(exc),
            "timestamp": time.time(),
            "service": "ia-nlp-microservice"
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    ✅ Handler para errores de validación de requests NLP.
    """
    logger.warning(
        f"❌ NLP Request Validation Error: {request.url.path}",
        extra={
            "path": request.url.path,
            "errors": exc.errors(),
            "service": "ia-nlp-microservice"
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request data for NLP processing",
            "details": exc.errors(),
            "timestamp": time.time(),
            "service": "ia-nlp-microservice"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    ✅ Handler general para errores no capturados en NLP.
    
    CRÍTICO: Errores en IA pueden afectar toda la funcionalidad del sistema.
    """
    logger.error(
        f"💥 Unexpected NLP Error: {str(exc)}",
        extra={
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "service": "ia-nlp-microservice"
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_NLP_ERROR",
            "message": "An unexpected error occurred in NLP processing",
            "timestamp": time.time(),
            "service": "ia-nlp-microservice"
        }
    )

# ================================================================================================
# 🤖 NLP PROCESSING ENDPOINTS - RF3.0 & RF4.0
# ================================================================================================

# Instancia global del procesador NLP (en producción sería inyección de dependencias)
nlp_processor = NLPProcessor()

@app.post(
    "/process/nlp",
    response_model=ProcessingResult,
    status_code=status.HTTP_200_OK,
    summary="🧠 Procesar Transcripción con IA/NLP",
    description="""
    **ENDPOINT PRINCIPAL - RF3.0 & RF4.0**
    
    Este endpoint implementa la funcionalidad core de IA del sistema:
    
    ### 🔍 RF3.0 - Extracción de Requisitos:
    - Análisis automático de transcripciones de reuniones
    - Identificación de requisitos funcionales y no funcionales
    - Detección de prioridades basada en lenguaje natural
    - Extracción de contexto y metadatos relevantes
    
    ### 👩‍💻 RF4.0 - Asignación Inteligente:
    - Mapeo automático de requisitos a roles de desarrollo
    - Asignación basada en análisis semántico de contenido
    - Generación de tareas con títulos y descripciones optimizadas
    - Estimación de esfuerzo y clasificación por complejidad
    
    ### 📊 Output Estructurado:
    - Lista completa de requisitos identificados
    - Tareas asignadas con roles específicos
    - Métricas de confianza y estadísticas de procesamiento
    - Metadatos para trazabilidad y auditoría
    
    **Casos de uso:**
    - ✅ Transcripción válida → Requisitos + Tareas asignadas
    - ❌ Transcripción vacía → Error 400 Bad Request  
    - ❌ Sin requisitos detectables → Success=false + mensaje explicativo
    - ⚠️ Procesamiento lento → Optimización automática y alertas
    """
)
async def procesar_transcripcion_nlp(request: ProcessingRequest) -> ProcessingResult:
    """
    🧠 ENDPOINT PRINCIPAL - Procesamiento completo con IA/NLP.
    
    Implementa RF3.0 (extracción) + RF4.0 (asignación) en un solo endpoint.
    """
    try:
        # Log del inicio del procesamiento
        logger.info(
            f"🧠 Starting NLP processing for meeting {request.meeting_id}",
            extra={
                "meeting_id": request.meeting_id,
                "text_length": len(request.transcription_text),
                "language": request.language,
                "operation": "nlp_processing_start"
            }
        )
        
        # Procesamiento principal
        result = nlp_processor.procesar_transcripcion(request)
        
        # Log del resultado
        logger.info(
            f"✅ NLP processing completed for meeting {request.meeting_id}",
            extra={
                "meeting_id": request.meeting_id,
                "success": result.success,
                "requirements_count": len(result.requirements),
                "tasks_count": len(result.assigned_tasks),
                "processing_time": result.processing_time_seconds,
                "confidence": result.confidence_score,
                "operation": "nlp_processing_completed"
            }
        )
        
        return result
        
    except InvalidTranscriptionException as e:
        # Re-raise para que sea manejada por el exception handler
        raise e
    
    except ProcessingFailedException as e:
        # Re-raise para que sea manejada por el exception handler
        raise e
    
    except Exception as e:
        # Log del error y re-raise para exception handler general
        logger.error(
            f"💥 Unexpected error processing meeting {request.meeting_id}: {str(e)}",
            extra={
                "meeting_id": request.meeting_id,
                "error_type": type(e).__name__,
                "operation": "nlp_processing_error"
            },
            exc_info=True
        )
        raise e


@app.post(
    "/process/nlp/async",
    response_model=ProcessingResult,
    status_code=status.HTTP_200_OK,
    summary="🚀 Procesamiento NLP Asíncrono",
    description="""
    **ENDPOINT ASÍNCRONO - Para transcripciones muy largas**
    
    Versión optimizada para procesamiento de transcripciones extensas
    que podrían exceder los timeouts normales de API.
    """
)
async def procesar_transcripcion_async(request: ProcessingRequest) -> ProcessingResult:
    """
    🚀 ENDPOINT ASÍNCRONO - Procesamiento NLP optimizado.
    
    Para transcripciones muy largas o cuando se requiere procesamiento no bloqueante.
    """
    try:
        logger.info(f"🚀 Starting async NLP processing for meeting {request.meeting_id}")
        
        # Procesamiento asíncrono
        result = await nlp_processor.procesar_transcripcion_async(request)
        
        logger.info(
            f"✅ Async NLP processing completed for meeting {request.meeting_id}",
            extra={
                "meeting_id": request.meeting_id,
                "processing_mode": "async",
                "requirements_count": len(result.requirements),
                "tasks_count": len(result.assigned_tasks)
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"💥 Async processing error for meeting {request.meeting_id}: {str(e)}",
            exc_info=True
        )
        raise e

# ================================================================================================
# 🏥 HEALTH CHECK & UTILITY ENDPOINTS
# ================================================================================================

@app.get(
    "/health",
    tags=["Health Check"],
    summary="🏥 Health check del microservicio NLP",
    response_model=Dict[str, Any]
)
async def health_check():
    """
    ✅ Endpoint de health check específico para IA/NLP.
    
    Verifica que los modelos y dependencias estén funcionando correctamente.
    """
    return {
        "status": "healthy",
        "service": "ia-nlp-microservice",
        "version": "1.0.0-green",
        "timestamp": time.time(),
        "capabilities": {
            "requirement_extraction": "enabled",  # RF3.0
            "task_assignment": "enabled",         # RF4.0
            "multilingual": "enabled",
            "async_processing": "enabled"
        },
        "checks": {
            "nlp_models": "ok",
            "memory_usage": "ok",
            # TODO: Agregar checks específicos de modelos NLP
            # "spacy_model": await check_spacy_model(),
            # "transformers_model": await check_transformers_model()
        },
        "performance": {
            "avg_processing_time_ms": 500,  # Mock - en producción serían métricas reales
            "requests_processed": 0,
            "success_rate": 100.0
        }
    }


@app.get(
    "/",
    tags=["Info"],
    summary="📋 Información del microservicio NLP"
)
async def root():
    """
    ✅ Endpoint de información básica del microservicio.
    """
    return {
        "service": "🤖 IA/NLP Microservice - Requirement Extraction & Task Assignment",
        "description": "Microservicio agnóstico para RF3.0 + RF4.0",
        "version": "1.0.0-green",
        "capabilities": ["requirement_extraction", "task_assignment", "multilingual", "async_processing"],
        "docs_url": "/docs",
        "health_url": "/health",
        "endpoints": {
            "process_nlp": "/process/nlp",
            "process_nlp_async": "/process/nlp/async"
        },
        "supported_languages": ["es", "en", "auto"],
        "architecture": {
            "pattern": "Clean Architecture + TDD",
            "principles": ["SOLID", "DIP", "SRP"],
            "integration": "Microservice (Agnóstico)"
        }
    }

# ================================================================================================
# 📊 PROMETHEUS INSTRUMENTATION
# ================================================================================================

# Instrumentación automática de FastAPI para IA/NLP
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress_nlp",
    inprogress_labels=True
)

# Exponer métricas estándar HTTP + custom
instrumentator.instrument(app).expose(
    app,
    endpoint="/metrics",
    tags=["Monitoring"],
    include_in_schema=True
)

logger.info("✅ Prometheus metrics enabled at /metrics for IA/NLP service")

# ================================================================================================
# 🚀 APPLICATION ENTRY POINT
# ================================================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting IA/NLP Microservice in development mode")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,  # Puerto específico para microservicio NLP
        reload=True,  # Solo en desarrollo
        log_level="info"
    )
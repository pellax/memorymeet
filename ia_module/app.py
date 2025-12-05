"""
✅ FastAPI Application - Módulo IA/NLP M2PRD-001
API principal para procesamiento de transcripciones y extracción de requisitos.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from config import settings
from models import (
    TranscriptionResult,
    Requirement,
    PRD,
    TranscriptionException,
    RequirementExtractionException
)

# ================================================================================================
# 🔍 LOGGING CONFIGURATION
# ================================================================================================
logger = structlog.get_logger(__name__)


# ================================================================================================
# 🚀 LIFESPAN EVENTS - Startup y Shutdown
# ================================================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ✅ Lifespan Context Manager - Gestiona startup y shutdown.
    
    Startup:
    - Inicializar conexiones
    - Cargar modelos spaCy
    - Validar configuración
    
    Shutdown:
    - Cerrar conexiones
    - Cleanup de recursos
    """
    # STARTUP
    logger.info(
        "application_startup_started",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment
    )
    
    try:
        # TODO: Inicializar servicios
        # - Cargar modelo spaCy
        # - Inicializar clientes (Deepgram, OpenAI)
        # - Verificar conexiones
        
        logger.info(
            "application_startup_completed",
            status="ready"
        )
        
        yield  # Aplicación corriendo
        
    except Exception as e:
        logger.error(
            "application_startup_failed",
            error=str(e),
            exc_info=True
        )
        raise
    
    finally:
        # SHUTDOWN
        logger.info("application_shutdown_started")
        
        # TODO: Cleanup
        # - Cerrar conexiones a APIs
        # - Liberar recursos
        
        logger.info("application_shutdown_completed")


# ================================================================================================
# 🎯 FASTAPI APPLICATION
# ================================================================================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Módulo de IA/NLP para procesamiento de transcripciones y extracción de requisitos",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development() else None,
    redoc_url="/redoc" if settings.is_development() else None
)


# ================================================================================================
# 🔧 MIDDLEWARE CONFIGURATION
# ================================================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development() else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================================================
# 📊 HEALTH CHECK ENDPOINTS
# ================================================================================================

@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint",
    response_model=Dict[str, Any]
)
async def health_check():
    """
    ✅ Health Check - Verifica estado del servicio.
    
    Returns:
        dict: Estado del servicio y sus dependencias
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": time.time()
    }


@app.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness probe",
    response_model=Dict[str, bool]
)
async def readiness_check():
    """
    ✅ Readiness Check - Verifica si el servicio está listo para recibir tráfico.
    
    Returns:
        dict: Estado de preparación del servicio
    """
    try:
        # TODO: Verificar dependencias críticas
        # - Conexión a Deepgram API
        # - Conexión a OpenAI API
        # - Modelo spaCy cargado
        
        return {
            "ready": True,
            "deepgram_api": True,  # TODO: Verificar real
            "openai_api": True,    # TODO: Verificar real
            "spacy_model": True    # TODO: Verificar real
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@app.get(
    "/health/live",
    tags=["Health"],
    summary="Liveness probe",
    response_model=Dict[str, bool]
)
async def liveness_check():
    """
    ✅ Liveness Check - Verifica si el servicio está vivo.
    
    Returns:
        dict: Estado de vida del servicio
    """
    return {"alive": True}


# ================================================================================================
# 🤖 API ENDPOINTS - TRANSCRIPTION (RF2.0)
# ================================================================================================

@app.post(
    "/api/v1/transcribe",
    tags=["Transcription"],
    summary="Transcribe audio from meeting URL",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK
)
async def transcribe_audio(
    meeting_url: str,
    language: str = "es"
):
    """
    ✅ Transcribe Audio - Transcribe audio de reunión usando Deepgram (RF2.0).
    
    Args:
        meeting_url: URL del audio de la reunión
        language: Idioma del audio (default: es)
    
    Returns:
        dict: Resultado de la transcripción
    
    Raises:
        HTTPException: Si falla la transcripción
    """
    start_time = time.time()
    
    try:
        logger.info(
            "transcription_started",
            meeting_url=meeting_url,
            language=language
        )
        
        # TODO: Implementar lógica de transcripción
        # 1. Validar URL
        # 2. Llamar a Deepgram API con Circuit Breaker
        # 3. Procesar respuesta
        
        # MOCK Response por ahora
        mock_transcription = TranscriptionResult(
            text="Esta es una transcripción de prueba del módulo IA/NLP. "
                 "Necesitamos implementar autenticación de usuarios con JWT y crear un dashboard responsive.",
            language=language,
            confidence=0.95,
            duration_seconds=120.0,
            words_count=15
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "transcription_completed",
            meeting_url=meeting_url,
            processing_time_seconds=processing_time,
            words_count=mock_transcription.words_count
        )
        
        return {
            "status": "success",
            "data": {
                "text": mock_transcription.text,
                "language": mock_transcription.language,
                "confidence": mock_transcription.confidence,
                "duration_seconds": mock_transcription.duration_seconds,
                "words_count": mock_transcription.words_count
            },
            "processing_time_seconds": processing_time
        }
        
    except TranscriptionException as e:
        logger.error(
            "transcription_failed",
            meeting_url=meeting_url,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "transcription_error",
            meeting_url=meeting_url,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during transcription"
        )


# ================================================================================================
# 📝 API ENDPOINTS - REQUIREMENT EXTRACTION (RF3.0, RF4.0)
# ================================================================================================

@app.post(
    "/api/v1/extract-requirements",
    tags=["Requirements"],
    summary="Extract requirements from transcription",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK
)
async def extract_requirements(
    transcription_text: str,
    extract_assignees: bool = True
):
    """
    ✅ Extract Requirements - Extrae requisitos de transcripción (RF3.0, RF4.0).
    
    Args:
        transcription_text: Texto de la transcripción
        extract_assignees: Si debe asignar roles automáticamente (RF4.0)
    
    Returns:
        dict: Requisitos extraídos y tareas asignadas
    
    Raises:
        HTTPException: Si falla la extracción
    """
    start_time = time.time()
    
    try:
        logger.info(
            "requirement_extraction_started",
            text_length=len(transcription_text),
            extract_assignees=extract_assignees
        )
        
        # TODO: Implementar lógica de extracción
        # 1. Usar OpenAI GPT-4 o spaCy según configuración
        # 2. Clasificar requisitos (funcional/no funcional)
        # 3. Asignar roles automáticamente si extract_assignees=True
        # 4. Aplicar Strategy Pattern para algoritmos intercambiables
        
        # MOCK Response por ahora
        from models import RequirementType, RequirementPriority, AssigneeRole
        
        mock_requirements = [
            Requirement(
                id="req-1",
                description="Implementar autenticación de usuarios con JWT",
                type=RequirementType.FUNCTIONAL,
                priority=RequirementPriority.P0,
                assignee_role=AssigneeRole.BACKEND_DEVELOPER,
                keywords=["autenticación", "JWT", "usuarios"],
                confidence_score=0.92
            ),
            Requirement(
                id="req-2",
                description="Crear dashboard responsive para visualización de datos",
                type=RequirementType.FUNCTIONAL,
                priority=RequirementPriority.P1,
                assignee_role=AssigneeRole.FRONTEND_DEVELOPER,
                keywords=["dashboard", "responsive", "UI"],
                confidence_score=0.88
            )
        ]
        
        processing_time = time.time() - start_time
        
        logger.info(
            "requirement_extraction_completed",
            requirements_count=len(mock_requirements),
            processing_time_seconds=processing_time
        )
        
        return {
            "status": "success",
            "data": {
                "requirements": [req.to_dict() for req in mock_requirements],
                "total_requirements": len(mock_requirements)
            },
            "processing_time_seconds": processing_time
        }
        
    except RequirementExtractionException as e:
        logger.error(
            "requirement_extraction_failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Requirement extraction failed: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "requirement_extraction_error",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during requirement extraction"
        )


# ================================================================================================
# 📄 API ENDPOINTS - PRD GENERATION (RF3.0)
# ================================================================================================

@app.post(
    "/api/v1/generate-prd",
    tags=["PRD"],
    summary="Generate complete PRD from meeting",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK
)
async def generate_prd(
    meeting_id: str,
    meeting_url: str,
    language: str = "es"
):
    """
    ✅ Generate PRD - Genera PRD completo desde reunión (RF3.0).
    
    Flujo completo:
    1. Transcribir audio (RF2.0)
    2. Extraer requisitos (RF3.0)
    3. Asignar tareas (RF4.0)
    4. Generar PRD estructurado
    
    Args:
        meeting_id: ID de la reunión
        meeting_url: URL del audio de la reunión
        language: Idioma del audio
    
    Returns:
        dict: PRD completo con requisitos y tareas
    
    Raises:
        HTTPException: Si falla la generación del PRD
    """
    start_time = time.time()
    
    try:
        logger.info(
            "prd_generation_started",
            meeting_id=meeting_id,
            meeting_url=meeting_url
        )
        
        # TODO: Implementar flujo completo
        # 1. Transcribir
        # 2. Extraer requisitos
        # 3. Generar PRD
        # 4. Asignar tareas
        
        # MOCK Response por ahora
        processing_time = time.time() - start_time
        
        logger.info(
            "prd_generation_completed",
            meeting_id=meeting_id,
            processing_time_seconds=processing_time
        )
        
        return {
            "status": "success",
            "data": {
                "prd_id": "prd-mock-123",
                "meeting_id": meeting_id,
                "title": "PRD Mock - Sistema de Autenticación",
                "requirements_count": 2,
                "tasks_count": 2,
                "complexity_level": "LOW"
            },
            "processing_time_seconds": processing_time
        }
        
    except Exception as e:
        logger.error(
            "prd_generation_error",
            meeting_id=meeting_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during PRD generation"
        )


# ================================================================================================
# 🚀 APPLICATION ENTRY POINT
# ================================================================================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development(),
        log_level=settings.log_level.lower()
    )

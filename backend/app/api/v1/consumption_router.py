# ================================================================================================
# 🌐 CONSUMPTION API ROUTER - FastAPI endpoints para el Gatekeeper (RF8.0)
# ================================================================================================
# Endpoints que exponen la funcionalidad crítica del servicio de consumo

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from ...domain.services.subscription_consumption_service import SubscriptionConsumptionService
from ...domain.value_objects.consumption_response import (
    ConsumptionVerificationResponse,
    ConsumptionUpdateResponse
)
from ...domain.exceptions.consumption_exceptions import (
    InsufficientHoursException,
    UserNotFoundException,
    SubscriptionNotFoundException,
    DatabaseTransactionException,
    InvalidConsumptionException
)
from ...services.webhook_trigger import (
    WebhookTrigger,
    WebhookPayload,
    WebhookStatus,
    create_webhook_trigger,
    create_webhook_payload_from_gatekeeper_data
)

# ================================================================================================
# 📝 PYDANTIC MODELS - Request/Response schemas
# ================================================================================================

class ProcessStartRequest(BaseModel):
    """✅ Request model para iniciar procesamiento"""
    user_id: str = Field(..., min_length=1, description="ID del usuario")
    meeting_url: str = Field(..., min_length=1, description="URL de la reunión")
    estimated_duration_minutes: int = Field(
        ..., 
        gt=0, 
        le=480,  # Max 8 horas
        description="Duración estimada en minutos"
    )
    meeting_id: str = Field(..., min_length=1, description="ID único de la reunión")
    transcription_text: str = Field(..., min_length=10, description="Texto de la transcripción de la reunión")
    language: str = Field(default="auto", description="Idioma de la transcripción (es, en, auto)")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-123",
                "meeting_url": "https://meet.google.com/abc-defg-hij",
                "estimated_duration_minutes": 60,
                "meeting_id": "meeting-456",
                "transcription_text": "Juan: Necesitamos implementar un sistema de autenticación...",
                "language": "es"
            }
        }


class ProcessUpdateRequest(BaseModel):
    """✅ Request model para actualizar consumo post-procesamiento"""
    user_id: str = Field(..., min_length=1, description="ID del usuario")
    actual_duration_minutes: int = Field(
        ..., 
        gt=0, 
        le=480,
        description="Duración real en minutos"
    )
    meeting_id: str = Field(..., min_length=1, description="ID único de la reunión")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-123",
                "actual_duration_minutes": 75,
                "meeting_id": "meeting-456"
            }
        }


class ProcessStartResponse(BaseModel):
    """✅ Response model para inicio de procesamiento"""
    authorized: bool
    message: str
    user_id: str
    remaining_hours: float
    consumption_percentage: float
    workflow_trigger_url: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "authorized": True,
                "message": "Processing authorized. Workflow triggered.",
                "user_id": "user-123",
                "remaining_hours": 8.5,
                "consumption_percentage": 15.0,
                "workflow_trigger_url": "https://n8n.company.com/webhook/process-meeting"
            }
        }


# ================================================================================================
# 🛣️ ROUTER CONFIGURATION
# ================================================================================================

router = APIRouter(
    prefix="/api/v1/consumption",
    tags=["Consumption Management"],
    responses={
        403: {"description": "Forbidden - Insufficient hours"},
        404: {"description": "Not Found - User or subscription not found"},
        500: {"description": "Internal Server Error - Transaction failed"}
    }
)

# ================================================================================================
# 🎯 DEPENDENCY INJECTION - Service layer
# ================================================================================================

async def get_consumption_service() -> SubscriptionConsumptionService:
    """
    ✅ Factory para obtener instancia del servicio de consumo.
    
    En producción, esto debería usar un container de DI real.
    """
    # TODO: Implementar inyección de dependencias real con container
    # Por ahora, mock para completar la API
    from ...domain.repositories.subscription_repository import SubscriptionRepository, UserRepository
    
    subscription_repo = SubscriptionRepository()  # Mock
    user_repo = UserRepository()  # Mock
    
    return SubscriptionConsumptionService(
        subscription_repository=subscription_repo,
        user_repository=user_repo
    )

# ================================================================================================
# 🚦 API ENDPOINTS - Fase 1 del Gatekeeper
# ================================================================================================

@router.post(
    "/process/start",
    response_model=ProcessStartResponse,
    status_code=status.HTTP_200_OK,
    summary="🚦 Iniciar procesamiento de reunión (Gatekeeper)",
    description="""
    **ENDPOINT CRÍTICO - RF8.0 Gatekeeper**
    
    Este endpoint actúa como **GATEKEEPER** del sistema SaaS. Verifica si un usuario
    puede procesar una reunión basado en su consumo de horas disponible.
    
    **Flujo:**
    1. Verificar consumo disponible del usuario
    2. Si autorizado → Disparar workflow de procesamiento 
    3. Si rechazado → Error 403 Forbidden
    
    **Casos de uso:**
    - ✅ Usuario con horas suficientes → 200 OK + trigger workflow
    - ❌ Usuario sin horas → 403 Forbidden
    - ❌ Usuario no encontrado → 404 Not Found
    - ❌ Suscripción inactiva → 403 Forbidden
    """
)
async def iniciar_procesamiento_reunion(
    request: ProcessStartRequest,
    consumption_service: SubscriptionConsumptionService = Depends(get_consumption_service)
) -> ProcessStartResponse:
    """
    🚦 GATEKEEPER + ORQUESTACIÓN - Verificar consumo y disparar workflow.
    
    Endpoint que implementa:
    1. RF8.0 (Control de Consumo) - Verificación de horas
    2. Orquestación - Disparar webhook a n8n con transcripción
    3. Circuit Breaker - Tolerancia a fallos de webhook
    """
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    
    try:
        # Convertir minutos estimados a horas
        estimated_hours = request.estimated_duration_minutes / 60.0
        
        # 1. VERIFICAR CONSUMO DISPONIBLE (LÓGICA CRÍTICA RF8.0)
        verification_result = await consumption_service.verificar_consumo_disponible(
            user_id=request.user_id,
            required_hours=estimated_hours
        )
        
        # 2. ✅ USUARIO AUTORIZADO - DISPARAR WEBHOOK A N8N
        processing_id = f"proc-{request.meeting_id}-{int(time.time())}"
        callback_url = "/api/v1/consumption/process/update"
        
        # Crear payload para webhook con transcripción
        webhook_payload = create_webhook_payload_from_gatekeeper_data(
            request=request,
            authorization_response=verification_result,
            processing_id=processing_id,
            callback_url=callback_url
        )
        
        # Inicializar webhook trigger
        webhook_trigger = create_webhook_trigger(environment="development")
        
        try:
            # 3. DISPARAR WEBHOOK A N8N/MAKE
            webhook_response = await webhook_trigger.trigger_workflow(webhook_payload)
            
            if webhook_response.status.value == "SENT":
                # ✅ Webhook exitoso - Procesamiento iniciado
                logger.info(
                    f"Webhook enviado exitosamente para procesamiento {processing_id}",
                    extra={
                        "meeting_id": request.meeting_id,
                        "processing_id": processing_id,
                        "user_id": request.user_id
                    }
                )
                
                return ProcessStartResponse(
                    authorized=True,
                    message=f"Processing initiated successfully. ID: {processing_id}",
                    user_id=request.user_id,
                    remaining_hours=verification_result.remaining_hours,
                    consumption_percentage=verification_result.consumption_percentage,
                    workflow_trigger_url=webhook_trigger.webhook_url
                )
            else:
                # ❌ Webhook falló - Error de orquestación
                logger.error(
                    f"Error en webhook para procesamiento {processing_id}: {webhook_response.error_message}",
                    extra={
                        "meeting_id": request.meeting_id,
                        "webhook_status": webhook_response.status.value,
                        "error": webhook_response.error_message
                    }
                )
                
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "WORKFLOW_UNAVAILABLE",
                        "message": "Processing service temporarily unavailable. Please try again later.",
                        "processing_id": processing_id,
                        "user_id": request.user_id
                    }
                )
                
        except Exception as webhook_error:
            # ❌ Error en webhook - Fallo de orquestación
            logger.error(
                f"Excepción en webhook para procesamiento {processing_id}: {str(webhook_error)}",
                extra={"meeting_id": request.meeting_id, "user_id": request.user_id},
                exc_info=True
            )
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "WORKFLOW_ERROR",
                    "message": "Internal error in processing service. Support has been notified.",
                    "processing_id": processing_id,
                    "user_id": request.user_id
                }
            )
        
    except InsufficientHoursException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "INSUFFICIENT_HOURS",
                "message": f"Not enough hours available. Required: {estimated_hours:.2f}, Available: {e.available_hours:.2f}",
                "user_id": e.user_id,
                "available_hours": e.available_hours,
                "required_hours": e.required_hours
            }
        )
    
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "USER_NOT_FOUND",
                "message": f"User {e.user_id} not found",
                "user_id": e.user_id
            }
        )
    
    except SubscriptionNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "NO_ACTIVE_SUBSCRIPTION",
                "message": f"User {e.user_id} has no active subscription",
                "user_id": e.user_id
            }
        )
    
    except InvalidConsumptionException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_CONSUMPTION",
                "message": e.reason,
                "user_id": e.user_id,
                "invalid_hours": e.invalid_hours
            }
        )


@router.put(
    "/process/update",
    response_model=ConsumptionUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="📊 Actualizar consumo post-procesamiento",
    description="""
    **ENDPOINT POST-PROCESAMIENTO - RF8.0**
    
    Este endpoint se llama DESPUÉS del procesamiento exitoso de una reunión
    para actualizar el consumo real de horas del usuario.
    
    **Flujo:**
    1. Recibir duración real del procesamiento
    2. Actualizar consumo en base de datos (transacción ACID)
    3. Retornar horas consumidas y restantes
    
    **Casos de uso:**
    - ✅ Actualización exitosa → 200 OK + datos actualizados
    - ❌ Error de transacción → 500 Internal Server Error
    - ❌ Usuario no encontrado → 404 Not Found
    """
)
async def actualizar_consumo_procesamiento(
    request: ProcessUpdateRequest,
    consumption_service: SubscriptionConsumptionService = Depends(get_consumption_service)
) -> ConsumptionUpdateResponse:
    """
    📊 POST-PROCESAMIENTO - Actualizar consumo real del usuario.
    
    Endpoint que actualiza el consumo de horas después del procesamiento exitoso.
    """
    try:
        # Actualizar consumo con duración real
        update_result = await consumption_service.actualizar_registro_consumo(
            user_id=request.user_id,
            duration_minutes=request.actual_duration_minutes,
            meeting_id=request.meeting_id
        )
        
        return ConsumptionUpdateResponse.from_update_result(update_result)
        
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "USER_NOT_FOUND",
                "message": f"User {e.user_id} not found",
                "user_id": e.user_id
            }
        )
    
    except SubscriptionNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SUBSCRIPTION_NOT_FOUND",
                "message": f"No active subscription found for user {e.user_id}",
                "user_id": e.user_id
            }
        )
    
    except DatabaseTransactionException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "TRANSACTION_FAILED",
                "message": "Failed to update consumption due to database error",
                "transaction_id": e.transaction_id,
                "user_id": e.user_id
            }
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_INPUT",
                "message": str(e)
            }
        )


@router.get(
    "/user/{user_id}/status",
    response_model=ConsumptionVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="📈 Consultar estado de consumo del usuario",
    description="""
    **ENDPOINT DE CONSULTA - RF8.0**
    
    Endpoint para consultar el estado actual de consumo de un usuario.
    Útil para dashboards, reportes y verificaciones.
    """
)
async def consultar_estado_consumo(
    user_id: str,
    consumption_service: SubscriptionConsumptionService = Depends(get_consumption_service)
) -> ConsumptionVerificationResponse:
    """
    📈 CONSULTA - Obtener estado actual de consumo del usuario.
    """
    try:
        # Obtener estado de consumo
        estado = await consumption_service.obtener_estado_consumo(user_id)
        
        return ConsumptionVerificationResponse(
            authorized=estado.can_consume,
            user_id=user_id,
            remaining_hours=estado.remaining_hours,
            plan_name=estado.subscription.plan.name,
            consumption_percentage=estado.consumption_percentage,
            message=f"User has {estado.remaining_hours:.2f} hours remaining"
        )
        
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "USER_NOT_FOUND",
                "message": f"User {user_id} not found"
            }
        )
    
    except SubscriptionNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SUBSCRIPTION_NOT_FOUND",
                "message": f"No active subscription found for user {user_id}"
            }
        )
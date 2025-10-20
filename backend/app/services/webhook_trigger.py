# ================================================================================================
# 🔗 WEBHOOK TRIGGER - Integración con n8n/Make Workflow
# ================================================================================================
# Componente que dispara workflows en n8n mediante webhooks HTTP

import httpx
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
from enum import Enum

from ..domain.exceptions.consumption_exceptions import DatabaseTransactionException


class WebhookStatus(Enum):
    """Estados de llamadas a webhook"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class WebhookPayload:
    """
    📤 Payload estándar para webhook de n8n.
    
    Estructura de datos que se enviará al workflow de n8n/Make.
    """
    # Datos del usuario y reunión
    user_id: str
    meeting_id: str
    meeting_url: str
    transcription_text: str
    
    # Configuración de procesamiento
    language: str = "auto"
    estimated_duration_minutes: int = 60
    
    # Datos del gatekeeper
    remaining_hours: float = 0.0
    plan_name: str = ""
    consumption_percentage: float = 0.0
    
    # Metadatos del workflow
    workflow_trigger_id: str = field(default_factory=lambda: f"trigger-{int(datetime.utcnow().timestamp())}")
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    
    # URLs de callback para n8n
    consumption_callback_url: str = ""
    status_callback_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para JSON"""
        return {
            "user_id": self.user_id,
            "meeting_id": self.meeting_id,
            "meeting_url": self.meeting_url,
            "transcription_text": self.transcription_text,
            "language": self.language,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "remaining_hours": self.remaining_hours,
            "plan_name": self.plan_name,
            "consumption_percentage": self.consumption_percentage,
            "workflow_trigger_id": self.workflow_trigger_id,
            "triggered_at": self.triggered_at.isoformat(),
            "callbacks": {
                "consumption_update": self.consumption_callback_url,
                "status_update": self.status_callback_url
            },
            "services": {
                "nlp_service_url": "http://localhost:8003",
                "gatekeeper_service_url": "http://localhost:8002"
            }
        }


@dataclass
class WebhookResponse:
    """
    📥 Respuesta del webhook de n8n.
    """
    status: WebhookStatus
    webhook_trigger_id: str
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    http_status_code: Optional[int] = None
    response_time_ms: float = 0.0
    sent_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_successful(self) -> bool:
        """Verificar si el webhook fue exitoso"""
        return (
            self.status == WebhookStatus.SENT and 
            self.http_status_code and 
            200 <= self.http_status_code < 300
        )
    
    @property
    def response_id(self) -> str:
        """ID de respuesta para logging y tracking."""
        return self.webhook_trigger_id


class WebhookTrigger:
    """
    🔗 Disparador de Webhooks para n8n/Make.
    
    Componente responsable de disparar workflows en plataformas de automatización
    enviando datos estructurados via HTTP POST.
    """
    
    def __init__(
        self,
        n8n_webhook_url: Optional[str] = None,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0
    ):
        self.n8n_webhook_url = n8n_webhook_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        
        # HTTP Client configurado
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "M2PRD-Gatekeeper/1.0"
            }
        )
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    @property
    def webhook_url(self) -> Optional[str]:
        """Propiedad para acceder a la URL del webhook configurada."""
        return self.n8n_webhook_url
    
    async def trigger_n8n_workflow(
        self, 
        payload: WebhookPayload,
        webhook_url: Optional[str] = None
    ) -> WebhookResponse:
        """
        🚀 Disparar workflow en n8n mediante webhook.
        
        Args:
            payload: Datos estructurados para el workflow
            webhook_url: URL del webhook (opcional, usa la configurada por defecto)
            
        Returns:
            WebhookResponse: Resultado de la llamada al webhook
        """
        # Usar URL proporcionada o la configurada por defecto
        target_url = webhook_url or self.n8n_webhook_url
        
        if not target_url:
            return WebhookResponse(
                status=WebhookStatus.FAILED,
                webhook_trigger_id=payload.workflow_trigger_id,
                error_message="No webhook URL configured"
            )
        
        self.logger.info(
            f"🔗 Triggering n8n workflow for meeting {payload.meeting_id}",
            extra={
                "meeting_id": payload.meeting_id,
                "user_id": payload.user_id,
                "workflow_trigger_id": payload.workflow_trigger_id,
                "webhook_url": target_url
            }
        )
        
        start_time = datetime.utcnow()
        
        # Intentar envío con reintentos
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self._send_webhook_request(target_url, payload, attempt)
                
                if response.is_successful():
                    self.logger.info(
                        f"✅ n8n webhook triggered successfully for meeting {payload.meeting_id}",
                        extra={
                            "meeting_id": payload.meeting_id,
                            "workflow_trigger_id": payload.workflow_trigger_id,
                            "attempt": attempt,
                            "response_time_ms": response.response_time_ms
                        }
                    )
                    return response
                else:
                    # Log warning pero continuar con reintentos si es aplicable
                    self.logger.warning(
                        f"⚠️ n8n webhook attempt {attempt} failed for meeting {payload.meeting_id}",
                        extra={
                            "meeting_id": payload.meeting_id,
                            "attempt": attempt,
                            "status_code": response.http_status_code,
                            "error": response.error_message
                        }
                    )
                    
                    # Si es el último intento, retornar el error
                    if attempt == self.max_retries:
                        return response
                        
            except Exception as e:
                error_msg = f"HTTP request failed on attempt {attempt}: {str(e)}"
                
                self.logger.error(
                    f"❌ n8n webhook error on attempt {attempt} for meeting {payload.meeting_id}",
                    extra={
                        "meeting_id": payload.meeting_id,
                        "attempt": attempt,
                        "error": str(e)
                    },
                    exc_info=True
                )
                
                # Si es el último intento, retornar el error
                if attempt == self.max_retries:
                    return WebhookResponse(
                        status=WebhookStatus.FAILED,
                        webhook_trigger_id=payload.workflow_trigger_id,
                        error_message=error_msg,
                        response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                    )
            
            # Esperar antes del siguiente intento
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay_seconds * attempt)  # Backoff exponencial
        
        # Este código no debería alcanzarse, pero por seguridad
        return WebhookResponse(
            status=WebhookStatus.FAILED,
            webhook_trigger_id=payload.workflow_trigger_id,
            error_message="Max retries exceeded"
        )
    
    # Alias para compatibilidad con endpoint
    async def trigger_workflow(self, payload: WebhookPayload, webhook_url: Optional[str] = None) -> WebhookResponse:
        """Alias para trigger_n8n_workflow para compatibilidad."""
        return await self.trigger_n8n_workflow(payload, webhook_url)
    
    async def _send_webhook_request(
        self, 
        url: str, 
        payload: WebhookPayload, 
        attempt: int
    ) -> WebhookResponse:
        """
        📡 Enviar request HTTP al webhook.
        """
        start_time = datetime.utcnow()
        
        try:
            # Preparar datos JSON
            json_data = payload.to_dict()
            
            # Realizar request POST
            response = await self.http_client.post(
                url,
                json=json_data
            )
            
            # Calcular tiempo de respuesta
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Procesar respuesta
            response_data = None
            try:
                if response.content:
                    response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            # Determinar status
            if 200 <= response.status_code < 300:
                status = WebhookStatus.SENT
                error_message = None
            else:
                status = WebhookStatus.FAILED
                error_message = f"HTTP {response.status_code}: {response.text[:200]}"
            
            return WebhookResponse(
                status=status,
                webhook_trigger_id=payload.workflow_trigger_id,
                response_data=response_data,
                error_message=error_message,
                http_status_code=response.status_code,
                response_time_ms=response_time
            )
            
        except httpx.TimeoutException:
            return WebhookResponse(
                status=WebhookStatus.TIMEOUT,
                webhook_trigger_id=payload.workflow_trigger_id,
                error_message=f"Request timeout after {self.timeout_seconds} seconds",
                response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
        
        except httpx.RequestError as e:
            return WebhookResponse(
                status=WebhookStatus.FAILED,
                webhook_trigger_id=payload.workflow_trigger_id,
                error_message=f"Request error: {str(e)}",
                response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
    
    def configure_webhook_url(self, webhook_url: str) -> None:
        """
        ⚙️ Configurar URL del webhook de n8n.
        
        Permite configurar la URL dinámicamente cuando esté disponible.
        """
        self.n8n_webhook_url = webhook_url
        self.logger.info(f"🔧 Webhook URL configured: {webhook_url}")
    
    async def test_webhook_connection(
        self, 
        webhook_url: Optional[str] = None
    ) -> WebhookResponse:
        """
        🧪 Probar conectividad con el webhook.
        
        Envía un payload de prueba para verificar que n8n responde correctamente.
        """
        test_payload = WebhookPayload(
            user_id="test-user",
            meeting_id="test-meeting",
            meeting_url="https://meet.google.com/test",
            transcription_text="Test transcription for webhook connectivity",
            language="en",
            workflow_trigger_id="test-connection"
        )
        
        return await self.trigger_n8n_workflow(test_payload, webhook_url)
    
    def get_callback_urls(self, base_url: str = "http://localhost:8002") -> Dict[str, str]:
        """
        📞 Generar URLs de callback para n8n.
        
        n8n puede usar estas URLs para notificar de vuelta al sistema.
        """
        return {
            "consumption_update": f"{base_url}/api/v1/consumption/process/update",
            "status_update": f"{base_url}/api/v1/workflow/status",
            "health_check": f"{base_url}/health"
        }
    
    async def close(self):
        """Cerrar el cliente HTTP"""
        await self.http_client.aclose()


# ================================================================================================
# 🏭 FACTORY & CONFIGURATION
# ================================================================================================

def create_webhook_trigger(
    webhook_url: Optional[str] = None,
    environment: str = "development"
) -> WebhookTrigger:
    """
    🏭 Factory para crear WebhookTrigger configurado.
    
    Args:
        webhook_url: URL del webhook de n8n
        environment: Entorno (development, staging, production)
    """
    # Configuración por entorno
    config = {
        "development": {
            "timeout_seconds": 30,
            "max_retries": 2,
            "retry_delay_seconds": 1.0
        },
        "staging": {
            "timeout_seconds": 45,
            "max_retries": 3,
            "retry_delay_seconds": 2.0
        },
        "production": {
            "timeout_seconds": 60,
            "max_retries": 5,
            "retry_delay_seconds": 3.0
        }
    }
    
    env_config = config.get(environment, config["development"])
    
    return WebhookTrigger(
        n8n_webhook_url=webhook_url,
        **env_config
    )


# ================================================================================================
# 🔧 HELPER FUNCTIONS
# ================================================================================================

def create_webhook_payload_from_gatekeeper_data(
    request,  # ProcessStartRequest
    authorization_response,  # ConsumptionVerificationResponse
    processing_id: str,
    callback_url: str,
    callback_base_url: str = "http://localhost:8002"
) -> WebhookPayload:
    """
    🔄 Crear payload de webhook desde datos del Gatekeeper.
    
    Transforma los datos del request/response del Gatekeeper en el formato esperado por n8n.
    
    Args:
        request: ProcessStartRequest con datos de la solicitud
        authorization_response: ConsumptionVerificationResponse con autorización
        processing_id: ID único del procesamiento
        callback_url: URL de callback para actualizaciones
        callback_base_url: URL base para generar callbacks
    """
    webhook_trigger = WebhookTrigger()
    callback_urls = webhook_trigger.get_callback_urls(callback_base_url)
    
    return WebhookPayload(
        user_id=request.user_id,
        meeting_id=request.meeting_id,
        meeting_url=request.meeting_url,
        transcription_text=request.transcription_text,
        language=getattr(request, 'language', 'auto'),
        estimated_duration_minutes=request.estimated_duration_minutes,
        remaining_hours=authorization_response.remaining_hours,
        plan_name=getattr(authorization_response, 'plan_name', 'default_plan'),
        consumption_percentage=authorization_response.consumption_percentage,
        consumption_callback_url=callback_url,
        status_callback_url=callback_urls["status_update"],
        workflow_trigger_id=processing_id  # Usar processing_id como trigger_id
    )

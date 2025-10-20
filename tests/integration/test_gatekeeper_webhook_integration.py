# ================================================================================================
# 🧪 INTEGRATION TESTS - Gatekeeper + Webhook Integration (Fase 3)
# ================================================================================================
# Tests que verifican la integración completa entre Gatekeeper y n8n webhook

import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
from httpx import Response
from datetime import datetime

from backend.app.api.v1.consumption_router import ProcessStartRequest, ProcessStartResponse
from backend.app.services.webhook_trigger import (
    WebhookTrigger, 
    WebhookPayload, 
    WebhookStatus,
    create_webhook_trigger
)
from backend.app.domain.value_objects.consumption_response import ConsumptionVerificationResponse


class TestGatekeeperWebhookIntegration:
    """✅ Tests de integración para Gatekeeper + n8n webhook"""
    
    def test_should_create_webhook_payload_from_gatekeeper_request(self):
        """RED: Test para creación de payload desde request del gatekeeper"""
        # Given
        request = ProcessStartRequest(
            user_id="user-123",
            meeting_url="https://meet.google.com/test-meeting",
            estimated_duration_minutes=60,
            meeting_id="meeting-456",
            transcription_text="Juan: Necesitamos implementar autenticación...",
            language="es"
        )
        
        authorization_response = ConsumptionVerificationResponse(
            authorized=True,
            user_id="user-123",
            remaining_hours=8.5,
            consumption_percentage=15.0,
            plan_name="Pro Plan",
            message="Processing authorized"
        )
        
        processing_id = "proc-meeting-456-12345"
        callback_url = "/api/v1/consumption/process/update"
        
        # When
        from backend.app.services.webhook_trigger import create_webhook_payload_from_gatekeeper_data
        
        payload = create_webhook_payload_from_gatekeeper_data(
            request=request,
            authorization_response=authorization_response,
            processing_id=processing_id,
            callback_url=callback_url
        )
        
        # Then
        assert payload.user_id == "user-123"
        assert payload.meeting_id == "meeting-456"
        assert payload.meeting_url == "https://meet.google.com/test-meeting"
        assert payload.transcription_text == "Juan: Necesitamos implementar autenticación..."
        assert payload.language == "es"
        assert payload.estimated_duration_minutes == 60
        assert payload.remaining_hours == 8.5
        assert payload.consumption_percentage == 15.0
        assert payload.consumption_callback_url == callback_url
        assert payload.workflow_trigger_id == processing_id
    
    @pytest.mark.asyncio
    async def test_should_trigger_webhook_successfully_with_mock_n8n(self):
        """GREEN: Test para disparar webhook exitosamente con n8n mock"""
        # Given
        webhook_trigger = create_webhook_trigger(environment="development")
        
        # Mock successful n8n response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "workflow_id": "workflow-123",
            "execution_id": "exec-456"
        }
        mock_response.text = '{"success": true}'
        mock_response.content = b'{"success": true}'
        
        # Patch HTTP client
        with patch.object(webhook_trigger.http_client, 'post', return_value=mock_response) as mock_post:
            
            # Create test payload
            payload = WebhookPayload(
                user_id="user-123",
                meeting_id="meeting-456", 
                meeting_url="https://meet.google.com/test",
                transcription_text="Test transcription",
                language="es"
            )
            
            # Configure webhook URL
            webhook_trigger.configure_webhook_url("https://test-n8n.com/webhook/process-meeting")
            
            # When
            response = await webhook_trigger.trigger_workflow(payload)
            
            # Then
            assert response.status == WebhookStatus.SENT
            assert response.is_successful()
            assert response.http_status_code == 200
            assert response.response_data["success"] is True
            
            # Verify HTTP call was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["user_id"] == "user-123"
            assert call_args[1]["json"]["transcription_text"] == "Test transcription"
    
    @pytest.mark.asyncio
    async def test_should_handle_webhook_failure_with_retries(self):
        """GREEN: Test para manejo de fallos de webhook con reintentos"""
        # Given
        webhook_trigger = create_webhook_trigger(environment="development")
        
        # Mock failed n8n response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 503  # Service Unavailable
        mock_response.json.return_value = {"error": "Service temporarily unavailable"}
        mock_response.text = 'Service temporarily unavailable'
        mock_response.content = b'Service temporarily unavailable'
        
        with patch.object(webhook_trigger.http_client, 'post', return_value=mock_response) as mock_post:
            
            payload = WebhookPayload(
                user_id="user-123",
                meeting_id="meeting-456",
                meeting_url="https://meet.google.com/test",
                transcription_text="Test transcription"
            )
            
            webhook_trigger.configure_webhook_url("https://test-n8n.com/webhook/process-meeting")
            
            # When
            response = await webhook_trigger.trigger_workflow(payload)
            
            # Then
            assert response.status == WebhookStatus.FAILED
            assert not response.is_successful()
            assert response.http_status_code == 503
            assert "Service temporarily unavailable" in response.error_message
            
            # Verify retries (development environment = 2 retries)
            assert mock_post.call_count == 2
    
    def test_webhook_payload_to_dict_contains_all_required_fields(self):
        """GREEN: Test para verificar que el payload contiene todos los campos necesarios para n8n"""
        # Given
        payload = WebhookPayload(
            user_id="user-123",
            meeting_id="meeting-456",
            meeting_url="https://meet.google.com/test-meeting",
            transcription_text="Test transcription content",
            language="es",
            estimated_duration_minutes=75,
            remaining_hours=8.5,
            plan_name="Pro Plan",
            consumption_percentage=15.0,
            consumption_callback_url="/api/v1/consumption/process/update",
            status_callback_url="/api/v1/workflow/status"
        )
        
        # When
        payload_dict = payload.to_dict()
        
        # Then - Verificar estructura para n8n
        assert "user_id" in payload_dict
        assert "meeting_id" in payload_dict
        assert "transcription_text" in payload_dict
        assert "callbacks" in payload_dict
        assert "services" in payload_dict
        
        # Verificar callbacks para n8n
        callbacks = payload_dict["callbacks"]
        assert "consumption_update" in callbacks
        assert "status_update" in callbacks
        
        # Verificar URLs de servicios para n8n
        services = payload_dict["services"]
        assert "nlp_service_url" in services
        assert "gatekeeper_service_url" in services
        
        # Verificar timestamp
        assert "triggered_at" in payload_dict
        assert isinstance(payload_dict["triggered_at"], str)  # ISO format
    
    @pytest.mark.asyncio 
    async def test_should_handle_no_webhook_url_configured(self):
        """GREEN: Test para manejo de webhook no configurado"""
        # Given
        webhook_trigger = WebhookTrigger()  # Sin URL configurada
        
        payload = WebhookPayload(
            user_id="user-123",
            meeting_id="meeting-456",
            meeting_url="https://meet.google.com/test",
            transcription_text="Test transcription"
        )
        
        # When
        response = await webhook_trigger.trigger_workflow(payload)
        
        # Then
        assert response.status == WebhookStatus.FAILED
        assert not response.is_successful()
        assert "No webhook URL configured" in response.error_message
    
    def test_create_webhook_trigger_factory_with_different_environments(self):
        """GREEN: Test para factory con diferentes entornos"""
        # Test development environment
        dev_trigger = create_webhook_trigger(environment="development")
        assert dev_trigger.timeout_seconds == 30
        assert dev_trigger.max_retries == 2
        assert dev_trigger.retry_delay_seconds == 1.0
        
        # Test production environment  
        prod_trigger = create_webhook_trigger(environment="production")
        assert prod_trigger.timeout_seconds == 60
        assert prod_trigger.max_retries == 5
        assert prod_trigger.retry_delay_seconds == 3.0
        
        # Test unknown environment (defaults to development)
        unknown_trigger = create_webhook_trigger(environment="unknown")
        assert unknown_trigger.timeout_seconds == 30
        assert unknown_trigger.max_retries == 2
    
    @pytest.mark.asyncio
    async def test_integration_complete_gatekeeper_to_webhook_flow(self):
        """REFACTOR: Test de integración completa del flujo Gatekeeper → Webhook"""
        # Given - Datos completos como en el endpoint real
        request_data = {
            "user_id": "user-123",
            "meeting_url": "https://meet.google.com/complete-test",
            "estimated_duration_minutes": 90,
            "meeting_id": "meeting-integration-test",
            "transcription_text": "María: Implementar sistema de reportes con dashboard React y API REST...",
            "language": "es"
        }
        
        authorization_data = {
            "authorized": True,
            "user_id": "user-123", 
            "remaining_hours": 12.5,
            "consumption_percentage": 25.0,
            "plan_name": "Enterprise Plan",
            "message": "Processing authorized"
        }
        
        # Mock n8n response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "workflow_id": "n8n-workflow-789",
            "message": "Meeting processing workflow started"
        }
        mock_response.text = '{"success": true}'
        mock_response.content = b'{"success": true}'
        
        # Create webhook trigger
        webhook_trigger = create_webhook_trigger(environment="development")
        webhook_trigger.configure_webhook_url("https://test-n8n.com/webhook/complete-flow")
        
        with patch.object(webhook_trigger.http_client, 'post', return_value=mock_response) as mock_post:
            
            # Create models as in endpoint
            request = ProcessStartRequest(**request_data)
            authorization_response = ConsumptionVerificationResponse(**authorization_data)
            
            # Create payload as in endpoint
            processing_id = f"proc-{request.meeting_id}-{int(datetime.utcnow().timestamp())}"
            callback_url = "/api/v1/consumption/process/update"
            
            from backend.app.services.webhook_trigger import create_webhook_payload_from_gatekeeper_data
            webhook_payload = create_webhook_payload_from_gatekeeper_data(
                request=request,
                authorization_response=authorization_response,
                processing_id=processing_id,
                callback_url=callback_url
            )
            
            # When - Trigger workflow as in endpoint
            webhook_response = await webhook_trigger.trigger_workflow(webhook_payload)
            
            # Then - Verify complete integration
            assert webhook_response.status == WebhookStatus.SENT
            assert webhook_response.is_successful()
            
            # Verify n8n received correct data structure
            mock_post.assert_called_once()
            sent_data = mock_post.call_args[1]["json"]
            
            # Verify all critical data was sent to n8n
            assert sent_data["user_id"] == "user-123"
            assert sent_data["meeting_id"] == "meeting-integration-test"
            assert "dashboard React y API REST" in sent_data["transcription_text"]
            assert sent_data["language"] == "es"
            assert sent_data["remaining_hours"] == 12.5
            assert sent_data["consumption_percentage"] == 25.0
            
            # Verify callbacks for n8n are properly set
            assert sent_data["callbacks"]["consumption_update"] == callback_url
            assert "status_update" in sent_data["callbacks"]
            
            # Verify service URLs for n8n
            assert "nlp_service_url" in sent_data["services"]
            assert "gatekeeper_service_url" in sent_data["services"]


class TestWebhookTriggerCircuitBreaker:
    """✅ Tests específicos para tolerancia a fallos (RNF5.0)"""
    
    @pytest.mark.asyncio
    async def test_should_implement_exponential_backoff_on_retries(self):
        """GREEN: Test para verificar backoff exponencial en reintentos"""
        # Given
        webhook_trigger = create_webhook_trigger(environment="development")
        
        # Mock que falla siempre
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.content = b"Internal Server Error"
        
        # Mock sleep para verificar backoff
        with patch('asyncio.sleep') as mock_sleep, \
             patch.object(webhook_trigger.http_client, 'post', return_value=mock_response):
            
            payload = WebhookPayload(
                user_id="user-123",
                meeting_id="meeting-456",
                meeting_url="https://meet.google.com/test",
                transcription_text="Test transcription"
            )
            
            webhook_trigger.configure_webhook_url("https://test-n8n.com/webhook/backoff-test")
            
            # When
            await webhook_trigger.trigger_workflow(payload)
            
            # Then - Verify exponential backoff
            # Development environment: max_retries = 2, retry_delay = 1.0
            # Expected delays: 1.0 * 1 = 1.0 second
            mock_sleep.assert_called_once_with(1.0)
    
    @pytest.mark.asyncio
    async def test_should_timeout_after_configured_seconds(self):
        """GREEN: Test para verificar timeout configurado"""
        # Given
        webhook_trigger = create_webhook_trigger(environment="development")
        
        # Simulate timeout exception
        from httpx import TimeoutException
        with patch.object(webhook_trigger.http_client, 'post', side_effect=TimeoutException("Timeout")):
            
            payload = WebhookPayload(
                user_id="user-123",
                meeting_id="meeting-456",
                meeting_url="https://meet.google.com/test",
                transcription_text="Test transcription"
            )
            
            webhook_trigger.configure_webhook_url("https://test-n8n.com/webhook/timeout-test")
            
            # When
            response = await webhook_trigger.trigger_workflow(payload)
            
            # Then
            assert response.status == WebhookStatus.TIMEOUT
            assert "timeout" in response.error_message.lower()
            assert response.response_time_ms > 0


# ================================================================================================
# 🎯 FIXTURES Y HELPERS PARA TESTS
# ================================================================================================

@pytest.fixture
def sample_gatekeeper_request():
    """Fixture con request típico del gatekeeper"""
    return ProcessStartRequest(
        user_id="test-user-123",
        meeting_url="https://meet.google.com/test-fixture", 
        estimated_duration_minutes=60,
        meeting_id="test-meeting-456",
        transcription_text="Test: Esta es una transcripción de prueba para el fixture...",
        language="es"
    )

@pytest.fixture
def sample_authorization_response():
    """Fixture con respuesta típica de autorización"""
    return ConsumptionVerificationResponse(
        authorized=True,
        user_id="test-user-123",
        remaining_hours=10.0,
        consumption_percentage=20.0,
        plan_name="Test Plan",
        message="Test authorization"
    )

@pytest.fixture
def mock_successful_n8n_response():
    """Fixture con respuesta exitosa de n8n"""
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "workflow_id": "test-workflow-123",
        "execution_started": True
    }
    mock_response.text = '{"success": true}'
    mock_response.content = b'{"success": true}'
    return mock_response
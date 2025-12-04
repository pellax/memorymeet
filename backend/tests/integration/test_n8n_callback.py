# ================================================================================================
# 🧪 TDD TESTS - n8n Callback Endpoint Integration
# ================================================================================================
# Tests para el endpoint de callback que n8n llama después del procesamiento

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import status
from datetime import datetime

from backend.app.api.v1.consumption_router import N8NCallbackRequest, N8NCallbackResponse
from backend.app.domain.exceptions.consumption_exceptions import (
    UserNotFoundException,
    SubscriptionNotFoundException,
    DatabaseTransactionException
)


# ================================================================================================
# 🔴 RED PHASE - Tests que definen el comportamiento del callback
# ================================================================================================

@pytest.mark.asyncio
class TestN8NCallbackEndpoint:
    """✅ TDD RED - Tests para el endpoint de callback de n8n."""
    
    async def test_should_update_consumption_on_successful_processing_callback(self):
        """
        🔴 RED: El callback debe actualizar el consumo cuando n8n notifica éxito.
        
        Escenario:
        - n8n completó el procesamiento exitosamente
        - El callback recibe datos completos (PRD generado, tareas creadas)
        - El sistema debe actualizar el consumo del usuario
        """
        # Given - Callback exitoso de n8n
        callback_request = N8NCallbackRequest(
            user_id="user-123",
            meeting_id="meeting-456",
            processing_id="proc-meeting-456-1234567890",
            actual_duration_minutes=75,
            prd_generated=True,
            tasks_created=12,
            requirements_extracted=8,
            workflow_execution_id="n8n-exec-789",
            processing_status="completed"
        )
        
        # Mock del servicio de consumo
        mock_service = AsyncMock()
        mock_update_result = Mock()
        mock_update_result.remaining_hours = 7.75
        mock_update_result.consumption_percentage = 22.5
        mock_service.actualizar_registro_consumo.return_value = mock_update_result
        
        # When - Procesar callback
        from backend.app.api.v1.consumption_router import n8n_processing_callback
        
        response = await n8n_processing_callback(
            callback_data=callback_request,
            consumption_service=mock_service
        )
        
        # Then - Verificar actualización exitosa
        assert response.success is True
        assert response.consumption_updated is True
        assert response.processing_id == "proc-meeting-456-1234567890"
        assert response.remaining_hours == 7.75
        assert response.consumption_percentage == 22.5
        
        # Verificar que se llamó al servicio con los datos correctos
        mock_service.actualizar_registro_consumo.assert_called_once_with(
            user_id="user-123",
            duration_minutes=75,
            meeting_id="meeting-456"
        )
    
    
    async def test_should_acknowledge_failed_processing_without_updating_consumption(self):
        """
        🔴 RED: El callback debe reconocer fallos sin actualizar consumo.
        
        Escenario:
        - n8n falló durante el procesamiento (error en IA/NLP)
        - El callback recibe notificación de fallo
        - El sistema NO debe actualizar consumo pero sí confirmar recepción
        """
        # Given - Callback de fallo de n8n
        callback_request = N8NCallbackRequest(
            user_id="user-123",
            meeting_id="meeting-456",
            processing_id="proc-meeting-456-1234567890",
            actual_duration_minutes=75,
            prd_generated=False,
            tasks_created=0,
            requirements_extracted=0,
            workflow_execution_id="n8n-exec-789",
            processing_status="failed",
            error_message="IA/NLP service timeout"
        )
        
        # Mock del servicio (no debería ser llamado)
        mock_service = AsyncMock()
        
        # When - Procesar callback de fallo
        from backend.app.api.v1.consumption_router import n8n_processing_callback
        
        response = await n8n_processing_callback(
            callback_data=callback_request,
            consumption_service=mock_service
        )
        
        # Then - Verificar reconocimiento sin actualización
        assert response.success is True  # Callback recibido correctamente
        assert response.consumption_updated is False  # NO se actualizó consumo
        assert response.processing_id == "proc-meeting-456-1234567890"
        assert "failure acknowledged" in response.message.lower()
        
        # Verificar que NO se llamó al servicio de actualización
        mock_service.actualizar_registro_consumo.assert_not_called()
    
    
    async def test_should_handle_user_not_found_error_during_callback(self):
        """
        🔴 RED: El callback debe manejar error de usuario no encontrado.
        
        Escenario:
        - n8n envía callback exitoso
        - El usuario fue eliminado durante el procesamiento
        - Debe retornar 404 Not Found
        """
        # Given - Callback válido pero usuario inexistente
        callback_request = N8NCallbackRequest(
            user_id="user-nonexistent",
            meeting_id="meeting-456",
            processing_id="proc-meeting-456-1234567890",
            actual_duration_minutes=75,
            prd_generated=True,
            tasks_created=12,
            requirements_extracted=8,
            processing_status="completed"
        )
        
        # Mock del servicio que lanza excepción
        mock_service = AsyncMock()
        mock_service.actualizar_registro_consumo.side_effect = UserNotFoundException(
            user_id="user-nonexistent",
            message="User not found"
        )
        
        # When & Then - Verificar excepción HTTP
        from backend.app.api.v1.consumption_router import n8n_processing_callback
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await n8n_processing_callback(
                callback_data=callback_request,
                consumption_service=mock_service
            )
        
        # Verificar error 404
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "USER_NOT_FOUND" in str(exc_info.value.detail)
    
    
    async def test_should_handle_database_transaction_error_during_callback(self):
        """
        🔴 RED: El callback debe manejar errores de transacción.
        
        Escenario:
        - n8n envía callback exitoso
        - La transacción de actualización de consumo falla (DB error)
        - Debe retornar 500 Internal Server Error
        """
        # Given - Callback válido pero error de DB
        callback_request = N8NCallbackRequest(
            user_id="user-123",
            meeting_id="meeting-456",
            processing_id="proc-meeting-456-1234567890",
            actual_duration_minutes=75,
            prd_generated=True,
            tasks_created=12,
            requirements_extracted=8,
            processing_status="completed"
        )
        
        # Mock del servicio que lanza excepción de transacción
        mock_service = AsyncMock()
        mock_service.actualizar_registro_consumo.side_effect = DatabaseTransactionException(
            user_id="user-123",
            transaction_id="txn-789",
            message="Database connection lost"
        )
        
        # When & Then - Verificar excepción HTTP
        from backend.app.api.v1.consumption_router import n8n_processing_callback
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await n8n_processing_callback(
                callback_data=callback_request,
                consumption_service=mock_service
            )
        
        # Verificar error 500
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "CONSUMPTION_UPDATE_FAILED" in str(exc_info.value.detail)
    
    
    async def test_should_include_processing_metadata_in_callback_response(self):
        """
        🔴 RED: El callback debe incluir metadatos del procesamiento en la respuesta.
        
        Escenario:
        - n8n envía callback exitoso con metadatos completos
        - La respuesta debe incluir información del procesamiento para tracking
        """
        # Given - Callback con metadatos completos
        callback_request = N8NCallbackRequest(
            user_id="user-123",
            meeting_id="meeting-456",
            processing_id="proc-meeting-456-1234567890",
            actual_duration_minutes=75,
            prd_generated=True,
            tasks_created=12,
            requirements_extracted=8,
            workflow_execution_id="n8n-exec-789",
            processing_status="completed"
        )
        
        # Mock del servicio
        mock_service = AsyncMock()
        mock_update_result = Mock()
        mock_update_result.remaining_hours = 7.75
        mock_update_result.consumption_percentage = 22.5
        mock_service.actualizar_registro_consumo.return_value = mock_update_result
        
        # When - Procesar callback
        from backend.app.api.v1.consumption_router import n8n_processing_callback
        
        response = await n8n_processing_callback(
            callback_data=callback_request,
            consumption_service=mock_service
        )
        
        # Then - Verificar metadatos en respuesta
        assert response.processing_id == "proc-meeting-456-1234567890"
        assert response.success is True
        assert response.consumption_updated is True
        assert "completed successfully" in response.message.lower()


# ================================================================================================
# 🧪 Integration Tests con FastAPI TestClient
# ================================================================================================

@pytest.mark.asyncio
class TestN8NCallbackEndpointIntegration:
    """✅ Integration Tests - Callback endpoint completo con FastAPI."""
    
    @pytest.fixture
    def test_client(self):
        """Fixture para FastAPI test client."""
        from fastapi.testclient import TestClient
        from backend.app.main import app  # Assuming main FastAPI app
        
        return TestClient(app)
    
    
    async def test_full_callback_flow_with_http_request(self, test_client):
        """
        🔴 RED: Test de flujo completo con request HTTP.
        
        Escenario:
        - n8n envía POST al endpoint /api/v1/consumption/process/callback
        - El endpoint procesa el callback y retorna respuesta JSON
        """
        # Given - Payload de callback de n8n
        callback_payload = {
            "user_id": "user-123",
            "meeting_id": "meeting-456",
            "processing_id": "proc-meeting-456-1234567890",
            "actual_duration_minutes": 75,
            "prd_generated": True,
            "tasks_created": 12,
            "requirements_extracted": 8,
            "workflow_execution_id": "n8n-exec-789",
            "processing_status": "completed"
        }
        
        # When - Enviar POST al endpoint
        with patch('backend.app.api.v1.consumption_router.get_consumption_service') as mock_get_service:
            # Mock del servicio
            mock_service = AsyncMock()
            mock_update_result = Mock()
            mock_update_result.remaining_hours = 7.75
            mock_update_result.consumption_percentage = 22.5
            mock_service.actualizar_registro_consumo.return_value = mock_update_result
            mock_get_service.return_value = mock_service
            
            response = test_client.post(
                "/api/v1/consumption/process/callback",
                json=callback_payload
            )
        
        # Then - Verificar respuesta HTTP
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["consumption_updated"] is True
        assert response_data["processing_id"] == "proc-meeting-456-1234567890"
        assert response_data["remaining_hours"] == 7.75
    
    
    async def test_callback_endpoint_rejects_invalid_payload(self, test_client):
        """
        🔴 RED: El endpoint debe rechazar payloads inválidos.
        
        Escenario:
        - n8n envía payload incompleto o con datos inválidos
        - El endpoint debe retornar 422 Validation Error
        """
        # Given - Payload inválido (falta user_id)
        invalid_payload = {
            "meeting_id": "meeting-456",
            "processing_id": "proc-meeting-456-1234567890",
            # user_id falta
            "actual_duration_minutes": 75,
            "prd_generated": True
        }
        
        # When - Enviar POST con payload inválido
        response = test_client.post(
            "/api/v1/consumption/process/callback",
            json=invalid_payload
        )
        
        # Then - Verificar error de validación
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ================================================================================================
# 🟢 GREEN PHASE - Implementation notes
# ================================================================================================
"""
✅ GREEN PHASE - Implementación mínima para pasar los tests:

1. ✅ Endpoint /process/callback creado en consumption_router.py
2. ✅ Modelos N8NCallbackRequest y N8NCallbackResponse definidos
3. ✅ Lógica de procesamiento implementada:
   - Verificar status de procesamiento
   - Actualizar consumo si exitoso
   - Manejar errores de usuario/suscripción/transacción
   - Logging estructurado para observabilidad
4. ✅ Manejo de excepciones con HTTPException
5. ✅ Validación de payload con Pydantic

🔵 REFACTOR PHASE - Próximas mejoras:
- Añadir autenticación/autorización para el endpoint (API Key de n8n)
- Implementar validación de IP origen (whitelist)
- Añadir firma HMAC del payload para seguridad
- Metricas de procesamiento (Prometheus)
- Circuit breaker para llamadas a servicios externos
"""

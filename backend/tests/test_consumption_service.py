import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.domain.services.subscription_consumption_service import SubscriptionConsumptionService
from app.domain.value_objects.consumption_response import ConsumptionUpdateResult
from app.domain.exceptions.consumption_exceptions import (
    InsufficientHoursException,
    UserNotFoundException,
    DatabaseTransactionException
)


class TestConsumptionServiceActualizarConsumo:
    """✅ TDD FASE 1 - Tests para actualizar_registro_consumo (RF8.0 Post-Proceso)"""

    @pytest.fixture
    def mock_subscription_repository(self):
        """Mock del repositorio de suscripciones"""
        mock = Mock()
        # Mock para subscription activa
        mock_subscription = Mock()
        mock_subscription.available_hours = 10.0
        mock_subscription.consume_hours.return_value = mock_subscription
        mock.get_active_subscription_by_user_id.return_value = mock_subscription
        return mock
    
    @pytest.fixture
    def mock_user_repository(self):
        """Mock del repositorio de usuarios"""
        mock = Mock()
        mock_user = Mock()
        mock.get_user_by_id.return_value = mock_user
        return mock

    @pytest.fixture
    def consumption_service(self, mock_subscription_repository, mock_user_repository):
        """Servicio de consumo con repositorios mockeados"""
        return SubscriptionConsumptionService(
            subscription_repository=mock_subscription_repository,
            user_repository=mock_user_repository
        )

    @pytest.mark.asyncio
    async def test_should_update_consumption_successfully_when_valid_data(
        self, consumption_service, mock_subscription_repository
    ):
        """🔴 RED: Test que define comportamiento exitoso de actualización"""
        # Given
        user_id = "user-123"
        duration_minutes = 90  # 1.5 horas
        meeting_id = "meeting-456"
        
        # Mock successful transaction
        mock_subscription_repository.begin_transaction.return_value = None
        mock_subscription_repository.commit_transaction.return_value = None
        mock_subscription_repository.update_subscription_with_audit.return_value = None
        
        # When
        result = await consumption_service.actualizar_registro_consumo(
            user_id=user_id,
            duration_minutes=duration_minutes,
            meeting_id=meeting_id
        )
        
        # Then
        assert result.success is True
        assert result.hours_consumed == 1.5
        assert result.remaining_hours == 10.0  # Mock subscription hours
        
        # Verificar llamadas al repositorio
        mock_subscription_repository.begin_transaction.assert_called_once()
        mock_subscription_repository.update_subscription_with_audit.assert_called_once()
        mock_subscription_repository.commit_transaction.assert_called_once()

    def test_should_create_usage_log_entry_during_update(
        self, consumption_service, mock_repository
    ):
        """🔴 RED: Test para verificar creación de log de auditoría"""
        # Given
        user_id = "user-789"
        duration_minutes = 60  # 1 hora exacta
        meeting_id = "meeting-audit-test"
        
        mock_repository.execute_consumption_update_transaction.return_value = True
        
        # When
        consumption_service.actualizar_registro_consumo(
            user_id=user_id,
            duration_minutes=duration_minutes,
            meeting_id=meeting_id
        )
        
        # Then - Verificar que se crea entrada de auditoría
        mock_repository.execute_consumption_update_transaction.assert_called_once()
        call_args = mock_repository.execute_consumption_update_transaction.call_args[1]
        
        # Verificar que los datos de auditoría están incluidos
        assert "audit_data" in call_args
        audit_data = call_args["audit_data"]
        assert audit_data["action"] == "consumption_update"
        assert audit_data["hours_consumed"] == 1.0
        assert audit_data["meeting_id"] == meeting_id

    def test_should_handle_zero_minutes_gracefully(
        self, consumption_service, mock_repository
    ):
        """🔴 RED: Test para manejo de casos edge - 0 minutos"""
        # Given
        user_id = "user-zero-test"
        duration_minutes = 0
        meeting_id = "meeting-zero"
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            consumption_service.actualizar_registro_consumo(
                user_id=user_id,
                duration_minutes=duration_minutes,
                meeting_id=meeting_id
            )
        
        assert "Duration must be greater than 0" in str(exc_info.value)

    def test_should_rollback_transaction_when_database_error_occurs(
        self, consumption_service, mock_repository
    ):
        """🔴 RED: Test para manejo de fallos transaccionales (ACID)"""
        # Given
        user_id = "user-db-error"
        duration_minutes = 30
        meeting_id = "meeting-db-fail"
        
        # Mock database failure
        mock_repository.execute_consumption_update_transaction.side_effect = \
            DatabaseTransactionException("Database constraint violation")
        
        # When & Then
        with pytest.raises(DatabaseTransactionException) as exc_info:
            consumption_service.actualizar_registro_consumo(
                user_id=user_id,
                duration_minutes=duration_minutes,
                meeting_id=meeting_id
            )
        
        assert "Database constraint violation" in str(exc_info.value)
        
        # Verificar que se intentó la transacción (para rollback automático)
        mock_repository.execute_consumption_update_transaction.assert_called_once()

    def test_should_handle_user_not_found_during_update(
        self, consumption_service, mock_repository
    ):
        """🔴 RED: Test para usuario inexistente en actualización"""
        # Given
        invalid_user_id = "nonexistent-user"
        duration_minutes = 45
        meeting_id = "meeting-no-user"
        
        # Mock user not found
        mock_repository.get_user_subscription.return_value = None
        
        # When & Then
        with pytest.raises(UserNotFoundException) as exc_info:
            consumption_service.actualizar_registro_consumo(
                user_id=invalid_user_id,
                duration_minutes=duration_minutes,
                meeting_id=meeting_id
            )
        
        assert f"User {invalid_user_id} not found" in str(exc_info.value)

    def test_should_validate_meeting_id_format(
        self, consumption_service, mock_repository
    ):
        """🔴 RED: Test para validación de formato de meeting_id"""
        # Given
        user_id = "user-validation-test"
        duration_minutes = 30
        invalid_meeting_id = ""  # ID vacío
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            consumption_service.actualizar_registro_consumo(
                user_id=user_id,
                duration_minutes=duration_minutes,
                meeting_id=invalid_meeting_id
            )
        
        assert "Meeting ID cannot be empty" in str(exc_info.value)

    def test_should_convert_minutes_to_hours_correctly(
        self, consumption_service, mock_repository
    ):
        """🔴 RED: Test para conversión correcta de minutos a horas"""
        # Given
        user_id = "user-conversion-test"
        duration_minutes = 135  # 2.25 horas
        meeting_id = "meeting-conversion"
        
        mock_repository.execute_consumption_update_transaction.return_value = True
        
        # When
        result = consumption_service.actualizar_registro_consumo(
            user_id=user_id,
            duration_minutes=duration_minutes,
            meeting_id=meeting_id
        )
        
        # Then
        assert result.hours_consumed == 2.25
        
        # Verificar conversión en llamada al repositorio
        call_args = mock_repository.execute_consumption_update_transaction.call_args[1]
        assert call_args["hours_consumed"] == 2.25

    @patch('backend.app.services.consumption_service.datetime')
    def test_should_include_timestamp_in_update_operation(
        self, mock_datetime, consumption_service, mock_repository
    ):
        """🔴 RED: Test para inclusión de timestamp en operación"""
        # Given
        fixed_time = datetime(2024, 1, 15, 10, 30, 0)
        mock_datetime.utcnow.return_value = fixed_time
        
        user_id = "user-timestamp-test"
        duration_minutes = 60
        meeting_id = "meeting-timestamp"
        
        mock_repository.execute_consumption_update_transaction.return_value = True
        
        # When
        consumption_service.actualizar_registro_consumo(
            user_id=user_id,
            duration_minutes=duration_minutes,
            meeting_id=meeting_id
        )
        
        # Then
        call_args = mock_repository.execute_consumption_update_transaction.call_args[1]
        assert call_args["timestamp"] == fixed_time

    def test_should_maintain_acid_properties_during_concurrent_updates(
        self, consumption_service, mock_repository
    ):
        """🔴 RED: Test para propiedades ACID en actualizaciones concurrentes"""
        # Given
        user_id = "user-concurrent-test"
        duration_minutes = 30
        meeting_id = "meeting-concurrent"
        
        # Mock successful atomic transaction
        mock_repository.execute_consumption_update_transaction.return_value = True
        
        # When
        result = consumption_service.actualizar_registro_consumo(
            user_id=user_id,
            duration_minutes=duration_minutes,
            meeting_id=meeting_id
        )
        
        # Then
        assert result.success is True
        
        # Verificar que se usa transacción (garantiza ACID)
        mock_repository.execute_consumption_update_transaction.assert_called_once()
        
        # Verificar que se incluye isolation level para concurrencia
        call_args = mock_repository.execute_consumption_update_transaction.call_args[1]
        assert "isolation_level" in call_args
        assert call_args["isolation_level"] == "READ_COMMITTED"
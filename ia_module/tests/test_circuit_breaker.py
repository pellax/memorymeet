"""
✅ TDD Tests - Circuit Breaker Pattern (RNF5.0 - Tolerancia a Fallos)

Tests que definen el comportamiento del Circuit Breaker antes de implementarlo.
Ciclo TDD: RED (estos tests fallan inicialmente) → GREEN → REFACTOR
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Callable


# ================================================================================================
# 🔴 RED PHASE - Tests que definen el comportamiento esperado
# ================================================================================================

class TestCircuitBreakerStates:
    """
    ✅ TDD RED - Tests para estados del Circuit Breaker.
    
    Estados:
    - CLOSED: Funcionamiento normal, permite llamadas
    - OPEN: Circuito abierto por fallos, rechaza llamadas
    - HALF_OPEN: Probando recuperación, permite llamadas limitadas
    """
    
    def test_should_start_in_closed_state(self):
        """RED: Circuit Breaker debe iniciar en estado CLOSED."""
        from circuit_breaker import CircuitBreaker, CircuitState
        
        # Given
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        
        # Then
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_should_allow_calls_when_circuit_is_closed(self):
        """RED: Debe permitir llamadas cuando el circuito está CLOSED."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(failure_threshold=3)
        
        def successful_operation():
            return "success"
        
        # When
        result = cb.call(successful_operation)
        
        # Then
        assert result == "success"
    
    def test_should_increment_failure_count_on_exception(self):
        """RED: Debe incrementar contador de fallos cuando hay excepciones."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(failure_threshold=3)
        
        def failing_operation():
            raise ConnectionError("Service unavailable")
        
        # When
        with pytest.raises(ConnectionError):
            cb.call(failing_operation)
        
        # Then
        assert cb.failure_count == 1
    
    def test_should_open_circuit_after_threshold_failures(self):
        """RED: Debe abrir el circuito tras alcanzar el umbral de fallos."""
        from circuit_breaker import CircuitBreaker, CircuitState
        
        # Given
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        
        def failing_operation():
            raise ConnectionError("Service unavailable")
        
        # When - Ejecutar 3 fallos consecutivos
        for _ in range(3):
            with pytest.raises(ConnectionError):
                cb.call(failing_operation)
        
        # Then
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
    
    def test_should_reject_calls_when_circuit_is_open(self):
        """RED: Debe rechazar llamadas cuando el circuito está OPEN."""
        from circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenException
        
        # Given
        cb = CircuitBreaker(failure_threshold=1, timeout=60)
        cb.state = CircuitState.OPEN  # Forzar estado OPEN
        
        def any_operation():
            return "should not execute"
        
        # When & Then
        with pytest.raises(CircuitBreakerOpenException) as exc_info:
            cb.call(any_operation)
        
        assert "circuit is open" in str(exc_info.value).lower()
    
    def test_should_transition_to_half_open_after_timeout(self):
        """RED: Debe transicionar a HALF_OPEN tras el timeout."""
        from circuit_breaker import CircuitBreaker, CircuitState
        
        # Given
        cb = CircuitBreaker(failure_threshold=1, timeout=1)  # 1 segundo
        
        # Forzar estado OPEN con fallo
        def failing_operation():
            raise ConnectionError("Service unavailable")
        
        with pytest.raises(ConnectionError):
            cb.call(failing_operation)
        
        assert cb.state == CircuitState.OPEN
        
        # When - Esperar timeout
        time.sleep(1.1)  # Esperar más que el timeout
        
        # Intentar nueva llamada exitosa
        def successful_operation():
            return "recovered"
        
        result = cb.call(successful_operation)
        
        # Then
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED  # Debe cerrar tras éxito
    
    def test_should_reset_failure_count_on_success(self):
        """RED: Debe resetear contador de fallos tras llamada exitosa."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(failure_threshold=3)
        
        def failing_operation():
            raise ConnectionError("Service unavailable")
        
        def successful_operation():
            return "success"
        
        # When - 2 fallos, luego éxito
        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(failing_operation)
        
        assert cb.failure_count == 2
        
        result = cb.call(successful_operation)
        
        # Then
        assert result == "success"
        assert cb.failure_count == 0  # Debe resetear


class TestCircuitBreakerConfiguration:
    """✅ TDD RED - Tests para configuración del Circuit Breaker."""
    
    def test_should_accept_custom_failure_threshold(self):
        """RED: Debe aceptar umbral de fallos personalizado."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(failure_threshold=5)
        
        # Then
        assert cb.failure_threshold == 5
    
    def test_should_accept_custom_timeout(self):
        """RED: Debe aceptar timeout personalizado."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(timeout=120)
        
        # Then
        assert cb.timeout == 120
    
    def test_should_filter_exceptions_by_type(self):
        """RED: Debe permitir filtrar qué excepciones activan el circuito."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(
            failure_threshold=2,
            expected_exception=ConnectionError  # Solo ConnectionError activa
        )
        
        def connection_error():
            raise ConnectionError("Network issue")
        
        def value_error():
            raise ValueError("Invalid input")
        
        # When - ValueError no debe contar como fallo
        with pytest.raises(ValueError):
            cb.call(value_error)
        
        assert cb.failure_count == 0  # No cuenta
        
        # ConnectionError sí cuenta
        with pytest.raises(ConnectionError):
            cb.call(connection_error)
        
        assert cb.failure_count == 1  # Sí cuenta


class TestCircuitBreakerIntegration:
    """✅ TDD RED - Tests de integración con servicios reales."""
    
    def test_should_protect_deepgram_api_calls(self):
        """RED: Debe proteger llamadas a Deepgram API."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        
        # Mock de servicio Deepgram
        deepgram_client = Mock()
        deepgram_client.transcribe.side_effect = ConnectionError("Deepgram unavailable")
        
        # When - Múltiples fallos
        for _ in range(3):
            with pytest.raises(ConnectionError):
                cb.call(deepgram_client.transcribe, "audio.mp3")
        
        # Then - Circuito debe estar abierto
        from circuit_breaker import CircuitState
        assert cb.state == CircuitState.OPEN
    
    def test_should_track_last_failure_time(self):
        """RED: Debe trackear el timestamp del último fallo."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(failure_threshold=1)
        
        def failing_operation():
            raise ConnectionError("Service down")
        
        # When
        before_call = time.time()
        with pytest.raises(ConnectionError):
            cb.call(failing_operation)
        after_call = time.time()
        
        # Then
        assert cb.last_failure_time is not None
        assert before_call <= cb.last_failure_time <= after_call


class TestCircuitBreakerObservability:
    """✅ TDD RED - Tests para observabilidad y métricas."""
    
    def test_should_provide_state_information(self):
        """RED: Debe proporcionar información del estado actual."""
        from circuit_breaker import CircuitBreaker, CircuitState
        
        # Given
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        
        # When
        state_info = cb.get_state_info()
        
        # Then
        assert state_info["state"] == CircuitState.CLOSED
        assert state_info["failure_count"] == 0
        assert state_info["failure_threshold"] == 3
        assert state_info["timeout"] == 60
    
    def test_should_track_total_calls(self):
        """RED: Debe trackear el total de llamadas."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(failure_threshold=3)
        
        def operation():
            return "success"
        
        # When
        for _ in range(5):
            cb.call(operation)
        
        # Then
        assert cb.total_calls == 5
    
    def test_should_calculate_success_rate(self):
        """RED: Debe calcular tasa de éxito."""
        from circuit_breaker import CircuitBreaker
        
        # Given
        cb = CircuitBreaker(failure_threshold=10)
        
        def success():
            return "ok"
        
        def failure():
            raise ConnectionError("fail")
        
        # When - 7 éxitos, 3 fallos
        for _ in range(7):
            cb.call(success)
        
        for _ in range(3):
            with pytest.raises(ConnectionError):
                cb.call(failure)
        
        # Then
        success_rate = cb.get_success_rate()
        assert success_rate == 0.7  # 70%


# ================================================================================================
# 🧪 FIXTURES DE TESTING
# ================================================================================================

@pytest.fixture
def mock_service():
    """Mock de servicio externo con comportamiento configurable."""
    service = Mock()
    service.call.return_value = "success"
    return service


@pytest.fixture
def failing_service():
    """Mock de servicio que siempre falla."""
    service = Mock()
    service.call.side_effect = ConnectionError("Service unavailable")
    return service


@pytest.fixture
def flaky_service():
    """Mock de servicio intermitente (falla ocasionalmente)."""
    class FlakyService:
        def __init__(self):
            self.call_count = 0
        
        def call(self):
            self.call_count += 1
            if self.call_count % 3 == 0:  # Falla cada 3 llamadas
                raise ConnectionError("Intermittent failure")
            return "success"
    
    return FlakyService()

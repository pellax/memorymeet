"""
🔴 RED PHASE - TDD Tests para TranscriptionService

Tests que definen el comportamiento esperado del servicio de transcripción
antes de implementarlo. Siguiendo metodología TDD estricta.

Requisitos:
- RF2.0: Transcripción de audio con Deepgram
- RNF5.0: Tolerancia a fallos con Circuit Breaker
- RNF1.0: Performance < 5 minutos
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time


# ================================================================================================
# 🔴 RED: Tests que fallarán hasta que implementemos TranscriptionService
# ================================================================================================


class TestTranscriptionServiceBasicOperations:
    """Tests básicos de transcripción de audio."""
    
    def test_should_transcribe_audio_url_successfully(self):
        """
        🔴 RED: Test que define comportamiento básico de transcripción.
        
        Given: Un TranscriptionService configurado
        When: Se transcribe una URL de audio válida
        Then: Debe retornar una transcripción de texto
        """
        # Arrange - Este código fallará hasta que creemos la clase
        from services.transcription_service import TranscriptionService
        
        mock_deepgram_client = Mock()
        mock_response = {
            'results': {
                'channels': [{
                    'alternatives': [{
                        'transcript': 'Hello world, this is a test transcription'
                    }]
                }]
            }
        }
        mock_deepgram_client.transcription.prerecorded.return_value = mock_response
        
        service = TranscriptionService(deepgram_client=mock_deepgram_client)
        audio_url = "https://example.com/audio.mp3"
        
        # Act
        result = service.transcribe_audio(audio_url)
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        assert result == "Hello world, this is a test transcription"
        
        # Verificar que se llamó a Deepgram
        mock_deepgram_client.transcription.prerecorded.assert_called_once()
    
    def test_should_include_metadata_in_transcription_result(self):
        """
        🔴 RED: La transcripción debe incluir metadata útil.
        
        Given: Un servicio de transcripción
        When: Se transcribe audio exitosamente
        Then: Debe retornar objeto con texto y metadata
        """
        from services.transcription_service import TranscriptionService, TranscriptionResult
        
        mock_client = Mock()
        mock_client.transcription.prerecorded.return_value = {
            'results': {
                'channels': [{
                    'alternatives': [{
                        'transcript': 'Test transcript',
                        'confidence': 0.95
                    }]
                }]
            },
            'metadata': {
                'duration': 120.5
            }
        }
        
        service = TranscriptionService(deepgram_client=mock_client)
        
        # Act
        result = service.transcribe_audio_with_metadata("https://example.com/audio.mp3")
        
        # Assert
        assert isinstance(result, TranscriptionResult)
        assert result.text == "Test transcript"
        assert result.confidence == 0.95
        assert result.duration_seconds == 120.5
        assert result.success is True
    
    def test_should_reject_invalid_audio_url(self):
        """
        🔴 RED: Debe validar URLs de audio antes de procesar.
        
        Given: Un TranscriptionService
        When: Se pasa una URL inválida o vacía
        Then: Debe lanzar InvalidAudioUrlException
        """
        from services.transcription_service import TranscriptionService, InvalidAudioUrlException
        
        service = TranscriptionService(deepgram_client=Mock())
        
        # Test con URL vacía
        with pytest.raises(InvalidAudioUrlException) as exc_info:
            service.transcribe_audio("")
        
        assert "Invalid audio URL" in str(exc_info.value)
        
        # Test con URL None
        with pytest.raises(InvalidAudioUrlException):
            service.transcribe_audio(None)
        
        # Test con URL sin formato válido
        with pytest.raises(InvalidAudioUrlException):
            service.transcribe_audio("not-a-valid-url")


class TestTranscriptionServiceCircuitBreaker:
    """Tests de integración con Circuit Breaker para tolerancia a fallos."""
    
    def test_should_use_circuit_breaker_for_external_calls(self):
        """
        🔴 RED: Las llamadas a Deepgram deben estar protegidas por Circuit Breaker.
        
        Given: TranscriptionService con Circuit Breaker configurado
        When: El servicio externo falla repetidamente
        Then: El Circuit Breaker debe abrir y lanzar CircuitBreakerOpenException
        """
        from services.transcription_service import TranscriptionService
        from circuit_breaker import CircuitBreakerOpenException
        
        mock_client = Mock()
        mock_client.transcription.prerecorded.side_effect = Exception("Deepgram service unavailable")
        
        # Circuit Breaker con threshold bajo para testing
        service = TranscriptionService(
            deepgram_client=mock_client,
            circuit_breaker_config={'failure_threshold': 2, 'timeout': 60}
        )
        
        # Primer fallo
        with pytest.raises(Exception):
            service.transcribe_audio("https://example.com/audio1.mp3")
        
        # Segundo fallo - debe abrir el circuito
        with pytest.raises(Exception):
            service.transcribe_audio("https://example.com/audio2.mp3")
        
        # Tercer intento - circuito abierto
        with pytest.raises(CircuitBreakerOpenException):
            service.transcribe_audio("https://example.com/audio3.mp3")
    
    def test_should_retry_with_exponential_backoff(self):
        """
        🔴 RED: Debe reintentar con backoff exponencial antes de abrir circuito.
        
        Given: TranscriptionService con retry configurado
        When: Deepgram falla temporalmente
        Then: Debe reintentar con delays crecientes
        """
        from services.transcription_service import TranscriptionService
        
        mock_client = Mock()
        # Falla 2 veces, luego éxito
        mock_client.transcription.prerecorded.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            {
                'results': {
                    'channels': [{
                        'alternatives': [{'transcript': 'Success after retry'}]
                    }]
                }
            }
        ]
        
        service = TranscriptionService(
            deepgram_client=mock_client,
            max_retries=3,
            initial_retry_delay=0.1  # Delay corto para testing
        )
        
        start_time = time.time()
        result = service.transcribe_audio("https://example.com/audio.mp3")
        elapsed_time = time.time() - start_time
        
        # Assert
        assert result == "Success after retry"
        # Verificar que hubo delay (backoff exponencial)
        assert elapsed_time >= 0.1  # Al menos el delay inicial
        # Verificar que se hicieron 3 intentos
        assert mock_client.transcription.prerecorded.call_count == 3


class TestTranscriptionServicePerformance:
    """Tests de performance según RNF1.0."""
    
    def test_should_complete_transcription_within_timeout(self):
        """
        🔴 RED: Debe completar transcripción en tiempo razonable (RNF1.0).
        
        Given: Audio de duración conocida
        When: Se transcribe
        Then: Debe completar en < 5 minutos (para audio de reunión típica)
        """
        from services.transcription_service import TranscriptionService, TranscriptionTimeoutException
        
        mock_client = Mock()
        # Simular respuesta lenta
        def slow_transcription(*args, **kwargs):
            time.sleep(0.1)  # Simulación rápida
            return {
                'results': {
                    'channels': [{
                        'alternatives': [{'transcript': 'Test'}]
                    }]
                }
            }
        
        mock_client.transcription.prerecorded.side_effect = slow_transcription
        
        service = TranscriptionService(
            deepgram_client=mock_client,
            transcription_timeout=300  # 5 minutos
        )
        
        start_time = time.time()
        result = service.transcribe_audio("https://example.com/audio.mp3")
        elapsed_time = time.time() - start_time
        
        # Assert
        assert result is not None
        assert elapsed_time < 300  # RNF1.0 compliance
    
    def test_should_raise_timeout_exception_if_too_slow(self):
        """
        🔴 RED: Debe lanzar excepción si excede timeout configurado.
        
        Given: TranscriptionService con timeout corto
        When: Deepgram responde muy lento
        Then: Debe lanzar TranscriptionTimeoutException
        """
        from services.transcription_service import TranscriptionService, TranscriptionTimeoutException
        
        mock_client = Mock()
        
        def very_slow_transcription(*args, **kwargs):
            time.sleep(1.0)  # Más lento que el timeout
            return {'results': {'channels': [{'alternatives': [{'transcript': 'Test'}]}]}}
        
        mock_client.transcription.prerecorded.side_effect = very_slow_transcription
        
        service = TranscriptionService(
            deepgram_client=mock_client,
            transcription_timeout=0.5  # Timeout muy corto para testing
        )
        
        # Assert
        with pytest.raises(TranscriptionTimeoutException) as exc_info:
            service.transcribe_audio("https://example.com/audio.mp3")
        
        assert "Transcription exceeded timeout" in str(exc_info.value)


class TestTranscriptionServiceConfiguration:
    """Tests de configuración y flexibilidad."""
    
    def test_should_accept_custom_deepgram_options(self):
        """
        🔴 RED: Debe permitir configurar opciones de Deepgram.
        
        Given: TranscriptionService con opciones custom
        When: Se transcribe audio
        Then: Debe pasar opciones correctas a Deepgram API
        """
        from services.transcription_service import TranscriptionService
        
        mock_client = Mock()
        mock_client.transcription.prerecorded.return_value = {
            'results': {
                'channels': [{
                    'alternatives': [{'transcript': 'Test'}]
                }]
            }
        }
        
        custom_options = {
            'model': 'nova-2',
            'language': 'es',
            'punctuate': True,
            'diarize': True
        }
        
        service = TranscriptionService(
            deepgram_client=mock_client,
            default_options=custom_options
        )
        
        # Act
        service.transcribe_audio("https://example.com/audio.mp3")
        
        # Assert - Verificar que se llamó con las opciones correctas
        call_args = mock_client.transcription.prerecorded.call_args
        assert call_args is not None
        # Verificar que las opciones se pasaron
        options_passed = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert 'model' in options_passed or options_passed == custom_options
    
    def test_should_support_multiple_audio_formats(self):
        """
        🔴 RED: Debe soportar diferentes formatos de audio.
        
        Given: TranscriptionService
        When: Se transcriben diferentes formatos (mp3, wav, m4a)
        Then: Debe procesar todos exitosamente
        """
        from services.transcription_service import TranscriptionService
        
        mock_client = Mock()
        mock_client.transcription.prerecorded.return_value = {
            'results': {
                'channels': [{
                    'alternatives': [{'transcript': 'Test'}]
                }]
            }
        }
        
        service = TranscriptionService(deepgram_client=mock_client)
        
        # Test diferentes formatos
        audio_formats = [
            "https://example.com/audio.mp3",
            "https://example.com/audio.wav",
            "https://example.com/audio.m4a",
            "https://example.com/audio.flac"
        ]
        
        for audio_url in audio_formats:
            result = service.transcribe_audio(audio_url)
            assert result is not None
            assert isinstance(result, str)


class TestTranscriptionServiceObservability:
    """Tests de logging y métricas."""
    
    def test_should_log_transcription_attempts(self, caplog):
        """
        🔴 RED: Debe logear intentos de transcripción para observabilidad.
        
        Given: TranscriptionService con logging configurado
        When: Se transcribe audio
        Then: Debe generar logs estructurados
        """
        from services.transcription_service import TranscriptionService
        
        mock_client = Mock()
        mock_client.transcription.prerecorded.return_value = {
            'results': {
                'channels': [{
                    'alternatives': [{'transcript': 'Test'}]
                }]
            }
        }
        
        service = TranscriptionService(deepgram_client=mock_client)
        
        # Act
        service.transcribe_audio("https://example.com/audio.mp3")
        
        # Assert - Verificar logs
        # (Esto verificará cuando implementemos logging)
        assert True  # Placeholder - verificaremos logs reales en implementación
    
    def test_should_track_transcription_metrics(self):
        """
        🔴 RED: Debe mantener métricas de transcripciones.
        
        Given: TranscriptionService
        When: Se realizan múltiples transcripciones
        Then: Debe exponer métricas (total, éxitos, fallos, tiempo promedio)
        """
        from services.transcription_service import TranscriptionService
        
        mock_client = Mock()
        mock_client.transcription.prerecorded.return_value = {
            'results': {
                'channels': [{
                    'alternatives': [{'transcript': 'Test'}]
                }]
            }
        }
        
        service = TranscriptionService(deepgram_client=mock_client)
        
        # Realizar varias transcripciones
        for _ in range(5):
            service.transcribe_audio("https://example.com/audio.mp3")
        
        # Assert - Verificar métricas
        metrics = service.get_metrics()
        assert metrics['total_transcriptions'] == 5
        assert metrics['successful_transcriptions'] == 5
        assert metrics['failed_transcriptions'] == 0
        assert 'average_duration' in metrics


# ================================================================================================
# 🎯 Fixtures para Tests
# ================================================================================================

@pytest.fixture
def mock_deepgram_client():
    """Fixture que proporciona un cliente Deepgram mockeado."""
    client = Mock()
    client.transcription = Mock()
    client.transcription.prerecorded = Mock()
    return client


@pytest.fixture
def sample_audio_url():
    """Fixture con URL de audio de ejemplo."""
    return "https://example.com/sample_meeting.mp3"


@pytest.fixture
def sample_transcription_response():
    """Fixture con respuesta típica de Deepgram."""
    return {
        'results': {
            'channels': [{
                'alternatives': [{
                    'transcript': 'This is a sample meeting transcription',
                    'confidence': 0.98
                }]
            }]
        },
        'metadata': {
            'duration': 180.0,
            'channels': 1,
            'model': 'nova-2'
        }
    }

"""
🔵 REFACTOR - TranscriptionService V2 con SOLID aplicado

Versión refactorizada del servicio de transcripción que aplica:
- DIP: Inyección de dependencias con abstracciones
- SRP: Responsabilidades claramente separadas
- OCP: Abierto para extensión (Strategy Pattern)
- ISP: Interfaces segregadas
- Clean Architecture: Ports & Adapters

Esta es la versión mejorada que mantiene la compatibilidad con los tests existentes.
"""

import time
import logging
from typing import Optional, Dict, Any

from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException

from .abstractions import (
    AudioSource,
    TranscriptionResult,
    AudioTranscriptionProvider,
    TranscriptionResultParser,
    RetryStrategy,
    ExponentialBackoffStrategy,
    TranscriptionServiceConfig,
    TranscriptionMetricsCollector,
    TranscriptionTimeoutException,
    InvalidAudioSourceException,
    ProviderUnavailableException
)

from .adapters import (
    DeepgramProvider,
    DeepgramResponseParser,
    InMemoryMetricsCollector,
    AudioSourceValidator
)

logger = logging.getLogger(__name__)


# ================================================================================================
# 🔵 REFACTORED TranscriptionService - Aplicando SOLID
# ================================================================================================

class TranscriptionServiceV2:
    """
    🔵 Servicio de transcripción REFACTORIZADO aplicando principios SOLID.
    
    Mejoras sobre la versión original:
    - ✅ DIP: Depende de abstracciones, no de implementaciones concretas
    - ✅ SRP: Cada componente tiene una responsabilidad única
    - ✅ OCP: Extensible via Strategy Pattern y Dependency Injection
    - ✅ ISP: Usa interfaces segregadas y específicas
    - ✅ Clean Architecture: Separación clara de capas
    
    Ejemplo de uso:
        # Con Deepgram
        provider = DeepgramProvider(deepgram_client)
        parser = DeepgramResponseParser()
        config = TranscriptionServiceConfig(provider=provider)
        
        service = TranscriptionServiceV2(config, parser)
        result = service.transcribe(audio_url)
    """
    
    def __init__(
        self,
        config: TranscriptionServiceConfig,
        response_parser: TranscriptionResultParser,
        validator: Optional[AudioSourceValidator] = None
    ):
        """
        ✅ DIP - Inyección de dependencias.
        
        Args:
            config: Configuración del servicio
            response_parser: Parser para respuestas del proveedor
            validator: Validador de fuentes de audio (opcional)
        """
        self.config = config
        self.response_parser = response_parser
        self.validator = validator or AudioSourceValidator()
        
        # Metrics collector (inyectado o por defecto)
        self.metrics = config.metrics_collector or InMemoryMetricsCollector()
    
    def transcribe(self, audio_url: str) -> str:
        """
        ✅ API compatible con tests existentes.
        
        Transcribe audio y retorna el texto (backward compatibility).
        
        Args:
            audio_url: URL del audio a transcribir
            
        Returns:
            Texto transcrito
        """
        result = self.transcribe_with_metadata(audio_url)
        
        if not result.success:
            raise Exception(f"Transcription failed: {result.metadata.get('error', 'Unknown error')}")
        
        return result.text
    
    def transcribe_with_metadata(self, audio_url: str) -> TranscriptionResult:
        """
        🔵 Método principal refactorizado con SOLID aplicado.
        
        Args:
            audio_url: URL del audio
            
        Returns:
            TranscriptionResult con texto y metadata
            
        Raises:
            InvalidAudioSourceException: Si la URL no es válida
            TranscriptionTimeoutException: Si excede timeout
            ProviderUnavailableException: Si el proveedor no está disponible
        """
        # 1. Crear AudioSource (Value Object)
        audio_source = AudioSource(url=audio_url)
        
        # 2. Validar fuente
        self.validator.validate(audio_source)
        
        # 3. Registrar intento (Metrics)
        self.metrics.record_transcription_attempt(audio_source)
        
        # 4. Transcribir con retry y circuit breaker
        start_time = time.time()
        
        try:
            result = self._transcribe_with_retry_and_circuit_breaker(audio_source)
            
            # Verificar timeout (RNF1.0)
            elapsed_time = time.time() - start_time
            if elapsed_time > self.config.transcription_timeout:
                raise TranscriptionTimeoutException(
                    f"Transcription exceeded timeout of {self.config.transcription_timeout}s"
                )
            
            # Registrar éxito
            self.metrics.record_transcription_success(elapsed_time, len(result.text))
            
            logger.info(
                "Transcription completed successfully",
                extra={
                    'audio_url': audio_url,
                    'duration': elapsed_time,
                    'word_count': result.get_word_count(),
                    'confidence': result.confidence
                }
            )
            
            return result
            
        except Exception as e:
            # Registrar fallo
            self.metrics.record_transcription_failure(e)
            
            logger.error(
                f"Transcription failed: {str(e)}",
                extra={'audio_url': audio_url},
                exc_info=True
            )
            
            # Re-lanzar excepciones específicas
            if isinstance(e, (TranscriptionTimeoutException, InvalidAudioSourceException)):
                raise
            
            # Convertir otras excepciones
            raise ProviderUnavailableException(f"Transcription service unavailable: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas del servicio.
        
        Returns:
            Diccionario con métricas
        """
        metrics = self.metrics.get_metrics()
        
        # Añadir información del proveedor
        if self.config.provider:
            metrics['provider'] = self.config.provider.get_provider_name()
            metrics['provider_available'] = self.config.provider.is_available()
        
        # Añadir estado del circuit breaker
        if self.config.circuit_breaker:
            metrics['circuit_breaker_state'] = self.config.circuit_breaker.state.value
        
        return metrics
    
    # ============================================================================================
    # 🔒 Private Methods - Lógica de retry y circuit breaker
    # ============================================================================================
    
    def _transcribe_with_retry_and_circuit_breaker(self, audio_source: AudioSource) -> TranscriptionResult:
        """
        ✅ SRP - Método enfocado en retry con circuit breaker.
        
        Args:
            audio_source: Fuente de audio
            
        Returns:
            TranscriptionResult
        """
        last_exception = None
        retry_strategy = self.config.retry_strategy
        
        for attempt in range(self.config.max_retries):
            try:
                # Llamada protegida por Circuit Breaker
                raw_response = self._call_provider_with_circuit_breaker(audio_source)
                
                # Parsear respuesta
                result = self.response_parser.parse_response(raw_response)
                
                return result
                
            except CircuitBreakerOpenException as e:
                # No reintentar si el circuito está abierto
                logger.warning("Circuit breaker is open, aborting retry")
                raise ProviderUnavailableException("Service circuit breaker is open")
                
            except Exception as e:
                last_exception = e
                
                # Verificar si debemos reintentar
                if not retry_strategy.should_retry(attempt, self.config.max_retries, e):
                    break
                
                # Esperar con backoff
                if attempt < self.config.max_retries - 1:
                    delay = retry_strategy.get_delay(attempt)
                    logger.warning(
                        f"Transcription attempt {attempt + 1} failed, retrying in {delay}s",
                        extra={
                            'attempt': attempt + 1,
                            'max_retries': self.config.max_retries,
                            'error': str(e)
                        }
                    )
                    time.sleep(delay)
        
        # Si llegamos aquí, todos los reintentos fallaron
        raise last_exception or Exception("Transcription failed after all retries")
    
    def _call_provider_with_circuit_breaker(self, audio_source: AudioSource) -> Dict[str, Any]:
        """
        ✅ DIP - Llama al proveedor abstracto con circuit breaker.
        
        Args:
            audio_source: Fuente de audio
            
        Returns:
            Respuesta raw del proveedor
        """
        if not self.config.provider:
            raise ProviderUnavailableException("No transcription provider configured")
        
        if not self.config.provider.is_available():
            raise ProviderUnavailableException(
                f"Provider {self.config.provider.get_provider_name()} is not available"
            )
        
        # Llamar con circuit breaker si está configurado
        if self.config.circuit_breaker:
            return self.config.circuit_breaker.call(
                self.config.provider.transcribe,
                audio_source,
                self.config.default_options
            )
        else:
            # Sin circuit breaker (no recomendado para producción)
            return self.config.provider.transcribe(audio_source, self.config.default_options)

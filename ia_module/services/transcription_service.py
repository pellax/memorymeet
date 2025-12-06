"""
🟢 GREEN PHASE - TranscriptionService Implementation

Implementación mínima del servicio de transcripción que hace pasar los tests TDD.
Integra Deepgram SDK y Circuit Breaker para tolerancia a fallos.

Requisitos:
- RF2.0: Transcripción de audio con Deepgram
- RNF5.0: Tolerancia a fallos con Circuit Breaker
- RNF1.0: Performance < 5 minutos
"""

import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import re
from urllib.parse import urlparse

# Circuit Breaker ya implementado
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException

logger = logging.getLogger(__name__)


# ================================================================================================
# 🟢 GREEN PHASE - Excepciones personalizadas
# ================================================================================================

class InvalidAudioUrlException(Exception):
    """Excepción lanzada cuando la URL de audio no es válida."""
    pass


class TranscriptionTimeoutException(Exception):
    """Excepción lanzada cuando la transcripción excede el timeout."""
    pass


class TranscriptionServiceException(Exception):
    """Excepción base para errores del servicio de transcripción."""
    pass


# ================================================================================================
# 🟢 GREEN PHASE - Modelo de datos
# ================================================================================================

@dataclass
class TranscriptionResult:
    """
    Resultado de una transcripción con metadata.
    
    Attributes:
        text: Texto transcrito
        success: Si la transcripción fue exitosa
        confidence: Nivel de confianza (0.0 - 1.0)
        duration_seconds: Duración del audio en segundos
        metadata: Metadata adicional de Deepgram
    """
    text: str
    success: bool = True
    confidence: float = 0.0
    duration_seconds: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


# ================================================================================================
# 🟢 GREEN PHASE - Implementación del Servicio
# ================================================================================================

class TranscriptionService:
    """
    🟢 Servicio de transcripción de audio usando Deepgram.
    
    Implementa tolerancia a fallos con Circuit Breaker y retry con backoff exponencial.
    
    Ejemplo:
        service = TranscriptionService(deepgram_client)
        result = service.transcribe_audio("https://example.com/audio.mp3")
        print(result)  # "Hello world, this is a test transcription"
    """
    
    def __init__(
        self,
        deepgram_client,
        circuit_breaker_config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        transcription_timeout: int = 300,  # 5 minutos (RNF1.0)
        default_options: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el servicio de transcripción.
        
        Args:
            deepgram_client: Cliente de Deepgram SDK
            circuit_breaker_config: Configuración del Circuit Breaker
            max_retries: Número máximo de reintentos
            initial_retry_delay: Delay inicial para backoff exponencial
            transcription_timeout: Timeout máximo en segundos
            default_options: Opciones por defecto para Deepgram
        """
        self.deepgram_client = deepgram_client
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.transcription_timeout = transcription_timeout
        self.default_options = default_options or {
            'model': 'nova-2',
            'punctuate': True,
            'language': 'en'
        }
        
        # Circuit Breaker configuration
        cb_config = circuit_breaker_config or {}
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=cb_config.get('failure_threshold', 3),
            timeout=cb_config.get('timeout', 60),
            expected_exception=Exception
        )
        
        # Métricas
        self._total_transcriptions = 0
        self._successful_transcriptions = 0
        self._failed_transcriptions = 0
        self._total_duration = 0.0
    
    def transcribe_audio(self, audio_url: str) -> str:
        """
        🟢 Transcribe audio desde una URL.
        
        Implementación mínima que pasa los tests básicos.
        
        Args:
            audio_url: URL del archivo de audio
            
        Returns:
            Texto transcrito
            
        Raises:
            InvalidAudioUrlException: Si la URL no es válida
            CircuitBreakerOpenException: Si el circuito está abierto
            TranscriptionTimeoutException: Si excede el timeout
        """
        # Validación de URL
        self._validate_audio_url(audio_url)
        
        # Tracking de inicio
        start_time = time.time()
        self._total_transcriptions += 1
        
        try:
            # Transcripción con retry y circuit breaker
            text = self._transcribe_with_retry(audio_url)
            
            # Verificar timeout (RNF1.0)
            elapsed_time = time.time() - start_time
            if elapsed_time > self.transcription_timeout:
                raise TranscriptionTimeoutException(
                    f"Transcription exceeded timeout of {self.transcription_timeout}s"
                )
            
            # Tracking de éxito
            self._successful_transcriptions += 1
            self._total_duration += elapsed_time
            
            logger.info(
                f"Transcription successful",
                extra={
                    'audio_url': audio_url,
                    'duration': elapsed_time,
                    'text_length': len(text)
                }
            )
            
            return text
            
        except (CircuitBreakerOpenException, TranscriptionTimeoutException):
            # Propagar excepciones específicas
            self._failed_transcriptions += 1
            raise
            
        except Exception as e:
            self._failed_transcriptions += 1
            logger.error(
                f"Transcription failed: {str(e)}",
                extra={'audio_url': audio_url},
                exc_info=True
            )
            raise
    
    def transcribe_audio_with_metadata(self, audio_url: str) -> TranscriptionResult:
        """
        🟢 Transcribe audio y retorna resultado con metadata completa.
        
        Args:
            audio_url: URL del archivo de audio
            
        Returns:
            TranscriptionResult con texto y metadata
        """
        self._validate_audio_url(audio_url)
        
        start_time = time.time()
        
        try:
            # Llamada protegida por Circuit Breaker
            response = self.circuit_breaker.call(
                self._call_deepgram_api,
                audio_url,
                self.default_options
            )
            
            # Extraer datos de la respuesta
            text = self._extract_transcript_text(response)
            confidence = self._extract_confidence(response)
            duration = self._extract_duration(response)
            
            elapsed_time = time.time() - start_time
            
            return TranscriptionResult(
                text=text,
                success=True,
                confidence=confidence,
                duration_seconds=duration,
                metadata={
                    'processing_time': elapsed_time,
                    'audio_url': audio_url,
                    'deepgram_response': response.get('metadata', {})
                }
            )
            
        except Exception as e:
            logger.error(f"Transcription with metadata failed: {str(e)}")
            return TranscriptionResult(
                text="",
                success=False,
                metadata={'error': str(e)}
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        🟢 Retorna métricas del servicio de transcripción.
        
        Returns:
            Diccionario con métricas
        """
        avg_duration = (
            self._total_duration / self._successful_transcriptions
            if self._successful_transcriptions > 0
            else 0.0
        )
        
        return {
            'total_transcriptions': self._total_transcriptions,
            'successful_transcriptions': self._successful_transcriptions,
            'failed_transcriptions': self._failed_transcriptions,
            'average_duration': avg_duration,
            'circuit_breaker_state': self.circuit_breaker.state.value
        }
    
    # ============================================================================================
    # 🔒 Private Methods
    # ============================================================================================
    
    def _validate_audio_url(self, audio_url: str) -> None:
        """
        Valida que la URL de audio sea válida.
        
        Args:
            audio_url: URL a validar
            
        Raises:
            InvalidAudioUrlException: Si la URL no es válida
        """
        if not audio_url:
            raise InvalidAudioUrlException("Invalid audio URL: URL is empty or None")
        
        # Validar formato de URL
        try:
            parsed = urlparse(audio_url)
            if not all([parsed.scheme, parsed.netloc]):
                raise InvalidAudioUrlException(
                    f"Invalid audio URL: {audio_url} - must be a valid URL with scheme and netloc"
                )
        except Exception:
            raise InvalidAudioUrlException(f"Invalid audio URL: {audio_url}")
        
        # Validar extensión (opcional - formatos soportados)
        supported_formats = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm']
        has_valid_extension = any(audio_url.lower().endswith(fmt) for fmt in supported_formats)
        
        if not has_valid_extension:
            logger.warning(
                f"Audio URL does not have recognized extension: {audio_url}",
                extra={'supported_formats': supported_formats}
            )
    
    def _transcribe_with_retry(self, audio_url: str) -> str:
        """
        Transcribe con retry y backoff exponencial.
        
        Args:
            audio_url: URL del audio
            
        Returns:
            Texto transcrito
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Llamada protegida por Circuit Breaker
                response = self.circuit_breaker.call(
                    self._call_deepgram_api,
                    audio_url,
                    self.default_options
                )
                
                return self._extract_transcript_text(response)
                
            except CircuitBreakerOpenException:
                # No reintentar si el circuito está abierto
                raise
                
            except Exception as e:
                last_exception = e
                
                # Si no es el último intento, esperar con backoff exponencial
                if attempt < self.max_retries - 1:
                    delay = self.initial_retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Transcription attempt {attempt + 1} failed, retrying in {delay}s",
                        extra={'audio_url': audio_url, 'error': str(e)}
                    )
                    time.sleep(delay)
        
        # Si llegamos aquí, todos los reintentos fallaron
        raise last_exception
    
    def _call_deepgram_api(self, audio_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Llama a la API de Deepgram.
        
        Args:
            audio_url: URL del audio
            options: Opciones de transcripción
            
        Returns:
            Respuesta de Deepgram
        """
        return self.deepgram_client.transcription.prerecorded(
            {'url': audio_url},
            options
        )
    
    def _extract_transcript_text(self, response: Dict[str, Any]) -> str:
        """
        Extrae el texto transcrito de la respuesta de Deepgram.
        
        Args:
            response: Respuesta de Deepgram
            
        Returns:
            Texto transcrito
        """
        try:
            return response['results']['channels'][0]['alternatives'][0]['transcript']
        except (KeyError, IndexError) as e:
            raise TranscriptionServiceException(
                f"Failed to extract transcript from response: {str(e)}"
            )
    
    def _extract_confidence(self, response: Dict[str, Any]) -> float:
        """Extrae el nivel de confianza de la respuesta."""
        try:
            return response['results']['channels'][0]['alternatives'][0].get('confidence', 0.0)
        except (KeyError, IndexError):
            return 0.0
    
    def _extract_duration(self, response: Dict[str, Any]) -> float:
        """Extrae la duración del audio de la respuesta."""
        try:
            return response.get('metadata', {}).get('duration', 0.0)
        except (KeyError, AttributeError):
            return 0.0

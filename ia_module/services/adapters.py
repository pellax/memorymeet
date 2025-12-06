"""
🔵 REFACTOR - Adaptadores concretos (Hexagonal Architecture)

Implementaciones específicas de proveedores de transcripción.
Aplicación de Adapter Pattern y Ports & Adapters.
"""

import logging
from typing import Dict, Any
from urllib.parse import urlparse

from .abstractions import (
    AudioTranscriptionProvider,
    TranscriptionResultParser,
    AudioSource,
    TranscriptionResult,
    TranscriptionMetricsCollector,
    InvalidAudioSourceException
)

logger = logging.getLogger(__name__)


# ================================================================================================
# 🔌 Adapters - Implementaciones concretas
# ================================================================================================

class DeepgramProvider(AudioTranscriptionProvider):
    """
    ✅ Adapter para Deepgram API.
    
    Implementa la interfaz AudioTranscriptionProvider para Deepgram.
    """
    
    def __init__(self, deepgram_client):
        """
        Inicializa el proveedor Deepgram.
        
        Args:
            deepgram_client: Cliente del SDK de Deepgram
        """
        self.client = deepgram_client
        self._available = True
    
    def transcribe(self, audio_source: AudioSource, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe audio usando Deepgram API.
        
        Args:
            audio_source: Fuente de audio
            options: Opciones de Deepgram (model, language, etc.)
            
        Returns:
            Respuesta raw de Deepgram
        """
        try:
            logger.info(
                f"Transcribing audio with Deepgram",
                extra={
                    'audio_url': audio_source.url,
                    'format': audio_source.format,
                    'options': options
                }
            )
            
            response = self.client.transcription.prerecorded(
                {'url': audio_source.url},
                options
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Deepgram transcription failed: {str(e)}", exc_info=True)
            self._available = False
            raise
    
    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor."""
        return "deepgram"
    
    def is_available(self) -> bool:
        """Verifica disponibilidad del proveedor."""
        return self._available


class DeepgramResponseParser(TranscriptionResultParser):
    """
    ✅ SRP - Parser específico para respuestas de Deepgram.
    
    Separa la lógica de parsing de la lógica de transcripción.
    """
    
    def parse_response(self, raw_response: Dict[str, Any]) -> TranscriptionResult:
        """
        Parsea respuesta de Deepgram a TranscriptionResult.
        
        Args:
            raw_response: Respuesta raw de Deepgram
            
        Returns:
            TranscriptionResult parseado
        """
        try:
            # Extraer texto
            text = self._extract_text(raw_response)
            
            # Extraer metadata
            confidence = self._extract_confidence(raw_response)
            duration = self._extract_duration(raw_response)
            
            # Metadata adicional
            metadata = {
                'deepgram_metadata': raw_response.get('metadata', {}),
                'model': raw_response.get('metadata', {}).get('model', 'unknown'),
                'channels': raw_response.get('metadata', {}).get('channels', 1)
            }
            
            return TranscriptionResult(
                text=text,
                success=True,
                confidence=confidence,
                duration_seconds=duration,
                metadata=metadata,
                provider='deepgram'
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Deepgram response: {str(e)}")
            return TranscriptionResult(
                text="",
                success=False,
                metadata={'error': str(e), 'raw_response': raw_response},
                provider='deepgram'
            )
    
    def _extract_text(self, response: Dict[str, Any]) -> str:
        """Extrae el texto transcrito."""
        try:
            return response['results']['channels'][0]['alternatives'][0]['transcript']
        except (KeyError, IndexError) as e:
            raise ValueError(f"Failed to extract transcript text: {str(e)}")
    
    def _extract_confidence(self, response: Dict[str, Any]) -> float:
        """Extrae el nivel de confianza."""
        try:
            return response['results']['channels'][0]['alternatives'][0].get('confidence', 0.0)
        except (KeyError, IndexError):
            return 0.0
    
    def _extract_duration(self, response: Dict[str, Any]) -> float:
        """Extrae la duración del audio."""
        try:
            return response.get('metadata', {}).get('duration', 0.0)
        except (KeyError, AttributeError):
            return 0.0


class InMemoryMetricsCollector(TranscriptionMetricsCollector):
    """
    ✅ Implementación en memoria para métricas de transcripción.
    
    Útil para desarrollo y testing. En producción se usaría Prometheus/Datadog.
    """
    
    def __init__(self):
        self._total_attempts = 0
        self._successful_transcriptions = 0
        self._failed_transcriptions = 0
        self._total_duration = 0.0
        self._total_text_length = 0
        self._errors = []
    
    def record_transcription_attempt(self, audio_source: AudioSource):
        """Registra un intento de transcripción."""
        self._total_attempts += 1
        logger.debug(f"Transcription attempt recorded: {audio_source.url}")
    
    def record_transcription_success(self, duration_seconds: float, text_length: int):
        """Registra una transcripción exitosa."""
        self._successful_transcriptions += 1
        self._total_duration += duration_seconds
        self._total_text_length += text_length
        
        logger.info(
            "Transcription success recorded",
            extra={
                'duration': duration_seconds,
                'text_length': text_length
            }
        )
    
    def record_transcription_failure(self, error: Exception):
        """Registra una transcripción fallida."""
        self._failed_transcriptions += 1
        self._errors.append({
            'error_type': type(error).__name__,
            'error_message': str(error)
        })
        
        logger.error(
            "Transcription failure recorded",
            extra={'error': str(error)}
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas recolectadas."""
        avg_duration = (
            self._total_duration / self._successful_transcriptions
            if self._successful_transcriptions > 0
            else 0.0
        )
        
        avg_text_length = (
            self._total_text_length / self._successful_transcriptions
            if self._successful_transcriptions > 0
            else 0
        )
        
        success_rate = (
            self._successful_transcriptions / self._total_attempts
            if self._total_attempts > 0
            else 0.0
        )
        
        return {
            'total_attempts': self._total_attempts,
            'successful_transcriptions': self._successful_transcriptions,
            'failed_transcriptions': self._failed_transcriptions,
            'success_rate': success_rate,
            'average_duration': avg_duration,
            'average_text_length': avg_text_length,
            'recent_errors': self._errors[-5:]  # Últimos 5 errores
        }


# ================================================================================================
# 🔧 Utility Adapters
# ================================================================================================

class AudioSourceValidator:
    """
    ✅ SRP - Validador especializado de fuentes de audio.
    
    Separa la lógica de validación del servicio principal.
    """
    
    SUPPORTED_FORMATS = ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'webm']
    
    @classmethod
    def validate(cls, audio_source: AudioSource) -> None:
        """
        Valida una fuente de audio.
        
        Args:
            audio_source: Fuente a validar
            
        Raises:
            InvalidAudioSourceException: Si la fuente no es válida
        """
        # Validar URL no vacía
        if not audio_source.url:
            raise InvalidAudioSourceException("Audio URL cannot be empty")
        
        # Validar formato de URL
        cls._validate_url_format(audio_source.url)
        
        # Validar formato de audio (warning si no está soportado)
        if audio_source.format not in cls.SUPPORTED_FORMATS and audio_source.format != 'unknown':
            logger.warning(
                f"Audio format may not be supported: {audio_source.format}",
                extra={
                    'url': audio_source.url,
                    'format': audio_source.format,
                    'supported_formats': cls.SUPPORTED_FORMATS
                }
            )
    
    @staticmethod
    def _validate_url_format(url: str) -> None:
        """
        Valida el formato de la URL.
        
        Args:
            url: URL a validar
            
        Raises:
            InvalidAudioSourceException: Si el formato no es válido
        """
        try:
            parsed = urlparse(url)
            
            # Verificar que tenga scheme y netloc
            if not all([parsed.scheme, parsed.netloc]):
                raise InvalidAudioSourceException(
                    f"Invalid URL format: {url} - must have scheme and network location"
                )
            
            # Verificar schemes válidos
            if parsed.scheme not in ['http', 'https', 'gs', 's3']:
                raise InvalidAudioSourceException(
                    f"Unsupported URL scheme: {parsed.scheme} - must be http, https, gs, or s3"
                )
                
        except Exception as e:
            if isinstance(e, InvalidAudioSourceException):
                raise
            raise InvalidAudioSourceException(f"Failed to parse URL: {str(e)}")

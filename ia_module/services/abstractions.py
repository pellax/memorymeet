"""
🔵 REFACTOR - Abstracciones para servicios de transcripción

Aplicación de principios SOLID:
- DIP (Dependency Inversion Principle): Dependencias de abstracciones
- ISP (Interface Segregation Principle): Interfaces específicas
- OCP (Open/Closed Principle): Abierto para extensión
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol
from dataclasses import dataclass
from datetime import datetime


# ================================================================================================
# 🎯 Domain Models (Value Objects)
# ================================================================================================

@dataclass
class AudioSource:
    """
    Value Object para fuente de audio.
    
    Encapsula la información de la fuente de audio y su validación.
    """
    url: str
    format: str = None
    duration_hint: float = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.url:
            raise ValueError("Audio URL cannot be empty")
        
        # Inferir formato si no se proporciona
        if not self.format:
            self.format = self._infer_format_from_url()
    
    def _infer_format_from_url(self) -> str:
        """Infiere el formato del audio desde la URL."""
        url_lower = self.url.lower()
        
        format_map = {
            '.mp3': 'mp3',
            '.wav': 'wav',
            '.m4a': 'm4a',
            '.flac': 'flac',
            '.ogg': 'ogg',
            '.webm': 'webm'
        }
        
        for ext, fmt in format_map.items():
            if url_lower.endswith(ext):
                return fmt
        
        return 'unknown'


@dataclass
class TranscriptionResult:
    """
    Value Object para resultado de transcripción.
    
    Inmutable y rico en comportamiento de dominio.
    """
    text: str
    success: bool = True
    confidence: float = 0.0
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    provider: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        
        if self.metadata is None:
            self.metadata = {}
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Verifica si la transcripción tiene alta confianza."""
        return self.confidence >= threshold
    
    def get_word_count(self) -> int:
        """Retorna el número de palabras en la transcripción."""
        return len(self.text.split()) if self.text else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            'text': self.text,
            'success': self.success,
            'confidence': self.confidence,
            'duration_seconds': self.duration_seconds,
            'word_count': self.get_word_count(),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'provider': self.provider,
            'metadata': self.metadata
        }


# ================================================================================================
# 🔌 Ports (Interfaces) - Hexagonal Architecture
# ================================================================================================

class AudioTranscriptionProvider(ABC):
    """
    ✅ DIP - Abstracción para proveedores de transcripción.
    
    Port (Hexagonal Architecture) que define el contrato para cualquier
    proveedor de transcripción de audio.
    
    Implementaciones: DeepgramProvider, WhisperProvider, GoogleSTTProvider
    """
    
    @abstractmethod
    def transcribe(self, audio_source: AudioSource, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe audio desde una fuente.
        
        Args:
            audio_source: Fuente de audio a transcribir
            options: Opciones específicas del proveedor
            
        Returns:
            Respuesta raw del proveedor
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el proveedor está disponible."""
        pass


class TranscriptionResultParser(ABC):
    """
    ✅ SRP - Responsabilidad única: parsear respuestas de proveedores.
    
    Separa la lógica de parsing de la lógica de transcripción.
    """
    
    @abstractmethod
    def parse_response(self, raw_response: Dict[str, Any]) -> TranscriptionResult:
        """
        Parsea la respuesta raw de un proveedor a TranscriptionResult.
        
        Args:
            raw_response: Respuesta del proveedor
            
        Returns:
            TranscriptionResult parseado
        """
        pass


class CircuitBreakerProtocol(Protocol):
    """
    ✅ DIP - Protocolo para Circuit Breaker.
    
    Permite inyección de cualquier implementación de Circuit Breaker.
    """
    
    def call(self, func, *args, **kwargs):
        """Ejecuta función protegida por circuit breaker."""
        ...
    
    @property
    def state(self):
        """Estado actual del circuit breaker."""
        ...


class TranscriptionMetricsCollector(ABC):
    """
    ✅ SRP - Responsabilidad única: recolectar métricas.
    
    Separa la lógica de métricas del servicio principal.
    """
    
    @abstractmethod
    def record_transcription_attempt(self, audio_source: AudioSource):
        """Registra un intento de transcripción."""
        pass
    
    @abstractmethod
    def record_transcription_success(self, duration_seconds: float, text_length: int):
        """Registra una transcripción exitosa."""
        pass
    
    @abstractmethod
    def record_transcription_failure(self, error: Exception):
        """Registra una transcripción fallida."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas recolectadas."""
        pass


# ================================================================================================
# 🎨 Strategy Pattern - Retry Strategies
# ================================================================================================

class RetryStrategy(ABC):
    """
    ✅ Strategy Pattern - Estrategias de retry configurables.
    """
    
    @abstractmethod
    def should_retry(self, attempt: int, max_attempts: int, error: Exception) -> bool:
        """Determina si se debe reintentar."""
        pass
    
    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Calcula el delay para el próximo reintento."""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """
    Estrategia de retry con backoff exponencial.
    """
    
    def __init__(self, initial_delay: float = 1.0, max_delay: float = 60.0, multiplier: float = 2.0):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
    
    def should_retry(self, attempt: int, max_attempts: int, error: Exception) -> bool:
        """Reintenta si no se alcanzó el máximo de intentos."""
        return attempt < max_attempts
    
    def get_delay(self, attempt: int) -> float:
        """Calcula delay exponencial."""
        delay = self.initial_delay * (self.multiplier ** attempt)
        return min(delay, self.max_delay)


class LinearBackoffStrategy(RetryStrategy):
    """
    Estrategia de retry con backoff lineal.
    """
    
    def __init__(self, delay_increment: float = 1.0, max_delay: float = 30.0):
        self.delay_increment = delay_increment
        self.max_delay = max_delay
    
    def should_retry(self, attempt: int, max_attempts: int, error: Exception) -> bool:
        return attempt < max_attempts
    
    def get_delay(self, attempt: int) -> float:
        """Calcula delay lineal."""
        delay = self.delay_increment * (attempt + 1)
        return min(delay, self.max_delay)


class NoRetryStrategy(RetryStrategy):
    """
    Estrategia sin retry - falla inmediatamente.
    """
    
    def should_retry(self, attempt: int, max_attempts: int, error: Exception) -> bool:
        return False
    
    def get_delay(self, attempt: int) -> float:
        return 0.0


# ================================================================================================
# 🏭 Factory Pattern - Configuration
# ================================================================================================

@dataclass
class TranscriptionServiceConfig:
    """
    ✅ Configuration as Code - Todas las configuraciones en un solo lugar.
    """
    # Provider configuration
    provider: AudioTranscriptionProvider = None
    circuit_breaker: CircuitBreakerProtocol = None
    
    # Retry configuration
    retry_strategy: RetryStrategy = None
    max_retries: int = 3
    
    # Timeout configuration
    transcription_timeout: int = 300  # 5 minutos (RNF1.0)
    
    # Deepgram specific options
    default_options: Dict[str, Any] = None
    
    # Metrics
    metrics_collector: TranscriptionMetricsCollector = None
    
    def __post_init__(self):
        if self.default_options is None:
            self.default_options = {
                'model': 'nova-2',
                'punctuate': True,
                'language': 'en'
            }
        
        if self.retry_strategy is None:
            self.retry_strategy = ExponentialBackoffStrategy()


# ================================================================================================
# 🎯 Domain Exceptions
# ================================================================================================

class TranscriptionException(Exception):
    """Base exception para errores de transcripción."""
    pass


class InvalidAudioSourceException(TranscriptionException):
    """Excepción cuando la fuente de audio no es válida."""
    pass


class TranscriptionTimeoutException(TranscriptionException):
    """Excepción cuando la transcripción excede el timeout."""
    pass


class ProviderUnavailableException(TranscriptionException):
    """Excepción cuando el proveedor no está disponible."""
    pass

"""
Services package for IA/NLP module.

⚠️ Backward Compatibility:
- TranscriptionService: Versión original (GREEN phase) - mantiene compatibilidad con tests
- TranscriptionServiceV2: Versión refactorizada (REFACTOR phase) - aplica SOLID

Se recomienda migrar a V2 para aprovechar mejor arquitectura.
"""

# Versión original (backward compatibility)
from .transcription_service import (
    TranscriptionService,
    TranscriptionResult,
    InvalidAudioUrlException,
    TranscriptionTimeoutException,
)

# Versión refactorizada con SOLID
from .transcription_service_v2 import TranscriptionServiceV2

# Abstracciones y adaptadores
from .abstractions import (
    AudioSource,
    AudioTranscriptionProvider,
    TranscriptionResultParser,
    RetryStrategy,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    NoRetryStrategy,
    TranscriptionServiceConfig,
    TranscriptionMetricsCollector,
    InvalidAudioSourceException,
    ProviderUnavailableException
)

from .adapters import (
    DeepgramProvider,
    DeepgramResponseParser,
    InMemoryMetricsCollector,
    AudioSourceValidator
)

__all__ = [
    # Original (backward compatibility)
    'TranscriptionService',
    'TranscriptionResult',
    'InvalidAudioUrlException',
    'TranscriptionTimeoutException',
    
    # V2 Refactorizado
    'TranscriptionServiceV2',
    
    # Abstractions
    'AudioSource',
    'AudioTranscriptionProvider',
    'TranscriptionResultParser',
    'RetryStrategy',
    'ExponentialBackoffStrategy',
    'LinearBackoffStrategy',
    'NoRetryStrategy',
    'TranscriptionServiceConfig',
    'TranscriptionMetricsCollector',
    'InvalidAudioSourceException',
    'ProviderUnavailableException',
    
    # Adapters
    'DeepgramProvider',
    'DeepgramResponseParser',
    'InMemoryMetricsCollector',
    'AudioSourceValidator',
]

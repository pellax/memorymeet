# TranscriptionService API Documentation

## 📚 Índice

1. [Introducción](#introducción)
2. [Arquitectura](#arquitectura)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [Configuración Avanzada](#configuración-avanzada)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Manejo de Errores](#manejo-de-errores)
8. [Mejores Prácticas](#mejores-prácticas)
9. [Migración de V1 a V2](#migración-de-v1-a-v2)

---

## Introducción

El **TranscriptionService** es un servicio robusto para transcripción de audio que implementa:

- ✅ **Circuit Breaker Pattern** (RNF5.0) - Tolerancia a fallos
- ✅ **Retry con Backoff Exponencial** - Resiliencia ante fallos temporales
- ✅ **SOLID Principles** - Arquitectura limpia y mantenible
- ✅ **Hexagonal Architecture** (Ports & Adapters) - Proveedores intercambiables
- ✅ **Métricas y Observabilidad** - Monitoreo integrado

### Versiones Disponibles

| Versión | Estado | Uso Recomendado |
|---------|--------|-----------------|
| **TranscriptionService (V1)** | ✅ Estable | Código legacy, backward compatibility |
| **TranscriptionServiceV2** | ✅ Recomendado | Nuevo desarrollo, mejor arquitectura |

---

## Arquitectura

### Clean Architecture (Capas)

```
┌─────────────────────────────────────────────────────┐
│ Application Layer                                   │
│ ├── TranscriptionServiceV2 (Use Case)              │
│ └── TranscriptionService (Legacy)                   │
├─────────────────────────────────────────────────────┤
│ Domain Layer                                        │
│ ├── AudioSource (Value Object)                     │
│ ├── TranscriptionResult (Value Object)             │
│ ├── AudioTranscriptionProvider (Port)              │
│ ├── TranscriptionResultParser (Port)               │
│ └── RetryStrategy (Strategy Pattern)               │
├─────────────────────────────────────────────────────┤
│ Infrastructure Layer                                │
│ ├── DeepgramProvider (Adapter)                     │
│ ├── DeepgramResponseParser (Adapter)               │
│ ├── InMemoryMetricsCollector (Adapter)             │
│ └── AudioSourceValidator (Utility)                  │
└─────────────────────────────────────────────────────┘
```

### Principios SOLID Aplicados

- **SRP**: Cada clase tiene una responsabilidad única
- **OCP**: Extensible vía Strategy Pattern y DI
- **LSP**: Proveedores intercambiables (Deepgram, Whisper, etc.)
- **ISP**: Interfaces específicas y segregadas
- **DIP**: Dependencias de abstracciones, no implementaciones

---

## Quick Start

### Instalación

```bash
# Las dependencias ya están en requirements.txt
pip install -r requirements.txt
```

### Uso Básico (V1 - Legacy)

```python
from services import TranscriptionService
from unittest.mock import Mock

# Crear cliente Deepgram (o mock para testing)
deepgram_client = Mock()
deepgram_client.transcription.prerecorded.return_value = {
    'results': {
        'channels': [{
            'alternatives': [{
                'transcript': 'Hello world'
            }]
        }]
    }
}

# Crear servicio
service = TranscriptionService(deepgram_client=deepgram_client)

# Transcribir
text = service.transcribe_audio("https://example.com/audio.mp3")
print(text)  # "Hello world"
```

### Uso Recomendado (V2 - Refactorizado)

```python
from services import (
    TranscriptionServiceV2,
    DeepgramProvider,
    DeepgramResponseParser,
    TranscriptionServiceConfig
)
from circuit_breaker import CircuitBreaker

# Configurar proveedor
provider = DeepgramProvider(deepgram_client)
parser = DeepgramResponseParser()

# Configurar circuit breaker
circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=60)

# Crear configuración
config = TranscriptionServiceConfig(
    provider=provider,
    circuit_breaker=circuit_breaker,
    max_retries=3,
    transcription_timeout=300
)

# Crear servicio
service = TranscriptionServiceV2(config, parser)

# Transcribir con metadata
result = service.transcribe_with_metadata("https://example.com/audio.mp3")
print(f"Text: {result.text}")
print(f"Confidence: {result.confidence}")
print(f"Duration: {result.duration_seconds}s")
```

---

## API Reference

### TranscriptionServiceV2

Servicio principal para transcripción de audio con arquitectura mejorada.

#### Constructor

```python
TranscriptionServiceV2(
    config: TranscriptionServiceConfig,
    response_parser: TranscriptionResultParser,
    validator: Optional[AudioSourceValidator] = None
)
```

**Parámetros:**

- `config` (TranscriptionServiceConfig): Configuración del servicio
- `response_parser` (TranscriptionResultParser): Parser para respuestas del proveedor
- `validator` (AudioSourceValidator, optional): Validador de fuentes de audio

**Ejemplo:**

```python
service = TranscriptionServiceV2(
    config=config,
    response_parser=DeepgramResponseParser(),
    validator=AudioSourceValidator()
)
```

#### Métodos

##### `transcribe(audio_url: str) -> str`

Transcribe audio y retorna solo el texto (backward compatibility con V1).

**Parámetros:**
- `audio_url` (str): URL del archivo de audio

**Returns:**
- `str`: Texto transcrito

**Raises:**
- `InvalidAudioSourceException`: URL inválida
- `TranscriptionTimeoutException`: Timeout excedido
- `ProviderUnavailableException`: Proveedor no disponible

**Ejemplo:**

```python
text = service.transcribe("https://example.com/meeting.mp3")
print(text)
```

##### `transcribe_with_metadata(audio_url: str) -> TranscriptionResult`

Transcribe audio y retorna resultado completo con metadata.

**Parámetros:**
- `audio_url` (str): URL del archivo de audio

**Returns:**
- `TranscriptionResult`: Resultado completo con metadata

**Raises:**
- `InvalidAudioSourceException`: URL inválida
- `TranscriptionTimeoutException`: Timeout excedido
- `ProviderUnavailableException`: Proveedor no disponible

**Ejemplo:**

```python
result = service.transcribe_with_metadata("https://example.com/meeting.mp3")

print(f"Text: {result.text}")
print(f"Success: {result.success}")
print(f"Confidence: {result.confidence}")
print(f"Duration: {result.duration_seconds}s")
print(f"Word count: {result.get_word_count()}")
print(f"High confidence: {result.is_high_confidence()}")
```

##### `get_metrics() -> Dict[str, Any]`

Retorna métricas del servicio.

**Returns:**
- `Dict[str, Any]`: Métricas de uso

**Ejemplo:**

```python
metrics = service.get_metrics()

print(f"Total attempts: {metrics['total_attempts']}")
print(f"Success rate: {metrics['success_rate']}")
print(f"Average duration: {metrics['average_duration']}s")
print(f"Provider: {metrics['provider']}")
print(f"Circuit breaker state: {metrics['circuit_breaker_state']}")
```

---

### TranscriptionServiceConfig

Configuración centralizada del servicio.

#### Constructor

```python
TranscriptionServiceConfig(
    provider: AudioTranscriptionProvider = None,
    circuit_breaker: CircuitBreakerProtocol = None,
    retry_strategy: RetryStrategy = None,
    max_retries: int = 3,
    transcription_timeout: int = 300,
    default_options: Dict[str, Any] = None,
    metrics_collector: TranscriptionMetricsCollector = None
)
```

**Parámetros:**

- `provider`: Proveedor de transcripción (DeepgramProvider, etc.)
- `circuit_breaker`: Circuit breaker para tolerancia a fallos
- `retry_strategy`: Estrategia de reintentos (Exponential, Linear, None)
- `max_retries`: Número máximo de reintentos (default: 3)
- `transcription_timeout`: Timeout en segundos (default: 300 = 5min)
- `default_options`: Opciones del proveedor
- `metrics_collector`: Collector de métricas personalizado

**Ejemplo:**

```python
from services import (
    TranscriptionServiceConfig,
    ExponentialBackoffStrategy,
    DeepgramProvider
)
from circuit_breaker import CircuitBreaker

config = TranscriptionServiceConfig(
    provider=DeepgramProvider(deepgram_client),
    circuit_breaker=CircuitBreaker(failure_threshold=3, timeout=60),
    retry_strategy=ExponentialBackoffStrategy(initial_delay=1.0, max_delay=60.0),
    max_retries=3,
    transcription_timeout=300,
    default_options={
        'model': 'nova-2',
        'language': 'es',
        'punctuate': True,
        'diarize': True
    }
)
```

---

### AudioSource

Value Object que representa una fuente de audio.

#### Constructor

```python
AudioSource(
    url: str,
    format: str = None,
    duration_hint: float = None,
    metadata: Dict[str, Any] = None
)
```

**Parámetros:**

- `url` (str): URL del archivo de audio (requerido)
- `format` (str, optional): Formato del audio (mp3, wav, etc.). Se infiere automáticamente
- `duration_hint` (float, optional): Duración aproximada en segundos
- `metadata` (Dict, optional): Metadata adicional

**Ejemplo:**

```python
from services import AudioSource

audio = AudioSource(
    url="https://example.com/meeting.mp3",
    format="mp3",
    duration_hint=1800.0,  # 30 minutos
    metadata={'meeting_id': 'MTG-123', 'language': 'es'}
)
```

---

### TranscriptionResult

Value Object que representa el resultado de una transcripción.

#### Atributos

```python
@dataclass
class TranscriptionResult:
    text: str                           # Texto transcrito
    success: bool = True                # Si fue exitosa
    confidence: float = 0.0             # Nivel de confianza (0.0 - 1.0)
    duration_seconds: float = 0.0       # Duración del audio
    metadata: Dict[str, Any] = None     # Metadata adicional
    timestamp: datetime = None          # Timestamp de la transcripción
    provider: str = None                # Proveedor usado
```

#### Métodos

##### `is_high_confidence(threshold: float = 0.8) -> bool`

Verifica si la transcripción tiene alta confianza.

**Parámetros:**
- `threshold` (float, optional): Umbral de confianza (default: 0.8)

**Returns:**
- `bool`: True si confidence >= threshold

**Ejemplo:**

```python
if result.is_high_confidence(threshold=0.85):
    print("Transcripción de alta calidad")
else:
    print("Revisar transcripción manualmente")
```

##### `get_word_count() -> int`

Retorna el número de palabras en la transcripción.

**Returns:**
- `int`: Número de palabras

**Ejemplo:**

```python
words = result.get_word_count()
print(f"Transcription contains {words} words")
```

##### `to_dict() -> Dict[str, Any]`

Convierte el resultado a diccionario.

**Returns:**
- `Dict[str, Any]`: Representación en diccionario

**Ejemplo:**

```python
data = result.to_dict()
# {
#   'text': '...',
#   'success': True,
#   'confidence': 0.95,
#   'word_count': 150,
#   'timestamp': '2024-12-06T17:00:00',
#   'provider': 'deepgram'
# }
```

---

### RetryStrategy

Estrategias de retry configurables.

#### ExponentialBackoffStrategy

Retry con backoff exponencial (recomendado).

```python
ExponentialBackoffStrategy(
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0
)
```

**Ejemplo:**

```python
from services import ExponentialBackoffStrategy

strategy = ExponentialBackoffStrategy(
    initial_delay=1.0,    # Primer retry: 1 segundo
    max_delay=60.0,       # Máximo: 60 segundos
    multiplier=2.0        # Cada retry duplica el delay
)

# Delays: 1s, 2s, 4s, 8s, 16s, 32s, 60s (max)
```

#### LinearBackoffStrategy

Retry con backoff lineal.

```python
LinearBackoffStrategy(
    delay_increment: float = 1.0,
    max_delay: float = 30.0
)
```

**Ejemplo:**

```python
from services import LinearBackoffStrategy

strategy = LinearBackoffStrategy(
    delay_increment=2.0,  # Incremento de 2 segundos
    max_delay=30.0
)

# Delays: 2s, 4s, 6s, 8s, ..., 30s (max)
```

#### NoRetryStrategy

Sin retry (falla inmediatamente).

```python
from services import NoRetryStrategy

strategy = NoRetryStrategy()
# No reintenta - útil para testing o casos específicos
```

---

## Configuración Avanzada

### Múltiples Proveedores con Fallback

```python
from services import (
    TranscriptionServiceV2,
    DeepgramProvider,
    TranscriptionServiceConfig
)

# Proveedor primario
primary_provider = DeepgramProvider(deepgram_client)

# Proveedor de fallback (ejemplo: Whisper)
# fallback_provider = WhisperProvider(whisper_client)

config = TranscriptionServiceConfig(
    provider=primary_provider,
    # Implementar lógica de fallback en capa superior si es necesario
)
```

### Configuración de Deepgram Personalizada

```python
config = TranscriptionServiceConfig(
    provider=DeepgramProvider(deepgram_client),
    default_options={
        'model': 'nova-2',           # Modelo de Deepgram
        'language': 'es',             # Idioma español
        'punctuate': True,            # Agregar puntuación
        'diarize': True,              # Detectar múltiples speakers
        'paragraphs': True,           # Separar en párrafos
        'utterances': True,           # Detectar utterances
        'smart_format': True,         # Formateo inteligente
        'profanity_filter': False,    # No filtrar groserías
        'redact': ['pii'],            # Redactar información personal
        'keywords': ['Python', 'TDD'] # Keywords importantes
    }
)
```

### Circuit Breaker Personalizado

```python
from circuit_breaker import CircuitBreaker

# Circuit Breaker agresivo (para desarrollo)
aggressive_cb = CircuitBreaker(
    failure_threshold=2,   # Abre tras 2 fallos
    timeout=30,            # Intenta recuperar en 30s
    expected_exception=Exception
)

# Circuit Breaker tolerante (para producción)
tolerant_cb = CircuitBreaker(
    failure_threshold=5,   # Abre tras 5 fallos
    timeout=120,           # Intenta recuperar en 2min
    expected_exception=Exception
)

config = TranscriptionServiceConfig(
    circuit_breaker=tolerant_cb
)
```

### Métricas Personalizadas

```python
from services import TranscriptionMetricsCollector, AudioSource
from typing import Dict, Any

class PrometheusMetricsCollector(TranscriptionMetricsCollector):
    """Collector que envía métricas a Prometheus."""
    
    def __init__(self, prometheus_client):
        self.client = prometheus_client
        self.transcription_counter = self.client.Counter(
            'transcriptions_total',
            'Total transcriptions'
        )
        self.transcription_duration = self.client.Histogram(
            'transcription_duration_seconds',
            'Transcription duration'
        )
    
    def record_transcription_attempt(self, audio_source: AudioSource):
        self.transcription_counter.inc()
    
    def record_transcription_success(self, duration_seconds: float, text_length: int):
        self.transcription_duration.observe(duration_seconds)
    
    def record_transcription_failure(self, error: Exception):
        self.transcription_counter.labels(status='failed').inc()
    
    def get_metrics(self) -> Dict[str, Any]:
        # Retornar métricas desde Prometheus
        return {}

# Usar en configuración
config = TranscriptionServiceConfig(
    metrics_collector=PrometheusMetricsCollector(prometheus_client)
)
```

---

## Ejemplos de Uso

### Ejemplo 1: Transcripción Simple

```python
from services import (
    TranscriptionServiceV2,
    DeepgramProvider,
    DeepgramResponseParser,
    TranscriptionServiceConfig
)
from circuit_breaker import CircuitBreaker

# Setup
provider = DeepgramProvider(deepgram_client)
parser = DeepgramResponseParser()
circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=60)

config = TranscriptionServiceConfig(
    provider=provider,
    circuit_breaker=circuit_breaker
)

service = TranscriptionServiceV2(config, parser)

# Uso
try:
    result = service.transcribe_with_metadata("https://example.com/meeting.mp3")
    
    if result.success and result.is_high_confidence():
        print(f"✅ Transcription successful: {result.text}")
        print(f"📊 Confidence: {result.confidence:.2%}")
    else:
        print("⚠️ Low confidence - manual review recommended")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
```

### Ejemplo 2: Batch Processing

```python
audio_urls = [
    "https://example.com/meeting1.mp3",
    "https://example.com/meeting2.mp3",
    "https://example.com/meeting3.mp3"
]

results = []

for url in audio_urls:
    try:
        result = service.transcribe_with_metadata(url)
        results.append(result)
        print(f"✅ Processed: {url}")
    except Exception as e:
        print(f"❌ Failed {url}: {str(e)}")
        results.append(None)

# Estadísticas
successful = sum(1 for r in results if r and r.success)
print(f"\n📊 Results: {successful}/{len(audio_urls)} successful")
```

### Ejemplo 3: Con Retry Strategy Personalizada

```python
from services import LinearBackoffStrategy

# Crear estrategia de retry lineal
retry_strategy = LinearBackoffStrategy(
    delay_increment=5.0,  # 5 segundos entre reintentos
    max_delay=60.0
)

config = TranscriptionServiceConfig(
    provider=provider,
    circuit_breaker=circuit_breaker,
    retry_strategy=retry_strategy,
    max_retries=5  # Hasta 5 intentos
)

service = TranscriptionServiceV2(config, parser)

result = service.transcribe_with_metadata("https://example.com/audio.mp3")
```

### Ejemplo 4: Monitoreo con Métricas

```python
# Procesar varios audios
for i in range(10):
    try:
        service.transcribe_with_metadata(f"https://example.com/audio{i}.mp3")
    except:
        pass

# Ver métricas
metrics = service.get_metrics()

print(f"""
📊 Transcription Service Metrics
================================
Total attempts: {metrics['total_attempts']}
Successful: {metrics['successful_transcriptions']}
Failed: {metrics['failed_transcriptions']}
Success rate: {metrics['success_rate']:.2%}
Average duration: {metrics['average_duration']:.2f}s
Provider: {metrics['provider']}
Circuit breaker: {metrics['circuit_breaker_state']}
""")
```

---

## Manejo de Errores

### Jerarquía de Excepciones

```
TranscriptionException (base)
├── InvalidAudioSourceException
├── TranscriptionTimeoutException
└── ProviderUnavailableException

CircuitBreakerOpenException (del circuit_breaker module)
```

### Manejo Recomendado

```python
from services import (
    InvalidAudioSourceException,
    TranscriptionTimeoutException,
    ProviderUnavailableException
)
from circuit_breaker import CircuitBreakerOpenException

try:
    result = service.transcribe_with_metadata(audio_url)
    
except InvalidAudioSourceException as e:
    # URL inválida - error del usuario
    print(f"❌ Invalid audio URL: {str(e)}")
    # Notificar al usuario para que corrija la URL
    
except TranscriptionTimeoutException as e:
    # Timeout excedido - audio muy largo
    print(f"⏱️ Transcription timeout: {str(e)}")
    # Dividir el audio en chunks más pequeños
    
except CircuitBreakerOpenException as e:
    # Circuit breaker abierto - servicio temporalmente no disponible
    print(f"🔌 Service temporarily unavailable: {str(e)}")
    # Usar fallback o encolar para procesar después
    
except ProviderUnavailableException as e:
    # Proveedor no disponible
    print(f"🚫 Provider unavailable: {str(e)}")
    # Intentar con proveedor alternativo si está configurado
    
except Exception as e:
    # Error inesperado
    print(f"💥 Unexpected error: {str(e)}")
    # Logging y alertas
```

---

## Mejores Prácticas

### 1. Configuración de Producción

```python
# ✅ RECOMENDADO para producción
config = TranscriptionServiceConfig(
    provider=DeepgramProvider(deepgram_client),
    circuit_breaker=CircuitBreaker(
        failure_threshold=5,
        timeout=120
    ),
    retry_strategy=ExponentialBackoffStrategy(
        initial_delay=2.0,
        max_delay=60.0
    ),
    max_retries=3,
    transcription_timeout=300,  # 5 minutos
    metrics_collector=PrometheusMetricsCollector()  # Usar Prometheus
)
```

### 2. Validación de Audio

```python
from services import AudioSource, AudioSourceValidator

validator = AudioSourceValidator()

# Validar antes de procesar
audio_source = AudioSource(url="https://example.com/audio.mp3")

try:
    validator.validate(audio_source)
    # Continuar con transcripción
except InvalidAudioSourceException as e:
    print(f"Invalid audio: {str(e)}")
```

### 3. Logging Estructurado

```python
import logging
import structlog

# Configurar structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Los servicios ya loguean automáticamente
result = service.transcribe_with_metadata(audio_url)
# Logs estructurados se generan automáticamente
```

### 4. Timeouts y RNF1.0

```python
# Para audios cortos (< 5 min)
config_short = TranscriptionServiceConfig(
    transcription_timeout=60  # 1 minuto
)

# Para audios largos (reuniones completas)
config_long = TranscriptionServiceConfig(
    transcription_timeout=300  # 5 minutos (RNF1.0)
)

# Para webinars/conferencias
config_webinar = TranscriptionServiceConfig(
    transcription_timeout=600  # 10 minutos
)
```

---

## Migración de V1 a V2

### Cambios Necesarios

#### Antes (V1)

```python
from services import TranscriptionService

service = TranscriptionService(
    deepgram_client=deepgram_client,
    circuit_breaker_config={'failure_threshold': 3, 'timeout': 60},
    max_retries=3
)

text = service.transcribe_audio("https://example.com/audio.mp3")
```

#### Después (V2)

```python
from services import (
    TranscriptionServiceV2,
    DeepgramProvider,
    DeepgramResponseParser,
    TranscriptionServiceConfig
)
from circuit_breaker import CircuitBreaker

# 1. Crear proveedor
provider = DeepgramProvider(deepgram_client)
parser = DeepgramResponseParser()

# 2. Crear circuit breaker explícito
circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=60)

# 3. Crear configuración
config = TranscriptionServiceConfig(
    provider=provider,
    circuit_breaker=circuit_breaker,
    max_retries=3
)

# 4. Crear servicio con DI
service = TranscriptionServiceV2(config, parser)

# 5. Usar (API compatible)
text = service.transcribe("https://example.com/audio.mp3")
```

### Beneficios de Migrar a V2

| Aspecto | V1 | V2 |
|---------|----|----|
| **Testabilidad** | Difícil (dependencias hardcodeadas) | Fácil (DI completa) |
| **Extensibilidad** | Limitada | Alta (Strategy Pattern) |
| **Mantenibilidad** | Media | Alta (SOLID aplicado) |
| **Observabilidad** | Básica | Avanzada (métricas separadas) |
| **Configurabilidad** | Limitada | Completa (Config object) |

---

## Apéndices

### A. Formatos de Audio Soportados

- ✅ MP3 (.mp3)
- ✅ WAV (.wav)
- ✅ M4A (.m4a)
- ✅ FLAC (.flac)
- ✅ OGG (.ogg)
- ✅ WEBM (.webm)

### B. Límites y Restricciones

- **Tamaño máximo**: Depende del proveedor (Deepgram: ~2GB)
- **Duración máxima**: 5 minutos (timeout configurable)
- **Rate limiting**: Según plan de Deepgram
- **Concurrencia**: Sin límite en el servicio (gestionar a nivel de aplicación)

### C. Performance

| Operación | Tiempo Típico |
|-----------|--------------|
| Transcripción (1 min audio) | ~5-10 segundos |
| Transcripción (5 min audio) | ~30-60 segundos |
| Validación de URL | < 1ms |
| Parsing de respuesta | < 10ms |

---

## Soporte y Contacto

- **Documentación del Proyecto**: `/docs`
- **Issues**: Reportar en el repositorio
- **Tests**: `pytest tests/test_transcription_service.py -v`

---

**Última actualización**: 2024-12-06  
**Versión del API**: 2.0  
**Estado**: ✅ Producción Ready

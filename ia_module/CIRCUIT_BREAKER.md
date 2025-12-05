# ✅ Circuit Breaker Pattern - Implementación RNF5.0

## 🎯 Descripción

Implementación completa del **Circuit Breaker Pattern** siguiendo metodología TDD y principios SOLID para el sistema M2PRD-001. Este patrón protege llamadas a servicios externos (Deepgram, OpenAI, APIs) detectando fallos y permitiendo recuperación automática.

## 📋 Requisitos Funcionales Cubiertos

- **RNF5.0**: Tolerancia a Fallos - El sistema debe recuperarse automáticamente de fallos en servicios externos
- **RNF1.0**: Performance - Evita sobrecarga en servicios caídos mediante apertura del circuito
- **RNF4.0**: Observabilidad - Proporciona métricas y logging para monitoreo

## 🔄 Estados del Circuit Breaker

```
┌─────────────┐
│   CLOSED    │ ◄──┐ ✅ Funcionamiento normal
│ (Normal)    │    │    Permite todas las llamadas
└──────┬──────┘    │
       │           │
       │ ≥ N fallos│ Éxito tras timeout
       │           │
       ▼           │
┌─────────────┐   │
│    OPEN     │   │ 🔴 Circuito abierto
│ (Rechazando)│   │    Rechaza llamadas inmediatamente
└──────┬──────┘   │
       │           │
       │ Timeout   │
       │ alcanzado │
       ▼           │
┌─────────────┐   │
│ HALF_OPEN   │───┘ 🟡 Probando recuperación
│ (Probando)  │      Permite llamadas limitadas
└─────────────┘
```

## 🧪 Tests TDD Implementados

✅ **15 tests pasando al 100%**

### Estados del Circuito
- `test_should_start_in_closed_state` - Inicio en CLOSED
- `test_should_allow_calls_when_circuit_is_closed` - Permitir llamadas
- `test_should_increment_failure_count_on_exception` - Contador de fallos
- `test_should_open_circuit_after_threshold_failures` - Apertura tras fallos
- `test_should_reject_calls_when_circuit_is_open` - Rechazo en OPEN
- `test_should_transition_to_half_open_after_timeout` - Transición a HALF_OPEN
- `test_should_reset_failure_count_on_success` - Reset tras éxito

### Configuración
- `test_should_accept_custom_failure_threshold` - Threshold personalizado
- `test_should_accept_custom_timeout` - Timeout personalizado
- `test_should_filter_exceptions_by_type` - Filtrado de excepciones

### Integración
- `test_should_protect_deepgram_api_calls` - Protección de APIs
- `test_should_track_last_failure_time` - Tracking de fallos

### Observabilidad
- `test_should_provide_state_information` - Información de estado
- `test_should_track_total_calls` - Tracking de llamadas
- `test_should_calculate_success_rate` - Tasa de éxito

## 🚀 Uso Básico

### 1. Importar Circuit Breaker

```python
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
```

### 2. Crear Instancia

```python
cb = CircuitBreaker(
    failure_threshold=3,  # Abrir tras 3 fallos consecutivos
    timeout=60,           # Esperar 60s antes de intentar recuperación
    expected_exception=ConnectionError  # Solo contar este tipo de excepciones
)
```

### 3. Proteger Llamadas

```python
try:
    result = cb.call(external_service.call, arg1, arg2)
    print(f"Success: {result}")
except CircuitBreakerOpenException:
    # Circuito abierto - usar fallback
    result = get_cached_response()
except ConnectionError as e:
    # Fallo real del servicio
    logger.error(f"Service failed: {e}")
```

## 🏭 Factory Pattern

Circuit Breakers preconfigurados para diferentes servicios:

```python
from circuit_breaker import CircuitBreakerFactory

# Para APIs de IA (Deepgram, OpenAI)
ai_cb = CircuitBreakerFactory.for_ai_services(
    failure_threshold=2,  # Baja tolerancia (costoso)
    timeout=120           # Mayor tiempo de recuperación
)

# Para APIs REST genéricas
api_cb = CircuitBreakerFactory.for_api_calls(
    failure_threshold=3,
    timeout=60
)

# Para bases de datos
db_cb = CircuitBreakerFactory.for_database(
    failure_threshold=5,  # Mayor tolerancia
    timeout=30            # Recuperación rápida
)
```

## 🎨 Decorador

Aplica Circuit Breaker automáticamente a funciones:

```python
from circuit_breaker import circuit_breaker

@circuit_breaker(failure_threshold=3, timeout=60)
def call_deepgram_api(audio_url):
    return deepgram_client.transcribe(audio_url)

# Uso normal - Circuit Breaker aplicado automáticamente
result = call_deepgram_api("audio.mp3")
```

## 📊 Monitoreo y Métricas

### Obtener Estado Actual

```python
state_info = cb.get_state_info()

print(f"Estado: {state_info['state']}")
print(f"Fallos: {state_info['failure_count']}/{state_info['failure_threshold']}")
print(f"Total llamadas: {state_info['total_calls']}")
print(f"Llamadas exitosas: {state_info['successful_calls']}")
print(f"Llamadas fallidas: {state_info['failed_calls']}")
```

### Calcular Tasa de Éxito

```python
success_rate = cb.get_success_rate()
print(f"Tasa de éxito: {success_rate * 100:.1f}%")
```

### Reset Manual

```python
# Útil para testing o recuperación forzada
cb.reset()
```

## 🔗 Integración con Servicios

### Ejemplo: Proteger Deepgram API

```python
from config import settings
from circuit_breaker import CircuitBreakerFactory

class TranscriptionService:
    def __init__(self):
        self.deepgram_client = DeepgramClient(settings.deepgram_api_key)
        self.circuit_breaker = CircuitBreakerFactory.for_ai_services()
    
    def transcribe(self, audio_url: str) -> str:
        try:
            result = self.circuit_breaker.call(
                self.deepgram_client.transcription.prerecorded,
                {'url': audio_url},
                {'model': 'nova-2', 'language': 'es'}
            )
            return result['results']['channels'][0]['alternatives'][0]['transcript']
        
        except CircuitBreakerOpenException:
            logger.error("Deepgram circuit is OPEN - using fallback")
            return self._get_fallback_transcription(audio_url)
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
```

### Ejemplo: Proteger OpenAI API

```python
class RequirementExtractionService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.circuit_breaker = CircuitBreakerFactory.for_ai_services()
    
    def extract_requirements(self, transcription: str) -> List[Requirement]:
        try:
            result = self.circuit_breaker.call(
                self.openai_client.chat.completions.create,
                model="gpt-4",
                messages=[{"role": "user", "content": transcription}]
            )
            return self._parse_requirements(result)
        
        except CircuitBreakerOpenException:
            logger.error("OpenAI circuit is OPEN - using spaCy fallback")
            return self._extract_with_spacy(transcription)
```

## 🧪 Ejecutar Tests

```bash
# Todos los tests del Circuit Breaker
cd ia_module
python -m pytest tests/test_circuit_breaker.py -v

# Con cobertura
python -m pytest tests/test_circuit_breaker.py -v --cov=circuit_breaker --cov-report=html

# Tests específicos
python -m pytest tests/test_circuit_breaker.py::TestCircuitBreakerStates -v
```

## 📖 Ejemplos Completos

Ejecutar ejemplos interactivos:

```bash
cd ia_module/examples
python circuit_breaker_example.py
```

Ejemplos incluidos:
- 📘 Uso básico con llamadas exitosas y fallidas
- 📗 Factory Pattern para diferentes servicios
- 📙 Uso con decorador `@circuit_breaker`
- 📕 Recuperación automática de circuito
- 📊 Monitoreo y métricas en tiempo real

## 🏗️ Arquitectura

### Principios SOLID Aplicados

- **S**ingle Responsibility: Circuit Breaker solo maneja tolerancia a fallos
- **O**pen/Closed: Extensible mediante Factory sin modificar código base
- **L**iskov Substitution: Factory methods retornan Circuit Breakers intercambiables
- **I**nterface Segregation: API mínima y cohesiva
- **D**ependency Inversion: Inyección de configuración mediante constructor

### Clean Architecture

```
┌─────────────────────────────────────────┐
│ Domain Layer                            │
│ - CircuitBreaker (core logic)           │
│ - CircuitState (estados)                │
│ - CircuitBreakerOpenException           │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│ Application Layer                       │
│ - CircuitBreakerFactory                 │
│ - @circuit_breaker decorator            │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│ Infrastructure Layer                    │
│ - TranscriptionService                  │
│ - RequirementExtractionService          │
│ - External API integrations             │
└─────────────────────────────────────────┘
```

## 📈 Métricas y Observabilidad

El Circuit Breaker trackea automáticamente:

- ✅ Total de llamadas realizadas
- ✅ Llamadas exitosas vs fallidas
- ✅ Tasa de éxito porcentual
- ✅ Contador de fallos consecutivos
- ✅ Timestamp del último fallo
- ✅ Estado actual del circuito
- ✅ Transiciones de estado (via logging)

## 🔒 Configuración desde Config.py

Integración con configuración centralizada:

```python
from config import settings

cb = CircuitBreaker(
    failure_threshold=settings.circuit_breaker_failure_threshold,
    timeout=settings.circuit_breaker_timeout_seconds,
    expected_exception=ConnectionError
)
```

Variables en `.env`:
```bash
CB_FAILURE_THRESHOLD=3
CB_TIMEOUT_SECONDS=60
CB_RECOVERY_TIMEOUT=30
```

## ✨ Características Destacadas

- ✅ **TDD Completo**: 15 tests, 100% de cobertura
- ✅ **SOLID Principles**: Código mantenible y extensible
- ✅ **Factory Pattern**: Circuit Breakers preconfigurados
- ✅ **Decorator Support**: Aplicación automática con `@circuit_breaker`
- ✅ **Métricas Built-in**: Observabilidad completa
- ✅ **Logging Estructurado**: Integración con structlog
- ✅ **Configurable**: Thresholds y timeouts ajustables
- ✅ **Type-Safe**: Type hints completos
- ✅ **Documentado**: Docstrings y ejemplos extensos

## 📝 Próximas Mejoras

- [ ] Integración con Prometheus para métricas
- [ ] Dashboard de monitoreo en tiempo real
- [ ] Circuit Breaker distribuido con Redis
- [ ] Políticas de retry avanzadas
- [ ] Fallback strategies configurables
- [ ] Health checks automáticos

---

**Desarrollado con ❤️ siguiendo TDD y Clean Architecture**

*Última actualización: 2025-12-05*

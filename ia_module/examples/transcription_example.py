#!/usr/bin/env python3
"""
🚀 Ejemplo Ejecutable - TranscriptionService

Este script demuestra el uso completo del TranscriptionService con diferentes
escenarios y configuraciones.

Uso:
    python examples/transcription_example.py
"""

import sys
import os

# Añadir path del módulo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock
from services import (
    # V2 Refactorizado (recomendado)
    TranscriptionServiceV2,
    DeepgramProvider,
    DeepgramResponseParser,
    TranscriptionServiceConfig,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    # V1 Legacy (backward compatibility)
    TranscriptionService,
)
from circuit_breaker import CircuitBreaker


# ================================================================================================
# 🎯 Mock Data - Simulación de respuestas de Deepgram
# ================================================================================================

def create_mock_deepgram_client():
    """Crea un cliente Deepgram mockeado para testing."""
    mock_client = Mock()
    
    # Respuesta de éxito
    mock_client.transcription.prerecorded.return_value = {
        'results': {
            'channels': [{
                'alternatives': [{
                    'transcript': 'En esta reunión discutimos los requisitos del nuevo módulo de autenticación. Necesitamos implementar login con JWT, recuperación de contraseña por email, y autenticación de dos factores. El sistema debe soportar hasta 10,000 usuarios concurrentes.',
                    'confidence': 0.95
                }]
            }]
        },
        'metadata': {
            'duration': 180.0,
            'channels': 1,
            'model': 'nova-2'
        }
    }
    
    return mock_client


# ================================================================================================
# 📊 Ejemplo 1: Uso Básico (V1 Legacy)
# ================================================================================================

def example_1_basic_v1():
    """
    Ejemplo 1: Uso básico del servicio (V1 - backward compatibility).
    
    Este es el método legacy pero aún soportado.
    """
    print("\n" + "="*80)
    print("📊 EJEMPLO 1: Uso Básico (V1 - Legacy)")
    print("="*80)
    
    # Crear cliente mockeado
    deepgram_client = create_mock_deepgram_client()
    
    # Crear servicio (versión legacy)
    service = TranscriptionService(deepgram_client=deepgram_client)
    
    # Transcribir audio
    audio_url = "https://example.com/meeting_recording.mp3"
    
    try:
        print(f"\n🎤 Transcribiendo: {audio_url}")
        text = service.transcribe_audio(audio_url)
        
        print(f"\n✅ Transcripción exitosa!")
        print(f"📝 Texto transcrito:")
        print(f"   {text[:200]}...")
        
        # Ver métricas
        metrics = service.get_metrics()
        print(f"\n📊 Métricas:")
        print(f"   Total transcripciones: {metrics['total_transcriptions']}")
        print(f"   Exitosas: {metrics['successful_transcriptions']}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


# ================================================================================================
# 🔥 Ejemplo 2: Uso Avanzado (V2 Refactorizado)
# ================================================================================================

def example_2_advanced_v2():
    """
    Ejemplo 2: Uso avanzado con V2 (arquitectura refactorizada).
    
    Demuestra todas las características: Circuit Breaker, Retry, Métricas.
    """
    print("\n" + "="*80)
    print("🔥 EJEMPLO 2: Uso Avanzado (V2 - Refactorizado)")
    print("="*80)
    
    # 1. Crear cliente mockeado
    deepgram_client = create_mock_deepgram_client()
    
    # 2. Configurar proveedor
    provider = DeepgramProvider(deepgram_client)
    parser = DeepgramResponseParser()
    
    # 3. Configurar Circuit Breaker
    circuit_breaker = CircuitBreaker(
        failure_threshold=3,
        timeout=60,
        expected_exception=Exception
    )
    
    # 4. Configurar estrategia de retry
    retry_strategy = ExponentialBackoffStrategy(
        initial_delay=1.0,
        max_delay=60.0,
        multiplier=2.0
    )
    
    # 5. Crear configuración completa
    config = TranscriptionServiceConfig(
        provider=provider,
        circuit_breaker=circuit_breaker,
        retry_strategy=retry_strategy,
        max_retries=3,
        transcription_timeout=300,
        default_options={
            'model': 'nova-2',
            'language': 'es',
            'punctuate': True,
            'diarize': True
        }
    )
    
    # 6. Crear servicio con DI
    service = TranscriptionServiceV2(config, parser)
    
    # 7. Transcribir con metadata completa
    audio_url = "https://example.com/project_meeting.mp3"
    
    try:
        print(f"\n🎤 Transcribiendo con metadata: {audio_url}")
        result = service.transcribe_with_metadata(audio_url)
        
        print(f"\n✅ Transcripción completada!")
        print(f"\n📝 Resultado:")
        print(f"   Texto: {result.text[:150]}...")
        print(f"   Confianza: {result.confidence:.2%}")
        print(f"   Duración: {result.duration_seconds}s")
        print(f"   Palabras: {result.get_word_count()}")
        print(f"   Alta confianza: {'Sí' if result.is_high_confidence() else 'No'}")
        print(f"   Proveedor: {result.provider}")
        
        # Ver métricas detalladas
        metrics = service.get_metrics()
        print(f"\n📊 Métricas del Servicio:")
        print(f"   Total intentos: {metrics['total_attempts']}")
        print(f"   Exitosas: {metrics['successful_transcriptions']}")
        print(f"   Fallidas: {metrics['failed_transcriptions']}")
        print(f"   Tasa de éxito: {metrics['success_rate']:.2%}")
        print(f"   Duración promedio: {metrics['average_duration']:.2f}s")
        print(f"   Proveedor: {metrics['provider']}")
        print(f"   Circuit Breaker: {metrics['circuit_breaker_state']}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


# ================================================================================================
# 🔄 Ejemplo 3: Batch Processing
# ================================================================================================

def example_3_batch_processing():
    """
    Ejemplo 3: Procesamiento por lotes de múltiples audios.
    
    Simula el procesamiento de varias reuniones.
    """
    print("\n" + "="*80)
    print("🔄 EJEMPLO 3: Batch Processing")
    print("="*80)
    
    # Setup servicio
    deepgram_client = create_mock_deepgram_client()
    provider = DeepgramProvider(deepgram_client)
    parser = DeepgramResponseParser()
    
    config = TranscriptionServiceConfig(
        provider=provider,
        circuit_breaker=CircuitBreaker(failure_threshold=3, timeout=60)
    )
    
    service = TranscriptionServiceV2(config, parser)
    
    # Lista de audios a procesar
    audio_urls = [
        "https://example.com/daily_standup_monday.mp3",
        "https://example.com/sprint_planning.mp3",
        "https://example.com/retrospective.mp3",
        "https://example.com/client_meeting.mp3",
    ]
    
    print(f"\n📋 Procesando {len(audio_urls)} audios...")
    
    results = []
    for i, url in enumerate(audio_urls, 1):
        try:
            print(f"\n[{i}/{len(audio_urls)}] Procesando: {url.split('/')[-1]}")
            result = service.transcribe_with_metadata(url)
            results.append(result)
            print(f"   ✅ Exitoso - {result.get_word_count()} palabras, {result.confidence:.2%} confianza")
            
        except Exception as e:
            print(f"   ❌ Falló: {str(e)}")
            results.append(None)
    
    # Estadísticas finales
    successful = sum(1 for r in results if r and r.success)
    total_words = sum(r.get_word_count() for r in results if r and r.success)
    avg_confidence = sum(r.confidence for r in results if r and r.success) / successful if successful > 0 else 0
    
    print(f"\n📊 Resumen del Batch:")
    print(f"   Total audios: {len(audio_urls)}")
    print(f"   Exitosos: {successful}")
    print(f"   Fallidos: {len(audio_urls) - successful}")
    print(f"   Total palabras: {total_words}")
    print(f"   Confianza promedio: {avg_confidence:.2%}")


# ================================================================================================
# ⚙️ Ejemplo 4: Configuraciones Personalizadas
# ================================================================================================

def example_4_custom_configurations():
    """
    Ejemplo 4: Diferentes configuraciones para diferentes escenarios.
    
    Muestra cómo adaptar la configuración según el caso de uso.
    """
    print("\n" + "="*80)
    print("⚙️ EJEMPLO 4: Configuraciones Personalizadas")
    print("="*80)
    
    deepgram_client = create_mock_deepgram_client()
    provider = DeepgramProvider(deepgram_client)
    parser = DeepgramResponseParser()
    
    # Configuración 1: Para audios cortos (< 5 min)
    print("\n1️⃣ Configuración para audios cortos:")
    config_short = TranscriptionServiceConfig(
        provider=provider,
        circuit_breaker=CircuitBreaker(failure_threshold=2, timeout=30),
        retry_strategy=ExponentialBackoffStrategy(initial_delay=0.5, max_delay=10.0),
        max_retries=2,
        transcription_timeout=60,  # 1 minuto
        default_options={'model': 'nova-2', 'language': 'es'}
    )
    print("   ✅ Timeout: 60s, Max retries: 2, Circuit breaker agresivo")
    
    # Configuración 2: Para reuniones largas
    print("\n2️⃣ Configuración para reuniones largas:")
    config_long = TranscriptionServiceConfig(
        provider=provider,
        circuit_breaker=CircuitBreaker(failure_threshold=5, timeout=120),
        retry_strategy=LinearBackoffStrategy(delay_increment=5.0, max_delay=60.0),
        max_retries=5,
        transcription_timeout=600,  # 10 minutos
        default_options={
            'model': 'nova-2',
            'language': 'es',
            'punctuate': True,
            'diarize': True,
            'paragraphs': True
        }
    )
    print("   ✅ Timeout: 600s, Max retries: 5, Circuit breaker tolerante")
    
    # Configuración 3: Para producción
    print("\n3️⃣ Configuración de producción:")
    config_production = TranscriptionServiceConfig(
        provider=provider,
        circuit_breaker=CircuitBreaker(failure_threshold=5, timeout=120),
        retry_strategy=ExponentialBackoffStrategy(initial_delay=2.0, max_delay=60.0),
        max_retries=3,
        transcription_timeout=300,
        default_options={
            'model': 'nova-2',
            'language': 'es',
            'punctuate': True,
            'diarize': True,
            'smart_format': True
        }
    )
    print("   ✅ Configuración balanceada para producción")
    
    # Usar configuración de producción
    service = TranscriptionServiceV2(config_production, parser)
    
    try:
        result = service.transcribe_with_metadata("https://example.com/audio.mp3")
        print(f"\n✅ Transcripción con config de producción exitosa!")
        print(f"   Confianza: {result.confidence:.2%}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


# ================================================================================================
# 🔍 Ejemplo 5: Manejo de Errores
# ================================================================================================

def example_5_error_handling():
    """
    Ejemplo 5: Manejo adecuado de diferentes tipos de errores.
    
    Muestra cómo manejar cada tipo de excepción del servicio.
    """
    print("\n" + "="*80)
    print("🔍 EJEMPLO 5: Manejo de Errores")
    print("="*80)
    
    from services import (
        InvalidAudioSourceException,
        TranscriptionTimeoutException,
        ProviderUnavailableException
    )
    from circuit_breaker import CircuitBreakerOpenException
    
    deepgram_client = create_mock_deepgram_client()
    provider = DeepgramProvider(deepgram_client)
    parser = DeepgramResponseParser()
    
    config = TranscriptionServiceConfig(
        provider=provider,
        circuit_breaker=CircuitBreaker(failure_threshold=3, timeout=60)
    )
    
    service = TranscriptionServiceV2(config, parser)
    
    # Caso 1: URL inválida
    print("\n1️⃣ Probando URL inválida:")
    try:
        service.transcribe_with_metadata("not-a-valid-url")
    except InvalidAudioSourceException as e:
        print(f"   ✅ Capturado correctamente: {type(e).__name__}")
        print(f"   📝 Mensaje: {str(e)}")
    
    # Caso 2: URL válida pero con formato no soportado
    print("\n2️⃣ Probando formato de URL válido:")
    try:
        result = service.transcribe_with_metadata("https://example.com/audio.mp3")
        print(f"   ✅ Transcripción exitosa: {result.success}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Caso 3: Simulación de timeout
    print("\n3️⃣ Información sobre timeouts:")
    print(f"   ⏱️  Timeout configurado: {config.transcription_timeout}s")
    print(f"   💡 Para audios largos, aumentar el timeout en la configuración")
    
    print("\n✅ Todos los escenarios de error manejados correctamente!")


# ================================================================================================
# 🎬 Main - Ejecutar todos los ejemplos
# ================================================================================================

def main():
    """Ejecuta todos los ejemplos en secuencia."""
    
    print("\n" + "🎬" * 40)
    print("🚀 EJEMPLOS EJECUTABLES - TranscriptionService")
    print("="*80)
    print("\nEste script demuestra el uso completo del TranscriptionService")
    print("con diferentes escenarios, configuraciones y casos de uso.")
    print("🎬" * 40)
    
    try:
        # Ejecutar ejemplos
        example_1_basic_v1()
        example_2_advanced_v2()
        example_3_batch_processing()
        example_4_custom_configurations()
        example_5_error_handling()
        
        # Resumen final
        print("\n" + "="*80)
        print("🎉 TODOS LOS EJEMPLOS COMPLETADOS EXITOSAMENTE")
        print("="*80)
        print("\n📚 Para más información, consulta:")
        print("   - Documentación: services/TRANSCRIPTION_API.md")
        print("   - Tests: tests/test_transcription_service.py")
        print("   - Código fuente: services/transcription_service_v2.py")
        
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

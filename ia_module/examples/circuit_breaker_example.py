"""
✅ Ejemplo de Uso del Circuit Breaker Pattern

Demuestra cómo usar el Circuit Breaker para proteger llamadas a servicios externos
como Deepgram API, OpenAI API, etc.
"""

import sys
sys.path.append('..')

from circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    CircuitBreakerFactory,
    circuit_breaker
)
import time


# ================================================================================================
# 📘 EJEMPLO 1: Uso Básico del Circuit Breaker
# ================================================================================================

def example_basic_usage():
    """Ejemplo básico de Circuit Breaker."""
    print("\n" + "="*80)
    print("📘 EJEMPLO 1: Uso Básico del Circuit Breaker")
    print("="*80)
    
    # Crear Circuit Breaker
    cb = CircuitBreaker(failure_threshold=3, timeout=5)
    
    # Simular servicio externo
    def external_api_call(should_fail=False):
        if should_fail:
            raise ConnectionError("API is down")
        return {"status": "success", "data": "some data"}
    
    # Llamadas exitosas
    print("\n✅ Llamadas exitosas:")
    for i in range(3):
        try:
            result = cb.call(external_api_call, should_fail=False)
            print(f"  Call {i+1}: {result}")
        except Exception as e:
            print(f"  Call {i+1}: Error - {e}")
    
    print(f"\nEstado del circuito: {cb.state}")
    print(f"Fallos: {cb.failure_count}/{cb.failure_threshold}")
    
    # Forzar fallos
    print("\n❌ Forzando fallos:")
    for i in range(4):
        try:
            result = cb.call(external_api_call, should_fail=True)
        except CircuitBreakerOpenException as e:
            print(f"  Call {i+1}: 🔴 Circuit OPEN - {e}")
        except ConnectionError as e:
            print(f"  Call {i+1}: 💥 Connection Error")
    
    print(f"\nEstado final: {cb.state}")
    print(f"Métricas: {cb.get_state_info()}")


# ================================================================================================
# 📗 EJEMPLO 2: Uso con Factory Pattern
# ================================================================================================

def example_factory_pattern():
    """Ejemplo usando Factory para diferentes servicios."""
    print("\n" + "="*80)
    print("📗 EJEMPLO 2: Circuit Breaker Factory Pattern")
    print("="*80)
    
    # Circuit Breaker optimizado para APIs de IA
    ai_circuit = CircuitBreakerFactory.for_ai_services()
    
    def deepgram_transcribe(audio_url):
        # Simular llamada a Deepgram
        print(f"  🎙️  Transcribiendo {audio_url}...")
        time.sleep(0.1)
        return "Transcripción de prueba"
    
    print("\n🤖 Usando Circuit Breaker para servicios de IA:")
    print(f"  - Failure threshold: {ai_circuit.failure_threshold}")
    print(f"  - Timeout: {ai_circuit.timeout}s")
    
    try:
        result = ai_circuit.call(deepgram_transcribe, "audio.mp3")
        print(f"  ✅ Resultado: {result}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print(f"\nTasa de éxito: {ai_circuit.get_success_rate() * 100:.1f}%")


# ================================================================================================
# 📙 EJEMPLO 3: Uso con Decorador
# ================================================================================================

@circuit_breaker(failure_threshold=2, timeout=10)
def call_openai_api(prompt):
    """Función decorada con Circuit Breaker."""
    print(f"  🧠 Llamando a OpenAI con prompt: {prompt[:50]}...")
    time.sleep(0.1)
    return {"response": "Mock GPT-4 response"}


def example_decorator_usage():
    """Ejemplo usando el decorador de Circuit Breaker."""
    print("\n" + "="*80)
    print("📙 EJEMPLO 3: Uso con Decorador @circuit_breaker")
    print("="*80)
    
    print("\n🎯 Función decorada automáticamente:")
    
    try:
        result = call_openai_api("Extract requirements from this text...")
        print(f"  ✅ Respuesta: {result}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


# ================================================================================================
# 📕 EJEMPLO 4: Recuperación Automática
# ================================================================================================

def example_automatic_recovery():
    """Ejemplo de recuperación automática del circuito."""
    print("\n" + "="*80)
    print("📕 EJEMPLO 4: Recuperación Automática del Circuito")
    print("="*80)
    
    cb = CircuitBreaker(failure_threshold=2, timeout=2)  # Timeout corto para demo
    
    call_count = [0]  # Usar lista para modificar en inner function
    
    def flaky_service():
        """Servicio que falla las primeras veces, luego funciona."""
        call_count[0] += 1
        if call_count[0] <= 3:
            raise ConnectionError(f"Service down (attempt {call_count[0]})")
        return "Service recovered!"
    
    print("\n🔄 Simulando servicio intermitente:")
    
    for i in range(6):
        try:
            result = cb.call(flaky_service)
            print(f"  Call {i+1}: ✅ {result}")
        except CircuitBreakerOpenException:
            print(f"  Call {i+1}: 🔴 Circuit OPEN - Esperando...")
        except ConnectionError as e:
            print(f"  Call {i+1}: 💥 {e}")
        
        # Mostrar estado
        state_info = cb.get_state_info()
        print(f"    Estado: {state_info['state'].value}, Fallos: {state_info['failure_count']}")
        
        # Esperar un poco para permitir recuperación
        if i == 2:
            print("\n  ⏰ Esperando timeout para recuperación...")
            time.sleep(2.5)


# ================================================================================================
# 📊 EJEMPLO 5: Monitoreo y Métricas
# ================================================================================================

def example_monitoring_metrics():
    """Ejemplo de monitoreo y métricas del Circuit Breaker."""
    print("\n" + "="*80)
    print("📊 EJEMPLO 5: Monitoreo y Métricas")
    print("="*80)
    
    cb = CircuitBreaker(failure_threshold=5)
    
    def unreliable_service():
        import random
        if random.random() < 0.3:  # 30% de probabilidad de fallo
            raise ConnectionError("Random failure")
        return "Success"
    
    print("\n📈 Ejecutando 20 llamadas a servicio no confiable:")
    
    for i in range(20):
        try:
            cb.call(unreliable_service)
        except (ConnectionError, CircuitBreakerOpenException):
            pass
    
    # Mostrar métricas finales
    print("\n📊 Métricas finales:")
    metrics = cb.get_state_info()
    print(f"  • Total de llamadas: {metrics['total_calls']}")
    print(f"  • Llamadas exitosas: {metrics['successful_calls']}")
    print(f"  • Llamadas fallidas: {metrics['failed_calls']}")
    print(f"  • Tasa de éxito: {cb.get_success_rate() * 100:.1f}%")
    print(f"  • Estado final: {metrics['state'].value}")
    print(f"  • Contador de fallos: {metrics['failure_count']}/{metrics['failure_threshold']}")


# ================================================================================================
# 🚀 EJECUTAR TODOS LOS EJEMPLOS
# ================================================================================================

if __name__ == "__main__":
    print("\n" + "🔴🟡🟢" * 20)
    print("CIRCUIT BREAKER PATTERN - EJEMPLOS DE USO")
    print("🔴🟡🟢" * 20)
    
    example_basic_usage()
    example_factory_pattern()
    example_decorator_usage()
    example_automatic_recovery()
    example_monitoring_metrics()
    
    print("\n" + "="*80)
    print("✅ Todos los ejemplos ejecutados correctamente")
    print("="*80 + "\n")

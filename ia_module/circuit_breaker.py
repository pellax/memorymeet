"""
✅ Circuit Breaker Pattern Implementation (RNF5.0 - Tolerancia a Fallos)

Implementación del patrón Circuit Breaker para proteger llamadas a servicios externos.
Fase GREEN del ciclo TDD: código mínimo que hace pasar los tests.
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Type
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ================================================================================================
# 🟢 GREEN PHASE - Implementación mínima que pasa los tests
# ================================================================================================

class CircuitState(Enum):
    """
    Estados del Circuit Breaker.
    
    - CLOSED: Circuito cerrado, operación normal
    - OPEN: Circuito abierto, rechaza llamadas
    - HALF_OPEN: Circuito semi-abierto, probando recuperación
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenException(Exception):
    """
    Excepción lanzada cuando se intenta llamar con el circuito abierto.
    """
    pass


@dataclass
class CircuitBreakerConfig:
    """Configuración del Circuit Breaker."""
    failure_threshold: int = 3
    timeout: int = 60  # segundos
    expected_exception: Type[Exception] = Exception


class CircuitBreaker:
    """
    ✅ Circuit Breaker - Implementación del patrón para tolerancia a fallos.
    
    Protege llamadas a servicios externos detectando fallos y abriendo el circuito
    temporalmente para permitir recuperación del servicio.
    
    Estados:
    - CLOSED: Funcionamiento normal
    - OPEN: Rechaza llamadas tras múltiples fallos
    - HALF_OPEN: Prueba recuperación con llamadas limitadas
    
    Ejemplo:
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        
        try:
            result = cb.call(external_service.call, arg1, arg2)
        except CircuitBreakerOpenException:
            # Circuito abierto, usar fallback
            result = fallback_response()
    """
    
    def __init__(
        self,
        failure_threshold: int = 3,
        timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Inicializa el Circuit Breaker.
        
        Args:
            failure_threshold: Número de fallos consecutivos antes de abrir el circuito
            timeout: Tiempo en segundos antes de intentar cerrar el circuito
            expected_exception: Tipo de excepción que activa el circuito
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        # Estado interno
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        
        # Métricas
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        ✅ Ejecuta una función protegida por el Circuit Breaker.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
        
        Returns:
            El resultado de la función si tiene éxito
        
        Raises:
            CircuitBreakerOpenException: Si el circuito está abierto
            Exception: La excepción original si la llamada falla
        """
        self.total_calls += 1
        
        # Verificar si debemos intentar recuperación
        if self.state == CircuitState.OPEN:
            # Si no hay timestamp de fallo, es un estado forzado - no intentar reset
            if self.last_failure_time is not None and self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit is OPEN. Last failure: {self.last_failure_time}"
                )
        
        # Intentar ejecutar la función
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            # Solo contar fallos del tipo esperado
            if isinstance(e, self.expected_exception):
                self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """
        Verifica si debe intentar resetear el circuito.
        
        Returns:
            True si ha pasado el timeout desde el último fallo
        """
        if self.last_failure_time is None:
            return True
        
        time_since_last_failure = time.time() - self.last_failure_time
        return time_since_last_failure >= self.timeout
    
    def _on_success(self) -> None:
        """
        Maneja una llamada exitosa.
        
        - Resetea contador de fallos
        - Cierra el circuito si estaba abierto
        - Incrementa métricas de éxito
        """
        self.failure_count = 0
        self.successful_calls += 1
        
        if self.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker recovering: {self.state} → CLOSED")
            self.state = CircuitState.CLOSED
    
    def _on_failure(self) -> None:
        """
        Maneja una llamada fallida.
        
        - Incrementa contador de fallos
        - Abre el circuito si alcanza el umbral
        - Registra el timestamp del fallo
        - Incrementa métricas de fallo
        """
        self.failure_count += 1
        self.failed_calls += 1
        self.last_failure_time = time.time()
        
        logger.warning(
            f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}"
        )
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker OPENED after {self.failure_count} failures"
            )
    
    def get_state_info(self) -> dict:
        """
        ✅ Retorna información del estado actual del Circuit Breaker.
        
        Returns:
            Diccionario con información del estado y métricas
        """
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "timeout": self.timeout,
            "last_failure_time": self.last_failure_time,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls
        }
    
    def get_success_rate(self) -> float:
        """
        ✅ Calcula la tasa de éxito de las llamadas.
        
        Returns:
            Tasa de éxito entre 0.0 y 1.0
        """
        if self.total_calls == 0:
            return 0.0
        
        return self.successful_calls / self.total_calls
    
    def reset(self) -> None:
        """
        Resetea el Circuit Breaker al estado inicial.
        
        Útil para testing o recuperación manual.
        """
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")


# ================================================================================================
# 🎯 DECORADOR PARA CIRCUIT BREAKER
# ================================================================================================

def circuit_breaker(
    failure_threshold: int = 3,
    timeout: int = 60,
    expected_exception: Type[Exception] = Exception
):
    """
    ✅ Decorador que aplica Circuit Breaker a una función.
    
    Uso:
        @circuit_breaker(failure_threshold=3, timeout=60)
        def call_external_api(url):
            return requests.get(url)
    
    Args:
        failure_threshold: Número de fallos antes de abrir el circuito
        timeout: Tiempo de espera antes de intentar recuperación
        expected_exception: Tipo de excepción que activa el circuito
    """
    cb = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout,
        expected_exception=expected_exception
    )
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator


# ================================================================================================
# 🏭 FACTORY PARA CIRCUIT BREAKERS
# ================================================================================================

class CircuitBreakerFactory:
    """
    ✅ Factory para crear Circuit Breakers con configuraciones predefinidas.
    
    Facilita la creación de Circuit Breakers para diferentes servicios.
    """
    
    @staticmethod
    def for_api_calls(failure_threshold: int = 3, timeout: int = 60) -> CircuitBreaker:
        """
        Circuit Breaker optimizado para llamadas a APIs externas.
        
        Args:
            failure_threshold: Número de fallos antes de abrir
            timeout: Tiempo antes de intentar recuperación
        
        Returns:
            CircuitBreaker configurado para APIs
        """
        return CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            expected_exception=(ConnectionError, TimeoutError)
        )
    
    @staticmethod
    def for_database(failure_threshold: int = 5, timeout: int = 30) -> CircuitBreaker:
        """
        Circuit Breaker optimizado para operaciones de base de datos.
        
        Mayor tolerancia a fallos y menor timeout para recuperación rápida.
        """
        return CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            expected_exception=Exception
        )
    
    @staticmethod
    def for_ai_services(failure_threshold: int = 2, timeout: int = 120) -> CircuitBreaker:
        """
        Circuit Breaker optimizado para servicios de IA (Deepgram, OpenAI).
        
        Menor tolerancia a fallos (más costoso) y mayor timeout (recuperación lenta).
        """
        return CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            expected_exception=(ConnectionError, TimeoutError, Exception)
        )

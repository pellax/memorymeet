# ================================================================================================
# 🔒 SUBSCRIPTION CONSUMPTION SERVICE - EL GATEKEEPER (RF8.0 CRITICAL)
# ================================================================================================
# Servicio de dominio que implementa la lógica crítica de control de consumo
# Este es el COMPONENTE MÁS IMPORTANTE del sistema SaaS

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from ..entities.user import User
from ..entities.subscription import Subscription, SubscriptionStatus
from ..exceptions.consumption_exceptions import (
    InsufficientHoursException,
    SubscriptionNotFoundException,
    UserNotFoundException,
    InvalidConsumptionException,
    SubscriptionSuspendedException
)
from ..repositories.subscription_repository import SubscriptionRepository, UserRepository


@dataclass
class ConsumptionVerificationResult:
    """
    📊 Resultado de la verificación de consumo.
    
    Value Object que encapsula el resultado de verificar si un usuario
    puede consumir horas para procesamiento.
    """
    can_consume: bool
    user: User
    subscription: Subscription
    remaining_hours: float
    consumption_percentage: float
    
    def is_near_limit(self, threshold: float = 80.0) -> bool:
        """Verificar si está cerca del límite."""
        return self.consumption_percentage >= threshold


@dataclass
class ConsumptionResult:
    """
    💰 Resultado del consumo de horas.
    
    Value Object que encapsula el resultado de consumir horas.
    """
    success: bool
    updated_subscription: Subscription
    consumed_hours: float
    remaining_hours: float
    transaction_id: Optional[str] = None


class SubscriptionConsumptionService:
    """
    🔒 GATEKEEPER SERVICE - Servicio crítico de control de consumo (RF8.0).
    
    Este servicio implementa la lógica de negocio MÁS CRÍTICA del sistema SaaS:
    - Verificar si un usuario puede consumir horas
    - Actualizar el consumo de horas de forma ATÓMICA
    - Mantener la integridad financiera del sistema
    
    Principios aplicados:
    - Single Responsibility Principle (SRP): Solo maneja consumo
    - Dependency Inversion Principle (DIP): Depende de abstracciones
    - Open/Closed Principle (OCP): Abierto para extensión
    - Clean Architecture: Lógica pura sin dependencias externas
    
    IMPORTANTE: Este servicio debe ejecutarse siempre dentro de 
    transacciones ACID para garantizar consistencia de datos.
    """
    
    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        user_repository: UserRepository
    ):
        """
        🏗️ Constructor con inyección de dependencias (DIP).
        
        Args:
            subscription_repository: Repository para acceso a suscripciones
            user_repository: Repository para acceso a usuarios
        """
        self._subscription_repository = subscription_repository
        self._user_repository = user_repository
    
    async def verificar_consumo_disponible(
        self, 
        user_id: str, 
        required_hours: float
    ) -> ConsumptionVerificationResult:
        """
        🎯 RF8.0 CORE FUNCTION - Verificar si un usuario puede consumir horas.
        
        Esta es la función MÁS CRÍTICA del sistema SaaS. Actúa como GATEKEEPER
        que determina si se permite o rechaza el procesamiento de una reunión.
        
        REGLAS DE NEGOCIO IMPLEMENTADAS:
        1. El usuario debe existir y estar activo
        2. Debe tener una suscripción activa
        3. Debe tener suficientes horas disponibles
        4. La suscripción no debe estar suspendida o expirada
        
        Args:
            user_id: Identificador del usuario
            required_hours: Horas necesarias para el procesamiento
            
        Returns:
            ConsumptionVerificationResult: Resultado de la verificación
            
        Raises:
            UserNotFoundException: Si el usuario no existe
            SubscriptionNotFoundException: Si no tiene suscripción activa
            InsufficientHoursException: Si no tiene suficientes horas
            SubscriptionSuspendedException: Si la suscripción está suspendida
            InvalidConsumptionException: Si las horas requeridas son inválidas
        """
        # Validación de entrada
        if required_hours <= 0:
            raise InvalidConsumptionException(
                user_id, 
                required_hours, 
                "Required hours must be positive"
            )
        
        # 1. Verificar que el usuario existe
        user = await self._user_repository.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        
        # 2. Verificar que el usuario puede acceder al sistema
        if not user.can_access_system():
            raise UserNotFoundException(f"User {user_id} cannot access system")
        
        # 3. Obtener suscripción activa
        subscription = await self._subscription_repository.get_active_subscription_by_user_id(user_id)
        if not subscription:
            raise SubscriptionNotFoundException(user_id)
        
        # 4. Verificar estado de la suscripción
        if subscription.status == SubscriptionStatus.SUSPENDED:
            raise SubscriptionSuspendedException(
                user_id, 
                subscription.id, 
                "Subscription is suspended"
            )
        
        # 5. Verificar disponibilidad de horas (LÓGICA CRÍTICA)
        can_consume = subscription.has_available_hours(required_hours)
        if not can_consume:
            raise InsufficientHoursException(
                user_id,
                required_hours,
                subscription.available_hours,
                subscription.status.value
            )
        
        # 6. Calcular métricas
        consumption_percentage = subscription.get_consumption_percentage()
        remaining_after_consumption = subscription.available_hours - required_hours
        
        return ConsumptionVerificationResult(
            can_consume=True,
            user=user,
            subscription=subscription,
            remaining_hours=remaining_after_consumption,
            consumption_percentage=consumption_percentage
        )
    
    async def consumir_horas(
        self, 
        user_id: str, 
        hours_to_consume: float,
        description: str = "Meeting processing"
    ) -> ConsumptionResult:
        """
        💰 RF8.0 CRITICAL - Consumir horas de la suscripción de forma ATÓMICA.
        
        Esta función actualiza el consumo de horas del usuario de forma
        transaccional, garantizando integridad ACID.
        
        IMPORTANTE: Debe ejecutarse dentro de una transacción ACID.
        
        Args:
            user_id: Identificador del usuario
            hours_to_consume: Horas a consumir
            description: Descripción del consumo (para auditoría)
            
        Returns:
            ConsumptionResult: Resultado del consumo
            
        Raises:
            UserNotFoundException: Si el usuario no existe
            SubscriptionNotFoundException: Si no tiene suscripción
            InsufficientHoursException: Si no tiene suficientes horas
            InvalidConsumptionException: Si las horas son inválidas
        """
        # 1. Verificar que puede consumir (reutilizar lógica)
        verification = await self.verificar_consumo_disponible(user_id, hours_to_consume)
        
        # 2. Consumir horas de la entidad (lógica de dominio)
        updated_subscription = verification.subscription.consume_hours(hours_to_consume)
        
        # 3. Persistir cambios de forma ATÓMICA
        try:
            await self._subscription_repository.begin_transaction()
            
            final_subscription = await self._subscription_repository.update_subscription(
                updated_subscription
            )
            
            await self._subscription_repository.commit_transaction()
            
            return ConsumptionResult(
                success=True,
                updated_subscription=final_subscription,
                consumed_hours=hours_to_consume,
                remaining_hours=final_subscription.available_hours
            )
            
        except Exception as e:
            await self._subscription_repository.rollback_transaction()
            raise InvalidConsumptionException(
                user_id, 
                hours_to_consume, 
                f"Transaction failed: {str(e)}"
            )
    
    async def obtener_estado_consumo(self, user_id: str) -> ConsumptionVerificationResult:
        """
        📊 Obtener estado actual de consumo del usuario.
        
        Función de consulta que no modifica datos, útil para dashboards
        y monitoreo de consumo.
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            ConsumptionVerificationResult: Estado actual del consumo
        """
        return await self.verificar_consumo_disponible(user_id, 0.1)  # Consulta mínima
# ================================================================================================
# 💰 SUBSCRIPTION ENTITY - DOMAIN LAYER (RF8.0 CORE)
# ================================================================================================
# Entidad crítica que encapsula la lógica de suscripciones y consumo de horas
# Esta entidad implementa las reglas de negocio más importantes del sistema SaaS

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class SubscriptionStatus(Enum):
    """Estados posibles de una suscripción."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class SubscriptionPlan(Enum):
    """Planes de suscripción disponibles (RF7.0)."""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class Subscription:
    """
    🔒 ENTIDAD CRÍTICA - Suscripción y control de consumo (RF8.0).
    
    Esta es la entidad MÁS IMPORTANTE del sistema SaaS, ya que controla:
    - Límites de consumo de horas (RF8.0)
    - Planes de suscripción (RF7.0)
    - Lógica de monetización
    
    Principios aplicados:
    - Single Responsibility: Solo maneja lógica de suscripciones
    - Business Rules: Encapsula todas las reglas de consumo
    - ACID Compliance: Designed para transacciones atómicas
    """
    
    # Identificadores (campos requeridos)
    id: str
    user_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    
    # CONSUMO DE HORAS (RF8.0 - CRÍTICO) - campos requeridos
    monthly_hours_limit: float
    available_hours: float
    monthly_price: float
    created_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    
    # Campos opcionales con valores por defecto
    consumed_hours: float = 0.0
    currency: str = "USD"
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones críticas de invariantes del dominio."""
        self._validate_domain_invariants()
    
    def _validate_domain_invariants(self) -> None:
        """
        🛡️ INVARIANTES CRÍTICAS - Reglas que NUNCA pueden violarse.
        
        Estas validaciones protegen la integridad financiera del sistema.
        
        Raises:
            ValueError: Si alguna invariante crítica es violada
        """
        if not self.id or len(self.id.strip()) == 0:
            raise ValueError("Subscription ID cannot be empty")
        
        if not self.user_id or len(self.user_id.strip()) == 0:
            raise ValueError("User ID cannot be empty")
        
        if self.monthly_hours_limit <= 0:
            raise ValueError("Monthly hours limit must be positive")
        
        if self.available_hours < 0:
            raise ValueError("Available hours cannot be negative")
        
        if self.consumed_hours < 0:
            raise ValueError("Consumed hours cannot be negative")
        
        if self.monthly_price < 0:
            raise ValueError("Monthly price cannot be negative")
        
        # REGLA CRÍTICA: Consumido + Disponible = Límite mensual
        total_hours = self.consumed_hours + self.available_hours
        if abs(total_hours - self.monthly_hours_limit) > 0.01:  # Tolerancia para floats
            raise ValueError(
                f"Hours consistency violation: consumed({self.consumed_hours}) + "
                f"available({self.available_hours}) != limit({self.monthly_hours_limit})"
            )
    
    def has_available_hours(self, required_hours: float) -> bool:
        """
        🎯 RF8.0 CORE - Verificar si hay horas disponibles para consumo.
        
        Esta es la función MÁS CRÍTICA del sistema SaaS.
        
        Args:
            required_hours: Horas necesarias para el procesamiento
            
        Returns:
            bool: True si hay suficientes horas disponibles
        """
        return (
            self.status == SubscriptionStatus.ACTIVE and
            self.available_hours >= required_hours
        )
    
    def consume_hours(self, hours_to_consume: float) -> 'Subscription':
        """
        💰 RF8.0 CRITICAL - Consumir horas de la suscripción.
        
        IMPORTANTE: Esta función debe ser llamada DENTRO de una transacción ACID.
        
        Args:
            hours_to_consume: Horas a consumir
            
        Returns:
            Subscription: Nueva instancia con horas actualizadas
            
        Raises:
            ValueError: Si no hay suficientes horas disponibles
        """
        if not self.has_available_hours(hours_to_consume):
            raise ValueError(
                f"Insufficient hours: required={hours_to_consume}, "
                f"available={self.available_hours}, status={self.status.value}"
            )
        
        new_available = self.available_hours - hours_to_consume
        new_consumed = self.consumed_hours + hours_to_consume
        
        return Subscription(
            id=self.id,
            user_id=self.user_id,
            plan=self.plan,
            status=self.status,
            monthly_hours_limit=self.monthly_hours_limit,
            available_hours=new_available,
            consumed_hours=new_consumed,
            monthly_price=self.monthly_price,
            currency=self.currency,
            created_at=self.created_at,
            current_period_start=self.current_period_start,
            current_period_end=self.current_period_end,
            updated_at=datetime.utcnow(),
            cancelled_at=self.cancelled_at
        )
    
    def get_consumption_percentage(self) -> float:
        """
        📊 BUSINESS LOGIC - Calcular porcentaje de consumo.
        
        Returns:
            float: Porcentaje consumido (0-100)
        """
        if self.monthly_hours_limit == 0:
            return 0.0
        
        return (self.consumed_hours / self.monthly_hours_limit) * 100
    
    def is_near_limit(self, threshold_percentage: float = 80.0) -> bool:
        """
        ⚠️ BUSINESS RULE - Verificar si está cerca del límite de consumo.
        
        Args:
            threshold_percentage: Umbral de alerta (default: 80%)
            
        Returns:
            bool: True si está cerca del límite
        """
        return self.get_consumption_percentage() >= threshold_percentage
    
    def can_be_renewed(self) -> bool:
        """
        🔄 BUSINESS RULE - Verificar si la suscripción puede renovarse.
        
        Returns:
            bool: True si puede renovarse
        """
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
    
    def suspend(self, reason: str = "Payment failure") -> 'Subscription':
        """
        🚫 BUSINESS LOGIC - Suspender suscripción.
        
        Args:
            reason: Razón de la suspensión
            
        Returns:
            Subscription: Nueva instancia suspendida
        """
        return Subscription(
            id=self.id,
            user_id=self.user_id,
            plan=self.plan,
            status=SubscriptionStatus.SUSPENDED,
            monthly_hours_limit=self.monthly_hours_limit,
            available_hours=0.0,  # Sin acceso cuando está suspendida
            consumed_hours=self.consumed_hours,
            monthly_price=self.monthly_price,
            currency=self.currency,
            created_at=self.created_at,
            current_period_start=self.current_period_start,
            current_period_end=self.current_period_end,
            updated_at=datetime.utcnow(),
            cancelled_at=self.cancelled_at
        )
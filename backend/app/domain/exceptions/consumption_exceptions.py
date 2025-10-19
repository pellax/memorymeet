# ================================================================================================
# 🚨 CONSUMPTION EXCEPTIONS - DOMAIN LAYER (RF8.0 CRITICAL)
# ================================================================================================
# Excepciones específicas para el dominio de consumo y suscripciones
# Estas excepciones representan violaciones de reglas de negocio críticas

from typing import Optional


class DomainException(Exception):
    """
    Base exception para todas las excepciones del dominio.
    
    Representa violaciones de reglas de negocio que no deben ser 
    manejadas como errores técnicos.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "DOMAIN_ERROR"


class InsufficientHoursException(DomainException):
    """
    🔴 EXCEPCIÓN CRÍTICA - Horas insuficientes para procesamiento (RF8.0).
    
    Esta excepción se lanza cuando un usuario intenta consumir más horas
    de las que tiene disponibles en su suscripción.
    
    Esta es una regla de negocio CRÍTICA que protege la monetización del SaaS.
    """
    
    def __init__(
        self, 
        user_id: str, 
        required_hours: float, 
        available_hours: float,
        subscription_status: str = "unknown"
    ):
        message = (
            f"Insufficient hours for user {user_id}: "
            f"required={required_hours:.2f}, available={available_hours:.2f}, "
            f"subscription_status={subscription_status}"
        )
        super().__init__(message, "INSUFFICIENT_HOURS")
        self.user_id = user_id
        self.required_hours = required_hours
        self.available_hours = available_hours
        self.subscription_status = subscription_status


class SubscriptionNotFoundException(DomainException):
    """
    🔍 EXCEPCIÓN DE NEGOCIO - Suscripción no encontrada.
    
    Se lanza cuando se intenta acceder a una suscripción que no existe
    o no está asociada al usuario especificado.
    """
    
    def __init__(self, user_id: str, subscription_id: Optional[str] = None):
        if subscription_id:
            message = f"Subscription {subscription_id} not found for user {user_id}"
        else:
            message = f"No active subscription found for user {user_id}"
        
        super().__init__(message, "SUBSCRIPTION_NOT_FOUND")
        self.user_id = user_id
        self.subscription_id = subscription_id


class InvalidConsumptionException(DomainException):
    """
    ⚠️ EXCEPCIÓN DE VALIDACIÓN - Consumo inválido.
    
    Se lanza cuando se intenta registrar un consumo de horas inválido
    (negativo, cero, o que viole reglas de negocio).
    """
    
    def __init__(self, user_id: str, invalid_hours: float, reason: str):
        message = (
            f"Invalid consumption for user {user_id}: "
            f"hours={invalid_hours}, reason={reason}"
        )
        super().__init__(message, "INVALID_CONSUMPTION")
        self.user_id = user_id
        self.invalid_hours = invalid_hours
        self.reason = reason


class UserNotFoundException(DomainException):
    """
    👤 EXCEPCIÓN DE NEGOCIO - Usuario no encontrado.
    
    Se lanza cuando se intenta acceder a un usuario que no existe
    en el sistema.
    """
    
    def __init__(self, user_id: str):
        message = f"User {user_id} not found"
        super().__init__(message, "USER_NOT_FOUND")
        self.user_id = user_id


class SubscriptionExpiredException(DomainException):
    """
    ⏰ EXCEPCIÓN DE NEGOCIO - Suscripción expirada.
    
    Se lanza cuando se intenta usar una suscripción que ha expirado.
    """
    
    def __init__(self, user_id: str, subscription_id: str, expired_at: str):
        message = (
            f"Subscription {subscription_id} for user {user_id} "
            f"expired at {expired_at}"
        )
        super().__init__(message, "SUBSCRIPTION_EXPIRED")
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.expired_at = expired_at


class SubscriptionSuspendedException(DomainException):
    """
    🚫 EXCEPCIÓN DE NEGOCIO - Suscripción suspendida.
    
    Se lanza cuando se intenta usar una suscripción que está suspendida
    (generalmente por falta de pago).
    """
    
    def __init__(self, user_id: str, subscription_id: str, reason: str = "Payment failure"):
        message = (
            f"Subscription {subscription_id} for user {user_id} "
            f"is suspended: {reason}"
        )
        super().__init__(message, "SUBSCRIPTION_SUSPENDED")
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.reason = reason
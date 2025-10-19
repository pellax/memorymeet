# ================================================================================================
# 🚨 DOMAIN EXCEPTIONS - M2PRD-001 SAAS (CLEAN ARCHITECTURE)
# ================================================================================================
# Excepciones específicas del dominio de negocio para manejo de errores

from .consumption_exceptions import (
    InsufficientHoursException,
    SubscriptionNotFoundException,
    InvalidConsumptionException,
    UserNotFoundException
)

__all__ = [
    "InsufficientHoursException",
    "SubscriptionNotFoundException", 
    "InvalidConsumptionException",
    "UserNotFoundException"
]
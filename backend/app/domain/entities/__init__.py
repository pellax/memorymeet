# ================================================================================================
# 🏗️ DOMAIN ENTITIES - M2PRD-001 SAAS (CLEAN ARCHITECTURE)
# ================================================================================================
# Entidades del dominio de negocio - Núcleo del sistema sin dependencias externas

from .user import User
from .subscription import Subscription

__all__ = ["User", "Subscription"]
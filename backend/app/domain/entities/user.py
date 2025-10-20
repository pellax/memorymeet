# ================================================================================================
# 👤 USER ENTITY - DOMAIN LAYER (CLEAN ARCHITECTURE)
# ================================================================================================
# Entidad de dominio que representa un usuario del sistema SaaS
# Principios: SOLID, Domain-Driven Design, Business Logic

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """
    🏗️ ENTIDAD DE DOMINIO - Usuario del sistema SaaS M2PRD-001.
    
    Esta entidad encapsula las reglas de negocio relacionadas con usuarios,
    independiente de la infraestructura (base de datos, APIs, etc.).
    
    Principios aplicados:
    - Single Responsibility: Solo maneja lógica de usuario
    - Domain-Driven Design: Refleja conceptos del negocio
    - Immutable: Usar frozen=True en producción para inmutabilidad
    """
    
    # Identificadores únicos (campos requeridos)
    id: str
    email: str
    full_name: str
    created_at: datetime
    
    # Estado del usuario (campos opcionales con defaults)
    is_active: bool = True
    is_verified: bool = False
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de invariantes del dominio."""
        self._validate_domain_invariants()
    
    def _validate_domain_invariants(self) -> None:
        """
        🛡️ DOMAIN INVARIANTS - Reglas de negocio que siempre deben cumplirse.
        
        Raises:
            ValueError: Si alguna invariante de dominio es violada
        """
        if not self.id or len(self.id.strip()) == 0:
            raise ValueError("User ID cannot be empty")
        
        if not self.email or "@" not in self.email:
            raise ValueError("User must have a valid email address")
        
        if not self.full_name or len(self.full_name.strip()) < 2:
            raise ValueError("User full name must be at least 2 characters")
    
    def mark_as_verified(self) -> 'User':
        """
        🔐 BUSINESS LOGIC - Marcar usuario como verificado.
        
        Returns:
            User: Nueva instancia del usuario verificado
        """
        return User(
            id=self.id,
            email=self.email,
            full_name=self.full_name,
            is_active=self.is_active,
            is_verified=True,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            last_login_at=self.last_login_at
        )
    
    def update_last_login(self) -> 'User':
        """
        📊 BUSINESS LOGIC - Actualizar último login del usuario.
        
        Returns:
            User: Nueva instancia con último login actualizado
        """
        return User(
            id=self.id,
            email=self.email,
            full_name=self.full_name,
            is_active=self.is_active,
            is_verified=self.is_verified,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            last_login_at=datetime.utcnow()
        )
    
    def can_access_system(self) -> bool:
        """
        🔒 BUSINESS RULE - Verificar si el usuario puede acceder al sistema.
        
        Un usuario puede acceder si:
        - Está activo
        - Está verificado
        
        Returns:
            bool: True si puede acceder, False en caso contrario
        """
        return self.is_active and self.is_verified
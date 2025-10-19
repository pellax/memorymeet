# ================================================================================================
# 📝 SUBSCRIPTION REPOSITORY INTERFACE - CLEAN ARCHITECTURE (DIP)
# ================================================================================================
# Interface/Port para el repositorio de suscripciones
# Principio DIP: El dominio define la interface, la infraestructura la implementa

from abc import ABC, abstractmethod
from typing import Optional
from ..entities.subscription import Subscription


class SubscriptionRepository(ABC):
    """
    🏗️ REPOSITORY INTERFACE - Port para acceso a datos de suscripciones.
    
    Esta interface define el contrato que debe cumplir cualquier implementación
    de persistencia para suscripciones, siguiendo el principio DIP (Dependency 
    Inversion Principle).
    
    El DOMINIO define la interface, la INFRAESTRUCTURA la implementa.
    
    Principios aplicados:
    - Dependency Inversion Principle (DIP)
    - Interface Segregation Principle (ISP)
    - Single Responsibility Principle (SRP)
    """
    
    @abstractmethod
    async def get_active_subscription_by_user_id(self, user_id: str) -> Optional[Subscription]:
        """
        🔍 Obtener suscripción activa de un usuario.
        
        Esta es la operación MÁS CRÍTICA para RF8.0 (Control de Consumo).
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Optional[Subscription]: Suscripción activa del usuario o None
            
        Raises:
            RepositoryException: Si hay error en el acceso a datos
        """
        pass
    
    @abstractmethod
    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """
        🔍 Obtener suscripción por ID.
        
        Args:
            subscription_id: Identificador de la suscripción
            
        Returns:
            Optional[Subscription]: Suscripción encontrada o None
            
        Raises:
            RepositoryException: Si hay error en el acceso a datos
        """
        pass
    
    @abstractmethod
    async def update_subscription(self, subscription: Subscription) -> Subscription:
        """
        💾 Actualizar suscripción existente.
        
        IMPORTANTE: Esta operación debe ser ATÓMICA y mantener consistencia ACID.
        
        Args:
            subscription: Suscripción con datos actualizados
            
        Returns:
            Subscription: Suscripción actualizada con timestamps
            
        Raises:
            RepositoryException: Si hay error en la actualización
            OptimisticLockException: Si hay conflicto de concurrencia
        """
        pass
    
    @abstractmethod
    async def create_subscription(self, subscription: Subscription) -> Subscription:
        """
        ➕ Crear nueva suscripción.
        
        Args:
            subscription: Nueva suscripción a crear
            
        Returns:
            Subscription: Suscripción creada con ID asignado
            
        Raises:
            RepositoryException: Si hay error en la creación
            DuplicateSubscriptionException: Si ya existe suscripción activa
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self):
        """
        🔄 Iniciar transacción ACID.
        
        Para operaciones críticas de consumo que requieren atomicidad.
        
        Returns:
            Transaction context manager
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self):
        """
        ✅ Confirmar transacción ACID.
        
        Raises:
            TransactionException: Si hay error en el commit
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self):
        """
        🔄 Revertir transacción ACID.
        
        Raises:
            TransactionException: Si hay error en el rollback
        """
        pass


class UserRepository(ABC):
    """
    👤 REPOSITORY INTERFACE - Port para acceso a datos de usuarios.
    
    Interface segregada específicamente para operaciones de usuarios,
    siguiendo ISP (Interface Segregation Principle).
    """
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional['User']:
        """
        🔍 Obtener usuario por ID.
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Optional[User]: Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    async def user_exists(self, user_id: str) -> bool:
        """
        ✅ Verificar si un usuario existe.
        
        Operación optimizada para validaciones rápidas.
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            bool: True si el usuario existe
        """
        pass
"""
🟢 GREEN PHASE - PRDRepository Implementation

Implementación mínima que satisface los tests TDD RED.
Garantiza persistencia ACID de PRDs con requisitos JSON.
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models import PRD
from ..database import DatabaseSessionManager


class PRDRepository:
    """
    ✅ TDD GREEN - Repository para operaciones CRUD de PRD.
    
    Implementa persistencia de PRDs con requisitos JSON y relaciones con Meeting.
    """
    
    def __init__(self, db_manager: DatabaseSessionManager):
        """
        Initialize repository with database manager.
        
        Args:
            db_manager: ACID-compliant database session manager
        """
        self.db_manager = db_manager
    
    def save(self, prd: PRD) -> PRD:
        """
        ✅ GREEN - Guarda un PRD en la base de datos.
        
        Valida consistencia antes de persistir (CONSISTENCY).
        Usa transacción para garantizar ATOMICITY.
        
        Args:
            prd: PRD entity to save
            
        Returns:
            PRD: Saved PRD with all fields
            
        Raises:
            ValueError: Si datos obligatorios están vacíos
            IntegrityError: Si viola constraints de BD (FK con Meeting)
        """
        # ✅ CONSISTENCY - Validar reglas de negocio
        self._validate_prd(prd)
        
        with self.db_manager.transaction() as session:
            try:
                session.add(prd)
                session.flush()
                session.refresh(prd)
                return prd
            except IntegrityError as e:
                # ✅ ATOMICITY - Rollback automático
                raise e
    
    def get_by_id(self, prd_id: str) -> Optional[PRD]:
        """
        ✅ GREEN - Obtiene un PRD por ID.
        
        Args:
            prd_id: Unique identifier
            
        Returns:
            PRD or None if not found
        """
        with self.db_manager.transaction() as session:
            statement = select(PRD).where(PRD.id == prd_id)
            return session.execute(statement).scalar_one_or_none()
    
    def get_by_meeting_id(self, meeting_id: str) -> Optional[PRD]:
        """
        ✅ GREEN - Obtiene PRD asociado a una reunión.
        
        Args:
            meeting_id: Meeting identifier
            
        Returns:
            PRD or None if not found
        """
        with self.db_manager.transaction() as session:
            statement = select(PRD).where(PRD.meeting_id == meeting_id)
            return session.execute(statement).scalar_one_or_none()
    
    def update_requirements(
        self, 
        prd_id: str, 
        new_requirements: List[dict]
    ) -> PRD:
        """
        ✅ GREEN - Actualiza los requisitos de un PRD.
        
        Args:
            prd_id: PRD identifier
            new_requirements: Lista actualizada de requisitos
            
        Returns:
            PRD: PRD actualizado
            
        Raises:
            ValueError: Si el PRD no existe
        """
        with self.db_manager.transaction() as session:
            statement = select(PRD).where(PRD.id == prd_id)
            prd = session.execute(statement).scalar_one_or_none()
            
            if not prd:
                raise ValueError(f"PRD {prd_id} not found")
            
            # Actualizar requisitos
            prd.requirements = new_requirements
            prd.updated_at = datetime.utcnow()
            
            session.flush()
            session.refresh(prd)
            
            return prd
    
    def delete(self, prd_id: str) -> bool:
        """
        ✅ GREEN - Elimina un PRD.
        
        Args:
            prd_id: PRD identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self.db_manager.transaction() as session:
            statement = select(PRD).where(PRD.id == prd_id)
            prd = session.execute(statement).scalar_one_or_none()
            
            if not prd:
                return False
            
            session.delete(prd)
            session.flush()
            
            return True
    
    def _validate_prd(self, prd: PRD) -> None:
        """
        ✅ CONSISTENCY - Valida reglas de negocio del PRD.
        
        Args:
            prd: PRD to validate
            
        Raises:
            ValueError: Si alguna validación falla
        """
        if not prd.title or prd.title.strip() == "":
            raise ValueError("title is required")
        
        if not prd.requirements or len(prd.requirements) == 0:
            raise ValueError("PRD must have at least one requirement")
        
        if not prd.meeting_id:
            raise ValueError("meeting_id is required")

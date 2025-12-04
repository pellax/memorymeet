"""
🟢 GREEN PHASE - MeetingRepository Implementation

Implementación mínima que satisface los tests TDD RED.
Garantiza principios ACID mediante DatabaseSessionManager.
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models import Meeting, MeetingStatus
from ..database import DatabaseSessionManager


class MeetingRepository:
    """
    ✅ TDD GREEN - Repository para operaciones CRUD de Meeting.
    
    Implementa operaciones de persistencia garantizando ACID compliance.
    """
    
    def __init__(self, db_manager: DatabaseSessionManager):
        """
        Initialize repository with database manager.
        
        Args:
            db_manager: ACID-compliant database session manager
        """
        self.db_manager = db_manager
    
    def save(self, meeting: Meeting) -> Meeting:
        """
        ✅ GREEN - Guarda una reunión en la base de datos.
        
        Valida consistencia antes de persistir (CONSISTENCY).
        Usa transacción para garantizar ATOMICITY.
        
        Args:
            meeting: Meeting entity to save
            
        Returns:
            Meeting: Saved meeting with all fields
            
        Raises:
            ValueError: Si datos obligatorios están vacíos
            IntegrityError: Si viola constraints de BD
        """
        # ✅ CONSISTENCY - Validar reglas de negocio
        self._validate_meeting(meeting)
        
        with self.db_manager.transaction() as session:
            try:
                session.add(meeting)
                session.flush()  # Forzar escritura para detectar errores
                session.refresh(meeting)  # Refrescar para evitar DetachedInstanceError
                return meeting
            except IntegrityError as e:
                # ✅ ATOMICITY - Rollback automático por el context manager
                raise e
    
    def get_by_id(self, meeting_id: str) -> Optional[Meeting]:
        """
        ✅ GREEN - Obtiene una reunión por ID.
        
        Args:
            meeting_id: Unique identifier
            
        Returns:
            Meeting or None if not found
        """
        with self.db_manager.transaction() as session:
            statement = select(Meeting).where(Meeting.id == meeting_id)
            result = session.execute(statement).scalar_one_or_none()
            
            # No hacer expunge - mantener objeto attached
            # SQLAlchemy maneja el ciclo de vida del objeto
            return result
    
    def get_by_user_id(self, user_id: str) -> List[Meeting]:
        """
        ✅ GREEN - Obtiene todas las reuniones de un usuario.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of meetings for the user
        """
        with self.db_manager.transaction() as session:
            statement = select(Meeting).where(Meeting.user_id == user_id)
            results = session.execute(statement).scalars().all()
            
            # Retornar lista sin expunge
            return list(results)
    
    def get_pending_meetings(self) -> List[Meeting]:
        """
        ✅ GREEN - Obtiene todas las reuniones pendientes.
        
        Returns:
            List of meetings with PENDING status
        """
        with self.db_manager.transaction() as session:
            statement = select(Meeting).where(
                Meeting.status == MeetingStatus.PENDING
            )
            results = session.execute(statement).scalars().all()
            
            # Retornar lista sin expunge
            return list(results)
    
    def update_status(
        self, 
        meeting_id: str, 
        new_status: MeetingStatus
    ) -> Meeting:
        """
        ✅ GREEN - Actualiza el estado de una reunión.
        
        Args:
            meeting_id: Meeting identifier
            new_status: New status to set
            
        Returns:
            Updated meeting
            
        Raises:
            ValueError: Si la reunión no existe
        """
        with self.db_manager.transaction() as session:
            statement = select(Meeting).where(Meeting.id == meeting_id)
            meeting = session.execute(statement).scalar_one_or_none()
            
            if not meeting:
                raise ValueError(f"Meeting {meeting_id} not found")
            
            # Update status using domain logic
            meeting.status = new_status
            
            if new_status == MeetingStatus.PROCESSING:
                meeting.mark_as_processing()
            elif new_status == MeetingStatus.COMPLETED:
                meeting.mark_as_completed()
            
            session.flush()
            session.refresh(meeting)  # Refrescar objeto
            
            return meeting
    
    def delete(self, meeting_id: str) -> bool:
        """
        ✅ GREEN - Elimina una reunión.
        
        Args:
            meeting_id: Meeting identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self.db_manager.transaction() as session:
            statement = select(Meeting).where(Meeting.id == meeting_id)
            meeting = session.execute(statement).scalar_one_or_none()
            
            if not meeting:
                return False
            
            session.delete(meeting)
            session.flush()
            
            return True
    
    def _validate_meeting(self, meeting: Meeting) -> None:
        """
        ✅ CONSISTENCY - Valida reglas de negocio del Meeting.
        
        Args:
            meeting: Meeting to validate
            
        Raises:
            ValueError: Si alguna validación falla
        """
        if not meeting.meeting_url or meeting.meeting_url.strip() == "":
            raise ValueError("meeting_url is required")
        
        if not meeting.user_id or meeting.user_id.strip() == "":
            raise ValueError("user_id is required")
        
        # Validar formato de URL básico
        if not meeting.meeting_url.startswith("http"):
            raise ValueError("meeting_url must be a valid URL")

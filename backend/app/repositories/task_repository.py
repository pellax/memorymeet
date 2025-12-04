"""
🟢 GREEN PHASE - TaskRepository Implementation

Implementación mínima que satisface los tests TDD RED.
Garantiza persistencia ACID de tareas con relaciones a PRD.
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models import Task, TaskPriority, TaskStatus
from ..database import DatabaseSessionManager


class TaskRepository:
    """
    ✅ TDD GREEN - Repository para operaciones CRUD de Task.
    
    Implementa persistencia de tareas con asignación de roles y relaciones con PRD.
    """
    
    def __init__(self, db_manager: DatabaseSessionManager):
        """
        Initialize repository with database manager.
        
        Args:
            db_manager: ACID-compliant database session manager
        """
        self.db_manager = db_manager
    
    def save(self, task: Task) -> Task:
        """
        ✅ GREEN - Guarda una tarea en la base de datos.
        
        Valida consistencia antes de persistir (CONSISTENCY).
        Usa transacción para garantizar ATOMICITY.
        
        Args:
            task: Task entity to save
            
        Returns:
            Task: Saved task with all fields
            
        Raises:
            ValueError: Si datos obligatorios están vacíos
            IntegrityError: Si viola constraints de BD (FK con PRD)
        """
        # ✅ CONSISTENCY - Validar reglas de negocio
        self._validate_task(task)
        
        with self.db_manager.transaction() as session:
            try:
                session.add(task)
                session.flush()
                session.refresh(task)
                return task
            except IntegrityError as e:
                # ✅ ATOMICITY - Rollback automático
                raise e
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        ✅ GREEN - Obtiene una tarea por ID.
        
        Args:
            task_id: Unique identifier
            
        Returns:
            Task or None if not found
        """
        with self.db_manager.transaction() as session:
            statement = select(Task).where(Task.id == task_id)
            return session.execute(statement).scalar_one_or_none()
    
    def get_by_prd_id(self, prd_id: str) -> List[Task]:
        """
        ✅ GREEN - Obtiene todas las tareas de un PRD.
        
        Args:
            prd_id: PRD identifier
            
        Returns:
            List of tasks for the PRD
        """
        with self.db_manager.transaction() as session:
            statement = select(Task).where(Task.prd_id == prd_id)
            return list(session.execute(statement).scalars().all())
    
    def get_by_assigned_role(self, role: str) -> List[Task]:
        """
        ✅ GREEN - Obtiene tareas asignadas a un rol específico.
        
        Args:
            role: Developer role (e.g., "Backend Developer")
            
        Returns:
            List of tasks assigned to the role
        """
        with self.db_manager.transaction() as session:
            statement = select(Task).where(Task.assigned_role == role)
            return list(session.execute(statement).scalars().all())
    
    def get_high_priority_tasks(self) -> List[Task]:
        """
        ✅ GREEN - Obtiene tareas de alta prioridad (CRITICAL y HIGH).
        
        Returns:
            List of high priority tasks
        """
        with self.db_manager.transaction() as session:
            statement = select(Task).where(
                Task.priority.in_([TaskPriority.CRITICAL, TaskPriority.HIGH])
            )
            return list(session.execute(statement).scalars().all())
    
    def update_status(self, task_id: str, new_status: TaskStatus) -> Task:
        """
        ✅ GREEN - Actualiza el estado de una tarea.
        
        Args:
            task_id: Task identifier
            new_status: New status to set
            
        Returns:
            Task: Updated task
            
        Raises:
            ValueError: Si la tarea no existe
        """
        with self.db_manager.transaction() as session:
            statement = select(Task).where(Task.id == task_id)
            task = session.execute(statement).scalar_one_or_none()
            
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Actualizar estado usando lógica de dominio
            if new_status == TaskStatus.IN_PROGRESS:
                task.mark_as_in_progress()
            elif new_status == TaskStatus.COMPLETED:
                task.mark_as_completed()
            else:
                task.status = new_status
                task.updated_at = datetime.utcnow()
            
            session.flush()
            session.refresh(task)
            
            return task
    
    def link_external_task(
        self, 
        task_id: str, 
        external_id: str, 
        external_url: str
    ) -> Task:
        """
        ✅ GREEN - Vincula tarea con sistema externo (Jira/Trello/Linear).
        
        Args:
            task_id: Task identifier
            external_id: ID en sistema externo (e.g., "JIRA-123")
            external_url: URL de la tarea externa
            
        Returns:
            Task: Updated task
            
        Raises:
            ValueError: Si la tarea no existe
        """
        with self.db_manager.transaction() as session:
            statement = select(Task).where(Task.id == task_id)
            task = session.execute(statement).scalar_one_or_none()
            
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Usar método de dominio para vincular
            task.link_external_task(external_id, external_url)
            
            session.flush()
            session.refresh(task)
            
            return task
    
    def delete(self, task_id: str) -> bool:
        """
        ✅ GREEN - Elimina una tarea.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self.db_manager.transaction() as session:
            statement = select(Task).where(Task.id == task_id)
            task = session.execute(statement).scalar_one_or_none()
            
            if not task:
                return False
            
            session.delete(task)
            session.flush()
            
            return True
    
    def _validate_task(self, task: Task) -> None:
        """
        ✅ CONSISTENCY - Valida reglas de negocio de Task.
        
        Args:
            task: Task to validate
            
        Raises:
            ValueError: Si alguna validación falla
        """
        if not task.title or task.title.strip() == "":
            raise ValueError("title is required")
        
        if not task.assigned_role or task.assigned_role.strip() == "":
            raise ValueError("assigned_role is required")
        
        if not task.prd_id:
            raise ValueError("prd_id is required")

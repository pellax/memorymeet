"""
✅ Domain Model: Task (Tarea Asignada)

Represents an assigned task generated from a requirement in the PRD.
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database.base import Base


class TaskPriority(PyEnum):
    """Prioridades de tareas."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(PyEnum):
    """Estados de tareas."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Task(Base):
    """
    ✅ TDD - Task entity.
    
    Represents a task assigned to a developer role.
    """
    __tablename__ = "tasks"
    
    # Primary Key
    id = Column(String(50), primary_key=True, index=True)
    
    # Task Information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Assignment
    assigned_role = Column(String(100), nullable=False, index=True)
    
    # Priority and Status
    priority = Column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True
    )
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Metadata
    confidence_score = Column(String(10), nullable=True)
    requirement_id = Column(String(50), nullable=True)  # ID del requisito origen
    
    # Foreign Keys
    prd_id = Column(String(50), ForeignKey("prds.id"), nullable=False, index=True)
    
    # External Integration (RF5.0 - PMS Integration)
    external_task_id = Column(String(100), nullable=True)  # ID en Jira/Trello/Linear
    external_task_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    prd = relationship("PRD", back_populates="tasks")
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, assigned_role={self.assigned_role})>"
    
    def is_high_priority(self) -> bool:
        """✅ Domain Logic - Verifica si la tarea es de alta prioridad."""
        return self.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]
    
    def mark_as_in_progress(self) -> None:
        """✅ Domain Logic - Marca tarea como en progreso."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
    
    def mark_as_completed(self) -> None:
        """✅ Domain Logic - Marca tarea como completada."""
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def link_external_task(self, external_id: str, external_url: str) -> None:
        """
        ✅ Domain Logic - Vincula tarea con sistema externo (Jira/Trello).
        
        Args:
            external_id: ID de la tarea en el sistema externo
            external_url: URL de la tarea externa
        """
        self.external_task_id = external_id
        self.external_task_url = external_url
        self.updated_at = datetime.utcnow()

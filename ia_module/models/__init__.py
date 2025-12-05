"""
✅ Domain Models - Módulo IA/NLP M2PRD-001
Modelos de dominio siguiendo principios de Clean Architecture y DDD.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class RequirementType(Enum):
    """Tipos de requisitos según el dominio del proyecto."""
    FUNCTIONAL = "funcional"
    NON_FUNCTIONAL = "no_funcional"
    TECHNICAL = "tecnico"


class RequirementPriority(Enum):
    """Prioridades de requisitos."""
    P0 = "critical"
    P1 = "high"
    P2 = "medium"
    P3 = "low"


class AssigneeRole(Enum):
    """Roles disponibles para asignación de tareas (RF4.0)."""
    FRONTEND_DEVELOPER = "Frontend Developer"
    BACKEND_DEVELOPER = "Backend Developer"
    FULLSTACK_DEVELOPER = "Full Stack Developer"
    CLOUD_ENGINEER = "Cloud Engineer"
    UX_DESIGNER = "UX Designer"
    QA_ENGINEER = "QA Engineer"
    DEVOPS_ENGINEER = "DevOps Engineer"


@dataclass
class TranscriptionResult:
    """
    ✅ Value Object - Resultado de transcripción de audio.
    
    Representa el resultado de la transcripción de una reunión.
    """
    text: str
    language: str = "es"
    confidence: float = 0.0
    duration_seconds: float = 0.0
    words_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validación de invariantes."""
        if not self.text or len(self.text.strip()) == 0:
            raise ValueError("Transcription text cannot be empty")
        
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        # Calcular words_count si no se proporciona
        if self.words_count == 0:
            self.words_count = len(self.text.split())


@dataclass
class Requirement:
    """
    ✅ Domain Entity - Requisito extraído de una reunión.
    
    Representa un requisito funcional o no funcional identificado
    en la transcripción de una reunión (RF3.0).
    """
    id: str
    description: str
    type: RequirementType
    priority: RequirementPriority = RequirementPriority.P2
    assignee_role: Optional[AssigneeRole] = None
    keywords: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    def __post_init__(self):
        """Validación de invariantes de dominio."""
        if not self.description or len(self.description.strip()) < 10:
            raise ValueError("Requirement description must be at least 10 characters")
        
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
    
    def to_dict(self) -> dict:
        """Serialización a diccionario."""
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type.value,
            "priority": self.priority.value,
            "assignee_role": self.assignee_role.value if self.assignee_role else None,
            "keywords": self.keywords,
            "confidence_score": self.confidence_score
        }


@dataclass
class AssignedTask:
    """
    ✅ Domain Entity - Tarea asignada a un rol específico.
    
    Representa una tarea creada a partir de un requisito,
    con asignación inteligente de rol (RF4.0).
    """
    id: str
    requirement_id: str
    description: str
    assignee_role: AssigneeRole
    priority: RequirementPriority
    status: str = "PENDING"
    estimated_hours: float = 0.0
    
    def __post_init__(self):
        """Validación de estado válido."""
        valid_statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")
    
    def to_dict(self) -> dict:
        """Serialización a diccionario."""
        return {
            "id": self.id,
            "requirement_id": self.requirement_id,
            "description": self.description,
            "assignee_role": self.assignee_role.value,
            "priority": self.priority.value,
            "status": self.status,
            "estimated_hours": self.estimated_hours
        }


@dataclass
class PRD:
    """
    ✅ Aggregate Root - Product Requirements Document.
    
    Entidad principal que encapsula todos los requisitos
    y tareas generadas a partir de una reunión (RF3.0).
    """
    id: str
    title: str
    meeting_id: str
    requirements: List[Requirement]
    tasks: List[AssignedTask] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    complexity_level: str = "MEDIUM"
    
    def __post_init__(self):
        """Validación de invariantes de dominio."""
        if not self.requirements:
            raise ValueError("PRD must have at least one requirement")
        
        if len(self.title) < 5:
            raise ValueError("PRD title must be at least 5 characters")
        
        # Calcular complejidad automáticamente
        self.complexity_level = self._calculate_complexity()
    
    def _calculate_complexity(self) -> str:
        """
        ✅ Domain Logic - Cálculo de complejidad del PRD.
        
        Business Rule: La complejidad se basa en el número de requisitos.
        """
        num_requirements = len(self.requirements)
        
        if num_requirements <= 3:
            return "LOW"
        elif num_requirements <= 8:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def add_requirement(self, requirement: Requirement) -> None:
        """Añade un requisito manteniendo invariantes."""
        if not requirement:
            raise ValueError("Requirement cannot be None")
        self.requirements.append(requirement)
        self.complexity_level = self._calculate_complexity()
    
    def generate_tasks(self) -> List[AssignedTask]:
        """
        ✅ Domain Logic - Genera tareas a partir de requisitos.
        
        Business Rule: Cada requisito genera una tarea con asignación de rol.
        """
        if not self.requirements:
            raise ValueError("Cannot generate tasks from empty requirements")
        
        tasks = []
        for req in self.requirements:
            if req.assignee_role:
                task = AssignedTask(
                    id=f"TASK-{req.id}",
                    requirement_id=req.id,
                    description=req.description,
                    assignee_role=req.assignee_role,
                    priority=req.priority
                )
                tasks.append(task)
        
        self.tasks = tasks
        return tasks
    
    def to_dict(self) -> dict:
        """Serialización completa a diccionario."""
        return {
            "id": self.id,
            "title": self.title,
            "meeting_id": self.meeting_id,
            "requirements": [req.to_dict() for req in self.requirements],
            "tasks": [task.to_dict() for task in self.tasks],
            "created_at": self.created_at.isoformat(),
            "complexity_level": self.complexity_level
        }


# ✅ Exceptions de Dominio
class DomainException(Exception):
    """Excepción base para errores de dominio."""
    pass


class TranscriptionException(DomainException):
    """Excepción para errores de transcripción."""
    pass


class RequirementExtractionException(DomainException):
    """Excepción para errores de extracción de requisitos."""
    pass


class InvalidRequirementException(DomainException):
    """Excepción para requisitos inválidos."""
    pass

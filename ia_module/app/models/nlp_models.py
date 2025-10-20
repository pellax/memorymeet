# ================================================================================================
# 📊 NLP DOMAIN MODELS - Entities y Value Objects para IA/NLP (RF3.0, RF4.0)
# ================================================================================================
# Modelos de dominio que definen las estructuras de datos del módulo IA

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID


class RequirementType(Enum):
    """🎯 Tipos de requisitos identificables por el NLP"""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    BUSINESS = "business"
    TECHNICAL = "technical"
    CONSTRAINT = "constraint"


class Priority(Enum):
    """🎯 Niveles de prioridad basados en análisis de lenguaje natural"""
    CRITICAL = "critical"    # Palabras clave: CRÍTICO, URGENTE, INMEDIATAMENTE
    HIGH = "high"           # Palabras clave: DEBE, IMPORTANTE, NECESARIO
    MEDIUM = "medium"       # Palabras clave: DEBERÍA, CONVENIENTE, BUENO
    LOW = "low"            # Palabras clave: PODRÍA, SI HAY TIEMPO, OPCIONAL


class DeveloperRole(Enum):
    """👩‍💻 Roles de desarrollador para asignación inteligente (RF4.0)"""
    BACKEND_DEVELOPER = "backend_developer"
    FRONTEND_DEVELOPER = "frontend_developer"
    FULLSTACK_DEVELOPER = "fullstack_developer"
    UX_DESIGNER = "ux_designer"
    UI_DESIGNER = "ui_designer"
    DEVOPS_ENGINEER = "devops_engineer"
    QA_ENGINEER = "qa_engineer"
    DATA_SCIENTIST = "data_scientist"
    MOBILE_DEVELOPER = "mobile_developer"
    PRODUCT_MANAGER = "product_manager"


@dataclass
class ProcessingRequest:
    """
    📥 Value Object para requests de procesamiento NLP.
    
    Encapsula toda la información necesaria para procesar una transcripción.
    """
    transcription_text: str
    meeting_id: str
    language: str = "auto"  # auto, es, en, fr, etc.
    processing_options: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validaciones básicas del request"""
        if not self.transcription_text or not self.transcription_text.strip():
            from ..exceptions.nlp_exceptions import InvalidTranscriptionException
            raise InvalidTranscriptionException("Transcription text cannot be empty")
        
        if not self.meeting_id:
            raise ValueError("Meeting ID is required")


@dataclass 
class Requirement:
    """
    📋 Entity que representa un requisito extraído del texto.
    
    Contiene toda la información identificada sobre un requisito específico.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    type: RequirementType = RequirementType.FUNCTIONAL
    priority: Priority = Priority.MEDIUM
    confidence_score: float = 0.0  # 0.0 - 1.0
    source_sentence: str = ""  # Frase original de donde se extrajo
    keywords: List[str] = field(default_factory=list)
    estimated_effort_hours: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)  # IDs de otros requisitos
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Verificar si el requisito tiene alta confianza"""
        return self.confidence_score >= threshold
    
    def get_effort_estimate(self) -> str:
        """Obtener estimación de esfuerzo en formato legible"""
        if not self.estimated_effort_hours:
            return "No estimado"
        
        if self.estimated_effort_hours < 1:
            return f"{int(self.estimated_effort_hours * 60)} minutos"
        elif self.estimated_effort_hours <= 8:
            return f"{self.estimated_effort_hours:.1f} horas"
        else:
            days = self.estimated_effort_hours / 8
            return f"{days:.1f} días"


@dataclass
class AssignedTask:
    """
    📝 Entity que representa una tarea asignada automáticamente.
    
    Resultado de la asignación inteligente de requisitos a roles (RF4.0).
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    requirement_id: str = ""
    title: str = ""
    description: str = ""
    assigned_role: DeveloperRole = DeveloperRole.FULLSTACK_DEVELOPER
    priority: Priority = Priority.MEDIUM
    confidence_score: float = 0.0
    estimated_hours: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_assignment_reason(self) -> str:
        """Explicar por qué se asignó a este rol"""
        role_reasoning = {
            DeveloperRole.BACKEND_DEVELOPER: "API, base de datos, lógica de negocio",
            DeveloperRole.FRONTEND_DEVELOPER: "Interfaz, componentes, experiencia visual",
            DeveloperRole.UX_DESIGNER: "Experiencia de usuario, diseño, usabilidad",
            DeveloperRole.DEVOPS_ENGINEER: "Infraestructura, despliegue, monitoreo",
            DeveloperRole.QA_ENGINEER: "Testing, calidad, validación",
            DeveloperRole.MOBILE_DEVELOPER: "Aplicación móvil, iOS, Android"
        }
        return role_reasoning.get(self.assigned_role, "Asignación general")


@dataclass
class ProcessingStats:
    """
    📊 Value Object con estadísticas del procesamiento.
    """
    total_words: int = 0
    total_sentences: int = 0
    total_paragraphs: int = 0
    detected_language: str = "unknown"
    language_confidence: float = 0.0
    processing_model: str = "unknown"
    unique_speakers: int = 0
    avg_sentence_length: float = 0.0
    complexity_score: float = 0.0  # 0.0 = simple, 1.0 = complejo


@dataclass
class ProcessingResult:
    """
    📤 Value Object para el resultado completo del procesamiento NLP.
    
    Encapsula todo lo generado por el módulo IA/NLP.
    """
    success: bool = False
    meeting_id: str = ""
    requirements: List[Requirement] = field(default_factory=list)
    assigned_tasks: List[AssignedTask] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    processed_at: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0  # Confianza general del procesamiento
    stats: Optional[ProcessingStats] = None
    error_message: Optional[str] = None
    model_version: str = "1.0.0"
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen ejecutivo del procesamiento"""
        return {
            "total_requirements": len(self.requirements),
            "functional_requirements": len([r for r in self.requirements 
                                          if r.type == RequirementType.FUNCTIONAL]),
            "non_functional_requirements": len([r for r in self.requirements 
                                              if r.type == RequirementType.NON_FUNCTIONAL]),
            "total_tasks": len(self.assigned_tasks),
            "high_priority_items": len([r for r in self.requirements 
                                      if r.priority in [Priority.CRITICAL, Priority.HIGH]]),
            "processing_time": f"{self.processing_time_seconds:.2f}s",
            "confidence": f"{self.confidence_score:.2%}",
            "roles_assigned": list(set(task.assigned_role.value for task in self.assigned_tasks))
        }
    
    def get_requirements_by_type(self, req_type: RequirementType) -> List[Requirement]:
        """Filtrar requisitos por tipo"""
        return [req for req in self.requirements if req.type == req_type]
    
    def get_tasks_by_role(self, role: DeveloperRole) -> List[AssignedTask]:
        """Filtrar tareas por rol asignado"""
        return [task for task in self.assigned_tasks if task.assigned_role == role]
    
    def has_critical_requirements(self) -> bool:
        """Verificar si hay requisitos críticos identificados"""
        return any(req.priority == Priority.CRITICAL for req in self.requirements)


@dataclass
class NLPModelConfig:
    """
    ⚙️ Value Object para configuración del modelo NLP.
    """
    language_models: Dict[str, str] = field(default_factory=lambda: {
        "en": "en_core_web_sm",
        "es": "es_core_news_sm"
    })
    confidence_threshold: float = 0.6
    max_requirements_per_sentence: int = 3
    enable_sentiment_analysis: bool = True
    enable_entity_recognition: bool = True
    priority_keywords: Dict[Priority, List[str]] = field(default_factory=lambda: {
        Priority.CRITICAL: ["crítico", "urgente", "inmediatamente", "critical", "urgent", "asap"],
        Priority.HIGH: ["debe", "importante", "necesario", "must", "important", "required"],
        Priority.MEDIUM: ["debería", "conveniente", "bueno", "should", "nice", "good"],
        Priority.LOW: ["podría", "opcional", "si hay tiempo", "could", "optional", "if time"]
    })
    role_keywords: Dict[DeveloperRole, List[str]] = field(default_factory=lambda: {
        DeveloperRole.BACKEND_DEVELOPER: ["api", "backend", "servidor", "base de datos", "database", "endpoint"],
        DeveloperRole.FRONTEND_DEVELOPER: ["frontend", "interfaz", "ui", "página", "componente", "react", "vue"],
        DeveloperRole.UX_DESIGNER: ["ux", "experiencia", "usuario", "diseño", "usabilidad", "accesible"],
        DeveloperRole.DEVOPS_ENGINEER: ["deploy", "infraestructura", "servidor", "docker", "kubernetes", "ci/cd"],
        DeveloperRole.QA_ENGINEER: ["testing", "test", "calidad", "validación", "prueba"]
    })


# ================================================================================================
# 🔧 FACTORY FUNCTIONS - Creación simplificada de objetos
# ================================================================================================

def create_functional_requirement(
    description: str,
    priority: Priority = Priority.MEDIUM,
    confidence: float = 0.8,
    source_sentence: str = ""
) -> Requirement:
    """Factory para crear requisito funcional"""
    return Requirement(
        description=description,
        type=RequirementType.FUNCTIONAL,
        priority=priority,
        confidence_score=confidence,
        source_sentence=source_sentence
    )


def create_non_functional_requirement(
    description: str,
    priority: Priority = Priority.MEDIUM,
    confidence: float = 0.8,
    source_sentence: str = ""
) -> Requirement:
    """Factory para crear requisito no funcional"""
    return Requirement(
        description=description,
        type=RequirementType.NON_FUNCTIONAL,
        priority=priority,
        confidence_score=confidence,
        source_sentence=source_sentence
    )


def create_assigned_task(
    requirement_id: str,
    title: str,
    description: str,
    role: DeveloperRole,
    priority: Priority = Priority.MEDIUM,
    confidence: float = 0.8
) -> AssignedTask:
    """Factory para crear tarea asignada"""
    return AssignedTask(
        requirement_id=requirement_id,
        title=title,
        description=description,
        assigned_role=role,
        priority=priority,
        confidence_score=confidence
    )
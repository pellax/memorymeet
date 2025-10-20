# ================================================================================================
# 🟢 NLP PROCESSOR SERVICE - Implementación TDD GREEN Phase (RF3.0, RF4.0)
# ================================================================================================
# Servicio principal que implementa la lógica de procesamiento NLP

import time
import re
from typing import List, Dict, Optional, Protocol
from datetime import datetime
from abc import ABC, abstractmethod

from ..models.nlp_models import (
    ProcessingRequest,
    ProcessingResult,
    Requirement,
    RequirementType,
    Priority,
    AssignedTask,
    DeveloperRole,
    ProcessingStats,
    NLPModelConfig,
    create_functional_requirement,
    create_non_functional_requirement,
    create_assigned_task
)
from ..exceptions.nlp_exceptions import (
    InvalidTranscriptionException,
    ProcessingFailedException,
    RequirementExtractionException,
    TaskAssignmentException,
    InsufficientDataException,
    create_processing_error
)


# ================================================================================================
# 🎯 INTERFACES & PROTOCOLS - Clean Architecture
# ================================================================================================

class RequirementExtractor(Protocol):
    """🎯 Interface para extracción de requisitos - Dependency Inversion Principle"""
    
    def extract_requirements(self, text: str, language: str = "auto") -> List[Requirement]:
        """Extraer requisitos del texto proporcionado"""
        ...
    
    def detect_priorities(self, text: str) -> Dict[str, Priority]:
        """Detectar prioridades basadas en análisis de lenguaje"""
        ...


class TaskAssigner(Protocol):
    """🎯 Interface para asignación inteligente de tareas - RF4.0"""
    
    def assign_tasks(self, requirements: List[Requirement]) -> List[AssignedTask]:
        """Asignar tareas basándose en los requisitos identificados"""
        ...
    
    def determine_role(self, requirement: Requirement) -> DeveloperRole:
        """Determinar el rol más apropiado para un requisito"""
        ...


# ================================================================================================
# 🟢 TDD GREEN PHASE - IMPLEMENTACIONES MÍNIMAS
# ================================================================================================

class SimpleRequirementExtractor(RequirementExtractor):
    """
    🟢 GREEN - Implementación mínima de extracción de requisitos.
    
    Utiliza reglas simples y palabras clave para pasar los tests iniciales.
    En REFACTOR phase se reemplazará por modelos más sofisticados.
    """
    
    def __init__(self, config: Optional[NLPModelConfig] = None):
        self.config = config or NLPModelConfig()
    
    def extract_requirements(self, text: str, language: str = "auto") -> List[Requirement]:
        """🟢 GREEN - Extracción básica usando palabras clave"""
        requirements = []
        
        # Dividir texto en oraciones
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            # Detectar si la oración contiene requisitos
            if self._contains_requirement_keywords(sentence):
                requirement = self._create_requirement_from_sentence(sentence)
                if requirement:
                    requirements.append(requirement)
        
        return requirements
    
    def detect_priorities(self, text: str) -> Dict[str, Priority]:
        """🟢 GREEN - Detección básica de prioridades"""
        priorities = {}
        text_lower = text.lower()
        
        for priority, keywords in self.config.priority_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Encontrar contexto alrededor de la palabra clave
                    sentences = self._split_into_sentences(text)
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            priorities[sentence] = priority
                            break
        
        return priorities
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Dividir texto en oraciones usando regex simple"""
        # Regex básica para dividir oraciones
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _contains_requirement_keywords(self, sentence: str) -> bool:
        """Verificar si una oración contiene palabras clave de requisitos"""
        requirement_keywords = [
            "necesitamos", "implementar", "debe", "debería", "requiere",
            "need", "implement", "should", "must", "require",
            "api", "interfaz", "sistema", "aplicación", "funcionalidad",
            "endpoint", "base de datos", "autenticación", "login",
            "diseño", "responsive", "página", "componente"
        ]
        
        sentence_lower = sentence.lower()
        return any(keyword in sentence_lower for keyword in requirement_keywords)
    
    def _create_requirement_from_sentence(self, sentence: str) -> Optional[Requirement]:
        """Crear requisito a partir de una oración"""
        if not sentence or len(sentence.strip()) < 10:
            return None
        
        # Determinar tipo de requisito
        req_type = self._determine_requirement_type(sentence)
        
        # Determinar prioridad
        priority = self._determine_priority_from_sentence(sentence)
        
        # Limpiar descripción
        description = self._clean_description(sentence)
        
        # Calcular confianza básica
        confidence = self._calculate_basic_confidence(sentence)
        
        if req_type == RequirementType.FUNCTIONAL:
            return create_functional_requirement(
                description=description,
                priority=priority,
                confidence=confidence,
                source_sentence=sentence
            )
        else:
            return create_non_functional_requirement(
                description=description,
                priority=priority,
                confidence=confidence,
                source_sentence=sentence
            )
    
    def _determine_requirement_type(self, sentence: str) -> RequirementType:
        """Determinar si es funcional o no funcional"""
        non_functional_keywords = [
            "performance", "rendimiento", "segundo", "tiempo", "velocidad",
            "usuarios concurrentes", "escalabilidad", "disponibilidad",
            "seguridad", "backup", "monitoreo"
        ]
        
        sentence_lower = sentence.lower()
        
        if any(keyword in sentence_lower for keyword in non_functional_keywords):
            return RequirementType.NON_FUNCTIONAL
        
        return RequirementType.FUNCTIONAL
    
    def _determine_priority_from_sentence(self, sentence: str) -> Priority:
        """Determinar prioridad basada en palabras clave"""
        sentence_lower = sentence.lower()
        
        for priority, keywords in self.config.priority_keywords.items():
            if any(keyword in sentence_lower for keyword in keywords):
                return priority
        
        return Priority.MEDIUM  # Default
    
    def _clean_description(self, sentence: str) -> str:
        """Limpiar y normalizar descripción"""
        # Eliminar nombres de personas y prefijos comunes
        description = re.sub(r'^(Juan|María|Carlos|Ana):\s*', '', sentence)
        description = re.sub(r'^(PM|UX|Dev|Designer):\s*', '', description)
        
        return description.strip()
    
    def _calculate_basic_confidence(self, sentence: str) -> float:
        """Calcular confianza básica basada en palabras clave"""
        high_confidence_keywords = [
            "necesitamos", "debe", "implementar", "requiere",
            "need", "must", "implement", "require"
        ]
        
        sentence_lower = sentence.lower()
        matches = sum(1 for keyword in high_confidence_keywords 
                     if keyword in sentence_lower)
        
        # Confianza basada en número de palabras clave
        return min(0.6 + (matches * 0.1), 0.9)


class SimpleTaskAssigner(TaskAssigner):
    """
    🟢 GREEN - Implementación mínima de asignación de tareas.
    
    Utiliza palabras clave básicas para determinar roles.
    """
    
    def __init__(self, config: Optional[NLPModelConfig] = None):
        self.config = config or NLPModelConfig()
    
    def assign_tasks(self, requirements: List[Requirement]) -> List[AssignedTask]:
        """🟢 GREEN - Asignación básica de tareas"""
        tasks = []
        
        for requirement in requirements:
            role = self.determine_role(requirement)
            
            task = create_assigned_task(
                requirement_id=requirement.id,
                title=self._generate_task_title(requirement),
                description=requirement.description,
                role=role,
                priority=requirement.priority,
                confidence=requirement.confidence_score * 0.9  # Slightly lower than requirement
            )
            
            tasks.append(task)
        
        return tasks
    
    def determine_role(self, requirement: Requirement) -> DeveloperRole:
        """🟢 GREEN - Determinación básica de rol por palabras clave"""
        description_lower = requirement.description.lower()
        
        # Buscar coincidencias con palabras clave de roles
        for role, keywords in self.config.role_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return role
        
        # Default: Full Stack Developer
        return DeveloperRole.FULLSTACK_DEVELOPER
    
    def _generate_task_title(self, requirement: Requirement) -> str:
        """Generar título de tarea basado en el requisito"""
        # Extraer acción y objeto del requisito
        description = requirement.description.lower()
        
        if "implementar" in description or "implement" in description:
            action = "Implementar"
        elif "diseñar" in description or "design" in description:
            action = "Diseñar"
        elif "crear" in description or "create" in description:
            action = "Crear"
        elif "configurar" in description or "configure" in description:
            action = "Configurar"
        else:
            action = "Desarrollar"
        
        # Extraer objeto principal
        objects = {
            "api": "API",
            "interfaz": "Interfaz",
            "autenticación": "Sistema de Autenticación",
            "login": "Sistema de Login",
            "base de datos": "Base de Datos",
            "endpoint": "Endpoint",
            "componente": "Componente",
            "página": "Página"
        }
        
        for keyword, obj in objects.items():
            if keyword in description:
                return f"{action} {obj}"
        
        # Título genérico si no se encuentra patrón específico
        return f"{action} funcionalidad requerida"


# ================================================================================================
# 🎯 SERVICIO PRINCIPAL - NLP PROCESSOR
# ================================================================================================

class NLPProcessor:
    """
    🟢 TDD GREEN - Procesador principal de NLP (RF3.0, RF4.0).
    
    Coordina la extracción de requisitos y asignación de tareas.
    Implementa Clean Architecture con inyección de dependencias.
    """
    
    def __init__(
        self,
        requirement_extractor: Optional[RequirementExtractor] = None,
        task_assigner: Optional[TaskAssigner] = None,
        config: Optional[NLPModelConfig] = None
    ):
        """
        🏗️ Constructor con Dependency Injection (Clean Architecture).
        
        Permite inyectar implementaciones específicas para testing y flexibilidad.
        """
        self.config = config or NLPModelConfig()
        self.requirement_extractor = requirement_extractor or SimpleRequirementExtractor(self.config)
        self.task_assigner = task_assigner or SimpleTaskAssigner(self.config)
    
    def procesar_transcripcion(self, request: ProcessingRequest) -> ProcessingResult:
        """
        🟢 GREEN - Función principal de procesamiento (RF3.0, RF4.0).
        
        Implementación mínima que pasa todos los tests TDD.
        """
        start_time = time.time()
        
        try:
            # Validaciones de entrada
            self._validate_request(request)
            
            # Calcular estadísticas básicas del texto
            stats = self._calculate_text_stats(request.transcription_text)
            
            # Verificar si hay suficientes datos
            if stats.total_words < 20:
                return ProcessingResult(
                    success=False,
                    meeting_id=request.meeting_id,
                    error_message="No requirements detected",
                    stats=stats,
                    processing_time_seconds=time.time() - start_time
                )
            
            # Extracción de requisitos (RF3.0)
            requirements = self.requirement_extractor.extract_requirements(
                request.transcription_text, 
                request.language
            )
            
            # Verificar si se encontraron requisitos
            if not requirements:
                return ProcessingResult(
                    success=False,
                    meeting_id=request.meeting_id,
                    error_message="No requirements detected",
                    stats=stats,
                    processing_time_seconds=time.time() - start_time
                )
            
            # Asignación inteligente de tareas (RF4.0)
            assigned_tasks = self.task_assigner.assign_tasks(requirements)
            
            # Calcular confianza general
            confidence_score = self._calculate_overall_confidence(requirements)
            
            # Tiempo de procesamiento
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                meeting_id=request.meeting_id,
                requirements=requirements,
                assigned_tasks=assigned_tasks,
                processing_time_seconds=processing_time,
                processed_at=datetime.utcnow(),
                confidence_score=confidence_score,
                stats=stats,
                model_version="1.0.0-green"
            )
            
        except InvalidTranscriptionException as e:
            raise e  # Re-raise validation exceptions
        
        except Exception as e:
            # Crear excepción de procesamiento con contexto
            raise create_processing_error(
                stage="transcription_processing",
                original_error=e,
                meeting_id=request.meeting_id,
                context={"text_length": len(request.transcription_text)}
            )
    
    async def procesar_transcripcion_async(self, request: ProcessingRequest) -> ProcessingResult:
        """🟢 GREEN - Versión asíncrona del procesamiento"""
        # Para la fase GREEN, simplemente llamamos a la versión síncrona
        # En REFACTOR se implementará procesamiento verdaderamente asíncrono
        return self.procesar_transcripcion(request)
    
    def _validate_request(self, request: ProcessingRequest) -> None:
        """Validar request de procesamiento"""
        if not request.transcription_text or not request.transcription_text.strip():
            raise InvalidTranscriptionException(
                "Transcription text cannot be empty",
                transcription_length=len(request.transcription_text),
                min_required_length=10
            )
        
        if len(request.transcription_text.strip()) < 10:
            raise InvalidTranscriptionException(
                "Transcription is too short for meaningful processing",
                transcription_length=len(request.transcription_text.strip()),
                min_required_length=10
            )
    
    def _calculate_text_stats(self, text: str) -> ProcessingStats:
        """Calcular estadísticas básicas del texto"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        # Detección básica de idioma
        detected_language = self._detect_language_simple(text)
        
        # Conteo de speakers únicos (simplificado)
        unique_speakers = self._count_unique_speakers(text)
        
        return ProcessingStats(
            total_words=len(words),
            total_sentences=len([s for s in sentences if s.strip()]),
            total_paragraphs=len([p for p in paragraphs if p.strip()]),
            detected_language=detected_language,
            language_confidence=0.8,  # Mock confidence
            processing_model="simple-keyword-extractor",
            unique_speakers=unique_speakers,
            avg_sentence_length=len(words) / max(len(sentences), 1),
            complexity_score=min(len(words) / 100, 1.0)
        )
    
    def _detect_language_simple(self, text: str) -> str:
        """Detección simple de idioma basada en palabras clave"""
        spanish_indicators = [
            "necesitamos", "implementar", "debe", "sistema", "usuario", 
            "autenticación", "diseño", "página", "aplicación"
        ]
        
        english_indicators = [
            "need", "implement", "should", "system", "user",
            "authentication", "design", "page", "application"
        ]
        
        text_lower = text.lower()
        
        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        if spanish_count > english_count:
            return "es"
        elif english_count > spanish_count:
            return "en"
        else:
            return "unknown"
    
    def _count_unique_speakers(self, text: str) -> int:
        """Contar speakers únicos basado en patrones de nombres"""
        # Buscar patrones como "Nombre:" al inicio de líneas
        speakers = set()
        lines = text.split('\n')
        
        for line in lines:
            match = re.match(r'^([A-Z][a-z]+):\s*', line)
            if match:
                speakers.add(match.group(1))
        
        return max(len(speakers), 1)  # Al menos 1 speaker
    
    def _calculate_overall_confidence(self, requirements: List[Requirement]) -> float:
        """Calcular confianza general del procesamiento"""
        if not requirements:
            return 0.0
        
        total_confidence = sum(req.confidence_score for req in requirements)
        avg_confidence = total_confidence / len(requirements)
        
        # Ajustar confianza basada en número de requisitos encontrados
        requirement_count_factor = min(len(requirements) / 5, 1.0)
        
        return avg_confidence * requirement_count_factor
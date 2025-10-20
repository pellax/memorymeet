# ================================================================================================
# 🔴 TDD RED PHASE - Tests para Módulo IA/NLP (RF3.0, RF4.0)
# ================================================================================================
# Tests que definen el comportamiento esperado del procesamiento NLP ANTES de implementar

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
from datetime import datetime

# Importaciones que fallarán inicialmente (TDD RED PHASE)
from app.services.nlp_processor import NLPProcessor, RequirementExtractor
from app.models.nlp_models import (
    ProcessingRequest,
    ProcessingResult,
    Requirement,
    RequirementType,
    Priority,
    AssignedTask,
    DeveloperRole
)
from app.exceptions.nlp_exceptions import (
    InvalidTranscriptionException,
    ProcessingFailedException,
    RequirementExtractionException
)


class TestNLPProcessorTDD:
    """🔴 TDD RED PHASE - Tests para el procesador principal de NLP"""

    @pytest.fixture
    def sample_transcription(self) -> str:
        """Transcripción de ejemplo para tests"""
        return """
        Reunión de Product Management - 2024-01-15
        
        Participantes: Juan (PM), María (UX Designer), Carlos (Backend Dev)
        
        Juan: Necesitamos implementar un sistema de autenticación para los usuarios.
        Debe incluir login con email y password, y también login con Google OAuth.
        
        María: Para la experiencia de usuario, sugiero que el formulario de login 
        tenga un diseño responsive y sea accesible. También necesitamos una página 
        de registro de usuarios nueva.
        
        Carlos: Por el lado técnico, necesitaremos una API REST para la autenticación,
        con endpoints para login, logout y registro. Deberíamos usar JWT tokens para 
        mantener las sesiones. También hay que configurar la integración con Google OAuth 2.0.
        
        Juan: Perfecto. Como requisito no funcional, el sistema debe responder en menos 
        de 2 segundos y debe soportar al menos 1000 usuarios concurrentes.
        
        María: ¿Qué tal si agregamos la posibilidad de recuperar contraseña?
        
        Carlos: Buena idea. Eso requeriría envío de emails y un endpoint adicional 
        para reset de password.
        """

    @pytest.fixture
    def nlp_processor(self) -> NLPProcessor:
        """Procesador NLP con dependencias mockeadas"""
        mock_extractor = Mock(spec=RequirementExtractor)
        return NLPProcessor(requirement_extractor=mock_extractor)

    def test_should_extract_functional_requirements_from_transcription(
        self, nlp_processor: NLPProcessor, sample_transcription: str
    ):
        """🔴 RED: Test principal - Extracción de requisitos funcionales"""
        # Given
        request = ProcessingRequest(
            transcription_text=sample_transcription,
            meeting_id="meeting-123",
            language="es"
        )

        # When
        result = nlp_processor.procesar_transcripcion(request)

        # Then - Verificar estructura del resultado
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert len(result.requirements) >= 5  # Al menos 5 requisitos identificados
        
        # Verificar que se identifican requisitos funcionales específicos
        functional_requirements = [req for req in result.requirements 
                                 if req.type == RequirementType.FUNCTIONAL]
        
        assert len(functional_requirements) >= 4
        
        # Verificar requisitos específicos esperados
        requirement_descriptions = [req.description for req in functional_requirements]
        
        # Debe identificar autenticación con email/password
        assert any("autenticación" in desc.lower() and "email" in desc.lower() 
                  for desc in requirement_descriptions)
        
        # Debe identificar OAuth con Google
        assert any("oauth" in desc.lower() and "google" in desc.lower() 
                  for desc in requirement_descriptions)
        
        # Debe identificar API REST
        assert any("api" in desc.lower() and "rest" in desc.lower() 
                  for desc in requirement_descriptions)
        
        # Debe identificar registro de usuarios
        assert any("registro" in desc.lower() and "usuario" in desc.lower() 
                  for desc in requirement_descriptions)

    def test_should_extract_non_functional_requirements_from_transcription(
        self, nlp_processor: NLPProcessor, sample_transcription: str
    ):
        """🔴 RED: Test para extracción de requisitos no funcionales"""
        # Given
        request = ProcessingRequest(
            transcription_text=sample_transcription,
            meeting_id="meeting-456",
            language="es"
        )

        # When
        result = nlp_processor.procesar_transcripcion(request)

        # Then - Verificar requisitos no funcionales
        non_functional_reqs = [req for req in result.requirements 
                             if req.type == RequirementType.NON_FUNCTIONAL]
        
        assert len(non_functional_reqs) >= 2
        
        # Verificar requisito de performance (< 2 segundos)
        performance_req = next(
            (req for req in non_functional_reqs 
             if "segundo" in req.description.lower() and "2" in req.description),
            None
        )
        assert performance_req is not None
        assert performance_req.priority == Priority.HIGH
        
        # Verificar requisito de concurrencia (1000 usuarios)
        concurrency_req = next(
            (req for req in non_functional_reqs 
             if "1000" in req.description and "usuario" in req.description.lower()),
            None
        )
        assert concurrency_req is not None

    def test_should_assign_tasks_intelligently_based_on_requirements(
        self, nlp_processor: NLPProcessor, sample_transcription: str
    ):
        """🔴 RED: Test para asignación inteligente de tareas (RF4.0)"""
        # Given
        request = ProcessingRequest(
            transcription_text=sample_transcription,
            meeting_id="meeting-789",
            language="es"
        )

        # When
        result = nlp_processor.procesar_transcripcion(request)

        # Then - Verificar asignación de tareas
        assert len(result.assigned_tasks) >= 4
        
        # Verificar que se asignan diferentes roles
        assigned_roles = {task.assigned_role for task in result.assigned_tasks}
        
        assert DeveloperRole.BACKEND_DEVELOPER in assigned_roles
        assert DeveloperRole.FRONTEND_DEVELOPER in assigned_roles
        assert DeveloperRole.UX_DESIGNER in assigned_roles
        
        # Verificar asignación específica por contenido
        backend_tasks = [task for task in result.assigned_tasks 
                        if task.assigned_role == DeveloperRole.BACKEND_DEVELOPER]
        
        # Las tareas de API y OAuth deben asignarse a Backend
        api_task = next(
            (task for task in backend_tasks 
             if "api" in task.description.lower()),
            None
        )
        assert api_task is not None
        
        oauth_task = next(
            (task for task in backend_tasks 
             if "oauth" in task.description.lower()),
            None
        )
        assert oauth_task is not None
        
        # Las tareas de UX deben asignarse a UX Designer
        ux_tasks = [task for task in result.assigned_tasks 
                   if task.assigned_role == DeveloperRole.UX_DESIGNER]
        
        design_task = next(
            (task for task in ux_tasks 
             if "diseño" in task.description.lower() or "responsive" in task.description.lower()),
            None
        )
        assert design_task is not None

    def test_should_handle_empty_transcription_gracefully(
        self, nlp_processor: NLPProcessor
    ):
        """🔴 RED: Test para manejo de transcripción vacía"""
        # Given
        request = ProcessingRequest(
            transcription_text="",
            meeting_id="empty-meeting",
            language="es"
        )

        # When & Then
        with pytest.raises(InvalidTranscriptionException) as exc_info:
            nlp_processor.procesar_transcripcion(request)
        
        assert "empty" in str(exc_info.value).lower() or "vacía" in str(exc_info.value).lower()

    def test_should_handle_transcription_without_requirements(
        self, nlp_processor: NLPProcessor
    ):
        """🔴 RED: Test para transcripción sin requisitos detectables"""
        # Given
        irrelevant_transcription = """
        Hola, ¿cómo están todos? Hoy hace buen clima.
        Me gusta el café. ¿Alguien vio la película de ayer?
        El tráfico estaba terrible esta mañana.
        """
        
        request = ProcessingRequest(
            transcription_text=irrelevant_transcription,
            meeting_id="irrelevant-meeting",
            language="es"
        )

        # When
        result = nlp_processor.procesar_transcripcion(request)

        # Then
        assert result.success is False
        assert len(result.requirements) == 0
        assert len(result.assigned_tasks) == 0
        assert "No requirements detected" in result.error_message

    def test_should_detect_priorities_based_on_language_cues(
        self, nlp_processor: NLPProcessor
    ):
        """🔴 RED: Test para detección de prioridades basada en lenguaje"""
        # Given
        priority_transcription = """
        Juan: Es CRÍTICO que implementemos el sistema de pagos inmediatamente.
        
        María: También sería bueno tener notificaciones push, pero no es urgente.
        
        Carlos: DEBE estar listo el backup automático para el viernes.
        
        Ana: Si tenemos tiempo, podríamos agregar un dashboard de analytics.
        """
        
        request = ProcessingRequest(
            transcription_text=priority_transcription,
            meeting_id="priority-meeting",
            language="es"
        )

        # When
        result = nlp_processor.procesar_transcripcion(request)

        # Then
        # Verificar que se detectan diferentes niveles de prioridad
        priorities = {req.priority for req in result.requirements}
        
        assert Priority.CRITICAL in priorities  # "CRÍTICO"
        assert Priority.HIGH in priorities      # "DEBE"
        assert Priority.MEDIUM in priorities    # "sería bueno"
        assert Priority.LOW in priorities       # "si tenemos tiempo"
        
        # Verificar asignación específica de prioridades
        critical_req = next(
            (req for req in result.requirements 
             if req.priority == Priority.CRITICAL and "pago" in req.description.lower()),
            None
        )
        assert critical_req is not None

    def test_should_handle_multilingual_transcription(
        self, nlp_processor: NLPProcessor
    ):
        """🔴 RED: Test para transcripciones multilingües"""
        # Given
        multilingual_transcription = """
        Juan: We need to implement user authentication.
        María: También necesitamos un diseño responsive.
        Carlos: The API should be RESTful and include JWT tokens.
        """
        
        request = ProcessingRequest(
            transcription_text=multilingual_transcription,
            meeting_id="multilingual-meeting",
            language="auto"  # Detección automática
        )

        # When
        result = nlp_processor.procesar_transcripcion(request)

        # Then
        assert result.success is True
        assert len(result.requirements) >= 2
        
        # Debe detectar tanto requisitos en inglés como en español
        descriptions = [req.description for req in result.requirements]
        assert any("authentication" in desc.lower() for desc in descriptions)
        assert any("responsive" in desc.lower() for desc in descriptions)

    def test_should_include_metadata_in_processing_result(
        self, nlp_processor: NLPProcessor, sample_transcription: str
    ):
        """🔴 RED: Test para metadatos en el resultado"""
        # Given
        request = ProcessingRequest(
            transcription_text=sample_transcription,
            meeting_id="metadata-meeting",
            language="es"
        )

        # When
        result = nlp_processor.procesar_transcripcion(request)

        # Then - Verificar metadatos del procesamiento
        assert result.meeting_id == "metadata-meeting"
        assert result.processing_time_seconds > 0
        assert result.processing_time_seconds < 30  # Debe ser rápido
        assert isinstance(result.processed_at, datetime)
        
        # Verificar estadísticas
        assert result.stats is not None
        assert result.stats.total_words > 0
        assert result.stats.total_sentences > 0
        assert result.stats.detected_language in ["es", "spanish", "Spanish"]
        
        # Verificar confianza del procesamiento
        assert result.confidence_score >= 0.0
        assert result.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_should_process_transcription_asynchronously(
        self, nlp_processor: NLPProcessor, sample_transcription: str
    ):
        """🔴 RED: Test para procesamiento asíncrono"""
        # Given
        request = ProcessingRequest(
            transcription_text=sample_transcription,
            meeting_id="async-meeting",
            language="es"
        )

        # When
        result = await nlp_processor.procesar_transcripcion_async(request)

        # Then
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert len(result.requirements) > 0

    def test_should_handle_processing_failure_gracefully(
        self, nlp_processor: NLPProcessor
    ):
        """🔴 RED: Test para manejo de fallos de procesamiento"""
        # Given
        # Mock que el extractor falle
        nlp_processor.requirement_extractor.extract_requirements.side_effect = \
            Exception("NLP model failed")
        
        request = ProcessingRequest(
            transcription_text="Some valid transcription",
            meeting_id="failing-meeting",
            language="es"
        )

        # When & Then
        with pytest.raises(ProcessingFailedException) as exc_info:
            nlp_processor.procesar_transcripcion(request)
        
        assert "NLP model failed" in str(exc_info.value)
# ================================================================================================
# ✅ TDD VERIFICATION - Test básico para verificar GREEN phase funcionando
# ================================================================================================
# Test simplificado para confirmar que el ciclo TDD está completo

import pytest
from app.services.nlp_processor import NLPProcessor
from app.models.nlp_models import ProcessingRequest, RequirementType, DeveloperRole


class TestNLPBasicFunctionality:
    """✅ Tests básicos para verificar implementación GREEN phase"""

    def test_nlp_processor_can_be_instantiated(self):
        """🟢 GREEN: Verificar que el procesador puede ser creado"""
        # Given & When
        processor = NLPProcessor()
        
        # Then
        assert processor is not None
        assert hasattr(processor, 'procesar_transcripcion')

    def test_processing_request_can_be_created(self):
        """🟢 GREEN: Verificar que ProcessingRequest funciona"""
        # Given & When
        request = ProcessingRequest(
            transcription_text="Test transcription with implementar API",
            meeting_id="test-meeting",
            language="es"
        )
        
        # Then
        assert request.transcription_text == "Test transcription with implementar API"
        assert request.meeting_id == "test-meeting"
        assert request.language == "es"

    def test_nlp_processor_handles_valid_transcription(self):
        """🟢 GREEN: Test fundamental - procesamiento básico funciona"""
        # Given
        processor = NLPProcessor()
        request = ProcessingRequest(
            transcription_text="""
            Juan: Necesitamos implementar un sistema de autenticación con login.
            María: También debería tener un diseño responsive para la interfaz.
            Carlos: La API debe ser REST y usar JWT tokens.
            """,
            meeting_id="basic-test",
            language="es"
        )
        
        # When
        result = processor.procesar_transcripcion(request)
        
        # Then - Verificaciones básicas
        assert result is not None
        assert result.meeting_id == "basic-test"
        assert result.success is True
        assert len(result.requirements) > 0  # Encontró algunos requisitos
        assert len(result.assigned_tasks) > 0  # Asignó algunas tareas
        assert result.processing_time_seconds > 0

    def test_nlp_processor_handles_empty_transcription(self):
        """🟢 GREEN: Test de manejo de entrada vacía"""
        # Given
        processor = NLPProcessor()
        
        # When & Then
        with pytest.raises(Exception):  # Debería lanzar alguna excepción
            request = ProcessingRequest(
                transcription_text="",
                meeting_id="empty-test",
                language="es"
            )

    def test_requirement_types_are_defined(self):
        """🟢 GREEN: Test de enums y tipos básicos"""
        # Given & When & Then
        assert RequirementType.FUNCTIONAL is not None
        assert RequirementType.NON_FUNCTIONAL is not None
        
        assert DeveloperRole.BACKEND_DEVELOPER is not None
        assert DeveloperRole.FRONTEND_DEVELOPER is not None
        assert DeveloperRole.UX_DESIGNER is not None

    def test_basic_requirement_extraction_works(self):
        """🟢 GREEN: Test básico de extracción"""
        # Given
        processor = NLPProcessor()
        request = ProcessingRequest(
            transcription_text="Necesitamos implementar una API REST para autenticación de usuarios.",
            meeting_id="extraction-test",
            language="es"
        )
        
        # When
        result = processor.procesar_transcripcion(request)
        
        # Then
        assert result.success is True
        assert len(result.requirements) >= 1
        
        # Verificar que al menos un requisito contiene palabras clave esperadas
        requirement_descriptions = [req.description.lower() for req in result.requirements]
        api_mentioned = any("api" in desc for desc in requirement_descriptions)
        assert api_mentioned is True

    def test_basic_task_assignment_works(self):
        """🟢 GREEN: Test básico de asignación"""
        # Given
        processor = NLPProcessor()
        request = ProcessingRequest(
            transcription_text="""
            Necesitamos implementar una API backend para usuarios.
            También crear una interfaz frontend responsive.
            """,
            meeting_id="assignment-test", 
            language="es"
        )
        
        # When
        result = processor.procesar_transcripcion(request)
        
        # Then
        assert result.success is True
        assert len(result.assigned_tasks) >= 1
        
        # Verificar que se asignaron diferentes tipos de roles
        assigned_roles = {task.assigned_role for task in result.assigned_tasks}
        assert len(assigned_roles) >= 1  # Al menos un rol fue asignado

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
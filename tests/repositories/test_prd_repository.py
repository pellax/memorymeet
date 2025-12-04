"""
🔴 RED PHASE - TDD Tests for PRDRepository

Tests que definen el comportamiento esperado del PRDRepository.
Valida persistencia de PRDs con requisitos JSON y relaciones con Meeting.
"""
import pytest
from uuid import uuid4
from datetime import datetime

# Imports ajustados para Docker (PYTHONPATH=/app)
from app.models import PRD, Meeting, MeetingStatus
from app.repositories.prd_repository import PRDRepository
from app.repositories.meeting_repository import MeetingRepository
from app.database import DatabaseSessionManager


class TestPRDRepositoryACID:
    """✅ TDD RED - Tests que definen comportamiento ACID del PRDRepository."""
    
    @pytest.fixture
    def db_manager(self):
        """Setup de database manager con SQLite en memoria para tests."""
        db_manager = DatabaseSessionManager(database_url="sqlite:///:memory:")
        db_manager.create_all_tables()
        yield db_manager
        db_manager.drop_all_tables()
    
    @pytest.fixture
    def prd_repository(self, db_manager):
        """Fixture que crea instancia de PRDRepository."""
        return PRDRepository(db_manager)
    
    @pytest.fixture
    def meeting_repository(self, db_manager):
        """Fixture para crear meetings de prueba."""
        return MeetingRepository(db_manager)
    
    @pytest.fixture
    def sample_meeting(self, meeting_repository):
        """Crea una reunión de prueba."""
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/test",
            user_id="user-123",
            status=MeetingStatus.COMPLETED
        )
        return meeting_repository.save(meeting)
    
    # ===== ATOMICITY TESTS =====
    
    def test_should_save_prd_with_requirements_atomically(
        self, prd_repository, sample_meeting
    ):
        """
        🔴 RED - Test para guardar PRD con requisitos JSON.
        
        Verifica que PRD se guarde completamente con todos sus requisitos.
        """
        # Given
        requirements = [
            {
                "id": "req-1",
                "description": "Implementar autenticación de usuarios",
                "type": "functional",
                "priority": "high"
            },
            {
                "id": "req-2",
                "description": "Sistema debe responder en < 200ms",
                "type": "non_functional",
                "priority": "medium"
            }
        ]
        
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="Sistema de Autenticación",
            description="PRD para módulo de autenticación",
            requirements=requirements,
            meeting_id=sample_meeting.id,
            confidence_score="0.85",
            language_detected="es"
        )
        
        # When
        saved_prd = prd_repository.save(prd)
        
        # Then - ATOMICITY: Todos los datos guardados
        assert saved_prd is not None
        assert saved_prd.id == prd.id
        assert saved_prd.title == prd.title
        assert len(saved_prd.requirements) == 2
        assert saved_prd.meeting_id == sample_meeting.id
    
    def test_should_rollback_prd_save_on_invalid_meeting_id(
        self, prd_repository
    ):
        """
        🔴 RED - Test para rollback con meeting_id inválido.
        
        Verifica integridad referencial con Meeting.
        """
        # Given - PRD con meeting_id que no existe
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="PRD Inválido",
            requirements=[{"id": "req-1", "description": "Test"}],
            meeting_id="nonexistent-meeting-id"  # ❌ No existe
        )
        
        # When & Then - Debe fallar por FK constraint
        with pytest.raises(Exception):
            prd_repository.save(prd)
    
    # ===== CONSISTENCY TESTS =====
    
    def test_should_validate_prd_required_fields(self, prd_repository, sample_meeting):
        """
        🔴 RED - Test para validación de campos obligatorios.
        
        Verifica que se validen reglas de negocio.
        """
        # Given - PRD sin título
        invalid_prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="",  # ❌ Título vacío
            requirements=[],
            meeting_id=sample_meeting.id
        )
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            prd_repository.save(invalid_prd)
        
        assert "title is required" in str(exc_info.value).lower()
    
    def test_should_validate_at_least_one_requirement(
        self, prd_repository, sample_meeting
    ):
        """
        🔴 RED - Test para validar que PRD tenga al menos un requisito.
        """
        # Given - PRD sin requisitos
        prd_without_requirements = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="PRD Sin Requisitos",
            requirements=[],  # ❌ Sin requisitos
            meeting_id=sample_meeting.id
        )
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            prd_repository.save(prd_without_requirements)
        
        assert "at least one requirement" in str(exc_info.value).lower()
    
    # ===== READ OPERATIONS TESTS =====
    
    def test_should_get_prd_by_id(self, prd_repository, sample_meeting):
        """🔴 RED - Test para obtener PRD por ID."""
        # Given
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="Test PRD",
            requirements=[{"id": "req-1", "description": "Test requirement"}],
            meeting_id=sample_meeting.id
        )
        saved_prd = prd_repository.save(prd)
        
        # When
        retrieved = prd_repository.get_by_id(saved_prd.id)
        
        # Then
        assert retrieved is not None
        assert retrieved.id == saved_prd.id
        assert retrieved.title == saved_prd.title
    
    def test_should_return_none_for_nonexistent_prd(self, prd_repository):
        """🔴 RED - Test para PRD inexistente."""
        # When
        retrieved = prd_repository.get_by_id("nonexistent-prd-id")
        
        # Then
        assert retrieved is None
    
    def test_should_get_prd_by_meeting_id(self, prd_repository, sample_meeting):
        """🔴 RED - Test para obtener PRD por meeting_id."""
        # Given
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="Meeting PRD",
            requirements=[{"id": "req-1", "description": "Test"}],
            meeting_id=sample_meeting.id
        )
        prd_repository.save(prd)
        
        # When
        retrieved = prd_repository.get_by_meeting_id(sample_meeting.id)
        
        # Then
        assert retrieved is not None
        assert retrieved.meeting_id == sample_meeting.id
    
    # ===== DOMAIN LOGIC TESTS =====
    
    def test_should_get_functional_requirements_only(
        self, prd_repository, sample_meeting
    ):
        """🔴 RED - Test para filtrar requisitos funcionales."""
        # Given
        requirements = [
            {"id": "req-1", "type": "functional", "description": "Func 1"},
            {"id": "req-2", "type": "non_functional", "description": "Non-func 1"},
            {"id": "req-3", "type": "functional", "description": "Func 2"}
        ]
        
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="Mixed Requirements PRD",
            requirements=requirements,
            meeting_id=sample_meeting.id
        )
        saved_prd = prd_repository.save(prd)
        
        # When
        retrieved = prd_repository.get_by_id(saved_prd.id)
        functional_reqs = retrieved.functional_requirements
        
        # Then
        assert len(functional_reqs) == 2
        assert all(req["type"] == "functional" for req in functional_reqs)
    
    def test_should_calculate_prd_complexity(self, prd_repository, sample_meeting):
        """🔴 RED - Test para cálculo de complejidad del PRD."""
        # Given - PRD con 5 requisitos (complejidad MEDIA)
        requirements = [
            {"id": f"req-{i}", "description": f"Requirement {i}"} 
            for i in range(5)
        ]
        
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="Medium Complexity PRD",
            requirements=requirements,
            meeting_id=sample_meeting.id
        )
        saved_prd = prd_repository.save(prd)
        
        # When
        retrieved = prd_repository.get_by_id(saved_prd.id)
        complexity = retrieved.calculate_complexity()
        
        # Then
        assert complexity == "MEDIUM"
    
    # ===== UPDATE OPERATIONS TESTS =====
    
    def test_should_update_prd_requirements(self, prd_repository, sample_meeting):
        """🔴 RED - Test para actualizar requisitos del PRD."""
        # Given
        initial_requirements = [
            {"id": "req-1", "description": "Initial requirement"}
        ]
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="Updatable PRD",
            requirements=initial_requirements,
            meeting_id=sample_meeting.id
        )
        saved_prd = prd_repository.save(prd)
        
        # When - Agregar nuevo requisito
        new_requirements = initial_requirements + [
            {"id": "req-2", "description": "New requirement"}
        ]
        
        updated_prd = prd_repository.update_requirements(
            saved_prd.id, new_requirements
        )
        
        # Then
        assert len(updated_prd.requirements) == 2
        assert updated_prd.requirements[1]["id"] == "req-2"
    
    # ===== DELETE OPERATIONS TESTS =====
    
    def test_should_delete_prd(self, prd_repository, sample_meeting):
        """🔴 RED - Test para eliminar PRD."""
        # Given
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="Deletable PRD",
            requirements=[{"id": "req-1", "description": "Test"}],
            meeting_id=sample_meeting.id
        )
        saved_prd = prd_repository.save(prd)
        
        # When
        result = prd_repository.delete(saved_prd.id)
        
        # Then
        assert result is True
        assert prd_repository.get_by_id(saved_prd.id) is None
    
    def test_should_return_false_when_deleting_nonexistent_prd(
        self, prd_repository
    ):
        """🔴 RED - Test para delete de PRD inexistente."""
        # When
        result = prd_repository.delete("nonexistent-prd-id")
        
        # Then
        assert result is False

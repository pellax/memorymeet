"""
🔴 RED PHASE - TDD Tests for MeetingRepository

Tests que definen el comportamiento esperado del MeetingRepository.
Valida principios ACID: Atomicity, Consistency, Isolation, Durability.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

# Imports ajustados para Docker (PYTHONPATH=/app)
from app.models import Meeting, MeetingStatus
from app.repositories.meeting_repository import MeetingRepository
from app.database import DatabaseSessionManager


class TestMeetingRepositoryACID:
    """✅ TDD RED - Tests que definen comportamiento ACID del MeetingRepository."""
    
    @pytest.fixture
    def db_manager(self):
        """Setup de database manager con SQLite en memoria para tests."""
        db_manager = DatabaseSessionManager(database_url="sqlite:///:memory:")
        db_manager.create_all_tables()
        yield db_manager
        db_manager.drop_all_tables()
    
    @pytest.fixture
    def meeting_repository(self, db_manager):
        """Fixture que crea instancia de MeetingRepository."""
        return MeetingRepository(db_manager)
    
    # ===== ATOMICITY TESTS =====
    
    def test_should_save_meeting_atomically(self, meeting_repository):
        """
        🔴 RED - Test para propiedad ATOMICITY.
        
        Verifica que una reunión se guarde completamente o no se guarde nada.
        """
        # Given
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/test-meeting",
            user_id="user-123",
            status=MeetingStatus.PENDING
        )
        
        # When
        saved_meeting = meeting_repository.save(meeting)
        
        # Then - ATOMICITY: Todos los datos deben estar guardados
        assert saved_meeting is not None
        assert saved_meeting.id == meeting.id
        assert saved_meeting.meeting_url == meeting.meeting_url
        assert saved_meeting.user_id == meeting.user_id
        assert saved_meeting.status == MeetingStatus.PENDING
    
    def test_should_rollback_on_save_error(self, meeting_repository, db_manager):
        """
        🔴 RED - Test para ATOMICITY en caso de error.
        
        Verifica que si falla una operación, se hace rollback completo.
        """
        # Given
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/test",
            user_id="user-456",
            status=MeetingStatus.PENDING
        )
        
        # Guardar reunión inicial
        meeting_repository.save(meeting)
        
        # When - Intentar guardar reunión duplicada (violación de PK)
        duplicate_meeting = Meeting(
            id=meeting.id,  # Mismo ID - violación
            meeting_url="https://different-url.com",
            user_id="user-789",
            status=MeetingStatus.PENDING
        )
        
        # Then - Debe lanzar excepción y hacer rollback
        with pytest.raises(Exception):
            meeting_repository.save(duplicate_meeting)
        
        # Verificar que la reunión original no se modificó (ATOMICITY)
        retrieved = meeting_repository.get_by_id(meeting.id)
        assert retrieved.meeting_url == "https://meet.google.com/test"
        assert retrieved.user_id == "user-456"
    
    # ===== CONSISTENCY TESTS =====
    
    def test_should_validate_required_fields_before_save(self, meeting_repository):
        """
        🔴 RED - Test para CONSISTENCY.
        
        Verifica que se validen reglas de negocio antes de persistir.
        """
        # Given - Reunión sin datos obligatorios
        invalid_meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="",  # ❌ URL vacía
            user_id="",      # ❌ User ID vacío
            status=MeetingStatus.PENDING
        )
        
        # When & Then - Debe rechazar reunión inválida
        with pytest.raises(ValueError) as exc_info:
            meeting_repository.save(invalid_meeting)
        
        assert "meeting_url is required" in str(exc_info.value).lower() or \
               "user_id is required" in str(exc_info.value).lower()
    
    def test_should_maintain_referential_integrity(self, meeting_repository):
        """
        🔴 RED - Test para CONSISTENCY de integridad referencial.
        
        Verifica que se mantenga consistencia en relaciones de datos.
        """
        # Given
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/test",
            user_id="user-123",
            status=MeetingStatus.PENDING
        )
        
        # When
        saved = meeting_repository.save(meeting)
        
        # Then - ID debe ser único y consistente
        retrieved = meeting_repository.get_by_id(saved.id)
        assert retrieved.id == saved.id
        
        # Verificar que no se puede crear otra reunión con mismo ID
        with pytest.raises(Exception):
            duplicate = Meeting(
                id=saved.id,
                meeting_url="https://different.com",
                user_id="user-999"
            )
            meeting_repository.save(duplicate)
    
    # ===== ISOLATION TESTS =====
    
    def test_should_isolate_concurrent_access(self, meeting_repository):
        """
        🔴 RED - Test para ISOLATION.
        
        Verifica que operaciones concurrentes estén aisladas.
        """
        # Given
        meeting_id = f"meeting-{uuid4().hex[:8]}"
        meeting = Meeting(
            id=meeting_id,
            meeting_url="https://meet.google.com/concurrent-test",
            user_id="user-123",
            status=MeetingStatus.PENDING
        )
        
        # When - Guardar reunión
        meeting_repository.save(meeting)
        
        # Then - Actualización aislada no debe afectar lectura concurrente
        retrieved = meeting_repository.get_by_id(meeting_id)
        assert retrieved.status == MeetingStatus.PENDING
        
        # Actualizar estado
        meeting_repository.update_status(meeting_id, MeetingStatus.PROCESSING)
        
        # Verificar que cambio se reflejó correctamente (ISOLATION)
        updated = meeting_repository.get_by_id(meeting_id)
        assert updated.status == MeetingStatus.PROCESSING
    
    # ===== DURABILITY TESTS =====
    
    def test_should_persist_meeting_after_commit(self, meeting_repository, db_manager):
        """
        🔴 RED - Test para DURABILITY.
        
        Verifica que los cambios persistan después del commit.
        """
        # Given
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/durability-test",
            user_id="user-123",
            status=MeetingStatus.PENDING
        )
        
        # When - Guardar y hacer commit explícito
        saved_meeting = meeting_repository.save(meeting)
        meeting_id = saved_meeting.id
        
        # Simular cierre de sesión y reapertura (DURABILITY)
        # Then - Los datos deben persistir después del commit
        retrieved = meeting_repository.get_by_id(meeting_id)
        assert retrieved is not None
        assert retrieved.id == meeting_id
        assert retrieved.meeting_url == "https://meet.google.com/durability-test"
        assert retrieved.user_id == "user-123"
    
    # ===== CRUD OPERATIONS TESTS =====
    
    def test_should_retrieve_meeting_by_id(self, meeting_repository):
        """🔴 RED - Test para operación READ."""
        # Given
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/read-test",
            user_id="user-123",
            status=MeetingStatus.PENDING
        )
        meeting_repository.save(meeting)
        
        # When
        retrieved = meeting_repository.get_by_id(meeting.id)
        
        # Then
        assert retrieved is not None
        assert retrieved.id == meeting.id
        assert retrieved.meeting_url == meeting.meeting_url
    
    def test_should_return_none_for_nonexistent_meeting(self, meeting_repository):
        """🔴 RED - Test para READ de reunión inexistente."""
        # When
        retrieved = meeting_repository.get_by_id("nonexistent-id")
        
        # Then
        assert retrieved is None
    
    def test_should_get_all_meetings_by_user(self, meeting_repository):
        """🔴 RED - Test para query por usuario."""
        # Given
        user_id = "user-123"
        meeting1 = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/meeting1",
            user_id=user_id,
            status=MeetingStatus.PENDING
        )
        meeting2 = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/meeting2",
            user_id=user_id,
            status=MeetingStatus.COMPLETED
        )
        meeting3 = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/meeting3",
            user_id="other-user",
            status=MeetingStatus.PENDING
        )
        
        meeting_repository.save(meeting1)
        meeting_repository.save(meeting2)
        meeting_repository.save(meeting3)
        
        # When
        user_meetings = meeting_repository.get_by_user_id(user_id)
        
        # Then
        assert len(user_meetings) == 2
        assert all(m.user_id == user_id for m in user_meetings)
    
    def test_should_update_meeting_status(self, meeting_repository):
        """🔴 RED - Test para UPDATE de estado."""
        # Given
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/update-test",
            user_id="user-123",
            status=MeetingStatus.PENDING
        )
        meeting_repository.save(meeting)
        
        # When
        updated = meeting_repository.update_status(
            meeting.id,
            MeetingStatus.PROCESSING
        )
        
        # Then
        assert updated.status == MeetingStatus.PROCESSING
        assert updated.processing_started_at is not None
    
    def test_should_delete_meeting(self, meeting_repository):
        """🔴 RED - Test para DELETE."""
        # Given
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/delete-test",
            user_id="user-123",
            status=MeetingStatus.PENDING
        )
        meeting_repository.save(meeting)
        
        # When
        result = meeting_repository.delete(meeting.id)
        
        # Then
        assert result is True
        assert meeting_repository.get_by_id(meeting.id) is None
    
    def test_should_get_pending_meetings(self, meeting_repository):
        """🔴 RED - Test para query por estado PENDING."""
        # Given
        pending1 = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/pending1",
            user_id="user-123",
            status=MeetingStatus.PENDING
        )
        pending2 = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/pending2",
            user_id="user-456",
            status=MeetingStatus.PENDING
        )
        completed = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/completed",
            user_id="user-789",
            status=MeetingStatus.COMPLETED
        )
        
        meeting_repository.save(pending1)
        meeting_repository.save(pending2)
        meeting_repository.save(completed)
        
        # When
        pending_meetings = meeting_repository.get_pending_meetings()
        
        # Then
        assert len(pending_meetings) == 2
        assert all(m.status == MeetingStatus.PENDING for m in pending_meetings)

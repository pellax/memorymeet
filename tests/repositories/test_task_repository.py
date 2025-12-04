"""
🔴 RED PHASE - TDD Tests for TaskRepository

Tests que definen el comportamiento esperado del TaskRepository.
Valida persistencia de tareas con relaciones a PRD y asignación de roles.
"""
import pytest
from uuid import uuid4

# Imports ajustados para Docker (PYTHONPATH=/app)
from app.models import Task, TaskPriority, TaskStatus, PRD, Meeting, MeetingStatus
from app.repositories.task_repository import TaskRepository
from app.repositories.prd_repository import PRDRepository
from app.repositories.meeting_repository import MeetingRepository
from app.database import DatabaseSessionManager


class TestTaskRepositoryACID:
    """✅ TDD RED - Tests que definen comportamiento ACID del TaskRepository."""
    
    @pytest.fixture
    def db_manager(self):
        """Setup de database manager con SQLite en memoria para tests."""
        db_manager = DatabaseSessionManager(database_url="sqlite:///:memory:")
        db_manager.create_all_tables()
        yield db_manager
        db_manager.drop_all_tables()
    
    @pytest.fixture
    def task_repository(self, db_manager):
        """Fixture que crea instancia de TaskRepository."""
        return TaskRepository(db_manager)
    
    @pytest.fixture
    def prd_repository(self, db_manager):
        """Fixture para PRDRepository."""
        return PRDRepository(db_manager)
    
    @pytest.fixture
    def meeting_repository(self, db_manager):
        """Fixture para MeetingRepository."""
        return MeetingRepository(db_manager)
    
    @pytest.fixture
    def sample_prd(self, prd_repository, meeting_repository):
        """Crea un PRD de prueba con meeting."""
        # Crear meeting primero
        meeting = Meeting(
            id=f"meeting-{uuid4().hex[:8]}",
            meeting_url="https://meet.google.com/test",
            user_id="user-123",
            status=MeetingStatus.COMPLETED
        )
        saved_meeting = meeting_repository.save(meeting)
        
        # Crear PRD
        prd = PRD(
            id=f"prd-{uuid4().hex[:8]}",
            title="Test PRD for Tasks",
            requirements=[
                {"id": "req-1", "description": "Test requirement"}
            ],
            meeting_id=saved_meeting.id
        )
        return prd_repository.save(prd)
    
    # ===== ATOMICITY TESTS =====
    
    def test_should_save_task_atomically(self, task_repository, sample_prd):
        """
        🔴 RED - Test para guardar tarea completa.
        
        Verifica que tarea se guarde con todos sus atributos.
        """
        # Given
        task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Implementar API de autenticación",
            description="Crear endpoints REST para login y registro",
            assigned_role="Backend Developer",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            requirement_id="req-1",
            prd_id=sample_prd.id,
            confidence_score="0.90"
        )
        
        # When
        saved_task = task_repository.save(task)
        
        # Then - ATOMICITY: Todos los datos guardados
        assert saved_task is not None
        assert saved_task.id == task.id
        assert saved_task.title == task.title
        assert saved_task.assigned_role == "Backend Developer"
        assert saved_task.priority == TaskPriority.HIGH
        assert saved_task.prd_id == sample_prd.id
    
    def test_should_rollback_task_save_on_invalid_prd_id(self, task_repository):
        """
        🔴 RED - Test para rollback con prd_id inválido.
        
        Verifica integridad referencial con PRD.
        """
        # Given - Task con prd_id que no existe
        task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Invalid Task",
            assigned_role="Backend Developer",
            prd_id="nonexistent-prd-id"  # ❌ No existe
        )
        
        # When & Then - Debe fallar por FK constraint
        with pytest.raises(Exception):
            task_repository.save(task)
    
    # ===== CONSISTENCY TESTS =====
    
    def test_should_validate_task_required_fields(self, task_repository, sample_prd):
        """
        🔴 RED - Test para validación de campos obligatorios.
        """
        # Given - Task sin título
        invalid_task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="",  # ❌ Título vacío
            assigned_role="Backend Developer",
            prd_id=sample_prd.id
        )
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            task_repository.save(invalid_task)
        
        assert "title is required" in str(exc_info.value).lower()
    
    def test_should_validate_assigned_role(self, task_repository, sample_prd):
        """
        🔴 RED - Test para validar rol asignado.
        """
        # Given - Task sin rol asignado
        task_without_role = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Task Without Role",
            assigned_role="",  # ❌ Sin rol
            prd_id=sample_prd.id
        )
        
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            task_repository.save(task_without_role)
        
        assert "assigned_role is required" in str(exc_info.value).lower()
    
    # ===== READ OPERATIONS TESTS =====
    
    def test_should_get_task_by_id(self, task_repository, sample_prd):
        """🔴 RED - Test para obtener tarea por ID."""
        # Given
        task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Test Task",
            assigned_role="Frontend Developer",
            prd_id=sample_prd.id
        )
        saved_task = task_repository.save(task)
        
        # When
        retrieved = task_repository.get_by_id(saved_task.id)
        
        # Then
        assert retrieved is not None
        assert retrieved.id == saved_task.id
        assert retrieved.title == saved_task.title
    
    def test_should_return_none_for_nonexistent_task(self, task_repository):
        """🔴 RED - Test para tarea inexistente."""
        # When
        retrieved = task_repository.get_by_id("nonexistent-task-id")
        
        # Then
        assert retrieved is None
    
    def test_should_get_tasks_by_prd_id(self, task_repository, sample_prd):
        """🔴 RED - Test para obtener todas las tareas de un PRD."""
        # Given - Crear 3 tareas para el mismo PRD
        task1 = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Task 1",
            assigned_role="Backend Developer",
            prd_id=sample_prd.id
        )
        task2 = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Task 2",
            assigned_role="Frontend Developer",
            prd_id=sample_prd.id
        )
        task3 = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Task 3",
            assigned_role="Backend Developer",
            prd_id=sample_prd.id
        )
        
        task_repository.save(task1)
        task_repository.save(task2)
        task_repository.save(task3)
        
        # When
        prd_tasks = task_repository.get_by_prd_id(sample_prd.id)
        
        # Then
        assert len(prd_tasks) == 3
        assert all(task.prd_id == sample_prd.id for task in prd_tasks)
    
    def test_should_get_tasks_by_assigned_role(self, task_repository, sample_prd):
        """🔴 RED - Test para filtrar tareas por rol asignado."""
        # Given
        backend_task1 = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Backend Task 1",
            assigned_role="Backend Developer",
            prd_id=sample_prd.id
        )
        backend_task2 = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Backend Task 2",
            assigned_role="Backend Developer",
            prd_id=sample_prd.id
        )
        frontend_task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Frontend Task",
            assigned_role="Frontend Developer",
            prd_id=sample_prd.id
        )
        
        task_repository.save(backend_task1)
        task_repository.save(backend_task2)
        task_repository.save(frontend_task)
        
        # When
        backend_tasks = task_repository.get_by_assigned_role("Backend Developer")
        
        # Then
        assert len(backend_tasks) == 2
        assert all(task.assigned_role == "Backend Developer" for task in backend_tasks)
    
    def test_should_get_high_priority_tasks(self, task_repository, sample_prd):
        """🔴 RED - Test para filtrar tareas de alta prioridad."""
        # Given
        critical_task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Critical Task",
            assigned_role="Backend Developer",
            priority=TaskPriority.CRITICAL,
            prd_id=sample_prd.id
        )
        high_task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="High Priority Task",
            assigned_role="Frontend Developer",
            priority=TaskPriority.HIGH,
            prd_id=sample_prd.id
        )
        low_task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Low Priority Task",
            assigned_role="QA Engineer",
            priority=TaskPriority.LOW,
            prd_id=sample_prd.id
        )
        
        task_repository.save(critical_task)
        task_repository.save(high_task)
        task_repository.save(low_task)
        
        # When
        high_priority_tasks = task_repository.get_high_priority_tasks()
        
        # Then
        assert len(high_priority_tasks) == 2
        assert all(task.is_high_priority() for task in high_priority_tasks)
    
    # ===== UPDATE OPERATIONS TESTS =====
    
    def test_should_update_task_status(self, task_repository, sample_prd):
        """🔴 RED - Test para actualizar estado de tarea."""
        # Given
        task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Updatable Task",
            assigned_role="Backend Developer",
            status=TaskStatus.PENDING,
            prd_id=sample_prd.id
        )
        saved_task = task_repository.save(task)
        
        # When
        updated_task = task_repository.update_status(
            saved_task.id, 
            TaskStatus.IN_PROGRESS
        )
        
        # Then
        assert updated_task.status == TaskStatus.IN_PROGRESS
    
    def test_should_link_external_task(self, task_repository, sample_prd):
        """🔴 RED - Test para vincular tarea con sistema externo (Jira)."""
        # Given
        task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Linkable Task",
            assigned_role="Backend Developer",
            prd_id=sample_prd.id
        )
        saved_task = task_repository.save(task)
        
        # When
        external_id = "JIRA-123"
        external_url = "https://jira.example.com/browse/JIRA-123"
        
        updated_task = task_repository.link_external_task(
            saved_task.id,
            external_id,
            external_url
        )
        
        # Then
        assert updated_task.external_task_id == external_id
        assert updated_task.external_task_url == external_url
    
    # ===== DELETE OPERATIONS TESTS =====
    
    def test_should_delete_task(self, task_repository, sample_prd):
        """🔴 RED - Test para eliminar tarea."""
        # Given
        task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Deletable Task",
            assigned_role="Backend Developer",
            prd_id=sample_prd.id
        )
        saved_task = task_repository.save(task)
        
        # When
        result = task_repository.delete(saved_task.id)
        
        # Then
        assert result is True
        assert task_repository.get_by_id(saved_task.id) is None
    
    def test_should_return_false_when_deleting_nonexistent_task(
        self, task_repository
    ):
        """🔴 RED - Test para delete de tarea inexistente."""
        # When
        result = task_repository.delete("nonexistent-task-id")
        
        # Then
        assert result is False
    
    # ===== DOMAIN LOGIC TESTS =====
    
    def test_should_identify_high_priority_task(self, task_repository, sample_prd):
        """🔴 RED - Test para lógica de dominio is_high_priority()."""
        # Given
        critical_task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title="Critical Task",
            assigned_role="Backend Developer",
            priority=TaskPriority.CRITICAL,
            prd_id=sample_prd.id
        )
        saved_task = task_repository.save(critical_task)
        
        # When
        retrieved = task_repository.get_by_id(saved_task.id)
        
        # Then
        assert retrieved.is_high_priority() is True

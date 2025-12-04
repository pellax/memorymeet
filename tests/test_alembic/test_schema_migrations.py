"""
✅ TDD TESTS - ALEMBIC MIGRATIONS VALIDATION
=============================================
Tests que validan que el schema generado por Alembic coincide con los modelos SQLAlchemy.

Principios:
- ACID compliance: Verificar constraints y foreign keys
- Schema integrity: Validar estructura de tablas e índices
- Migration consistency: Asegurar que migrations están sincronizadas con models
"""

import pytest
from sqlalchemy import inspect, MetaData, Table, text
from sqlalchemy.orm import Session

from app.database.session_manager import DatabaseSessionManager
from app.models.meeting import Meeting, MeetingStatus
from app.models.prd import PRD
from app.models.task import Task, TaskPriority, TaskStatus


class TestAlembicMigrations:
    """✅ TDD - Tests de validación de migraciones Alembic."""
    
    @pytest.fixture
    def db_manager(self):
        """Fixture que proporciona un DatabaseSessionManager."""
        # Usar la misma DB que la aplicación
        import os
        database_url = os.getenv("DATABASE_URL", "postgresql://m2prd_user:memorymeet2024@postgres:5432/m2prd_main")
        return DatabaseSessionManager(database_url=database_url)
    
    @pytest.fixture
    def inspector(self, db_manager):
        """Fixture que proporciona un Inspector para introspección del schema."""
        return inspect(db_manager.engine)
    
    # ===== TESTS DE EXISTENCIA DE TABLAS =====
    
    def test_should_have_meetings_table(self, inspector):
        """🔴 RED → 🟢 GREEN: Verificar que tabla meetings existe."""
        tables = inspector.get_table_names()
        assert "meetings" in tables, "Tabla 'meetings' no existe en el schema"
    
    def test_should_have_prds_table(self, inspector):
        """🔴 RED → 🟢 GREEN: Verificar que tabla prds existe."""
        tables = inspector.get_table_names()
        assert "prds" in tables, "Tabla 'prds' no existe en el schema"
    
    def test_should_have_tasks_table(self, inspector):
        """🔴 RED → 🟢 GREEN: Verificar que tabla tasks existe."""
        tables = inspector.get_table_names()
        assert "tasks" in tables, "Tabla 'tasks' no existe en el schema"
    
    def test_should_have_alembic_version_table(self, inspector):
        """🔴 RED → 🟢 GREEN: Verificar que tabla de control de Alembic existe."""
        tables = inspector.get_table_names()
        assert "alembic_version" in tables, "Tabla 'alembic_version' no existe"
    
    # ===== TESTS DE COLUMNAS =====
    
    def test_meetings_table_should_have_required_columns(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar columnas de meetings."""
        columns = {col["name"]: col for col in inspector.get_columns("meetings")}
        
        # Columnas requeridas
        required_columns = [
            "id", "meeting_url", "audio_url", "duration_minutes",
            "status", "user_id", "transcription_text", "created_at",
            "processing_started_at", "processing_completed_at",
            "error_message", "retry_count"
        ]
        
        for col_name in required_columns:
            assert col_name in columns, f"Columna '{col_name}' falta en tabla meetings"
        
        # Verificar tipos críticos
        assert columns["id"]["type"].python_type == str
        assert columns["status"]["type"].__class__.__name__ == "ENUM"
        assert columns["retry_count"]["type"].python_type == int
    
    def test_prds_table_should_have_required_columns(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar columnas de prds."""
        columns = {col["name"]: col for col in inspector.get_columns("prds")}
        
        required_columns = [
            "id", "title", "description", "requirements",
            "confidence_score", "language_detected", "meeting_id",
            "created_at", "updated_at"
        ]
        
        for col_name in required_columns:
            assert col_name in columns, f"Columna '{col_name}' falta en tabla prds"
        
        # Verificar tipo JSON para requirements
        assert columns["requirements"]["type"].__class__.__name__ == "JSON"
    
    def test_tasks_table_should_have_required_columns(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar columnas de tasks."""
        columns = {col["name"]: col for col in inspector.get_columns("tasks")}
        
        required_columns = [
            "id", "title", "description", "assigned_role",
            "priority", "status", "confidence_score",
            "requirement_id", "prd_id", "external_task_id",
            "external_task_url", "created_at", "updated_at"
        ]
        
        for col_name in required_columns:
            assert col_name in columns, f"Columna '{col_name}' falta en tabla tasks"
        
        # Verificar ENUMs
        assert columns["priority"]["type"].__class__.__name__ == "ENUM"
        assert columns["status"]["type"].__class__.__name__ == "ENUM"
    
    # ===== TESTS DE PRIMARY KEYS =====
    
    def test_meetings_table_should_have_primary_key(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar PK de meetings."""
        pk = inspector.get_pk_constraint("meetings")
        assert pk["constrained_columns"] == ["id"], "PK de meetings debe ser 'id'"
    
    def test_prds_table_should_have_primary_key(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar PK de prds."""
        pk = inspector.get_pk_constraint("prds")
        assert pk["constrained_columns"] == ["id"], "PK de prds debe ser 'id'"
    
    def test_tasks_table_should_have_primary_key(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar PK de tasks."""
        pk = inspector.get_pk_constraint("tasks")
        assert pk["constrained_columns"] == ["id"], "PK de tasks debe ser 'id'"
    
    # ===== TESTS DE FOREIGN KEYS (ACID CONSISTENCY) =====
    
    def test_prds_table_should_have_foreign_key_to_meetings(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar FK de prds → meetings."""
        fks = inspector.get_foreign_keys("prds")
        
        assert len(fks) >= 1, "prds debe tener al menos 1 foreign key"
        
        meeting_fk = next((fk for fk in fks if fk["referred_table"] == "meetings"), None)
        assert meeting_fk is not None, "prds debe tener FK hacia meetings"
        assert "meeting_id" in meeting_fk["constrained_columns"], \
            "FK debe estar en columna 'meeting_id'"
        assert "id" in meeting_fk["referred_columns"], \
            "FK debe apuntar a columna 'id' de meetings"
    
    def test_tasks_table_should_have_foreign_key_to_prds(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar FK de tasks → prds."""
        fks = inspector.get_foreign_keys("tasks")
        
        assert len(fks) >= 1, "tasks debe tener al menos 1 foreign key"
        
        prd_fk = next((fk for fk in fks if fk["referred_table"] == "prds"), None)
        assert prd_fk is not None, "tasks debe tener FK hacia prds"
        assert "prd_id" in prd_fk["constrained_columns"], \
            "FK debe estar en columna 'prd_id'"
        assert "id" in prd_fk["referred_columns"], \
            "FK debe apuntar a columna 'id' de prds"
    
    # ===== TESTS DE ÍNDICES (PERFORMANCE OPTIMIZATION) =====
    
    def test_meetings_table_should_have_indexes(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar índices de meetings."""
        indexes = inspector.get_indexes("meetings")
        index_names = {idx["name"] for idx in indexes}
        
        # Índices esperados según migración
        expected_indexes = [
            "ix_meetings_id",
            "ix_meetings_status",
            "ix_meetings_user_id"
        ]
        
        for idx_name in expected_indexes:
            assert idx_name in index_names, f"Índice '{idx_name}' falta en meetings"
    
    def test_tasks_table_should_have_indexes(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar índices de tasks."""
        indexes = inspector.get_indexes("tasks")
        index_names = {idx["name"] for idx in indexes}
        
        expected_indexes = [
            "ix_tasks_id",
            "ix_tasks_assigned_role",
            "ix_tasks_prd_id",
            "ix_tasks_priority",
            "ix_tasks_status"
        ]
        
        for idx_name in expected_indexes:
            assert idx_name in index_names, f"Índice '{idx_name}' falta en tasks"
    
    # ===== TESTS DE UNIQUE CONSTRAINTS =====
    
    def test_prds_table_should_have_unique_meeting_id(self, inspector):
        """🔴 RED → 🟢 GREEN: Validar constraint UNIQUE en prds.meeting_id."""
        unique_constraints = inspector.get_unique_constraints("prds")
        
        meeting_unique = next(
            (uc for uc in unique_constraints if "meeting_id" in uc["column_names"]),
            None
        )
        
        assert meeting_unique is not None, \
            "prds.meeting_id debe tener constraint UNIQUE (1 PRD por reunión)"
    
    # ===== TESTS DE MIGRATION VERSION =====
    
    def test_alembic_version_should_be_latest(self, db_manager):
        """🔴 RED → 🟢 GREEN: Validar que la versión aplicada es la última."""
        with db_manager.transaction() as session:
            result = session.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar_one_or_none()
            
            assert current_version is not None, \
                "No hay versión de Alembic aplicada"
            
            # La versión actual debe ser '164cf67dea8e' (Initial schema)
            assert current_version == "164cf67dea8e", \
                f"Versión aplicada '{current_version}' no es la esperada '164cf67dea8e'"
    
    # ===== TESTS DE INTEGRIDAD END-TO-END =====
    
    def test_should_insert_data_respecting_foreign_keys(self, db_manager):
        """🔴 RED → 🟢 GREEN: Test E2E de integridad referencial."""
        with db_manager.transaction() as session:
            # 1. Crear Meeting
            meeting = Meeting(
                id="test-migration-meeting",
                meeting_url="https://meet.google.com/test",
                user_id="test-user",
                status=MeetingStatus.COMPLETED,
                retry_count=0
            )
            session.add(meeting)
            session.flush()
            
            # 2. Crear PRD asociado
            prd = PRD(
                id="test-migration-prd",
                title="Test PRD",
                requirements=[{"id": "req-1", "type": "functional"}],
                meeting_id=meeting.id,
                confidence_score="0.95",
                language_detected="es"
            )
            session.add(prd)
            session.flush()
            
            # 3. Crear Task asociada
            task = Task(
                id="test-migration-task",
                title="Test Task",
                assigned_role="Backend Developer",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                prd_id=prd.id,
                confidence_score="0.90"
            )
            session.add(task)
            session.flush()
            
            # 4. Verificar relaciones
            assert task.prd_id == prd.id
            assert prd.meeting_id == meeting.id
            
            # Cleanup
            session.delete(task)
            session.delete(prd)
            session.delete(meeting)

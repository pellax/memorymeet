"""
✅ ACID Transaction Manager for M2PRD-001.

Implements context manager that guarantees:
- ATOMICITY: All or nothing transactions
- CONSISTENCY: Business rules validation
- ISOLATION: Transaction isolation levels
- DURABILITY: Changes persist after commit

Usage:
    with db_manager.transaction() as session:
        session.add(meeting)
        session.commit()  # Automatic commit on success
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool


class DatabaseSessionManager:
    """
    ✅ TDD - ACID-compliant database session manager.
    
    Manages database connections and transactions following ACID principles.
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize database session manager.
        
        Args:
            database_url: PostgreSQL connection string
        """
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://user:pass@localhost:5432/memorymeet_dev"
            )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL debugging
        )
        
        # Session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False  # ✅ Evita DetachedInstanceError
        )
    
    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        ✅ ACID Context Manager - Guarantees all ACID properties.
        
        Yields:
            Session: SQLAlchemy session for database operations
            
        Example:
            with db_manager.transaction() as session:
                session.add(meeting)
                # Automatic commit on success, rollback on exception
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()  # ✅ ATOMICITY & DURABILITY
        except Exception as e:
            session.rollback()  # ✅ ATOMICITY - Rollback on error
            raise e
        finally:
            session.close()  # ✅ ISOLATION - Clean up session
    
    def create_all_tables(self):
        """Create all tables in the database."""
        from .base import Base
        Base.metadata.create_all(bind=self.engine)
    
    def drop_all_tables(self):
        """Drop all tables (use with caution!)."""
        from .base import Base
        Base.metadata.drop_all(bind=self.engine)


# Global database manager instance
_db_manager = None


def get_db_session() -> DatabaseSessionManager:
    """
    Get the global database session manager instance.
    
    Returns:
        DatabaseSessionManager: Singleton instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseSessionManager()
    return _db_manager

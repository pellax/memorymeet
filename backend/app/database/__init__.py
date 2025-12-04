"""
Database configuration and session management.

Implements ACID-compliant transaction manager for M2PRD-001.
"""
from .session_manager import DatabaseSessionManager, get_db_session
from .base import Base

__all__ = ["DatabaseSessionManager", "get_db_session", "Base"]

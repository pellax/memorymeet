"""
✅ Domain Model: Meeting (Reunión)

Represents a meeting to be processed in M2PRD-001.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, String, DateTime, Enum, Integer, Text
from sqlalchemy.orm import relationship

from ..database.base import Base


class MeetingStatus(PyEnum):
    """Estados posibles de una reunión."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Meeting(Base):
    """
    ✅ TDD - Meeting entity with ACID compliance.
    
    Represents a meeting that will be transcribed and processed.
    """
    __tablename__ = "meetings"
    
    # Primary Key
    id = Column(String(50), primary_key=True, index=True)
    
    # Meeting Information
    meeting_url = Column(String(500), nullable=False)
    audio_url = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Processing Status
    status = Column(
        Enum(MeetingStatus),
        default=MeetingStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # User Information (for RF8.0 - Consumption Control)
    user_id = Column(String(50), nullable=False, index=True)
    
    # Transcription
    transcription_text = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    prd = relationship("PRD", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Meeting(id={self.id}, status={self.status}, user_id={self.user_id})>"
    
    def is_processable(self) -> bool:
        """
        ✅ Domain Logic - Verifica si la reunión puede ser procesada.
        
        Returns:
            bool: True si puede procesarse
        """
        return self.status == MeetingStatus.PENDING and self.retry_count < 3
    
    def mark_as_processing(self) -> None:
        """✅ Domain Logic - Marca reunión como en procesamiento."""
        self.status = MeetingStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
    
    def mark_as_completed(self) -> None:
        """✅ Domain Logic - Marca reunión como completada."""
        self.status = MeetingStatus.COMPLETED
        self.processing_completed_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str) -> None:
        """✅ Domain Logic - Marca reunión como fallida."""
        self.status = MeetingStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1

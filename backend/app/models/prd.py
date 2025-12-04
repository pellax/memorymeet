"""
✅ Domain Model: PRD (Product Requirements Document)

Represents a generated PRD with requirements extracted from meeting transcription.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..database.base import Base


class PRD(Base):
    """
    ✅ TDD - PRD entity (Aggregate Root).
    
    Product Requirements Document generated from meeting analysis.
    """
    __tablename__ = "prds"
    
    # Primary Key
    id = Column(String(50), primary_key=True, index=True)
    
    # PRD Information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Requirements (stored as JSON for flexibility)
    requirements = Column(JSON, nullable=False, default=list)
    
    # Metadata
    confidence_score = Column(String(10), nullable=True)  # e.g., "0.85"
    language_detected = Column(String(10), nullable=True)  # e.g., "es", "en"
    
    # Foreign Keys
    meeting_id = Column(String(50), ForeignKey("meetings.id"), nullable=False, unique=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="prd")
    tasks = relationship("Task", back_populates="prd", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<PRD(id={self.id}, title={self.title}, meeting_id={self.meeting_id})>"
    
    @property
    def functional_requirements(self) -> List[dict]:
        """✅ Domain Logic - Obtiene solo requisitos funcionales."""
        return [
            req for req in self.requirements 
            if req.get("type") == "functional"
        ]
    
    @property
    def non_functional_requirements(self) -> List[dict]:
        """✅ Domain Logic - Obtiene solo requisitos no funcionales."""
        return [
            req for req in self.requirements 
            if req.get("type") == "non_functional"
        ]
    
    def add_requirement(self, requirement: dict) -> None:
        """
        ✅ Domain Logic - Añade un requisito al PRD.
        
        Args:
            requirement: Dict con estructura de requisito
        """
        if not isinstance(self.requirements, list):
            self.requirements = []
        self.requirements.append(requirement)
    
    def calculate_complexity(self) -> str:
        """
        ✅ Domain Logic - Calcula complejidad del PRD.
        
        Returns:
            str: LOW, MEDIUM, HIGH
        """
        num_requirements = len(self.requirements) if self.requirements else 0
        
        if num_requirements <= 3:
            return "LOW"
        elif num_requirements <= 8:
            return "MEDIUM"
        else:
            return "HIGH"

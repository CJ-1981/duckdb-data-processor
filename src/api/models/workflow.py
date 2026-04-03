"""
Workflow model for data processing pipelines.

This module defines the Workflow model with
- Workflow metadata (name, description)
- DAG definition for processing steps
- Version management
- Relationships to owner, jobs, versions
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, Integer, JSON, Column, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .job import Job
    from .workflow_version import WorkflowVersion


class Workflow(BaseModel):
    """Workflow model for data processing pipelines"""

    __tablename__ = "workflows"

    # Workflow metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Workflow definition (DAG)
    definition = Column(JSON, nullable=False)

    # Owner and version
    # @MX:ANCHOR: Foreign key to users table (fan_in >= 3: Workflow model, Job model, queries)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    # @MX:ANCHOR: Workflow-owner relationship (fan_in >= 3 callers expected)
    owner = relationship("User", back_populates="workflows")
    # @MX:ANCHOR: Workflow-job relationship (fan_in >= 3 callers expected)
    jobs = relationship("Job", back_populates="workflow")
    # @MX:ANCHOR: Workflow-version relationship (fan_in >= 3 callers expected)
    versions = relationship("WorkflowVersion", back_populates="workflow")

    def __init__(self, **kwargs):
        """Initialize Workflow with defaults for non-nullable fields

        Provides Python-level defaults since SQLAlchemy defaults only apply at DB level.
        """
        # Set defaults BEFORE calling super().__init__
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'version' not in kwargs:
            kwargs['version'] = 1

        # Call parent init
        super().__init__(**kwargs)

        # Post-init validation - CRITICAL: Set AFTER SQLAlchemy processes attributes
        if getattr(self, 'is_active', None) is None:
            self.is_active = True
        if getattr(self, 'version', None) is None:
            self.version = 1

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, version={self.version})>"

    def to_dict(self) -> dict:
        """Convert workflow to dictionary with definition"""
        result = super().to_dict()
        result["definition"] = self.definition
        return result

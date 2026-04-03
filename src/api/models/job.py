"""
Job model for workflow execution tracking.

This module defines the Job model with
- Execution status tracking
- Progress monitoring
- Error handling
- Result storage
- Relationships to workflow and creator
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, Float, DateTime, JSON, Enum as SQLEnum, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .workflow import Workflow


# Job status enumeration
class JobStatus(str, PyEnum):
    """Job status enumeration for execution tracking"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Job(BaseModel):
    """Job model for workflow execution tracking"""

    __tablename__ = "jobs"

    # Job identification
    id = Column(String(36), primary_key=True)  # UUID as string

    # @MX:ANCHOR: Foreign key to workflows table (fan_in >= 3: Job model, queries, statistics)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)

    # Execution status
    status = Column(SQLEnum(JobStatus), default=JobStatus.pending, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Progress and results
    progress = Column(Float, default=0.0, nullable=False)
    error_message = Column(String, nullable=True)
    result = Column(JSON, nullable=True)

    # Creator
    # @MX:ANCHOR: Foreign key to users table (fan_in >= 3: Job model, audit logs, user activity)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    # @MX:ANCHOR: Job-workflow relationship (fan_in >= 3 callers expected)
    workflow = relationship("Workflow", back_populates="jobs")
    # @MX:ANCHOR: Job-creator relationship (fan_in >= 3 callers expected)
    creator = relationship("User", back_populates="jobs")

    def __init__(self, **kwargs):
        """Initialize Job with defaults for non-nullable fields

        Provides Python-level defaults since SQLAlchemy defaults only apply at DB level.
        """
        # Set defaults BEFORE calling super().__init__
        if 'status' not in kwargs:
            kwargs['status'] = JobStatus.pending
        if 'progress' not in kwargs:
            kwargs['progress'] = 0.0

        # Call parent init
        super().__init__(**kwargs)

        # Post-init validation - CRITICAL: Set AFTER SQLAlchemy processes attributes
        if getattr(self, 'status', None) is None:
            self.status = JobStatus.pending
        if getattr(self, 'progress', None) is None:
            self.progress = 0.0

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status}, progress={self.progress})>"

    def to_dict(self) -> dict:
        """Convert job to dictionary with result"""
        result = super().to_dict()
        if self.result:
            result["result"] = self.result
        return result

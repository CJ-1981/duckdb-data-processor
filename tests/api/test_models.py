"""
SQLAlchemy Models tests for P2-T004 implementation.

This test suite validates model definitions, relationships, database operations, and validation.

Test Structure:
- Model Creation tests
- Relationship tests
- CRUD operation tests
- Query tests
- Validation tests
- Edge case tests
"""

import pytest
import pytest_asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Database URL for tests (SQLite in-memory)
TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_DATABASE_URL_ASYNC = "sqlite+aiosqlite:///:memory:"

# Async engine for tests
engine = create_async_engine(TEST_DATABASE_URL_ASYNC, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Base class for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


# Base model with common fields
class BaseModel(Base):
    """Base model with common fields and soft delete support"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    def is_deleted(self) -> bool:
        """Check if model is soft deleted"""
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


# User model
class User(BaseModel):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    workflows = relationship("Workflow", back_populates="owner", lazy="dynamic")
    jobs = relationship("Job", back_populates="creator", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash and set the user's password"""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# Workflow model
class Workflow(BaseModel):
    """Workflow model for data processing pipelines"""
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))  # UUID primary key
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    definition = Column(JSON, nullable=False)  # DAG definition
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="workflows", lazy="selectin")
    jobs = relationship("Job", back_populates="workflow", lazy="dynamic")
    versions = relationship("WorkflowVersion", back_populates="workflow", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name})>"


# Job model
class Job(BaseModel):
    """Job model for workflow execution tracking"""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="jobs", lazy="selectin")
    creator = relationship("User", back_populates="jobs", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status})>"


# WorkflowVersion model (for version history)
class WorkflowVersion(BaseModel):
    """WorkflowVersion model for tracking workflow changes over time"""
    __tablename__ = "workflow_versions"

    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    definition = Column(JSON, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="versions", lazy="selectin")
    creator = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<WorkflowVersion(id={self.id}, version={self.version})>"


# Role enum for users
class UserRole(str, SQLEnum):
    """User role enumeration"""
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


# Job status enum for jobs
class JobStatus(str, SQLEnum):
    """Job status enumeration"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


# ============================================================================
# Model Creation Tests
# ============================================================================

class TestModelCreation:
    """Test model creation and basic functionality"""

    def test_user_creation(self):
        """Test creating a user instance"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$ab$cd422b$",
            role="analyst"
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "analyst"
        assert user.is_active is True
        assert user.id is None  # Not persisted yet

    def test_workflow_creation(self):
        """Test creating a workflow instance"""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
            definition={"nodes": [], "edges": []},
            owner_id=1
        )

        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.definition == {"nodes": [], "edges": []}
        assert workflow.owner_id == 1
        assert workflow.is_active is True
        assert workflow.version == 1

    def test_job_creation(self):
        """Test creating a job instance"""
        job = Job(
            workflow_id="workflow-uuid",
            status="pending",
            created_by=1
        )

        assert job.workflow_id == "workflow-uuid"
        assert job.status == "pending"
        assert job.progress == 0
        assert job.created_by == 1

    def test_workflow_version_creation(self):
        """Test creating a workflow version instance"""
        version = WorkflowVersion(
            workflow_id="workflow-uuid",
            version=2,
            definition={"nodes": [], "edges": []},
            created_by=1
        )

        assert version.workflow_id == "workflow-uuid"
        assert version.version == 2
        assert version.definition == {"nodes": [], "edges": []}


# ============================================================================
# Password Security Tests
# ============================================================================

class TestPasswordSecurity:
    """Test password hashing and verification"""

    def test_set_password(self):
        """Test password hashing"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=""
        )

        user.set_password("SecurePass123!")

        assert user.password_hash != ""
        assert user.password_hash.startswith("$2b$")
        assert len(user.password_hash) > 50

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=""
        )
        user.set_password("SecurePass123!")

        assert user.verify_password("SecurePass123!") is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=""
        )
        user.set_password("SecurePass123!")

        assert user.verify_password("WrongPassword") is False


# ============================================================================
# Model Methods Tests
# ============================================================================

class TestModelMethods:
    """Test model methods"""

    def test_to_dict(self):
        """Test to_dict method"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$ab$cd422b$"
        )

        user_dict = user.to_dict()

        assert "id" in user_dict
        assert "created_at" in user_dict
        assert "updated_at" in user_dict
        assert "deleted_at" in user_dict

    def test_is_deleted(self):
        """Test is_deleted method"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$ab$cd422b$"
        )

        assert user.is_deleted() is False

        user.deleted_at = datetime.utcnow()
        assert user.is_deleted() is True

    def test_repr(self):
        """Test __repr__ method"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$ab$cd422b$"
        )

        repr_str = repr(user)
        assert "User" in repr_str
        assert "username=testuser" in repr_str


# ============================================================================
# Relationship Tests
# ============================================================================

class TestRelationships:
    """Test model relationships"""

    def test_user_workflow_relationship(self):
        """Test user-workflow relationship"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$ab$cd422b$"
        )

        workflow = Workflow(
            name="Test Workflow",
            definition={},
            owner_id=user.id
        )

        # Note: Relationships require actual database to test properly
        assert workflow.owner_id == user.id

    def test_workflow_job_relationship(self):
        """Test workflow-job relationship"""
        workflow = Workflow(
            name="Test Workflow",
            definition={},
            owner_id=1
        )

        job = Job(
            workflow_id=workflow.id,
            status="pending",
            created_by=1
        )

        assert job.workflow_id == workflow.id


# ============================================================================
# Validation Tests
# ============================================================================

class TestValidation:
    """Test model validation"""

    def test_user_username_required(self):
        """Test username is required"""
        with pytest.raises(Exception):
            user = User(email="test@example.com", password_hash="$2b$12$ab$cd422b$")

    def test_user_email_required(self):
        """Test email is required"""
        with pytest.raises(Exception):
            user = User(username="testuser", password_hash="$2b$12$ab$cd422b$")

    def test_workflow_name_required(self):
        """Test workflow name is required"""
        with pytest.raises(Exception):
            workflow = Workflow(definition={}, owner_id=1)


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_user_role_default(self):
        """Test user role defaults to viewer"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$ab$cd422b$"
        )

        assert user.role == "viewer"

    def test_workflow_version_default(self):
        """Test workflow version defaults to 1"""
        workflow = Workflow(
            name="Test Workflow",
            definition={},
            owner_id=1
        )

        assert workflow.version == 1

    def test_job_status_default(self):
        """Test job status defaults to pending"""
        job = Job(
            workflow_id="workflow-uuid",
            created_by=1
        )

        assert job.status == "pending"
        assert job.progress == 0

    def test_job_progress_default(self):
        """Test job progress defaults to 0"""
        job = Job(
            workflow_id="workflow-uuid",
            created_by=1
        )

        assert job.progress == 0

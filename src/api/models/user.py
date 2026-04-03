"""
User model for authentication and authorization.

This module defines the User model with:
- Basic user information (username, email)
- Role-based access control (admin, analyst, viewer)
- Password hashing with bcrypt
- Relationships to workflows and jobs
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Column, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel

if TYPE_CHECKING:
    from .workflow import Workflow
    from .job import Job


# Role enumeration
class UserRole(str, PyEnum):
    """User role enumeration for RBAC"""
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class User(BaseModel):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    # User information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash

    # Role and status
    role = Column(SQLEnum(UserRole), default=UserRole.viewer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    # @MX:ANCHOR: User-workflow relationship (fan_in >= 3 callers expected)
    workflows = relationship("Workflow", back_populates="owner")
    # @MX:ANCHOR: User-job relationship (fan_in >= 3 callers expected)
    jobs = relationship("Job", back_populates="creator")

    def __init__(self, **kwargs):
        """Initialize User with defaults for non-nullable fields

        Provides Python-level defaults since SQLAlchemy defaults only apply at DB level.
        """
        # Call parent init first
        super().__init__(**kwargs)

        # Set defaults AFTER SQLAlchemy initialization
        # Column defaults only apply at DB level, not Python object level
        if not hasattr(self, 'is_active') or self.is_active is None:
            object.__setattr__(self, 'is_active', True)
        if not hasattr(self, 'role') or self.role is None:
            object.__setattr__(self, 'role', UserRole.viewer)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password.

        Args:
            password: Plain text password to hash

        Note: This method should be implemented with bcrypt
        """
        # This will be implemented when bcrypt is installed
        raise NotImplementedError("Password hashing requires bcrypt installation")

    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise

        Note: This method should be implemented with bcrypt
        """
        # This will be implemented when bcrypt is installed
        raise NotImplementedError("Password verification requires bcrypt installation")


# Event listener to set defaults after initialization
# This must be defined after the User class
from sqlalchemy import event

@event.listens_for(User, "init", propagate=True)
def set_user_defaults(target, args, kwargs):
    """Set default values for User model after SQLAlchemy initialization

    This event listener runs after SQLAlchemy's internal processing but before
    the object is returned to the caller. It ensures defaults are set even when
    not explicitly provided in kwargs.

    # @MX:NOTE: Event listener ensures defaults are set at SQLAlchemy level
    """
    # Set defaults directly on the instance using object.__setattr__
    # This bypasses any SQLAlchemy attribute tracking
    if not hasattr(target, 'is_active') or getattr(target, 'is_active', None) is None:
        object.__setattr__(target, 'is_active', True)
    if not hasattr(target, 'role') or getattr(target, 'role', None) is None:
        object.__setattr__(target, 'role', UserRole.viewer)

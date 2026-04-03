"""
Authorization decorators for FastAPI endpoints.

@MX:ANCHOR: Authorization decorators used across all API routes
@MX:REASON: Centralized authorization logic for consistent security enforcement
@MX:SPEC: SPEC-PLATFORM-001 P2-T003
@MX:NOTE: Decorators are pass-through for now; authorization happens in endpoint functions
"""

from functools import wraps
from typing import Callable, Optional
from fastapi import HTTPException, status

import logging

logger = logging.getLogger(__name__)


def require_role(*roles: str):
    """
    Decorator to require specific role(s) for endpoint access.

    User must have ANY of the specified roles to access the endpoint.

    Args:
        *roles: Required role names (any one is sufficient)

    Usage:
        @require_role("admin")
        async def admin_only_endpoint(current_user: dict = None):
            # User must have "admin" role
            pass

    Raises:
        HTTPException: 403 Forbidden if user lacks required role
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs or args
            # FastAPI dependencies are passed as kwargs
            current_user = kwargs.get("current_user") or (
                args[0]
                if args and isinstance(args[0], dict) and "role" in args[0]
                else None
            )

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_role = current_user.get("role", "viewer")

            # Check if user has any of the required roles
            if user_role not in roles:
                log_authorization(
                    user_id=current_user.get("id"),
                    username=current_user.get("username"),
                    permission=f"role:({'|'.join(roles)})",
                    granted=False,
                    reason=f"User has role '{user_role}', required one of: {roles}",
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: requires one of roles: {roles}",
                )

            # Log successful authorization
            log_authorization(
                user_id=current_user.get("id"),
                username=current_user.get("username"),
                permission=f"role:({'|'.join(roles)})",
                granted=True,
            )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(*permissions: str):
    """
    Decorator to require specific permission(s) for endpoint access.

    User must have ALL of the specified permissions to access the endpoint.

    Args:
        *permissions: Required permission strings (all are required)

    Usage:
        @require_permission("data:read")
        async def read_data_endpoint(current_user: dict = Depends(get_current_user)):
            # User must have "data:read" permission
            pass

    Raises:
        HTTPException: 403 Forbidden if user lacks required permissions
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs or args
            current_user = kwargs.get("current_user") or (
                args[0]
                if args and isinstance(args[0], dict) and "permissions" in args[0]
                else None
            )

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_permissions = current_user.get("permissions", [])

            # Check for wildcard permission (admin has all permissions)
            if "*" not in user_permissions:
                # Check if user has ALL of the required permissions
                missing_permissions = [
                    p for p in permissions if p not in user_permissions
                ]

                if missing_permissions:
                    log_authorization(
                        user_id=current_user.get("id"),
                        username=current_user.get("username"),
                        permission=f"permission:({', '.join(permissions)})",
                        granted=False,
                        reason=f"Missing permissions: {missing_permissions}",
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: requires permissions: {permissions}",
                    )

            # Log successful authorization
            log_authorization(
                user_id=current_user.get("id"),
                username=current_user.get("username"),
                permission=f"permission:({', '.join(permissions)})",
                granted=True,
            )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def log_authorization(
    user_id: Optional[int],
    username: Optional[str],
    permission: str,
    granted: bool,
    reason: Optional[str] = None,
) -> None:
    """
    Log authorization attempt for audit trail.

    @MX:NOTE: All authorization attempts are logged for security auditing

    Args:
        user_id: User ID attempting access
        username: Username attempting access
        permission: Permission or role being checked
        granted: True if access granted, False if denied
        reason: Optional reason for the decision
    """
    from datetime import datetime

    log_entry = {
        "user_id": user_id,
        "username": username,
        "permission": permission,
        "granted": granted,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if granted:
        logger.info(f"Authorization GRANTED: user={username}, permission={permission}")
    else:
        logger.warning(
            f"Authorization DENIED: user={username}, permission={permission}, reason={reason}"
        )

    # In production, this would be written to audit log database
    # For now, we just log it
    # TODO: Implement audit log persistence (SPEC-PLATFORM-001 UR-002)

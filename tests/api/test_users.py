"""
User Management Endpoints Tests

Tests for user registration, profile management, and user listing.
Following TDD methodology: RED phase first.

@MX:SPEC: SPEC-PLATFORM-001 P2-T010
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestUserRegistration:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration."""
        from src.api.schemas.user import UserCreate
        from src.api.models.user import User

        # Mock database session
        mock_db = AsyncMock()

        # Mock user service
        mock_user_service = AsyncMock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "newuser"
        mock_user.email = "newuser@example.com"
        mock_user.created_at = datetime.utcnow()

        mock_user_service.create_user.return_value = mock_user

        # Set datetime attributes properly for response serialization
        mock_user.updated_at = mock_user.created_at

        # Request data
        user_data = UserCreate(
            username="newuser", email="newuser@example.com", password="SecurePass123!"
        )

        # Mock dependency override
        app = FastAPI()

        # Include the router instead of manually registering the route
        from src.api.routes.users import router

        app.include_router(router)

        from src.api.dependencies import get_user_service

        # Override get_user_service properly
        async def override_get_user_service():
            yield mock_user_service

        app.dependency_overrides[get_user_service] = override_get_user_service

        client = TestClient(app)

        # Make request
        response = client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!",
            },
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self):
        """Test registration with duplicate email fails."""
        from src.api.routes.users import register_user

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()
        mock_user_service.create_user.side_effect = ValueError(
            "Email already registered"
        )

        app = FastAPI()
        app.post("/api/v1/users/register")(register_user)

        from src.api.dependencies import get_user_service

        # Override get_user_service properly
        async def override_get_user_service():
            yield mock_user_service

        app.dependency_overrides[get_user_service] = override_get_user_service

        client = TestClient(app)

        # Make request with duplicate email
        response = client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "existing@example.com",
                "password": "SecurePass123!",
            },
        )

        # Verify conflict response
        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_user_validation(self):
        """Test registration with invalid data fails."""
        from src.api.routes.users import register_user

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()

        app = FastAPI()
        app.post("/api/v1/users/register")(register_user)

        from src.api.dependencies import get_user_service

        # Override get_user_service properly
        async def override_get_user_service():
            yield mock_user_service

        app.dependency_overrides[get_user_service] = override_get_user_service

        client = TestClient(app)

        # Make request with invalid email
        response = client.post(
            "/api/v1/users/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "short",
            },
        )

        # Verify validation error
        assert response.status_code == 422


class TestUserProfileUpdate:
    """Test user profile update endpoint."""

    @pytest.mark.asyncio
    async def test_update_profile_success(self):
        """Test successful profile update."""
        from src.api.models.user import User

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()

        # Mock updated user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "updated@example.com"
        created_time = datetime.utcnow()
        mock_user.created_at = created_time
        mock_user.updated_at = created_time

        mock_user_service.update_user.return_value = mock_user

        app = FastAPI()
        from src.api.routes.users import router

        app.include_router(router)

        from src.api.dependencies import get_user_service
        from src.api.auth.dependencies import get_current_user

        # Use dict instead of Mock since get_current_user returns Dict[str, Any]
        mock_current_user = {"id": 1}

        async def override_get_user_service():
            yield mock_user_service

        async def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request
        response = client.put("/api/v1/users/me", json={"email": "updated@example.com"})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """Test successful password change."""
        from src.api.models.user import User

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user_service.change_password.return_value = True

        app = FastAPI()
        from src.api.routes.users import router

        app.include_router(router)

        from src.api.dependencies import get_user_service
        from src.api.auth.dependencies import get_current_user

        # Use dict instead of Mock since get_current_user returns Dict[str, Any]
        mock_current_user = {"id": 1}

        async def override_get_user_service():
            yield mock_user_service

        async def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request
        response = client.post(
            "/api/v1/users/me/change-password",
            json={"current_password": "OldPass123!", "new_password": "NewPass456!"},
        )

        # Verify response
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self):
        """Test password change with wrong current password fails."""

        mock_db = AsyncMock()
        mock_user_service = AsyncMock()
        mock_user_service.change_password.side_effect = ValueError("Incorrect password")

        app = FastAPI()
        from src.api.routes.users import router

        app.include_router(router)

        from src.api.dependencies import get_user_service
        from src.api.auth.dependencies import get_current_user

        # Use dict instead of Mock since get_current_user returns Dict[str, Any]
        mock_current_user = {"id": 1}

        async def override_get_user_service():
            yield mock_user_service

        async def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[get_user_service] = override_get_user_service
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)

        # Make request with wrong password
        response = client.post(
            "/api/v1/users/me/change-password",
            json={"current_password": "WrongPass123!", "new_password": "NewPass456!"},
        )

        # Verify error response
        assert response.status_code == 400


class TestUserListing:
    """Test user listing endpoint with pagination."""

    @pytest.mark.asyncio
    async def test_list_users_success(self):
        """Test successful user listing."""
        from src.api.routes.users import list_users

        mock_user_service = AsyncMock()

        # Mock user list with proper datetime attributes
        created_time = datetime.utcnow()
        mock_users = [
            Mock(
                id=1,
                username="user1",
                email="user1@example.com",
                created_at=created_time,
                updated_at=created_time,
            ),
            Mock(
                id=2,
                username="user2",
                email="user2@example.com",
                created_at=created_time,
                updated_at=created_time,
            ),
        ]

        mock_user_service.list_users.return_value = (mock_users, 2)

        # Use dict for current_user since get_current_user returns Dict[str, Any]
        mock_current_user = {"id": 1, "role": "admin"}

        # Call the route function directly (like test_rbac.py does)
        result = await list_users(
            user_service=mock_user_service,
            current_user=mock_current_user,
            page=1,
            page_size=20,
            search=None,
        )

        # Verify response
        assert result.total == 2
        assert len(result.users) == 2
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_list_users_forbidden(self):
        """Test user listing fails for non-admin users."""
        from src.api.routes.users import list_users
        from fastapi import HTTPException

        mock_user_service = AsyncMock()

        # Use dict for current_user with viewer role
        mock_current_user = {"id": 1, "role": "viewer"}

        # Call the route function directly and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await list_users(
                user_service=mock_user_service,
                current_user=mock_current_user,
                page=1,
                page_size=20,
                search="",
            )

        # Verify forbidden response
        assert exc_info.value.status_code == 403


class TestUserDeletion:
    """Test user deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """Test successful user deletion."""
        from src.api.routes.users import delete_user

        mock_user_service = AsyncMock()
        mock_user_service.delete_user.return_value = True

        # Use dict for current_user with admin role
        mock_current_user = {"id": 1, "role": "admin"}

        # Call the route function directly
        result = await delete_user(
            user_id=2, user_service=mock_user_service, current_user=mock_current_user
        )

        # Verify response (delete returns None on success with 204 status)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        """Test deleting non-existent user fails."""
        from src.api.routes.users import delete_user
        from fastapi import HTTPException

        mock_user_service = AsyncMock()
        mock_user_service.delete_user.return_value = False

        # Use dict for current_user with admin role
        mock_current_user = {"id": 1, "role": "admin"}

        # Call the route function directly and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await delete_user(
                user_id=999,
                user_service=mock_user_service,
                current_user=mock_current_user,
            )

        # Verify not found response
        assert exc_info.value.status_code == 404


class TestUserService:
    """Test user service business logic."""

    @pytest.mark.asyncio
    async def test_create_user_hashes_password(self):
        """Test that user creation hashes password."""
        from src.api.services.users import UserService
        from src.api.schemas.user import UserCreate
        from unittest.mock import AsyncMock, Mock

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = Mock()

        # Mock the database query result - no existing user
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock hash_password to return a known hash value
        with patch("src.api.services.users.hash_password") as mock_hash:
            mock_hash.return_value = "hashed_password_value"

            user_service = UserService(mock_db)

            # Create user
            user_data = UserCreate(
                username="testuser",
                email="test@example.com",
                password="PlainPassword123!",
            )

            user = await user_service.create_user(user_data)

            # Verify hash_password was called with the plain password
            mock_hash.assert_called_once_with("PlainPassword123!")

            # Verify the user's password was hashed (not stored as plain text)
            assert user.password_hash == "hashed_password_value"

    @pytest.mark.asyncio
    async def test_change_password_verifies_current(self):
        """Test password change verifies current password."""
        from src.api.services.users import UserService
        from src.api.models.user import User
        from unittest.mock import AsyncMock

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        user_service = UserService(mock_db)

        # Mock user with existing password
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.password_hash = "existing_hash"

        # Mock get_user to return the mock user
        user_service.get_user = AsyncMock(return_value=mock_user)

        # Mock password verification and hash_password
        with (
            patch("src.api.services.users.verify_password") as mock_verify,
            patch("src.api.services.users.hash_password") as mock_hash,
        ):
            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"

            # Change password - now takes user_id instead of user object
            result = await user_service.change_password(
                1,  # user_id
                "OldPass123!",
                "NewPass456!",
            )

            # Verify old password was checked
            mock_verify.assert_called_once_with("OldPass123!", "existing_hash")

            # Verify new password was hashed
            mock_hash.assert_called_once_with("NewPass456!")

            # Verify commit was called
            mock_db.commit.assert_called_once()

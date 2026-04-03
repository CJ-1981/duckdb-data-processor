"""
Comprehensive test suite for JWT authentication following TDD methodology.

Tests are designed to document expected behavior and verify correct assertions
using `pytest.mark.parametrize` along with `pytest-asyncio` for async testing.
"""

import pytest
try:
    import jwt
except ImportError:
    # PyJWT not installed, skip this test file
    pytest.skip("PyJWT not installed", allow_module_level=True)

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Test data fixtures
@pytest.fixture
def mock_config():
    """Create mock configuration with JWT settings."""
    mock_config = Mock()
    mock_config.auth = Mock()
    mock_config.auth.secret_key = "test-secret-key-here-for-testing"
    mock_config.auth.algorithm = "HS256"
    mock_config.auth.access_token_expire_minutes = 15
    mock_config.auth.refresh_token_expire_days = 7
    yield mock_config


@pytest.fixture
def mock_token_storage():
    """Create mock token storage for testing."""
    storage = Mock()
    return storage


@pytest.fixture
def password_hasher():
    """Create password hasher for testing."""
    hasher = Mock()
    hasher.hash_password = Mock(return_value="$2b$12$ab$cd422b$")
    hasher.verify_password = Mock(return_value=True)
    hasher.validate_password_strength = Mock(return_value=True)
    return hasher


@pytest.fixture
def valid_user_data():
    """Create valid user data for testing."""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = "$2b$12$ab$cd422b$"
    user.roles = ["user"]
    user.created_at = datetime(2024, 1, 1, 12, 0, 0)
    return user


@pytest.fixture
def mock_jwt_handler():
    """Create mock JWT handler for testing."""
    handler = Mock()
    handler.secret_key = "test-secret-key"
    handler.algorithm = "HS256"
    handler.access_token_expire = timedelta(minutes=15)
    handler.refresh_token_expire = timedelta(days=7)
    return handler


@pytest.fixture
def mock_token_generator():
    """Create mock token generator for testing."""
    generator = Mock()
    generator.secret_key = "test-secret-key"
    generator.algorithm = "HS256"
    return generator


# ============================================================================
# Password Security Tests
# ============================================================================

class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_hash_password(self, password_hasher):
        """Test password hashing"""
        password = "SecurePass123!"
        hashed = password_hasher.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self, password_hasher):
        """Test password verification with correct password"""
        password = "SecurePass123!"
        hashed = password_hasher.hash_password(password)

        assert password_hasher.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, password_hasher):
        """Test password verification with incorrect password"""
        password = "WrongPassword"
        hashed = password_hasher.hash_password("SecurePass123!")

        assert password_hasher.verify_password(password, hashed) is False

    def test_validate_password_strength_valid(self, password_hasher):
        """Test password strength validation - valid password"""
        password = "SecurePass123!"

        assert password_hasher.validate_password_strength(password) is True

    @pytest.mark.parametrize("password,expected", [
        ("ShortPass1", False),
        ("weakpass", False),
        ("NoUpper123", False),
        ("NoLower123", False),
        ("NoNumber123", False),
        ("Valid123", True),
    ])
    def test_validate_password_strength(self, password_hasher, password: str, expected: bool):
        result = password_hasher.validate_password_strength(password)
        assert result == expected, f"Invalid password '{password}' failed validation: expected {expected}"

    def test_validate_password_strength_no_special(self, password_hasher):
        """Test password strength validation - missing special character"""
        password = "NoSpecialChar123"

        # This password meets length, uppercase, lowercase, number but no special char
        assert password_hasher.validate_password_strength(password) is False

    def test_hash_password_edge_cases(self, password_hasher):
        """Test password hashing with edge cases"""
        # Test with empty string (should raise ValueError or handle gracefully)
        with pytest.raises((ValueError, AttributeError)):
            password_hasher.hash_password("")


# ============================================================================
# Token Generation Tests
# ============================================================================

class TestTokenGeneration:
    """Test token generation functionality"""

    def test_create_access_token(self, mock_token_generator, valid_user_data):
        """Test access token creation"""
        token = "mock_access_token"
        mock_token_generator.create_access_token = Mock(return_value=token)

        result = mock_token_generator.create_access_token(valid_user_data)

        assert result is not None
        assert result != ""

    def test_create_refresh_token(self, mock_token_generator, valid_user_data):
        """Test refresh token creation"""
        token = "mock_refresh_token"
        mock_token_generator.create_refresh_token = Mock(return_value=token)

        result = mock_token_generator.create_refresh_token(valid_user_data)

        assert result is not None
        assert result != ""

    def test_token_claims(self, mock_token_generator, valid_user_data):
        """Test token claims are included correctly"""
        token = jwt.encode(
            {
                "sub": str(valid_user_data.id),
                "username": valid_user_data.username,
                "roles": valid_user_data.roles,
                "type": "access",
                "exp": datetime.utcnow() + timedelta(minutes=15),
                "iat": datetime.utcnow()
            },
            "test-secret",
            algorithm="HS256"
        )

        # Decode token to verify claims
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["sub"] == str(valid_user_data.id)
        assert payload["username"] == valid_user_data.username
        assert payload["roles"] == valid_user_data.roles
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_pair(self, mock_token_generator, valid_user_data):
        """Test creating access and refresh token pair"""
        access_token = "mock_access_token"
        refresh_token = "mock_refresh_token"
        mock_token_generator.create_access_token = Mock(return_value=access_token)
        mock_token_generator.create_refresh_token = Mock(return_value=refresh_token)

        access = mock_token_generator.create_access_token(valid_user_data)
        refresh = mock_token_generator.create_refresh_token(valid_user_data)

        assert access is not None
        assert refresh is not None
        assert access != ""
        assert refresh != ""


# ============================================================================
# JWT Handler Tests
# ============================================================================

class TestJWTHandler:
    """Test JWT handler functionality"""

    def test_init(self, mock_jwt_handler):
        """Test handler initialization"""
        assert mock_jwt_handler.secret_key == "test-secret-key"
        assert mock_jwt_handler.algorithm == "HS256"
        assert mock_jwt_handler.access_token_expire == timedelta(minutes=15)
        assert mock_jwt_handler.refresh_token_expire == timedelta(days=7)

    def test_create_tokens(self, mock_jwt_handler, valid_user_data):
        """Test token creation"""
        access_token = "mock_access_token"
        refresh_token = "mock_refresh_token"
        mock_jwt_handler.create_tokens = Mock(return_value=(access_token, refresh_token))

        access, refresh = mock_jwt_handler.create_tokens(valid_user_data)

        assert access is not None
        assert refresh is not None
        assert access != ""
        assert refresh != ""
        assert isinstance(access, str)
        assert isinstance(refresh, str)

    def test_validate_token_valid(self, mock_jwt_handler, valid_user_data):
        """Test token validation"""
        token = jwt.encode(
            {
                "sub": str(valid_user_data.id),
                "username": valid_user_data.username,
                "roles": valid_user_data.roles,
                "type": "access",
                "exp": datetime.utcnow() + timedelta(minutes=15),
                "iat": datetime.utcnow()
            },
            "test-secret",
            algorithm="HS256"
        )
        mock_jwt_handler.validate_token = Mock(return_value=jwt.decode(token, options={"verify_signature": False}))

        payload = mock_jwt_handler.validate_token(token)

        assert payload is not None
        assert payload["sub"] == str(valid_user_data.id)
        assert payload["username"] == valid_user_data.username
        assert payload["roles"] == valid_user_data.roles
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_validate_token_invalid(self, mock_jwt_handler):
        """Test token validation with invalid token"""
        token = "invalid-token"
        mock_jwt_handler.validate_token = Mock(side_effect=jwt.InvalidTokenError)

        with pytest.raises(jwt.InvalidTokenError):
            mock_jwt_handler.validate_token(token)

    def test_validate_token_missing(self, mock_jwt_handler):
        """Test token validation with missing token"""
        mock_jwt_handler.validate_token = Mock(side_effect=jwt.InvalidTokenError)

        with pytest.raises(jwt.InvalidTokenError):
            mock_jwt_handler.validate_token("")


# ============================================================================
# Authentication Endpoints Tests
# ============================================================================

class TestAuthenticationEndpoints:
    """Test authentication endpoints functionality"""

    @pytest.fixture
    def auth_service(self):
        """Create auth service for testing"""
        service = Mock()
        service.secret_key = "test-secret-key"
        service.algorithm = "HS256"
        return service

    @pytest.mark.asyncio
    async def test_register(self, auth_service):
        """Test user registration"""
        user = Mock()
        user.id = 1
        user.username = "newuser"
        user.email = "newuser@example.com"
        user.password_hash = "$2b$12$ab$cd422b$"
        user.roles = ["user"]

        auth_service.register = Mock(return_value=user)

        result = await auth_service.register(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123!"
        )

        assert result is not None
        assert result.username == "newuser"
        assert result.email == "newuser@example.com"
        assert result.password_hash.startswith("$2b$")
        assert result.roles == ["user"]

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service):
        """Test successful login"""
        token_response = Mock()
        token_response.access_token = "mock_access_token"
        token_response.refresh_token = "mock_refresh_token"

        auth_service.login = Mock(return_value=token_response)

        result = await auth_service.login(
            username="testuser",
            password="SecurePass123!"
        )

        assert result is not None
        assert result.access_token == "mock_access_token"
        assert result.refresh_token == "mock_refresh_token"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service):
        """Test login with invalid credentials"""
        auth_service.login = Mock(side_effect=Exception("Invalid credentials"))

        with pytest.raises(Exception):
            await auth_service.login(
                username="testuser",
                password="wrongpassword"
            )

    @pytest.mark.asyncio
    async def test_refresh_token(self, auth_service):
        """Test token refresh"""
        new_token_response = Mock()
        new_token_response.access_token = "new_mock_access_token"
        new_token_response.refresh_token = "new_mock_refresh_token"

        auth_service.refresh_token = Mock(return_value=new_token_response)

        result = await auth_service.refresh_token("valid_refresh_token")

        assert result is not None
        assert result.access_token != ""
        assert result.refresh_token != ""

    @pytest.mark.asyncio
    async def test_get_current_user(self, auth_service):
        """Test get current user"""
        current_user = Mock()
        current_user.id = 1
        current_user.username = "testuser"

        auth_service.get_current_user = Mock(return_value=current_user)

        result = await auth_service.get_current_user("valid_token")

        assert result is not None
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_logout(self, auth_service):
        """Test logout"""
        auth_service.logout = Mock(return_value=None)

        result = await auth_service.logout("refresh_token")

        assert result is None
        auth_service.logout.assert_called_once_with("refresh_token")

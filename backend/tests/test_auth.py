"""Tests for authentication endpoints and services."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    normalize_email,
    verify_password,
    verify_refresh_token,
)
from app.main import app
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_service(session: Session):
    """Create auth service with test session."""
    return AuthService(session)


@pytest.fixture
def user_repo(session: Session):
    """Create user repository with test session."""
    return UserRepository(session)


# ============================================================================
# Security Module Tests
# ============================================================================


def test_hash_password():
    """Test password hashing."""
    password = "test_password_123"
    hash_val = hash_password(password)
    assert hash_val != password
    assert len(hash_val) > 20
    assert verify_password(password, hash_val)


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "test_password_123"
    hash_val = hash_password(password)
    assert verify_password(password, hash_val) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "test_password_123"
    wrong_password = "wrong_password"
    hash_val = hash_password(password)
    assert verify_password(wrong_password, hash_val) is False


def test_verify_password_invalid_hash():
    """Test password verification with invalid hash."""
    password = "test_password_123"
    invalid_hash = "invalid_hash_string"
    assert verify_password(password, invalid_hash) is False


def test_normalize_email():
    """Test email normalization."""
    assert normalize_email("User@Example.COM") == "user@example.com"
    assert normalize_email("  user@example.com  ") == "user@example.com"
    assert normalize_email("UPPERCASE@EXAMPLE.COM") == "uppercase@example.com"


def test_create_refresh_token():
    """Test refresh token generation."""
    token = create_refresh_token()
    assert isinstance(token, str)
    assert len(token) > 20
    # Tokens should be unique
    token2 = create_refresh_token()
    assert token != token2


def test_hash_refresh_token():
    """Test refresh token hashing."""
    token = create_refresh_token()
    token_hash = hash_refresh_token(token)
    assert token_hash != token
    assert verify_refresh_token(token, token_hash) is True


def test_verify_refresh_token_correct():
    """Test refresh token verification with correct token."""
    token = create_refresh_token()
    token_hash = hash_refresh_token(token)
    assert verify_refresh_token(token, token_hash) is True


def test_verify_refresh_token_incorrect():
    """Test refresh token verification with incorrect token."""
    token = create_refresh_token()
    token_hash = hash_refresh_token(token)
    wrong_token = create_refresh_token()
    assert verify_refresh_token(wrong_token, token_hash) is False


def test_verify_refresh_token_invalid_hash():
    """Test refresh token verification with invalid hash."""
    token = create_refresh_token()
    invalid_hash = "invalid_hash_string"
    assert verify_refresh_token(token, invalid_hash) is False


def test_create_access_token():
    """Test access token creation."""
    user_id = "test_user_123"
    token = create_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 20


def test_decode_access_token():
    """Test access token decoding."""
    from app.core.security import decode_access_token

    user_id = "test_user_123"
    token = create_access_token(user_id)
    payload = decode_access_token(token)
    assert payload["user_id"] == user_id
    assert "exp" in payload
    assert "iat" in payload


def test_decode_access_token_expired():
    """Test decoding expired token."""
    from app.core.exceptions import AppException
    from app.core.security import decode_access_token

    user_id = "test_user_123"
    # Create token that expires immediately
    token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
    with pytest.raises(AppException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.status_code == 401


def test_decode_access_token_invalid():
    """Test decoding invalid token."""
    from app.core.exceptions import AppException
    from app.core.security import decode_access_token

    with pytest.raises(AppException) as exc_info:
        decode_access_token("invalid_token")
    assert exc_info.value.status_code == 401


# ============================================================================
# Repository Tests
# ============================================================================


def test_create_user(user_repo: UserRepository):
    """Test user creation."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    assert user.id is not None
    assert user.email == email
    assert user.password_hash == password_hash
    assert user.is_active is True


def test_create_user_duplicate_email(user_repo: UserRepository):
    """Test creating user with duplicate email."""
    from app.core.exceptions import AppException

    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user_repo.create_user(email, password_hash, display_name)
    with pytest.raises(AppException) as exc_info:
        user_repo.create_user(email, password_hash, display_name)
    assert exc_info.value.status_code == 400


def test_get_user_by_id(user_repo: UserRepository):
    """Test getting user by ID."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    retrieved = user_repo.get_user_by_id(user.id)
    assert retrieved is not None
    assert retrieved.id == user.id
    assert retrieved.email == email


def test_get_user_by_id_not_found(user_repo: UserRepository):
    """Test getting non-existent user by ID."""
    retrieved = user_repo.get_user_by_id("non_existent_id")
    assert retrieved is None


def test_get_user_by_email(user_repo: UserRepository):
    """Test getting user by email."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user_repo.create_user(email, password_hash, display_name)
    retrieved = user_repo.get_user_by_email(email)
    assert retrieved is not None
    assert retrieved.email == email


def test_get_user_by_email_case_insensitive(user_repo: UserRepository):
    """Test getting user by email (case-insensitive)."""
    email = "Test@Example.COM"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(normalize_email(email), password_hash, display_name)
    # Should find with different case
    retrieved = user_repo.get_user_by_email("test@example.com")
    assert retrieved is not None
    assert retrieved.id == user.id


def test_get_user_profile(user_repo: UserRepository):
    """Test getting user profile."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    profile = user_repo.get_user_profile(user.id)
    assert profile is not None
    assert profile.user_id == user.id
    assert profile.display_name == display_name


def test_update_user_profile(user_repo: UserRepository):
    """Test updating user profile."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    new_display_name = "Updated Name"
    profile = user_repo.update_user_profile(user.id, display_name=new_display_name)
    assert profile is not None
    assert profile.display_name == new_display_name


def test_create_refresh_token_entry(user_repo: UserRepository):
    """Test creating refresh token entry."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    token = create_refresh_token()
    token_hash = hash_refresh_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db_token = user_repo.create_refresh_token(user.id, token_hash, expires_at)
    assert db_token.id is not None
    assert db_token.user_id == user.id
    assert db_token.revoked is False


def test_revoke_refresh_token(user_repo: UserRepository):
    """Test revoking refresh token."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    token = create_refresh_token()
    token_hash = hash_refresh_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    user_repo.create_refresh_token(user.id, token_hash, expires_at)
    result = user_repo.revoke_refresh_token(token_hash)
    assert result is True
    # Verify it's revoked
    db_token = user_repo.get_refresh_token_by_hash(token_hash)
    assert db_token.revoked is True


def test_is_token_valid(user_repo: UserRepository):
    """Test checking token validity."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    token = create_refresh_token()
    token_hash = hash_refresh_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    user_repo.create_refresh_token(user.id, token_hash, expires_at)
    assert user_repo.is_token_valid(token_hash) is True


def test_is_token_valid_revoked(user_repo: UserRepository):
    """Test checking validity of revoked token."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    token = create_refresh_token()
    token_hash = hash_refresh_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    user_repo.create_refresh_token(user.id, token_hash, expires_at)
    user_repo.revoke_refresh_token(token_hash)
    assert user_repo.is_token_valid(token_hash) is False


def test_is_token_valid_expired(user_repo: UserRepository):
    """Test checking validity of expired token."""
    email = "test@example.com"
    password_hash = hash_password("password123")
    display_name = "Test User"
    user = user_repo.create_user(email, password_hash, display_name)
    token = create_refresh_token()
    token_hash = hash_refresh_token(token)
    expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    user_repo.create_refresh_token(user.id, token_hash, expires_at)
    assert user_repo.is_token_valid(token_hash) is False


# ============================================================================
# Service Tests
# ============================================================================


def test_register_user(auth_service: AuthService):
    """Test user registration."""
    email = "test@example.com"
    password = "password123"
    display_name = "Test User"
    response = auth_service.register_user(email, password, display_name)
    assert response.data["user"]["email"] == email
    assert response.data["user"]["display_name"] == display_name


def test_register_user_duplicate_email(auth_service: AuthService):
    """Test registering user with duplicate email."""
    from app.core.exceptions import AppException

    email = "test@example.com"
    password = "password123"
    display_name = "Test User"
    auth_service.register_user(email, password, display_name)
    with pytest.raises(AppException) as exc_info:
        auth_service.register_user(email, password, display_name)
    assert exc_info.value.status_code == 400


def test_authenticate_user(auth_service: AuthService):
    """Test user authentication."""
    email = "test@example.com"
    password = "password123"
    display_name = "Test User"
    auth_service.register_user(email, password, display_name)
    response = auth_service.authenticate_user(email, password)
    assert response.data.access_token is not None
    assert response.data.refresh_token is not None


def test_authenticate_user_wrong_password(auth_service: AuthService):
    """Test authentication with wrong password."""
    from app.core.exceptions import AppException

    email = "test@example.com"
    password = "password123"
    display_name = "Test User"
    auth_service.register_user(email, password, display_name)
    with pytest.raises(AppException) as exc_info:
        auth_service.authenticate_user(email, "wrong_password")
    assert exc_info.value.status_code == 401


def test_authenticate_user_not_found(auth_service: AuthService):
    """Test authentication with non-existent email."""
    from app.core.exceptions import AppException

    with pytest.raises(AppException) as exc_info:
        auth_service.authenticate_user("nonexistent@example.com", "password")
    assert exc_info.value.status_code == 401


def test_refresh_access_token(auth_service: AuthService):
    """Test refreshing access token."""
    email = "test@example.com"
    password = "password123"
    display_name = "Test User"
    auth_service.register_user(email, password, display_name)
    login_response = auth_service.authenticate_user(email, password)
    old_refresh_token = login_response.data.refresh_token
    new_response = auth_service.refresh_access_token(old_refresh_token)
    assert new_response.access_token is not None
    assert new_response.refresh_token is not None
    # Refresh token should be different (rotation)
    assert new_response.refresh_token != old_refresh_token


def test_refresh_access_token_rotation(auth_service: AuthService, user_repo: UserRepository):
    """Test that refresh token rotation revokes old token."""
    email = "test@example.com"
    password = "password123"
    display_name = "Test User"
    auth_service.register_user(email, password, display_name)
    login_response = auth_service.authenticate_user(email, password)
    old_refresh_token = login_response.data.refresh_token
    auth_service.refresh_access_token(old_refresh_token)
    # Old refresh token should not be reusable
    with pytest.raises(Exception):
        auth_service.refresh_access_token(old_refresh_token)


def test_logout_user(auth_service: AuthService):
    """Test user logout."""
    email = "test@example.com"
    password = "password123"
    display_name = "Test User"
    auth_service.register_user(email, password, display_name)
    login_response = auth_service.authenticate_user(email, password)
    auth_service.logout_user(login_response.data.refresh_token)
    # After logout, refresh should fail
    with pytest.raises(Exception):
        auth_service.refresh_access_token(login_response.data.refresh_token)


def test_logout_idempotent(auth_service: AuthService):
    """Test that logout is idempotent."""
    email = "test@example.com"
    password = "password123"
    display_name = "Test User"
    auth_service.register_user(email, password, display_name)
    login_response = auth_service.authenticate_user(email, password)
    # First logout
    auth_service.logout_user(login_response.data.refresh_token)
    # Second logout should not raise
    auth_service.logout_user(login_response.data.refresh_token)


# ============================================================================
# Endpoint Tests
# ============================================================================


def test_register_endpoint(client: TestClient):
    """Test register endpoint."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["user"]["email"] == "test@example.com"


def test_login_endpoint(client: TestClient):
    """Test login endpoint."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_token" in response.json()["data"]


def test_me_endpoint(client: TestClient):
    """Test get current user endpoint."""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["data"]["access_token"]
    # Get user
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "test@example.com"


def test_me_endpoint_no_token(client: TestClient):
    """Test get current user endpoint without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_logout_endpoint(client: TestClient):
    """Test logout endpoint."""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["data"]["access_token"]
    refresh_token = login_response.json()["data"]["refresh_token"]
    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


def test_profile_endpoint(client: TestClient):
    """Test get profile endpoint."""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["data"]["access_token"]
    # Get profile
    response = client.get(
        "/api/v1/settings/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "test@example.com"


def test_update_profile_endpoint(client: TestClient):
    """Test update profile endpoint."""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["data"]["access_token"]
    # Update profile
    response = client.patch(
        "/api/v1/settings/profile",
        json={"display_name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["display_name"] == "Updated Name"

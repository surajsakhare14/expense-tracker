"""Business logic layer for authentication.

Handles:
- User registration
- User login
- Token refresh and rotation
- User logout
- Current user retrieval
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    normalize_email,
    validate_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResponse, RegisterResponse, TokenResponse, UserResponse


class AuthService:
    """Authentication business logic."""

    def __init__(self, session: Session):
        """Initialize service with database session.

        Args:
            session: SQLAlchemy database session
        """
        self.repository = UserRepository(session)
        self.session = session

    def register_user(self, email: str, password: str, display_name: str) -> RegisterResponse:
        """Register a new user.

        Args:
            email: User email
            password: User password
            display_name: User display name

        Returns:
            RegisterResponse with created user info

        Raises:
            AppException: If email exists, password invalid, or registration fails
        """
        # Normalize email
        email = normalize_email(email)

        # Validate password
        try:
            validate_password(password)
        except Exception as exc:
            raise AppException(
                code="INVALID_PASSWORD",
                message=str(exc),
                status_code=400,
            ) from exc

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = self.repository.create_user(email, password_hash, display_name)

        # Build response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            display_name=display_name,
        )
        return RegisterResponse(user=user_response)

    def authenticate_user(self, email: str, password: str) -> LoginResponse:
        """Authenticate user and issue tokens.

        Args:
            email: User email
            password: User password

        Returns:
            LoginResponse with access and refresh tokens

        Raises:
            AppException: If email/password incorrect or user inactive
        """
        # Normalize email
        email = normalize_email(email)

        # Get user
        user = self.repository.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            # Generic error: don't reveal if email exists
            raise AppException(
                code="INVALID_CREDENTIALS",
                message="Email or password is incorrect.",
                status_code=401,
            )

        if not user.is_active:
            raise AppException(
                code="USER_INACTIVE",
                message="User account is inactive.",
                status_code=401,
            )

        # Create tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token()
        refresh_token_hash = hash_refresh_token(refresh_token)

        # Store refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        self.repository.create_refresh_token(user.id, refresh_token_hash, expires_at)

        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,
        )
        return LoginResponse(data=token_response)

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token (with rotation).

        Args:
            refresh_token: User's refresh token (plaintext)

        Returns:
            TokenResponse with new access and refresh tokens

        Raises:
            AppException: If refresh token invalid, expired, or revoked
        """
        # Hash the provided token to look it up
        refresh_token_hash = hash_refresh_token(refresh_token)

        # Get token from DB
        db_token = self.repository.get_refresh_token_by_hash(refresh_token_hash)
        if not db_token:
            raise AppException(
                code="INVALID_TOKEN",
                message="Invalid or expired token.",
                status_code=401,
            )

        if db_token.revoked:
            raise AppException(
                code="TOKEN_REVOKED",
                message="Invalid or expired token.",
                status_code=401,
            )

        now = datetime.now(timezone.utc)
        if db_token.expires_at < now:
            raise AppException(
                code="TOKEN_EXPIRED",
                message="Invalid or expired token.",
                status_code=401,
            )

        user = self.repository.get_user_by_id(db_token.user_id)
        if not user or not user.is_active:
            raise AppException(
                code="USER_INACTIVE",
                message="Invalid or expired token.",
                status_code=401,
            )

        # Token rotation: revoke old token
        self.repository.revoke_refresh_token(refresh_token_hash)

        # Issue new tokens
        access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token()
        new_refresh_token_hash = hash_refresh_token(new_refresh_token)

        new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        self.repository.create_refresh_token(user.id, new_refresh_token_hash, new_expires_at)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=3600,
        )

    def logout_user(self, refresh_token: str) -> None:
        """Logout user by revoking refresh token.

        Idempotent: returns successfully even if token not found or already revoked.

        Args:
            refresh_token: User's refresh token (plaintext)
        """
        refresh_token_hash = hash_refresh_token(refresh_token)
        # Idempotent: just attempt to revoke, don't error if not found
        self.repository.revoke_refresh_token(refresh_token_hash)

    def get_current_user_data(self, user_id: str) -> dict:
        """Get current user information.

        Args:
            user_id: User UUID (from JWT)

        Returns:
            Dictionary with user id, email, display_name

        Raises:
            AppException: If user not found or inactive
        """
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise AppException(
                code="USER_NOT_FOUND",
                message="User not found.",
                status_code=401,
            )

        if not user.is_active:
            raise AppException(
                code="USER_INACTIVE",
                message="User account is inactive.",
                status_code=401,
            )

        profile = self.repository.get_user_profile(user_id)
        display_name = profile.display_name if profile else "Unknown"

        return {
            "id": user.id,
            "email": user.email,
            "display_name": display_name,
        }

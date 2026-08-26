"""Repository layer for user data access.

Handles all database operations for users, profiles, and refresh tokens.
Provides CRUD operations and queries for authentication.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.user import RefreshToken, User, UserProfile


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def create_user(self, email: str, password_hash: str, display_name: str) -> User:
        """Create a new user with profile.

        Args:
            email: User email (normalized)
            password_hash: Argon2 password hash
            display_name: User display name

        Returns:
            Created User object

        Raises:
            AppException: If email already exists
        """
        # Check if email already exists (case-insensitive)
        existing = self.get_user_by_email(email)
        if existing:
            raise AppException(
                code="EMAIL_ALREADY_EXISTS",
                message="Email is already registered.",
                status_code=400,
            )

        user_id = str(uuid4())

        # Create user
        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash,
        )
        self.session.add(user)
        self.session.flush()  # Flush to get the user in session

        # Create profile
        profile = UserProfile(
            id=str(uuid4()),
            user_id=user_id,
            display_name=display_name,
        )
        self.session.add(profile)
        self.session.flush()

        self.session.commit()
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User object or None if not found
        """
        stmt = select(User).where(User.id == user_id)
        return self.session.scalars(stmt).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive).

        Args:
            email: User email (normalized)

        Returns:
            User object or None if not found
        """
        # Use LOWER() for case-insensitive comparison
        stmt = select(User).where(func.lower(User.email) == func.lower(email))
        return self.session.scalars(stmt).first()

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID.

        Args:
            user_id: User UUID

        Returns:
            UserProfile object or None if not found
        """
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        return self.session.scalars(stmt).first()

    def update_user_profile(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Optional[UserProfile]:
        """Update user profile.

        Args:
            user_id: User UUID
            display_name: New display name (optional)
            avatar_url: New avatar URL (optional)

        Returns:
            Updated UserProfile or None if not found
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return None

        if display_name is not None:
            profile.display_name = display_name
        if avatar_url is not None:
            profile.avatar_url = avatar_url

        profile.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        return profile

    def create_refresh_token(
        self, user_id: str, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        """Create a refresh token entry.

        Args:
            user_id: User UUID
            token_hash: Argon2 hash of the refresh token (never raw token)
            expires_at: Token expiration timestamp

        Returns:
            Created RefreshToken object
        """
        token = RefreshToken(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        self.session.commit()
        return token

    def get_refresh_token_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by its hash.

        Args:
            token_hash: Argon2 hash of the refresh token

        Returns:
            RefreshToken object or None if not found
        """
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.session.scalars(stmt).first()

    def revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a refresh token.

        Args:
            token_hash: Argon2 hash of the refresh token

        Returns:
            True if token was revoked, False if not found
        """
        token = self.get_refresh_token_by_hash(token_hash)
        if not token:
            return False

        token.revoked = True
        self.session.commit()
        return True

    def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user.

        Args:
            user_id: User UUID
        """
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        tokens = self.session.scalars(stmt).all()
        for token in tokens:
            token.revoked = True
        self.session.commit()

    def is_token_valid(self, token_hash: str) -> bool:
        """Check if a refresh token is valid (exists, not revoked, not expired).

        Args:
            token_hash: Argon2 hash of the refresh token

        Returns:
            True if token is valid, False otherwise
        """
        token = self.get_refresh_token_by_hash(token_hash)
        if not token:
            return False

        if token.revoked:
            return False

        now = datetime.now(timezone.utc)
        if token.expires_at < now:
            return False

        return True

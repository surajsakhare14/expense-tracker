"""Security utilities for authentication and token management.

Handles:
- Password hashing and verification (Argon2)
- Refresh token hashing and verification (SHA256 for deterministic lookups)
- JWT access token creation and decoding
- Password validation
- Email normalization
"""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Dict

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import AppException

# Argon2 password hasher - used for passwords only
_hasher = PasswordHasher()

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using Argon2.

    Args:
        password: Plain text password to hash

    Returns:
        Argon2 hash string

    Raises:
        AppException: If hashing fails
    """
    try:
        return _hasher.hash(password)
    except Exception as exc:
        raise AppException(
            code="PASSWORD_HASH_ERROR",
            message="Password hashing failed.",
            status_code=500,
        ) from exc


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        password_hash: Argon2 hash to verify against

    Returns:
        True if password matches hash, False otherwise
    """
    try:
        _hasher.verify(password_hash, plain_password)
        return True
    except (InvalidHash, VerificationError):
        return False
    except Exception:
        # Any other exception means verification failed
        return False


def validate_password(password: str) -> None:
    """Validate password meets minimum requirements.

    Args:
        password: Password to validate

    Raises:
        ValidationError: If password doesn't meet requirements
    """
    min_length = settings.password_min_length
    max_length = settings.password_max_length

    if len(password) < min_length:
        raise ValidationError(
            f"Password must be at least {min_length} characters long."
        )
    if len(password) > max_length:
        raise ValidationError(f"Password must be at most {max_length} characters long.")


def normalize_email(email: str) -> str:
    """Normalize email: trim whitespace and convert to lowercase.

    Args:
        email: Raw email string

    Returns:
        Normalized email (lowercase, trimmed)
    """
    return email.strip().lower()


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token using SHA256 (deterministic for database lookups).

    Args:
        token: Raw refresh token string

    Returns:
        SHA256 hash of the token (hex format)

    Raises:
        AppException: If hashing fails
    """
    try:
        return sha256(token.encode()).hexdigest()
    except Exception as exc:
        raise AppException(
            code="TOKEN_HASH_ERROR",
            message="Token hashing failed.",
            status_code=500,
        ) from exc

def verify_refresh_token(plain_token: str, token_hash: str) -> bool:
    """Verify a refresh token against its SHA256 hash.

    Args:
        plain_token: Raw refresh token string
        token_hash: SHA256 hash of the token

    Returns:
        True if token matches hash, False otherwise
    """
    try:
        computed_hash = sha256(plain_token.encode()).hexdigest()
        return computed_hash == token_hash
    except Exception:
        return False


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID to include in token
        expires_delta: Custom expiration time (defaults to configured TTL)

    Returns:
        Encoded JWT token string

    Raises:
        AppException: If token creation fails
    """
    try:
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.token_expire_minutes)

        now = datetime.now(timezone.utc)
        expire_at = now + expires_delta

        payload = {
            "user_id": user_id,
            "exp": expire_at,
            "iat": now,
        }

        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return token
    except Exception as exc:
        raise AppException(
            code="TOKEN_CREATION_ERROR",
            message="Access token creation failed.",
            status_code=500,
        ) from exc


def create_refresh_token() -> str:
    """Generate a random refresh token string.

    Returns:
        Random token string (base64-like format)
    """
    import secrets

    return secrets.token_urlsafe(32)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        AppException: If token is invalid, expired, or cannot be decoded
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise AppException(
            code="TOKEN_EXPIRED",
            message="Token has expired.",
            status_code=401,
        )
    except jwt.InvalidTokenError as exc:
        raise AppException(
            code="INVALID_TOKEN",
            message="Invalid token.",
            status_code=401,
        ) from exc
    except Exception as exc:
        raise AppException(
            code="TOKEN_DECODE_ERROR",
            message="Token validation failed.",
            status_code=401,
        ) from exc

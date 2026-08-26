from fastapi import Header

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import decode_access_token

__all__ = ["get_db", "get_current_user"]


async def get_current_user(
    authorization: str = Header(None),
):
    """Extract and validate JWT token from Authorization header.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")

    Returns:
        Dictionary with user_id, exp, iat from token payload

    Raises:
        AppException: If token missing, malformed, invalid, or expired
    """
    if not authorization:
        raise AppException(
            code="MISSING_TOKEN",
            message="Authorization header is missing.",
            status_code=401,
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AppException(
            code="INVALID_AUTHORIZATION_HEADER",
            message="Invalid authorization header format. Expected: Bearer <token>",
            status_code=401,
        )

    token = parts[1]
    payload = decode_access_token(token)

    return payload
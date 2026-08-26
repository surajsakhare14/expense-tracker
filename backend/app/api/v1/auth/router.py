"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)
from app.schemas.user import UserProfileDataResponse, UserProfileResponse, UserProfileUpdateRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: Session = Depends(get_db),
) -> RegisterResponse:
    """Register a new user.

    Args:
        request: Registration request with email, password, display_name

    Returns:
        RegisterResponse with created user information (no tokens)

    Raises:
        400: If email already exists or password invalid
        500: If registration fails
    """
    service = AuthService(session)
    return service.register_user(request.email, request.password, request.display_name)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    session: Session = Depends(get_db),
) -> LoginResponse:
    """Login user and issue tokens.

    Args:
        request: Login request with email and password

    Returns:
        LoginResponse with access_token and refresh_token

    Raises:
        401: If email or password incorrect, or user inactive
        500: If login fails
    """
    service = AuthService(session)
    return service.authenticate_user(request.email, request.password)


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    request: RefreshTokenRequest,
    session: Session = Depends(get_db),
) -> RefreshTokenResponse:
    """Refresh access token.

    Token rotation: old refresh token is revoked, new one issued.

    Args:
        request: RefreshTokenRequest with refresh_token

    Returns:
        RefreshTokenResponse with new access_token and refresh_token

    Raises:
        401: If refresh token invalid, expired, or revoked
        500: If refresh fails
    """
    service = AuthService(session)
    token_response = service.refresh_access_token(request.refresh_token)
    return RefreshTokenResponse(data=token_response)


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CurrentUserResponse:
    """Get current authenticated user.

    Args:
        current_user: Injected from JWT token

    Returns:
        CurrentUserResponse with user id, email, display_name

    Raises:
        401: If token invalid, expired, or user not found
    """
    service = AuthService(session)
    user_data = service.get_current_user_data(current_user["user_id"])
    user_response = UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        display_name=user_data["display_name"],
    )
    return CurrentUserResponse(data=user_response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: LogoutRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> None:
    """Logout user by revoking refresh token.

    Idempotent: returns 204 even if token already revoked or not found.

    Args:
        request: LogoutRequest with refresh_token
        current_user: Injected from JWT token (ensures auth)

    Returns:
        204 No Content
    """
    service = AuthService(session)
    service.logout_user(request.refresh_token)


# Profile endpoints (under /settings/profile, but included in auth router for organization)
profile_router = APIRouter(prefix="/settings/profile", tags=["profile"])


@profile_router.get("", status_code=status.HTTP_200_OK)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> UserProfileDataResponse:
    """Get current user profile.

    Args:
        current_user: Injected from JWT token

    Returns:
        UserProfileDataResponse with user profile information

    Raises:
        401: If token invalid or user not found
    """
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(session)
    profile = repo.get_user_profile(current_user["user_id"])

    if not profile:
        from app.core.exceptions import AppException

        raise AppException(
            code="PROFILE_NOT_FOUND",
            message="User profile not found.",
            status_code=404,
        )

    user = repo.get_user_by_id(current_user["user_id"])

    return UserProfileDataResponse(
        data=UserProfileResponse(
            user_id=profile.user_id,
            display_name=profile.display_name,
            email=user.email,
            currency=profile.currency,
            timezone=profile.timezone,
            avatar_url=profile.avatar_url,
        )
    )


@profile_router.patch("", status_code=status.HTTP_200_OK)
async def update_profile(
    request: UserProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> UserProfileDataResponse:
    """Update current user profile.

    Args:
        request: UserProfileUpdateRequest with optional display_name and avatar_url
        current_user: Injected from JWT token

    Returns:
        UserProfileDataResponse with updated profile

    Raises:
        401: If token invalid or user not found
        404: If user profile not found
    """
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(session)
    profile = repo.update_user_profile(
        current_user["user_id"],
        display_name=request.display_name,
        avatar_url=request.avatar_url,
    )

    if not profile:
        from app.core.exceptions import AppException

        raise AppException(
            code="PROFILE_NOT_FOUND",
            message="User profile not found.",
            status_code=404,
        )

    user = repo.get_user_by_id(current_user["user_id"])

    return UserProfileDataResponse(
        data=UserProfileResponse(
            user_id=profile.user_id,
            display_name=profile.display_name,
            email=user.email,
            currency=profile.currency,
            timezone=profile.timezone,
            avatar_url=profile.avatar_url,
        )
    )

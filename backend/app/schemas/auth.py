"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=255, description="User password")
    display_name: str = Field(..., min_length=1, max_length=255, description="Display name")


class UserResponse(BaseModel):
    """User information response."""

    id: str
    email: str
    display_name: str


class RegisterResponse(BaseModel):
    """User registration response."""

    data: dict = Field(default_factory=dict)

    def __init__(self, user: UserResponse, **kwargs):
        super().__init__(data={"user": user.model_dump()}, **kwargs)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Token response for login and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class LoginResponse(BaseModel):
    """Login response with tokens."""

    data: TokenResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response."""

    data: TokenResponse


class CurrentUserResponse(BaseModel):
    """Current user information."""

    data: UserResponse


class LogoutRequest(BaseModel):
    """Logout request."""

    refresh_token: str = Field(..., description="Refresh token to revoke")

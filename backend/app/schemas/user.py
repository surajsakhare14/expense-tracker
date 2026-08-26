"""Pydantic schemas for user profile endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    """User profile information."""

    user_id: str
    display_name: str
    email: str
    currency: str
    timezone: str
    avatar_url: Optional[str] = None


class UserProfileUpdateRequest(BaseModel):
    """User profile update request."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=2048)


class UserProfileDataResponse(BaseModel):
    """Wrapped user profile response."""

    data: UserProfileResponse

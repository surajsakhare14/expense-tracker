"""Pydantic schemas for category endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CategoryType = Literal["EXPENSE", "INCOME"]


class CategoryCreateRequest(BaseModel):
    """Request to create a custom category."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    type: CategoryType

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class CategoryUpdateRequest(BaseModel):
    """Request to update a custom category."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=255)
    type: CategoryType | None = None

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class CategoryResponse(BaseModel):
    """Category response using the documented API field name."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: CategoryType = Field(validation_alias="category_type")
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CategoryDataResponse(BaseModel):
    """Wrapped category response."""

    data: CategoryResponse


class CategoryListResponse(BaseModel):
    """Wrapped category collection response."""

    data: list[CategoryResponse]

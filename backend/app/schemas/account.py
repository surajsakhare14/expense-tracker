"""Pydantic schemas for account endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

AccountType = Literal["BANK", "CASH", "CREDIT_CARD", "WALLET", "OTHER"]


class AccountCreateRequest(BaseModel):
    """Request to create an account."""

    name: str = Field(..., min_length=1, max_length=255)
    account_type: AccountType
    institution_name: str | None = Field(None, max_length=255)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("name", "currency", "institution_name", mode="before")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        value = value.upper()
        if not value.isalpha():
            raise ValueError("Currency must contain exactly three letters.")
        return value


class AccountUpdateRequest(BaseModel):
    """Request to update editable account fields."""

    name: str | None = Field(None, min_length=1, max_length=255)
    account_type: AccountType | None = None
    institution_name: str | None = Field(None, max_length=255)
    currency: str | None = Field(None, min_length=3, max_length=3)

    @field_validator("name", "currency", "institution_name", mode="before")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.upper()
        if not value.isalpha():
            raise ValueError("Currency must contain exactly three letters.")
        return value


class AccountResponse(BaseModel):
    """Account response."""

    id: str
    name: str
    account_type: AccountType
    institution_name: str | None
    currency: str
    current_balance: Decimal
    is_active: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AccountDataResponse(BaseModel):
    """Wrapped single-account response."""

    data: AccountResponse


class AccountListResponse(BaseModel):
    """Wrapped account collection response."""

    data: list[AccountResponse]

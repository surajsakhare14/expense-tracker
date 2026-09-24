"""Pydantic schemas for transfer endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TransferStatus = Literal["PENDING", "COMPLETED", "CANCELLED"]


class TransferCreateRequest(BaseModel):
    """Request to create a transfer between two user-owned accounts.

    ``status`` is intentionally not exposed: manual transfers default to
    COMPLETED at the service layer.
    """

    model_config = ConfigDict(extra="forbid")

    source_account_id: str = Field(..., min_length=1)
    destination_account_id: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    transfer_date: datetime
    description: str | None = Field(None, max_length=500)

    @field_validator("description", mode="before")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class TransferUpdateRequest(BaseModel):
    """Request to update editable fields of a transfer.

    Source and destination accounts are fixed once a transfer exists and are not
    editable. All fields are optional; only provided fields are applied.
    """

    model_config = ConfigDict(extra="forbid")

    amount: Decimal | None = Field(None, gt=0)
    transfer_date: datetime | None = None
    description: str | None = Field(None, max_length=500)

    @field_validator("description", mode="before")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class TransferResponse(BaseModel):
    """Transfer response for normal retrieval (soft-delete state omitted)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    status: TransferStatus
    transfer_date: datetime
    description: str | None
    created_at: datetime
    updated_at: datetime


class TransferDataResponse(BaseModel):
    """Wrapped single-transfer response."""

    data: TransferResponse


class TransferListResponse(BaseModel):
    """Wrapped transfer collection response."""

    data: list[TransferResponse]

"""Pydantic schemas for transaction endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Users may only create/retype income and expense transactions. OPENING_BALANCE
# is created only as part of account creation, and BALANCE_ADJUSTMENT has its
# own dedicated endpoint; neither is a user-selectable type here.
TransactionTypeInput = Literal["INCOME", "EXPENSE"]
TransactionType = Literal["INCOME", "EXPENSE", "OPENING_BALANCE", "BALANCE_ADJUSTMENT"]
TransactionStatus = Literal["PENDING", "COMPLETED", "CANCELLED"]


class TransactionCreateRequest(BaseModel):
    """Request to create a manual transaction.

    ``status`` is intentionally not exposed: manual transactions default to
    COMPLETED at the service layer. ``category_id`` stays optional at the schema
    level; the service enforces that INCOME/EXPENSE require a matching category.
    """

    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(..., min_length=1)
    category_id: str | None = Field(None, min_length=1)
    transaction_type: TransactionTypeInput
    amount: Decimal = Field(..., gt=0)
    transaction_date: datetime
    description: str | None = Field(None, max_length=500)
    merchant_name: str | None = Field(None, max_length=255)

    @field_validator("description", "merchant_name", mode="before")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class BalanceAdjustmentRequest(BaseModel):
    """Request to record a manual BALANCE_ADJUSTMENT against an account.

    The signed ``amount`` is applied directly to the balance (positive raises,
    negative lowers) and must be non-zero. ``transaction_type``, ``status`` and
    ``category`` are fixed by the endpoint and never accepted from the client.
    """

    model_config = ConfigDict(extra="forbid")

    amount: Decimal
    transaction_date: datetime
    description: str | None = Field(None, max_length=500)

    @field_validator("amount")
    @classmethod
    def non_zero(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("Balance adjustment amount must not be zero.")
        return value

    @field_validator("description", mode="before")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class TransactionUpdateRequest(BaseModel):
    """Request to update editable fields of a transaction.

    ``account_id`` and ``status`` are not editable through the API. All fields
    are optional; only provided fields are applied.
    """

    model_config = ConfigDict(extra="forbid")

    category_id: str | None = Field(None, min_length=1)
    transaction_type: TransactionTypeInput | None = None
    amount: Decimal | None = Field(None, gt=0)
    transaction_date: datetime | None = None
    description: str | None = Field(None, max_length=500)
    merchant_name: str | None = Field(None, max_length=255)

    @field_validator("description", "merchant_name", mode="before")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class TransactionResponse(BaseModel):
    """Transaction response for normal retrieval (soft-delete state omitted)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    category_id: str | None
    transaction_type: TransactionType
    status: TransactionStatus
    amount: Decimal
    transaction_date: datetime
    description: str | None
    merchant_name: str | None
    created_at: datetime
    updated_at: datetime


class TransactionDataResponse(BaseModel):
    """Wrapped single-transaction response."""

    data: TransactionResponse


class TransactionListResponse(BaseModel):
    """Wrapped transaction collection response."""

    data: list[TransactionResponse]

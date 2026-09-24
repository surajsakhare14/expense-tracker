"""SQLAlchemy model for money transfers between two user-owned accounts."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.account import Account


class Transfer(Base):
    """A movement of funds from one account to another.

    A ``COMPLETED`` transfer debits the source and credits the destination in a
    single atomic operation. A transfer is never an income/expense transaction;
    credit-card payments are modelled as transfers. Deletions are soft
    (``deleted_at``) so transfer history is preserved.
    """

    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'CANCELLED')",
            name="ck_transfers_status",
        ),
        CheckConstraint("amount > 0", name="ck_transfers_amount_positive"),
        CheckConstraint(
            "source_account_id <> destination_account_id",
            name="ck_transfers_distinct_accounts",
        ),
        Index("ix_transfers_source_account_id_transfer_date", "source_account_id", "transfer_date"),
        Index(
            "ix_transfers_destination_account_id_transfer_date",
            "destination_account_id",
            "transfer_date",
        ),
        Index("ix_transfers_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), nullable=False
    )
    destination_account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    transfer_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[source_account_id]
    )
    destination_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[destination_account_id]
    )

    def __repr__(self) -> str:
        return (
            f"<Transfer id={self.id} source={self.source_account_id} "
            f"destination={self.destination_account_id} "
            f"status={self.status} amount={self.amount}>"
        )

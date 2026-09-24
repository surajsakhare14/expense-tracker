"""SQLAlchemy model for the transaction ledger (financial events)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.category import Category


class Transaction(Base):
    """A single financial event against one account.

    A transaction is the immutable-by-default ledger entry that drives an
    account's ``current_balance`` snapshot. Only ``COMPLETED`` transactions
    affect balance; ``PENDING`` and ``CANCELLED`` do not. Deletions are soft
    (``deleted_at``) so financial history is never physically removed.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN "
            "('INCOME', 'EXPENSE', 'OPENING_BALANCE', 'BALANCE_ADJUSTMENT')",
            name="ck_transactions_transaction_type",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'CANCELLED')",
            name="ck_transactions_status",
        ),
        CheckConstraint(
            "(transaction_type IN ('INCOME', 'EXPENSE') AND amount > 0) OR "
            "(transaction_type IN ('OPENING_BALANCE', 'BALANCE_ADJUSTMENT') "
            "AND amount <> 0)",
            name="ck_transactions_amount_sign",
        ),
        CheckConstraint(
            "(transaction_type IN ('INCOME', 'EXPENSE') AND category_id IS NOT NULL) OR "
            "(transaction_type IN ('OPENING_BALANCE', 'BALANCE_ADJUSTMENT') "
            "AND category_id IS NULL)",
            name="ck_transactions_category_presence",
        ),
        Index("ix_transactions_account_id_transaction_date", "account_id", "transaction_date"),
        Index("ix_transactions_account_id_status", "account_id", "status"),
        Index("ix_transactions_category_id", "category_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), nullable=False
    )
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
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

    account: Mapped["Account"] = relationship("Account")
    category: Mapped["Category | None"] = relationship("Category")

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} account_id={self.account_id} "
            f"type={self.transaction_type} status={self.status} amount={self.amount}>"
        )

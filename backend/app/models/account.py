"""SQLAlchemy model for user-owned financial accounts."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Account(Base):
    """A user-owned financial account."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('BANK', 'CASH', 'CREDIT_CARD', 'WALLET', 'OTHER')",
            name="ck_accounts_account_type",
        ),
        CheckConstraint(
            "currency = upper(currency) AND length(currency) = 3",
            name="ck_accounts_currency_format",
        ),
        CheckConstraint(
            "(is_active = TRUE AND archived_at IS NULL) OR "
            "(is_active = FALSE AND archived_at IS NOT NULL)",
            name="ck_accounts_archive_state",
        ),
        Index(
            "uq_accounts_active_user_name",
            "user_id",
            text("lower(name)"),
            unique=True,
            postgresql_where=text("archived_at IS NULL"),
        ),
        Index("ix_accounts_user_id_is_active", "user_id", "is_active"),
        Index("ix_accounts_user_id_archived_at", "user_id", "archived_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    institution_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(19, 4), nullable=False, default=0
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="accounts")

    def __repr__(self) -> str:
        return f"<Account id={self.id} user_id={self.user_id} name={self.name}>"

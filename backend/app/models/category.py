"""SQLAlchemy model for system and user-defined categories."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Category(Base):
    """A global system category or a category owned by one user."""

    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "category_type IN ('EXPENSE', 'INCOME')",
            name="ck_categories_category_type",
        ),
        CheckConstraint(
            "(is_system = TRUE AND user_id IS NULL) OR "
            "(is_system = FALSE AND user_id IS NOT NULL)",
            name="ck_categories_scope",
        ),
        CheckConstraint(
            "parent_id IS NULL OR parent_id <> id", name="ck_categories_not_self_parent"
        ),
        CheckConstraint(
            "is_system = FALSE OR is_active = TRUE", name="ck_categories_system_active"
        ),
        Index(
            "uq_categories_active_system_name_type",
            text("lower(name)"),
            "category_type",
            unique=True,
            postgresql_where=text("is_system = TRUE AND is_active = TRUE"),
        ),
        Index(
            "uq_categories_active_user_name_type",
            "user_id",
            text("lower(name)"),
            "category_type",
            unique=True,
            postgresql_where=text("is_system = FALSE AND is_active = TRUE"),
        ),
        Index("ix_categories_user_id_is_active", "user_id", "is_active"),
        Index("ix_categories_category_type_is_active", "category_type", "is_active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_type: Mapped[str] = mapped_column(String(16), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True, index=True
    )
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User | None"] = relationship("User", back_populates="categories")
    parent: Mapped["Category | None"] = relationship("Category", remote_side="Category.id")

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name} system={self.is_system}>"

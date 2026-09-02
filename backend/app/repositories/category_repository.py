"""Repository operations for system and user-owned categories."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.category import Category


class CategoryRepository:
    """Database access for categories with explicit visibility rules."""

    def __init__(self, session: Session):
        self.session = session

    def create_category(self, user_id: str, name: str, category_type: str) -> Category:
        category = Category(
            id=str(uuid4()),
            user_id=user_id,
            name=name,
            category_type=category_type,
            is_system=False,
            is_active=True,
        )
        self.session.add(category)
        self.session.flush()
        self.session.commit()
        return category

    def list_categories(self, user_id: str, category_type: str | None = None) -> list[Category]:
        conditions = [
            Category.is_active.is_(True),
            or_(Category.is_system.is_(True), Category.user_id == user_id),
        ]
        if category_type is not None:
            conditions.append(Category.category_type == category_type)
        statement = select(Category).where(*conditions).order_by(
            Category.is_system.desc(), Category.category_type, Category.name
        )
        return list(self.session.scalars(statement).all())

    def get_visible_category(self, category_id: str, user_id: str) -> Category | None:
        statement = select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
            or_(Category.is_system.is_(True), Category.user_id == user_id),
        )
        return self.session.scalars(statement).first()

    def get_custom_category(self, category_id: str, user_id: str) -> Category | None:
        statement = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.is_system.is_(False),
            Category.is_active.is_(True),
        )
        return self.session.scalars(statement).first()

    def has_active_name(
        self, user_id: str, name: str, category_type: str, exclude_id: str | None = None
    ) -> bool:
        conditions = [
            Category.user_id == user_id,
            Category.is_system.is_(False),
            Category.is_active.is_(True),
            Category.name.ilike(name),
            Category.category_type == category_type,
        ]
        if exclude_id is not None:
            conditions.append(Category.id != exclude_id)
        return self.session.scalars(select(Category.id).where(*conditions)).first() is not None

    def has_active_system_name(self, name: str, category_type: str) -> bool:
        statement = select(Category.id).where(
            Category.is_system.is_(True),
            Category.is_active.is_(True),
            Category.name.ilike(name),
            Category.category_type == category_type,
        )
        return self.session.scalars(statement).first() is not None

    def has_transaction_references(self, category_id: str) -> bool:
        transaction_table = Base.metadata.tables.get("transactions")
        if transaction_table is None:
            return False
        statement = select(transaction_table.c.id).where(
            transaction_table.c.category_id == category_id
        )
        return self.session.execute(statement.limit(1)).first() is not None

    def update_category(self, category: Category, values: dict[str, object]) -> Category:
        if "name" in values:
            category.name = values["name"]
        if "type" in values:
            category.category_type = values["type"]
        category.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return category

    def archive_category(self, category: Category) -> Category:
        category.is_active = False
        category.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return category

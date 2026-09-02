"""Add system and user-defined categories."""

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_add_categories"
down_revision = "0003_add_accounts"
branch_labels = None
depends_on = None

SYSTEM_CATEGORIES = (
    ("10000000-0000-0000-0000-000000000001", "Food", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000002", "Groceries", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000003", "Shopping", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000004", "Travel", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000005", "Transport", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000006", "Bills", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000007", "Entertainment", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000008", "Healthcare", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000009", "Education", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000010", "Personal Care", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000011", "Subscriptions", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000012", "Rent", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000013", "EMI", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000014", "Insurance", "EXPENSE"),
    ("10000000-0000-0000-0000-000000000015", "Other", "EXPENSE"),
    ("20000000-0000-0000-0000-000000000001", "Salary", "INCOME"),
    ("20000000-0000-0000-0000-000000000002", "Freelance", "INCOME"),
    ("20000000-0000-0000-0000-000000000003", "Business", "INCOME"),
    ("20000000-0000-0000-0000-000000000004", "Interest", "INCOME"),
    ("20000000-0000-0000-0000-000000000005", "Dividend", "INCOME"),
    ("20000000-0000-0000-0000-000000000006", "Cashback", "INCOME"),
    ("20000000-0000-0000-0000-000000000007", "Refund", "INCOME"),
    ("20000000-0000-0000-0000-000000000008", "Bonus", "INCOME"),
    ("20000000-0000-0000-0000-000000000009", "Other", "INCOME"),
)


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category_type", sa.String(16), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_categories_user_id_users"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["categories.id"], name=op.f("fk_categories_parent_id_categories")
        ),
        sa.CheckConstraint(
            "category_type IN ('EXPENSE', 'INCOME')", name="ck_categories_category_type"
        ),
        sa.CheckConstraint(
            "(is_system = TRUE AND user_id IS NULL) OR "
            "(is_system = FALSE AND user_id IS NOT NULL)",
            name="ck_categories_scope",
        ),
        sa.CheckConstraint("parent_id IS NULL OR parent_id <> id", name="ck_categories_not_self_parent"),
        sa.CheckConstraint("is_system = FALSE OR is_active = TRUE", name="ck_categories_system_active"),
    )
    op.create_index(op.f("ix_categories_user_id"), "categories", ["user_id"], unique=False)
    op.create_index(op.f("ix_categories_parent_id"), "categories", ["parent_id"], unique=False)
    op.create_index(op.f("ix_categories_is_system"), "categories", ["is_system"], unique=False)
    op.create_index(
        op.f("ix_categories_user_id_is_active"), "categories", ["user_id", "is_active"], unique=False
    )
    op.create_index(
        op.f("ix_categories_category_type_is_active"),
        "categories",
        ["category_type", "is_active"],
        unique=False,
    )
    op.create_index(
        "uq_categories_active_system_name_type",
        "categories",
        [sa.text("lower(name)"), "category_type"],
        unique=True,
        postgresql_where=sa.text("is_system = TRUE AND is_active = TRUE"),
    )
    op.create_index(
        "uq_categories_active_user_name_type",
        "categories",
        ["user_id", sa.text("lower(name)"), "category_type"],
        unique=True,
        postgresql_where=sa.text("is_system = FALSE AND is_active = TRUE"),
    )

    categories = sa.table(
        "categories",
        sa.column("id", sa.String),
        sa.column("user_id", sa.String),
        sa.column("name", sa.String),
        sa.column("category_type", sa.String),
        sa.column("parent_id", sa.String),
        sa.column("is_system", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": category_id,
            "user_id": None,
            "name": name,
            "category_type": category_type,
            "parent_id": None,
            "is_system": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        for category_id, name, category_type in SYSTEM_CATEGORIES
    ]
    statement = postgresql.insert(categories).values(rows).on_conflict_do_nothing(index_elements=["id"])
    op.execute(statement)


def downgrade() -> None:
    op.drop_index("uq_categories_active_user_name_type", table_name="categories")
    op.drop_index("uq_categories_active_system_name_type", table_name="categories")
    op.drop_index(op.f("ix_categories_category_type_is_active"), table_name="categories")
    op.drop_index(op.f("ix_categories_user_id_is_active"), table_name="categories")
    op.drop_index(op.f("ix_categories_is_system"), table_name="categories")
    op.drop_index(op.f("ix_categories_parent_id"), table_name="categories")
    op.drop_index(op.f("ix_categories_user_id"), table_name="categories")
    op.drop_table("categories")

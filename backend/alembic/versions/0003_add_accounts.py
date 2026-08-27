"""Add user-owned financial accounts."""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_accounts"
down_revision = "0002_add_user_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(32), nullable=False),
        sa.Column("institution_name", sa.String(255), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("current_balance", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_accounts_user_id_users"), ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "account_type IN ('BANK', 'CASH', 'CREDIT_CARD', 'WALLET', 'OTHER')",
            name="ck_accounts_account_type",
        ),
        sa.CheckConstraint(
            "currency = upper(currency) AND length(currency) = 3",
            name="ck_accounts_currency_format",
        ),
        sa.CheckConstraint(
            "(is_active = TRUE AND archived_at IS NULL) OR "
            "(is_active = FALSE AND archived_at IS NOT NULL)",
            name="ck_accounts_archive_state",
        ),
    )
    op.create_index(op.f("ix_accounts_user_id"), "accounts", ["user_id"], unique=False)
    op.create_index(
        "uq_accounts_active_user_name",
        "accounts",
        ["user_id", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )
    op.create_index(
        op.f("ix_accounts_user_id_is_active"), "accounts", ["user_id", "is_active"], unique=False
    )
    op.create_index(
        op.f("ix_accounts_user_id_archived_at"), "accounts", ["user_id", "archived_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_accounts_user_id_archived_at"), table_name="accounts")
    op.drop_index(op.f("ix_accounts_user_id_is_active"), table_name="accounts")
    op.drop_index("uq_accounts_active_user_name", table_name="accounts")
    op.drop_index(op.f("ix_accounts_user_id"), table_name="accounts")
    op.drop_table("accounts")

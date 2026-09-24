"""Add transactions ledger and transfers between accounts."""

from alembic import op
import sqlalchemy as sa


revision = "0005_add_transactions_transfers"
down_revision = "0004_add_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("account_id", sa.String(36), nullable=False),
        sa.Column("category_id", sa.String(36), nullable=True),
        sa.Column("transaction_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("merchant_name", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_transactions_account_id_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_transactions_category_id_categories"),
        ),
        sa.CheckConstraint(
            "transaction_type IN "
            "('INCOME', 'EXPENSE', 'OPENING_BALANCE', 'BALANCE_ADJUSTMENT')",
            name="ck_transactions_transaction_type",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'CANCELLED')",
            name="ck_transactions_status",
        ),
        sa.CheckConstraint(
            "(transaction_type IN ('INCOME', 'EXPENSE') AND amount > 0) OR "
            "(transaction_type IN ('OPENING_BALANCE', 'BALANCE_ADJUSTMENT') "
            "AND amount <> 0)",
            name="ck_transactions_amount_sign",
        ),
        sa.CheckConstraint(
            "(transaction_type IN ('INCOME', 'EXPENSE') AND category_id IS NOT NULL) OR "
            "(transaction_type IN ('OPENING_BALANCE', 'BALANCE_ADJUSTMENT') "
            "AND category_id IS NULL)",
            name="ck_transactions_category_presence",
        ),
    )
    op.create_index(
        "ix_transactions_account_id_transaction_date",
        "transactions",
        ["account_id", "transaction_date"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_account_id_status",
        "transactions",
        ["account_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_category_id", "transactions", ["category_id"], unique=False
    )

    op.create_table(
        "transfers",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("source_account_id", sa.String(36), nullable=False),
        sa.Column("destination_account_id", sa.String(36), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("transfer_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transfers")),
        sa.ForeignKeyConstraint(
            ["source_account_id"],
            ["accounts.id"],
            name=op.f("fk_transfers_source_account_id_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["destination_account_id"],
            ["accounts.id"],
            name=op.f("fk_transfers_destination_account_id_accounts"),
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'CANCELLED')",
            name="ck_transfers_status",
        ),
        sa.CheckConstraint("amount > 0", name="ck_transfers_amount_positive"),
        sa.CheckConstraint(
            "source_account_id <> destination_account_id",
            name="ck_transfers_distinct_accounts",
        ),
    )
    op.create_index(
        "ix_transfers_source_account_id_transfer_date",
        "transfers",
        ["source_account_id", "transfer_date"],
        unique=False,
    )
    op.create_index(
        "ix_transfers_destination_account_id_transfer_date",
        "transfers",
        ["destination_account_id", "transfer_date"],
        unique=False,
    )
    op.create_index("ix_transfers_status", "transfers", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transfers_status", table_name="transfers")
    op.drop_index(
        "ix_transfers_destination_account_id_transfer_date", table_name="transfers"
    )
    op.drop_index(
        "ix_transfers_source_account_id_transfer_date", table_name="transfers"
    )
    op.drop_table("transfers")

    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_index("ix_transactions_account_id_status", table_name="transactions")
    op.drop_index(
        "ix_transactions_account_id_transaction_date", table_name="transactions"
    )
    op.drop_table("transactions")

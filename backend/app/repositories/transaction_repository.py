"""Repository operations for the transaction ledger, always scoped to a user."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction


class TransactionRepository:
    """Database access for transactions.

    Ownership is always enforced by joining to the owning account, since a
    transaction has no direct ``user_id``. Soft-deleted rows are excluded from
    normal reads; the service layer may opt in to fetching a deleted row when it
    needs to reverse a balance effect.

    This repository performs no balance arithmetic and never commits: the
    service owns the financial transaction boundary and commits once. Writes are
    flushed so generated defaults and ordering are visible within that boundary.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_transaction(
        self,
        account_id: str,
        category_id: str | None,
        transaction_type: str,
        status: str,
        amount: Decimal,
        transaction_date: datetime,
        description: str | None = None,
        merchant_name: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            id=str(uuid4()),
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            status=status,
            amount=amount,
            transaction_date=transaction_date,
            description=description,
            merchant_name=merchant_name,
        )
        self.session.add(transaction)
        self.session.flush()
        return transaction

    def get_transaction(
        self, transaction_id: str, user_id: str, include_deleted: bool = False
    ) -> Transaction | None:
        conditions = [
            Transaction.id == transaction_id,
            Account.user_id == user_id,
        ]
        if not include_deleted:
            conditions.append(Transaction.deleted_at.is_(None))
        statement = (
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(*conditions)
        )
        return self.session.scalars(statement).first()

    def list_transactions(
        self,
        user_id: str,
        account_id: str | None = None,
        category_id: str | None = None,
        transaction_type: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Transaction]:
        statement = (
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(
                *self._filters(
                    user_id,
                    account_id,
                    category_id,
                    transaction_type,
                    status,
                    date_from,
                    date_to,
                )
            )
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        )
        if offset is not None:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.session.scalars(statement).all())

    def count_transactions(
        self,
        user_id: str,
        account_id: str | None = None,
        category_id: str | None = None,
        transaction_type: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(
                *self._filters(
                    user_id,
                    account_id,
                    category_id,
                    transaction_type,
                    status,
                    date_from,
                    date_to,
                )
            )
        )
        return self.session.scalar(statement) or 0

    def update_transaction(
        self, transaction: Transaction, values: dict[str, object]
    ) -> Transaction:
        for field, value in values.items():
            setattr(transaction, field, value)
        transaction.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return transaction

    def soft_delete_transaction(self, transaction: Transaction) -> Transaction:
        now = datetime.now(timezone.utc)
        transaction.deleted_at = now
        transaction.updated_at = now
        self.session.flush()
        return transaction

    @staticmethod
    def _filters(
        user_id: str,
        account_id: str | None,
        category_id: str | None,
        transaction_type: str | None,
        status: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list:
        conditions = [Account.user_id == user_id, Transaction.deleted_at.is_(None)]
        if account_id is not None:
            conditions.append(Transaction.account_id == account_id)
        if category_id is not None:
            conditions.append(Transaction.category_id == category_id)
        if transaction_type is not None:
            conditions.append(Transaction.transaction_type == transaction_type)
        if status is not None:
            conditions.append(Transaction.status == status)
        if date_from is not None:
            conditions.append(Transaction.transaction_date >= date_from)
        if date_to is not None:
            conditions.append(Transaction.transaction_date <= date_to)
        return conditions

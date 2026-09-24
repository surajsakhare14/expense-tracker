"""Repository operations for account-to-account transfers, scoped to a user."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transfer import Transfer


class TransferRepository:
    """Database access for transfers.

    Ownership is enforced by requiring both the source and destination accounts
    to belong to the authenticated user, since a transfer has no direct
    ``user_id``. Soft-deleted rows are excluded from normal reads; the service
    may opt in with ``include_deleted`` to reverse or edit an effective transfer.

    This repository performs no balance arithmetic and never commits: the
    service owns the financial transaction boundary and commits once. Writes are
    flushed so generated defaults and ordering are visible within that boundary.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_transfer(
        self,
        source_account_id: str,
        destination_account_id: str,
        amount: Decimal,
        status: str,
        transfer_date: datetime,
        description: str | None = None,
    ) -> Transfer:
        transfer = Transfer(
            id=str(uuid4()),
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            amount=amount,
            status=status,
            transfer_date=transfer_date,
            description=description,
        )
        self.session.add(transfer)
        self.session.flush()
        return transfer

    def get_transfer(
        self, transfer_id: str, user_id: str, include_deleted: bool = False
    ) -> Transfer | None:
        conditions = [Transfer.id == transfer_id, *self._ownership(user_id)]
        if not include_deleted:
            conditions.append(Transfer.deleted_at.is_(None))
        return self.session.scalars(select(Transfer).where(*conditions)).first()

    def list_transfers(
        self,
        user_id: str,
        account_id: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Transfer]:
        statement = (
            select(Transfer)
            .where(*self._filters(user_id, account_id, status, date_from, date_to))
            .order_by(Transfer.transfer_date.desc(), Transfer.created_at.desc())
        )
        if offset is not None:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.session.scalars(statement).all())

    def count_transfers(
        self,
        user_id: str,
        account_id: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Transfer)
            .where(*self._filters(user_id, account_id, status, date_from, date_to))
        )
        return self.session.scalar(statement) or 0

    def update_transfer(self, transfer: Transfer, values: dict[str, object]) -> Transfer:
        for field, value in values.items():
            setattr(transfer, field, value)
        transfer.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return transfer

    def soft_delete_transfer(self, transfer: Transfer) -> Transfer:
        now = datetime.now(timezone.utc)
        transfer.deleted_at = now
        transfer.updated_at = now
        self.session.flush()
        return transfer

    @staticmethod
    def _ownership(user_id: str) -> list:
        user_accounts = select(Account.id).where(Account.user_id == user_id)
        return [
            Transfer.source_account_id.in_(user_accounts),
            Transfer.destination_account_id.in_(user_accounts),
        ]

    def _filters(
        self,
        user_id: str,
        account_id: str | None,
        status: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list:
        conditions = [*self._ownership(user_id), Transfer.deleted_at.is_(None)]
        if account_id is not None:
            conditions.append(
                or_(
                    Transfer.source_account_id == account_id,
                    Transfer.destination_account_id == account_id,
                )
            )
        if status is not None:
            conditions.append(Transfer.status == status)
        if date_from is not None:
            conditions.append(Transfer.transfer_date >= date_from)
        if date_to is not None:
            conditions.append(Transfer.transfer_date <= date_to)
        return conditions

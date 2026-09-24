"""Repository operations for user-owned accounts."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.transfer import Transfer


class AccountRepository:
    """Database access for accounts, always scoped to a user."""

    def __init__(self, session: Session):
        self.session = session

    def add_account(
        self,
        user_id: str,
        name: str,
        account_type: str,
        institution_name: str | None,
        currency: str,
    ) -> Account:
        """Create and flush a new account without committing.

        The caller owns the transaction boundary, so this is used when account
        creation must be atomic with other writes (e.g. an opening-balance
        transaction). ``create_account`` wraps this and commits on its own.
        """
        account = Account(
            id=str(uuid4()),
            user_id=user_id,
            name=name,
            account_type=account_type,
            institution_name=institution_name,
            currency=currency,
            current_balance=0,
        )
        self.session.add(account)
        self.session.flush()
        return account

    def create_account(
        self,
        user_id: str,
        name: str,
        account_type: str,
        institution_name: str | None,
        currency: str,
    ) -> Account:
        account = self.add_account(
            user_id=user_id,
            name=name,
            account_type=account_type,
            institution_name=institution_name,
            currency=currency,
        )
        self.session.commit()
        return account

    def has_financial_activity(self, account_id: str) -> bool:
        """Whether any effective financial record references this account.

        Soft-deleted transactions are treated as reversed history and do not
        count. A transfer counts whenever a (non-deleted) record links the
        account as source or destination, regardless of status.
        """
        transaction_activity = (
            select(Transaction.id)
            .where(
                Transaction.account_id == account_id,
                Transaction.deleted_at.is_(None),
            )
            .limit(1)
        )
        transfer_activity = (
            select(Transfer.id)
            .where(
                or_(
                    Transfer.source_account_id == account_id,
                    Transfer.destination_account_id == account_id,
                ),
                Transfer.deleted_at.is_(None),
            )
            .limit(1)
        )
        statement = select(
            or_(exists(transaction_activity), exists(transfer_activity))
        )
        return bool(self.session.scalar(statement))

    def get_account(
        self, account_id: str, user_id: str, include_archived: bool = False
    ) -> Account | None:
        conditions = [Account.id == account_id, Account.user_id == user_id]
        if not include_archived:
            conditions.append(Account.archived_at.is_(None))
        return self.session.scalars(select(Account).where(*conditions)).first()

    def get_account_for_update(
        self, account_id: str, user_id: str, include_archived: bool = True
    ) -> Account | None:
        """Fetch a user-owned account with a row-level lock (``SELECT ... FOR UPDATE``).

        Used by financial services to serialize concurrent balance mutations.
        Archived accounts are included by default so existing history can still
        be reversed; callers enforce the "no new activity on archived" rule.
        """
        conditions = [Account.id == account_id, Account.user_id == user_id]
        if not include_archived:
            conditions.append(Account.archived_at.is_(None))
        statement = select(Account).where(*conditions).with_for_update()
        return self.session.scalars(statement).first()

    def list_accounts(self, user_id: str, include_archived: bool = False) -> list[Account]:
        conditions = [Account.user_id == user_id]
        if not include_archived:
            conditions.append(Account.archived_at.is_(None))
        statement = select(Account).where(*conditions).order_by(Account.created_at.desc())
        return list(self.session.scalars(statement).all())

    def has_active_name(self, user_id: str, name: str, exclude_id: str | None = None) -> bool:
        conditions = [
            Account.user_id == user_id,
            Account.archived_at.is_(None),
            func.lower(Account.name) == name.lower(),
        ]
        if exclude_id is not None:
            conditions.append(Account.id != exclude_id)
        return self.session.scalars(select(Account.id).where(*conditions)).first() is not None

    def update_account(self, account: Account, values: dict[str, object]) -> Account:
        for field, value in values.items():
            setattr(account, field, value)
        account.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return account

    def archive_account(self, account: Account) -> Account:
        account.is_active = False
        account.archived_at = datetime.now(timezone.utc)
        account.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return account

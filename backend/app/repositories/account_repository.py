"""Repository operations for user-owned accounts."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account


class AccountRepository:
    """Database access for accounts, always scoped to a user."""

    def __init__(self, session: Session):
        self.session = session

    def create_account(
        self,
        user_id: str,
        name: str,
        account_type: str,
        institution_name: str | None,
        currency: str,
    ) -> Account:
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
        self.session.commit()
        return account

    def get_account(
        self, account_id: str, user_id: str, include_archived: bool = False
    ) -> Account | None:
        conditions = [Account.id == account_id, Account.user_id == user_id]
        if not include_archived:
            conditions.append(Account.archived_at.is_(None))
        return self.session.scalars(select(Account).where(*conditions)).first()

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

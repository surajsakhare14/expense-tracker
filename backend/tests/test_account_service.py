"""Focused unit tests for the 0005 account financial-activity integration.

These drive AccountService / AccountRepository directly (with real
TransactionService and TransferService activity) because the behaviors under
test — opening-balance transaction creation, atomic rollback, and the
account_type/currency lock after financial activity — live in the service and
repository layers, not in the client-facing schema.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.account import AccountCreateRequest, AccountUpdateRequest
from app.services.account_service import AccountService
from app.services.transaction_service import TransactionService
from app.services.transfer_service import TransferService


def _make_user(session: Session) -> User:
    user = User(
        id=str(uuid4()),
        email=f"{uuid4().hex}@example.com",
        password_hash="not-a-real-hash",
        is_active=True,
    )
    session.add(user)
    session.commit()
    return user


def _make_category(session: Session, user_id: str, category_type: str):
    return CategoryRepository(session).create_category(
        user_id, f"Cat {uuid4().hex[:8]}", category_type
    )


def _create_account(
    service: AccountService,
    user_id: str,
    *,
    name: str | None = None,
    account_type: str = "BANK",
    currency: str = "INR",
    institution_name: str | None = None,
    opening_balance: Decimal | None = None,
):
    request = AccountCreateRequest(
        name=name or f"Acct {uuid4().hex[:8]}",
        account_type=account_type,
        currency=currency,
        institution_name=institution_name,
        opening_balance=opening_balance,
    )
    return service.create_account(user_id, request).data


def _update_account(service: AccountService, account_id: str, user_id: str, **fields):
    return service.update_account(account_id, user_id, AccountUpdateRequest(**fields)).data


def _account_transactions(session: Session, account_id: str) -> list[Transaction]:
    statement = select(Transaction).where(Transaction.account_id == account_id)
    return list(session.scalars(statement).all())


def _balance(session: Session, account_id: str) -> Decimal:
    session.expire_all()
    return session.get(Account, account_id).current_balance


def _add_income(session: Session, user_id: str, account_id: str) -> None:
    category = _make_category(session, user_id, "INCOME")
    TransactionService(session).create_transaction(
        user_id,
        account_id=account_id,
        transaction_type="INCOME",
        amount=Decimal("10.00"),
        category_id=category.id,
    )


# 1. Creation without opening_balance keeps balance at 0 and creates no transaction.
def test_create_without_opening_balance(session: Session):
    user = _make_user(session)
    account = _create_account(AccountService(session), user.id)
    assert account.current_balance == Decimal("0")
    assert _account_transactions(session, account.id) == []


# 2. opening_balance=0 keeps balance at 0 and creates no transaction.
def test_create_with_zero_opening_balance(session: Session):
    user = _make_user(session)
    account = _create_account(AccountService(session), user.id, opening_balance=Decimal("0"))
    assert account.current_balance == Decimal("0")
    assert _account_transactions(session, account.id) == []


# 3. Positive opening_balance creates one COMPLETED OPENING_BALANCE transaction.
def test_positive_opening_balance_creates_one_transaction(session: Session):
    user = _make_user(session)
    account = _create_account(AccountService(session), user.id, opening_balance=Decimal("100.00"))
    txns = _account_transactions(session, account.id)
    assert len(txns) == 1
    assert txns[0].transaction_type == "OPENING_BALANCE"
    assert txns[0].status == "COMPLETED"


# 4. Negative opening_balance creates one COMPLETED OPENING_BALANCE transaction.
def test_negative_opening_balance_creates_one_transaction(session: Session):
    user = _make_user(session)
    account = _create_account(AccountService(session), user.id, opening_balance=Decimal("-50.00"))
    txns = _account_transactions(session, account.id)
    assert len(txns) == 1
    assert txns[0].transaction_type == "OPENING_BALANCE"
    assert txns[0].status == "COMPLETED"


# 5. The opening transaction has category_id = NULL.
def test_opening_transaction_has_no_category(session: Session):
    user = _make_user(session)
    account = _create_account(AccountService(session), user.id, opening_balance=Decimal("100.00"))
    assert _account_transactions(session, account.id)[0].category_id is None


# 6. The opening transaction amount preserves the signed opening balance.
def test_opening_transaction_amount_is_signed(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    positive = _create_account(service, user.id, opening_balance=Decimal("100.00"))
    negative = _create_account(service, user.id, opening_balance=Decimal("-50.00"))
    assert _account_transactions(session, positive.id)[0].amount == Decimal("100")
    assert _account_transactions(session, negative.id)[0].amount == Decimal("-50")


# 7. Account current_balance equals the opening balance after creation.
def test_current_balance_equals_opening_balance(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    positive = _create_account(service, user.id, opening_balance=Decimal("100.00"))
    negative = _create_account(service, user.id, opening_balance=Decimal("-50.00"))
    assert _balance(session, positive.id) == Decimal("100")
    assert _balance(session, negative.id) == Decimal("-50")


# 8. Opening-balance creation is atomic: a forced commit failure persists neither
# the account nor its opening transaction.
def test_opening_balance_creation_is_atomic(session: Session, monkeypatch):
    user = _make_user(session)
    service = AccountService(session)

    def boom() -> None:
        raise RuntimeError("commit failed")

    monkeypatch.setattr(session, "commit", boom)
    with pytest.raises(RuntimeError):
        _create_account(service, user.id, name="Atomic", opening_balance=Decimal("100.00"))
    monkeypatch.undo()

    assert AccountRepository(session).has_active_name(user.id, "Atomic") is False
    assert list(session.scalars(select(Transaction)).all()) == []


# 9. account_type can be changed before any financial activity.
def test_account_type_editable_before_activity(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    account = _create_account(service, user.id, account_type="BANK")
    updated = _update_account(service, account.id, user.id, account_type="CASH")
    assert updated.account_type == "CASH"


# 10. currency can be changed before any financial activity.
def test_currency_editable_before_activity(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    account = _create_account(service, user.id, currency="INR")
    updated = _update_account(service, account.id, user.id, currency="USD")
    assert updated.currency == "USD"


# 11. account_type cannot be changed after transaction activity.
def test_account_type_locked_after_transaction(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    account = _create_account(service, user.id, account_type="BANK")
    _add_income(session, user.id, account.id)
    with pytest.raises(AppException) as exc:
        _update_account(service, account.id, user.id, account_type="CASH")
    assert exc.value.code == "ACCOUNT_ACTIVITY_LOCKED"


# 12. currency cannot be changed after transaction activity.
def test_currency_locked_after_transaction(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    account = _create_account(service, user.id, currency="INR")
    _add_income(session, user.id, account.id)
    with pytest.raises(AppException) as exc:
        _update_account(service, account.id, user.id, currency="USD")
    assert exc.value.code == "ACCOUNT_ACTIVITY_LOCKED"


# 13. account_type cannot be changed after transfer activity.
def test_account_type_locked_after_transfer(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    source = _create_account(service, user.id)
    dest = _create_account(service, user.id)
    TransferService(session).create_transfer(
        user.id, source_account_id=source.id, destination_account_id=dest.id, amount=Decimal("5")
    )
    with pytest.raises(AppException) as exc:
        _update_account(service, source.id, user.id, account_type="CASH")
    assert exc.value.code == "ACCOUNT_ACTIVITY_LOCKED"


# 14. currency cannot be changed after transfer activity.
def test_currency_locked_after_transfer(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    source = _create_account(service, user.id)
    dest = _create_account(service, user.id)
    TransferService(session).create_transfer(
        user.id, source_account_id=source.id, destination_account_id=dest.id, amount=Decimal("5")
    )
    with pytest.raises(AppException) as exc:
        _update_account(service, dest.id, user.id, currency="USD")
    assert exc.value.code == "ACCOUNT_ACTIVITY_LOCKED"


# 15. name remains editable after financial activity.
def test_name_editable_after_activity(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    account = _create_account(service, user.id)
    _add_income(session, user.id, account.id)
    updated = _update_account(service, account.id, user.id, name="Renamed")
    assert updated.name == "Renamed"


# 16. institution_name remains editable after financial activity.
def test_institution_name_editable_after_activity(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    account = _create_account(service, user.id)
    _add_income(session, user.id, account.id)
    updated = _update_account(service, account.id, user.id, institution_name="New Bank")
    assert updated.institution_name == "New Bank"


# 17. Soft-deleted (reversed) transaction activity does not count, so the
# account_type/currency lock is released once the only transaction is deleted.
def test_soft_deleted_activity_releases_lock(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    account = _create_account(service, user.id, account_type="BANK")
    category = _make_category(session, user.id, "INCOME")
    txn = TransactionService(session).create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("10.00"),
        category_id=category.id,
    )
    repository = AccountRepository(session)
    assert repository.has_financial_activity(account.id) is True
    TransactionService(session).delete_transaction(txn.id, user.id)
    assert repository.has_financial_activity(account.id) is False
    updated = _update_account(service, account.id, user.id, account_type="CASH")
    assert updated.account_type == "CASH"


# 18. An allowed edit (renaming) leaves existing transaction and transfer history
# fully intact.
def test_existing_history_remains_intact(session: Session):
    service = AccountService(session)
    user = _make_user(session)
    source = _create_account(service, user.id)
    dest = _create_account(service, user.id)
    category = _make_category(session, user.id, "INCOME")
    txn = TransactionService(session).create_transaction(
        user.id,
        account_id=source.id,
        transaction_type="INCOME",
        amount=Decimal("10.00"),
        category_id=category.id,
    )
    transfer = TransferService(session).create_transfer(
        user.id, source_account_id=source.id, destination_account_id=dest.id, amount=Decimal("5")
    )

    _update_account(service, source.id, user.id, name="Renamed Source")

    fetched_txn = TransactionService(session).get_transaction(txn.id, user.id)
    fetched_transfer = TransferService(session).get_transfer(transfer.id, user.id)
    assert fetched_txn.amount == Decimal("10")
    assert fetched_transfer.amount == Decimal("5")
    assert AccountRepository(session).has_financial_activity(source.id) is True

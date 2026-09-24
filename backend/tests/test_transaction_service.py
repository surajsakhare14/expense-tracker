"""Focused unit tests for TransactionService balance behavior.

These exercise the service directly (not the HTTP API) because several behaviors
under test — PENDING/CANCELLED status, completed<->pending transitions, and the
atomic rollback path — are not reachable through the client-facing schema, where
``status`` is never user-controlled.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.account import Account
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.services.transaction_service import TransactionService


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


def _make_account(
    session: Session, user_id: str, account_type: str = "BANK", currency: str = "INR"
) -> Account:
    return AccountRepository(session).create_account(
        user_id=user_id,
        name=f"Acct {uuid4().hex[:8]}",
        account_type=account_type,
        institution_name=None,
        currency=currency,
    )


def _make_category(session: Session, user_id: str, category_type: str):
    return CategoryRepository(session).create_category(
        user_id, f"Cat {uuid4().hex[:8]}", category_type
    )


def _balance(session: Session, account_id: str) -> Decimal:
    session.expire_all()
    return session.get(Account, account_id).current_balance


# 1. INCOME increases asset account balance.
def test_income_increases_asset_balance(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "INCOME")
    TransactionService(session).create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("100.00"),
        category_id=category.id,
    )
    assert _balance(session, account.id) == Decimal("100")


# 2. EXPENSE decreases asset account balance.
def test_expense_decreases_asset_balance(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "EXPENSE")
    TransactionService(session).create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="EXPENSE",
        amount=Decimal("40.00"),
        category_id=category.id,
    )
    assert _balance(session, account.id) == Decimal("-40")


# 3. CREDIT_CARD EXPENSE increases card owed balance.
def test_credit_card_expense_increases_owed(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "CREDIT_CARD")
    category = _make_category(session, user.id, "EXPENSE")
    TransactionService(session).create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="EXPENSE",
        amount=Decimal("50.00"),
        category_id=category.id,
    )
    assert _balance(session, account.id) == Decimal("50")


# 4. CREDIT_CARD INCOME/refund decreases card owed balance.
def test_credit_card_income_decreases_owed(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "CREDIT_CARD")
    category = _make_category(session, user.id, "INCOME")
    TransactionService(session).create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("30.00"),
        category_id=category.id,
    )
    assert _balance(session, account.id) == Decimal("-30")


# 5. PENDING transaction does not affect balance.
def test_pending_does_not_affect_balance(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "INCOME")
    TransactionService(session).create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("100.00"),
        category_id=category.id,
        status="PENDING",
    )
    assert _balance(session, account.id) == Decimal("0")


# 6. CANCELLED transaction does not affect balance.
def test_cancelled_does_not_affect_balance(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "EXPENSE")
    TransactionService(session).create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="EXPENSE",
        amount=Decimal("75.00"),
        category_id=category.id,
        status="CANCELLED",
    )
    assert _balance(session, account.id) == Decimal("0")


# 7. Editing a completed transaction applies only the balance delta.
def test_edit_completed_applies_only_delta(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "INCOME")
    service = TransactionService(session)
    txn = service.create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("100.00"),
        category_id=category.id,
    )
    service.update_transaction(txn.id, user.id, {"amount": Decimal("150.00")})
    assert _balance(session, account.id) == Decimal("150")


# 8. Editing completed -> pending reverses the old effect.
def test_edit_completed_to_pending_reverses(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "INCOME")
    service = TransactionService(session)
    txn = service.create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("100.00"),
        category_id=category.id,
    )
    service.update_transaction(txn.id, user.id, {"status": "PENDING"})
    assert _balance(session, account.id) == Decimal("0")


# 9. Editing pending -> completed applies the new effect.
def test_edit_pending_to_completed_applies(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "INCOME")
    service = TransactionService(session)
    txn = service.create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("100.00"),
        category_id=category.id,
        status="PENDING",
    )
    assert _balance(session, account.id) == Decimal("0")
    service.update_transaction(txn.id, user.id, {"status": "COMPLETED"})
    assert _balance(session, account.id) == Decimal("100")


# 10. Soft-deleting a completed transaction reverses its balance.
def test_delete_completed_reverses_balance(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "EXPENSE")
    service = TransactionService(session)
    txn = service.create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="EXPENSE",
        amount=Decimal("40.00"),
        category_id=category.id,
    )
    assert _balance(session, account.id) == Decimal("-40")
    service.delete_transaction(txn.id, user.id)
    assert _balance(session, account.id) == Decimal("0")


# 11. Soft-deleting a pending/cancelled transaction does not change balance.
def test_delete_pending_does_not_change_balance(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "INCOME")
    service = TransactionService(session)
    txn = service.create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("100.00"),
        category_id=category.id,
        status="PENDING",
    )
    service.delete_transaction(txn.id, user.id)
    assert _balance(session, account.id) == Decimal("0")


# 12. A deleted transaction is hidden from normal retrieval.
def test_deleted_transaction_hidden_from_retrieval(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "EXPENSE")
    service = TransactionService(session)
    txn = service.create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="EXPENSE",
        amount=Decimal("40.00"),
        category_id=category.id,
    )
    service.delete_transaction(txn.id, user.id)
    with pytest.raises(AppException) as exc:
        service.get_transaction(txn.id, user.id)
    assert exc.value.code == "TRANSACTION_NOT_FOUND"


# 13. A user cannot access another user's transaction.
def test_transaction_is_user_isolated(session: Session):
    owner = _make_user(session)
    account = _make_account(session, owner.id, "BANK")
    category = _make_category(session, owner.id, "INCOME")
    service = TransactionService(session)
    txn = service.create_transaction(
        owner.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("100.00"),
        category_id=category.id,
    )
    other = _make_user(session)
    with pytest.raises(AppException) as exc:
        service.get_transaction(txn.id, other.id)
    assert exc.value.code == "TRANSACTION_NOT_FOUND"


# 14. A new transaction cannot be created on an archived account.
def test_cannot_create_on_archived_account(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "INCOME")
    AccountRepository(session).archive_account(account)
    with pytest.raises(AppException) as exc:
        TransactionService(session).create_transaction(
            user.id,
            account_id=account.id,
            transaction_type="INCOME",
            amount=Decimal("100.00"),
            category_id=category.id,
        )
    assert exc.value.code == "ACCOUNT_ARCHIVED"


# 15. BALANCE_ADJUSTMENT applies the signed amount.
def test_balance_adjustment_applies_signed_amount(session: Session):
    user = _make_user(session)
    positive = _make_account(session, user.id, "BANK")
    negative = _make_account(session, user.id, "BANK")
    service = TransactionService(session)
    service.create_transaction(
        user.id,
        account_id=positive.id,
        transaction_type="BALANCE_ADJUSTMENT",
        amount=Decimal("25.00"),
        category_id=None,
    )
    service.create_transaction(
        user.id,
        account_id=negative.id,
        transaction_type="BALANCE_ADJUSTMENT",
        amount=Decimal("-25.00"),
        category_id=None,
    )
    assert _balance(session, positive.id) == Decimal("25")
    assert _balance(session, negative.id) == Decimal("-25")


# 16. BALANCE_ADJUSTMENT has no category (none stored; a category is rejected).
def test_balance_adjustment_has_no_category(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "EXPENSE")
    service = TransactionService(session)
    txn = service.create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="BALANCE_ADJUSTMENT",
        amount=Decimal("10.00"),
        category_id=None,
    )
    assert txn.category_id is None
    with pytest.raises(AppException) as exc:
        service.create_transaction(
            user.id,
            account_id=account.id,
            transaction_type="BALANCE_ADJUSTMENT",
            amount=Decimal("10.00"),
            category_id=category.id,
        )
    assert exc.value.code == "TRANSACTION_CATEGORY_NOT_ALLOWED"


# 17. Account balance remains unchanged when the operation rolls back.
def test_balance_unchanged_when_operation_rolls_back(session: Session, monkeypatch):
    user = _make_user(session)
    account = _make_account(session, user.id, "BANK")
    category = _make_category(session, user.id, "INCOME")
    service = TransactionService(session)
    service.create_transaction(
        user.id,
        account_id=account.id,
        transaction_type="INCOME",
        amount=Decimal("100.00"),
        category_id=category.id,
    )
    assert _balance(session, account.id) == Decimal("100")

    def boom() -> None:
        raise RuntimeError("commit failed")

    # Fail the commit after the balance delta has been applied and flushed; the
    # service's except-branch must roll the whole operation back.
    monkeypatch.setattr(session, "commit", boom)
    with pytest.raises(RuntimeError):
        service.create_transaction(
            user.id,
            account_id=account.id,
            transaction_type="INCOME",
            amount=Decimal("500.00"),
            category_id=category.id,
        )
    monkeypatch.undo()

    assert _balance(session, account.id) == Decimal("100")

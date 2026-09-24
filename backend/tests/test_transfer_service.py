"""Focused unit tests for TransferService balance behavior and locking.

Behaviors 1-19 use the rollback-per-test ``session`` fixture. Behavior 20 (the
concurrency check) deliberately bypasses that savepoint fixture and drives two
real, separately committed PostgreSQL sessions so that the service's
``SELECT ... FOR UPDATE`` locking and deterministic sorted-id ordering are
genuinely exercised.
"""

import threading
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, or_
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import AppException
from app.models.account import Account
from app.models.transfer import Transfer
from app.models.user import User
from app.repositories.account_repository import AccountRepository
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


def _balance(session: Session, account_id: str) -> Decimal:
    session.expire_all()
    return session.get(Account, account_id).current_balance


def _pair(
    session: Session,
    source_type: str = "BANK",
    dest_type: str = "BANK",
    source_currency: str = "INR",
    dest_currency: str = "INR",
):
    user = _make_user(session)
    source = _make_account(session, user.id, source_type, source_currency)
    dest = _make_account(session, user.id, dest_type, dest_currency)
    return user, source, dest


def _transfer(session, user_id, source_id, dest_id, amount, **kwargs):
    return TransferService(session).create_transfer(
        user_id,
        source_account_id=source_id,
        destination_account_id=dest_id,
        amount=Decimal(amount),
        **kwargs,
    )


# 1. COMPLETED asset -> asset decreases source and increases destination.
def test_completed_asset_to_asset(session: Session):
    user, source, dest = _pair(session)
    _transfer(session, user.id, source.id, dest.id, "100")
    assert _balance(session, source.id) == Decimal("-100")
    assert _balance(session, dest.id) == Decimal("100")


# 2. PENDING transfer changes neither balance.
def test_pending_transfer_no_effect(session: Session):
    user, source, dest = _pair(session)
    _transfer(session, user.id, source.id, dest.id, "100", status="PENDING")
    assert _balance(session, source.id) == Decimal("0")
    assert _balance(session, dest.id) == Decimal("0")


# 3. CANCELLED transfer changes neither balance.
def test_cancelled_transfer_no_effect(session: Session):
    user, source, dest = _pair(session)
    _transfer(session, user.id, source.id, dest.id, "100", status="CANCELLED")
    assert _balance(session, source.id) == Decimal("0")
    assert _balance(session, dest.id) == Decimal("0")


# 4. Transfer INTO a credit card decreases the card's owed balance.
def test_transfer_into_credit_card_decreases_owed(session: Session):
    user, source, dest = _pair(session, dest_type="CREDIT_CARD")
    _transfer(session, user.id, source.id, dest.id, "100")
    assert _balance(session, dest.id) == Decimal("-100")


# 5. Transfer OUT OF a credit card increases the card's owed balance.
def test_transfer_out_of_credit_card_increases_owed(session: Session):
    user, source, dest = _pair(session, source_type="CREDIT_CARD")
    _transfer(session, user.id, source.id, dest.id, "100")
    assert _balance(session, source.id) == Decimal("100")


# 6. A same-account transfer is rejected.
def test_same_account_rejected(session: Session):
    user, source, _dest = _pair(session)
    with pytest.raises(AppException) as exc:
        _transfer(session, user.id, source.id, source.id, "100")
    assert exc.value.code == "TRANSFER_SAME_ACCOUNT"


# 7. A transfer between different currencies is rejected.
def test_currency_mismatch_rejected(session: Session):
    user, source, dest = _pair(session, dest_currency="USD")
    with pytest.raises(AppException) as exc:
        _transfer(session, user.id, source.id, dest.id, "100")
    assert exc.value.code == "TRANSFER_CURRENCY_MISMATCH"


# 8. A source account owned by another user is rejected.
def test_source_from_other_user_rejected(session: Session):
    owner = _make_user(session)
    other = _make_user(session)
    foreign_source = _make_account(session, other.id, "BANK")
    dest = _make_account(session, owner.id, "BANK")
    with pytest.raises(AppException) as exc:
        _transfer(session, owner.id, foreign_source.id, dest.id, "100")
    assert exc.value.code == "ACCOUNT_NOT_FOUND"


# 9. A destination account owned by another user is rejected.
def test_destination_from_other_user_rejected(session: Session):
    owner = _make_user(session)
    other = _make_user(session)
    source = _make_account(session, owner.id, "BANK")
    foreign_dest = _make_account(session, other.id, "BANK")
    with pytest.raises(AppException) as exc:
        _transfer(session, owner.id, source.id, foreign_dest.id, "100")
    assert exc.value.code == "ACCOUNT_NOT_FOUND"


# 10. An archived source account rejects a new transfer.
def test_archived_source_rejected(session: Session):
    user, source, dest = _pair(session)
    AccountRepository(session).archive_account(source)
    with pytest.raises(AppException) as exc:
        _transfer(session, user.id, source.id, dest.id, "100")
    assert exc.value.code == "ACCOUNT_ARCHIVED"


# 11. An archived destination account rejects a new transfer.
def test_archived_destination_rejected(session: Session):
    user, source, dest = _pair(session)
    AccountRepository(session).archive_account(dest)
    with pytest.raises(AppException) as exc:
        _transfer(session, user.id, source.id, dest.id, "100")
    assert exc.value.code == "ACCOUNT_ARCHIVED"


# 12. Editing the amount reverses the old effect and applies the new effect.
def test_edit_amount_reverses_and_reapplies(session: Session):
    user, source, dest = _pair(session)
    transfer = _transfer(session, user.id, source.id, dest.id, "100")
    TransferService(session).update_transfer(transfer.id, user.id, {"amount": Decimal("150")})
    assert _balance(session, source.id) == Decimal("-150")
    assert _balance(session, dest.id) == Decimal("150")


# 13. Editing completed -> pending reverses the old balance effect.
def test_edit_completed_to_pending_reverses(session: Session):
    user, source, dest = _pair(session)
    transfer = _transfer(session, user.id, source.id, dest.id, "100")
    TransferService(session).update_transfer(transfer.id, user.id, {"status": "PENDING"})
    assert _balance(session, source.id) == Decimal("0")
    assert _balance(session, dest.id) == Decimal("0")


# 14. Editing pending -> completed applies the new balance effect.
def test_edit_pending_to_completed_applies(session: Session):
    user, source, dest = _pair(session)
    transfer = _transfer(session, user.id, source.id, dest.id, "100", status="PENDING")
    TransferService(session).update_transfer(transfer.id, user.id, {"status": "COMPLETED"})
    assert _balance(session, source.id) == Decimal("-100")
    assert _balance(session, dest.id) == Decimal("100")


# 15. Source/destination account changes are rejected.
def test_account_change_rejected(session: Session):
    user, source, dest = _pair(session)
    third = _make_account(session, user.id, "BANK")
    transfer = _transfer(session, user.id, source.id, dest.id, "100")
    with pytest.raises(AppException) as exc:
        TransferService(session).update_transfer(
            transfer.id, user.id, {"source_account_id": third.id}
        )
    assert exc.value.code == "TRANSFER_ACCOUNTS_IMMUTABLE"


# 16. Deleting a completed transfer reverses both balances.
def test_delete_completed_reverses_both(session: Session):
    user, source, dest = _pair(session)
    transfer = _transfer(session, user.id, source.id, dest.id, "100")
    assert _balance(session, source.id) == Decimal("-100")
    TransferService(session).delete_transfer(transfer.id, user.id)
    assert _balance(session, source.id) == Decimal("0")
    assert _balance(session, dest.id) == Decimal("0")


# 17. Deleting a pending/cancelled transfer changes no balances.
def test_delete_pending_no_change(session: Session):
    user, source, dest = _pair(session)
    transfer = _transfer(session, user.id, source.id, dest.id, "100", status="PENDING")
    TransferService(session).delete_transfer(transfer.id, user.id)
    assert _balance(session, source.id) == Decimal("0")
    assert _balance(session, dest.id) == Decimal("0")


# 18. A deleted transfer is hidden from normal retrieval.
def test_deleted_transfer_hidden(session: Session):
    user, source, dest = _pair(session)
    transfer = _transfer(session, user.id, source.id, dest.id, "100")
    TransferService(session).delete_transfer(transfer.id, user.id)
    with pytest.raises(AppException) as exc:
        TransferService(session).get_transfer(transfer.id, user.id)
    assert exc.value.code == "TRANSFER_NOT_FOUND"


# 19. A failed transfer operation rolls back both balances atomically.
def test_failed_transfer_rolls_back_both(session: Session, monkeypatch):
    user, source, dest = _pair(session)
    _transfer(session, user.id, source.id, dest.id, "100")
    assert _balance(session, source.id) == Decimal("-100")
    assert _balance(session, dest.id) == Decimal("100")

    def boom() -> None:
        raise RuntimeError("commit failed")

    # Fail the commit after both deltas are applied and flushed; the service's
    # except-branch must roll the whole operation back, leaving both untouched.
    monkeypatch.setattr(session, "commit", boom)
    with pytest.raises(RuntimeError):
        _transfer(session, user.id, source.id, dest.id, "500")
    monkeypatch.undo()

    assert _balance(session, source.id) == Decimal("-100")
    assert _balance(session, dest.id) == Decimal("100")


# 20. Two simultaneous opposite-direction transfers over the same account pair
# must not deadlock and must leave the mathematically correct final balances.
# This drives real, separately committed sessions (not the savepoint fixture) so
# the service's FOR UPDATE locking and sorted-id ordering are truly exercised.
def test_concurrent_opposite_transfers_no_deadlock(test_db_engine):
    maker = sessionmaker(bind=test_db_engine, class_=Session, expire_on_commit=False)

    setup = maker()
    user = _make_user(setup)
    account_a = _make_account(setup, user.id, "BANK")
    account_b = _make_account(setup, user.id, "BANK")
    account_a.current_balance = Decimal("1000")
    account_b.current_balance = Decimal("1000")
    setup.commit()
    a_id, b_id, user_id = account_a.id, account_b.id, user.id
    setup.close()

    start = threading.Barrier(2)
    errors: list[Exception] = []

    def run(src: str, dst: str, amount: str) -> None:
        worker = maker()
        try:
            start.wait(timeout=10)
            TransferService(worker).create_transfer(
                user_id,
                source_account_id=src,
                destination_account_id=dst,
                amount=Decimal(amount),
            )
        except Exception as error:
            errors.append(error)
        finally:
            worker.close()

    threads = [
        threading.Thread(target=run, args=(a_id, b_id, "100")),
        threading.Thread(target=run, args=(b_id, a_id, "40")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)

    try:
        assert all(not thread.is_alive() for thread in threads), "a transfer deadlocked"
        assert errors == [], f"unexpected errors: {errors}"
        # A: 1000 - 100 (out) + 40 (in) = 940; B: 1000 + 100 (in) - 40 (out) = 1060.
        verify = maker()
        try:
            assert verify.get(Account, a_id).current_balance == Decimal("940")
            assert verify.get(Account, b_id).current_balance == Decimal("1060")
        finally:
            verify.close()
    finally:
        # These rows were committed for real, so the savepoint fixture will not
        # roll them back; remove them explicitly to keep the test DB clean.
        cleanup = maker()
        try:
            cleanup.execute(
                delete(Transfer).where(
                    or_(
                        Transfer.source_account_id.in_([a_id, b_id]),
                        Transfer.destination_account_id.in_([a_id, b_id]),
                    )
                )
            )
            cleanup.execute(delete(Account).where(Account.id.in_([a_id, b_id])))
            cleanup.execute(delete(User).where(User.id == user_id))
            cleanup.commit()
        finally:
            cleanup.close()

"""Focused tests for the M4 analytics accounts endpoint.

The accounts report is a current-position snapshot, not a period report: it reads
each account's authoritative ``current_balance`` straight from the account domain
(never reconstructing it from transactions), signs it by account role
(``CREDIT_CARD`` balances are debt and count negatively), and groups totals per
currency without ever combining currencies. These tests drive
``AnalyticsService.get_accounts`` directly against the database, mirroring the
fixture and helper style of the income/expense/category analytics tests. Balances
are arranged by setting ``current_balance`` directly, since that column is the
authoritative snapshot the report is defined to read.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.analytics_service import AnalyticsService


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


def _account(
    session: Session,
    user_id: str,
    *,
    account_type: str = "BANK",
    currency: str = "INR",
    balance: Decimal = Decimal("0"),
    archived: bool = False,
    name: str | None = None,
):
    repo = AccountRepository(session)
    account = repo.create_account(
        user_id=user_id,
        name=name or f"Acct {uuid4().hex[:8]}",
        account_type=account_type,
        institution_name=None,
        currency=currency,
    )
    account.current_balance = balance
    session.commit()
    if archived:
        repo.archive_account(account)
    return account


def _snapshot(session, user_id, account_id=None):
    return AnalyticsService(session).get_accounts(user_id, account_id).data


def _by_id(result):
    return {account.account_id: account for account in result.accounts}


def _by_currency(result):
    return {totals.currency: totals for totals in result.totals_by_currency}


# 1. An asset account's financial position equals its current balance.
def test_asset_position_equals_current_balance(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", balance=Decimal("50000.0000"))

    result = _snapshot(session, user.id)
    assert len(result.accounts) == 1
    account = result.accounts[0]
    assert account.current_balance == Decimal("50000.0000")
    assert account.financial_position == Decimal("50000.0000")
    assert account.account_type == "BANK"
    assert account.is_archived is False


# 2. Multiple asset accounts sum into total_assets with no liabilities.
def test_multiple_asset_accounts_sum_into_total_assets(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", balance=Decimal("50000.00"))
    _account(session, user.id, account_type="CASH", balance=Decimal("1500.00"))
    _account(session, user.id, account_type="WALLET", balance=Decimal("500.00"))

    totals = _by_currency(_snapshot(session, user.id))["INR"]
    assert totals.total_assets == Decimal("52000.00")
    assert totals.total_liabilities == Decimal("0")
    assert totals.net_position == Decimal("52000.00")


# 3. A credit-card balance is reported as a negative financial position.
def test_credit_card_balance_is_a_negative_position(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="CREDIT_CARD", balance=Decimal("12000.0000"))

    account = _snapshot(session, user.id).accounts[0]
    assert account.current_balance == Decimal("12000.0000")
    assert account.financial_position == Decimal("-12000.0000")


# 4. A credit card lowers the net position (spec example: 50000 - 12000 = 38000).
def test_credit_card_reduces_net_position(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", balance=Decimal("50000.00"))
    _account(session, user.id, account_type="CREDIT_CARD", balance=Decimal("12000.00"))

    totals = _by_currency(_snapshot(session, user.id))["INR"]
    assert totals.total_assets == Decimal("50000.00")
    assert totals.total_liabilities == Decimal("12000.00")
    assert totals.net_position == Decimal("38000.00")


# 5. Different currencies are never combined into one total.
def test_multiple_currencies_are_kept_separate(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", currency="INR", balance=Decimal("50000.00"))
    _account(
        session,
        user.id,
        account_type="CREDIT_CARD",
        currency="INR",
        balance=Decimal("10000.00"),
    )
    _account(session, user.id, account_type="BANK", currency="USD", balance=Decimal("1000.00"))

    by_currency = _by_currency(_snapshot(session, user.id))
    assert set(by_currency) == {"INR", "USD"}
    assert by_currency["INR"].total_assets == Decimal("50000.00")
    assert by_currency["INR"].total_liabilities == Decimal("10000.00")
    assert by_currency["INR"].net_position == Decimal("40000.00")
    assert by_currency["USD"].total_assets == Decimal("1000.00")
    assert by_currency["USD"].total_liabilities == Decimal("0")
    assert by_currency["USD"].net_position == Decimal("1000.00")
    # No currency's net is the cross-currency sum (40000 + 1000).
    assert all(totals.net_position != Decimal("41000.00") for totals in by_currency.values())


# 6. account_id narrows the report to that single owned account.
def test_account_id_filters_to_a_single_owned_account(session: Session):
    user = _make_user(session)
    kept = _account(session, user.id, account_type="BANK", balance=Decimal("100.00"))
    _account(session, user.id, account_type="BANK", balance=Decimal("200.00"))

    result = _snapshot(session, user.id, account_id=kept.id)
    assert [a.account_id for a in result.accounts] == [kept.id]
    assert _by_currency(result)["INR"].total_assets == Decimal("100.00")


# 7. Another user's account id is rejected with the standard 404 (no data leak).
def test_foreign_account_id_is_rejected(session: Session):
    owner = _make_user(session)
    owner_account = _account(session, owner.id, balance=Decimal("100.00"))
    other = _make_user(session)

    with pytest.raises(AppException) as exc:
        _snapshot(session, other.id, account_id=owner_account.id)
    assert exc.value.code == "ACCOUNT_NOT_FOUND"
    assert exc.value.status_code == 404


# 8. A wholly unknown account id is rejected the same way.
def test_nonexistent_account_id_is_rejected(session: Session):
    user = _make_user(session)

    with pytest.raises(AppException) as exc:
        _snapshot(session, user.id, account_id=str(uuid4()))
    assert exc.value.code == "ACCOUNT_NOT_FOUND"
    assert exc.value.status_code == 404


# 9. A user's snapshot never includes another user's accounts.
def test_accounts_are_isolated_between_users(session: Session):
    owner = _make_user(session)
    _account(session, owner.id, balance=Decimal("999.00"))
    other = _make_user(session)

    result = _snapshot(session, other.id)
    assert result.accounts == []
    assert result.totals_by_currency == []


# 10. Archived accounts are included (they still hold real balances) and flagged.
def test_archived_account_is_included_and_flagged(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", balance=Decimal("300.00"))
    _account(session, user.id, account_type="BANK", balance=Decimal("200.00"), archived=True)

    result = _snapshot(session, user.id)
    by_archived = sorted(result.accounts, key=lambda a: a.is_archived)
    assert [a.is_archived for a in by_archived] == [False, True]
    # The archived account's balance still counts toward the current position.
    assert _by_currency(result)["INR"].total_assets == Decimal("500.00")


# 11. A zero-balance account is included and contributes zero.
def test_zero_balance_account_is_included(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", balance=Decimal("0"))

    result = _snapshot(session, user.id)
    assert len(result.accounts) == 1
    assert result.accounts[0].financial_position == Decimal("0")
    assert _by_currency(result)["INR"].net_position == Decimal("0")


# 12. A user with no accounts gets empty lists (no error, no totals).
def test_no_accounts_returns_empty_lists(session: Session):
    user = _make_user(session)

    result = _snapshot(session, user.id)
    assert result.accounts == []
    assert result.totals_by_currency == []


# 13. Decimal precision is preserved end to end (no float coercion).
def test_decimal_precision_is_preserved(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", balance=Decimal("12345.6789"))
    _account(session, user.id, account_type="CREDIT_CARD", balance=Decimal("0.0001"))

    result = _snapshot(session, user.id)
    totals = _by_currency(result)["INR"]
    assert isinstance(totals.total_assets, Decimal)
    assert totals.total_assets == Decimal("12345.6789")
    assert totals.total_liabilities == Decimal("0.0001")
    assert totals.net_position == Decimal("12345.6788")
    positions = {a.financial_position for a in result.accounts}
    assert Decimal("12345.6789") in positions
    assert Decimal("-0.0001") in positions


# 14. A negative (credit) card balance is a positive position and raises the net.
def test_credit_card_credit_balance_counts_as_positive(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="CREDIT_CARD", balance=Decimal("-500.00"))

    result = _snapshot(session, user.id)
    assert result.accounts[0].financial_position == Decimal("500.00")
    totals = _by_currency(result)["INR"]
    assert totals.total_liabilities == Decimal("-500.00")
    assert totals.net_position == Decimal("500.00")


# 15. An overdrawn asset account keeps its negative balance as its position.
def test_negative_asset_balance_is_reported_as_is(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", balance=Decimal("-200.00"))

    result = _snapshot(session, user.id)
    assert result.accounts[0].financial_position == Decimal("-200.00")
    assert _by_currency(result)["INR"].net_position == Decimal("-200.00")


# 16. Within a currency, net_position equals the sum of the signed positions.
def test_net_position_equals_sum_of_positions_per_currency(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", balance=Decimal("800.00"))
    _account(session, user.id, account_type="CREDIT_CARD", balance=Decimal("300.00"))

    result = _snapshot(session, user.id)
    totals = _by_currency(result)["INR"]
    expected = sum((a.financial_position for a in result.accounts), Decimal("0"))
    assert totals.net_position == expected
    assert totals.net_position == Decimal("500.00")


# 17. totals_by_currency rows are ordered by currency for a deterministic response.
def test_totals_by_currency_are_ordered_by_currency(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="BANK", currency="USD", balance=Decimal("1.00"))
    _account(session, user.id, account_type="BANK", currency="EUR", balance=Decimal("2.00"))
    _account(session, user.id, account_type="BANK", currency="INR", balance=Decimal("3.00"))

    result = _snapshot(session, user.id)
    assert [t.currency for t in result.totals_by_currency] == ["EUR", "INR", "USD"]


# 18. Every non-credit-card type is treated as an asset (no liabilities).
def test_non_credit_card_types_are_assets(session: Session):
    user = _make_user(session)
    _account(session, user.id, account_type="OTHER", balance=Decimal("40.00"))

    result = _snapshot(session, user.id)
    assert result.accounts[0].financial_position == Decimal("40.00")
    assert _by_currency(result)["INR"].total_liabilities == Decimal("0")


# 19. The position is read from current_balance, never reconstructed from transactions.
def test_financial_position_uses_current_balance_not_transactions(session: Session):
    user = _make_user(session)
    account = _account(session, user.id, account_type="BANK", balance=Decimal("100.00"))
    category = CategoryRepository(session).create_category(
        user.id, f"Cat {uuid4().hex[:8]}", "EXPENSE"
    )
    TransactionRepository(session).create_transaction(
        account_id=account.id,
        category_id=category.id,
        transaction_type="EXPENSE",
        status="COMPLETED",
        amount=Decimal("40.00"),
        transaction_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
    )

    # The raw transaction insert does not touch current_balance, so the snapshot
    # still reports the authoritative balance rather than balance minus spend.
    position = _snapshot(session, user.id).accounts[0]
    assert position.current_balance == Decimal("100.00")
    assert position.financial_position == Decimal("100.00")





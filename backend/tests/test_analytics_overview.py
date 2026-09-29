"""Focused tests for the M4 analytics overview endpoint.

These exercise the analytics service and repository directly against the
database because several eligibility rules under test — PENDING/CANCELLED
status, soft-deleted rows, and the OPENING_BALANCE/BALANCE_ADJUSTMENT types —
are not reachable through the client-facing schema, where ``status`` and those
types are never user-controlled. They reuse the same fixtures and helper style
as the other service-level tests rather than introducing a parallel system.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.account import Account
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.transfer_repository import TransferRepository
from app.schemas.analytics import AnalyticsFilters
from app.services.analytics_service import AnalyticsService

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 1, 31)
IN_WINDOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)


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


def _make_account(session: Session, user_id: str) -> Account:
    return AccountRepository(session).create_account(
        user_id=user_id,
        name=f"Acct {uuid4().hex[:8]}",
        account_type="BANK",
        institution_name=None,
        currency="INR",
    )


def _make_category(session: Session, user_id: str, category_type: str):
    return CategoryRepository(session).create_category(
        user_id, f"Cat {uuid4().hex[:8]}", category_type
    )


def _txn(
    session: Session,
    account_id: str,
    transaction_type: str,
    amount: Decimal,
    when: datetime = IN_WINDOW,
    *,
    status: str = "COMPLETED",
    category_id: str | None = None,
):
    return TransactionRepository(session).create_transaction(
        account_id=account_id,
        category_id=category_id,
        transaction_type=transaction_type,
        status=status,
        amount=amount,
        transaction_date=when,
    )


def _overview(session, user_id, account_id=None, start=PERIOD_START, end=PERIOD_END):
    filters = AnalyticsFilters(start_date=start, end_date=end, account_id=account_id)
    return AnalyticsService(session).get_overview(user_id, filters).data


# 1. Eligible INCOME is summed into total_income.
def test_income_is_summed_into_total_income(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("100.00"), category_id=income.id)

    result = _overview(session, user.id)
    assert result.total_income == Decimal("100.00")
    assert result.total_expense == Decimal("0")
    assert result.net_cash_flow == Decimal("100.00")
    assert result.net_balance_adjustment == Decimal("0")


# 2. Eligible EXPENSE is summed into total_expense.
def test_expense_is_summed_into_total_expense(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    expense = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "EXPENSE", Decimal("40.00"), category_id=expense.id)

    result = _overview(session, user.id)
    assert result.total_expense == Decimal("40.00")
    assert result.total_income == Decimal("0")
    assert result.net_cash_flow == Decimal("-40.00")


# 3. net_cash_flow equals total_income minus total_expense.
def test_net_cash_flow_is_income_minus_expense(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    expense = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "INCOME", Decimal("100.00"), category_id=income.id)
    _txn(session, account.id, "EXPENSE", Decimal("40.00"), category_id=expense.id)

    result = _overview(session, user.id)
    assert result.total_income == Decimal("100.00")
    assert result.total_expense == Decimal("40.00")
    assert result.net_cash_flow == Decimal("60.00")


# 4. BALANCE_ADJUSTMENT is its own signed metric, never income or expense.
def test_balance_adjustments_are_a_separate_signed_metric(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    _txn(session, account.id, "BALANCE_ADJUSTMENT", Decimal("25.00"))
    _txn(session, account.id, "BALANCE_ADJUSTMENT", Decimal("-10.00"))

    result = _overview(session, user.id)
    assert result.net_balance_adjustment == Decimal("15.00")
    assert result.total_income == Decimal("0")
    assert result.total_expense == Decimal("0")
    assert result.net_cash_flow == Decimal("0")


# 5. OPENING_BALANCE is excluded from every overview metric.
def test_opening_balance_is_excluded_from_all_metrics(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    _txn(session, account.id, "OPENING_BALANCE", Decimal("500.00"))

    result = _overview(session, user.id)
    assert result.total_income == Decimal("0")
    assert result.total_expense == Decimal("0")
    assert result.net_cash_flow == Decimal("0")
    assert result.net_balance_adjustment == Decimal("0")


# 6. Transfers never affect income, expense, or adjustment (credit-card payments
#    are transfers, not expenses, so they must not be double-counted).
def test_transfers_do_not_affect_any_metric(session: Session):
    user = _make_user(session)
    source = _make_account(session, user.id)
    destination = _make_account(session, user.id)
    TransferRepository(session).create_transfer(
        source_account_id=source.id,
        destination_account_id=destination.id,
        amount=Decimal("75.00"),
        status="COMPLETED",
        transfer_date=IN_WINDOW,
    )

    result = _overview(session, user.id)
    assert result.total_income == Decimal("0")
    assert result.total_expense == Decimal("0")
    assert result.net_balance_adjustment == Decimal("0")
    assert result.net_cash_flow == Decimal("0")


# 7. PENDING transactions are excluded.
def test_pending_transactions_are_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("100.00"), status="PENDING", category_id=income.id)

    assert _overview(session, user.id).total_income == Decimal("0")


# 8. CANCELLED transactions are excluded.
def test_cancelled_transactions_are_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    expense = _make_category(session, user.id, "EXPENSE")
    _txn(
        session, account.id, "EXPENSE", Decimal("50.00"), status="CANCELLED", category_id=expense.id
    )

    assert _overview(session, user.id).total_expense == Decimal("0")


# 9. Soft-deleted transactions are excluded.
def test_soft_deleted_transactions_are_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    txn = _txn(session, account.id, "INCOME", Decimal("70.00"), category_id=income.id)
    TransactionRepository(session).soft_delete_transaction(txn)

    assert _overview(session, user.id).total_income == Decimal("0")


# 10. An empty period returns Decimal zero for every metric, never null.
def test_empty_period_returns_decimal_zero_not_null(session: Session):
    user = _make_user(session)
    _make_account(session, user.id)

    result = _overview(session, user.id)
    for value in (
        result.total_income,
        result.total_expense,
        result.net_cash_flow,
        result.net_balance_adjustment,
    ):
        assert isinstance(value, Decimal)
        assert value == Decimal("0")


# 11. account_id restricts the report to that single account.
def test_account_id_filters_to_a_single_account(session: Session):
    user = _make_user(session)
    account_a = _make_account(session, user.id)
    account_b = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account_a.id, "INCOME", Decimal("100.00"), category_id=income.id)
    _txn(session, account_b.id, "INCOME", Decimal("200.00"), category_id=income.id)

    scoped = _overview(session, user.id, account_id=account_a.id)
    assert scoped.total_income == Decimal("100.00")
    assert _overview(session, user.id).total_income == Decimal("300.00")


# 12a. A user's overview never includes another user's activity.
def test_overview_is_isolated_between_users(session: Session):
    owner = _make_user(session)
    owner_account = _make_account(session, owner.id)
    owner_income = _make_category(session, owner.id, "INCOME")
    _txn(session, owner_account.id, "INCOME", Decimal("999.00"), category_id=owner_income.id)

    other = _make_user(session)
    assert _overview(session, other.id).total_income == Decimal("0")


# 12b. Requesting another user's account id is rejected (no data leak).
def test_overview_rejects_a_foreign_account_id(session: Session):
    owner = _make_user(session)
    owner_account = _make_account(session, owner.id)
    other = _make_user(session)

    with pytest.raises(AppException) as exc:
        _overview(session, other.id, account_id=owner_account.id)
    assert exc.value.code == "ACCOUNT_NOT_FOUND"
    assert exc.value.status_code == 404


# 13. The date range is inclusive of both the first and last day.
def test_date_range_is_inclusive_of_both_ends(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    on_start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    on_end = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
    before = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    after = datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc)
    _txn(session, account.id, "INCOME", Decimal("10.00"), when=on_start, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("20.00"), when=on_end, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("5.00"), when=before, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("7.00"), when=after, category_id=income.id)

    assert _overview(session, user.id).total_income == Decimal("30.00")


# 14. Decimal precision is preserved end to end (no float coercion).
def test_decimal_precision_is_preserved(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    expense = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "INCOME", Decimal("100.1234"), category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("0.0001"), category_id=income.id)
    _txn(session, account.id, "EXPENSE", Decimal("50.5555"), category_id=expense.id)

    result = _overview(session, user.id)
    assert isinstance(result.total_income, Decimal)
    assert result.total_income == Decimal("100.1235")
    assert result.total_expense == Decimal("50.5555")
    assert result.net_cash_flow == Decimal("49.5680")


# 15. Missing start_date/end_date is rejected (the overview requires a window).
def test_missing_dates_are_rejected(session: Session):
    user = _make_user(session)
    with pytest.raises(AppException) as exc:
        AnalyticsService(session).get_overview(
            user.id, AnalyticsFilters(start_date=None, end_date=PERIOD_END)
        )
    assert exc.value.code == "ANALYTICS_DATE_RANGE_REQUIRED"
    assert exc.value.status_code == 422






"""Focused tests for the M4 analytics trends (monthly time-series) endpoint.

Like the other analytics service tests these drive ``AnalyticsService.get_trends``
directly against the database, because several eligibility rules under test —
PENDING/CANCELLED status, soft-deleted rows and the OPENING_BALANCE/
BALANCE_ADJUSTMENT types — are not reachable through the client-facing schema.
Trends are reported per currency and per calendar month; every month in the
requested range appears (zero-filled) while a range with no eligible activity
yields an empty series, since there is then no currency to attach a zero row to.
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

JAN_START = date(2026, 1, 1)
JAN_END = date(2026, 1, 31)
MAR_END = date(2026, 3, 31)
IN_JAN = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
IN_FEB = datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc)
IN_MAR = datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc)


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
    session: Session,
    user_id: str,
    *,
    account_type: str = "BANK",
    currency: str = "INR",
    archived: bool = False,
) -> Account:
    repo = AccountRepository(session)
    account = repo.create_account(
        user_id=user_id,
        name=f"Acct {uuid4().hex[:8]}",
        account_type=account_type,
        institution_name=None,
        currency=currency,
    )
    if archived:
        repo.archive_account(account)
    return account


def _make_category(session: Session, user_id: str, category_type: str):
    return CategoryRepository(session).create_category(
        user_id, f"Cat {uuid4().hex[:8]}", category_type
    )


def _txn(
    session: Session,
    account_id: str,
    transaction_type: str,
    amount: Decimal,
    when: datetime = IN_JAN,
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


def _trends(session, user_id, start, end, *, account_id=None, group_by="month"):
    filters = AnalyticsFilters(start_date=start, end_date=end, account_id=account_id)
    return AnalyticsService(session).get_trends(user_id, filters, group_by).data


def _by_period(result):
    return {row.period: row for row in result.trends}


def _rows(result):
    return {(row.period, row.currency): row for row in result.trends}


# 1. A single month with both income and expense reports both and their net.
def test_single_month_income_and_expense(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    expense = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "INCOME", Decimal("50000.00"), category_id=income.id)
    _txn(session, account.id, "EXPENSE", Decimal("30000.00"), category_id=expense.id)

    result = _trends(session, user.id, JAN_START, JAN_END)
    assert [row.period for row in result.trends] == ["2026-01"]
    row = result.trends[0]
    assert row.currency == "INR"
    assert row.income == Decimal("50000.00")
    assert row.expense == Decimal("30000.00")
    assert row.net_cash_flow == Decimal("20000.00")


# 2. Activity in several months yields one row per month.
def test_multiple_months(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("100.00"), IN_JAN, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("200.00"), IN_FEB, category_id=income.id)

    by_period = _by_period(_trends(session, user.id, JAN_START, date(2026, 2, 28)))
    assert set(by_period) == {"2026-01", "2026-02"}
    assert by_period["2026-01"].income == Decimal("100.00")
    assert by_period["2026-02"].income == Decimal("200.00")


# 3. Rows are returned in chronological order across the range.
def test_chronological_ordering(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("30.00"), IN_MAR, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("10.00"), IN_JAN, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("20.00"), IN_FEB, category_id=income.id)

    result = _trends(session, user.id, JAN_START, MAR_END)
    assert [row.period for row in result.trends] == ["2026-01", "2026-02", "2026-03"]


# 4. net_cash_flow equals income minus expense for every row.
def test_net_cash_flow_is_income_minus_expense(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    expense = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "INCOME", Decimal("45000.00"), category_id=income.id)
    _txn(session, account.id, "EXPENSE", Decimal("32000.00"), category_id=expense.id)

    row = _trends(session, user.id, JAN_START, JAN_END).trends[0]
    assert row.net_cash_flow == row.income - row.expense == Decimal("13000.00")


# 5. A month with no transactions still appears as a zero row.
def test_empty_month_appears_as_zero_row(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("10.00"), IN_JAN, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("30.00"), IN_MAR, category_id=income.id)

    by_period = _by_period(_trends(session, user.id, JAN_START, MAR_END))
    assert set(by_period) == {"2026-01", "2026-02", "2026-03"}
    february = by_period["2026-02"]
    assert february.income == Decimal("0")
    assert february.expense == Decimal("0")
    assert february.net_cash_flow == Decimal("0")


# 6. The first month counts only activity on or after start_date.
def test_partial_first_month_respects_start_date(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    before = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
    on_or_after = datetime(2026, 1, 20, 12, 0, tzinfo=timezone.utc)
    _txn(session, account.id, "INCOME", Decimal("5.00"), before, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("50.00"), on_or_after, category_id=income.id)

    by_period = _by_period(_trends(session, user.id, date(2026, 1, 15), date(2026, 2, 28)))
    assert by_period["2026-01"].income == Decimal("50.00")


# 7. The last month counts only activity on or before end_date.
def test_partial_last_month_respects_end_date(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    in_range = datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc)
    after = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)
    _txn(session, account.id, "INCOME", Decimal("40.00"), in_range, category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("70.00"), after, category_id=income.id)

    by_period = _by_period(_trends(session, user.id, JAN_START, date(2026, 3, 10)))
    assert by_period["2026-03"].income == Decimal("40.00")


# 8. PENDING transactions never contribute.
def test_pending_transactions_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("100.00"), category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("999.00"), status="PENDING", category_id=income.id)

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert row.income == Decimal("100.00")


# 9. CANCELLED transactions never contribute.
def test_cancelled_transactions_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    expense = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "EXPENSE", Decimal("40.00"), category_id=expense.id)
    _txn(
        session, account.id, "EXPENSE", Decimal("77.00"),
        status="CANCELLED", category_id=expense.id,
    )

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert row.expense == Decimal("40.00")


# 10. Soft-deleted transactions never contribute.
def test_soft_deleted_transactions_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("100.00"), category_id=income.id)
    deleted = _txn(session, account.id, "INCOME", Decimal("999.00"), category_id=income.id)
    TransactionRepository(session).soft_delete_transaction(deleted)

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert row.income == Decimal("100.00")


# 11. OPENING_BALANCE transactions never contribute to income or expense.
def test_opening_balance_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("100.00"), category_id=income.id)
    _txn(session, account.id, "OPENING_BALANCE", Decimal("5000.00"), category_id=None)

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert row.income == Decimal("100.00")
    assert row.expense == Decimal("0")


# 12. BALANCE_ADJUSTMENT transactions never contribute to income or expense.
def test_balance_adjustment_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("100.00"), category_id=income.id)
    _txn(session, account.id, "BALANCE_ADJUSTMENT", Decimal("250.00"), category_id=None)

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert row.income == Decimal("100.00")
    assert row.expense == Decimal("0")


# 13. Transfers live in a separate table and never appear as income or expense.
def test_transfers_never_contribute(session: Session):
    user = _make_user(session)
    source = _make_account(session, user.id)
    dest = _make_account(session, user.id)
    TransferRepository(session).create_transfer(
        source_account_id=source.id,
        destination_account_id=dest.id,
        amount=Decimal("500.00"),
        status="COMPLETED",
        transfer_date=IN_JAN,
    )

    assert _trends(session, user.id, JAN_START, JAN_END).trends == []


# 14. A credit-card purchase is an EXPENSE and is reported.
def test_credit_card_purchase_is_expense(session: Session):
    user = _make_user(session)
    card = _make_account(session, user.id, account_type="CREDIT_CARD")
    expense = _make_category(session, user.id, "EXPENSE")
    _txn(session, card.id, "EXPENSE", Decimal("1200.00"), category_id=expense.id)

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert row.expense == Decimal("1200.00")
    assert row.net_cash_flow == Decimal("-1200.00")


# 15. A bank -> credit-card payment is a transfer and is excluded.
def test_credit_card_payment_transfer_excluded(session: Session):
    user = _make_user(session)
    bank = _make_account(session, user.id)
    card = _make_account(session, user.id, account_type="CREDIT_CARD")
    TransferRepository(session).create_transfer(
        source_account_id=bank.id,
        destination_account_id=card.id,
        amount=Decimal("800.00"),
        status="COMPLETED",
        transfer_date=IN_JAN,
    )

    assert _trends(session, user.id, JAN_START, JAN_END).trends == []


# 16. account_id narrows the report to a single owned account.
def test_account_id_filters_to_single_account(session: Session):
    user = _make_user(session)
    a = _make_account(session, user.id)
    b = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, a.id, "INCOME", Decimal("100.00"), category_id=income.id)
    _txn(session, b.id, "INCOME", Decimal("500.00"), category_id=income.id)

    result = _trends(session, user.id, JAN_START, JAN_END, account_id=a.id)
    assert _by_period(result)["2026-01"].income == Decimal("100.00")


# 17. A foreign account_id is rejected with a 404.
def test_foreign_account_id_rejected(session: Session):
    user = _make_user(session)
    other = _make_user(session)
    foreign = _make_account(session, other.id)
    with pytest.raises(AppException) as exc:
        _trends(session, user.id, JAN_START, JAN_END, account_id=foreign.id)
    assert exc.value.status_code == 404
    assert exc.value.code == "ACCOUNT_NOT_FOUND"


# 18. An unknown account_id is rejected with a 404.
def test_nonexistent_account_id_rejected(session: Session):
    user = _make_user(session)
    with pytest.raises(AppException) as exc:
        _trends(session, user.id, JAN_START, JAN_END, account_id=str(uuid4()))
    assert exc.value.status_code == 404
    assert exc.value.code == "ACCOUNT_NOT_FOUND"


# 19. Another user's activity never leaks into the caller's trends.
def test_user_isolation(session: Session):
    user = _make_user(session)
    other = _make_user(session)
    other_account = _make_account(session, other.id)
    income = _make_category(session, other.id, "INCOME")
    _txn(session, other_account.id, "INCOME", Decimal("777.00"), category_id=income.id)

    assert _trends(session, user.id, JAN_START, JAN_END).trends == []


# 20. Activity on an archived owned account is still reported.
def test_archived_account_still_reported(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("321.00"), category_id=income.id)
    AccountRepository(session).archive_account(account)

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert row.income == Decimal("321.00")


# 21. A month with income but no expense reports zero expense and net = income.
def test_income_only_month_has_zero_expense(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("500.00"), category_id=income.id)

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert row.income == Decimal("500.00")
    assert row.expense == Decimal("0")
    assert row.net_cash_flow == Decimal("500.00")


# 22. Sums preserve Decimal precision (no float drift such as 0.30000000000000004).
def test_decimal_precision_no_float_drift(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("0.10"), category_id=income.id)
    _txn(session, account.id, "INCOME", Decimal("0.20"), category_id=income.id)

    row = _by_period(_trends(session, user.id, JAN_START, JAN_END))["2026-01"]
    assert isinstance(row.income, Decimal)
    assert row.income == Decimal("0.30")


# 23. An unsupported group_by is rejected with a 422.
def test_unsupported_group_by_rejected(session: Session):
    user = _make_user(session)
    with pytest.raises(AppException) as exc:
        _trends(session, user.id, JAN_START, JAN_END, group_by="week")
    assert exc.value.status_code == 422
    assert exc.value.code == "ANALYTICS_INVALID_GROUP_BY"


# 24. Missing start_date/end_date is rejected with a 422.
def test_missing_dates_rejected(session: Session):
    user = _make_user(session)
    with pytest.raises(AppException) as exc:
        _trends(session, user.id, None, None)
    assert exc.value.status_code == 422
    assert exc.value.code == "ANALYTICS_DATE_RANGE_REQUIRED"


# 26. Different currencies are reported as separate rows, never combined.
def test_multi_currency_reported_per_currency(session: Session):
    user = _make_user(session)
    inr = _make_account(session, user.id, currency="INR")
    usd = _make_account(session, user.id, currency="USD")
    income = _make_category(session, user.id, "INCOME")
    _txn(session, inr.id, "INCOME", Decimal("100.00"), category_id=income.id)
    _txn(session, usd.id, "INCOME", Decimal("40.00"), category_id=income.id)

    result = _trends(session, user.id, JAN_START, JAN_END)
    rows = _rows(result)
    assert [(r.period, r.currency) for r in result.trends] == [
        ("2026-01", "INR"),
        ("2026-01", "USD"),
    ]
    assert rows[("2026-01", "INR")].income == Decimal("100.00")
    assert rows[("2026-01", "USD")].income == Decimal("40.00")

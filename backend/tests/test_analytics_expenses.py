"""Focused tests for the M4 analytics expense endpoint.

Like the income service tests, these exercise ``AnalyticsService.get_expense``
directly against the database so the eligibility rules the client-facing schema
never exposes (PENDING/CANCELLED status, soft deletes, the OPENING_BALANCE and
BALANCE_ADJUSTMENT types, transfers, credit-card payments) can be verified. They
reuse the same fixtures and helper style as the other service-level analytics
tests.

One rule cannot be reached through real data: ``ck_transactions_category_presence``
forbids an EXPENSE row without a category, so genuinely "uncategorized" expense
is impossible to insert (see ``test_uncategorized_expense_cannot_be_created``).
The service's handling of that branch is therefore verified by stubbing the
repository aggregation, proving such expense would be surfaced, not discarded.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.account import Account
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.analytics_repository import AnalyticsRepository
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
def _make_account(session: Session, user_id: str, account_type: str = "BANK") -> Account:
    return AccountRepository(session).create_account(
        user_id=user_id,
        name=f"Acct {uuid4().hex[:8]}",
        account_type=account_type,
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


def _expense(session, user_id, account_id=None, start=PERIOD_START, end=PERIOD_END):
    filters = AnalyticsFilters(start_date=start, end_date=end, account_id=account_id)
    return AnalyticsService(session).get_expense(user_id, filters).data


def _by_id(result):
    return {category.category_id: category for category in result.categories}
# 1. A single eligible expense transaction sets total_expense to its amount.
def test_total_expense_sums_eligible_expense(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "EXPENSE", Decimal("100.00"), category_id=groceries.id)

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("100.00")
    assert len(result.categories) == 1
    assert result.categories[0].category_id == groceries.id
    assert result.categories[0].amount == Decimal("100.00")


# 2. Expense in different categories is grouped into one row per category.
def test_expense_is_grouped_by_category(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    rent = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "EXPENSE", Decimal("100.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("200.00"), category_id=rent.id)

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("300.00")
    by_id = _by_id(result)
    assert set(by_id) == {groceries.id, rent.id}
    assert by_id[groceries.id].amount == Decimal("100.00")
    assert by_id[rent.id].amount == Decimal("200.00")


# 3. Multiple expense transactions in one category are summed into a single row.
def test_multiple_transactions_in_one_category_are_aggregated(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "EXPENSE", Decimal("30.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("70.00"), category_id=groceries.id)

    result = _expense(session, user.id)
    assert len(result.categories) == 1
    assert result.categories[0].category_id == groceries.id
    assert result.categories[0].amount == Decimal("100.00")
    assert result.total_expense == Decimal("100.00")
# 4. Each category's percentage is its amount over the total, times 100.
def test_category_percentage_is_share_of_total(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    rent = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "EXPENSE", Decimal("25.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("75.00"), category_id=rent.id)

    by_id = _by_id(_expense(session, user.id))
    assert by_id[groceries.id].percentage == Decimal("25.00")
    assert by_id[rent.id].percentage == Decimal("75.00")


# 4b. Percentages are reported to two decimals (repeating shares are rounded).
def test_percentages_are_rounded_to_two_decimals(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    first = _make_category(session, user.id, "EXPENSE")
    second = _make_category(session, user.id, "EXPENSE")
    third = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "EXPENSE", Decimal("10.00"), category_id=first.id)
    _txn(session, account.id, "EXPENSE", Decimal("10.00"), category_id=second.id)
    _txn(session, account.id, "EXPENSE", Decimal("10.00"), category_id=third.id)

    for category in _expense(session, user.id).categories:
        assert category.percentage == Decimal("33.33")


# 5 & 6. Expense with no category is surfaced (not dropped) as a single row with
#        category_id=None labelled "Uncategorized". The DB forbids such a row
#        (see test_uncategorized_expense_cannot_be_created), so the repository
#        aggregation is stubbed to drive the service's mapping directly.
def test_uncategorized_expense_is_surfaced_as_named_bucket(
    session: Session, monkeypatch
):
    def fake_expense_by_category(self, user_id, start_date, end_date, account_id=None):
        return {
            "total_expense": Decimal("100.00"),
            "categories": [
                {"category_id": "cat-1", "category_name": "Rent", "amount": Decimal("60.00")},
                {"category_id": None, "category_name": None, "amount": Decimal("40.00")},
            ],
        }

    monkeypatch.setattr(
        AnalyticsRepository, "expense_by_category", fake_expense_by_category
    )
    user = _make_user(session)

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("100.00")
    by_id = _by_id(result)
    assert None in by_id
    assert by_id[None].category_name == "Uncategorized"
    assert by_id[None].amount == Decimal("40.00")
    assert by_id[None].percentage == Decimal("40.00")


# The DB invariant behind the stubbed test above: an EXPENSE row must carry a
# category, so genuinely uncategorized expense cannot be inserted through any path.
def test_uncategorized_expense_cannot_be_created(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    with pytest.raises(IntegrityError):
        _txn(session, account.id, "EXPENSE", Decimal("10.00"), category_id=None)
# 7. Income transactions never contribute to expense.
def test_income_is_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    salary = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "EXPENSE", Decimal("40.00"), category_id=groceries.id)
    _txn(session, account.id, "INCOME", Decimal("100.00"), category_id=salary.id)

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("40.00")
    assert set(_by_id(result)) == {groceries.id}


# 8. OPENING_BALANCE is never expense.
def test_opening_balance_is_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    _txn(session, account.id, "OPENING_BALANCE", Decimal("500.00"))

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 9. BALANCE_ADJUSTMENT is never expense.
def test_balance_adjustments_are_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    _txn(session, account.id, "BALANCE_ADJUSTMENT", Decimal("25.00"))

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 10. PENDING expense is excluded.
def test_pending_expense_is_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    _txn(
        session, account.id, "EXPENSE", Decimal("100.00"), status="PENDING",
        category_id=groceries.id,
    )

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []
# 11. CANCELLED expense is excluded.
def test_cancelled_expense_is_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    _txn(
        session, account.id, "EXPENSE", Decimal("100.00"), status="CANCELLED",
        category_id=groceries.id,
    )

    assert _expense(session, user.id).total_expense == Decimal("0")


# 12. Soft-deleted expense is excluded.
def test_soft_deleted_expense_is_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    txn = _txn(session, account.id, "EXPENSE", Decimal("70.00"), category_id=groceries.id)
    TransactionRepository(session).soft_delete_transaction(txn)

    assert _expense(session, user.id).total_expense == Decimal("0")


# 13. Transfers never affect expense (they live in a separate table).
def test_transfers_do_not_affect_expense(session: Session):
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

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 13b. A credit-card payment is modelled as a transfer to the card account and
#      must never be counted as expense (no double counting of the purchases the
#      payment settles).
def test_credit_card_payment_transfer_is_not_an_expense(session: Session):
    user = _make_user(session)
    bank = _make_account(session, user.id, account_type="BANK")
    card = _make_account(session, user.id, account_type="CREDIT_CARD")
    TransferRepository(session).create_transfer(
        source_account_id=bank.id,
        destination_account_id=card.id,
        amount=Decimal("500.00"),
        status="COMPLETED",
        transfer_date=IN_WINDOW,
    )

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []
# 14. An empty period yields Decimal zero expense and no category rows.
def test_empty_period_returns_zero_and_no_categories(session: Session):
    user = _make_user(session)
    _make_account(session, user.id)

    result = _expense(session, user.id)
    assert isinstance(result.total_expense, Decimal)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 15. account_id restricts the report to that single account.
def test_account_id_filters_to_a_single_account(session: Session):
    user = _make_user(session)
    account_a = _make_account(session, user.id)
    account_b = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    _txn(session, account_a.id, "EXPENSE", Decimal("100.00"), category_id=groceries.id)
    _txn(session, account_b.id, "EXPENSE", Decimal("200.00"), category_id=groceries.id)

    scoped = _expense(session, user.id, account_id=account_a.id)
    assert scoped.total_expense == Decimal("100.00")
    assert _expense(session, user.id).total_expense == Decimal("300.00")


# 16. A user's expense never includes another user's activity.
def test_expense_is_isolated_between_users(session: Session):
    owner = _make_user(session)
    owner_account = _make_account(session, owner.id)
    owner_groceries = _make_category(session, owner.id, "EXPENSE")
    _txn(session, owner_account.id, "EXPENSE", Decimal("999.00"), category_id=owner_groceries.id)

    other = _make_user(session)
    result = _expense(session, other.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 17. The date range is inclusive of both the first and last day.
def test_date_range_is_inclusive_of_both_ends(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    on_start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    on_end = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
    before = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    after = datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc)
    _txn(session, account.id, "EXPENSE", Decimal("10.00"), when=on_start, category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("20.00"), when=on_end, category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("5.00"), when=before, category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("7.00"), when=after, category_id=groceries.id)

    assert _expense(session, user.id).total_expense == Decimal("30.00")
# 18. Decimal precision is preserved end to end (no float coercion).
def test_decimal_precision_is_preserved(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id, "EXPENSE")
    _txn(session, account.id, "EXPENSE", Decimal("100.1234"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("0.0001"), category_id=groceries.id)

    result = _expense(session, user.id)
    assert isinstance(result.total_expense, Decimal)
    assert result.total_expense == Decimal("100.1235")
    assert result.categories[0].amount == Decimal("100.1235")
    assert result.categories[0].percentage == Decimal("100.00")


# 19. Zero total expense produces no percentages and no division-by-zero error.
def test_zero_expense_has_no_division_by_zero(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    salary = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("40.00"), category_id=salary.id)

    result = _expense(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 20. Requesting another user's account id is rejected (no data leak).
def test_expense_rejects_a_foreign_account_id(session: Session):
    owner = _make_user(session)
    owner_account = _make_account(session, owner.id)
    other = _make_user(session)

    with pytest.raises(AppException) as exc:
        _expense(session, other.id, account_id=owner_account.id)
    assert exc.value.code == "ACCOUNT_NOT_FOUND"
    assert exc.value.status_code == 404


# Missing start_date/end_date is rejected (the expense report requires a window).
def test_missing_dates_are_rejected(session: Session):
    user = _make_user(session)
    with pytest.raises(AppException) as exc:
        AnalyticsService(session).get_expense(
            user.id, AnalyticsFilters(start_date=None, end_date=PERIOD_END)
        )
    assert exc.value.code == "ANALYTICS_DATE_RANGE_REQUIRED"
    assert exc.value.status_code == 422

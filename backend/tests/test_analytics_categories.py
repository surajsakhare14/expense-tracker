"""Focused tests for the M4 analytics category endpoint.

For M4 v1 the category report is expense-centric: it exposes, per expense
category, the amount, its share of the period total, and how many eligible
transactions it covers. Like the other service-level analytics tests, these
exercise ``AnalyticsService.get_categories`` directly against the database so the
eligibility rules the client-facing schema never surfaces (PENDING/CANCELLED
status, soft deletes, OPENING_BALANCE and BALANCE_ADJUSTMENT, transfers,
credit-card payments) can be verified. They reuse the same fixtures and helper
style as the income and expense analytics tests.

One rule cannot be reached through real data: ``ck_transactions_category_presence``
forbids an EXPENSE row without a category, so a genuinely "uncategorized"
category is impossible to insert (see ``test_uncategorized_expense_cannot_be_created``).
The service's handling of that branch is therefore verified by stubbing the
repository aggregation, proving such a group would be surfaced, not discarded.
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


def _make_category(session: Session, user_id: str, category_type: str = "EXPENSE"):
    return CategoryRepository(session).create_category(
        user_id, f"Cat {uuid4().hex[:8]}", category_type
    )


def _named_category(session: Session, user_id: str, name: str, category_type: str = "EXPENSE"):
    return CategoryRepository(session).create_category(user_id, name, category_type)


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


def _categories(session, user_id, account_id=None, start=PERIOD_START, end=PERIOD_END):
    filters = AnalyticsFilters(start_date=start, end_date=end, account_id=account_id)
    return AnalyticsService(session).get_categories(user_id, filters).data


def _by_id(result):
    return {category.category_id: category for category in result.categories}
# 1. A category's amount is the sum of its eligible expense.
def test_category_expense_amount_is_correct(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    _txn(session, account.id, "EXPENSE", Decimal("100.00"), category_id=groceries.id)

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("100.00")
    assert len(result.categories) == 1
    assert result.categories[0].category_id == groceries.id
    assert result.categories[0].amount == Decimal("100.00")


# 2. Multiple expenses in one category are aggregated into a single row.
def test_multiple_expenses_in_one_category_are_aggregated(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    _txn(session, account.id, "EXPENSE", Decimal("30.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("70.00"), category_id=groceries.id)

    result = _categories(session, user.id)
    assert len(result.categories) == 1
    assert result.categories[0].amount == Decimal("100.00")
    assert result.total_expense == Decimal("100.00")


# 3. transaction_count reflects the number of eligible expense rows per category.
def test_transaction_count_is_correct(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    rent = _make_category(session, user.id)
    _txn(session, account.id, "EXPENSE", Decimal("10.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("20.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("30.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("40.00"), category_id=rent.id)

    by_id = _by_id(_categories(session, user.id))
    assert by_id[groceries.id].transaction_count == 3
    assert by_id[rent.id].transaction_count == 1


# 4. Each category's percentage is its amount over the total, times 100.
def test_category_percentage_is_share_of_total(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    rent = _make_category(session, user.id)
    _txn(session, account.id, "EXPENSE", Decimal("25.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("75.00"), category_id=rent.id)

    by_id = _by_id(_categories(session, user.id))
    assert by_id[groceries.id].percentage == Decimal("25.00")
    assert by_id[rent.id].percentage == Decimal("75.00")
# 5. Every category with eligible expense is returned.
def test_multiple_categories_are_returned(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    rent = _make_category(session, user.id)
    travel = _make_category(session, user.id)
    _txn(session, account.id, "EXPENSE", Decimal("10.00"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("20.00"), category_id=rent.id)
    _txn(session, account.id, "EXPENSE", Decimal("30.00"), category_id=travel.id)

    result = _categories(session, user.id)
    assert set(_by_id(result)) == {groceries.id, rent.id, travel.id}
    assert result.total_expense == Decimal("60.00")


# 6. Categories are ordered by amount descending.
def test_categories_are_ordered_by_amount_descending(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    small = _make_category(session, user.id)
    large = _make_category(session, user.id)
    medium = _make_category(session, user.id)
    _txn(session, account.id, "EXPENSE", Decimal("100.00"), category_id=small.id)
    _txn(session, account.id, "EXPENSE", Decimal("300.00"), category_id=large.id)
    _txn(session, account.id, "EXPENSE", Decimal("200.00"), category_id=medium.id)

    result = _categories(session, user.id)
    assert [c.category_id for c in result.categories] == [large.id, medium.id, small.id]
    assert [c.amount for c in result.categories] == [
        Decimal("300.00"),
        Decimal("200.00"),
        Decimal("100.00"),
    ]


# 7. Categories with equal amounts fall back to category name ascending.
def test_equal_amounts_break_ties_by_category_name_ascending(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    zebra = _named_category(session, user.id, "Zebra")
    apple = _named_category(session, user.id, "Apple")
    mango = _named_category(session, user.id, "Mango")
    _txn(session, account.id, "EXPENSE", Decimal("50.00"), category_id=zebra.id)
    _txn(session, account.id, "EXPENSE", Decimal("50.00"), category_id=apple.id)
    _txn(session, account.id, "EXPENSE", Decimal("50.00"), category_id=mango.id)

    result = _categories(session, user.id)
    assert [c.category_name for c in result.categories] == ["Apple", "Mango", "Zebra"]
# 8. Income never contributes to the category report.
def test_income_is_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    salary = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "EXPENSE", Decimal("40.00"), category_id=groceries.id)
    _txn(session, account.id, "INCOME", Decimal("100.00"), category_id=salary.id)

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("40.00")
    assert set(_by_id(result)) == {groceries.id}


# 9. OPENING_BALANCE is never in the category report.
def test_opening_balance_is_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    _txn(session, account.id, "OPENING_BALANCE", Decimal("500.00"))

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 10. BALANCE_ADJUSTMENT is never in the category report.
def test_balance_adjustments_are_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    _txn(session, account.id, "BALANCE_ADJUSTMENT", Decimal("25.00"))

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 11. PENDING expense is excluded.
def test_pending_expenses_are_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    _txn(
        session, account.id, "EXPENSE", Decimal("100.00"), status="PENDING",
        category_id=groceries.id,
    )

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []
# 12. CANCELLED expense is excluded.
def test_cancelled_expenses_are_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    _txn(
        session, account.id, "EXPENSE", Decimal("100.00"), status="CANCELLED",
        category_id=groceries.id,
    )

    assert _categories(session, user.id).total_expense == Decimal("0")


# 13. Soft-deleted expense is excluded.
def test_soft_deleted_expenses_are_excluded(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    txn = _txn(session, account.id, "EXPENSE", Decimal("70.00"), category_id=groceries.id)
    TransactionRepository(session).soft_delete_transaction(txn)

    assert _categories(session, user.id).total_expense == Decimal("0")


# 14. Transfers never affect the category report (separate table).
def test_transfers_do_not_affect_categories(session: Session):
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

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 15. A credit-card payment (a transfer to the card account) is not an expense.
def test_credit_card_payment_transfer_is_not_a_category(session: Session):
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

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []
# 16. An empty period yields Decimal zero total and no category rows.
def test_empty_period_returns_zero_and_no_categories(session: Session):
    user = _make_user(session)
    _make_account(session, user.id)

    result = _categories(session, user.id)
    assert isinstance(result.total_expense, Decimal)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 17. account_id restricts the report to that single account.
def test_account_id_filters_to_a_single_account(session: Session):
    user = _make_user(session)
    account_a = _make_account(session, user.id)
    account_b = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    _txn(session, account_a.id, "EXPENSE", Decimal("100.00"), category_id=groceries.id)
    _txn(session, account_b.id, "EXPENSE", Decimal("200.00"), category_id=groceries.id)

    scoped = _categories(session, user.id, account_id=account_a.id)
    assert scoped.total_expense == Decimal("100.00")
    assert scoped.categories[0].transaction_count == 1
    assert _categories(session, user.id).total_expense == Decimal("300.00")


# 18. A user's category report never includes another user's activity.
def test_categories_are_isolated_between_users(session: Session):
    owner = _make_user(session)
    owner_account = _make_account(session, owner.id)
    owner_groceries = _make_category(session, owner.id)
    _txn(session, owner_account.id, "EXPENSE", Decimal("999.00"), category_id=owner_groceries.id)

    other = _make_user(session)
    result = _categories(session, other.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 19. The date range is inclusive of both the first and last day.
def test_date_range_is_inclusive_of_both_ends(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    on_start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    on_end = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
    before = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    after = datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc)
    _txn(session, account.id, "EXPENSE", Decimal("10.00"), when=on_start, category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("20.00"), when=on_end, category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("5.00"), when=before, category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("7.00"), when=after, category_id=groceries.id)

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("30.00")
    assert result.categories[0].transaction_count == 2
# 20. Decimal precision is preserved end to end (no float coercion).
def test_decimal_precision_is_preserved(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    groceries = _make_category(session, user.id)
    _txn(session, account.id, "EXPENSE", Decimal("100.1234"), category_id=groceries.id)
    _txn(session, account.id, "EXPENSE", Decimal("0.0001"), category_id=groceries.id)

    result = _categories(session, user.id)
    assert isinstance(result.total_expense, Decimal)
    assert result.total_expense == Decimal("100.1235")
    assert result.categories[0].amount == Decimal("100.1235")
    assert result.categories[0].percentage == Decimal("100.00")
    assert result.categories[0].transaction_count == 2


# 21. Zero total expense produces no percentages and no division-by-zero error.
def test_zero_expense_has_no_division_by_zero(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    salary = _make_category(session, user.id, "INCOME")
    _txn(session, account.id, "INCOME", Decimal("40.00"), category_id=salary.id)

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("0")
    assert result.categories == []


# 22. Requesting another user's account id is rejected (no data leak).
def test_categories_reject_a_foreign_account_id(session: Session):
    owner = _make_user(session)
    owner_account = _make_account(session, owner.id)
    other = _make_user(session)

    with pytest.raises(AppException) as exc:
        _categories(session, other.id, account_id=owner_account.id)
    assert exc.value.code == "ACCOUNT_NOT_FOUND"
    assert exc.value.status_code == 404
# 23. Expense with no category is surfaced (not dropped) as a single row with
#     category_id=None labelled "Uncategorized" and its own count. The DB forbids
#     such a row (see test_uncategorized_expense_cannot_be_created), so the
#     repository aggregation is stubbed to drive the service's mapping directly.
def test_uncategorized_category_is_surfaced_as_named_bucket(session: Session, monkeypatch):
    def fake_expense_category_breakdown(
        self, user_id, start_date, end_date, account_id=None
    ):
        return {
            "total_expense": Decimal("100.00"),
            "categories": [
                {
                    "category_id": "cat-1",
                    "category_name": "Rent",
                    "amount": Decimal("60.00"),
                    "transaction_count": 2,
                },
                {
                    "category_id": None,
                    "category_name": None,
                    "amount": Decimal("40.00"),
                    "transaction_count": 1,
                },
            ],
        }

    monkeypatch.setattr(
        AnalyticsRepository, "expense_category_breakdown", fake_expense_category_breakdown
    )
    user = _make_user(session)

    result = _categories(session, user.id)
    assert result.total_expense == Decimal("100.00")
    by_id = _by_id(result)
    assert None in by_id
    assert by_id[None].category_name == "Uncategorized"
    assert by_id[None].amount == Decimal("40.00")
    assert by_id[None].percentage == Decimal("40.00")
    assert by_id[None].transaction_count == 1


# The DB invariant behind the stubbed test above: an EXPENSE row must carry a
# category, so a genuinely uncategorized expense cannot be inserted through any path.
def test_uncategorized_expense_cannot_be_created(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    with pytest.raises(IntegrityError):
        _txn(session, account.id, "EXPENSE", Decimal("10.00"), category_id=None)


# Missing start_date/end_date is rejected (the category report requires a window).
def test_missing_dates_are_rejected(session: Session):
    user = _make_user(session)
    with pytest.raises(AppException) as exc:
        AnalyticsService(session).get_categories(
            user.id, AnalyticsFilters(start_date=None, end_date=PERIOD_END)
        )
    assert exc.value.code == "ANALYTICS_DATE_RANGE_REQUIRED"
    assert exc.value.status_code == 422

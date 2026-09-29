"""Focused tests for the M4 analytics foundation.

These cover only the foundation shipped in this chunk — the reusable request
filter validation, the shared filter dependency, and the repository's
user-scoped eligibility seam. There are no analytics report endpoints yet, so
there is nothing else to exercise here.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.v1.analytics.router import get_analytics_filters
from app.api.v1.analytics.router import router as analytics_router
from app.core.exceptions import AppException
from app.models.account import Account
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.analytics import AnalyticsFilters

TXN_DATE = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)


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


# --- filter schema validation ------------------------------------------------
def test_filters_accept_valid_and_empty_ranges():
    assert AnalyticsFilters().start_date is None
    window = AnalyticsFilters(start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
    assert window.end_date == date(2026, 1, 31)
    same_day = AnalyticsFilters(start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
    assert same_day.start_date == same_day.end_date


def test_filters_reject_start_after_end():
    with pytest.raises(ValidationError):
        AnalyticsFilters(start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))


def test_filters_forbid_unknown_fields_and_blank_account_id():
    with pytest.raises(ValidationError):
        AnalyticsFilters(group_by="month")
    with pytest.raises(ValidationError):
        AnalyticsFilters(account_id="")


# --- shared filter dependency ------------------------------------------------
def test_dependency_builds_validated_filters():
    filters = get_analytics_filters(
        start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), account_id=str(uuid4())
    )
    assert isinstance(filters, AnalyticsFilters)
    assert filters.start_date == date(2026, 1, 1)


def test_dependency_maps_bad_range_to_app_exception():
    with pytest.raises(AppException) as exc_info:
        get_analytics_filters(start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))
    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "ANALYTICS_INVALID_DATE_RANGE"


# --- repository eligibility seam ---------------------------------------------
def test_base_query_returns_only_eligible_user_scoped_transactions(session: Session):
    user = _make_user(session)
    account = _make_account(session, user.id)
    income = _make_category(session, user.id, "INCOME")
    expense = _make_category(session, user.id, "EXPENSE")
    txns = TransactionRepository(session)

    eligible_income = txns.create_transaction(
        account_id=account.id, category_id=income.id, transaction_type="INCOME",
        status="COMPLETED", amount=Decimal("100.00"), transaction_date=TXN_DATE,
    )
    eligible_expense = txns.create_transaction(
        account_id=account.id, category_id=expense.id, transaction_type="EXPENSE",
        status="COMPLETED", amount=Decimal("40.00"), transaction_date=TXN_DATE,
    )
    # Excluded from analytics: PENDING, CANCELLED, and soft-deleted rows.
    txns.create_transaction(
        account_id=account.id, category_id=income.id, transaction_type="INCOME",
        status="PENDING", amount=Decimal("10.00"), transaction_date=TXN_DATE,
    )
    txns.create_transaction(
        account_id=account.id, category_id=income.id, transaction_type="INCOME",
        status="CANCELLED", amount=Decimal("10.00"), transaction_date=TXN_DATE,
    )
    deleted = txns.create_transaction(
        account_id=account.id, category_id=income.id, transaction_type="INCOME",
        status="COMPLETED", amount=Decimal("10.00"), transaction_date=TXN_DATE,
    )
    txns.soft_delete_transaction(deleted)

    # Another user's completed transaction must never appear.
    other = _make_user(session)
    other_account = _make_account(session, other.id)
    other_income = _make_category(session, other.id, "INCOME")
    txns.create_transaction(
        account_id=other_account.id, category_id=other_income.id, transaction_type="INCOME",
        status="COMPLETED", amount=Decimal("999.00"), transaction_date=TXN_DATE,
    )

    query = AnalyticsRepository(session).base_transaction_query(user.id)
    result_ids = {row.id for row in session.scalars(query).all()}
    assert result_ids == {eligible_income.id, eligible_expense.id}


def test_analytics_router_is_configured_with_prefix():
    assert analytics_router.prefix == "/analytics"

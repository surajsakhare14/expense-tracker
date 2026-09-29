"""Analytics API routes (read-only financial reporting).

This is the M4 foundation. The router is registered so later chunks can attach
the analytics reports (overview/income/expenses/categories/accounts/trends)
without touching app wiring. It intentionally exposes no report endpoints yet
and returns no placeholder data. ``get_analytics_filters`` is the shared
dependency those endpoints will consume, so the start_date/end_date/account_id
validation is written once here rather than repeated per endpoint.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AppException
from app.schemas.analytics import (
    AnalyticsAccountsDataResponse,
    AnalyticsCategoriesDataResponse,
    AnalyticsExpenseDataResponse,
    AnalyticsFilters,
    AnalyticsIncomeDataResponse,
    AnalyticsOverviewDataResponse,
    AnalyticsTrendsDataResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_filters(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    account_id: str | None = Query(default=None, min_length=1),
) -> AnalyticsFilters:
    """Build the validated, shared analytics filter from query parameters.

    FastAPI validates each parameter's type first (a malformed date yields the
    project's 422 ``VALIDATION_ERROR``), so the only cross-field rule left is
    ``start_date`` <= ``end_date``, surfaced here as the standard ``AppException``
    so every analytics endpoint reuses identical validation.
    """
    try:
        return AnalyticsFilters(
            start_date=start_date, end_date=end_date, account_id=account_id
        )
    except ValidationError as exc:
        raise AppException(
            code="ANALYTICS_INVALID_DATE_RANGE",
            message="start_date must not be after end_date.",
            status_code=422,
        ) from exc


@router.get("/overview", status_code=status.HTTP_200_OK)
async def get_overview(
    filters: AnalyticsFilters = Depends(get_analytics_filters),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AnalyticsOverviewDataResponse:
    """Return aggregate income/expense/cash-flow/adjustment totals for a period.

    ``start_date`` and ``end_date`` are required and inclusive; an optional
    ``account_id`` narrows the report to a single owned account. All heavy
    lifting (validation of required dates, ownership, aggregation) lives in the
    service so this endpoint stays a thin, read-only pass-through.
    """
    return AnalyticsService(session).get_overview(current_user["user_id"], filters)


@router.get("/income", status_code=status.HTTP_200_OK)
async def get_income(
    filters: AnalyticsFilters = Depends(get_analytics_filters),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AnalyticsIncomeDataResponse:
    """Return total income for a period and its distribution by category.

    ``start_date`` and ``end_date`` are required and inclusive; an optional
    ``account_id`` narrows the report to a single owned account. Each category
    carries its ``Decimal`` amount and its percentage of the total; income with
    no category is reported under a single ``"Uncategorized"`` entry. As with the
    other analytics routes this endpoint is a thin, read-only pass-through — all
    validation, ownership and aggregation live in the service.
    """
    return AnalyticsService(session).get_income(current_user["user_id"], filters)


@router.get("/expenses", status_code=status.HTTP_200_OK)
async def get_expenses(
    filters: AnalyticsFilters = Depends(get_analytics_filters),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AnalyticsExpenseDataResponse:
    """Return total expense for a period and its distribution by category.

    ``start_date`` and ``end_date`` are required and inclusive; an optional
    ``account_id`` narrows the report to a single owned account. Each category
    carries its ``Decimal`` amount and its percentage of the total; expense with
    no category would be reported under a single ``"Uncategorized"`` entry. As
    with the other analytics routes this endpoint is a thin, read-only
    pass-through — all validation, ownership and aggregation live in the service.
    """
    return AnalyticsService(session).get_expense(current_user["user_id"], filters)


@router.get("/categories", status_code=status.HTTP_200_OK)
async def get_categories(
    filters: AnalyticsFilters = Depends(get_analytics_filters),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AnalyticsCategoriesDataResponse:
    """Return per-category expense totals, counts and shares for a period.

    The category-centric counterpart of ``/expenses``: for M4 v1 it reports, per
    expense category, the ``Decimal`` amount, its percentage of the period's total
    expense and the number of eligible transactions. ``start_date`` and
    ``end_date`` are required and inclusive; an optional ``account_id`` narrows the
    report to a single owned account. Categories are ordered by amount descending
    then name ascending; expense with no category would be reported under a single
    ``"Uncategorized"`` entry. As with the other analytics routes this endpoint is
    a thin, read-only pass-through — all validation, ownership and aggregation live
    in the service.
    """
    return AnalyticsService(session).get_categories(current_user["user_id"], filters)


@router.get("/trends", status_code=status.HTTP_200_OK)
async def get_trends(
    filters: AnalyticsFilters = Depends(get_analytics_filters),
    group_by: str = Query(default="month"),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AnalyticsTrendsDataResponse:
    """Return a monthly time-series of income, expense and net cash flow.

    ``start_date`` and ``end_date`` are required and inclusive; an optional
    ``account_id`` narrows the report to a single owned account and an optional
    ``group_by`` selects the bucketing (M4 v1 supports only ``"month"``; any other
    value yields a 422). Each row covers one calendar month for one currency — rows
    are reported per currency and never combined across currencies — and every month
    in the range appears even when it has no activity (zero-filled). As with the
    other analytics routes this endpoint is a thin, read-only pass-through —
    validation, ownership, aggregation and empty-month filling live in the service.
    """
    return AnalyticsService(session).get_trends(
        current_user["user_id"], filters, group_by
    )


@router.get("/accounts", status_code=status.HTTP_200_OK)
async def get_accounts(
    account_id: str | None = Query(default=None, min_length=1),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AnalyticsAccountsDataResponse:
    """Return the caller's current financial position across their accounts.

    A point-in-time snapshot rather than a period report, so — unlike the other
    analytics routes — it takes no ``start_date``/``end_date`` and does not depend
    on ``get_analytics_filters``. The only query parameter is an optional
    ``account_id`` that narrows the report to a single owned account (a foreign or
    unknown id yields the standard 404). Each account's authoritative
    ``current_balance`` is signed into a ``financial_position`` (credit-card debt
    counts negatively) and totals are grouped per currency, never combined across
    currencies. As with the other analytics routes this endpoint is a thin,
    read-only pass-through — ownership, signing and aggregation live in the service.
    """
    return AnalyticsService(session).get_accounts(current_user["user_id"], account_id)

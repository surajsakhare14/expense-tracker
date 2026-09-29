"""Pydantic schemas for the analytics domain (read-only financial reporting)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnalyticsFilters(BaseModel):
    """Shared query filters for every analytics endpoint.

    Centralising these here keeps the date-range and account validation in one
    place instead of duplicating it across the six planned analytics endpoints.
    All fields are optional so each report can pick its own default window;
    ``account_id`` follows the project convention of a non-empty opaque string id
    (existence and ownership are enforced in the service/repository layer, as
    elsewhere in the codebase).
    """

    model_config = ConfigDict(extra="forbid")

    start_date: date | None = None
    end_date: date | None = None
    account_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_range(self) -> "AnalyticsFilters":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date.")
        return self


class AnalyticsOverviewResponse(BaseModel):
    """Aggregate financial activity for the requested period.

    Every monetary field is a ``Decimal`` (never a float) and defaults to
    ``Decimal("0")`` when no eligible rows match, so consumers never have to
    special-case ``null``. ``net_balance_adjustment`` reports signed balance
    adjustments as their own metric and is deliberately excluded from income,
    expense and ``net_cash_flow``; transfers and OPENING_BALANCE never appear in
    any of these figures.
    """

    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date
    total_income: Decimal
    total_expense: Decimal
    net_cash_flow: Decimal
    net_balance_adjustment: Decimal


class AnalyticsOverviewDataResponse(BaseModel):
    """Wrapped analytics-overview response (matches the project ``data`` envelope)."""

    data: AnalyticsOverviewResponse


class AnalyticsIncomeCategory(BaseModel):
    """One row of the income-by-category breakdown.

    ``category_id`` is ``None`` for income that carries no category, in which case
    ``category_name`` is the literal ``"Uncategorized"`` (uncategorised income is
    surfaced, never silently dropped). ``amount`` is the ``Decimal`` sum of that
    category's eligible income and ``percentage`` is its share of ``total_income``
    (``amount / total_income * 100``); both preserve ``Decimal`` precision.
    """

    model_config = ConfigDict(from_attributes=True)

    category_id: str | None
    category_name: str
    amount: Decimal
    percentage: Decimal


class AnalyticsIncomeResponse(BaseModel):
    """Total income for a period and its distribution across categories.

    ``total_income`` is the ``Decimal`` sum of every eligible ``INCOME``
    transaction in the window (defaulting to ``Decimal("0")`` when none match, so
    consumers never see ``null``). ``categories`` holds the per-category
    breakdown, and is an empty list whenever ``total_income`` is zero.
    """

    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date
    total_income: Decimal
    categories: list[AnalyticsIncomeCategory]


class AnalyticsIncomeDataResponse(BaseModel):
    """Wrapped analytics-income response (matches the project ``data`` envelope)."""

    data: AnalyticsIncomeResponse


class AnalyticsExpenseCategory(BaseModel):
    """One row of the expense-by-category breakdown.

    ``category_id`` is ``None`` for expense that carries no category, in which
    case ``category_name`` is the literal ``"Uncategorized"`` (mirroring the
    income report; such spending is surfaced, never silently dropped). ``amount``
    is the ``Decimal`` sum of that category's eligible expense and ``percentage``
    is its share of ``total_expense`` (``amount / total_expense * 100``); both
    preserve ``Decimal`` precision.
    """

    model_config = ConfigDict(from_attributes=True)

    category_id: str | None
    category_name: str
    amount: Decimal
    percentage: Decimal


class AnalyticsExpenseResponse(BaseModel):
    """Total expense for a period and its distribution across categories.

    ``total_expense`` is the ``Decimal`` sum of every eligible ``EXPENSE``
    transaction in the window (defaulting to ``Decimal("0")`` when none match, so
    consumers never see ``null``). ``categories`` holds the per-category
    breakdown, and is an empty list whenever ``total_expense`` is zero.
    """

    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date
    total_expense: Decimal
    categories: list[AnalyticsExpenseCategory]


class AnalyticsExpenseDataResponse(BaseModel):
    """Wrapped analytics-expense response (matches the project ``data`` envelope)."""

    data: AnalyticsExpenseResponse


class AnalyticsCategoryBreakdown(BaseModel):
    """One row of the expense category-analytics breakdown.

    Extends the expense-by-category row with a ``transaction_count`` — the number
    of eligible expense transactions in the category — so the report answers both
    "how much" and "how often" per category. ``category_id`` is ``None`` for
    expense that carries no category, in which case ``category_name`` is the
    literal ``"Uncategorized"`` (consistent with the income/expense reports; such
    spending is surfaced, never silently dropped). ``amount`` is the ``Decimal``
    sum of that category's eligible expense and ``percentage`` is its share of
    ``total_expense`` (``amount / total_expense * 100``); both preserve ``Decimal``
    precision.
    """

    model_config = ConfigDict(from_attributes=True)

    category_id: str | None
    category_name: str
    amount: Decimal
    percentage: Decimal
    transaction_count: int


class AnalyticsCategoriesResponse(BaseModel):
    """Per-category expense breakdown for a period (category-centric report).

    ``total_expense`` is the ``Decimal`` sum of every eligible ``EXPENSE``
    transaction in the window (defaulting to ``Decimal("0")`` when none match, so
    consumers never see ``null``). ``categories`` holds the per-category rows
    ordered by amount descending then name ascending, and is an empty list
    whenever ``total_expense`` is zero.
    """

    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date
    total_expense: Decimal
    categories: list[AnalyticsCategoryBreakdown]


class AnalyticsCategoriesDataResponse(BaseModel):
    """Wrapped analytics-categories response (matches the project ``data`` envelope)."""

    data: AnalyticsCategoriesResponse


class AnalyticsAccountPosition(BaseModel):
    """One account's current-position snapshot (a point-in-time balance, not a period sum).

    ``current_balance`` is the account's authoritative snapshot straight from the
    account domain (never reconstructed from transactions). ``financial_position``
    is that balance signed by account role: for asset accounts (BANK/CASH/WALLET/
    OTHER) it equals ``current_balance``; for a ``CREDIT_CARD`` — where a positive
    balance is money owed — it is negated, so debt lowers the user's position.
    ``is_archived`` marks accounts kept for their standing balance though no longer
    active. All money is ``Decimal`` (never float).
    """

    model_config = ConfigDict(from_attributes=True)

    account_id: str
    account_name: str
    account_type: str
    currency: str
    current_balance: Decimal
    financial_position: Decimal
    is_archived: bool


class AnalyticsCurrencyTotals(BaseModel):
    """Per-currency asset/liability/net totals (currencies are never combined).

    Balances held in different currencies are reported in separate rows and never
    summed into one figure. ``total_assets`` is the sum of asset-account balances
    (BANK/CASH/WALLET/OTHER); ``total_liabilities`` is the sum of ``CREDIT_CARD``
    balances (money owed, kept as the positive amount owed); ``net_position`` is
    ``total_assets - total_liabilities``. Every value is a ``Decimal``.
    """

    model_config = ConfigDict(from_attributes=True)

    currency: str
    total_assets: Decimal
    total_liabilities: Decimal
    net_position: Decimal


class AnalyticsAccountsResponse(BaseModel):
    """Current distribution of a user's money across their accounts.

    A point-in-time snapshot, not a period report: it carries no date range.
    ``accounts`` lists every account's signed position individually, while
    ``totals_by_currency`` groups the assets/liabilities/net totals per currency so
    balances in different currencies are never added together. Both lists are empty
    when the user has no accounts.
    """

    model_config = ConfigDict(from_attributes=True)

    accounts: list[AnalyticsAccountPosition]
    totals_by_currency: list[AnalyticsCurrencyTotals]


class AnalyticsAccountsDataResponse(BaseModel):
    """Wrapped analytics-accounts response (matches the project ``data`` envelope)."""

    data: AnalyticsAccountsResponse


class AnalyticsTrendPeriod(BaseModel):
    """One period row of the time-series trend (one calendar month per currency).

    ``period`` is the calendar month as ``YYYY-MM`` (e.g. ``"2026-01"``).
    ``currency`` scopes the row to a single currency — trend rows are reported per
    currency and are never combined across currencies (there is no mathematically
    invalid cross-currency total). ``income`` and ``expense`` are the ``Decimal``
    sums of eligible ``INCOME``/``EXPENSE`` transactions that fall in that month and
    currency (each defaulting to ``Decimal("0")`` for a month with no activity), and
    ``net_cash_flow`` is ``income - expense``. All money is ``Decimal`` (never float).
    """

    model_config = ConfigDict(from_attributes=True)

    period: str
    currency: str
    income: Decimal
    expense: Decimal
    net_cash_flow: Decimal


class AnalyticsTrendsResponse(BaseModel):
    """Time-series view of financial activity across a requested date range.

    ``group_by`` echoes the requested grouping (M4 v1 supports only ``"month"``).
    ``trends`` holds one row per (calendar month x currency) spanning the full
    requested range — every month in the range appears even when it has no activity
    (zero-filled), so the series represents the requested timeline rather than only
    the months that happen to contain transactions. Rows are ordered by ``period``
    ascending then ``currency`` ascending for a stable chronological response.
    """

    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date
    group_by: str
    trends: list[AnalyticsTrendPeriod]


class AnalyticsTrendsDataResponse(BaseModel):
    """Wrapped analytics-trends response (matches the project ``data`` envelope)."""

    data: AnalyticsTrendsResponse

"""Business logic for the analytics domain (read-only financial reporting).

Analytics are read-only: this service issues no writes and owns no transaction
boundary (unlike the financial-mutation services, it never commits). It wires
the analytics repository and exposes the per-report methods
(overview/income/expenses/categories/accounts/trends) across the M4 chunks;
those methods must preserve ``Decimal`` precision and never coerce money to
float.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.repositories.account_repository import AccountRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsAccountPosition,
    AnalyticsAccountsDataResponse,
    AnalyticsAccountsResponse,
    AnalyticsCategoriesDataResponse,
    AnalyticsCategoriesResponse,
    AnalyticsCategoryBreakdown,
    AnalyticsCurrencyTotals,
    AnalyticsExpenseCategory,
    AnalyticsExpenseDataResponse,
    AnalyticsExpenseResponse,
    AnalyticsFilters,
    AnalyticsIncomeCategory,
    AnalyticsIncomeDataResponse,
    AnalyticsIncomeResponse,
    AnalyticsOverviewDataResponse,
    AnalyticsOverviewResponse,
    AnalyticsTrendPeriod,
    AnalyticsTrendsDataResponse,
    AnalyticsTrendsResponse,
)


class AnalyticsService:
    """User-scoped, read-only analytics operations over the financial tables."""

    # Percentages are reported to two decimal places (e.g. ``33.33``); money keeps
    # its full ``Numeric(19, 4)`` precision and is never rounded here.
    _PERCENTAGE_QUANTUM = Decimal("0.01")

    # Account roles for the current-position report: only ``CREDIT_CARD`` is a
    # liability (a positive balance is money owed); every other type is an asset.
    # There is no ``AccountType`` enum — the type is a constrained string on the
    # account model — so the role is decided by comparing that string here.
    _LIABILITY_ACCOUNT_TYPES = frozenset({"CREDIT_CARD"})

    # Time-series grouping supported by the trends report. M4 v1 supports only
    # month; any other value is rejected as a 422 rather than silently ignored so
    # the contract can widen (week/quarter/year) without breaking existing callers.
    _SUPPORTED_GROUP_BY = frozenset({"month"})
    _DEFAULT_GROUP_BY = "month"

    def __init__(self, session: Session):
        self.session = session
        self.repository = AnalyticsRepository(session)
        self.accounts = AccountRepository(session)

    def get_overview(
        self, user_id: str, filters: AnalyticsFilters
    ) -> AnalyticsOverviewDataResponse:
        """Compute the financial overview for the requested period.

        The overview reports activity *within* the period, so it aggregates
        eligible transactions rather than reading any account balance snapshot.
        ``net_cash_flow`` is derived here (income minus expense) while the raw
        sums come from the repository; every value is a ``Decimal``. When an
        ``account_id`` is supplied it must belong to the caller, otherwise the
        request is rejected with the standard 404 used elsewhere in the API.
        """
        self._require_date_range(filters, "overview")
        if filters.account_id is not None:
            self._require_owned_account(filters.account_id, user_id)

        totals = self.repository.overview_totals(
            user_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            account_id=filters.account_id,
        )
        total_income = totals["total_income"]
        total_expense = totals["total_expense"]
        overview = AnalyticsOverviewResponse(
            start_date=filters.start_date,
            end_date=filters.end_date,
            total_income=total_income,
            total_expense=total_expense,
            net_cash_flow=total_income - total_expense,
            net_balance_adjustment=totals["net_balance_adjustment"],
        )
        return AnalyticsOverviewDataResponse(data=overview)

    def get_income(
        self, user_id: str, filters: AnalyticsFilters
    ) -> AnalyticsIncomeDataResponse:
        """Compute total income for the period and its per-category distribution.

        Only eligible ``INCOME`` transactions in the (inclusive) window are
        counted; expense, opening-balance, balance-adjustment, non-``COMPLETED``,
        soft-deleted rows and transfers never contribute. The repository does the
        grouping/summing in SQL; this method derives each category's share of the
        total. ``percentage`` is ``amount / total_income * 100`` as a ``Decimal``
        rounded to two places. Income carrying no category is surfaced as a single
        ``category_id=None`` / ``category_name="Uncategorized"`` row rather than
        being dropped. When no income matches, ``total_income`` is ``Decimal("0")``
        and ``categories`` is empty, so no division by zero can occur. A supplied
        ``account_id`` must belong to the caller (else a standard 404).
        """
        self._require_date_range(filters, "income")
        if filters.account_id is not None:
            self._require_owned_account(filters.account_id, user_id)

        breakdown = self.repository.income_by_category(
            user_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            account_id=filters.account_id,
        )
        total_income = breakdown["total_income"]
        categories = [
            AnalyticsIncomeCategory(
                category_id=row["category_id"],
                category_name=row["category_name"] or "Uncategorized",
                amount=row["amount"],
                percentage=self._percentage(row["amount"], total_income),
            )
            for row in breakdown["categories"]
        ]
        income = AnalyticsIncomeResponse(
            start_date=filters.start_date,
            end_date=filters.end_date,
            total_income=total_income,
            categories=categories,
        )
        return AnalyticsIncomeDataResponse(data=income)

    def get_expense(
        self, user_id: str, filters: AnalyticsFilters
    ) -> AnalyticsExpenseDataResponse:
        """Compute total expense for the period and its per-category distribution.

        The expense counterpart of ``get_income``: only eligible ``EXPENSE``
        transactions in the (inclusive) window are counted; income,
        opening-balance, balance-adjustment, non-``COMPLETED``, soft-deleted rows
        and transfers never contribute (credit-card payments are transfers, not
        expenses). The repository does the grouping/summing in SQL; this method
        derives each category's share of the total. ``percentage`` is
        ``amount / total_expense * 100`` as a ``Decimal`` rounded to two places.
        Expense carrying no category would be surfaced as a single
        ``category_id=None`` / ``category_name="Uncategorized"`` row rather than
        dropped. When no expense matches, ``total_expense`` is ``Decimal("0")`` and
        ``categories`` is empty, so no division by zero can occur. A supplied
        ``account_id`` must belong to the caller (else a standard 404).
        """
        self._require_date_range(filters, "expense")
        if filters.account_id is not None:
            self._require_owned_account(filters.account_id, user_id)

        breakdown = self.repository.expense_by_category(
            user_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            account_id=filters.account_id,
        )
        total_expense = breakdown["total_expense"]
        categories = [
            AnalyticsExpenseCategory(
                category_id=row["category_id"],
                category_name=row["category_name"] or "Uncategorized",
                amount=row["amount"],
                percentage=self._percentage(row["amount"], total_expense),
            )
            for row in breakdown["categories"]
        ]
        expense = AnalyticsExpenseResponse(
            start_date=filters.start_date,
            end_date=filters.end_date,
            total_expense=total_expense,
            categories=categories,
        )
        return AnalyticsExpenseDataResponse(data=expense)

    def get_categories(
        self, user_id: str, filters: AnalyticsFilters
    ) -> AnalyticsCategoriesDataResponse:
        """Compute the per-category expense breakdown for the period.

        Category analytics is expense-centric for M4 v1: it answers "how much and
        how often did I spend in each category?". It applies the same eligibility,
        scoping and precision rules as ``get_expense`` and additionally reports
        each category's ``transaction_count``. Categories arrive already ordered by
        amount (descending, then name) from the repository; ``percentage`` is each
        category's share of ``total_expense`` as a two-place ``Decimal``. Expense
        carrying no category would be surfaced as a single ``category_id=None`` /
        ``category_name="Uncategorized"`` row rather than dropped. When no expense
        matches, ``total_expense`` is ``Decimal("0")`` and ``categories`` is empty,
        so no division by zero can occur. A supplied ``account_id`` must belong to
        the caller (else a standard 404).
        """
        self._require_date_range(filters, "categories")
        if filters.account_id is not None:
            self._require_owned_account(filters.account_id, user_id)

        breakdown = self.repository.expense_category_breakdown(
            user_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            account_id=filters.account_id,
        )
        total_expense = breakdown["total_expense"]
        categories = [
            AnalyticsCategoryBreakdown(
                category_id=row["category_id"],
                category_name=row["category_name"] or "Uncategorized",
                amount=row["amount"],
                percentage=self._percentage(row["amount"], total_expense),
                transaction_count=row["transaction_count"],
            )
            for row in breakdown["categories"]
        ]
        response = AnalyticsCategoriesResponse(
            start_date=filters.start_date,
            end_date=filters.end_date,
            total_expense=total_expense,
            categories=categories,
        )
        return AnalyticsCategoriesDataResponse(data=response)

    def get_trends(
        self,
        user_id: str,
        filters: AnalyticsFilters,
        group_by: str | None = None,
    ) -> AnalyticsTrendsDataResponse:
        """Compute a monthly time-series of income, expense and net cash flow.

        Reports, for every calendar month spanning the (inclusive) requested range,
        the eligible ``INCOME`` and ``EXPENSE`` totals and their difference
        (``net_cash_flow = income - expense``). The same eligibility, scoping and
        precision rules as the other period reports apply; ``OPENING_BALANCE``,
        ``BALANCE_ADJUSTMENT`` and transfers (including credit-card payments) never
        contribute, while a credit-card *purchase* is an ordinary ``EXPENSE`` and is
        counted. Rows are reported per currency and never combined across currencies.
        The repository aggregates each present (month, currency) in PostgreSQL; this
        method fills every empty month in the range with ``Decimal("0")`` so the
        series follows the requested timeline, and orders rows by month then
        currency. ``group_by`` supports only ``"month"`` in M4 v1 (any other value is
        a 422). A supplied ``account_id`` must belong to the caller (else a 404).
        """
        self._require_date_range(filters, "trends")
        group_by = group_by if group_by is not None else self._DEFAULT_GROUP_BY
        self._require_supported_group_by(group_by)
        if filters.account_id is not None:
            self._require_owned_account(filters.account_id, user_id)

        rows = self.repository.monthly_trends(
            user_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            account_id=filters.account_id,
        )
        trends = self._build_trend_timeline(filters.start_date, filters.end_date, rows)
        response = AnalyticsTrendsResponse(
            start_date=filters.start_date,
            end_date=filters.end_date,
            group_by=group_by,
            trends=trends,
        )
        return AnalyticsTrendsDataResponse(data=response)

    def get_accounts(
        self, user_id: str, account_id: str | None = None
    ) -> AnalyticsAccountsDataResponse:
        """Report how the caller's money is currently distributed across accounts.

        Unlike the period reports this is a point-in-time snapshot, so it takes no
        date range. Each account's ``current_balance`` is read straight from the
        account domain (the authoritative source — never reconstructed from
        transactions) and signed into a ``financial_position``: assets keep their
        balance, a ``CREDIT_CARD`` balance is negated because a positive card
        balance is money owed. Totals are grouped per currency and never combined
        across currencies. Archived accounts are included — an archived account can
        still hold a real balance, so dropping it would misstate the position — and
        are flagged with ``is_archived``. When an ``account_id`` is given it must
        belong to the caller (else a standard 404) and only that account is
        reported; otherwise every account the user owns is included.
        """
        if account_id is not None:
            self._require_owned_account(account_id, user_id)
            snapshot = [self.accounts.get_account(account_id, user_id, include_archived=True)]
        else:
            snapshot = self.accounts.list_accounts(user_id, include_archived=True)

        positions = [self._account_position(account) for account in snapshot]
        response = AnalyticsAccountsResponse(
            accounts=positions,
            totals_by_currency=self._totals_by_currency(positions),
        )
        return AnalyticsAccountsDataResponse(data=response)

    @staticmethod
    def _require_date_range(filters: AnalyticsFilters, report: str) -> None:
        # Every period report requires an explicit window. The shared filter makes
        # the dates optional (so one dependency serves all reports), so the
        # required-ness is enforced here as the project's standard 422.
        if filters.start_date is None or filters.end_date is None:
            raise AppException(
                code="ANALYTICS_DATE_RANGE_REQUIRED",
                message=f"start_date and end_date are required for the {report} report.",
                status_code=422,
            )

    def _require_supported_group_by(self, group_by: str) -> None:
        # M4 v1 supports only monthly grouping. An unsupported value is a client
        # error, surfaced as the project's standard 422 (never silently coerced to
        # "month") so callers learn the value was rejected.
        if group_by not in self._SUPPORTED_GROUP_BY:
            supported = ", ".join(sorted(self._SUPPORTED_GROUP_BY))
            raise AppException(
                code="ANALYTICS_INVALID_GROUP_BY",
                message=f"group_by must be one of: {supported}.",
                status_code=422,
            )

    def _percentage(self, amount: Decimal, total: Decimal) -> Decimal:
        # Guard against division by zero: eligible income/expense amounts are
        # always positive, so a zero total means there are no rows and this is
        # never reached — but the guard keeps the method total and self-contained.
        if total == 0:
            return Decimal("0.00")
        return (amount / total * Decimal("100")).quantize(
            self._PERCENTAGE_QUANTUM, rounding=ROUND_HALF_UP
        )

    def _require_owned_account(self, account_id: str, user_id: str) -> None:
        # Archived accounts are included: past activity on a now-archived account
        # still belongs to the user and must be reportable. Only genuinely foreign
        # or unknown ids are rejected, matching the rest of the API's 404 behavior.
        if self.accounts.get_account(account_id, user_id, include_archived=True) is None:
            raise AppException(
                code="ACCOUNT_NOT_FOUND",
                message="Account could not be found.",
                status_code=404,
            )

    def _account_position(self, account) -> AnalyticsAccountPosition:
        # Sign the authoritative balance by account role: a credit card's positive
        # balance is debt, so it is negated; every other type is held as an asset.
        balance = account.current_balance
        if account.account_type in self._LIABILITY_ACCOUNT_TYPES:
            financial_position = -balance
        else:
            financial_position = balance
        return AnalyticsAccountPosition(
            account_id=account.id,
            account_name=account.name,
            account_type=account.account_type,
            currency=account.currency,
            current_balance=balance,
            financial_position=financial_position,
            is_archived=account.archived_at is not None,
        )

    def _totals_by_currency(
        self, positions: list[AnalyticsAccountPosition]
    ) -> list[AnalyticsCurrencyTotals]:
        # Aggregate strictly within each currency — balances in different currencies
        # are never added together. Assets add to ``total_assets``; credit cards add
        # their owed balance to ``total_liabilities``; net is assets minus
        # liabilities. Rows are ordered by currency for a deterministic response.
        assets: dict[str, Decimal] = {}
        liabilities: dict[str, Decimal] = {}
        for position in positions:
            currency = position.currency
            assets.setdefault(currency, Decimal("0"))
            liabilities.setdefault(currency, Decimal("0"))
            if position.account_type in self._LIABILITY_ACCOUNT_TYPES:
                liabilities[currency] += position.current_balance
            else:
                assets[currency] += position.current_balance
        return [
            AnalyticsCurrencyTotals(
                currency=currency,
                total_assets=assets[currency],
                total_liabilities=liabilities[currency],
                net_position=assets[currency] - liabilities[currency],
            )
            for currency in sorted(assets)
        ]

    def _build_trend_timeline(
        self, start_date: date, end_date: date, rows: list[dict]
    ) -> list[AnalyticsTrendPeriod]:
        # The repository returns only (month, currency) pairs that actually have
        # activity; expand that into the full requested timeline so every month in
        # range appears for each currency the user transacted in — empty months are
        # zero-filled rather than dropped. Currencies come from the data (a wholly
        # empty range therefore yields no rows, as there is no currency to attach a
        # zero series to); different currencies stay in separate rows and are never
        # summed. Rows are ordered by month then currency for a stable response.
        periods = self._month_sequence(start_date, end_date)
        currencies = sorted({row["currency"] for row in rows})
        by_key = {(row["period"], row["currency"]): row for row in rows}
        trends: list[AnalyticsTrendPeriod] = []
        for period in periods:
            for currency in currencies:
                row = by_key.get((period, currency))
                income = row["income"] if row is not None else Decimal("0")
                expense = row["expense"] if row is not None else Decimal("0")
                trends.append(
                    AnalyticsTrendPeriod(
                        period=period,
                        currency=currency,
                        income=income,
                        expense=expense,
                        net_cash_flow=income - expense,
                    )
                )
        return trends

    @staticmethod
    def _month_sequence(start_date: date, end_date: date) -> list[str]:
        # Enumerate calendar months from start_date's month through end_date's month
        # inclusive as ``YYYY-MM`` labels. This is the presentation axis (which months
        # to show); the monthly aggregation itself happens in PostgreSQL, so no month
        # boundary is computed here for summing.
        periods: list[str] = []
        year, month = start_date.year, start_date.month
        while (year, month) <= (end_date.year, end_date.month):
            periods.append(f"{year:04d}-{month:02d}")
            month += 1
            if month > 12:
                month = 1
                year += 1
        return periods
